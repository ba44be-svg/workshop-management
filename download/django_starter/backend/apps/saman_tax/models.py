"""
Saman Tax Models — TaxInvoice
"""
from django.db import models
from django.utils.translation import gettext_lazy as _


class InvoiceStatus(models.TextChoices):
    DRAFT = 'draft', _('پیش‌نویس')
    SENT = 'sent', _('ارسال شد')
    CONFIRMED = 'confirmed', _('تأیید شد')
    CANCELED = 'canceled', _('لغو شد')
    REJECTED = 'rejected', _('رد شد')


class TaxInvoice(models.Model):
    """صورتحساب الکترونیکی سامان"""

    store = models.ForeignKey(
        'partners.Store',
        on_delete=models.RESTRICT,
        related_name='tax_invoices',
        verbose_name=_('فروشگاه'),
    )
    sale = models.ForeignKey(
        'sales.SalesHeader',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='tax_invoices',
        verbose_name=_('سند فروش'),
    )
    saman_uid = models.CharField(
        max_length=200, blank=True, unique=True, null=True,
        verbose_name=_('UID سامان'),
    )
    invoice_status = models.CharField(
        max_length=20,
        choices=InvoiceStatus.choices,
        default=InvoiceStatus.DRAFT,
        verbose_name=_('وضعیت'),
    )
    header_data = models.JSONField(
        default=dict,
        verbose_name=_('اطلاعات سربرگ'),
        help_text=_('اطلاعات فروشنده و خریدار (استاندارد سامان)'),
    )
    body_data = models.JSONField(
        default=list,
        verbose_name=_('اقلام صورتحساب'),
        help_text=_('لیست اقلام به فرمت سامان'),
    )
    sent_at = models.DateTimeField(null=True, blank=True, verbose_name=_('زمان ارسال'))
    confirmed_at = models.DateTimeField(null=True, blank=True, verbose_name=_('زمان تأیید'))
    rejection_reason = models.TextField(blank=True, verbose_name=_('دلیل رد'))
    retry_count = models.PositiveSmallIntegerField(default=0, verbose_name=_('تعداد تلاش مجدد'))
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
        db_table = 'tax_invoices'
        verbose_name = _('صورتحساب سامان')
        verbose_name_plural = _('صورتحساب‌های سامان')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['store', 'created_at']),
            models.Index(fields=['invoice_status']),
        ]

    def __str__(self):
        return f'Invoice {self.id} - {self.store.name} - {self.invoice_status}'

    @property
    def is_confirmed(self):
        return self.invoice_status == InvoiceStatus.CONFIRMED
