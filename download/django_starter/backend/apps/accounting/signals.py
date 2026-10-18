"""
Accounting Signals — دریافت سیگنال‌های فروش/برگشت/پرداخت
"""
from django.dispatch import receiver
from .services import JournalService


@receiver(sale_posted, sender='apps.sales.signals')
def on_sale_posted(sender, **kwargs):
    """وقتی فروش ثبت شد، سند حسابداری خودکار بساز"""
    sale = kwargs.get('instance')
    if sale and kwargs.get('created'):
        try:
            JournalService.create_sale_journal(sale)
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(
                f'Failed to create journal for sale {sale.sale_no}: {e}'
            )


@receiver(return_posted, sender='apps.sales.signals')
def on_return_posted(sender, **kwargs):
    """وقتی برگشت ثبت شد، سند معکوس بساز"""
    return_header = kwargs.get('instance')
    if return_header and kwargs.get('created'):
        try:
            JournalService.create_return_journal(return_header)
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(
                f'Failed to create journal for return {return_header.return_no}: {e}'
            )
