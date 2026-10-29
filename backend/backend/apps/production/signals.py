"""
Production Signals
"""
from django.db.models.signals import Signal
from django.dispatch import receiver
from .models import ProductionBatch


# سیگنال سفارشی برای تکمیل بچ تولید
batch_completed = Signal()
batch_canceled = Signal()


@receiver(batch_completed, sender=ProductionBatch)
def on_batch_completed(sender, instance, **kwargs):
    """هنگام تکمیل بچ تولید"""
    # در فاز ۴: ارسال سیگنال برای سند حسابداری تولید
    # در فاز ۷: ساخت بارکد برای لات جدید
    pass
