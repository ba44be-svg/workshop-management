"""
Workshop Signals —
- سیگنال‌های سفارشی برای خرید/حواله/برگشت کارگاه (ارسال پس از commit موفق)
- post_save روی Contractor: ساخت خودکار تفصیلی حساب «کالای نزد کارپرداز» 140/{code}
"""
import logging
from django.db.models.signals import Signal, post_save
from django.dispatch import receiver
from .models import Contractor

logger = logging.getLogger(__name__)

# سیگنال‌های سفارشی برای ارسال پس از commit موفق
purchase_posted = Signal()
issue_posted = Signal()
return_posted = Signal()


@receiver(post_save, sender=Contractor)
def ensure_contractor_detail_account(sender, instance, created, **kwargs):
    """ساخت خودکار حساب تفصیلی برای هر کارپرداز جدید (140/{code}).

    اگر حساب والد 140 هنوز ساخته نشده باشد، این هندلر آن را skip می‌کند
    (در seed_data والد 140 باید از قبل ساخته شود).
    """
    if instance.detail_account:
        return
    try:
        from apps.accounting.services import JournalService
        detail = JournalService.get_or_create_detail_account(
            parent_code=JournalService.ACCOUNT_CODES['workshop_goods'],
            child_code=instance.code,
            name=f'کالای نزد کارپرداز - {instance.name}',
            acc_type='asset',
            description=f'تفصیلی کارپرداز {instance.code}',
            created_by=getattr(instance, 'created_by', None),
        )
        # آپدیت مستقیم برای جلوگیری از ارسال مجدد سیگنال
        Contractor.objects.filter(pk=instance.pk).update(detail_account=detail)
        instance.detail_account = detail
    except Exception as e:
        logger.warning(
            f'Could not auto-create detail_account for contractor {instance.code}: {e}'
        )
