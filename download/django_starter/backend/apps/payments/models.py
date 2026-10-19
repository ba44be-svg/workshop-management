"""
Payments Models — PaymentTransaction, CheckPayment, CashReceipt
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from core.models import BaseModel


class GatewayType(models.TextChoices):
    ZARINPAL = 'zarinpal', _('زرین‌پال')
    IDPAY = 'idpay', _('آیدی‌پی')
    PARSIAN = 'parsian', _('بانک پارسیان')


class PaymentStatus(models.TextChoices):
    INITIATED = 'initiated', _('شروع شده')
    PAID = 'paid', _('پرداخت شد')
    FAILED = 'failed', _('ناموفق')
    VERIFIED = 'verified', _('تأیید شد')
    REFUNDED = 'refunded', _('بازگشت داده شد')


class PaymentTransaction(models.Model):
    """تراکنش‌های پرداخت آنلاین"""

    transaction_no = models.CharField(
        max_length=50, unique=True,
        verbose_name=_('شماره تراکنش'),
    )
    store = models.ForeignKey(
        'partners.Store',
        on_delete=models.RESTRICT,
        related_name='payments',
        verbose_name=_('فروشگاه'),
    )
    gateway = models.CharField(
        max_length=20,
        choices=GatewayType.choices,
        verbose_name=_('درگاه'),
    )
    amount = models.DecimalField(
        max_digits=18, decimal_places=4,
        verbose_name=_('مبلغ (ریال)'),
    )
    status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.INITIATED,
        verbose_name=_('وضعیت'),
    )
    authority = models.CharField(
        max_length=200, blank=True,
        verbose_name=_('Authority'),
        help_text=_('کد قبل از پرداخت (زرین‌پال)'),
    )
    ref_id = models.CharField(
        max_length=100, blank=True,
        verbose_name=_('کد پیگیری'),
        help_text=_('پس از پرداخت موفق'),
    )
    paid_at = models.DateTimeField(
        null=True, blank=True,
        verbose_name=_('زمان پرداخت'),
    )
    related_doc_type = models.CharField(
        max_length=50,
        verbose_name=_('نوع سند مرتبط'),
        help_text='store_order, manual',
    )
    related_doc_id = models.BigIntegerField(
        null=True, blank=True,
        verbose_name=_('شناسه سند مرتبط'),
    )
    journal = models.ForeignKey(
        'accounting.JournalHeader',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='payments',
        verbose_name=_('سند حسابداری'),
    )
    description = models.TextField(blank=True, verbose_name=_('توضیحات'))
    gateway_response = models.JSONField(
        default=dict, blank=True,
        verbose_name=_('پاسخ درگاه'),
    )
    ip_address = models.GenericIPAddressField(
        null=True, blank=True,
        verbose_name=_('IP پرداخت‌کننده'),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='+',
        verbose_name=_('کاربر'),
    )

    class Meta:
        db_table = 'payment_transactions'
        verbose_name = _('تراکنش پرداخت')
        verbose_name_plural = _('تراکنش‌های پرداخت')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['store', 'created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['related_doc_type', 'related_doc_id']),
        ]

    def __str__(self):
        return f'{self.transaction_no} - {self.amount} - {self.status}'

    @property
    def is_verified(self):
        return self.status == PaymentStatus.VERIFIED


class CheckPayment(models.Model):
    """پرداخت با چک"""

    store = models.ForeignKey(
        'partners.Store',
        on_delete=models.RESTRICT,
        related_name='check_payments',
        verbose_name=_('فروشگاه'),
    )
    amount = models.DecimalField(
        max_digits=18, decimal_places=4,
        verbose_name=_('مبلغ چک'),
    )
    check_number = models.CharField(max_length=50, verbose_name=_('شماره چک'))
    bank_name = models.CharField(max_length=100, verbose_name=_('نام بانک'))
    issue_date = models.DateField(verbose_name=_('تاریخ صدور'))
    due_date = models.DateField(verbose_name=_('تاریخ سررسید'))
    is_cashed = models.BooleanField(default=False, verbose_name=_('وصول شد'))
    cashed_at = models.DateField(null=True, blank=True, verbose_name=_('تاریخ وصول'))
    related_order = models.ForeignKey(
        'store_portal.StoreOrder',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='checks',
        verbose_name=_('سفارش مرتبط'),
    )
    image = models.ImageField(
        upload_to='checks/%Y/%m/',
        null=True, blank=True,
        verbose_name=_('تصویر چک'),
    )
    notes = models.TextField(blank=True, verbose_name=_('یادداشت'))
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='+',
        verbose_name=_('کاربر'),
    )

    class Meta:
        db_table = 'check_payments'
        verbose_name = _('چک')
        verbose_name_plural = _('چک‌ها')
        ordering = ['-due_date']

    def __str__(self):
        return f'چک {self.check_number} - {self.amount}'


class CashReceipt(models.Model):
    """رسید پرداخت نقدی (تحویل به عامل)"""

    store = models.ForeignKey(
        'partners.Store',
        on_delete=models.RESTRICT,
        related_name='cash_receipts',
        verbose_name=_('فروشگاه'),
    )
    amount = models.DecimalField(
        max_digits=18, decimal_places=4,
        verbose_name=_('مبلغ نقدی'),
    )
    received_from = models.CharField(
        max_length=200,
        verbose_name=_('دریافت‌شده از'),
    )
    received_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='+',
        verbose_name=_('گیرنده (عامل)'),
    )
    receipt_no = models.CharField(max_length=50, unique=True, verbose_name=_('شماره رسید'))
    receipt_date = models.DateField(verbose_name=_('تاریخ رسید'))
    related_order = models.ForeignKey(
        'store_portal.StoreOrder',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='cash_receipts',
        verbose_name=_('سفارش مرتبط'),
    )
    notes = models.TextField(blank=True, verbose_name=_('یادداشت'))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'cash_receipts'
        verbose_name = _('رسید نقدی')
        verbose_name_plural = _('رسیدهای نقدی')
        ordering = ['-receipt_date']

    def __str__(self):
        return f'{self.receipt_no} - {self.amount}'
