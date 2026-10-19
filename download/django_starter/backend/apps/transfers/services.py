"""
Transfers Service — منطق انتقال + Transfer Suggester هوشمند
"""
from decimal import Decimal
from typing import List, Optional
from datetime import timedelta
from django.db import transaction
from django.utils import timezone
from django.db.models import Sum, F
from .models import TransferHeader, TransferLine, TransferSuggestion
from apps.inventory.models import InventoryLot, InventoryMovement, Warehouse, StockBalance
from apps.sales.models import SalesHeader, SalesLine


class TransferService:
    """سرویس انتقال بین فروشگاه‌ها"""

    @staticmethod
    @transaction.atomic
    def create_transfer(
        *,
        from_store_id: int,
        to_store_id: int,
        lines: List[dict],
        reason: str = '',
        created_by=None,
        transfer_date=None,
    ) -> TransferHeader:
        """
        ساخت درخواست انتقال.

        خطوط ورودی:
            [{'product_id': 1, 'lot_id': 5, 'qty': 30}, ...]
        """

        if from_store_id == to_store_id:
            raise ValueError('فروشگاه مبدأ و مقصد نمی‌توانند یکی باشند')

        if transfer_date is None:
            transfer_date = timezone.now().date()

        transfer = TransferHeader.objects.create(
            transfer_no=TransferService._generate_transfer_number(),
            from_store_id=from_store_id,
            to_store_id=to_store_id,
            transfer_date=transfer_date,
            status=TransferHeader.TransferStatus.PENDING,
            initiator=created_by,
            reason=reason,
            created_by=created_by,
        )

        # ساخت خطوط انتقال
        for line_data in lines:
            lot_id = line_data['lot_id']
            qty = Decimal(line_data['qty'])

            # بررسی موجودی لات در انبار مبدأ
            lot = InventoryLot.objects.select_for_update().get(id=lot_id)
            if lot.warehouse.store_id != from_store_id:
                raise ValueError(
                    f'لات {lot.batch_no} در انبار فروشگاه {lot.warehouse.store_id} است، '
                    f'نه {from_store_id}'
                )
            if lot.current_qty < qty:
                raise ValueError(
                    f'موجودی لات {lot.batch_no} کافی نیست: {lot.current_qty} موجود، {qty} موردنیاز'
                )

            TransferLine.objects.create(
                transfer=transfer,
                product_id=lot.product_id,
                lot=lot,
                qty=qty,
                expiry_date=lot.expiry_date,
                created_by=created_by,
            )

        return transfer

    @staticmethod
    @transaction.atomic
    def approve_transfer(*, transfer_id: int, approved_by=None) -> TransferHeader:
        """تأیید انتقال توسط مدیر — اجرای واقعی انتقال موجودی"""

        transfer = TransferHeader.objects.select_for_update().get(id=transfer_id)

        if transfer.status != TransferHeader.TransferStatus.PENDING:
            raise ValueError(
                f'انتقال {transfer.transfer_no} در وضعیت {transfer.status} است'
            )

        transfer.status = TransferHeader.TransferStatus.IN_TRANSIT
        transfer.save(update_fields=['status', 'updated_at'])

        # برای هر خط، انتقال موجودی انجام بده
        for line in transfer.lines.all():
            TransferService._transfer_lot_between_stores(
                lot_id=line.lot_id,
                qty=line.qty,
                from_store_id=transfer.from_store_id,
                to_store_id=transfer.to_store_id,
                transfer_id=transfer.id,
                created_by=approved_by,
            )

        transfer.status = TransferHeader.TransferStatus.RECEIVED
        transfer.receiver = approved_by
        transfer.save(update_fields=['status', 'receiver', 'updated_at'])

        # ارسال سیگنال برای سند حسابداری
        from .signals import transfer_completed
        transfer_completed.send(sender=TransferHeader, instance=transfer)

        return transfer

    @staticmethod
    @transaction.atomic
    def reject_transfer(*, transfer_id: int, reason: str = '', rejected_by=None):
        """رد انتقال"""
        transfer = TransferHeader.objects.get(id=transfer_id)
        if transfer.status != TransferHeader.TransferStatus.PENDING:
            raise ValueError('فقط انتقال در حال انتظار قابل رد است')
        transfer.status = TransferHeader.TransferStatus.REJECTED
        if reason:
            transfer.notes = f'{transfer.notes}\n\nرد: {reason}'.strip()
        transfer.save(update_fields=['status', 'notes', 'updated_at'])
        return transfer

    @staticmethod
    @transaction.atomic
    def _transfer_lot_between_stores(*, lot_id, qty, from_store_id, to_store_id, transfer_id, created_by):
        """انتقال واقعی موجودی لات از انبار فروشگاه مبدأ به مقصد"""

        lot = InventoryLot.objects.select_for_update().get(id=lot_id)

        # دریافت انبار فروشگاه مبدأ
        from_warehouse = Warehouse.objects.get(
            store_id=from_store_id, type=Warehouse.WarehouseType.STORE,
        )

        # دریافت یا ساخت انبار فروشگاه مقصد
        to_warehouse, _ = Warehouse.objects.get_or_create(
            store_id=to_store_id,
            type=Warehouse.WarehouseType.STORE,
            defaults={
                'code': f'WH-STORE-{to_store_id}',
                'name': f'انبار فروشگاه {to_store_id}',
            },
        )

        # کاهش موجودی لات در انبار مبدأ
        lot.current_qty -= Decimal(qty)
        lot.save(update_fields=['current_qty', 'updated_at'])

        # ثبت حرکت خروج از انبار مبدأ
        InventoryMovement.objects.create(
            lot=lot,
            product_id=lot.product_id,
            warehouse_id=from_warehouse.id,
            movement_type=InventoryMovement.MovementType.TRANSFER,
            qty=-Decimal(qty),
            unit_cost=lot.weighted_avg_cost,
            ref_doc_type='transfer',
            ref_doc_id=transfer_id,
            created_by=created_by,
        )

        # ساخت لات در انبار مقصد
        to_lot, _ = InventoryLot.objects.get_or_create(
            product_id=lot.product_id,
            warehouse=to_warehouse,
            batch_no=lot.batch_no,
            defaults={
                'production_date': lot.production_date,
                'expiry_date': lot.expiry_date,
                'initial_qty': Decimal('0'),
                'current_qty': Decimal('0'),
                'weighted_avg_cost': lot.weighted_avg_cost,
            },
        )
        to_lot.current_qty += Decimal(qty)
        to_lot.save(update_fields=['current_qty', 'updated_at'])

        # ثبت حرکت ورود به انبار مقصد
        InventoryMovement.objects.create(
            lot=to_lot,
            product_id=to_lot.product_id,
            warehouse_id=to_warehouse.id,
            movement_type=InventoryMovement.MovementType.TRANSFER,
            qty=Decimal(qty),
            unit_cost=lot.weighted_avg_cost,
            ref_doc_type='transfer',
            ref_doc_id=transfer_id,
            created_by=created_by,
        )

        # به‌روزرسانی موجودی تجمیعی هر دو انبار
        TransferService._update_stock_balance(
            product_id=lot.product_id,
            warehouse_id=from_warehouse.id,
            qty_change=-Decimal(qty),
            value_change=-Decimal(qty) * lot.weighted_avg_cost,
            last_lot_id=lot.id,
        )
        TransferService._update_stock_balance(
            product_id=to_lot.product_id,
            warehouse_id=to_warehouse.id,
            qty_change=Decimal(qty),
            value_change=Decimal(qty) * lot.weighted_avg_cost,
            last_lot_id=to_lot.id,
        )

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
    def _generate_transfer_number() -> str:
        year = timezone.now().year
        count = TransferHeader.objects.count() + 1
        return f'TR-{year}-{count:06d}'


class TransferSuggesterService:
    """سرویس پیشنهاد انتقال FEFO — الگوریتم هوشمند"""

    NEAR_EXPIRY_DAYS = 5
    MIN_TRANSFER_QTY = 5
    MAX_DISTANCE_KM = 50  # حداکثر فاصله برای پیشنهاد انتقال

    @classmethod
    @transaction.atomic
    def generate_suggestions(cls) -> int:
        """
        تولید پیشنهاد انتقال — هر شب توسط Celery Beat اجرا می‌شود.

        الگوریتم:
        ۱. یافتن لات‌های نزدیک به انقضا در انبارهای فروشگاه‌ها
        ۲. محاسبه نرخ فروش روزانه در فروشگاه مبدأ
        ۳. اگر DOS > DTE (موجودی بیشتر از توان فروش) → نیاز به انتقال
        ۴. یافتن فروشگاه مقصد با تقاضای بالا و نزدیک
        ۵. محاسبه تعداد قابل انتقال
        ۶. ساخت TransferSuggestion
        """
        today = timezone.now().date()
        cutoff = today + timedelta(days=cls.NEAR_EXPIRY_DAYS)

        # ۱. تمام لات‌های نزدیک به انقضا در انبارهای فروشگاه‌ها
        near_expiry_lots = InventoryLot.objects.filter(
            warehouse__type=Warehouse.WarehouseType.STORE,
            warehouse__store__isnull=False,
            current_qty__gt=0,
            status=InventoryLot.LotStatus.ACTIVE,
            expiry_date__gte=today,
            expiry_date__lte=cutoff,
            deleted_at__isnull=True,
        ).select_related('product', 'warehouse', 'warehouse__store')

        # پاک کردن پیشنهادهای قدیمی پردازش‌نشده
        TransferSuggestion.objects.filter(
            is_processed=False, is_approved=False,
        ).delete()

        suggestions_created = 0

        for lot in near_expiry_lots:
            store = lot.warehouse.store

            # ۲. محاسبه نرخ فروش روزانه (۷ روز گذشته)
            dsr = TransferSuggesterService._calculate_dsr(
                product_id=lot.product_id, store_id=store.id,
            )

            if dsr <= 0:
                continue  # فروشی نیست، پیشنهاد نمی‌دهیم

            # ۳. محاسبه Days of Stock
            dos = lot.current_qty / Decimal(dsr) if dsr > 0 else Decimal('999')
            dte = (lot.expiry_date - today).days

            # اگر موجودی کمتر از ۳ روز فروش نباشد، انتقال نمی‌دهیم
            if dos < 3:
                continue

            # ۴. یافتن فروشگاه مقصد پرفروش و نزدیک
            dest_store = TransferSuggesterService._find_dest_store(
                product_id=lot.product_id,
                exclude_store_id=store.id,
                from_store=store,
            )

            if not dest_store:
                continue

            # ۵. محاسبه تعداد قابل انتقال
            qty_to_transfer = min(
                lot.current_qty - Decimal(dsr) * dte,  # مازاد بر نیاز فروشگاه فعلی
                TransferSuggesterService._dest_daily_demand(
                    product_id=lot.product_id, store_id=dest_store.id,
                ) * 3,  # حداکثر ۳ روز نیاز مقصد
            )

            if qty_to_transfer < cls.MIN_TRANSFER_QTY:
                continue

            # ۶. محاسبه امتیاز اولویت
            score = TransferSuggesterService._calculate_score(
                dte, dos, qty_to_transfer, dsr,
            )

            # تعیین اولویت
            if dte <= 1:
                urgency = TransferSuggestion.Urgency.URGENT
            elif dte <= 3:
                urgency = TransferSuggestion.Urgency.HIGH
            elif dte <= 5:
                urgency = TransferSuggestion.Urgency.MEDIUM
            else:
                urgency = TransferSuggestion.Urgency.LOW

            TransferSuggestion.objects.create(
                lot=lot,
                from_store=store,
                to_store=dest_store,
                qty=qty_to_transfer,
                urgency=urgency,
                score=score,
            )
            suggestions_created += 1

        return suggestions_created

    @staticmethod
    def _calculate_dsr(*, product_id, store_id, days=7):
        """محاسبه Daily Sales Rate (نرخ فروش روزانه)"""
        from datetime import timedelta
        cutoff_date = timezone.now().date() - timedelta(days=days)
        total_qty = SalesLine.objects.filter(
            sale__store_id=store_id,
            product_id=product_id,
            sale__sale_date__gte=cutoff_date,
            sale__status=SalesHeader.SalesStatus.POSTED,
        ).aggregate(total=Sum('qty'))['total'] or Decimal('0')
        return float(total_qty) / days if days > 0 else 0

    @staticmethod
    def _find_dest_store(*, product_id, exclude_store_id, from_store):
        """یافتن فروشگاه مقصد با تقاضای بالا و نزدیک"""
        from apps.partners.models import Store
        from django.db.models import Sum

        # یافتن فروشگاه‌های پرفروش این محصول در ۷ روز گذشته
        cutoff_date = timezone.now().date() - timedelta(days=7)
        candidates = SalesLine.objects.filter(
            product_id=product_id,
            sale__sale_date__gte=cutoff_date,
            sale__status=SalesHeader.SalesStatus.POSTED,
        ).exclude(
            sale__store_id=exclude_store_id,
        ).values('sale__store_id').annotate(
            total_qty=Sum('qty'),
        ).order_by('-total_qty')[:5]  # ۵ فروشگاه برتر

        for cand in candidates:
            store_id = cand['sale__store_id']
            try:
                store = Store.objects.get(id=store_id)
            except Store.DoesNotExist:
                continue

            # بررسی فاصله جغرافیایی
            if from_store.geo_lat and store.geo_lat:
                distance = TransferSuggesterService._haversine_distance(
                    float(from_store.geo_lat), float(from_store.geo_lng),
                    float(store.geo_lat), float(store.geo_lng),
                )
                if distance > TransferSuggesterService.MAX_DISTANCE_KM:
                    continue

            # بررسی موجودی پایین در مقصد (نیاز به موجودی)
            current_stock = TransferSuggesterService._get_store_stock(
                product_id=product_id, store_id=store_id,
            )
            if current_stock > 20:  # موجودی کافی در مقصد، نیاز نیست
                continue

            return store

        return None

    @staticmethod
    def _dest_daily_demand(*, product_id, store_id):
        """تقاضای روزانه مقصد"""
        return Decimal(TransferSuggesterService._calculate_dsr(
            product_id=product_id, store_id=store_id,
        ))

    @staticmethod
    def _get_store_stock(*, product_id, store_id):
        """موجودی فعلی محصول در فروشگاه"""
        from apps.inventory.services.fefo_service import FEFOService
        try:
            warehouse = Warehouse.objects.get(
                store_id=store_id, type=Warehouse.WarehouseType.STORE,
            )
            stock = StockBalance.objects.filter(
                product_id=product_id, warehouse=warehouse,
            ).first()
            return float(stock.total_qty) if stock else 0
        except Warehouse.DoesNotExist:
            return 0

    @staticmethod
    def _calculate_score(dte, dos, qty, dsr):
        """محاسبه امتیاز اولویت"""
        # امتیاز بالاتر = اولویت بیشتر
        # ۱۰۰ / DTE (انقضای نزدیک‌تر = امتیاز بالاتر)
        # + DOS * 10 (موجودی زیاد = امتیاز بالاتر)
        # + qty * 0.1 (تعداد قابل انتقال)
        try:
            return Decimal(100 / max(dte, 1)) + Decimal(dos * 10) + Decimal(qty * Decimal('0.1'))
        except Exception:
            return Decimal('0')

    @staticmethod
    def _haversine_distance(lat1, lng1, lat2, lng2):
        """محاسبه فاصله هافرسین بین دو نقطه جغرافیایی (کیلومتر)"""
        from math import radians, sin, cos, sqrt, atan2
        R = 6371  # شعاع زمین به کیلومتر
        dlat = radians(lat2 - lat1)
        dlng = radians(lng2 - lng1)
        a = (sin(dlat / 2) ** 2 +
             cos(radians(lat1)) * cos(radians(lat2)) * sin(dlng / 2) ** 2)
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        return R * c

    @staticmethod
    @transaction.atomic
    def approve_suggestion(*, suggestion_id: int, approved_by=None):
        """تأیید یک پیشنهاد و ساخت سند انتقال"""
        suggestion = TransferSuggestion.objects.get(id=suggestion_id)
        if suggestion.is_processed:
            raise ValueError('این پیشنهاد قبلاً پردازش شده')

        transfer = TransferService.create_transfer(
            from_store_id=suggestion.from_store_id,
            to_store_id=suggestion.to_store_id,
            lines=[{
                'product_id': suggestion.lot.product_id,
                'lot_id': suggestion.lot_id,
                'qty': suggestion.qty,
            }],
            reason=f'پیشنهاد خودکار FEFO (انقضا: {suggestion.lot.expiry_date})',
            created_by=approved_by,
        )

        # تأیید خودکار انتقال
        TransferService.approve_transfer(
            transfer_id=transfer.id, approved_by=approved_by,
        )

        suggestion.is_approved = True
        suggestion.is_processed = True
        suggestion.processed_at = timezone.now()
        suggestion.save()

        return transfer

    @staticmethod
    def approve_all_pending(approved_by=None):
        """تأیید همه پیشنهادهای پردازش‌نشده"""
        pending = TransferSuggestion.objects.filter(
            is_processed=False, is_approved=False,
        )
        approved_count = 0
        for suggestion in pending:
            try:
                TransferSuggesterService.approve_suggestion(
                    suggestion_id=suggestion.id, approved_by=approved_by,
                )
                approved_count += 1
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(
                    f'Failed to approve suggestion {suggestion.id}: {e}'
                )
        return approved_count
