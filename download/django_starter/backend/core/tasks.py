"""
Celery tasks — scheduled tasks
"""
from celery import shared_task
from django.utils import timezone
from datetime import timedelta


@shared_task
def flag_expired_lots():
    """علامت‌گذاری لات‌های منقضی (هر شب اجرا می‌شود)"""
    from apps.inventory.models import InventoryLot
    updated = InventoryLot.objects.filter(
        expiry_date__lt=timezone.now().date(),
        status='active',
        current_qty__gt=0,
    ).update(status='expired')
    return f'Flagged {updated} lots as expired'


@shared_task
def send_visit_reminders():
    """یادآوری سرکشی به عوامل پخش (هر شب ساعت ۲۳)"""
    from apps.notifications.services import NotificationService
    from apps.partners.models import Distributor
    from apps.dispatch.models import Route

    tomorrow = (timezone.now() + timedelta(days=1)).date()
    day_of_week = tomorrow.weekday()

    routes = Route.objects.filter(day_of_week=day_of_week, is_active=True)
    sent_count = 0
    for route in routes:
        NotificationService.send_sms(
            recipient=route.distributor.mobile,
            template='visit_reminder',
            context={
                'distributor_name': route.distributor.name,
                'date': tomorrow.strftime('%Y-%m-%d'),
                'start_time': '08:00',
                'first_store': route.store_sequence[0]['store_name'] if route.store_sequence else 'نامشخص',
            },
        )
        sent_count += 1
    return f'Sent {sent_count} visit reminders'


@shared_task
def generate_transfer_suggestions():
    """پیشنهاد انتقال FEFO (هر شب اجرا می‌شود)"""
    from apps.loyalty.services.smart_reorder import generate_transfer_suggestions as impl
    count = impl()
    return f'Generated {count} transfer suggestions'


@shared_task
def send_push_notification(user_id, title, body, data=None):
    """ارسال Push Notification"""
    from apps.notifications.services import PushService
    return PushService.send_to_user(user_id, title, body, data)


@shared_task
def retry_failed_sms():
    """تلاش مجدد برای پیامک‌های ناموفق"""
    from apps.notifications.models import SmsQueue
    failed = SmsQueue.objects.filter(
        status='failed',
        retry_count__lt=4,
    )
    for sms in failed:
        sms.next_retry_at = timezone.now()
        sms.save()
    return f'Queued {failed.count()} SMS for retry'


@shared_task
def retry_failed_tax_invoices():
    """تلاش مجدد برای صورتحساب‌های ناموفق سامان"""
    from apps.saman_tax.services import SamanService
    SamanService.retry_failed_invoices()
