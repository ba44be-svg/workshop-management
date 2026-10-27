"""
Approval Workflow Models — ApprovalQueue, ApprovalRule, ApprovalDecision
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from core.models import BaseModel


class ApprovalPriority(models.TextChoices):
    LOW = 'low', _('کم')
    MEDIUM = 'medium', _('متوسط')
    HIGH = 'high', _('بالا')
    URGENT = 'urgent', _('فوری')


class ApprovalStatus(models.TextChoices):
    PENDING = 'pending', _('در انتظار')
    REVIEWING = 'reviewing', _('در حال بررسی')
    APPROVED = 'approved', _('تأیید شد')
    REJECTED = 'rejected', _('رد شد')
    POSTED = 'posted', _('ثبت شد')


class RefDocType(models.TextChoices):
    SALES_DRAFT = 'sales_draft', _('پیش‌نویس فروش')
    STORE_ORDER = 'store_order', _('سفارش فروشگاه')
    TRANSFER = 'transfer', _('انتقال')
    MANUAL = 'manual', _('دستی')


class ApprovalQueue(BaseModel):
    """صف مرکزی تأیید مدیر"""

    ref_doc_type = models.CharField(
        max_length=50,
        choices=RefDocType.choices,
        verbose_name=_('نوع سند'),
    )
    ref_doc_id = models.BigIntegerField(verbose_name=_('شناسه سند'))
    requested_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='approval_requests',
        verbose_name=_('درخواست‌کننده'),
    )
    requested_at = models.DateTimeField(auto_now_add=True, verbose_name=_('زمان درخواست'))
    assigned_to = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='assigned_approvals',
        verbose_name=_('محول‌شده به'),
    )
    status = models.CharField(
        max_length=20,
        choices=ApprovalStatus.choices,
        default=ApprovalStatus.PENDING,
        verbose_name=_('وضعیت'),
    )
    priority = models.CharField(
        max_length=10,
        choices=ApprovalPriority.choices,
        default=ApprovalPriority.MEDIUM,
        verbose_name=_('اولویت'),
    )
    decision_reason = models.TextField(blank=True, verbose_name=_('دلیل تصمیم'))
    decided_at = models.DateTimeField(null=True, blank=True, verbose_name=_('زمان تصمیم'))
    decided_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='approval_decisions',
        verbose_name=_('تصمیم‌گیرنده'),
    )
    notes = models.TextField(blank=True, verbose_name=_('یادداشت'))

    class Meta:
        db_table = 'approval_queue'
        verbose_name = _('آیتم تأیید')
        verbose_name_plural = _('صف تأیید')
        ordering = ['-priority', '-requested_at']
        unique_together = ('ref_doc_type', 'ref_doc_id')
        indexes = [
            models.Index(fields=['status', 'priority', 'requested_at']),
            models.Index(fields=['assigned_to']),
        ]

    def __str__(self):
        return f'{self.ref_doc_type}:{self.ref_doc_id} - {self.status}'


class ApprovalRule(models.Model):
    """قوانین تأیید — تعریف خودکار آیتم‌های تأیید"""

    doc_type = models.CharField(
        max_length=50,
        choices=RefDocType.choices,
        verbose_name=_('نوع سند'),
    )
    auto_assign_to = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='+',
        verbose_name=_('محول خودکار به'),
    )
    auto_priority = models.CharField(
        max_length=10,
        choices=ApprovalPriority.choices,
        default=ApprovalPriority.MEDIUM,
        verbose_name=_('اولویت خودکار'),
    )
    is_active = models.BooleanField(default=True, verbose_name=_('فعال'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'approval_rules'
        verbose_name = _('قانون تأیید')
        verbose_name_plural = _('قوانین تأیید')
        unique_together = ('doc_type',)

    def __str__(self):
        return f'{self.doc_type} - {self.auto_priority}'
