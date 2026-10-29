"""
Workshop Models — کارپرداز، خرید مواد اولیه، حواله/برگشت کارگاه
کارپرداز (Contractor):
    - خرید مواد اولیه به نمایندگی کارگاه
    - تحویل مواد در کارگاه (حواله کارگاه)
    - برگشت مواد استفاده‌نشده (برگشت کارگاه)
    - حساب تفصیلی «کالای نزد کارپرداز» (140/C001)
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from core.models import BaseModel, AuditedManager


class Contractor(BaseModel):
    """کارپرداز — شخص/موجودیت مستقل از عامل پخش (Distributor)"""

    objects = AuditedManager()
    all_objects = models.Manager()

    code = models.CharField(max_length=50, unique=True, verbose_name=_('کد'))
    name = models.CharField(max_length=200, verbose_name=_('نام کامل'))
    national_id = models.CharField(
        max_length=20, blank=True,
        verbose_name=_('کد ملی'),
    )
    mobile = models.CharField(max_length=20, unique=True, verbose_name=_('موبایل'))
    phone = models.CharField(max_length=20, blank=True, verbose_name=_('تلفن ثابت'))
    address = models.TextField(blank=True, verbose_name=_('آدرس'))
    workshop_name = models.CharField(
        max_length=200, blank=True,
        verbose_name=_('نام کارگاه'),
    )
    is_active = models.BooleanField(default=True, verbose_name=_('فعال'))
    detail_account = models.ForeignKey(
        'accounting.Account',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='contractors',
        verbose_name=_('حساب تفصیلی'),
        help_text=_('حساب تفصیلی «کالای نزد کارپرداز» 140/{code}'),
    )

    class Meta:
        db_table = 'contractors'
        verbose_name = _('کارپرداز')
        verbose_name_plural = _('کارپردازها')
        ordering = ['code']
        indexes = [
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f'{self.code} - {self.name}'


class Employee(BaseModel):
    """کارکنان (پرسنل) — کارگر، انباردار، مسئول کارگاه و ..."""

    objects = AuditedManager()
    all_objects = models.Manager()

    code = models.CharField(max_length=50, unique=True, verbose_name=_('کد'))
    first_name = models.CharField(max_length=100, verbose_name=_('نام'))
    last_name = models.CharField(max_length=100, verbose_name=_('نام خانوادگی'))
    national_id = models.CharField(
        max_length=20, blank=True,
        verbose_name=_('کد ملی'),
    )
    mobile = models.CharField(max_length=20, blank=True, verbose_name=_('موبایل'))
    phone = models.CharField(max_length=20, blank=True, verbose_name=_('تلفن ثابت'))
    position = models.CharField(
        max_length=200,
        verbose_name=_('سمت'),
        help_text=_('انباردار، کارگر، مسئول کارگاه، ...'),
    )
    workshop = models.ForeignKey(
        'inventory.Warehouse',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='employees',
        verbose_name=_('کارگاه'),
        help_text=_('کارگاهی که این کارکنان به آن تعلق دارد'),
    )
    hire_date = models.DateField(verbose_name=_('تاریخ شروع به کار'))
    is_active = models.BooleanField(default=True, verbose_name=_('فعال'))

    class Meta:
        db_table = 'employees'
        verbose_name = _('کارکنان')
        verbose_name_plural = _('کارکنان')
        ordering = ['code']
        indexes = [
            models.Index(fields=['is_active']),
            models.Index(fields=['workshop']),
            models.Index(fields=['position']),
        ]

    def __str__(self):
        return f'{self.code} - {self.full_name} ({self.position})'

    @property
    def full_name(self) -> str:
        """نام و نام خانوادگی به‌همراه."""
        return f'{self.first_name} {self.last_name}'.strip()


class PurchaseHeader(BaseModel):
    """خرید مواد اولیه — خرید از جانب کارپرداز به انبار مواد اولیه"""

    objects = AuditedManager()
    all_objects = models.Manager()

    class PurchaseStatus(models.TextChoices):
        DRAFT = 'draft', _('پیش‌نویس')
        POSTED = 'posted', _('ثبت شد')
        CANCELED = 'canceled', _('لغو شد')

    purchase_no = models.CharField(max_length=50, unique=True, verbose_name=_('شماره خرید'))
    purchase_date = models.DateField(verbose_name=_('تاریخ خرید'))
    contractor = models.ForeignKey(
        Contractor,
        on_delete=models.RESTRICT,
        related_name='purchases',
        verbose_name=_('کارپرداز'),
    )
    warehouse = models.ForeignKey(
        'inventory.Warehouse',
        on_delete=models.RESTRICT,
        related_name='purchases',
        verbose_name=_('انبار مقصد (مواد اولیه)'),
    )
    cash_account = models.ForeignKey(
        'accounting.Account',
        on_delete=models.RESTRICT,
        related_name='purchases_paid',
        verbose_name=_('حساب نقد/بانک پرداختی'),
    )
    total_amount = models.DecimalField(
        max_digits=18, decimal_places=4,
        default=0,
        verbose_name=_('مبلغ کل'),
    )
    total_qty = models.DecimalField(
        max_digits=14, decimal_places=3,
        default=0,
        verbose_name=_('مقدار کل'),
    )
    notes = models.TextField(blank=True, verbose_name=_('یادداشت'))
    journal = models.ForeignKey(
        'accounting.JournalHeader',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='purchases',
        verbose_name=_('سند حسابداری'),
    )
    status = models.CharField(
        max_length=20,
        choices=PurchaseStatus.choices,
        default=PurchaseStatus.POSTED,
        verbose_name=_('وضعیت'),
    )

    class Meta:
        db_table = 'purchase_headers'
        verbose_name = _('سند خرید مواد اولیه')
        verbose_name_plural = _('اسناد خرید مواد اولیه')
        ordering = ['-purchase_date', '-id']
        indexes = [
            models.Index(fields=['purchase_date']),
            models.Index(fields=['contractor']),
            models.Index(fields=['warehouse']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f'{self.purchase_no} ({self.contractor.code})'


class PurchaseLine(BaseModel):
    """خطوط خرید مواد اولیه — هر خط یک لات جدید می‌سازد"""

    purchase = models.ForeignKey(
        PurchaseHeader,
        on_delete=models.CASCADE,
        related_name='lines',
        verbose_name=_('سند خرید'),
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.RESTRICT,
        related_name='purchase_lines',
        verbose_name=_('محصول'),
    )
    qty = models.DecimalField(
        max_digits=14, decimal_places=3,
        verbose_name=_('مقدار'),
    )
    unit_price = models.DecimalField(
        max_digits=18, decimal_places=4,
        verbose_name=_('قیمت واحد'),
    )
    unit_cost = models.DecimalField(
        max_digits=18, decimal_places=4,
        default=0,
        verbose_name=_('بهای تمام‌شده واحد'),
        help_text=_('برای میانگین موزون — برابر با قیمت خرید است'),
    )
    shelf_life_days = models.IntegerField(
        default=15,
        verbose_name=_('مدت ماندگاری (روز)'),
    )
    expiry_date = models.DateField(verbose_name=_('تاریخ انقضا'))
    lot_no = models.CharField(max_length=50, verbose_name=_('شماره لات'))
    line_total = models.DecimalField(
        max_digits=18, decimal_places=4,
        default=0,
        verbose_name=_('جمع خط'),
    )

    class Meta:
        db_table = 'purchase_lines'
        verbose_name = _('خط خرید')
        verbose_name_plural = _('خطوط خرید')
        indexes = [
            models.Index(fields=['purchase']),
            models.Index(fields=['product']),
        ]

    def __str__(self):
        return f'{self.purchase.purchase_no} - {self.product.code} ({self.qty})'


class WorkshopIssue(BaseModel):
    """حواله کارگاه — خروج مواد اولیه از انبار به کارگاه کارپرداز"""

    objects = AuditedManager()
    all_objects = models.Manager()

    class IssueStatus(models.TextChoices):
        DRAFT = 'draft', _('پیش‌نویس')
        POSTED = 'posted', _('ثبت شد')
        CANCELED = 'canceled', _('لغو شد')

    issue_no = models.CharField(max_length=50, unique=True, verbose_name=_('شماره حواله'))
    issue_date = models.DateField(verbose_name=_('تاریخ حواله'))
    contractor = models.ForeignKey(
        Contractor,
        on_delete=models.RESTRICT,
        related_name='issues_received',
        verbose_name=_('کارپرداز تحویل‌گیرنده'),
        null=True, blank=True,
        help_text=_('حساب تفصیلی مرتبط — اختیاری در صورت انتخاب کارکنان'),
    )
    employee = models.ForeignKey(
        Employee,
        on_delete=models.RESTRICT,
        related_name='issues_received',
        verbose_name=_('شخص تحویل‌گیرنده'),
        null=True, blank=True,
        help_text=_('کارکنانی که حواله را دریافت می‌کند'),
    )
    from_warehouse = models.ForeignKey(
        'inventory.Warehouse',
        on_delete=models.RESTRICT,
        related_name='issues_from',
        verbose_name=_('انبار مبدأ (مواد اولیه)'),
    )
    to_warehouse = models.ForeignKey(
        'inventory.Warehouse',
        on_delete=models.RESTRICT,
        related_name='issues_to',
        verbose_name=_('انبار مقصد (کارگاه)'),
    )
    production_batch = models.ForeignKey(
        'production.ProductionBatch',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='workshop_issues',
        verbose_name=_('بچ تولید مرجع'),
    )
    total_qty = models.DecimalField(
        max_digits=14, decimal_places=3,
        default=0,
        verbose_name=_('مقدار کل'),
    )
    total_value = models.DecimalField(
        max_digits=18, decimal_places=4,
        default=0,
        verbose_name=_('ارزش کل'),
    )
    notes = models.TextField(blank=True, verbose_name=_('یادداشت'))
    journal = models.ForeignKey(
        'accounting.JournalHeader',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='workshop_issues',
        verbose_name=_('سند حسابداری'),
    )
    status = models.CharField(
        max_length=20,
        choices=IssueStatus.choices,
        default=IssueStatus.POSTED,
        verbose_name=_('وضعیت'),
    )

    class Meta:
        db_table = 'workshop_issues'
        verbose_name = _('حواله کارگاه')
        verbose_name_plural = _('حواله‌های کارگاه')
        ordering = ['-issue_date', '-id']
        indexes = [
            models.Index(fields=['issue_date']),
            models.Index(fields=['contractor']),
            models.Index(fields=['from_warehouse']),
            models.Index(fields=['to_warehouse']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f'{self.issue_no} ({self.contractor.code})'


class WorkshopIssueLine(BaseModel):
    """خطوط حواله کارگاه — تخصیص FEFO لات‌های مواد اولیه"""

    issue = models.ForeignKey(
        WorkshopIssue,
        on_delete=models.CASCADE,
        related_name='lines',
        verbose_name=_('حواله کارگاه'),
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.RESTRICT,
        related_name='workshop_issue_lines',
        verbose_name=_('محصول'),
    )
    lot = models.ForeignKey(
        'inventory.InventoryLot',
        on_delete=models.RESTRICT,
        related_name='workshop_issue_lines',
        verbose_name=_('لات مبدأ'),
    )
    qty = models.DecimalField(
        max_digits=14, decimal_places=3,
        verbose_name=_('مقدار'),
    )
    unit_cost = models.DecimalField(
        max_digits=18, decimal_places=4,
        default=0,
        verbose_name=_('بهای تمام‌شده در لحظه حواله'),
    )
    line_total = models.DecimalField(
        max_digits=18, decimal_places=4,
        default=0,
        verbose_name=_('جمع خط'),
    )

    class Meta:
        db_table = 'workshop_issue_lines'
        verbose_name = _('خط حواله کارگاه')
        verbose_name_plural = _('خطوط حواله کارگاه')
        indexes = [
            models.Index(fields=['issue']),
            models.Index(fields=['product']),
            models.Index(fields=['lot']),
        ]

    def __str__(self):
        return f'{self.issue.issue_no} - {self.product.code} ({self.qty})'


class WorkshopReturn(BaseModel):
    """برگشت کارگاه — بازگشت مواد استفاده‌نشده از کارگاه به انبار مواد اولیه"""

    objects = AuditedManager()
    all_objects = models.Manager()

    class ReturnStatus(models.TextChoices):
        DRAFT = 'draft', _('پیش‌نویس')
        POSTED = 'posted', _('ثبت شد')
        CANCELED = 'canceled', _('لغو شد')

    return_no = models.CharField(max_length=50, unique=True, verbose_name=_('شماره برگشت'))
    return_date = models.DateField(verbose_name=_('تاریخ برگشت'))
    issue = models.ForeignKey(
        WorkshopIssue,
        on_delete=models.RESTRICT,
        related_name='returns',
        verbose_name=_('حواله مرجع'),
    )
    contractor = models.ForeignKey(
        Contractor,
        on_delete=models.RESTRICT,
        related_name='returns_made',
        verbose_name=_('کارپرداز'),
    )
    from_warehouse = models.ForeignKey(
        'inventory.Warehouse',
        on_delete=models.RESTRICT,
        related_name='returns_from',
        verbose_name=_('انبار مبدأ (کارگاه)'),
    )
    to_warehouse = models.ForeignKey(
        'inventory.Warehouse',
        on_delete=models.RESTRICT,
        related_name='returns_to',
        verbose_name=_('انبار مقصد (مواد اولیه)'),
    )
    reason = models.TextField(blank=True, verbose_name=_('علت برگشت'))
    total_qty = models.DecimalField(
        max_digits=14, decimal_places=3,
        default=0,
        verbose_name=_('مقدار کل'),
    )
    total_value = models.DecimalField(
        max_digits=18, decimal_places=4,
        default=0,
        verbose_name=_('ارزش کل'),
    )
    journal = models.ForeignKey(
        'accounting.JournalHeader',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='workshop_returns',
        verbose_name=_('سند حسابداری'),
    )
    status = models.CharField(
        max_length=20,
        choices=ReturnStatus.choices,
        default=ReturnStatus.POSTED,
        verbose_name=_('وضعیت'),
    )

    class Meta:
        db_table = 'workshop_returns'
        verbose_name = _('برگشت کارگاه')
        verbose_name_plural = _('برگشت‌های کارگاه')
        ordering = ['-return_date', '-id']
        indexes = [
            models.Index(fields=['return_date']),
            models.Index(fields=['contractor']),
            models.Index(fields=['issue']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f'{self.return_no} ({self.contractor.code})'


class WorkshopReturnLine(BaseModel):
    """خطوط برگشت کارگاه — مرتبط با خط حواله مرجع"""

    return_doc = models.ForeignKey(
        WorkshopReturn,
        on_delete=models.CASCADE,
        related_name='lines',
        verbose_name=_('سند برگشت'),
    )
    issue_line = models.ForeignKey(
        WorkshopIssueLine,
        on_delete=models.RESTRICT,
        related_name='return_lines',
        verbose_name=_('خط حواله مرجع'),
    )
    qty = models.DecimalField(
        max_digits=14, decimal_places=3,
        verbose_name=_('مقدار برگشتی'),
        help_text=_('باید کمتر یا مساوی مقدار خط حواله باشد'),
    )
    unit_cost = models.DecimalField(
        max_digits=18, decimal_places=4,
        default=0,
        verbose_name=_('بهای تمام‌شده در لحظه برگشت'),
    )
    line_total = models.DecimalField(
        max_digits=18, decimal_places=4,
        default=0,
        verbose_name=_('جمع خط'),
    )

    class Meta:
        db_table = 'workshop_return_lines'
        verbose_name = _('خط برگشت کارگاه')
        verbose_name_plural = _('خطوط برگشت کارگاه')
        indexes = [
            models.Index(fields=['return_doc']),
            models.Index(fields=['issue_line']),
        ]

    def __str__(self):
        return f'{self.return_doc.return_no} - {self.issue_line.product.code} ({self.qty})'


# ============================================================================
# PurchaseReturn — برگشت از خرید
# ============================================================================

class PurchaseReturn(BaseModel):
    """برگشت از خرید — بازگشت کالای خریداری‌شده به تأمین‌کننده/کارپرداز"""

    objects = AuditedManager()
    all_objects = models.Manager()

    class ReturnStatus(models.TextChoices):
        DRAFT = 'draft', _('پیش‌نویس')
        POSTED = 'posted', _('ثبت شد')
        CANCELED = 'canceled', _('لغو شد')

    return_no = models.CharField(max_length=50, unique=True, verbose_name=_('شماره برگشت'))
    return_date = models.DateField(verbose_name=_('تاریخ برگشت'))
    purchase = models.ForeignKey(
        'PurchaseHeader',
        on_delete=models.RESTRICT,
        related_name='returns',
        verbose_name=_('فاکتور خرید'),
    )
    contractor = models.ForeignKey(
        'Contractor',
        on_delete=models.RESTRICT,
        related_name='purchase_returns',
        verbose_name=_('کارپرداز'),
    )
    warehouse = models.ForeignKey(
        'inventory.Warehouse',
        on_delete=models.RESTRICT,
        related_name='purchase_returns',
        verbose_name=_('انبار'),
    )
    cash_account = models.ForeignKey(
        'accounting.Account',
        on_delete=models.RESTRICT,
        related_name='purchase_returns',
        verbose_name=_('حساب دریافتنی'),
    )
    total_qty = models.DecimalField(
        max_digits=14, decimal_places=3, default=0,
        verbose_name=_('مقدار کل'),
    )
    total_amount = models.DecimalField(
        max_digits=18, decimal_places=4, default=0,
        verbose_name=_('مبلغ کل'),
    )
    reason = models.TextField(blank=True, verbose_name=_('علت برگشت'))
    journal = models.ForeignKey(
        'accounting.JournalHeader',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='purchase_returns',
        verbose_name=_('سند حسابداری'),
    )
    status = models.CharField(
        max_length=20,
        choices=ReturnStatus.choices,
        default=ReturnStatus.POSTED,
        verbose_name=_('وضعیت'),
    )

    class Meta:
        db_table = 'workshop_purchase_returns'
        verbose_name = _('برگشت از خرید')
        verbose_name_plural = _('برگشت‌های خرید')
        ordering = ['-return_date', '-id']
        indexes = [
            models.Index(fields=['return_date']),
            models.Index(fields=['status']),
            models.Index(fields=['purchase']),
        ]

    def __str__(self):
        return f'{self.return_no} - {self.purchase.purchase_no}'


class PurchaseReturnLine(BaseModel):
    """اقلام برگشت از خرید"""

    return_doc = models.ForeignKey(
        PurchaseReturn,
        on_delete=models.CASCADE,
        related_name='lines',
        verbose_name=_('سند برگشت'),
    )
    purchase_line = models.ForeignKey(
        'PurchaseLine',
        on_delete=models.RESTRICT,
        related_name='returns',
        verbose_name=_('قلم خرید'),
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.RESTRICT,
        related_name='purchase_returns',
        verbose_name=_('محصول'),
    )
    lot = models.ForeignKey(
        'inventory.InventoryLot',
        on_delete=models.RESTRICT,
        related_name='purchase_returns',
        verbose_name=_('لات'),
    )
    qty = models.DecimalField(
        max_digits=14, decimal_places=3,
        verbose_name=_('مقدار برگشتی'),
    )
    unit_price = models.DecimalField(
        max_digits=18, decimal_places=4,
        verbose_name=_('قیمت واحد'),
    )
    line_total = models.DecimalField(
        max_digits=18, decimal_places=4, default=0,
        verbose_name=_('جمع خط'),
    )

    class Meta:
        db_table = 'workshop_purchase_return_lines'
        verbose_name = _('قلم برگشت خرید')
        verbose_name_plural = _('اقلام برگشت خرید')
        indexes = [
            models.Index(fields=['return_doc']),
            models.Index(fields=['product']),
        ]

    def __str__(self):
        return f'{self.return_doc.return_no} - {self.product.code} ({self.qty})'
