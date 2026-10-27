"""
Barcode Service — تولید EAN-13 و QR Code
"""
from typing import Optional
from io import BytesIO
import base64
from django.db import transaction
from django.conf import settings
from apps.products.models import Barcode, BarcodeScan


class BarcodeService:
    """سرویس تولید بارکد و QR"""

    # پیشوندهای ایران (642-645)
    IRAN_PREFIX = '642'

    @classmethod
    def generate_ean13(cls, entity_id: int) -> str:
        """
        تولید بارکد EAN-13 برای یک شناسه.

        فرمت: [پیشوند ایران: 3] + [شناسه: 9] + [چک‌سام: 1] = 13 رقم
        """
        prefix = cls.IRAN_PREFIX
        body = str(entity_id).zfill(9)[:9]
        partial = prefix + body  # 12 رقم
        checksum = cls._ean13_checksum(partial)
        return partial + str(checksum)

    @staticmethod
    def _ean13_checksum(partial: str) -> int:
        """
        محاسبه رقم چک‌سام EAN-13.

        روش: مجموع (موقعیت‌های فرد × 1) + (موقعیت‌های زوج × 3)
        چک‌سام = (10 - (sum % 10)) % 10
        """
        total = 0
        for i, digit in enumerate(partial):
            d = int(digit)
            # در EAN-13: موقعیت‌های زوج (1, 3, 5, ...) × 3
            # موقعیت‌های فرد (0, 2, 4, ...) × 1
            if i % 2 == 0:
                total += d
            else:
                total += d * 3
        return (10 - (total % 10)) % 10

    @classmethod
    def generate_qr_data(cls, *, entity_type: str, entity_id: int,
                          extra_data: dict = None) -> str:
        """
        تولید داده QR Code.

        QR شامل: نوع موجودیت، شناسه، و داده‌های اضافه.
        """
        import json
        from django.conf import settings
        site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')

        data = {
            'type': entity_type,
            'id': entity_id,
            'url': f'{site_url}/api/{entity_type}/{entity_id}/',
        }
        if extra_data:
            data.update(extra_data)
        return json.dumps(data, ensure_ascii=False)

    @classmethod
    @transaction.atomic
    def create_or_get_barcode(
        cls,
        *,
        entity_type: str,
        entity_id: int,
        created_by=None,
        extra_data: dict = None,
    ) -> Barcode:
        """ساخت یا دریافت بارکد برای یک موجودیت"""

        # اگر قبلاً ساخته شده، برگرداند
        existing = Barcode.objects.filter(
            entity_type=entity_type, entity_id=entity_id,
        ).first()
        if existing:
            return existing

        # تولید بارکد EAN-13
        barcode_value = cls.generate_ean13(entity_id)

        # تولید داده QR
        qr_data = cls.generate_qr_data(
            entity_type=entity_type,
            entity_id=entity_id,
            extra_data=extra_data,
        )

        return Barcode.objects.create(
            entity_type=entity_type,
            entity_id=entity_id,
            barcode_value=barcode_value,
            qr_code_data=qr_data,
            created_by=created_by,
        )

    @classmethod
    def get_barcode_image_base64(cls, barcode_value: str) -> Optional[str]:
        """تولید تصویر بارکد به‌صورت base64"""
        try:
            import barcode
            from barcode.writer import SVGWriter

            # تولید بارکد EAN-13
            barcode_class = barcode.get_barcode_class('ean13')
            my_barcode = barcode_class(barcode_value, writer=SVGWriter())

            # ذخیره در BytesIO
            stream = BytesIO()
            my_barcode.write(stream)
            return base64.b64encode(stream.getvalue()).decode('utf-8')
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f'Failed to generate barcode image: {e}')
            return None

    @classmethod
    def get_qr_image_base64(cls, qr_data: str) -> Optional[str]:
        """تولید تصویر QR Code به‌صورت base64"""
        try:
            import qrcode
            from io import BytesIO
            import base64

            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(qr_data)
            qr.make(fit=True)

            img = qr.make_image(fill_color='black', back_color='white')
            stream = BytesIO()
            img.save(stream, format='PNG')
            return base64.b64encode(stream.getvalue()).decode('utf-8')
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f'Failed to generate QR image: {e}')
            return None

    @classmethod
    @transaction.atomic
    def scan(
        cls,
        *,
        barcode_value: str,
        scanned_by_id: int,
        context: str = 'sale_draft',
        ref_doc_type: str = '',
        ref_doc_id: int = None,
        device_id: str = '',
    ) -> dict:
        """
        اسکن بارکد از موبایل.

        Returns:
            dict با کلیدهای:
            - found: True/False
            - entity_type, entity_id (اگر یافت شد)
            - product, unit_price (اگر محصول)
        """
        # جستجوی بارکد
        try:
            barcode = Barcode.objects.get(barcode_value=barcode_value)
        except Barcode.DoesNotExist:
            # ثبت اسکن ناموفق
            BarcodeScan.objects.create(
                barcode_value=barcode_value,
                scanned_by_id=scanned_by_id,
                scan_context=context,
                ref_doc_type=ref_doc_type,
                ref_doc_id=ref_doc_id,
                device_id=device_id,
            )
            return {'found': False, 'barcode_value': barcode_value}

        # ثبت اسکن موفق
        BarcodeScan.objects.create(
            barcode=barcode,
            barcode_value=barcode_value,
            scanned_by_id=scanned_by_id,
            scan_context=context,
            ref_doc_type=ref_doc_type,
            ref_doc_id=ref_doc_id,
            device_id=device_id,
        )

        # اگر بارکد محصول، اطلاعات محصول را برگردان
        if barcode.entity_type == 'product':
            from apps.products.models import Product
            from apps.products.services import ProductService
            try:
                product = Product.objects.get(id=barcode.entity_id)
                return {
                    'found': True,
                    'entity_type': 'product',
                    'entity_id': barcode.entity_id,
                    'product': {
                        'id': product.id,
                        'code': product.code,
                        'name': product.name,
                        'unit': getattr(product.unit, 'name', None) or '',
                        'unit_code': getattr(product.unit, 'code', None) or '',
                        'default_price': str(product.default_price),
                    },
                }
            except Product.DoesNotExist:
                pass

        return {
            'found': True,
            'entity_type': barcode.entity_type,
            'entity_id': barcode.entity_id,
        }
