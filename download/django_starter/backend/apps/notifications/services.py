"""
Notifications Services — SMS Provider + Firebase Push Notification
"""
import logging
from typing import Optional, Dict
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from .models import (
    SmsQueue, SmsTemplate, PushNotification, NotificationSchedule,
    NotificationStatus,
)

logger = logging.getLogger(__name__)


class SMSProviderInterface:
    """رابط اصلی پروایدرهای پیامک"""

    def send(self, recipient: str, message: str, **kwargs) -> dict:
        raise NotImplementedError

    def send_template(self, recipient: str, template_code: str, context: dict) -> dict:
        raise NotImplementedError


class KavenegarProvider(SMSProviderInterface):
    """پروایدر کاوه‌نگار"""

    API_URL = "https://api.kavenegar.com/v1/{key}/verify/lookup.json"

    def __init__(self):
        self.api_key = getattr(settings, 'KAVENEGAR_API_KEY', '')

    def send(self, recipient: str, message: str, **kwargs) -> dict:
        """ارسال پیامک متن خام"""
        if not self.api_key:
            logger.error('KAVENEGAR_API_KEY not configured')
            return {'status': 'failed', 'error': 'API key not configured'}

        try:
            import requests
            url = self.API_URL.format(key=self.api_key)
            response = requests.post(url, data={
                'receptor': recipient,
                'message': message,
                'sender': kwargs.get('sender', getattr(settings, 'KAVENEGAR_SENDER', '')),
            }, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data.get('return', {}).get('status') == 200:
                return {
                    'status': 'sent',
                    'message_id': str(data['entries'][0]['messageid']),
                }
            return {'status': 'failed', 'error': str(data)}
        except Exception as e:
            logger.error(f'Kavenegar send failed: {e}')
            return {'status': 'failed', 'error': str(e)}

    def send_template(self, recipient: str, template_code: str, context: dict) -> dict:
        """ارسال با قالب کاوه‌نگار (verify/lookup)"""
        if not self.api_key:
            return {'status': 'failed', 'error': 'API key not configured'}

        try:
            import requests
            url = self.API_URL.format(key=self.api_key)
            response = requests.post(url, data={
                'receptor': recipient,
                'token': context.get('token', ''),
                'token2': context.get('token2', ''),
                'token3': context.get('token3', ''),
                'template': template_code,
            }, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data.get('return', {}).get('status') == 200:
                return {
                    'status': 'sent',
                    'message_id': str(data['entries'][0]['messageid']),
                }
            return {'status': 'failed', 'error': str(data)}
        except Exception as e:
            logger.error(f'Kavenegar template send failed: {e}')
            return {'status': 'failed', 'error': str(e)}


class FarapayamakProvider(SMSProviderInterface):
    """پروایدر فراپیامک (پشتیبان)"""

    def __init__(self):
        self.api_key = getattr(settings, 'FARAPAYAMAK_API_KEY', '')

    def send(self, recipient: str, message: str, **kwargs) -> dict:
        # پیاده‌سازی مشابه کاوه‌نگار
        try:
            import requests
            response = requests.post(
                'https://api.farapayamak.ir/api/v1/sms/send',
                json={
                    'apiKey': self.api_key,
                    'to': recipient,
                    'text': message,
                },
                timeout=10,
            )
            if response.status_code == 200:
                return {'status': 'sent', 'message_id': response.json().get('id', '')}
            return {'status': 'failed', 'error': response.text}
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}


class NotificationService:
    """سرویس اصلی اعلان — SMS + Push"""

    PROVIDERS = {
        'kavenegar': KavenegarProvider,
        'farapayamak': FarapayamakProvider,
    }

    @classmethod
    def send_sms(
        cls,
        *,
        recipient: str,
        template_code: str = None,
        context: dict = None,
        raw_text: str = None,
        related_user=None,
        related_doc_type: str = '',
        related_doc_id: int = None,
        provider: str = 'kavenegar',
        immediate: bool = False,
    ) -> SmsQueue:
        """ثبت پیامک در صف و (در صورت immediate=True) ارسال فوری"""

        # ساخت رکورد در صف
        queue_item = SmsQueue.objects.create(
            recipient=recipient,
            template_id=cls._get_template_id(template_code) if template_code else None,
            context_data=context or {},
            raw_text=raw_text or '',
            provider=provider,
            related_user=related_user,
            related_doc_type=related_doc_type,
            related_doc_id=related_doc_id,
        )

        if immediate:
            cls._process_queue_item(queue_item)
        else:
            # اضافه به Celery task برای پردازش
            from core.tasks import retry_failed_sms
            retry_failed_sms.delay()

        return queue_item

    @classmethod
    def _process_queue_item(cls, item: SmsQueue) -> bool:
        """پردازش یک آیتم صف پیامک"""

        provider_class = cls.PROVIDERS.get(item.provider)
        if not provider_class:
            item.status = NotificationStatus.FAILED
            item.error_message = f'Unknown provider: {item.provider}'
            item.save()
            return False

        provider_instance = provider_class()

        try:
            message = item.message_text
            if not message:
                item.status = NotificationStatus.FAILED
                item.error_message = 'Empty message'
                item.save()
                return False

            result = provider_instance.send(item.recipient, message)

            if result['status'] == 'sent':
                item.status = NotificationStatus.SENT
                item.message_id = result.get('message_id', '')
                item.sent_at = timezone.now()
                item.save()
                return True
            else:
                cls._mark_failed(item, result.get('error', 'Unknown error'))
                return False
        except Exception as e:
            cls._mark_failed(item, str(e))
            return False

    @staticmethod
    def _mark_failed(item: SmsQueue, error: str):
        """علامت‌گذاری آیتم به‌عنوان ناموفق با Exponential Backoff"""
        item.status = NotificationStatus.FAILED
        item.error_message = error[:500]
        item.retry_count += 1

        # تلاش مجدد با Exponential Backoff
        if item.retry_count < 4:
            delays = [1, 5, 15, 60]  # دقیقه
            delay_min = delays[min(item.retry_count - 1, len(delays) - 1)]
            item.next_retry_at = timezone.now() + timedelta(minutes=delay_min)
            item.status = NotificationStatus.QUEUED  # برگشت به صف

        item.save()

    @staticmethod
    def _get_template_id(code: str):
        """دریافت شناسه قالب بر اساس کد"""
        try:
            return SmsTemplate.objects.get(code=code).id
        except SmsTemplate.DoesNotExist:
            return None


class PushService:
    """سرویس Push Notification با Firebase"""

    _firebase_app = None

    @classmethod
    def _get_firebase_app(cls):
        """مقداردهی اولیه Firebase (lazy)"""
        if cls._firebase_app is None:
            try:
                import firebase_admin
                from firebase_admin import credentials
                cred_path = getattr(settings, 'FIREBASE_CREDENTIALS_PATH', '')
                if cred_path:
                    cred = credentials.Certificate(cred_path)
                    cls._firebase_app = firebase_admin.initialize_app(cred)
                else:
                    logger.warning('FIREBASE_CREDENTIALS_PATH not set')
            except Exception as e:
                logger.error(f'Firebase init failed: {e}')
        return cls._firebase_app

    @classmethod
    def send_to_user(
        cls,
        *,
        user_id: int,
        title: str,
        body: str,
        data: dict = None,
        related_doc_type: str = '',
        related_doc_id: int = None,
        immediate: bool = True,
    ) -> PushNotification:
        """ارسال Push Notification به یک کاربر"""

        from apps.accounts.models import User
        user = User.objects.get(id=user_id)

        # ساخت رکورد Push
        push = PushNotification.objects.create(
            user=user,
            title=title,
            body=body,
            data=data or {},
            related_doc_type=related_doc_type,
            related_doc_id=related_doc_id,
        )

        if immediate:
            cls._process_push(push)

        return push

    @classmethod
    def _process_push(cls, push: PushNotification) -> bool:
        """پردازش یک Push Notification"""

        if not push.user.fcm_token:
            logger.info(f'User {push.user.id} has no FCM token')
            return False

        app = cls._get_firebase_app()
        if not app:
            return False

        try:
            from firebase_admin import messaging

            message = messaging.Message(
                notification=messaging.Notification(title=push.title, body=push.body),
                data={k: str(v) for k, v in (push.data or {}).items()},
                token=push.user.fcm_token,
                android=messaging.AndroidConfig(priority='high'),
                apns=messaging.APNSConfig(
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(badge=1, sound='default'),
                    ),
                ),
            )

            response = messaging.send(message)
            push.fcm_message_id = response
            push.status = NotificationStatus.SENT
            push.sent_at = timezone.now()
            push.save()
            return True
        except Exception as e:
            logger.error(f'FCM send failed: {e}')
            # اگر توکن نامعتبر است، آن را پاک کن
            if 'UNREGISTERED' in str(e).upper():
                push.user.fcm_token = None
                push.user.save(update_fields=['fcm_token'])

            push.status = NotificationStatus.FAILED
            push.error_message = str(e)[:500] if hasattr(push, 'error_message') else None
            push.save()
            return False

    @classmethod
    def send_to_stores(
        cls,
        *,
        store_ids: list,
        title: str,
        body: str,
        data: dict = None,
    ):
        """ارسال گروهی به چند فروشگاه (Multicast)"""
        from apps.accounts.models import User
        from django.db.models import Q
        from apps.partners.models import Store

        # یافتن کاربران فروشگاه‌ها با FCM token
        store_owners = User.objects.filter(
            profile__store_id__in=store_ids,
            fcm_token__isnull=False,
        ).exclude(fcm_token='')

        sent_count = 0
        for user in store_owners:
            try:
                cls.send_to_user(
                    user_id=user.id, title=title, body=body, data=data,
                )
                sent_count += 1
            except Exception as e:
                logger.error(f'Failed to send push to {user.id}: {e}')

        return {
            'total_targeted': store_owners.count(),
            'sent': sent_count,
            'failed': store_owners.count() - sent_count,
        }

    @classmethod
    def mark_as_read(cls, *, push_id: int):
        """علامت‌گذاری به‌عنوان خوانده‌شده"""
        try:
            push = PushNotification.objects.get(id=push_id)
            push.status = NotificationStatus.READ
            push.read_at = timezone.now()
            push.save()
            return True
        except PushNotification.DoesNotExist:
            return False

    @classmethod
    def get_unread_count(cls, user_id: int) -> int:
        """تعداد اعلان‌های خوانده‌نشده یک کاربر"""
        return PushNotification.objects.filter(
            user_id=user_id,
            status__in=[NotificationStatus.QUEUED, NotificationStatus.SENT, NotificationStatus.DELIVERED],
        ).count()


# alias برای استفاده آسان
class NotificationServiceFull(NotificationService):
    """سرویس کامل اعلان — هم SMS هم Push"""

    @classmethod
    def notify_user(
        cls,
        *,
        user,
        scenario: str,
        context: dict,
        channel: str = 'both',
        related_doc_type: str = '',
        related_doc_id: int = None,
    ):
        """ارسال اعلان به کاربر بر اساس سناریو و کانال"""
        results = {}

        if channel in ('sms', 'both') and user.phone:
            # پیدا کردن قالب مناسب
            template_code = scenario
            results['sms'] = NotificationService.send_sms(
                recipient=user.phone,
                template_code=template_code,
                context=context,
                related_user=user,
                related_doc_type=related_doc_type,
                related_doc_id=related_doc_id,
            )

        if channel in ('push', 'both'):
            results['push'] = PushService.send_to_user(
                user_id=user.id,
                title=cls._get_push_title(scenario, context),
                body=cls._get_push_body(scenario, context),
                data=context,
                related_doc_type=related_doc_type,
                related_doc_id=related_doc_id,
            )

        return results

    @staticmethod
    def _get_push_title(scenario: str, context: dict) -> str:
        """عنوان Push بر اساس سناریو"""
        titles = {
            'visit_reminder': 'یادآوری سرکشی',
            'sale_confirmation': 'تأیید فروش',
            'expiry_alert': 'هشدار انقضا',
            'transfer_request': 'درخواست انتقال',
            'low_stock': 'کمبود موجودی',
            'journal_error': 'خطای توازن سند',
            'order_approved': 'سفارش شما تأیید شد',
            'order_rejected': 'سفارش شما رد شد',
            'payment_success': 'پرداخت دریافت شد',
            'tier_upgrade': 'ارتقاء لایه',
            'draft_rejected': 'پیش‌نویس رد شد',
        }
        return titles.get(scenario, 'اعلان')

    @staticmethod
    def _get_push_body(scenario: str, context: dict) -> str:
        """متن Push بر اساس سناریو و context"""
        if scenario == 'visit_reminder':
            return (f"{context.get('distributor_name', '')}، شروع سرکشی ساعت "
                    f"{context.get('start_time', '')}. اولین فروشگاه: "
                    f"{context.get('first_store', '')}")
        if scenario == 'sale_confirmation':
            return (f"فروش به مبلغ {context.get('total_amount', '')} با شماره "
                    f"{context.get('sale_no', '')} ثبت شد.")
        if scenario == 'expiry_alert':
            return (f"{context.get('count', '')} لات نزدیک به انقضا. اولویت: "
                    f"{context.get('highest', '')}.")
        if scenario == 'payment_success':
            return (f"پرداخت {context.get('amount', '')} ریال دریافت شد. "
                    f"کد پیگیری: {context.get('ref_id', '')}")
        if scenario == 'tier_upgrade':
            return (f"تبریک! شما به {context.get('tier_name', '')} ارتقا یافتید. "
                    f"تخفیف {context.get('discount', '')}% فعال است.")
        return 'اعلان جدید'
