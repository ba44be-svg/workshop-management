"""
Sales Signals — یکپارچگی انبار-حسابداری
"""
from django.db.models.signals import Signal
from django.dispatch import receiver
from .models import SalesHeader, ReturnHeader


# سیگنال سفارشی برای ارسال پس از commit موفق فروش
sale_posted = Signal()
return_posted = Signal()


@receiver(sale_posted, sender=SalesHeader)
def create_sale_journal(sender, instance, created, **kwargs):
    """ثبت خودکار سند حسابداری پس از commit فروش"""
    if not created:
        return

    # این Signal توسط Accounting Service دریافت می‌شود
    # در فاز ۴ پیاده‌سازی خواهد شد
    try:
        from apps.accounting.services import JournalService
        JournalService.create_sale_journal(instance)
    except ImportError:
        # Accounting Service هنوز پیاده‌سازی نشده
        pass


@receiver(return_posted, sender=ReturnHeader)
def create_return_journal(sender, instance, created, **kwargs):
    """ثبت خودکار سند معکوس حسابداری پس از commit برگشت"""
    if not created:
        return
    try:
        from apps.accounting.services import JournalService
        JournalService.create_return_journal(instance)
    except ImportError:
        pass
