"""
Waste Service — مدیریت ضایعات فروشگاه/انبار/عامل پخش
"""
from decimal import Decimal
from typing import List, Optional
from django.db import transaction
from django.utils import timezone
from ..models import WasteDocument, WasteLine, InventoryLot, StockBalance


class WasteService:
    """سرویس مدیریت ضایعات"""

    @staticmethod
    @transaction.atomic
    def create_waste(
        *,
        waste_type: str,
        lines: List[dict],
        store_id: Optional[int] = None,
        warehouse_id: Optional[int] = None,
        distributor_id: Optional[int] = None,
        reason: str = '',
        waste_date=None,
        created_by=None,
    ) -> WasteDocument:
        """
        ساخت سند ضایعات.

        پارامترها:
            waste_type: 'store' | 'warehouse' | 'distributor'
            lines: [{'product_id': 1, 'qty': 5, 'unit_cost': 25000, 'condition': 'damaged', 'description': '...'}]
            store_id/warehouse_id/distributor_id: بر اساس waste_type، یکی الزامی است
        """

        # اعتبارسنجی
        if waste_type == 'store' and not store_id:
            raise ValueError('برای ضایعات فروشگاه، store_id الزامی است')
        if waste_type == 'warehouse' and not warehouse_id:
            raise ValueError('برای ضایعات انبار، warehouse_id الزامی است')
        if waste_type == 'distributor' and not distributor_id:
            raise ValueError('برای ضایعات عامل پخش، distributor_id الزامی است')

        if waste_date is None:
            waste_date = timezone.now().date()

        # ساخت سند
        waste_doc = WasteDocument.objects.create(
            waste_no=WasteService._generate_waste_number(),
            waste_type=waste_type,
            store_id=store_id,
            warehouse_id=warehouse_id,
            distributor_id=distributor_id,
            waste_date=waste_date,
            reason=reason,
            status='posted',
            created_by=created_by,
        )

        total_value = Decimal('0')

        # ساخت خطوط
        for line_data in lines:
            product_id = line_data['product_id']
            qty = Decimal(line_data['qty'])
            unit_cost = Decimal(str(line_data.get('unit_cost', 0) or 0))
            line_total = qty * unit_cost
            total_value += line_total

            # پیدا کردن lot با موجودی کافی برای محصول (اختیاری)
            lot = None
            if warehouse_id:
                lot = (
                    InventoryLot.objects.select_for_update()
                    .filter(
                        product_id=product_id,
                        warehouse_id=warehouse_id,
                        current_qty__gte=qty,
                    )
                    .order_by('expiry_date')
                    .first()
                )

                # کم کردن موجودی lot
                if lot:
                    lot.current_qty -= qty
                    lot.save(update_fields=['current_qty', 'updated_at'])

                    # به‌روزرسانی StockBalance
                    sb, _ = StockBalance.objects.get_or_create(
                        product_id=product_id,
                        warehouse_id=warehouse_id,
                    )
                    sb.total_qty -= qty
                    sb.total_value -= (qty * (lot.weighted_avg_cost or 0))
                    sb.save(update_fields=['total_qty', 'total_value', 'updated_at'])

            WasteLine.objects.create(
                waste_document=waste_doc,
                product_id=product_id,
                lot=lot,
                qty=qty,
                unit_cost=unit_cost,
                line_total=line_total,
                condition=line_data.get('condition', 'damaged'),
                description=line_data.get('description', ''),
                created_by=created_by,
            )

        # به‌روزرسانی total_value سند
        waste_doc.total_value = total_value
        waste_doc.save(update_fields=['total_value', 'updated_at'])

        return waste_doc

    @staticmethod
    def _generate_waste_number() -> str:
        """تولید شماره ضایعات به‌صورت WST-YYYY-NNNNNN"""
        today = timezone.now()
        year = today.year
        last = WasteDocument.objects.filter(
            waste_no__startswith=f'WST-{year}-',
        ).order_by('-waste_no').first()
        if last:
            try:
                seq = int(last.waste_no.split('-')[-1]) + 1
            except (ValueError, IndexError):
                seq = 1
        else:
            seq = 1
        return f'WST-{year}-{seq:06d}'
