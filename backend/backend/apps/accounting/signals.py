"""
Accounting Signals — دریافت سیگنال‌های فروش/برگشت/پرداخت
برای ثبت خودکار سند حسابداری
"""
import logging
from django.dispatch import receiver
from apps.sales.signals import sale_posted, return_posted

logger = logging.getLogger(__name__)


@receiver(sale_posted)
def on_sale_posted(sender, **kwargs):
    """وقتی فروش ثبت شد، سند حسابداری خودکار بساز"""
    sale = kwargs.get('instance')
    if sale and kwargs.get('created'):
        try:
            from .services import JournalService
            JournalService.create_sale_journal(sale)
        except Exception as e:
            logger.error(
                f'Failed to create journal for sale {sale.sale_no}: {e}'
            )


@receiver(return_posted)
def on_return_posted(sender, **kwargs):
    """وقتی برگشت ثبت شد، سند معکوس بساز"""
    return_header = kwargs.get('instance')
    if return_header and kwargs.get('created'):
        try:
            from .services import JournalService
            JournalService.create_return_journal(return_header)
        except Exception as e:
            logger.error(
                f'Failed to create journal for return {return_header.return_no}: {e}'
            )
