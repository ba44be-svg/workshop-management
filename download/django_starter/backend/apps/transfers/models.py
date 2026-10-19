"""
Transfers Models — TransferHeader, TransferLine, TransferSuggestion
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from core.models import BaseModel, AuditedManager


class TransferHeader(BaseModel):
    """سند انتقال بین دو فروشگاه"""

    objects = AuditedManager()
    all_objects = models.Manager()

    class TransferStatus(models.TextChoices):
        PENDING = 'pending', _('در انتظار')
        REVIEWING = 'reviewing', _('در حال بررسی')
        APPROVED = 'approved', _('تأیید شد')
        REJECTED = 'rejected', _('رد شد')
        IN_TRANSIT = 'in_transit', _('در حال انتقال')
        RECEIVED = 'received', _('دریافت شد')
        CANCELED = 'canceled', _('لغو شد')

    transfer_no = models.CharField(max_length=50, unique=True, verbose_name=_('شماره انتقال'))
    from_store = models.ForeignKey(
        'partners.Store',
        on_delete=models.RESTRICT,
        related_name='outgoing_transfers',
        verbose_name=_('فروشگاه مبدأ'),
    )
    to_store = models.ForeignKey(
        'partners.Store',
        on_delete=models.RESTRICT,
        related_name='incoming_transfers',
        verbose_name=_('فروشگاه مقصد'),
    )
    transfer_date = models.DateField(verbose_name=_('تاریخ انتقال'))
    status = models.CharField(
        max_length=20,
        choices=TransferStatus.choices,
        default=TransferStatus.PENDING,
        verbose_name=_('وضعیت'),
    )
    initiator = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='initiated_transfers',
        verbose_name=_('آغازگر'),
    )
    receiver = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='received_transfers',
        verbose_name=_('گیرنده'),
    )
    reason = models.TextField(blank=True, verbose_name=_('دلیل'))
    journal = models.ForeignKey(
        'accounting.JournalHeader',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='transfers',
        verbose_name=_('سند حسابداری'),
    )
    notes = models.TextField(blank=True, verbose_name=_('یادداشت'))

    class Meta:
        db_table = 'transfer_headers'
        verbose_name = _('انتقال')
        verbose_name_plural = _('انتقال‌ها')
        ordering = ['-transfer_date', '-id']
        indexes = [
            models.Index(fields=['from_store', 'transfer_date']),
            models.Index(fields=['to_store', 'transfer_date']),
            models.Index(fields=['status']),
        ]
        constraints = [
            models.CheckConstraint(
                check=~models.Q(from_store=models.F('to_store')),
                name='transfer_different_stores',
            ),
        ]

    def __str__(self):
        return f'{self.transfer_no}: {self.from_store.code} → {self.to_store.code}'


class TransferLine(BaseModel):
    """اقلام انتقال با لات مشخص"""

    transfer = models.ForeignKey(
        TransferHeader,
        on_delete=models.CASCADE,
        related_name='lines',
        verbose_name=_('انتقال'),
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.RESTRICT,
        related_name='transfer_lines',
        verbose_name=_('محصول'),
    )
    lot = models.ForeignKey(
        'inventory.InventoryLot',
        on_delete=models.RESTRICT,
        related_name='transfer_lines',
        verbose_name=_('لات'),
    )
    qty = models.DecimalField(
        max_digits=14, decimal_places=3,
        verbose_name=_('تعداد'),
    )
    expiry_date = models.DateField(
        verbose_name=_('تاریخ انقضا'),
        help_text=_('Snapshot برای نمایش'),
    )

    class Meta:
        db_table = 'transfer_lines'
        verbose_name = _('قلم انتقال')
        verbose_name_plural = _('اقلام انتقال')
        indexes = [
            models.Index(fields=['transfer']),
            models.Index(fields=['lot']),
        ]

    def __str__(self):
        return f'{self.product.code} x {self.qty} (Lot {self.lot.batch_no})'


class TransferSuggestion(models.Model):
    """پیشنهاد انتقال FEFO — تولیدشده به‌صورت خودکار"""

    class Urgency(models.TextChoices):
        LOW = 'low', _('کم')
        MEDIUM = 'medium', _('متوسط')
        HIGH = 'high', _('بالا')
        URGENT = 'urgent', _('فوری')

    lot = models.ForeignKey(
        'inventory.InventoryLot',
        on_delete=models.CASCADE,
        related_name='transfer_suggestions',
        verbose_name=_('لات'),
    )
    from_store = models.ForeignKey(
        'partners.Store',
        on_delete=models.CASCADE,
        related_name='outgoing_suggestions',
        verbose_name=_('فروشگاه مبدأ'),
    )
    to_store = models.ForeignKey(
        'partners.Store',
        on_delete=models.CASCADE,
        related_name='incoming_suggestions',
        verbose_name=_('فروشگاه مقصد'),
    )
    qty = models.DecimalField(
        max_digits=14, decimal_places=3,
        verbose_name=_('تعداد پیشنهادی'),
    )
    urgency = models.CharField(
        max_length=10,
        choices=Urgency.choices,
        default=Urgency.MEDIUM,
        verbose_name=_('اولویت'),
    )
    score = models.DecimalField(
        max_digits=10, decimal_places=4,
        default=0,
        verbose_name=_('امتیاز اولویت'),
    )
    is_approved = models.BooleanField(
        default=False,
        verbose_name=_('تأیید شده'),
    )
    is_processed = models.BooleanField(
        default=False,
        verbose_name=_('پردازش شده'),
        help_text=_('آیا سند انتقال ساخته شده؟'),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, verbose_name=_('یادداشت'))

    class Meta:
        db_table = 'transfer_suggestions'
        verbose_name = _('پیشنهاد انتقال')
        verbose_name_plural = _('پیشنهادهای انتقال')
        ordering = ['-score', '-urgency', '-created_at']
        indexes = [
            models.Index(fields=['is_approved', 'is_processed']),
            models.Index(fields=['urgency']),
            models.Index(fields=['-score']),
        ]

    def __str__(self):
        return f'{self.lot.product.code} {self.qty} from {self.from_store.code} to {self.to_store.code}'

    @property
    def days_to_expiry(self):
        """تعداد روز تا انقضا"""
        from django.utils import timezone
        return (self.lot.expiry_date - timezone.now().date()).days
