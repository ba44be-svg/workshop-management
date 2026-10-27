"""
Inventory Signals
"""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from decimal import Decimal
from .models import InventoryLot, InventoryMovement, StockBalance
from .services.fefo_service import WeightedAverageService, FEFOService


@receiver(post_save, sender=InventoryMovement)
def handle_movement_created(sender, instance, created, **kwargs):
    """هنگام ثبت حرکت انبار، میانگین موزون و stock_balance را به‌روزرسانی کن"""
    if not created:
        return

    # اگر حرکت ورود بود، میانگین موزون را به‌روز کن
    if instance.movement_type == 'in' and instance.qty > 0:
        WeightedAverageService.update_weighted_average(
            lot_id=instance.lot_id,
            in_qty=instance.qty,
            in_unit_cost=instance.unit_cost or Decimal(0),
        )


@receiver(post_save, sender=InventoryLot)
def update_stock_balance_on_lot_save(sender, instance, **kwargs):
    """هنگام تغییر لات، stock_balance را به‌روز کن"""
    # این signal بیشتر برای پیگیری دستی تغییرات است
    # (معمولاً update از طریق service انجام می‌شود)
    pass
