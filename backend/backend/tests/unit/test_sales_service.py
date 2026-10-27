"""
Unit Tests for Sales Service — امانی/قطعی
"""
import pytest
from decimal import Decimal
from django.utils import timezone

from apps.sales.models import SalesHeader, SalesLine
from apps.sales.services import SalesService
from apps.inventory.models import InventoryLot, StockBalance
from core.exceptions import InsufficientStockError


@pytest.mark.django_db
@pytest.mark.unit
class TestSalesService:

    def test_create_sale_basic(self, store, product, main_warehouse, db, seed_accounts):
        """تست پایه: ساخت فروش امانی"""
        # ابتدا موجودی بساز
        from datetime import timedelta
        today = timezone.now().date()
        InventoryLot.objects.create(
            product=product, warehouse=main_warehouse,
            batch_no='B1', production_date=today,
            expiry_date=today + timedelta(days=15),
            initial_qty=100, current_qty=100, weighted_avg_cost=25000,
        )

        # ساخت فروش
        sale = SalesService.create_sale(
            store_id=store.id,
            sales_type='consignment',
            lines=[
                {'product_id': product.id, 'qty': 30, 'unit_price': 50000},
            ],
        )

        assert sale.id is not None
        assert sale.status == 'posted'
        assert sale.total_amount == Decimal('1500000')  # 30 × 50000
        assert sale.total_cost == Decimal('750000')    # 30 × 25000
        assert sale.total_profit == Decimal('750000')

        # بررسی کاهش موجودی
        lot = InventoryLot.objects.first()
        assert lot.current_qty == Decimal('70')

    def test_create_sale_firm_type(self, store, product, main_warehouse, db, seed_accounts):
        """فروش قطعی"""
        from datetime import timedelta
        today = timezone.now().date()
        InventoryLot.objects.create(
            product=product, warehouse=main_warehouse,
            batch_no='B1', production_date=today,
            expiry_date=today + timedelta(days=15),
            initial_qty=100, current_qty=100, weighted_avg_cost=25000,
        )

        sale = SalesService.create_sale(
            store_id=store.id,
            sales_type='firm',
            lines=[
                {'product_id': product.id, 'qty': 20, 'unit_price': 60000},
            ],
        )

        assert sale.sales_type == 'firm'
        assert sale.total_amount == Decimal('1200000')

    def test_create_sale_insufficient_stock(self, store, product, main_warehouse, db):
        """فروش بیشتر از موجودی"""
        from datetime import timedelta
        today = timezone.now().date()
        InventoryLot.objects.create(
            product=product, warehouse=main_warehouse,
            batch_no='B1', production_date=today,
            expiry_date=today + timedelta(days=15),
            initial_qty=10, current_qty=10, weighted_avg_cost=25000,
        )

        with pytest.raises(InsufficientStockError):
            SalesService.create_sale(
                store_id=store.id,
                sales_type='consignment',
                lines=[
                    {'product_id': product.id, 'qty': 50, 'unit_price': 50000},  # موجودی فقط ۱۰
                ],
            )

    def test_create_sale_multiple_lines(self, store, product, main_warehouse, db, seed_accounts):
        """فروش با چند خط و چند محصول"""
        from apps.products.models import Product, ProductCategory
        from datetime import timedelta
        today = timezone.now().date()

        cat = ProductCategory.objects.first() or ProductCategory.objects.create(
            code='CAT2', name='دسته ۲'
        )
        p1 = product
        p2 = Product.objects.create(
            code='P-TEST-002', name='محصول ۲',
            category=cat, unit='عدد', shelf_life_days=15,
            default_price=60000,
        )

        # موجودی برای هر دو
        InventoryLot.objects.create(
            product=p1, warehouse=main_warehouse,
            batch_no='B1', production_date=today,
            expiry_date=today + timedelta(days=15),
            initial_qty=100, current_qty=100, weighted_avg_cost=25000,
        )
        InventoryLot.objects.create(
            product=p2, warehouse=main_warehouse,
            batch_no='B2', production_date=today,
            expiry_date=today + timedelta(days=15),
            initial_qty=100, current_qty=100, weighted_avg_cost=30000,
        )

        sale = SalesService.create_sale(
            store_id=store.id,
            sales_type='consignment',
            lines=[
                {'product_id': p1.id, 'qty': 20, 'unit_price': 50000},
                {'product_id': p2.id, 'qty': 10, 'unit_price': 60000},
            ],
        )

        assert sale.lines.count() == 2
        assert sale.total_amount == Decimal('1600000')  # 20×50000 + 10×60000


@pytest.mark.django_db
@pytest.mark.unit
class TestStore:
    """تست‌های مدل Store"""

    def test_store_available_credit(self, store):
        """موجودی اعتبار"""
        store.credit_limit = Decimal('100000000')
        store.current_credit = Decimal('30000000')
        store.save()

        assert store.available_credit == Decimal('70000000')

    def test_store_discount_percentage(self, store):
        """درصد تخفیف بر اساس لایه"""
        store.tier = 'regular'
        assert store.discount_percentage == 0

        store.tier = 'silver'
        assert store.discount_percentage == 2

        store.tier = 'gold'
        assert store.discount_percentage == 5

        store.tier = 'platinum'
        assert store.discount_percentage == 8
