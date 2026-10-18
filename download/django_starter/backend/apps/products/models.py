"""
Products Models — Product, ProductCategory, PricingRule, ProductImage, Barcode
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from core.models import BaseModel, AuditedManager
from django.utils import timezone


class ProductCategory(BaseModel):
    """دسته‌بندی محصولات (درختی)"""

    objects = AuditedManager()
    all_objects = models.Manager()  # شامل soft-deleted

    code = models.CharField(max_length=50, unique=True, verbose_name=_('کد'))
    name = models.CharField(max_length=200, verbose_name=_('نام'))
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='children',
        verbose_name=_('دسته والد'),
    )
    level = models.PositiveSmallIntegerField(default=1, verbose_name=_('سطح'))
    is_active = models.BooleanField(default=True, verbose_name=_('فعال'))

    class Meta:
        db_table = 'product_categories'
        verbose_name = _('دسته محصول')
        verbose_name_plural = _('دسته‌بندی محصولات')
        ordering = ['code']
        indexes = [
            models.Index(fields=['parent']),
            models.Index(fields=['code']),
        ]

    def __str__(self):
        return f'{self.code} - {self.name}'

    def save(self, *args, **kwargs):
        """محاسبه خودکار level بر اساس parent"""
        if self.parent:
            self.level = self.parent.level + 1
        else:
            self.level = 1
        super().save(*args, **kwargs)


class Product(BaseModel):
    """محصول"""

    objects = AuditedManager()
    all_objects = models.Manager()

    code = models.CharField(max_length=50, unique=True, verbose_name=_('کد'))
    name = models.CharField(max_length=200, verbose_name=_('نام'))
    category = models.ForeignKey(
        ProductCategory,
        on_delete=models.RESTRICT,
        related_name='products',
        verbose_name=_('دسته'),
    )
    unit = models.CharField(max_length=20, default='عدد', verbose_name=_('واحد'))
    shelf_life_days = models.PositiveSmallIntegerField(
        verbose_name=_('مدت ماندگاری (روز)'),
        help_text=_('تعداد روز از تولید تا انقضا'),
    )
    default_price = models.DecimalField(
        max_digits=18, decimal_places=4,
        verbose_name=_('قیمت پایه (ریال)'),
    )
    cost_center = models.ForeignKey(
        'accounting.CostCenter',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='products',
        verbose_name=_('مرکز هزینه'),
    )
    barcode = models.CharField(
        max_length=50, unique=True, null=True, blank=True,
        verbose_name=_('بارکد EAN-13'),
    )
    description = models.TextField(blank=True, verbose_name=_('توضیحات'))
    is_active = models.BooleanField(default=True, verbose_name=_('فعال'))

    class Meta:
        db_table = 'products'
        verbose_name = _('محصول')
        verbose_name_plural = _('محصولات')
        ordering = ['code']
        indexes = [
            models.Index(fields=['category']),
            models.Index(fields=['barcode']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f'{self.code} - {self.name}'

    @property
    def default_image(self):
        """تصویر پیش‌فرض محصول"""
        return self.images.filter(is_primary=True).first() or self.images.first()


class ProductImage(BaseModel):
    """تصاویر محصول"""

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name=_('محصول'),
    )
    image = models.ImageField(
        upload_to='products/%Y/%m/',
        verbose_name=_('تصویر'),
    )
    alt_text = models.CharField(max_length=200, blank=True, verbose_name=_('متن جایگزین'))
    is_primary = models.BooleanField(default=False, verbose_name=_('تصویر اصلی'))
    sort_order = models.PositiveSmallIntegerField(default=0, verbose_name=_('ترتیب'))

    class Meta:
        db_table = 'product_images'
        verbose_name = _('تصویر محصول')
        verbose_name_plural = _('تصاویر محصولات')
        ordering = ['sort_order', '-is_primary']

    def __str__(self):
        return f'{self.product.code} - Image {self.id}'


class PricingRule(BaseModel):
    """قیمت‌گذاری پویا بر اساس لایه فروشگاه"""

    class StoreTier(models.TextChoices):
        REGULAR = 'regular', _('عادی')
        SILVER = 'silver', _('نقره‌ای')
        GOLD = 'gold', _('طلایی')
        PLATINUM = 'platinum', _('پلاتین')

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='pricing_rules',
        verbose_name=_('محصول'),
    )
    store_tier = models.CharField(
        max_length=20,
        choices=StoreTier.choices,
        verbose_name=_('لایه فروشگاه'),
    )
    min_price = models.DecimalField(
        max_digits=18, decimal_places=4,
        verbose_name=_('حداقل قیمت'),
    )
    default_price = models.DecimalField(
        max_digits=18, decimal_places=4,
        verbose_name=_('قیمت پیش‌فرض'),
    )
    effective_date = models.DateField(
        default=timezone.now,
        verbose_name=_('تاریخ شروع اعتبار'),
    )
    expires_at = models.DateField(
        null=True, blank=True,
        verbose_name=_('تاریخ انقضای قیمت'),
    )

    class Meta:
        db_table = 'pricing_rules'
        verbose_name = _('قیمت‌گذاری')
        verbose_name_plural = _('قیمت‌گذاری‌ها')
        unique_together = ('product', 'store_tier', 'effective_date')
        indexes = [
            models.Index(fields=['product', 'store_tier', 'effective_date']),
        ]

    def __str__(self):
        return f'{self.product.code} - {self.get_store_tier_display()}: {self.default_price}'


class Barcode(models.Model):
    """بارکد و QR Code برای هر موجودیت"""

    class EntityType(models.TextChoices):
        PRODUCT = 'product', _('محصول')
        LOT = 'lot', _('لات')
        SALES_ORDER = 'sales_order', _('سفارش فروش')
        STORE_ORDER = 'store_order', _('سفارش فروشگاه')
        DISPATCH = 'dispatch', _('سند پخش')

    entity_type = models.CharField(
        max_length=20,
        choices=EntityType.choices,
        verbose_name=_('نوع موجودیت'),
    )
    entity_id = models.BigIntegerField(verbose_name=_('شناسه موجودیت'))
    barcode_value = models.CharField(
        max_length=50, unique=True,
        verbose_name=_('مقدار بارکد'),
    )
    qr_code_data = models.TextField(verbose_name=_('داده QR'))
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='+',
    )

    class Meta:
        db_table = 'barcodes'
        verbose_name = _('بارکد')
        verbose_name_plural = _('بارکدها')
        unique_together = ('entity_type', 'entity_id')
        indexes = [
            models.Index(fields=['entity_type', 'entity_id']),
            models.Index(fields=['barcode_value']),
        ]

    def __str__(self):
        return f'{self.barcode_value} ({self.entity_type}:{self.entity_id})'


class BarcodeScan(models.Model):
    """لاگ اسکن‌های بارکد از موبایل"""

    barcode = models.ForeignKey(
        Barcode,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name=_('بارکد'),
    )
    barcode_value = models.CharField(max_length=50, verbose_name=_('مقدار اسکن‌شده'))
    scanned_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='+',
        verbose_name=_('کاربر اسکن‌کننده'),
    )
    scan_context = models.CharField(
        max_length=50, blank=True,
        verbose_name=_('محتوا'),
        help_text='sale_draft, transfer, inventory_check',
    )
    ref_doc_type = models.CharField(max_length=50, blank=True, verbose_name=_('نوع سند مرجع'))
    ref_doc_id = models.BigIntegerField(null=True, blank=True, verbose_name=_('شناسه سند مرجع'))
    scanned_at = models.DateTimeField(auto_now_add=True, verbose_name=_('زمان اسکن'))
    device_id = models.CharField(max_length=100, blank=True, verbose_name=_('شناسه دستگاه'))

    class Meta:
        db_table = 'barcode_scans'
        verbose_name = _('اسکن بارکد')
        verbose_name_plural = _('اسکن‌های بارکد')
        indexes = [
            models.Index(fields=['scanned_by', 'scanned_at']),
            models.Index(fields=['barcode_value']),
        ]

    def __str__(self):
        return f'{self.barcode_value} by {self.scanned_by}'
