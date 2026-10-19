"""
Production Models — بچ تولید، مصرف مواد، خروج محصول
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from core.models import BaseModel, AuditedManager
from decimal import Decimal


class ProductionBatch(BaseModel):
    """بچ تولید"""

    objects = AuditedManager()
    all_objects = models.Manager()

    class BatchStatus(models.TextChoices):
        PLANNED = 'planned', _('برنامه‌ریزی شده')
        IN_PROGRESS = 'in_progress', _('در حال اجرا')
        COMPLETED = 'completed', _('تکمیل شده')
        CANCELED = 'canceled', _('لغو شده')

    batch_no = models.CharField(max_length=50, unique=True, verbose_name=_('شماره بچ'))
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.RESTRICT,
        related_name='production_batches',
        verbose_name=_('محصول نهایی'),
    )
    planned_qty = models.DecimalField(
        max_digits=14, decimal_places=3,
        verbose_name=_('مقدار برنامه‌ریزی‌شده'),
    )
    actual_qty = models.DecimalField(
        max_digits=14, decimal_places=3,
        default=Decimal('0'),
        verbose_name=_('مقدار واقعی تولیدشده'),
    )
    waste_qty = models.DecimalField(
        max_digits=14, decimal_places=3,
        default=Decimal('0'),
        verbose_name=_('ضایعات'),
    )
    start_at = models.DateTimeField(
        null=True, blank=True,
        verbose_name=_('زمان شروع'),
    )
    end_at = models.DateTimeField(
        null=True, blank=True,
        verbose_name=_('زمان پایان'),
    )
    status = models.CharField(
        max_length=20,
        choices=BatchStatus.choices,
        default=BatchStatus.PLANNED,
        verbose_name=_('وضعیت'),
    )
    weighted_avg_cost = models.DecimalField(
        max_digits=18, decimal_places=4,
        default=Decimal('0'),
        verbose_name=_('بهای تمام‌شده میانگین موزون'),
    )
    notes = models.TextField(blank=True, verbose_name=_('یادداشت'))

    class Meta:
        db_table = 'production_batches'
        verbose_name = _('بچ تولید')
        verbose_name_plural = _('بچ‌های تولید')
        ordering = ['-start_at', '-id']
        indexes = [
            models.Index(fields=['product']),
            models.Index(fields=['status']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(planned_qty__gt=0),
                name='batch_planned_qty_positive',
            ),
            models.CheckConstraint(
                check=models.Q(actual_qty__gte=0) & models.Q(waste_qty__gte=0),
                name='batch_qty_nonneg',
            ),
        ]

    def __str__(self):
        return f'{self.batch_no} - {self.product.code} ({self.status})'

    @property
    def efficiency(self):
        """راندمان تولید = واقعی / برنامه‌ریزی‌شده × ۱۰۰"""
        if self.planned_qty == 0:
            return 0
        return (self.actual_qty / self.planned_qty) * 100

    @property
    def total_consumption_cost(self):
        """مجموع هزینه مواد مصرف‌شده"""
        return sum(
            (c.qty_consumed * c.cost_at_consumption for c in self.consumptions.all()),
            Decimal('0'),
        )


class ProductionConsumption(BaseModel):
    """مصرف مواد اولیه برای هر بچ"""

    batch = models.ForeignKey(
        ProductionBatch,
        on_delete=models.CASCADE,
        related_name='consumptions',
        verbose_name=_('بچ'),
    )
    material_lot = models.ForeignKey(
        'inventory.InventoryLot',
        on_delete=models.RESTRICT,
        related_name='consumptions',
        verbose_name=_('لات ماده اولیه'),
    )
    qty_consumed = models.DecimalField(
        max_digits=14, decimal_places=3,
        verbose_name=_('مقدار مصرف‌شده'),
    )
    cost_at_consumption = models.DecimalField(
        max_digits=18, decimal_places=4,
        verbose_name=_('هزینه در لحظه مصرف'),
        help_text=_('میانگین موزون لات ماده اولیه'),
    )
    consumed_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('زمان مصرف'),
    )

    class Meta:
        db_table = 'production_consumption'
        verbose_name = _('مصرف مواد')
        verbose_name_plural = _('مصرف‌های مواد')
        ordering = ['-consumed_at']
        indexes = [
            models.Index(fields=['batch']),
            models.Index(fields=['material_lot']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(qty_consumed__gt=0),
                name='consumption_qty_positive',
            ),
        ]

    def __str__(self):
        return f'{self.batch.batch_no} ← {self.material_lot.product.code}: {self.qty_consumed}'

    @property
    def total_cost(self):
        """هزینه کل این مصرف"""
        return self.qty_consumed * self.cost_at_consumption


class ProductionOutput(BaseModel):
    """خروج محصول نهایی از بچ تولید"""

    batch = models.ForeignKey(
        ProductionBatch,
        on_delete=models.CASCADE,
        related_name='outputs',
        verbose_name=_('بچ'),
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.RESTRICT,
        related_name='production_outputs',
        verbose_name=_('محصول نهایی'),
    )
    qty_produced = models.DecimalField(
        max_digits=14, decimal_places=3,
        verbose_name=_('مقدار تولیدشده'),
    )
    qty_waste = models.DecimalField(
        max_digits=14, decimal_places=3,
        default=Decimal('0'),
        verbose_name=_('ضایعات'),
    )
    lot = models.ForeignKey(
        'inventory.InventoryLot',
        on_delete=models.RESTRICT,
        related_name='production_outputs',
        verbose_name=_('لات تولیدشده'),
        help_text=_('لات جدیدی که در نتیجه این خروج ساخته شده'),
    )
    output_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('زمان خروج'),
    )

    class Meta:
        db_table = 'production_outputs'
        verbose_name = _('خروج تولید')
        verbose_name_plural = _('خروج‌های تولید')
        ordering = ['-output_at']
        indexes = [
            models.Index(fields=['batch']),
            models.Index(fields=['lot']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(qty_produced__gt=0) & models.Q(qty_waste__gte=0),
                name='output_qty_positive',
            ),
        ]

    def __str__(self):
        return f'{self.batch.batch_no} → Lot {self.lot.batch_no}: {self.qty_produced}'
