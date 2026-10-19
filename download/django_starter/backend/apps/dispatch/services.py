"""
Dispatch Service — منطق پخش و بارگیری
"""
from decimal import Decimal
from typing import List
from django.db import transaction
from django.utils import timezone
from .models import DispatchHeader, DispatchLine, Vehicle, Route, SalespersonVisit
from apps.inventory.models import InventoryLot, InventoryMovement, StockBalance


class DispatchService:
    """سرویس پخش و بارگیری"""

    @staticmethod
    @transaction.atomic
    def create_dispatch(
        *,
        distributor_id: int,
        dispatch_date=None,
        vehicle_id: int = None,
        lines: List[dict],
        notes: str = '',
        created_by=None,
    ) -> DispatchHeader:
        """
        ساخت سند پخش جدید.

        این متد:
        ۱. سند پخش می‌سازد
        ۲. برای هر خط، FEFO تخصیص می‌دهد (لات‌ها مشخص‌اند)
        ۳. موجودی لات‌ها را به انبار مجازی فروشگاه مقصد منتقل می‌کند
        """

        if dispatch_date is None:
            dispatch_date = timezone.now().date()

        dispatch = DispatchHeader.objects.create(
            dispatch_no=DispatchService._generate_dispatch_number(),
            distributor_id=distributor_id,
            dispatch_date=dispatch_date,
            vehicle_id=vehicle_id,
            status=DispatchHeader.DispatchStatus.PENDING,
            notes=notes,
            created_by=created_by,
        )

        total_qty = Decimal('0')
        total_amount = Decimal('0')

        for line_data in lines:
            product_id = line_data['product_id']
            lot_id = line_data.get('lot_id')
            qty = Decimal(line_data['qty'])
            unit_price = Decimal(line_data['unit_price'])
            dest_store_id = line_data['dest_store_id']

            # اگر lot_id مشخص نشده، FEFO تخصیص بده
            if not lot_id:
                from apps.inventory.services.fefo_service import FEFOService
                alloc = FEFOService.allocate_lots(
                    product_id=product_id,
                    warehouse_id=DispatchService._get_main_warehouse_id(),
                    qty_needed=qty,
                )
                if len(alloc.allocations) != 1:
                    raise ValueError(
                        f'محصول {product_id}: تخصیص از چند لات پشتیبانی نمی‌شود'
                        f' در این endpoint. لطفاً lot_id را مشخص کنید.'
                    )
                lot_id = alloc.allocations[0].lot_id

            # ساخت خط پخش
            line = DispatchLine.objects.create(
                dispatch=dispatch,
                product_id=product_id,
                lot_id=lot_id,
                qty=qty,
                unit_price=unit_price,
                dest_store_id=dest_store_id,
                created_by=created_by,
            )

            total_qty += qty
            total_amount += line.line_total

            # انتقال موجودی از انبار اصلی به انبار مجازی فروشگاه مقصد
            DispatchService._transfer_lot_to_store(
                lot_id=lot_id,
                qty=qty,
                store_id=dest_store_id,
                dispatch_id=dispatch.id,
                created_by=created_by,
            )

        # به‌روزرسانی مجموع
        dispatch.total_qty = total_qty
        dispatch.total_amount = total_amount
        dispatch.save(update_fields=['total_qty', 'total_amount', 'updated_at'])

        return dispatch

    @staticmethod
    @transaction.atomic
    def start_delivery(*, dispatch_id: int, started_by=None):
        """شروع تحویل — وضعیت به in_delivery تغییر می‌کند"""
        dispatch = DispatchHeader.objects.get(id=dispatch_id)
        if dispatch.status != DispatchHeader.DispatchStatus.PENDING:
            raise ValueError(
                f'سند پخش {dispatch.dispatch_no} در وضعیت {dispatch.status} است'
            )
        dispatch.status = DispatchHeader.DispatchStatus.IN_DELIVERY
        dispatch.save(update_fields=['status', 'updated_at'])
        return dispatch

    @staticmethod
    @transaction.atomic
    def mark_arrived(*, dispatch_id: int, arrived_by=None):
        """تحویل شد — وضعیت به arrived تغییر می‌کند"""
        dispatch = DispatchHeader.objects.get(id=dispatch_id)
        if dispatch.status != DispatchHeader.DispatchStatus.IN_DELIVERY:
            raise ValueError(
                f'سند پخش {dispatch.dispatch_no} در وضعیت {dispatch.status} است'
            )
        dispatch.status = DispatchHeader.DispatchStatus.ARRIVED
        dispatch.save(update_fields=['status', 'updated_at'])

        # ثبت سرکشی (visit) برای گزارش‌گیری
        SalespersonVisit.objects.get_or_create(
            distributor=dispatch.distributor,
            store_id=dispatch.lines.first().dest_store_id if dispatch.lines.first() else None,
            visit_date=dispatch.dispatch_date,
            defaults={
                'check_in_time': timezone.now(),
                'sales_count': dispatch.lines.count(),
                'sales_amount': dispatch.total_amount,
                'created_by': arrived_by,
            },
        )
        return dispatch

    @staticmethod
    @transaction.atomic
    def cancel_dispatch(*, dispatch_id: int, reason: str = '', canceled_by=None):
        """لغو پخش — برگشت موجودی به انبار اصلی"""
        dispatch = DispatchHeader.objects.select_for_update().get(id=dispatch_id)
        if dispatch.status == DispatchHeader.DispatchStatus.ARRIVED:
            raise ValueError('سند تحویل‌شده قابل لغو نیست')

        # برگرداندن موجودی به انبار اصلی
        for line in dispatch.lines.all():
            DispatchService._return_lot_to_main(
                lot_id=line.lot_id,
                qty=line.qty,
                dispatch_id=dispatch.id,
                created_by=canceled_by,
            )

        dispatch.status = DispatchHeader.DispatchStatus.CANCELED
        if reason:
            dispatch.notes = f'{dispatch.notes}\n\nلغو: {reason}'.strip()
        dispatch.save(update_fields=['status', 'notes', 'updated_at'])
        return dispatch

    @staticmethod
    @transaction.atomic
    def _transfer_lot_to_store(*, lot_id, qty, store_id, dispatch_id, created_by):
        """انتقال موجودی لات از انبار اصلی به انبار مجازی فروشگاه"""
        from apps.inventory.models import Warehouse

        lot = InventoryLot.objects.select_for_update().get(id=lot_id)
        main_warehouse_id = DispatchService._get_main_warehouse_id()

        # کاهش موجودی در انبار اصلی
        lot.current_qty -= Decimal(qty)
        lot.save(update_fields=['current_qty', 'updated_at'])

        # ثبت حرکت در انبار اصلی (خروج)
        InventoryMovement.objects.create(
            lot=lot,
            product_id=lot.product_id,
            warehouse_id=main_warehouse_id,
            movement_type=InventoryMovement.MovementType.TRANSFER,
            qty=-Decimal(qty),
            unit_cost=lot.weighted_avg_cost,
            ref_doc_type='dispatch',
            ref_doc_id=dispatch_id,
            created_by=created_by,
        )

        # به‌روزرسانی موجودی تجمیعی انبار اصلی
        DispatchService._update_stock_balance(
            product_id=lot.product_id,
            warehouse_id=main_warehouse_id,
            qty_change=-Decimal(qty),
            value_change=-Decimal(qty) * lot.weighted_avg_cost,
            last_lot_id=lot.id,
        )

        # دریافت یا ساخت انبار مجازی فروشگاه
        store_wh, created = Warehouse.objects.get_or_create(
            store_id=store_id,
            type=Warehouse.WarehouseType.STORE,
            defaults={
                'code': f'WH-STORE-{store_id}',
                'name': f'انبار فروشگاه {store_id}',
            },
        )

        # ساخت لات در انبار فروشگاه (یا افزایش موجودی لات موجود)
        store_lot, _ = InventoryLot.objects.get_or_create(
            product_id=lot.product_id,
            warehouse=store_wh,
            batch_no=lot.batch_no,
            defaults={
                'production_date': lot.production_date,
                'expiry_date': lot.expiry_date,
                'initial_qty': Decimal('0'),
                'current_qty': Decimal('0'),
                'weighted_avg_cost': lot.weighted_avg_cost,
            },
        )
        store_lot.current_qty += Decimal(qty)
        store_lot.save(update_fields=['current_qty', 'updated_at'])

        # ثبت حرکت در انبار فروشگاه (ورود)
        InventoryMovement.objects.create(
            lot=store_lot,
            product_id=store_lot.product_id,
            warehouse_id=store_wh.id,
            movement_type=InventoryMovement.MovementType.TRANSFER,
            qty=Decimal(qty),
            unit_cost=lot.weighted_avg_cost,
            ref_doc_type='dispatch',
            ref_doc_id=dispatch_id,
            created_by=created_by,
        )

        # به‌روزرسانی موجودی تجمیعی انبار فروشگاه
        DispatchService._update_stock_balance(
            product_id=store_lot.product_id,
            warehouse_id=store_wh.id,
            qty_change=Decimal(qty),
            value_change=Decimal(qty) * lot.weighted_avg_cost,
            last_lot_id=store_lot.id,
        )

    @staticmethod
    def _return_lot_to_main(*, lot_id, qty, dispatch_id, created_by):
        """بازگرداندن موجودی به انبار اصلی (در لغو پخش)"""
        lot = InventoryLot.objects.select_for_update().get(id=lot_id)
        lot.current_qty += Decimal(qty)
        lot.save(update_fields=['current_qty', 'updated_at'])

        InventoryMovement.objects.create(
            lot=lot,
            product_id=lot.product_id,
            warehouse_id=lot.warehouse_id,
            movement_type=InventoryMovement.MovementType.ADJUSTMENT,
            qty=Decimal(qty),
            unit_cost=lot.weighted_avg_cost,
            ref_doc_type='dispatch_cancel',
            ref_doc_id=dispatch_id,
            created_by=created_by,
        )

    @staticmethod
    def _get_main_warehouse_id() -> int:
        from apps.inventory.models import Warehouse
        return Warehouse.objects.get(type=Warehouse.WarehouseType.MAIN).id

    @staticmethod
    def _update_stock_balance(*, product_id, warehouse_id, qty_change, value_change, last_lot_id=None):
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

    @staticmethod
    def _generate_dispatch_number() -> str:
        year = timezone.now().year
        count = DispatchHeader.objects.count() + 1
        return f'DISP-{year}-{count:06d}'
