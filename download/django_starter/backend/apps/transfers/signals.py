"""
Transfers Signals
"""
from django.dispatch import Signal
from django.dispatch import receiver


# سیگنال سفارشی برای تکمیل انتقال
transfer_completed = Signal()


@receiver(transfer_completed, sender='apps.transfers.signals')
def on_transfer_completed(sender, **kwargs):
    """هنگام تکمیل انتقال"""
    # در فاز ۴: ارسال سیگنال برای سند حسابداری انتقال
    pass
