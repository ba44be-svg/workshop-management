"""
Partners Models — Distributor, Store, Customer, PartnerCredit, LoyaltyPoint
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from core.models import BaseModel, AuditedManager
from django.db.models import Sum


class Distributor(BaseModel):
    """عوامل پخش"""

    objects = AuditedManager()
    all_objects = models.Manager()

    code = models.CharField(max_length=50, unique=True, verbose_name=_('کد'))
    name = models.CharField(max_length=200, verbose_name=_('نام'))
    mobile = models.CharField(max_length=20, unique=True, verbose_name=_('موبایل'))
    vehicle = models.ForeignKey(
        'dispatch.Vehicle',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='distributors',
        verbose_name=_('خودرو'),
    )
    default_route = models.ForeignKey(
        'dispatch.Route',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='default_distributors',
        verbose_name=_('مسیر پیش‌فرض'),
    )
    commission_rate = models.DecimalField(
        max_digits=5, decimal_places=2,
        default=5.00,
        verbose_name=_('درصد پورسانت'),
    )
    is_active = models.BooleanField(default=True, verbose_name=_('فعال'))

    class Meta:
        db_table = 'distributors'
        verbose_name = _('عامل پخش')
        verbose_name_plural = _('عوامل پخش')
        ordering = ['code']

    def __str__(self):
        return f'{self.code} - {self.name}'


class Store(BaseModel):
    """فروشگاه‌ها"""

    objects = AuditedManager()
    all_objects = models.Manager()

    class StoreTier(models.TextChoices):
        REGULAR = 'regular', _('عادی')
        SILVER = 'silver', _('نقره‌ای')
        GOLD = 'gold', _('طلایی')
        PLATINUM = 'platinum', _('پلاتین')

    class SalesModel(models.TextChoices):
        CONSIGNMENT = 'consignment', _('امانی')
        FIRM = 'firm', _('قطعی')
        MIXED = 'mixed', _('ترکیبی')

    code = models.CharField(max_length=50, unique=True, verbose_name=_('کد'))
    name = models.CharField(max_length=200, verbose_name=_('نام'))
    address = models.TextField(blank=True, verbose_name=_('آدرس'))
    phone = models.CharField(max_length=20, blank=True, verbose_name=_('تلفن'))
    geo_lat = models.DecimalField(
        max_digits=10, decimal_places=7, null=True, blank=True,
        verbose_name=_('عرض جغرافیایی'),
    )
    geo_lng = models.DecimalField(
        max_digits=10, decimal_places=7, null=True, blank=True,
        verbose_name=_('طول جغرافیایی'),
    )
    distributor = models.ForeignKey(
        Distributor,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='stores',
        verbose_name=_('عامل پخش'),
    )
    sales_model = models.CharField(
        max_length=20,
        choices=SalesModel.choices,
        default=SalesModel.CONSIGNMENT,
        verbose_name=_('مدل فروش'),
    )
    tier = models.CharField(
        max_length=20,
        choices=StoreTier.choices,
        default=StoreTier.REGULAR,
        verbose_name=_('لایه وفاداری'),
    )
    credit_limit = models.DecimalField(
        max_digits=18, decimal_places=4,
        default=0,
        verbose_name=_('سقف اعتبار'),
    )
    current_credit = models.DecimalField(
        max_digits=18, decimal_places=4,
        default=0,
        verbose_name=_('اعتبار استفاده‌شده'),
    )
    loyalty_points = models.PositiveIntegerField(
        default=0,
        verbose_name=_('امتیاز وفاداری'),
    )
    is_active = models.BooleanField(default=True, verbose_name=_('فعال'))

    class Meta:
        db_table = 'stores'
        verbose_name = _('فروشگاه')
        verbose_name_plural = _('فروشگاه‌ها')
        ordering = ['code']
        indexes = [
            models.Index(fields=['distributor']),
            models.Index(fields=['tier']),
            models.Index(fields=['geo_lat', 'geo_lng']),
        ]

    def __str__(self):
        return f'{self.code} - {self.name} ({self.get_tier_display()})'

    @property
    def available_credit(self):
        """اعتبار باقی‌مانده"""
        return self.credit_limit - self.current_credit

    @property
    def discount_percentage(self):
        """درصد تخفیف بر اساس لایه"""
        return {
            'regular': 0,
            'silver': 2,
            'gold': 5,
            'platinum': 8,
        }.get(self.tier, 0)


class Customer(BaseModel):
    """مشتریان آنلاین"""

    objects = AuditedManager()
    all_objects = models.Manager()

    class CustomerType(models.TextChoices):
        INDIVIDUAL = 'individual', _('فردی')
        BUSINESS = 'business', _('تجاری')
        PLATFORM = 'platform', _('پلتفرم')

    type = models.CharField(
        max_length=20,
        choices=CustomerType.choices,
        verbose_name=_('نوع'),
    )
    name = models.CharField(max_length=200, verbose_name=_('نام'))
    phone = models.CharField(max_length=20, blank=True, verbose_name=_('موبایل'))
    platform = models.CharField(
        max_length=50, blank=True,
        verbose_name=_('پلتفرم'),
        help_text='instagram, snapp, website',
    )
    platform_user_id = models.CharField(
        max_length=200, blank=True,
        verbose_name=_('شناسه روی پلتفرم'),
    )
    credit_limit = models.DecimalField(
        max_digits=18, decimal_places=4,
        default=0,
        verbose_name=_('سقف اعتبار'),
    )
    is_active = models.BooleanField(default=True, verbose_name=_('فعال'))

    class Meta:
        db_table = 'customers'
        verbose_name = _('مشتری')
        verbose_name_plural = _('مشتریان')
        ordering = ['name']

    def __str__(self):
        return f'{self.name} ({self.get_type_display()})'


class PartnerCredit(models.Model):
    """اعتبار و گردش حساب هر فروشگاه — Cache برای عملکرد بالا"""

    store = models.ForeignKey(
        Store,
        on_delete=models.CASCADE,
        related_name='credits',
        verbose_name=_('فروشگاه'),
    )
    total_purchases = models.DecimalField(
        max_digits=18, decimal_places=4,
        default=0,
        verbose_name=_('مجموع خرید'),
    )
    total_paid = models.DecimalField(
        max_digits=18, decimal_places=4,
        default=0,
        verbose_name=_('مجموع پرداخت'),
    )
    total_returns = models.DecimalField(
        max_digits=18, decimal_places=4,
        default=0,
        verbose_name=_('مجموع برگشت'),
    )
    balance = models.DecimalField(
        max_digits=18, decimal_places=4,
        default=0,
        verbose_name=_('مانده'),
        help_text=_('مثبت = طلبکار، منفی = بدهکار'),
    )
    last_transaction = models.DateTimeField(
        auto_now=True,
        verbose_name=_('آخرین تراکنش'),
    )

    class Meta:
        db_table = 'partner_credits'
        verbose_name = _('اعتبار شریک')
        verbose_name_plural = _('اعتبارات شرکا')

    def __str__(self):
        return f'{self.store.name} - Balance: {self.balance}'

    @property
    def is_in_credit_limit(self):
        """آیا در محدوده اعتبار است؟"""
        return self.balance < self.store.credit_limit


class LoyaltyPoint(models.Model):
    """تراکنش‌های امتیاز وفاداری"""

    store = models.ForeignKey(
        Store,
        on_delete=models.CASCADE,
        related_name='loyalty_transactions',
        verbose_name=_('فروشگاه'),
    )
    points_change = models.IntegerField(
        verbose_name=_('تغییر امتیاز'),
        help_text=_('مثبت = کسب، منفی = مصرف'),
    )
    reason = models.CharField(
        max_length=50,
        verbose_name=_('دلیل'),
        help_text='purchase, payment_ontime, no_return, tier_bonus',
    )
    ref_doc_type = models.CharField(max_length=50, blank=True, verbose_name=_('نوع سند مرجع'))
    ref_doc_id = models.BigIntegerField(null=True, blank=True, verbose_name=_('شناسه سند مرجع'))
    new_balance = models.IntegerField(
        verbose_name=_('مانده جدید'),
        help_text=_('امتیاز بعد از این تراکنش'),
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('زمان'))

    class Meta:
        db_table = 'loyalty_transactions'
        verbose_name = _('تراکنش وفاداری')
        verbose_name_plural = _('تراکنش‌های وفاداری')
        indexes = [
            models.Index(fields=['store', 'created_at']),
        ]

    def __str__(self):
        return f'{self.store.name} - {self.points_change:+d} ({self.reason})'
