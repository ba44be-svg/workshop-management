"""
Inventory Models — قلب FEFO
Warehouse, InventoryLot, InventoryMovement, StockBalance
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from core.models import BaseModel, AuditedManager


class Warehouse(BaseModel):
    """انبار اصلی + مجازی هر فروشگاه"""

    objects = AuditedManager()
    all_objects = models.Manager()

    class WarehouseType(models.TextChoices):
        MAIN = 'main', _('اصلی')
        STORE = 'store', _('فروشگاه')
        VIRTUAL = 'virtual', _('مجازی')

    code = models.CharField(max_length=50, unique=True, verbose_name=_('کد'))
    name = models.CharField(max_length=200, verbose_name=_('نام'))
    type = models.CharField(
        max_length=20,
        choices=WarehouseType.choices,
        verbose_name=_('نوع'),
    )
    store = models.ForeignKey(
        'partners.Store',
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='warehouses',
        verbose_name=_('فروشگاه'),
    )
    address = models.TextField(blank=True, verbose_name=_('آدرس'))
    is_active = models.BooleanField(default=True, verbose_name=_('فعال'))

    class Meta:
        db_table = 'warehouses'
        verbose_name = _('انبار')
        verbose_name_plural = _('انبارها')
        ordering = ['code']
        constraints = [
            # اگر type=store پس store_id نباید NULL باشد
            models.CheckConstraint(
                check=(
                    models.Q(type='store', store__isnull=False) |
                    models.Q(type__in=['main', 'virtual'], store__isnull=True)
                ),
                name='warehouse_type_store_consistency',
            ),
        ]

    def __str__(self):
        return f'{self.code} - {self.name}'


class InventoryLot(BaseModel):
    """لات موجودی — هر بچ تولید یک لات"""

    objects = AuditedManager()
    all_objects = models.Manager()

    class LotStatus(models.TextChoices):
        ACTIVE = 'active', _('فعال')
        EXPIRED = 'expired', _('منقضی')
        DISPOSED = 'disposed', _('ضایعات')
        RETURNED = 'returned', _('برگشتی')

    product = models.ForeignKey(
        'products.Product',
        on_delete=models.RESTRICT,
        related_name='lots',
        verbose_name=_('محصول'),
    )
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.RESTRICT,
        related_name='lots',
        verbose_name=_('انبار'),
    )
    batch_no = models.CharField(max_length=50, verbose_name=_('شماره بچ'))
    production_date = models.DateField(verbose_name=_('تاریخ تولید'))
    expiry_date = models.DateField(verbose_name=_('تاریخ انقضا'))  # ⭐ معیار FEFO
    initial_qty = models.DecimalField(
        max_digits=14, decimal_places=3,
        verbose_name=_('مقدار اولیه'),
    )
    current_qty = models.DecimalField(
        max_digits=14, decimal_places=3,
        default=0,
        verbose_name=_('مقدار فعلی'),
    )
    weighted_avg_cost = models.DecimalField(
        max_digits=18, decimal_places=4,
        default=0,
        verbose_name=_('بهای تمام‌شده میانگین موزون'),
    )
    status = models.CharField(
        max_length=20,
        choices=LotStatus.choices,
        default=LotStatus.ACTIVE,
        verbose_name=_('وضعیت'),
    )
    production_batch = models.ForeignKey(
        'production.ProductionBatch',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='lots',
        verbose_name=_('بچ تولید مرجع'),
    )

    class Meta:
        db_table = 'inventory_lots'
        verbose_name = _('لات انبار')
        verbose_name_plural = _('لات‌های انبار')
        unique_together = ('product', 'warehouse', 'batch_no')
        indexes = [
            # ⭐ ایندکس FEFO — مهم‌ترین ایندکس سیستم
            models.Index(
                fields=['product', 'warehouse', 'expiry_date', 'current_qty'],
                name='idx_lots_fefo',
            ),
            models.Index(fields=['expiry_date']),
            models.Index(fields=['status']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(initial_qty__gte=0),
                name='lot_initial_qty_nonneg',
            ),
            models.CheckConstraint(
                check=models.Q(current_qty__gte=0),
                name='lot_current_qty_nonneg',
            ),
            models.CheckConstraint(
                check=models.Q(expiry_date__gte=models.F('production_date')),
                name='lot_expiry_after_production',
            ),
        ]

    def __str__(self):
        return f'Lot {self.batch_no} - {self.product.code} ({self.current_qty})'

    @property
    def days_to_expiry(self):
        """تعداد روز تا انقضا"""
        from django.utils import timezone
        return (self.expiry_date - timezone.now().date()).days


class InventoryMovement(BaseModel):
    """حرکت‌های انبار — تاریخچه کامل"""

    class MovementType(models.TextChoices):
        IN = 'in', _('ورود')
        OUT = 'out', _('خروج')
        TRANSFER = 'transfer', _('انتقال')
        RETURN = 'return', _('برگشت')
        ADJUSTMENT = 'adjustment', _('تعدیل')
        PRODUCTION = 'production', _('تولید')

    lot = models.ForeignKey(
        InventoryLot,
        on_delete=models.RESTRICT,
        related_name='movements',
        verbose_name=_('لات'),
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.RESTRICT,
        related_name='movements',
        verbose_name=_('محصول'),
    )
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.RESTRICT,
        related_name='movements',
        verbose_name=_('انبار'),
    )
    movement_type = models.CharField(
        max_length=20,
        choices=MovementType.choices,
        verbose_name=_('نوع حرکت'),
    )
    qty = models.DecimalField(
        max_digits=14, decimal_places=3,
        verbose_name=_('مقدار'),
        help_text=_('مثبت برای ورود، منفی برای خروج'),
    )
    unit_cost = models.DecimalField(
        max_digits=18, decimal_places=4,
        null=True, blank=True,
        verbose_name=_('هزینه واحد'),
    )
    ref_doc_type = models.CharField(
        max_length=50,
        verbose_name=_('نوع سند مرجع'),
        help_text='sale, production, transfer, return, etc.',
    )
    ref_doc_id = models.BigIntegerField(
        null=True, blank=True,
        verbose_name=_('شناسه سند مرجع'),
    )

    class Meta:
        db_table = 'inventory_movements'
        verbose_name = _('حرکت انبار')
        verbose_name_plural = _('حرکت‌های انبار')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['lot']),
            models.Index(fields=['product', 'warehouse']),
            models.Index(fields=['ref_doc_type', 'ref_doc_id']),
            models.Index(fields=['created_at']),
        ]
        constraints = [
            models.CheckConstraint(
                check=~models.Q(qty=0),
                name='movement_qty_nonzero',
            ),
        ]

    def __str__(self):
        return f'{self.movement_type} {self.qty} - {self.product.code}'


class StockBalance(models.Model):
    """موجودی تجمیعی — Cache برای عملکرد بالا"""

    product = models.ForeignKey(
        'products.Product',
        on_delete=models.RESTRICT,
        related_name='balances',
        verbose_name=_('محصول'),
    )
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.RESTRICT,
        related_name='balances',
        verbose_name=_('انبار'),
    )
    total_qty = models.DecimalField(
        max_digits=14, decimal_places=3,
        default=0,
        verbose_name=_('موجودی کل'),
    )
    total_value = models.DecimalField(
        max_digits=18, decimal_places=4,
        default=0,
        verbose_name=_('ارزش کل'),
    )
    last_lot = models.ForeignKey(
        InventoryLot,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='+',
        verbose_name=_('آخرین لات تعامل‌شده'),
    )
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('به‌روزرسانی'))

    class Meta:
        db_table = 'stock_balances'
        verbose_name = _('موجودی تجمیعی')
        verbose_name_plural = _('موجودی‌های تجمیعی')
        unique_together = ('product', 'warehouse')
        indexes = [
            models.Index(fields=['product', 'warehouse']),
        ]

    def __str__(self):
        return f'{self.product.code} @ {self.warehouse.code}: {self.total_qty}'
