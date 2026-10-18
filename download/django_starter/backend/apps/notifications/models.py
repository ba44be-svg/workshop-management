"""
Notifications Models — SmsTemplate, SmsQueue, PushNotification, NotificationSchedule
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from core.models import BaseModel


class NotificationScenario(models.TextChoices):
    VISIT_REMINDER = 'visit_reminder', _('یادآوری سرکشی')
    SALE_CONFIRMATION = 'sale_confirmation', _('تأیید فروش')
    EXPIRY_ALERT = 'expiry_alert', _('هشدار انقضا')
    TRANSFER_REQUEST = 'transfer_request', _('درخواست انتقال')
    LOW_STOCK = 'low_stock', _('کمبود موجودی')
    JOURNAL_ERROR = 'journal_error', _('خطای توازن سند')
    ORDER_APPROVED = 'order_approved', _('تأیید سفارش')
    ORDER_REJECTED = 'order_rejected', _('رد سفارش')
    PAYMENT_SUCCESS = 'payment_success', _('تأیید پرداخت')
    TIER_UPGRADE = 'tier_upgrade', _('ارتقاء لایه')
    DRAFT_REJECTED = 'draft_rejected', _('رد پیش‌نویس')


class NotificationStatus(models.TextChoices):
    QUEUED = 'queued', _('در صف')
    SENT = 'sent', _('ارسال شد')
    DELIVERED = 'delivered', _('تحویل شد')
    FAILED = 'failed', _('ناموفق')
    READ = 'read', _('خوانده شد')


class NotificationChannel(models.TextChoices):
    SMS = 'sms', _('پیامک')
    PUSH = 'push', _('Push Notification')
    BOTH = 'both', _('هر دو')


class SmsTemplate(models.Model):
    """قالب‌های پیامک با placeholder‌های Jinja2"""

    code = models.CharField(max_length=50, unique=True, verbose_name=_('کد'))
    name = models.CharField(max_length=200, verbose_name=_('نام'))
    template_text = models.TextField(
        verbose_name=_('متن قالب'),
        help_text=_('با placeholder‌های Jinja2: {{name}}, {{amount}}, etc.'),
    )
    active = models.BooleanField(default=True, verbose_name=_('فعال'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'sms_templates'
        verbose_name = _('قالب پیامک')
        verbose_name_plural = _('قالب‌های پیامک')
        ordering = ['code']

    def __str__(self):
        return f'{self.code} - {self.name}'

    def render(self, context: dict) -> str:
        """رندر کردن قالب با داده‌های context"""
        from jinja2 import Template
        template = Template(self.template_text)
        return template.render(**context)


class SmsQueue(models.Model):
    """صف ارسال پیامک"""

    recipient = models.CharField(max_length=20, verbose_name=_('گیرنده'))
    template = models.ForeignKey(
        SmsTemplate,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='queue_items',
        verbose_name=_('قالب'),
    )
    context_data = models.JSONField(
        default=dict, blank=True,
        verbose_name=_('داده‌های placeholder'),
    )
    raw_text = models.TextField(
        blank=True,
        verbose_name=_('متن خام'),
        help_text=_('اگر قالب استفاده نشود'),
    )
    status = models.CharField(
        max_length=20,
        choices=NotificationStatus.choices,
        default=NotificationStatus.QUEUED,
        verbose_name=_('وضعیت'),
    )
    scheduled_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('زمان برنامه‌ریزی'),
    )
    sent_at = models.DateTimeField(null=True, blank=True, verbose_name=_('زمان ارسال'))
    delivered_at = models.DateTimeField(null=True, blank=True, verbose_name=_('زمان تحویل'))
    message_id = models.CharField(
        max_length=100, blank=True,
        verbose_name=_('شناسه از پروایدر'),
    )
    provider = models.CharField(
        max_length=20, default='kavenegar',
        verbose_name=_('پروایدر'),
    )
    retry_count = models.PositiveSmallIntegerField(
        default=0,
        verbose_name=_('تعداد تلاش مجدد'),
    )
    next_retry_at = models.DateTimeField(null=True, blank=True, verbose_name=_('تلاش بعدی'))
    error_message = models.TextField(blank=True, verbose_name=_('خطا'))
    related_user = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='+',
        verbose_name=_('کاربر مرتبط'),
    )
    related_doc_type = models.CharField(max_length=50, blank=True, verbose_name=_('نوع سند مرتبط'))
    related_doc_id = models.BigIntegerField(null=True, blank=True, verbose_name=_('شناسه سند مرتبط'))

    class Meta:
        db_table = 'sms_queue'
        verbose_name = _('صف پیامک')
        verbose_name_plural = _('صف پیامک')
        ordering = ['-scheduled_at']
        indexes = [
            models.Index(fields=['status', 'scheduled_at']),
            models.Index(fields=['next_retry_at']),
        ]

    def __str__(self):
        return f'{self.recipient} - {self.status}'

    @property
    def message_text(self) -> str:
        """متن نهایی پیامک"""
        if self.raw_text:
            return self.raw_text
        if self.template and self.context_data:
            return self.template.render(self.context_data)
        return ''


class PushNotification(models.Model):
    """لاگ Push Notification با Firebase Cloud Messaging"""

    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='push_notifications',
        verbose_name=_('کاربر'),
    )
    title = models.CharField(max_length=200, verbose_name=_('عنوان'))
    body = models.TextField(verbose_name=_('متن'))
    data = models.JSONField(default=dict, blank=True, verbose_name=_('داده‌های اضافه'))
    status = models.CharField(
        max_length=20,
        choices=NotificationStatus.choices,
        default=NotificationStatus.QUEUED,
        verbose_name=_('وضعیت'),
    )
    scheduled_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('زمان برنامه‌ریزی'),
    )
    sent_at = models.DateTimeField(null=True, blank=True, verbose_name=_('زمان ارسال'))
    delivered_at = models.DateTimeField(null=True, blank=True, verbose_name=_('زمان تحویل'))
    read_at = models.DateTimeField(null=True, blank=True, verbose_name=_('زمان خواندن'))
    fcm_message_id = models.CharField(
        max_length=200, blank=True,
        verbose_name=_('شناسه FCM'),
    )
    related_doc_type = models.CharField(max_length=50, blank=True, verbose_name=_('نوع سند مرتبط'))
    related_doc_id = models.BigIntegerField(null=True, blank=True, verbose_name=_('شناسه سند مرتبط'))

    class Meta:
        db_table = 'push_notifications'
        verbose_name = _('Push Notification')
        verbose_name_plural = _('Push Notifications')
        ordering = ['-scheduled_at']
        indexes = [
            models.Index(fields=['user', 'scheduled_at']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f'{self.user.username} - {self.title}'


class NotificationSchedule(models.Model):
    """زمان‌بندی اعلان‌ها با Celery Beat"""

    scenario = models.CharField(
        max_length=50,
        choices=NotificationScenario.choices,
        verbose_name=_('سناریو'),
    )
    recipient_type = models.CharField(
        max_length=50,
        verbose_name=_('نوع گیرنده'),
        help_text='distributor, store, manager, etc.',
    )
    recipient_id = models.BigIntegerField(
        null=True, blank=True,
        verbose_name=_('شناسه گیرنده'),
    )
    channel = models.CharField(
        max_length=10,
        choices=NotificationChannel.choices,
        default=NotificationChannel.BOTH,
        verbose_name=_('کانال'),
    )
    cron_expression = models.CharField(
        max_length=50, blank=True,
        verbose_name=_('عبارت cron'),
        help_text=_('مثلاً "0 8 * * *" برای ۸ صبح هر روز'),
    )
    is_active = models.BooleanField(default=True, verbose_name=_('فعال'))
    last_run_at = models.DateTimeField(null=True, blank=True, verbose_name=_('آخرین اجرا'))
    next_run_at = models.DateTimeField(null=True, blank=True, verbose_name=_('اجرای بعدی'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'notification_schedules'
        verbose_name = _('زمان‌بندی اعلان')
        verbose_name_plural = _('زمان‌بندی اعلان‌ها')
        ordering = ['next_run_at']
        indexes = [
            models.Index(fields=['is_active', 'next_run_at']),
        ]

    def __str__(self):
        return f'{self.scenario} - {self.recipient_type}'
