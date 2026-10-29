"""
Sales Models — SalesHeaders/Lines, ReturnHeaders/Lines
ساختار Header-Line با پشتیبانی امانی/قطعی
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from core.models import BaseModel, AuditedManager
from django.db.models import F


class SalesHeader(BaseModel):
    """سند فروش (امانی/قطعی)"""

    objects = AuditedManager()
    all_objects = models.Manager()

    class SalesType(models.TextChoices):
        CONSIGNMENT = 'consignment', _('امانی')
        FIRM = 'firm', _('قطعی')

    class SalesStatus(models.TextChoices):
        PENDING = 'pending', _('در انتظار')
        REVIEWING = 'reviewing', _('در حال بررسی')
        APPROVED = 'approved', _('تأیید شد')
        REJECTED = 'rejected', _('رد شد')
        POSTED = 'posted', _('ثبت شد')
        CANCELED = 'canceled', _('لغو شد')

    PAYMENT_CHOICES = [
        ('cash', _('نقد')),
        ('check', _('چک')),
        ('card', _('کارت')),
        ('bank_transfer', _('انتقال بانکی')),
    ]

    sale_no = models.CharField(max_length=50, unique=True, verbose_name=_('شماره فروش'))
    store = models.ForeignKey(
        'partners.Store',
        on_delete=models.RESTRICT,
        related_name='sales',
        verbose_name=_('فروشگاه'),
    )
    sale_date = models.DateField(verbose_name=_('تاریخ فروش'))
    sales_type = models.CharField(
        max_length=20,
        choices=SalesType.choices,
        verbose_name=_('نوع فروش'),
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_CHOICES,
        default='cash',
        verbose_name=_('نحوه دریافت وجه'),
    )
    paid_amount = models.DecimalField(
        max_digits=18, decimal_places=4,
        default=0,
        verbose_name=_('مبلغ دریافت‌شده'),
    )
    total_amount = models.DecimalField(
        max_digits=18, decimal_places=4,
        default=0,
        verbose_name=_('مبلغ کل'),
    )
    total_cost = models.DecimalField(
        max_digits=18, decimal_places=4,
        default=0,
        verbose_name=_('بهای تمام‌شده کل'),
    )
    status = models.CharField(
        max_length=20,
        choices=SalesStatus.choices,
        default=SalesStatus.POSTED,
        verbose_name=_('وضعیت'),
    )
    journal = models.ForeignKey(
        'accounting.JournalHeader',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='sales',
        verbose_name=_('سند حسابداری'),
    )
    tax_invoice = models.ForeignKey(
        'saman_tax.TaxInvoice',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='sales',
        verbose_name=_('صورتحساب سامان'),
    )
    dispatch = models.ForeignKey(
        'dispatch.DispatchHeader',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='sales',
        verbose_name=_('سند پخش'),
    )
    distributor = models.ForeignKey(
        'partners.Distributor',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='sales',
        verbose_name=_('عامل پخش'),
    )
    notes = models.TextField(blank=True, verbose_name=_('یادداشت'))

    class Meta:
        db_table = 'sales_headers'
        verbose_name = _('فروش')
        verbose_name_plural = _('فروش‌ها')
        ordering = ['-sale_date', '-id']
        indexes = [
            models.Index(fields=['store', 'sale_date']),
            models.Index(fields=['sales_type']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f'{self.sale_no} - {self.store.name} - {self.total_amount}'

    @property
    def total_profit(self):
        """سود کل = مبلغ فروش - بهای تمام‌شده"""
        return self.total_amount - self.total_cost

    def recalculate_totals(self):
        """محاسبه مجدد مبلغ کل و بهای تمام‌شده از روی خطوط"""
        lines = self.lines.all()
        self.total_amount = sum(line.line_total for line in lines) or 0
        self.total_cost = sum(line.unit_cost * line.qty for line in lines) or 0
        self.save(update_fields=['total_amount', 'total_cost', 'updated_at'])


class SalesLine(BaseModel):
    """اقلام فروش با لات مشخص (FEFO)"""

    sale = models.ForeignKey(
        SalesHeader,
        on_delete=models.CASCADE,
        related_name='lines',
        verbose_name=_('سند فروش'),
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.RESTRICT,
        related_name='sales_lines',
        verbose_name=_('محصول'),
    )
    lot = models.ForeignKey(
        'inventory.InventoryLot',
        on_delete=models.RESTRICT,
        related_name='sales_lines',
        verbose_name=_('لات'),  # ⭐ ردیابی FEFO
    )
    qty = models.DecimalField(
        max_digits=14, decimal_places=3,
        verbose_name=_('تعداد'),
    )
    unit_price = models.DecimalField(
        max_digits=18, decimal_places=4,
        verbose_name=_('قیمت واحد فروش'),
    )
    unit_cost = models.DecimalField(
        max_digits=18, decimal_places=4,
        verbose_name=_('بهای تمام‌شده واحد'),
        help_text=_('میانگین موزون لات'),
    )

    class Meta:
        db_table = 'sales_lines'
        verbose_name = _('قلم فروش')
        verbose_name_plural = _('اقلام فروش')
        indexes = [
            models.Index(fields=['sale']),
            models.Index(fields=['lot']),
            models.Index(fields=['product']),
        ]

    def __str__(self):
        return f'{self.product.code} x {self.qty}'

    @property
    def line_total(self):
        """جمع این قلم = تعداد × قیمت"""
        return self.qty * self.unit_price

    @property
    def line_cost(self):
        """بهای تمام‌شده این قلم"""
        return self.qty * self.unit_cost

    @property
    def line_profit(self):
        """سود این قلم"""
        return self.line_total - self.line_cost


class ReturnHeader(BaseModel):
    """سند برگشت از فروشگاه"""

    objects = AuditedManager()
    all_objects = models.Manager()

    return_no = models.CharField(max_length=50, unique=True, verbose_name=_('شماره برگشت'))
    store = models.ForeignKey(
        'partners.Store',
        on_delete=models.RESTRICT,
        related_name='returns',
        verbose_name=_('فروشگاه'),
    )
    return_date = models.DateField(verbose_name=_('تاریخ برگشت'))
    original_sale = models.ForeignKey(
        SalesHeader,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='returns',
        verbose_name=_('فروش اصلی'),
    )
    total_qty = models.DecimalField(
        max_digits=14, decimal_places=3,
        default=0,
        verbose_name=_('تعداد کل'),
    )
    reason = models.TextField(blank=True, verbose_name=_('دلیل'))
    status = models.CharField(
        max_length=20,
        default='pending',
        verbose_name=_('وضعیت'),
    )
    journal = models.ForeignKey(
        'accounting.JournalHeader',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='returns',
        verbose_name=_('سند معکوس حسابداری'),
    )

    class Meta:
        db_table = 'return_headers'
        verbose_name = _('برگشت')
        verbose_name_plural = _('برگشت‌ها')
        ordering = ['-return_date', '-id']
        indexes = [
            models.Index(fields=['store', 'return_date']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f'{self.return_no} - {self.store.name}'


class ReturnLine(BaseModel):
    """اقلام برگشت با وضعیت"""

    class ReturnCondition(models.TextChoices):
        SELLABLE = 'sellable', _('قابل فروش مجدد')
        EXPIRED = 'expired', _('منقضی')
        DAMAGED = 'damaged', _('آسیب‌دیده')
        NEAR_EXPIRY = 'near_expiry', _('نزدیک به انقضا')

    return_header = models.ForeignKey(
        ReturnHeader,
        on_delete=models.CASCADE,
        related_name='lines',
        verbose_name=_('سند برگشت'),
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.RESTRICT,
        related_name='return_lines',
        verbose_name=_('محصول'),
    )
    lot = models.ForeignKey(
        'inventory.InventoryLot',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='return_lines',
        verbose_name=_('لات'),
    )
    qty = models.DecimalField(
        max_digits=14, decimal_places=3,
        verbose_name=_('تعداد'),
    )
    condition = models.CharField(
        max_length=20,
        choices=ReturnCondition.choices,
        default=ReturnCondition.SELLABLE,
        verbose_name=_('وضعیت'),
    )
    notes = models.TextField(blank=True, verbose_name=_('یادداشت'))

    class Meta:
        db_table = 'return_lines'
        verbose_name = _('قلم برگشت')
        verbose_name_plural = _('اقلام برگشت')
        indexes = [
            models.Index(fields=['return_header']),
            models.Index(fields=['condition']),
        ]

    def __str__(self):
        return f'{self.product.code} x {self.qty} ({self.condition})'
