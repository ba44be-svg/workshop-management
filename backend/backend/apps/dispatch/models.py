"""
Dispatch Models — Vehicle, Route, DispatchHeader, DispatchLine
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.db.models import F
from core.models import BaseModel, AuditedManager


class Vehicle(BaseModel):
    """خودروهای پخش"""

    objects = AuditedManager()
    all_objects = models.Manager()

    plate = models.CharField(max_length=20, unique=True, verbose_name=_('پلاک'))
    capacity = models.DecimalField(
        max_digits=14, decimal_places=3,
        verbose_name=_('ظرفیت'),
    )
    driver_name = models.CharField(
        max_length=200, blank=True,
        verbose_name=_('نام راننده'),
    )
    fuel_card = models.CharField(
        max_length=50, blank=True,
        verbose_name=_('کارت سوخت'),
    )
    is_active = models.BooleanField(default=True, verbose_name=_('فعال'))

    class Meta:
        db_table = 'vehicles'
        verbose_name = _('خودرو')
        verbose_name_plural = _('خودروها')
        ordering = ['plate']

    def __str__(self):
        return f'{self.plate} - {self.driver_name or "—"}'


class Route(BaseModel):
    """مسیر هر عامل در هر روز هفته"""

    objects = AuditedManager()
    all_objects = models.Manager()

    class DaysOfWeek(models.IntegerChoices):
        SATURDAY = 0, _('شنبه')
        SUNDAY = 1, _('یکشنبه')
        MONDAY = 2, _('دوشنبه')
        TUESDAY = 3, _('سه‌شنبه')
        WEDNESDAY = 4, _('چهارشنبه')
        THURSDAY = 5, _('پنجشنبه')
        FRIDAY = 6, _('جمعه')

    distributor = models.ForeignKey(
        'partners.Distributor',
        on_delete=models.CASCADE,
        related_name='routes',
        verbose_name=_('عامل پخش'),
    )
    day_of_week = models.PositiveSmallIntegerField(
        choices=DaysOfWeek.choices,
        verbose_name=_('روز هفته'),
    )
    store_sequence = models.JSONField(
        default=list,
        verbose_name=_('ترتیب فروشگاه‌ها'),
        help_text='[{store_id, store_name, expected_time}]',
    )
    is_active = models.BooleanField(default=True, verbose_name=_('فعال'))

    class Meta:
        db_table = 'routes'
        verbose_name = _('مسیر')
        verbose_name_plural = _('مسیرها')
        unique_together = ('distributor', 'day_of_week')
        ordering = ['distributor', 'day_of_week']
        indexes = [
            models.Index(fields=['distributor', 'day_of_week']),
        ]

    def __str__(self):
        return f'{self.distributor.code} - {self.get_day_of_week_display()}'


class DispatchHeader(BaseModel):
    """سند پخش به عامل"""

    objects = AuditedManager()
    all_objects = models.Manager()

    class DispatchStatus(models.TextChoices):
        PENDING = 'pending', _('در انتظار')
        IN_DELIVERY = 'in_delivery', _('در حال تحویل')
        ARRIVED = 'arrived', _('تحویل شد')
        CANCELED = 'canceled', _('لغو شد')

    dispatch_no = models.CharField(max_length=50, unique=True, verbose_name=_('شماره پخش'))
    distributor = models.ForeignKey(
        'partners.Distributor',
        on_delete=models.RESTRICT,
        related_name='dispatches',
        verbose_name=_('عامل پخش'),
    )
    dispatch_date = models.DateField(verbose_name=_('تاریخ پخش'))
    total_qty = models.DecimalField(
        max_digits=14, decimal_places=3,
        default=0,
        verbose_name=_('مجموع تعداد'),
    )
    total_amount = models.DecimalField(
        max_digits=18, decimal_places=4,
        default=0,
        verbose_name=_('مبلغ کل'),
    )
    status = models.CharField(
        max_length=20,
        choices=DispatchStatus.choices,
        default=DispatchStatus.PENDING,
        verbose_name=_('وضعیت'),
    )
    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='dispatches',
        verbose_name=_('خودرو'),
    )
    notes = models.TextField(blank=True, verbose_name=_('یادداشت'))
    journal = models.ForeignKey(
        'accounting.JournalHeader',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='dispatches',
        verbose_name=_('سند حسابداری'),
        help_text=_('سند حسابداری خودکار متصل به این پخش'),
    )

    class Meta:
        db_table = 'dispatch_headers'
        verbose_name = _('سند پخش')
        verbose_name_plural = _('اسناد پخش')
        ordering = ['-dispatch_date', '-id']
        indexes = [
            models.Index(fields=['distributor', 'dispatch_date']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f'{self.dispatch_no} - {self.distributor.name} ({self.status})'

    def recalculate_totals(self):
        """محاسبه مجدد مجموع‌ها از روی خطوط"""
        lines = self.lines.all()
        self.total_qty = sum(line.qty for line in lines) or 0
        self.total_amount = sum(line.line_total for line in lines) or 0
        self.save(update_fields=['total_qty', 'total_amount', 'updated_at'])


class DispatchLine(BaseModel):
    """اقلام پخش با مقصد هر فروشگاه"""

    dispatch = models.ForeignKey(
        DispatchHeader,
        on_delete=models.CASCADE,
        related_name='lines',
        verbose_name=_('سند پخش'),
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.RESTRICT,
        related_name='dispatch_lines',
        verbose_name=_('محصول'),
    )
    lot = models.ForeignKey(
        'inventory.InventoryLot',
        on_delete=models.RESTRICT,
        related_name='dispatch_lines',
        verbose_name=_('لات'),
    )
    qty = models.DecimalField(
        max_digits=14, decimal_places=3,
        verbose_name=_('تعداد'),
    )
    unit_price = models.DecimalField(
        max_digits=18, decimal_places=4,
        verbose_name=_('قیمت واحد'),
    )
    dest_store = models.ForeignKey(
        'partners.Store',
        on_delete=models.RESTRICT,
        related_name='incoming_dispatches',
        verbose_name=_('فروشگاه مقصد'),
    )

    class Meta:
        db_table = 'dispatch_lines'
        verbose_name = _('قلم پخش')
        verbose_name_plural = _('اقلام پخش')
        indexes = [
            models.Index(fields=['dispatch']),
            models.Index(fields=['dest_store']),
            models.Index(fields=['lot']),
        ]

    def __str__(self):
        return f'{self.product.code} x {self.qty} → {self.dest_store.name}'

    @property
    def line_total(self):
        """جمع این قلم"""
        return self.qty * self.unit_price


class SalespersonVisit(BaseModel):
    """ردیابی سرکشی روزانه عامل"""

    distributor = models.ForeignKey(
        'partners.Distributor',
        on_delete=models.RESTRICT,
        related_name='visits',
        verbose_name=_('عامل پخش'),
    )
    store = models.ForeignKey(
        'partners.Store',
        on_delete=models.RESTRICT,
        related_name='visits',
        verbose_name=_('فروشگاه'),
    )
    visit_date = models.DateField(verbose_name=_('تاریخ سرکشی'))
    check_in_time = models.DateTimeField(
        null=True, blank=True,
        verbose_name=_('زمان ورود'),
    )
    check_out_time = models.DateTimeField(
        null=True, blank=True,
        verbose_name=_('زمان خروج'),
    )
    sales_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_('تعداد فروش'),
    )
    sales_amount = models.DecimalField(
        max_digits=18, decimal_places=4,
        default=0,
        verbose_name=_('مبلغ فروش'),
    )
    geo_lat_checkin = models.DecimalField(
        max_digits=10, decimal_places=7, null=True, blank=True,
        verbose_name=_('عرض جغرافیایی ورود'),
    )
    geo_lng_checkin = models.DecimalField(
        max_digits=10, decimal_places=7, null=True, blank=True,
        verbose_name=_('طول جغرافیایی ورود'),
    )
    notes = models.TextField(blank=True, verbose_name=_('یادداشت'))

    class Meta:
        db_table = 'salesperson_visits'
        verbose_name = _('سرکشی')
        verbose_name_plural = _('سرکشی‌ها')
        unique_together = ('distributor', 'store', 'visit_date')
        ordering = ['-visit_date', 'check_in_time']
        indexes = [
            models.Index(fields=['visit_date']),
            models.Index(fields=['distributor', 'visit_date']),
        ]

    def __str__(self):
        return f'{self.distributor.code} → {self.store.name} ({self.visit_date})'

    @property
    def duration_minutes(self):
        """مدت سرکشی به دقیقه"""
        if self.check_in_time and self.check_out_time:
            delta = self.check_out_time - self.check_in_time
            return delta.total_seconds() / 60
        return None
