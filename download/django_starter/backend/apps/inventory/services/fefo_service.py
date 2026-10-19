"""
FEFO Service — الگوریتم First-Expired-First-Out
قلب منطق کسب‌وکار برای انتخاب لات‌ها در فروش
"""
from decimal import Decimal
from typing import List
from dataclasses import dataclass
from django.db import transaction
from django.utils import timezone
from django.db import models
from core.exceptions import InsufficientStockError
from ..models import InventoryLot, InventoryMovement, StockBalance


@dataclass
class AllocationItem:
    """آیتم تخصیص FEFO"""
    lot_id: int
    qty: Decimal
    unit_cost: Decimal
    expiry_date: str
    days_to_expiry: int
    batch_no: str = ''


@dataclass
class FEFOAllocationResult:
    """نتیجه تخصیص FEFO"""
    allocated: bool
    total_allocated_qty: Decimal
    allocations: List[AllocationItem]
    warning: str = None


class FEFOService:
    """سرویس FEFO"""

    NEAR_EXPIRY_THRESHOLD_DAYS = 3

    @classmethod
    @transaction.atomic
    def allocate_lots(
        cls,
        *,
        product_id: int,
        warehouse_id: int,
        qty_needed: Decimal,
        sale_date=None,
        reserve: bool = False,
    ) -> FEFOAllocationResult:
        """
        انتخاب لات‌ها بر اساس FEFO برای یک فروش.
        """
        if sale_date is None:
            sale_date = timezone.now().date()

        lots_qs = InventoryLot.objects.filter(
            product_id=product_id,
            warehouse_id=warehouse_id,
            current_qty__gt=0,
            status=InventoryLot.LotStatus.ACTIVE,
            expiry_date__gt=sale_date,
            deleted_at__isnull=True,
        ).order_by('expiry_date', 'production_date')

        if reserve:
            lots_qs = lots_qs.select_for_update()

        lots = list(lots_qs)

        if not lots:
            raise InsufficientStockError(
                f'موجودی برای محصول {product_id} در انبار {warehouse_id} موجود نیست'
            )

        nearest_expiry = lots[0].expiry_date
        days_to_expiry = (nearest_expiry - sale_date).days
        warning = None
        if days_to_expiry <= cls.NEAR_EXPIRY_THRESHOLD_DAYS:
            warning = (
                f'لات نزدیک به انقضا — محصول: {product_id}, '
                f'انقضا: {nearest_expiry} ({days_to_expiry} روز باقی‌مانده)'
            )

        allocations = []
        remaining = Decimal(qty_needed)
        total_allocated = Decimal('0')

        for lot in lots:
            if remaining <= 0:
                break
            take = min(lot.current_qty, remaining)
            allocations.append(AllocationItem(
                lot_id=lot.id,
                qty=take,
                unit_cost=lot.weighted_avg_cost,
                expiry_date=lot.expiry_date.isoformat(),
                days_to_expiry=days_to_expiry,
                batch_no=lot.batch_no,
            ))
            remaining -= take
            total_allocated += take

        if remaining > 0:
            total_available = sum(lot.current_qty for lot in lots)
            raise InsufficientStockError(
                f'موجودی ناکافی: {total_available} موجود، '
                f'{qty_needed} موردنیاز. کمبود: {remaining}'
            )

        return FEFOAllocationResult(
            allocated=True,
            total_allocated_qty=total_allocated,
            allocations=allocations,
            warning=warning,
        )

    @classmethod
    @transaction.atomic
    def consume_lots(
        cls,
        *,
        allocations: List[AllocationItem],
        warehouse_id: int,
        movement_type: str = 'out',
        ref_doc_type: str,
        ref_doc_id: int,
        created_by=None,
    ) -> List[InventoryMovement]:
        """مصرف لات‌های تخصیص‌داده‌شده (پس از تأیید فروش)."""
        movements = []
        for alloc in allocations:
            lot = InventoryLot.objects.select_for_update().get(id=alloc.lot_id)
            lot.current_qty -= alloc.qty
            lot.save(update_fields=['current_qty', 'updated_at'])

            movement = InventoryMovement.objects.create(
                lot_id=lot.id,
                product_id=lot.product_id,
                warehouse_id=warehouse_id,
                movement_type=movement_type,
                qty=-alloc.qty,
                unit_cost=alloc.unit_cost,
                ref_doc_type=ref_doc_type,
                ref_doc_id=ref_doc_id,
                created_by=created_by,
            )
            movements.append(movement)

            cls._update_stock_balance(
                product_id=lot.product_id,
                warehouse_id=warehouse_id,
                qty_change=-alloc.qty,
                value_change=-alloc.qty * alloc.unit_cost,
                last_lot_id=lot.id,
            )
        return movements

    @classmethod
    def _update_stock_balance(cls, *, product_id, warehouse_id,
                                qty_change, value_change, last_lot_id=None):
        """به‌روزرسانی موجودی تجمیعی (Upsert)"""
        from django.db.models import F
        stock, created = StockBalance.objects.select_for_update().get_or_create(
            product_id=product_id,
            warehouse_id=warehouse_id,
            defaults={
                'total_qty': qty_change,
                'total_value': value_change,
                'last_lot_id': last_lot_id,
            },
        )
        if not created:
            stock.total_qty = F('total_qty') + qty_change
            stock.total_value = F('total_value') + value_change
            stock.last_lot_id = last_lot_id
            stock.save()

    @classmethod
    def find_near_expiry_lots(cls, days_threshold: int = 5):
        """یافتن لات‌های نزدیک به انقضا (برای Transfer Suggester)"""
        from datetime import timedelta
        cutoff = timezone.now().date() + timedelta(days=days_threshold)
        return InventoryLot.objects.filter(
            expiry_date__lte=cutoff,
            expiry_date__gt=timezone.now().date(),
            current_qty__gt=0,
            status=InventoryLot.LotStatus.ACTIVE,
            deleted_at__isnull=True,
        ).select_related(
            'product', 'warehouse', 'warehouse__store'
        ).order_by('expiry_date')

    @classmethod
    def trace_lot_history(cls, lot_id: int):
        """ردیابی تاریخچه کامل یک لات — برای Trace-back."""
        lot = InventoryLot.objects.select_related(
            'product', 'warehouse', 'production_batch'
        ).get(id=lot_id)

        movements = InventoryMovement.objects.filter(
            lot_id=lot_id,
        ).select_related('product', 'warehouse').order_by('created_at')

        return {
            'lot': {
                'id': lot.id,
                'batch_no': lot.batch_no,
                'product': {
                    'id': lot.product.id,
                    'code': lot.product.code,
                    'name': lot.product.name,
                },
                'warehouse': lot.warehouse.code,
                'production_date': lot.production_date.isoformat(),
                'expiry_date': lot.expiry_date.isoformat(),
                'initial_qty': str(lot.initial_qty),
                'current_qty': str(lot.current_qty),
                'weighted_avg_cost': str(lot.weighted_avg_cost),
                'status': lot.status,
            },
            'movements': [
                {
                    'id': m.id,
                    'type': m.movement_type,
                    'qty': str(m.qty),
                    'unit_cost': str(m.unit_cost) if m.unit_cost else None,
                    'ref_doc_type': m.ref_doc_type,
                    'ref_doc_id': m.ref_doc_id,
                    'created_at': m.created_at.isoformat(),
                }
                for m in movements
            ],
        }


class WeightedAverageService:
    """سرویس محاسبه میانگین موزون"""

    @staticmethod
    @transaction.atomic
    def update_weighted_average(*, lot_id, in_qty, in_unit_cost):
        """محاسبه میانگین موزون پس از ورود کالا."""
        lot = InventoryLot.objects.select_for_update().get(id=lot_id)

        existing_qty = lot.current_qty or Decimal(0)
        old_avg = lot.weighted_avg_cost or Decimal(0)

        if existing_qty + in_qty == 0:
            new_avg = Decimal(0)
        else:
            new_avg = (
                (existing_qty * old_avg) + (in_qty * in_unit_cost)
            ) / (existing_qty + in_qty)

        lot.weighted_avg_cost = new_avg
        lot.current_qty = existing_qty + in_qty
        lot.save(update_fields=['weighted_avg_cost', 'current_qty', 'updated_at'])

        return new_avg

    @staticmethod
    def get_current_cost(product_id: int, warehouse_id: int) -> Decimal:
        """دریافت بهای تمام‌شده فعلی محصول در انبار"""
        lot = InventoryLot.objects.filter(
            product_id=product_id,
            warehouse_id=warehouse_id,
            current_qty__gt=0,
            status=InventoryLot.LotStatus.ACTIVE,
            deleted_at__isnull=True,
        ).order_by('-updated_at').first()
        return lot.weighted_avg_cost if lot else Decimal(0)
