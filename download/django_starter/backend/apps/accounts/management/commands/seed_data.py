"""
Management command to seed initial data
Usage: docker compose exec backend python manage.py seed_data
"""
from django.core.management.base import BaseCommand
from decimal import Decimal
from datetime import date, timedelta


class Command(BaseCommand):
    help = 'Seed initial data: products, stores, distributors, lots, accounts'

    def handle(self, *args, **options):
        # Category
        from apps.products.models import Product, ProductCategory
        cat, created = ProductCategory.objects.get_or_create(
            code='CAT-01', defaults={'name': 'گروه A'}
        )
        if created:
            self.stdout.write('  ✓ Category: CAT-01')

        # Products
        products_data = [
            ('P001', 'محصول نمونه A1', 50000),
            ('P002', 'محصول نمونه A2', 55000),
            ('P003', 'محصول نمونه A3', 60000),
            ('P004', 'محصول نمونه A4', 65000),
            ('P005', 'محصول نمونه A5', 70000),
            ('P011', 'محصول نمونه B1', 100000),
            ('P012', 'محصول نمونه B2', 105000),
            ('P013', 'محصول نمونه B3', 110000),
            ('P021', 'محصول نمونه C1', 150000),
            ('P022', 'محصول نمونه C2', 155000),
        ]
        for code, name, price in products_data:
            p, c = Product.objects.get_or_create(
                code=code,
                defaults={
                    'name': name, 'category': cat,
                    'unit': 'عدد', 'shelf_life_days': 15,
                    'default_price': Decimal(str(price)),
                }
            )
            if c:
                self.stdout.write(f'  ✓ Product: {code}')

        # Distributors
        from apps.partners.models import Distributor
        for code, name, mobile in [
            ('D001', 'عامل پخش مرکز', '09121110001'),
            ('D002', 'عامل پخش شمال', '09121110002'),
            ('D003', 'عامل پخش جنوب', '09121110003'),
        ]:
            d, c = Distributor.objects.get_or_create(
                code=code, defaults={'name': name, 'mobile': mobile}
            )
            if c:
                self.stdout.write(f'  ✓ Distributor: {code}')

        # Stores
        from apps.partners.models import Store
        stores_data = [
            ('S001', 'فروشگاه ۱', 'تهران', 35.7219, 51.3347, 'gold'),
            ('S002', 'فروشگاه ۲', 'کرج', 35.8401, 50.9391, 'silver'),
            ('S003', 'فروشگاه ۳', 'اصفهان', 32.6546, 51.6680, 'platinum'),
            ('S004', 'فروشگاه ۴', 'شیراز', 29.5916, 52.5837, 'gold'),
            ('S005', 'فروشگاه ۵', 'مشهد', 36.2972, 59.6062, 'regular'),
            ('S006', 'فروشگاه ۶', 'تبریز', 38.0800, 46.2919, 'silver'),
            ('S007', 'فروشگاه ۷', 'اهواز', 31.3181, 48.6705, 'regular'),
            ('S008', 'فروشگاه ۸', 'رشت', 37.2709, 49.5890, 'gold'),
            ('S009', 'فروشگاه ۹', 'قم', 34.6398, 50.8807, 'silver'),
            ('S010', 'فروشگاه ۱۰', 'یزد', 31.8974, 54.3569, 'platinum'),
        ]
        for code, name, address, lat, lng, tier in stores_data:
            s, c = Store.objects.get_or_create(
                code=code,
                defaults={
                    'name': name, 'address': address,
                    'distributor_id': 1, 'sales_model': 'consignment',
                    'tier': tier, 'credit_limit': Decimal('500000000'),
                    'geo_lat': Decimal(str(lat)), 'geo_lng': Decimal(str(lng)),
                }
            )
            if c:
                self.stdout.write(f'  ✓ Store: {code}')

        # Warehouse
        from apps.inventory.models import Warehouse
        wh, c = Warehouse.objects.get_or_create(
            code='WH-MAIN', defaults={'name': 'انبار اصلی', 'type': 'main'}
        )
        if c:
            self.stdout.write('  ✓ Warehouse: WH-MAIN')

        # Inventory Lots
        from apps.inventory.models import InventoryLot
        today = date.today()
        for i, code in enumerate(['P001', 'P002', 'P003', 'P004', 'P005']):
            lot, c = InventoryLot.objects.get_or_create(
                product=Product.objects.get(code=code),
                warehouse=wh,
                batch_no=f'BATCH-2025-{i+1:03d}',
                defaults={
                    'production_date': today,
                    'expiry_date': today + timedelta(days=15),
                    'initial_qty': Decimal('100'),
                    'current_qty': Decimal('100'),
                    'weighted_avg_cost': Decimal('25000'),
                }
            )
            if c:
                self.stdout.write(f'  ✓ Lot: {lot.batch_no}')

        # Accounting - seed accounts
        from apps.accounting.models import Account
        accounts_data = [
            ('1', 'دارایی‌ها', 'asset', None, False),
            ('10', 'دارایی‌های جاری', 'asset', '1', False),
            ('101', 'موجودی کالا', 'asset', '10', True),
            ('102', 'حساب‌های دریافتنی', 'asset', '10', True),
            ('103', 'نقد و بانک', 'asset', '10', True),
            ('2', 'بدهی‌ها', 'liability', None, False),
            ('201', 'حساب‌های پرداختنی', 'liability', '2', True),
            ('3', 'حقوق صاحبان سهام', 'equity', None, False),
            ('30', 'سرمایه', 'equity', '3', True),
            ('4', 'درآمدها', 'revenue', None, False),
            ('40', 'درآمد فروش', 'revenue', '4', True),
            ('5', 'هزینه‌ها', 'expense', None, False),
            ('50', 'بهای تمام‌شده فروش', 'expense', '5', True),
        ]
        for code, name, acc_type, parent_code, postable in accounts_data:
            parent = Account.objects.filter(code=parent_code).first() if parent_code else None
            obj, c = Account.objects.get_or_create(
                code=code,
                defaults={'name': name, 'type': acc_type, 'parent': parent, 'is_postable': postable}
            )
            if c:
                self.stdout.write(f'  ✓ Account: {code}')

        # Cost Center
        from apps.accounting.models import CostCenter
        cc, c = CostCenter.objects.get_or_create(
            code='CC01', defaults={'name': 'خط تولید', 'type': 'production'}
        )
        if c:
            self.stdout.write('  ✓ CostCenter: CC01')

        # Loyalty Tiers
        from apps.loyalty.models import LoyaltyTier
        for name, min_pts, disc, inc in [
            ('regular', 0, 0, 0), ('silver', 100, 2, 50),
            ('gold', 500, 5, 100), ('platinum', 1000, 8, 200),
        ]:
            obj, c = LoyaltyTier.objects.get_or_create(
                name=name, defaults={
                    'min_points': min_pts,
                    'discount_percentage': Decimal(str(disc)),
                    'credit_increase_percentage': Decimal(str(inc)),
                }
            )
            if c:
                self.stdout.write(f'  ✓ LoyaltyTier: {name}')

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'✅ Data seeded!'))
        self.stdout.write(f'   Products: {Product.objects.count()}')
        self.stdout.write(f'   Stores: {Store.objects.count()}')
        self.stdout.write(f'   Lots: {InventoryLot.objects.count()}')
        self.stdout.write(f'   Accounts: {Account.objects.count()}')
