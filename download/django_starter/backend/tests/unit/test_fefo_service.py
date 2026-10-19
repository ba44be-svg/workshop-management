"""
Unit Tests for FEFO Service — قلب منطق کسب‌وکار
این مهم‌ترین فایل تست پروژه است!
"""
import pytest
from decimal import Decimal
from datetime import date, timedelta
from django.utils import timezone
from django.db import transaction

from apps.inventory.models import InventoryLot, InventoryMovement, StockBalance
from apps.inventory.services.fefo_service import (
    FEFOService, WeightedAverageService, AllocationItem, FEFOAllocationResult,
)
from core.exceptions import InsufficientStockError


@pytest.mark.django_db
@pytest.mark.unit
class TestFEFOService:
    """تست‌های FEFO Service"""

    def test_allocate_lots_basic(self, lot_with_stock, product, main_warehouse):
        """تست پایه: تخصیص لات برای فروش"""
        result = FEFOService.allocate_lots(
            product_id=product.id,
            warehouse_id=main_warehouse.id,
            qty_needed=Decimal('30'),
            sale_date=timezone.now().date(),
        )
        assert result.allocated is True
        assert result.total_allocated_qty == Decimal('30')
        assert len(result.allocations) == 1
        assert result.allocations[0].lot_id == lot_with_stock.id

    def test_allocate_lots_multiple_lots(self, product, main_warehouse, db):
        """تست با چند لات — باید از نزدیک‌ترین به انقضا استفاده کنه"""
        today = timezone.now().date()

        # لات ۱: انقضا ۳ روز بعد (اول در FEFO)
        lot1 = InventoryLot.objects.create(
            product=product, warehouse=main_warehouse,
            batch_no='B1', production_date=today,
            expiry_date=today + timedelta(days=3),
            initial_qty=20, current_qty=20, weighted_avg_cost=25000,
        )

        # لات ۲: انقضا ۱۵ روز بعد
        lot2 = InventoryLot.objects.create(
            product=product, warehouse=main_warehouse,
            batch_no='B2', production_date=today,
            expiry_date=today + timedelta(days=15),
            initial_qty=50, current_qty=50, weighted_avg_cost=26000,
        )

        # درخواست ۳۰ عدد — باید اول ۲۰ از lot1، بعد ۱۰ از lot2
        result = FEFOService.allocate_lots(
            product_id=product.id,
            warehouse_id=main_warehouse.id,
            qty_needed=Decimal('30'),
        )

        assert len(result.allocations) == 2
        assert result.allocations[0].lot_id == lot1.id
        assert result.allocations[0].qty == Decimal('20')
        assert result.allocations[1].lot_id == lot2.id
        assert result.allocations[1].qty == Decimal('10')

    def test_allocate_lots_insufficient_stock(self, lot_with_stock, product, main_warehouse):
        """تست کمبود موجودی — باید InsufficientStockError بدهد"""
        with pytest.raises(InsufficientStockError) as exc:
            FEFOService.allocate_lots(
                product_id=product.id,
                warehouse_id=main_warehouse.id,
                qty_needed=Decimal('200'),  # موجودی ۱۰۰ است
            )
        assert 'موجودی ناکافی' in str(exc.value.detail) or 'ناکافی' in str(exc.value.detail)

    def test_allocate_lots_no_stock(self, product, main_warehouse):
        """تست نبود هیچ موجودی"""
        with pytest.raises(InsufficientStockError):
            FEFOService.allocate_lots(
                product_id=product.id,
                warehouse_id=main_warehouse.id,
                qty_needed=Decimal('1'),
            )

    def test_allocate_lots_expired_lot_skipped(self, product, main_warehouse, db):
        """لات منقضی شده نباید انتخاب شود"""
        today = timezone.now().date()

        # لات منقضی شده
        InventoryLot.objects.create(
            product=product, warehouse=main_warehouse,
            batch_no='EXPIRED', production_date=today - timedelta(days=20),
            expiry_date=today - timedelta(days=5),  # منقضی شده
            initial_qty=100, current_qty=100, weighted_avg_cost=25000,
            status=InventoryLot.LotStatus.ACTIVE,  # فعال ولی منقضی
        )

        # لات فعال
        active_lot = InventoryLot.objects.create(
            product=product, warehouse=main_warehouse,
            batch_no='ACTIVE', production_date=today,
            expiry_date=today + timedelta(days=15),
            initial_qty=50, current_qty=50, weighted_avg_cost=26000,
        )

        result = FEFOService.allocate_lots(
            product_id=product.id,
            warehouse_id=main_warehouse.id,
            qty_needed=Decimal('30'),
        )

        # باید از لات فعال استفاده کنه، نه لات منقضی
        assert len(result.allocations) == 1
        assert result.allocations[0].lot_id == active_lot.id

    def test_near_expiry_warning(self, product, main_warehouse, db):
        """هشدار لات نزدیک به انقضا"""
        today = timezone.now().date()
        InventoryLot.objects.create(
            product=product, warehouse=main_warehouse,
            batch_no='NEAR', production_date=today,
            expiry_date=today + timedelta(days=2),  # فقط ۲ روز
            initial_qty=50, current_qty=50, weighted_avg_cost=25000,
        )

        result = FEFOService.allocate_lots(
            product_id=product.id,
            warehouse_id=main_warehouse.id,
            qty_needed=Decimal('10'),
        )

        assert result.warning is not None
        assert 'انقضا' in result.warning or 'نزدیک' in result.warning


@pytest.mark.django_db
@pytest.mark.unit
class TestWeightedAverageService:
    """تست‌های میانگین موزون"""

    def test_update_weighted_average(self, lot_with_stock):
        """تست محاسبه میانگین موزون پس از ورود کالا"""
        # حالت اولیه: ۱۰۰ عدد با میانگین ۲۵٬۰۰۰
        assert lot_with_stock.current_qty == Decimal('100')
        assert lot_with_stock.weighted_avg_cost == Decimal('25000')

        # ورود ۵۰ عدد با قیمت ۲۸٬۰۰۰
        new_avg = WeightedAverageService.update_weighted_average(
            lot_id=lot_with_stock.id,
            in_qty=Decimal('50'),
            in_unit_cost=Decimal('28000'),
        )

        # میانگین جدید = (100×25000 + 50×28000) / 150 = 26000
        assert new_avg == Decimal('26000.0000')

        lot_with_stock.refresh_from_db()
        assert lot_with_stock.current_qty == Decimal('150')
        assert lot_with_stock.weighted_avg_cost == Decimal('26000.0000')

    def test_weighted_avg_formula(self, lot_with_stock):
        """بررسی دقیق فرمول"""
        # حالت اولیه: ۱۰۰ × ۲۵۰۰۰ = ۲٬۵۰۰٬۰۰۰
        # ورود: ۳۰ × ۳۰۰۰۰ = ۹۰۰٬۰۰۰
        # مجموع: ۳٬۴۰۰٬۰۰۰
        # میانگین: 3,400,000 / 130 = 26153.846
        new_avg = WeightedAverageService.update_weighted_average(
            lot_id=lot_with_stock.id,
            in_qty=Decimal('30'),
            in_unit_cost=Decimal('30000'),
        )

        expected = (Decimal('100') * Decimal('25000') +
                    Decimal('30') * Decimal('30000')) / Decimal('130')
        assert new_avg == expected

    def test_get_current_cost(self, lot_with_stock, product, main_warehouse):
        """دریافت بهای فعلی"""
        cost = WeightedAverageService.get_current_cost(
            product.id, main_warehouse.id,
        )
        assert cost == Decimal('25000')


@pytest.mark.django_db
@pytest.mark.unit
class TestEAN13Barcode:
    """تست‌های تولید بارکد EAN-13"""

    def test_generate_ean13_checksum(self, db):
        """تست صحت چک‌سام EAN-13"""
        from apps.products.services import ProductService

        # تولید بارکد برای محصول با شناسه ۱
        barcode = ProductService._generate_ean13(1)
        assert len(barcode) == 13
        assert barcode.startswith('642')  # پیشوند ایران

        # بررسی چک‌سام
        partial = barcode[:12]
        checksum = barcode[12]
        expected = str(ProductService._ean13_checksum(partial))
        assert checksum == expected

    def test_ean13_checksum_algorithm(self):
        """بررسی دقیق الگوریتم چک‌سام"""
        from apps.products.services import ProductService

        # مثال استاندارد EAN-13: 5901234123457
        # پیشوند: 590123412345
        # چک‌سام: 7
        assert ProductService._ean13_checksum('590123412345') == 7
