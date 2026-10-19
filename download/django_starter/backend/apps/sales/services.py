"""
Sales Service — منطق کسب‌وکار فروش (امانی/قطعی)
"""
from decimal import Decimal
from typing import List, Optional
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify
from core.exceptions import InsufficientStockError
from .models import SalesHeader, SalesLine, ReturnHeader, ReturnLine
from apps.inventory.models import InventoryLot
from apps.inventory.services.fefo_service import (
    FEFOService, AllocationItem, WeightedAverageService
)


class SalesService:
    """سرویس فروش با پشتیبانی امانی/قطعی"""

    @staticmethod
    @transaction.atomic
    def create_sale(
        *,
        store_id: int,
        sales_type: str,
        sale_date=None,
        lines: List[dict],
        distributor_id: Optional[int] = None,
        dispatch_id: Optional[int] = None,
        created_by=None,
        notes: str = '',
    ) -> SalesHeader:
        """
        ساخت سند فروش با تخصیص FEFO خودکار.

        خطوط ورودی:
            [{'product_id': 1, 'qty': 30, 'unit_price': 50000, 'warehouse_id': 1}, ...]
        """
        if sale_date is None:
            sale_date = timezone.now().date()

        # ۱. ساخت سند فروش
        sale = SalesHeader.objects.create(
            sale_no=SalesService._generate_sale_number(),
            store_id=store_id,
            sale_date=sale_date,
            sales_type=sales_type,
            status=SalesHeader.SalesStatus.POSTED,
            distributor_id=distributor_id,
            dispatch_id=dispatch_id,
            created_by=created_by,
            notes=notes,
        )

        total_amount = Decimal('0')
        total_cost = Decimal('0')

        # ۲. برای هر خط، تخصیص FEFO و ساخت SalesLine
        for line_data in lines:
            product_id = line_data['product_id']
            warehouse_id = line_data.get('warehouse_id') or SalesService._get_main_warehouse_id()
            qty = Decimal(line_data['qty'])
            unit_price = Decimal(line_data['unit_price'])

            # تخصیص FEFO
            alloc_result = FEFOService.allocate_lots(
                product_id=product_id,
                warehouse_id=warehouse_id,
                qty_needed=qty,
                sale_date=sale_date,
                reserve=True,
            )

            # برای هر لات تخصیص‌داده‌شده، یک SalesLine بساز
            for alloc in alloc_result.allocations:
                line = SalesLine.objects.create(
                    sale=sale,
                    product_id=product_id,
                    lot_id=alloc.lot_id,
                    qty=alloc.qty,
                    unit_price=unit_price,
                    unit_cost=alloc.unit_cost,
                    created_by=created_by,
                )
                total_amount += line.line_total
                total_cost += line.line_cost

            # مصرف لات‌ها (کاهش موجودی)
            FEFOService.consume_lots(
                allocations=alloc_result.allocations,
                warehouse_id=warehouse_id,
                movement_type='out',
                ref_doc_type='sale',
                ref_doc_id=sale.id,
                created_by=created_by,
            )

        # ۳. به‌روزرسانی مجموع‌های سند
        sale.total_amount = total_amount
        sale.total_cost = total_cost
        sale.save(update_fields=['total_amount', 'total_cost', 'updated_at'])

        # ۴. ارسال سیگنال برای تولید سند حسابداری خودکار
        from django.db.models.signals import post_save
        from .signals import sale_posted
        sale_posted.send(sender=SalesHeader, instance=sale, created=True)

        # ۵. ارسال صورتحساب سامان (فقط برای فروش قطعی)
        if sales_type == SalesHeader.SalesType.FIRM:
            SalesService._create_tax_invoice(sale)

        return sale

    @staticmethod
    @transaction.atomic
    def create_return(
        *,
        store_id: int,
        original_sale_id: Optional[int],
        lines: List[dict],
        reason: str = '',
        return_date=None,
        created_by=None,
    ) -> ReturnHeader:
        """ساخت سند برگشت"""
        if return_date is None:
            return_date = timezone.now().date()

        return_header = ReturnHeader.objects.create(
            return_no=SalesService._generate_return_number(),
            store_id=store_id,
            return_date=return_date,
            original_sale_id=original_sale_id,
            reason=reason,
            status='posted',
            created_by=created_by,
        )

        total_qty = Decimal('0')
        for line_data in lines:
            condition = line_data.get('condition', 'sellable')
            qty = Decimal(line_data['qty'])

            ReturnLine.objects.create(
                return_header=return_header,
                product_id=line_data['product_id'],
                lot_id=line_data.get('lot_id'),
                qty=qty,
                condition=condition,
                notes=line_data.get('notes', ''),
                created_by=created_by,
            )
            total_qty += qty

            # اگر قابل فروش مجدد باشد، به انبار برگردانده شود
            if condition == 'sellable' and line_data.get('lot_id'):
                SalesService._return_to_inventory(
                    lot_id=line_data['lot_id'],
                    qty=qty,
                    warehouse_id=line_data.get('warehouse_id'),
                    return_id=return_header.id,
                    created_by=created_by,
                )

        return_header.total_qty = total_qty
        return_header.save(update_fields=['total_qty', 'updated_at'])

        # ارسال سیگنال برای سند معکوس حسابداری
        from .signals import return_posted
        return_posted.send(sender=ReturnHeader, instance=return_header, created=True)

        return return_header

    @staticmethod
    def _return_to_inventory(*, lot_id, qty, warehouse_id, return_id, created_by):
        """بازگرداندن کالای برگشتی به انبار"""
        from apps.inventory.models import InventoryMovement

        lot = InventoryLot.objects.select_for_update().get(id=lot_id)
        lot.current_qty += qty
        lot.save(update_fields=['current_qty', 'updated_at'])

        InventoryMovement.objects.create(
            lot=lot,
            product_id=lot.product_id,
            warehouse_id=warehouse_id or lot.warehouse_id,
            movement_type='return',
            qty=qty,
            unit_cost=lot.weighted_avg_cost,
            ref_doc_type='return',
            ref_doc_id=return_id,
            created_by=created_by,
        )

    @staticmethod
    def _get_main_warehouse_id() -> int:
        """دریافت شناسه انبار اصلی"""
        from apps.inventory.models import Warehouse
        return Warehouse.objects.get(type=Warehouse.WarehouseType.MAIN).id

    @staticmethod
    def _generate_sale_number() -> str:
        """تولید شماره فروش یکتا"""
        year = timezone.now().year
        count = SalesHeader.objects.count() + 1
        return f'SALE-{year}-{count:06d}'

    @staticmethod
    def _generate_return_number() -> str:
        """تولید شماره برگشت یکتا"""
        year = timezone.now().year
        count = ReturnHeader.objects.count() + 1
        return f'RET-{year}-{count:06d}'

    @staticmethod
    def _create_tax_invoice(sale: SalesHeader):
        """ارسال صورتحساب به سامان (در پس‌زمینه)"""
        # این در فاز ۷ پیاده‌سازی می‌شود
        # from apps.saman_tax.services import SamanService
        # SamanService.send_invoice_for_sale(sale.id)
        pass

    @staticmethod
    def get_store_balance(store_id: int) -> dict:
        """محاسبه مانده حساب یک فروشگاه"""
        from django.db.models import Sum

        total_sales = SalesHeader.objects.filter(
            store_id=store_id,
            sales_type=SalesHeader.SalesType.FIRM,
            status=SalesHeader.SalesStatus.POSTED,
        ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0')

        total_paid = Decimal('0')
        # TODO: اضافه کردن محاسبه پرداخت‌ها از apps.payments

        return {
            'store_id': store_id,
            'total_sales': total_sales,
            'total_paid': total_paid,
            'balance': total_sales - total_paid,
        }
