"""
Payment Service — منطق پرداخت آنلاین
"""
from decimal import Decimal
from typing import Optional
from django.db import transaction
from django.utils import timezone
from django.conf import settings
from .models import PaymentTransaction, CheckPayment, CashReceipt
from .models import PaymentStatus, GatewayType
from .providers import GatewayFactory
from apps.accounting.services import JournalService
from apps.notifications.services import PushService


class PaymentService:
    """سرویس پرداخت آنلاین"""

    @staticmethod
    @transaction.atomic
    def initiate_payment(
        *,
        store_id: int,
        amount: Decimal,
        related_doc_type: str,
        related_doc_id: int,
        gateway: str = None,
        description: str = '',
        created_by=None,
    ) -> dict:
        """
        شروع پرداخت آنلاین.

        ۱. انتخاب درگاه (پیش‌فرض: زرین‌پال)
        ۲. ساخت رکورد تراکنش
        ۳. درخواست Authority از درگاه
        ۴. بازگرداندن URL redirect
        """
        amount = Decimal(amount)

        # انتخاب درگاه
        if not gateway:
            gateway = GatewayFactory.DEFAULT_GATEWAY
        gateway_instance = GatewayFactory.create_gateway(gateway)

        # ساخت رکورد تراکنش
        tx = PaymentTransaction.objects.create(
            transaction_no=PaymentService._generate_tx_number(),
            store_id=store_id,
            gateway=gateway,
            amount=amount,
            status=PaymentStatus.INITIATED,
            related_doc_type=related_doc_type,
            related_doc_id=related_doc_id,
            description=description,
            created_by=created_by,
        )

        # تنظیم callback URL
        callback_url = PaymentService._get_callback_url(gateway, tx.id)

        # درخواست Authority از درگاه
        result = gateway_instance.request_authority(
            amount=amount,
            callback_url=callback_url,
            description=description or f'پرداخت تراکنش {tx.transaction_no}',
        )

        if result.get('success'):
            tx.authority = result['authority']
            tx.gateway_response = result
            tx.save(update_fields=['authority', 'gateway_response'])

            return {
                'transaction_id': tx.id,
                'transaction_no': tx.transaction_no,
                'redirect_url': result['redirect_url'],
                'gateway': gateway,
                'amount': str(amount),
            }
        else:
            tx.status = PaymentStatus.FAILED
            tx.gateway_response = result
            tx.save(update_fields=['status', 'gateway_response'])
            raise Exception(
                f'Payment gateway failed: {result.get("error", "Unknown")}'
            )

    @staticmethod
    @transaction.atomic
    def handle_callback(
        *,
        transaction_id: int,
        status_str: str,
        authority: str = None,
    ) -> PaymentTransaction:
        """
        پردازش callback از درگاه پس از پرداخت.

        ۱. اگر status=OK → تأیید نهایی (verify)
        ۲. اگر status=NOK → ثبت به‌عنوان ناموفق
        """
        tx = PaymentTransaction.objects.select_for_update().get(id=transaction_id)

        if tx.status != PaymentStatus.INITIATED:
            logger.warning(f'Transaction {tx.id} already processed')
            return tx

        if not authority:
            authority = tx.authority

        # بررسی موفق بودن
        if status_str.upper() in ('OK', 'SUCCESS', '100', 'PAID'):
            # تأیید نهایی
            return PaymentService._verify_payment(tx, authority)
        else:
            # پرداخت ناموفق
            tx.status = PaymentStatus.FAILED
            tx.gateway_response = {'status': status_str, 'authority': authority}
            tx.save(update_fields=['status', 'gateway_response'])

            # ارسال اعلان به فروشگاه
            PushService.send_to_user(
                user_id=tx.created_by_id,
                title='پرداخت ناموفق',
                body=f'پرداخت تراکنش {tx.transaction_no} ناموفق بود.',
            )
            return tx

    @staticmethod
    @transaction.atomic
    def _verify_payment(tx: PaymentTransaction, authority: str) -> PaymentTransaction:
        """تأیید نهایی پرداخت با درگاه"""
        gateway_instance = GatewayFactory.create_gateway(tx.gateway)

        result = gateway_instance.verify(
            authority=authority,
            amount=tx.amount,
        )

        if result.get('verified'):
            tx.status = PaymentStatus.VERIFIED
            tx.ref_id = result.get('ref_id', '')
            tx.paid_at = timezone.now()
            tx.gateway_response = {**tx.gateway_response, 'verify': result}
            tx.save(update_fields=['status', 'ref_id', 'paid_at', 'gateway_response'])

            # به‌روزرسانی سند مرتبط (store_order)
            if tx.related_doc_type == 'store_order':
                from apps.store_portal.models import StoreOrder
                StoreOrder.objects.filter(id=tx.related_doc_id).update(
                    payment_status=StoreOrder.PaymentStatus.VERIFIED,
                )

            # ساخت سند حسابداری پرداخت
            try:
                JournalService.create_payment_journal(tx)
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(
                    f'Failed to create payment journal for tx {tx.id}: {e}'
                )

            # ارسال Push به فروشگاه
            try:
                PushService.send_to_user(
                    user_id=tx.created_by_id,
                    title='پرداخت دریافت شد',
                    body=f'پرداخت {tx.amount} ریال دریافت شد. کد پیگیری: {tx.ref_id}',
                    data={
                        'transaction_id': tx.id,
                        'amount': str(tx.amount),
                        'ref_id': tx.ref_id,
                    },
                    related_doc_type='payment',
                    related_doc_id=tx.id,
                )
            except Exception:
                pass

            return tx
        else:
            tx.status = PaymentStatus.FAILED
            tx.gateway_response = {**tx.gateway_response, 'verify': result}
            tx.save(update_fields=['status', 'gateway_response'])
            return tx

    @staticmethod
    @transaction.atomic
    def refund_payment(*, transaction_id: int, refunded_by=None) -> PaymentTransaction:
        """بازگشت وجه"""
        tx = PaymentTransaction.objects.get(id=transaction_id)

        if tx.status != PaymentStatus.VERIFIED:
            raise ValueError('فقط تراکنش‌های تأییدشده قابل بازگشت هستند')

        gateway_instance = GatewayFactory.create_gateway(tx.gateway)
        result = gateway_instance.refund(
            authority=tx.authority,
            amount=tx.amount,
        )

        if result.get('refunded'):
            tx.status = PaymentStatus.REFUNDED
            tx.save(update_fields=['status', 'updated_at'])

            # معکوس کردن سند حسابداری
            if tx.journal:
                JournalService.reverse_journal(
                    journal_id=tx.journal.id,
                    reason=f'بازگشت تراکنش {tx.transaction_no}',
                    reversed_by=refunded_by,
                )

        return tx

    @staticmethod
    def get_payment_history(store_id: int, status: str = None):
        """تاریخچه پرداخت‌های یک فروشگاه"""
        qs = PaymentTransaction.objects.filter(store_id=store_id)
        if status:
            qs = qs.filter(status=status)
        return qs.order_by('-created_at')

    @staticmethod
    def _get_callback_url(gateway: str, tx_id: int) -> str:
        """دریافت URL callback برای درگاه"""
        site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
        return f'{site_url}/api/payments/callback/{gateway}/?tx_id={tx_id}'

    @staticmethod
    def _generate_tx_number() -> str:
        year = timezone.now().year
        count = PaymentTransaction.objects.count() + 1
        return f'TX-{year}-{count:06d}'


import logging  # noqa
logger = logging.getLogger(__name__)
