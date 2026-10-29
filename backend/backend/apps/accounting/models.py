"""
Accounting Models — JournalHeader, JournalLine, Account, FiscalPeriod, CostCenter
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from core.models import BaseModel, AuditedManager


class AccountType(models.TextChoices):
    ASSET = 'asset', _('دارایی')
    LIABILITY = 'liability', _('بدهی')
    EQUITY = 'equity', _('سرمایه')
    REVENUE = 'revenue', _('درآمد')
    EXPENSE = 'expense', _('هزینه')


class Account(BaseModel):
    """کدینگ حساب‌ها — درختی با ۵ نوع اصلی
    ساختار تفصیلی چندسطحی:
        level 1 = کل        (مثال: 1 دارایی‌ها)
        level 2 = میانی      (مثال: 10 دارایی‌های جاری)
        level 3 = تفصیلی     (مثال: 101 موجودی کالا — قابل ثبت سند)
        level 4 = شخص تفصیلی (مثال: 101/WH-RAW-01 — قابل ثبت سند)
    """

    objects = AuditedManager()
    all_objects = models.Manager()

    code = models.CharField(max_length=30, unique=True, verbose_name=_('کد'))
    name = models.CharField(max_length=200, verbose_name=_('نام'))
    type = models.CharField(
        max_length=20,
        choices=AccountType.choices,
        verbose_name=_('نوع'),
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.RESTRICT,
        null=True, blank=True,
        related_name='children',
        verbose_name=_('حساب والد'),
    )
    level = models.PositiveIntegerField(
        default=1,
        verbose_name=_('سطح'),
        help_text='1=کل، 2=میانی، 3=تفصیلی، 4=شخص تفصیلی',
    )
    is_active = models.BooleanField(default=True, verbose_name=_('فعال'))
    is_postable = models.BooleanField(
        default=True,
        verbose_name=_('قابل ثبت سند'),
        help_text=_('اگر FALSE یعنی فقط گروه‌بندی است — فقط level>=3 قابل ثبت است'),
    )
    description = models.TextField(blank=True, verbose_name=_('توضیحات'))

    class Meta:
        db_table = 'accounts'
        verbose_name = _('حساب')
        verbose_name_plural = _('حساب‌ها')
        ordering = ['code']
        indexes = [
            models.Index(fields=['parent']),
            models.Index(fields=['type']),
            models.Index(fields=['level']),
        ]

    def __str__(self):
        return f'{self.code} - {self.name}'

    def save(self, *args, **kwargs):
        """محاسبه خودکار level بر اساس parent"""
        if self.parent:
            self.level = self.parent.level + 1
        else:
            self.level = 1
        # فقط سطح ۳ به بالا قابل ثبت سند هستند
        # (در صورت صریحاً false شدن، احترام می‌گذاریم)
        if self.level < 3:
            self.is_postable = False
        super().save(*args, **kwargs)

    def get_balance(self, as_of_date=None):
        """مانده حساب تا تاریخ مشخص"""
        lines = self.journal_lines.filter(journal__status='posted')
        if as_of_date:
            lines = lines.filter(journal__date__lte=as_of_date)
        debit = sum(l.debit for l in lines)
        credit = sum(l.credit for l in lines)
        return debit - credit


class CostCenter(BaseModel):
    """مرکز هزینه — درختی"""

    objects = AuditedManager()
    all_objects = models.Manager()

    code = models.CharField(max_length=50, unique=True, verbose_name=_('کد'))
    name = models.CharField(max_length=200, verbose_name=_('نام'))
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='children',
        verbose_name=_('مرکز والد'),
    )
    type = models.CharField(
        max_length=50,
        verbose_name=_('نوع'),
        help_text='production, dept, warehouse, distribution, administrative',
    )
    is_active = models.BooleanField(default=True, verbose_name=_('فعال'))

    class Meta:
        db_table = 'cost_centers'
        verbose_name = _('مرکز هزینه')
        verbose_name_plural = _('مراکز هزینه')
        ordering = ['code']

    def __str__(self):
        return f'{self.code} - {self.name}'


class FiscalPeriod(BaseModel):
    """دوره‌های مالی"""

    class PeriodType(models.TextChoices):
        MONTHLY = 'monthly', _('ماهانه')
        QUARTERLY = 'quarterly', _('فصلی')
        YEARLY = 'yearly', _('سالانه')

    name = models.CharField(max_length=100, unique=True, verbose_name=_('نام'))
    type = models.CharField(
        max_length=20,
        choices=PeriodType.choices,
        verbose_name=_('نوع'),
    )
    start_date = models.DateField(verbose_name=_('شروع'))
    end_date = models.DateField(verbose_name=_('پایان'))
    is_closed = models.BooleanField(default=False, verbose_name=_('بسته شده'))
    closed_at = models.DateTimeField(null=True, blank=True, verbose_name=_('زمان بستن'))
    closed_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='+',
        verbose_name=_('بسته‌کننده'),
    )

    class Meta:
        db_table = 'fiscal_periods'
        verbose_name = _('دوره مالی')
        verbose_name_plural = _('دوره‌های مالی')
        ordering = ['-start_date']
        constraints = [
            models.CheckConstraint(
                check=models.Q(end_date__gt=models.F('start_date')),
                name='period_end_after_start',
            ),
        ]

    def __str__(self):
        return self.name


class JournalTemplate(models.Model):
    """قالب‌های سند حسابداری خودکار"""

    class SourceType(models.TextChoices):
        SALE = 'sale', _('فروش')
        PURCHASE = 'purchase', _('خرید')
        TRANSFER = 'transfer', _('انتقال')
        RETURN = 'return', _('برگشت')
        PAYMENT = 'payment', _('پرداخت')
        PRODUCTION = 'production', _('تولید')
        MANUAL = 'manual', _('دستی')

    name = models.CharField(max_length=200, verbose_name=_('نام'))
    source_type = models.CharField(
        max_length=50,
        choices=SourceType.choices,
        verbose_name=_('نوع منبع'),
    )
    template_json = models.JSONField(
        verbose_name=_('قالب'),
        help_text='{"debit": [...], "credit": [...]}',
    )
    is_active = models.BooleanField(default=True, verbose_name=_('فعال'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='+',
    )

    class Meta:
        db_table = 'journal_templates'
        verbose_name = _('قالب سند')
        verbose_name_plural = _('قالب‌های سند')
        indexes = [
            models.Index(fields=['source_type']),
        ]

    def __str__(self):
        return f'{self.source_type} - {self.name}'


class JournalHeader(BaseModel):
    """سند حسابداری — با کنترل توازن"""

    objects = AuditedManager()
    all_objects = models.Manager()

    class JournalStatus(models.TextChoices):
        DRAFT = 'draft', _('پیش‌نویس')
        POSTED = 'posted', _('ثبت شد')
        REVERSED = 'reversed', _('معکوس شد')
        CANCELED = 'canceled', _('لغو شد')

    journal_no = models.CharField(max_length=50, unique=True, verbose_name=_('شماره سند'))
    date = models.DateField(verbose_name=_('تاریخ'))
    source_type = models.CharField(
        max_length=50,
        default='manual',
        verbose_name=_('نوع منبع'),
        help_text='sale, purchase, transfer, manual, etc.',
    )
    source_id = models.BigIntegerField(
        null=True, blank=True,
        verbose_name=_('شناسه سند مبدأ'),
    )
    total_debit = models.DecimalField(
        max_digits=18, decimal_places=4,
        default=0,
        verbose_name=_('مجموع بدهکار'),
    )
    total_credit = models.DecimalField(
        max_digits=18, decimal_places=4,
        default=0,
        verbose_name=_('مجموع بستانکار'),
    )
    status = models.CharField(
        max_length=20,
        choices=JournalStatus.choices,
        default=JournalStatus.DRAFT,
        verbose_name=_('وضعیت'),
    )
    period = models.ForeignKey(
        FiscalPeriod,
        on_delete=models.RESTRICT,
        null=True, blank=True,
        related_name='journals',
        verbose_name=_('دوره مالی'),
    )
    description = models.TextField(blank=True, verbose_name=_('توضیحات'))
    reversed_by_journal = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='reversals',
        verbose_name=_('سند معکوس'),
    )

    class Meta:
        db_table = 'journal_headers'
        verbose_name = _('سند حسابداری')
        verbose_name_plural = _('اسناد حسابداری')
        ordering = ['-date', '-id']
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['source_type', 'source_id']),
            models.Index(fields=['period']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f'{self.journal_no} - {self.date} ({self.total_debit})'

    @property
    def is_balanced(self):
        """آیا سند متوازن است؟"""
        return self.total_debit == self.total_credit

    def recalculate_totals(self):
        """محاسبه مجدد مجموع از روی خطوط"""
        from django.db.models import Sum
        totals = self.lines.aggregate(
            debit=Sum('debit'),
            credit=Sum('credit'),
        )
        self.total_debit = totals['debit'] or 0
        self.total_credit = totals['credit'] or 0
        self.save(update_fields=['total_debit', 'total_credit', 'updated_at'])


class JournalLine(models.Model):
    """خطوط سند حسابداری"""

    journal = models.ForeignKey(
        JournalHeader,
        on_delete=models.CASCADE,
        related_name='lines',
        verbose_name=_('سند'),
    )
    account = models.ForeignKey(
        Account,
        on_delete=models.RESTRICT,
        related_name='journal_lines',
        verbose_name=_('حساب'),
    )
    cost_center = models.ForeignKey(
        CostCenter,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='journal_lines',
        verbose_name=_('مرکز هزینه'),
    )
    debit = models.DecimalField(
        max_digits=18, decimal_places=4,
        default=0,
        verbose_name=_('بدهکار'),
    )
    credit = models.DecimalField(
        max_digits=18, decimal_places=4,
        default=0,
        verbose_name=_('بستانکار'),
    )
    description = models.TextField(blank=True, verbose_name=_('توضیحات'))
    ref_doc_type = models.CharField(max_length=50, blank=True, verbose_name=_('نوع سند مرجع'))
    ref_doc_id = models.BigIntegerField(null=True, blank=True, verbose_name=_('شناسه سند مرجع'))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'journal_lines'
        verbose_name = _('خط سند')
        verbose_name_plural = _('خطوط اسناد')
        indexes = [
            models.Index(fields=['journal']),
            models.Index(fields=['account']),
            models.Index(fields=['cost_center']),
        ]
        constraints = [
            # هر خط یا بدهکار یا بستانکار (نه هر دو)
            models.CheckConstraint(
                check=(
                    models.Q(debit__gt=0, credit=0) |
                    models.Q(debit=0, credit__gt=0)
                ),
                name='line_debit_xor_credit',
            ),
        ]

    def __str__(self):
        return f'{self.journal.journal_no} - {self.account.code} - D:{self.debit} C:{self.credit}'


class ExchangeRate(models.Model):
    """نرخ ارز"""

    currency = models.CharField(max_length=10, verbose_name=_('ارز'))
    rate = models.DecimalField(
        max_digits=18, decimal_places=6,
        verbose_name=_('نرخ به ریال'),
    )
    effective_date = models.DateField(verbose_name=_('تاریخ اعتبار'))
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='+',
    )

    class Meta:
        db_table = 'exchange_rates'
        verbose_name = _('نرخ ارز')
        verbose_name_plural = _('نرخ ارزها')
        unique_together = ('currency', 'effective_date')
        ordering = ['-effective_date']

    def __str__(self):
        return f'{self.currency} - {self.rate} ({self.effective_date})'
