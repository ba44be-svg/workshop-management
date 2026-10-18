"""
Production Service — منطق تولید، ساخت لات خودکار و محاسبه بهای تمام‌شده
"""
from decimal import Decimal
from typing import List, Optional
from datetime import timedelta
from django.db import transaction
from django.utils import timezone

from .models import ProductionBatch, ProductionConsumption, ProductionOutput
from apps.inventory.models import InventoryLot, InventoryMovement, Warehouse
from apps.inventory.services.fefo_service import WeightedAverageService


class ProductionService:
    """سرویس تولید — قلب منطق تولید و ساخت لات"""

    @staticmethod
    @transaction.atomic
    def create_batch(
        *,
        product_id: int,
        planned_qty: Decimal,
        notes: str = '',
        created_by=None,
    ) -> ProductionBatch:
        """ایجاد بچ تولید جدید (وضعیت: planned)"""

        batch_no = ProductionService._generate_batch_number()
        batch = ProductionBatch.objects.create(
            batch_no=batch_no,
            product_id=product_id,
            planned_qty=Decimal(planned_qty),
            actual_qty=Decimal('0'),
            waste_qty=Decimal('0'),
            status=ProductionBatch.BatchStatus.PLANNED,
            notes=notes,
            created_by=created_by,
        )
        return batch

    @staticmethod
    @transaction.atomic
    def start_batch(
        *,
        batch_id: int,
        started_by=None,
    ) -> ProductionBatch:
        """شروع بچ تولید"""

        batch = ProductionBatch.objects.select_for_update().get(id=batch_id)

        if batch.status != ProductionBatch.BatchStatus.PLANNED:
            raise ValueError(
                f'بچ {batch.batch_no} در وضعیت {batch.status} است و قابل شروع نیست'
            )

        batch.status = ProductionBatch.BatchStatus.IN_PROGRESS
        batch.start_at = timezone.now()
        batch.save(update_fields=['status', 'start_at', 'updated_at'])

        # ارسال سیگنال برای تولید سند حسابداری شروع تولید (در فاز ۴)
        return batch

    @staticmethod
    @transaction.atomic
    def consume_material(
        *,
        batch_id: int,
        material_lot_id: int,
        qty: Decimal,
        consumed_by=None,
    ) -> ProductionConsumption:
        """
        مصرف مواد اولیه برای بچ تولید.

        این متد:
        ۱. موجودی لات ماده اولیه را کاهش می‌دهد
        ۲. حرکت انبار ثبت می‌کند
        ۳. هزینه لحظه‌ای را در ProductionConsumption ذخیره می‌کند
        """

        batch = ProductionBatch.objects.select_for_update().get(id=batch_id)
        if batch.status != ProductionBatch.BatchStatus.IN_PROGRESS:
            raise ValueError(
                f'بچ {batch.batch_no} در وضعیت {batch.status} است. '
                f'ابتدا بچ را شروع کنید.'
            )

        # قفل لات ماده اولیه
        material_lot = InventoryLot.objects.select_for_update().get(id=material_lot_id)
        if material_lot.current_qty < qty:
            raise ValueError(
                f'موجودی ماده اولیه کافی نیست. '
                f'موجودی: {material_lot.current_qty}, موردنیاز: {qty}'
            )

        # محاسبه هزینه لحظه‌ای (میانگین موزون)
        cost_at_consumption = material_lot.weighted_avg_cost

        # ثبت مصرف
        consumption = ProductionConsumption.objects.create(
            batch=batch,
            material_lot=material_lot,
            qty_consumed=Decimal(qty),
            cost_at_consumption=cost_at_consumption,
            created_by=consumed_by,
        )

        # کاهش موجودی لات ماده اولیه
        material_lot.current_qty -= Decimal(qty)
        material_lot.save(update_fields=['current_qty', 'updated_at'])

        # ثبت حرکت انبار (خروج)
        InventoryMovement.objects.create(
            lot=material_lot,
            product_id=material_lot.product_id,
            warehouse_id=material_lot.warehouse_id,
            movement_type=InventoryMovement.MovementType.PRODUCTION,
            qty=-Decimal(qty),
            unit_cost=cost_at_consumption,
            ref_doc_type='production',
            ref_doc_id=batch.id,
            created_by=consumed_by,
        )

        # به‌روزرسانی موجودی تجمیعی
        ProductionService._update_stock_balance(
            product_id=material_lot.product_id,
            warehouse_id=material_lot.warehouse_id,
            qty_change=-Decimal(qty),
            value_change=-Decimal(qty) * cost_at_consumption,
            last_lot_id=material_lot.id,
        )

        return consumption

    @staticmethod
    @transaction.atomic
    def complete_batch(
        *,
        batch_id: int,
        actual_qty: Decimal,
        waste_qty: Decimal = Decimal('0'),
        completed_by=None,
    ) -> ProductionBatch:
        """
        تکمیل بچ تولید.

        این متد:
        ۱. لات جدید برای محصول نهایی می‌سازد
        ۲. موجودی لات جدید را تنظیم می‌کند
        ۳. بهای تمام‌شده میانگین موزون را محاسبه می‌کند
        ۴. ProductionOutput ثبت می‌کند
        ۵. حرکت ورود به انبار را ثبت می‌کند
        """

        batch = ProductionBatch.objects.select_for_update().get(id=batch_id)
        if batch.status != ProductionBatch.BatchStatus.IN_PROGRESS:
            raise ValueError(
                f'بچ {batch.batch_no} در وضعیت {batch.status} است. '
                f'ابتدا بچ را شروع کنید.'
            )

        # ۱. محاسبه بهای تمام‌شده کل = مجموع هزینه مواد مصرفی
        total_cost = batch.total_consumption_cost
        if actual_qty > 0:
            weighted_avg_cost = total_cost / Decimal(actual_qty)
        else:
            weighted_avg_cost = Decimal('0')

        # ۲. دریافت انبار اصلی
        main_warehouse = Warehouse.objects.get(type=Warehouse.WarehouseType.MAIN)

        # ۳. ساخت لات جدید برای محصول نهایی
        today = timezone.now().date()
        expiry_date = today + timedelta(days=batch.product.shelf_life_days)

        new_lot = InventoryLot.objects.create(
            product=batch.product,
            warehouse=main_warehouse,
            batch_no=batch.batch_no,
            production_date=today,
            expiry_date=expiry_date,
            initial_qty=Decimal(actual_qty),
            current_qty=Decimal(actual_qty),
            weighted_avg_cost=weighted_avg_cost,
            status=InventoryLot.LotStatus.ACTIVE,
            production_batch=batch,
            created_by=completed_by,
        )

        # ۴. ثبت ProductionOutput
        output = ProductionOutput.objects.create(
            batch=batch,
            product=batch.product,
            qty_produced=Decimal(actual_qty),
            qty_waste=Decimal(waste_qty),
            lot=new_lot,
            created_by=completed_by,
        )

        # ۵. ثبت حرکت ورود به انبار
        InventoryMovement.objects.create(
            lot=new_lot,
            product_id=new_lot.product_id,
            warehouse_id=main_warehouse.id,
            movement_type=InventoryMovement.MovementType.PRODUCTION,
            qty=Decimal(actual_qty),
            unit_cost=weighted_avg_cost,
            ref_doc_type='production',
            ref_doc_id=batch.id,
            created_by=completed_by,
        )

        # ۶. به‌روزرسانی موجودی تجمیعی (ورود)
        ProductionService._update_stock_balance(
            product_id=new_lot.product_id,
            warehouse_id=main_warehouse.id,
            qty_change=Decimal(actual_qty),
            value_change=Decimal(actual_qty) * weighted_avg_cost,
            last_lot_id=new_lot.id,
        )

        # ۷. به‌روزرسانی بچ
        batch.actual_qty = Decimal(actual_qty)
        batch.waste_qty = Decimal(waste_qty)
        batch.weighted_avg_cost = weighted_avg_cost
        batch.status = ProductionBatch.BatchStatus.COMPLETED
        batch.end_at = timezone.now()
        batch.save(update_fields=[
            'actual_qty', 'waste_qty', 'weighted_avg_cost',
            'status', 'end_at', 'updated_at',
        ])

        # ۸. ثبت Barcode برای لات جدید (در فاز ۷)
        # from apps.products.models import Barcode
        # Barcode.objects.create(...)

        # ۹. ارسال سیگنال برای سند حسابداری (در فاز ۴)
        from .signals import batch_completed
        batch_completed.send(sender=ProductionBatch, instance=batch)

        return batch

    @staticmethod
    @transaction.atomic
    def cancel_batch(
        *,
        batch_id: int,
        reason: str = '',
        canceled_by=None,
    ) -> ProductionBatch:
        """لغو بچ تولید"""
        batch = ProductionBatch.objects.get(id=batch_id)
        if batch.status == ProductionBatch.BatchStatus.COMPLETED:
            raise ValueError('بچ تکمیل‌شده قابل لغو نیست')
        batch.status = ProductionBatch.BatchStatus.CANCELED
        if reason:
            batch.notes = f'{batch.notes}\n\nلغو: {reason}'.strip()
        batch.save(update_fields=['status', 'notes', 'updated_at'])
        return batch

    @staticmethod
    def _update_stock_balance(*, product_id, warehouse_id, qty_change, value_change, last_lot_id=None):
        """به‌روزرسانی موجودی تجمیعی"""
        from django.db.models import F
        from apps.inventory.models import StockBalance
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

    @staticmethod
    def _generate_batch_number() -> str:
        """تولید شماره بچ یکتا"""
        year = timezone.now().year
        count = ProductionBatch.objects.count() + 1
        return f'BATCH-{year}-{count:06d}'

    @staticmethod
    def get_production_report(date_from=None, date_to=None):
        """گزارش تولید در بازه زمانی"""
        from django.db.models import Sum, Count, Avg
        from django.utils import timezone
        from datetime import timedelta

        if date_to is None:
            date_to = timezone.now().date()
        if date_from is None:
            date_from = date_to - timedelta(days=30)

        batches = ProductionBatch.objects.filter(
            end_at__date__gte=date_from,
            end_at__date__lte=date_to,
            status=ProductionBatch.BatchStatus.COMPLETED,
        )

        summary = batches.aggregate(
            total_batches=Count('id'),
            total_produced=Sum('actual_qty'),
            total_waste=Sum('waste_qty'),
            avg_cost=Avg('weighted_avg_cost'),
        )

        return {
            'date_from': date_from.isoformat(),
            'date_to': date_to.isoformat(),
            'total_batches': summary['total_batches'] or 0,
            'total_produced': str(summary['total_produced'] or 0),
            'total_waste': str(summary['total_waste'] or 0),
            'avg_cost': str(summary['avg_cost'] or 0),
            'waste_percentage': (
                float(summary['total_waste'] or 0) /
                float((summary['total_produced'] or 0) + (summary['total_waste'] or 0)) * 100
                if (summary['total_produced'] or 0) + (summary['total_waste'] or 0) > 0
                else 0
            ),
        }
