"""
Products Services — منطق کسب‌وکار محصولات
"""
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from .models import Product, ProductCategory, PricingRule, ProductImage, Barcode


class ProductService:
    """سرویس مدیریت محصولات"""

    @staticmethod
    @transaction.atomic
    def create_product(*, code, name, category_id, unit, shelf_life_days,
                       default_price, barcode=None, description='',
                       is_active=True, cost_center=None, created_by=None):
        """ساخت محصول جدید با تولید خودکار بارکد"""
        product = Product.objects.create(
            code=code,
            name=name,
            category_id=category_id,
            unit=unit,
            shelf_life_days=shelf_life_days,
            default_price=default_price,
            barcode=barcode,
            description=description,
            is_active=is_active,
            cost_center=cost_center,
            created_by=created_by,
        )

        # ساخت قیمت‌گذاری پیش‌فرض برای هر ۴ لایه فروشگاه
        for tier in PricingRule.StoreTier.values:
            PricingRule.objects.create(
                product=product,
                store_tier=tier,
                min_price=default_price * Decimal('0.95'),
                default_price=default_price,
                effective_date=timezone.now().date(),
                created_by=created_by,
            )

        # ساخت بارکد خودکار
        # نکته: signal با نام on_product_created در apps/products/signals.py
        # هنگام Product.objects.create بالا بارکد را هم می‌سازد.
        # اینجا فقط در صورت عدم وجود، آن را به‌روز می‌کنیم تا از UNIQUE conflict جلوگیری شود.
        if not barcode and not product.barcode:
            barcode_value = ProductService._generate_ean13(product.id)
            product.barcode = barcode_value
            product.save(update_fields=['barcode'])
            # اگر signal قبلاً ساخته، دوباره نساز
            from .models import Barcode
            if not Barcode.objects.filter(
                entity_type='product', entity_id=product.id,
            ).exists():
                Barcode.objects.create(
                    entity_type='product',
                    entity_id=product.id,
                    barcode_value=barcode_value,
                    qr_code_data=f'PROD:{product.code}:{product.id}',
                    created_by=created_by,
                )

        return product

    @staticmethod
    def _generate_ean13(product_id):
        """تولید بارکد EAN-13 بر اساس شناسه محصول"""
        # پیشوند ۶۴۲ برای ایران + ۹ رقم شناسه محصول = ۱۲ رقم
        prefix = '642'
        body = str(product_id).zfill(9)[:9]
        partial = prefix + body  # ۱۲ رقم

        # محاسبه رقم چک‌سام EAN-13
        checksum = ProductService._ean13_checksum(partial)
        return partial + str(checksum)  # ۱۳ رقم

    @staticmethod
    def _ean13_checksum(partial):
        """محاسبه رقم چک‌سام EAN-13"""
        total = 0
        for i, digit in enumerate(partial):
            d = int(digit)
            # اعداد در موقعیت فرد (1, 3, 5, ...) × 3
            if i % 2 == 0:
                total += d
            else:
                total += d * 3
        # رقم چک: کمترین عددی که total + checksum مضرب ۱۰ بشه
        return (10 - (total % 10)) % 10

    @staticmethod
    @transaction.atomic
    def add_product_image(*, product_id, image, is_primary=False,
                          alt_text='', created_by=None):
        """افزودن تصویر به محصول"""
        if is_primary:
            # حذف پرچم primary از سایر تصاویر
            ProductImage.objects.filter(
                product_id=product_id,
                is_primary=True,
            ).update(is_primary=False)

        return ProductImage.objects.create(
            product_id=product_id,
            image=image,
            is_primary=is_primary,
            alt_text=alt_text,
            created_by=created_by,
        )

    @staticmethod
    def get_price_for_store(*, product_id, store_tier):
        """قیمت مناسب برای محصول در لایه فروشگاه مشخص‌شده"""
        today = timezone.now().date()
        return PricingRule.objects.filter(
            product_id=product_id,
            store_tier=store_tier,
            effective_date__lte=today,
        ).filter(
            models.Q(expires_at__isnull=True) | models.Q(expires_at__gte=today),
        ).order_by('-effective_date').first()


# alias برای import آسان
from django.db import models  # noqa: E402 (پایین import شده تا رفرنس circular نباشه)
