"""
Saman Tax Service — یکپارچگی با سامانه سامان
"""
import logging
import requests
from typing import Optional
from django.db import transaction
from django.utils import timezone
from django.conf import settings
from .models import TaxInvoice, InvoiceStatus

logger = logging.getLogger(__name__)


class SamanService:
    """سرویس یکپارچگی با سامانه مالیاتی سامان"""

    BASE_URL = getattr(settings, 'SAMAN_BASE_URL', 'https://api.saman.tid.ir/api/v1')
    MAX_RETRY = 5

    # ----- احراز هویت -----

    @classmethod
    def _get_token(cls) -> Optional[str]:
        """دریافت access token از سامان"""
        try:
            url = f"{cls.BASE_URL}/auth/token"
            data = {
                'username': getattr(settings, 'SAMAN_USERNAME', ''),
                'password': getattr(settings, 'SAMAN_PASSWORD', ''),
                'client_id': getattr(settings, 'SAMAN_CLIENT_ID', ''),
                'client_secret': getattr(settings, 'SAMAN_CLIENT_SECRET', ''),
                'grant_type': 'password',
            }
            response = requests.post(url, json=data, timeout=15)
            response.raise_for_status()
            return response.json().get('access_token')
        except Exception as e:
            logger.error(f'Saman auth failed: {e}')
            return None

    # ----- ساخت صورتحساب -----

    @classmethod
    @transaction.atomic
    def create_invoice_for_sale(cls, sale_id: int) -> TaxInvoice:
        """ساخت صورتحساب برای یک فروش قطعی"""

        from apps.sales.models import SalesHeader
        sale = SalesHeader.objects.select_related('store').get(id=sale_id)

        if sale.sales_type != SalesHeader.SalesType.FIRM:
            raise ValueError('فقط برای فروش‌های قطعی صورتحساب صادر می‌شود')

        # اگر قبلاً صورتحساب ساخته شده، برگرداند
        existing = TaxInvoice.objects.filter(sale=sale).first()
        if existing:
            return existing

        # ساخت header_data (اطلاعات سربرگ)
        header_data = cls._build_header_data(sale)

        # ساخت body_data (اقلام صورتحساب)
        body_data = cls._build_body_data(sale)

        return TaxInvoice.objects.create(
            store=sale.store,
            sale=sale,
            invoice_status=InvoiceStatus.DRAFT,
            header_data=header_data,
            body_data=body_data,
            created_by=sale.created_by,
        )

    @staticmethod
    def _build_header_data(sale) -> dict:
        """ساخت داده سربرگ صورتحساب"""
        return {
            'invoiceType': 'TAX_INVOICE',
            'invoiceDate': sale.sale_date.isoformat(),
            'invoiceNumber': sale.sale_no,
            'seller': {
                'taxID': getattr(settings, 'SAMAN_SELLER_TAX_ID', ''),
                'name': getattr(settings, 'SAMAN_SELLER_NAME', 'کارگاه تولیدی'),
                'address': getattr(settings, 'SAMAN_SELLER_ADDRESS', ''),
            },
            'buyer': {
                'taxID': sale.store.code,  # در عمل شناسه اقتصادی فروشگاه
                'name': sale.store.name,
                'address': sale.store.address,
            },
            'totalAmount': float(sale.total_amount),
            'totalTax': float(sale.total_amount) * 0.09,  # VAT 9%
            'totalPayable': float(sale.total_amount) * 1.09,
        }

    @staticmethod
    def _build_body_data(sale) -> list:
        """ساخت لیست اقلام صورتحساب"""
        items = []
        for line in sale.lines.all():
            items.append({
                'productId': line.product.code,
                'productName': line.product.name,
                'quantity': float(line.qty),
                'unitPrice': float(line.unit_price),
                'totalAmount': float(line.line_total),
                'taxAmount': float(line.line_total) * 0.09,
                'totalWithTax': float(line.line_total) * 1.09,
            })
        return items

    # ----- ارسال به سامان -----

    @classmethod
    @transaction.atomic
    def send_invoice(cls, invoice_id: int) -> dict:
        """ارسال صورتحساب به سامان"""

        invoice = TaxInvoice.objects.select_for_update().get(id=invoice_id)

        if invoice.invoice_status not in [InvoiceStatus.DRAFT, InvoiceStatus.REJECTED]:
            raise ValueError(
                f'صورتحساب در وضعیت {invoice.invoice_status} قابل ارسال نیست'
            )

        token = cls._get_token()
        if not token:
            invoice.retry_count += 1
            invoice.save(update_fields=['retry_count'])
            raise Exception('احراز هویت سامان ناموفق بود')

        try:
            url = f"{cls.BASE_URL}/invoices"
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json',
            }
            payload = {
                'header': invoice.header_data,
                'body': invoice.body_data,
            }

            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()

            if data.get('uid'):
                invoice.saman_uid = data['uid']
                invoice.invoice_status = InvoiceStatus.SENT
                invoice.sent_at = timezone.now()
                invoice.save(update_fields=[
                    'saman_uid', 'invoice_status', 'sent_at', 'updated_at',
                ])
                return {'success': True, 'uid': data['uid']}

            invoice.invoice_status = InvoiceStatus.REJECTED
            invoice.rejection_reason = str(data)
            invoice.retry_count += 1
            invoice.save(update_fields=[
                'invoice_status', 'rejection_reason', 'retry_count', 'updated_at',
            ])
            return {'success': False, 'error': data}

        except Exception as e:
            logger.error(f'Saman send failed for invoice {invoice_id}: {e}')
            invoice.retry_count += 1
            invoice.rejection_reason = str(e)[:500]
            invoice.save(update_fields=[
                'retry_count', 'rejection_reason', 'updated_at',
            ])
            return {'success': False, 'error': str(e)}

    # ----- تأیید وضعیت -----

    @classmethod
    def check_status(cls, invoice_id: int) -> dict:
        """بررسی وضعیت صورتحساب در سامان"""
        invoice = TaxInvoice.objects.get(id=invoice_id)
        if not invoice.saman_uid:
            return {'status': invoice.invoice_status, 'detail': 'هنوز ارسال نشده'}

        token = cls._get_token()
        if not token:
            return {'status': 'error', 'detail': 'احراز هویت ناموفق'}

        try:
            url = f"{cls.BASE_URL}/invoices/{invoice.saman_uid}"
            headers = {'Authorization': f'Bearer {token}'}
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            data = response.json()

            # به‌روزرسانی وضعیت در دیتابیس
            saman_status = data.get('status', '').lower()
            if saman_status == 'confirmed':
                invoice.invoice_status = InvoiceStatus.CONFIRMED
                invoice.confirmed_at = timezone.now()
            elif saman_status == 'rejected':
                invoice.invoice_status = InvoiceStatus.REJECTED
                invoice.rejection_reason = data.get('rejectionReason', '')

            invoice.save()
            return {'status': invoice.invoice_status, 'saman_response': data}

        except Exception as e:
            return {'status': 'error', 'detail': str(e)}

    # ----- تلاش مجدد -----

    @classmethod
    def retry_failed_invoices(cls):
        """تلاش مجدد برای صورتحساب‌های ناموفق (در پس‌زمینه)"""
        failed = TaxInvoice.objects.filter(
            invoice_status__in=[InvoiceStatus.DRAFT, InvoiceStatus.REJECTED],
            retry_count__lt=cls.MAX_RETRY,
        )
        sent_count = 0
        for invoice in failed:
            try:
                result = cls.send_invoice(invoice.id)
                if result.get('success'):
                    sent_count += 1
            except Exception as e:
                logger.error(f'Retry failed for invoice {invoice.id}: {e}')
        return sent_count

    # ----- لغو -----

    @classmethod
    @transaction.atomic
    def cancel_invoice(cls, invoice_id: int, reason: str = '') -> TaxInvoice:
        """لغو صورتحساب در سامان"""
        invoice = TaxInvoice.objects.get(id=invoice_id)

        if invoice.invoice_status == InvoiceStatus.CONFIRMED:
            # درخواست لغو به سامان
            token = cls._get_token()
            if token and invoice.saman_uid:
                url = f"{cls.BASE_URL}/invoices/{invoice.saman_uid}/cancel"
                headers = {'Authorization': f'Bearer {token}'}
                requests.post(url, json={'reason': reason}, headers=headers, timeout=15)

        invoice.invoice_status = InvoiceStatus.CANCELED
        if reason:
            invoice.rejection_reason = reason
        invoice.save()
        return invoice
