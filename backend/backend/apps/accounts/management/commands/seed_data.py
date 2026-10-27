"""
Management command to seed initial data
Usage: python manage.py seed_data
"""
from django.core.management.base import BaseCommand
from decimal import Decimal
from datetime import date, timedelta


class Command(BaseCommand):
    help = 'Seed initial data: users, products, stores, distributors, lots, accounts,' \
           ' plus extra near-expiry lots, sales, dispatches, waste docs (idempotent).' \
           ' Also seeds workshop: contractors, raw/finished/workshop warehouses,' \
           ' purchases, workshop issues/returns, completed production batch.'

    # ----- idempotency markers -----
    SEED_MARKER_SALE = 'SEED-SALE-V1'
    SEED_MARKER_DISP = 'SEED-DISP-V1'
    SEED_MARKER_WASTE = 'SEED-WASTE-V1'
    SEED_MARKER_WORKSHOP = 'SEED-WORKSHOP-V1'
    SEED_MARKER_PROD = 'SEED-PROD-V1'

    def handle(self, *args, **options):
        # ۱) Admin user با نقش manager
        from apps.accounts.models import User
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@workshop.local',
                'first_name': 'مدیر',
                'last_name': 'کل',
                'is_active': True,
                'is_staff': True,
                'is_superuser': True,
            },
        )
        if created:
            admin_user.set_password('Admin@12345678')
            admin_user.role = 'manager'
            admin_user.save()
            self.stdout.write('  ✓ User: admin (password: Admin@12345678, role: manager)')
        else:
            # اگه کاربر وجود داشت، مطمئن شو نقش manager داره و پسورد درسته
            admin_user.role = 'manager'
            admin_user.is_superuser = True
            admin_user.is_staff = True
            admin_user.is_active = True
            admin_user.set_password('Admin@12345678')
            admin_user.save()
            self.stdout.write('  ~ User: admin (updated: role=manager, password reset)')

        # ۲) کاربرهای نمونه با نقش‌های مختلف (برای تست Settings > Users)
        sample_users = [
            ('accountant1', 'حسابدار', 'Sample', 'accountant'),
            ('storekeeper1', 'انباردار', 'Sample', 'storekeeper'),
            ('distributor1', 'عامل پخش', 'Sample', 'distributor'),
        ]
        for username, first, last, role in sample_users:
            u, c = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': f'{username}@workshop.local',
                    'first_name': first,
                    'last_name': last,
                    'is_active': True,
                    'is_staff': False,
                },
            )
            if c:
                u.set_password('Sample@12345678')
                u.role = role
                u.save()
                self.stdout.write(f'  ✓ User: {username} (role: {role})')

        # Category
        from apps.products.models import Product, ProductCategory, Unit
        cat, created = ProductCategory.objects.get_or_create(
            code='CAT-01', defaults={'name': 'گروه A'}
        )
        if created:
            self.stdout.write('  ✓ Category: CAT-01')

        # Units — ۸ واحد پایه: عدد، کیلوگرم، گرم، لیتر، بسته، جعبه، متر، متر مربع
        unit_specs = [
            ('NUM',  'عدد'),
            ('KG',   'کیلوگرم'),
            ('G',    'گرم'),
            ('L',    'لیتر'),
            ('PACK', 'بسته'),
            ('BOX',  'جعبه'),
            ('M',    'متر'),
            ('M2',   'متر مربع'),
        ]
        unit_map = {}
        for code, name in unit_specs:
            obj, c = Unit.objects.get_or_create(
                code=code, defaults={'name': name, 'is_active': True}
            )
            unit_map[code] = obj
            if c:
                self.stdout.write(f'  ✓ Unit: {code} ({name})')
        # Remove extra units pre-created by the products.0002 data migration
        # (CRTN, DZN) that are not in our 8-unit canonical list.
        extra_unit_codes = ['CRTN', 'DZN']
        for extra_code in extra_unit_codes:
            deleted, _ = Unit.objects.filter(code=extra_code).delete()
            if deleted:
                self.stdout.write(f'  - Removed extra Unit: {extra_code}')
        # default unit
        unit_default = unit_map.get('NUM')

        # Products — برخی به‌عنوان محصول تمام‌شده (is_finished_good=True)
        # (code, name, price, unit_code, is_finished_good)
        products_data = [
            ('P001', 'آرد سفید', 50000,  'NUM',  False),
            ('P002', 'آرد سبوس‌دار', 55000,  'NUM',  False),
            ('P003', 'شکر', 60000,  'KG',   False),
            ('P004', 'روغن مایع', 65000,  'KG',   False),
            ('P005', 'مخمر نانوایی', 70000,  'KG',   False),
            ('P011', 'نان بربری', 100000, 'NUM',  True),
            ('P012', 'نان سنگک', 105000, 'NUM',  True),
            ('P013', 'نان لواش', 110000, 'PACK', True),
            ('P021', 'کیک پادشاهی', 150000, 'PACK', True),
            ('P022', 'شیرمال', 155000, 'BOX',  True),
        ]
        for code, name, price, unit_code, is_fg in products_data:
            unit_obj = unit_map.get(unit_code) or unit_default
            p, c = Product.objects.get_or_create(
                code=code,
                defaults={
                    'name': name, 'category': cat,
                    'unit': unit_obj, 'shelf_life_days': 15,
                    'default_price': Decimal(str(price)),
                    'is_finished_good': is_fg,
                }
            )
            if c:
                self.stdout.write(f'  ✓ Product: {code} (unit={unit_code}, fg={is_fg})')

        # Distributors
        from apps.partners.models import Distributor
        for code, name, mobile in [
            ('D001', 'عامل پخص مرکز', '09121110001'),
            ('D002', 'عامل پخص شمال', '09121110002'),
            ('D003', 'عامل پخص جنوب', '09121110003'),
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

        # Inventory Lots — برای همه‌ی محصولات نمونه لات ایجاد می‌کنیم
        # تا فروش FEFO بدون خطا کار کند.
        from apps.inventory.models import InventoryLot
        today = date.today()
        # انقضای متغیر برای تست FEFO: ۳، ۷، ۱۵، ۳۰، ۶۰ روز
        expiry_days = [3, 7, 15, 30, 60, 90]
        all_product_codes = ['P001', 'P002', 'P003', 'P004', 'P005',
                             'P011', 'P012', 'P013', 'P021', 'P022']
        for i, code in enumerate(all_product_codes):
            try:
                prod = Product.objects.get(code=code)
            except Product.DoesNotExist:
                continue
            days_offset = expiry_days[i % len(expiry_days)]
            batch_no = f'BATCH-2026-{i+1:03d}'
            lot, c = InventoryLot.objects.get_or_create(
                product=prod,
                warehouse=wh,
                batch_no=batch_no,
                defaults={
                    'production_date': today - timedelta(days=2),
                    'expiry_date': today + timedelta(days=days_offset),
                    'initial_qty': Decimal('200'),
                    'current_qty': Decimal('200'),
                    'weighted_avg_cost': Decimal('25000'),
                }
            )
            if c:
                self.stdout.write(f'  ✓ Lot: {lot.batch_no} (محصول {code}، انقضا {days_offset} روز)')

        # ۲.۱) StockBalance — برای هر لات یک رکورد موجودی تجمیعی بساز
        # (StockBalance به‌صورت خودکار از lot ساخته نمی‌شود؛ باید دستی بسازیم)
        from apps.inventory.models import StockBalance
        for lot in InventoryLot.objects.all():
            sb, c = StockBalance.objects.get_or_create(
                product=lot.product,
                warehouse=lot.warehouse,
                defaults={
                    'total_qty': lot.current_qty,
                    'total_value': lot.current_qty * lot.weighted_avg_cost,
                },
            )
            if c:
                self.stdout.write(f'  ✓ StockBalance: {lot.product.code} = {lot.current_qty}')
            else:
                # به‌روزرسانی
                sb.total_qty = lot.current_qty
                sb.total_value = lot.current_qty * lot.weighted_avg_cost
                sb.save()

        # Accounting - seed accounts (4-level chart of accounts)
        # level 1 = کل, 2 = میانی, 3 = تفصیلی (postable), 4 = شخص تفصیلی (postable)
        # Only level >= 3 are postable (enforced by Account.save()).
        # These account codes are referenced by JournalService.ACCOUNT_CODES and
        # the auto-journal services. They MUST exist or the signal will
        # log an error and the journal will not be created.
        from apps.accounting.models import Account
        # (code, name, type, parent_code, level, postable_override)
        # postable_override: True/False/None — None means "auto from level"
        accounts_data = [
            # Level 1 — کل
            ('1', 'دارایی‌ها', 'asset', None, 1, None),
            ('2', 'بدهی‌ها', 'liability', None, 1, None),
            ('3', 'حقوق صاحبان سهام', 'equity', None, 1, None),
            ('4', 'درآمدها', 'revenue', None, 1, None),
            ('5', 'هزینه‌ها', 'expense', None, 1, None),

            # Level 2 — میانی (not postable)
            ('10', 'دارایی‌های جاری', 'asset', '1', 2, None),
            ('14', 'سایر دارایی‌های جاری', 'asset', '1', 2, None),
            ('20', 'بدهی‌های جاری', 'liability', '2', 2, None),
            ('30', 'سرمایه', 'equity', '3', 2, None),
            ('40', 'درآمد فروش', 'revenue', '4', 2, None),

            # Level 3 — تفصیلی (postable)
            # نکته: کدهای 50/51/52 برای backward-compat با ACCOUNT_CODES فعلی،
            # در سطح 3 (تفصیلی) مستقیماً تحت '5' قرار می‌گیرند.
            ('101', 'موجودی مواد اولیه', 'asset', '10', 3, None),
            ('101F', 'موجودی محصولات', 'asset', '10', 3, None),
            ('102', 'حساب‌های دریافتنی از فروشگاه', 'asset', '10', 3, None),
            ('103', 'نقد و بانک', 'asset', '10', 3, None),
            ('104', 'موجودی امانی در فروشگاه', 'asset', '10', 3, None),
            ('140', 'کالای نزد کارپرداز', 'asset', '14', 3, None),
            ('141', 'کالای در حال ساخت', 'asset', '14', 3, None),
            ('201', 'حساب‌های پرداختنی', 'liability', '20', 3, None),
            ('401', 'درآمد فروش امانی', 'revenue', '40', 3, None),
            ('402', 'درآمد فروش قطعی', 'revenue', '40', 3, None),
            ('50', 'بهای تمام‌شده فروش', 'expense', '5', 3, None),
            ('51', 'ضایعات تولید', 'expense', '5', 3, None),
            ('52', 'هزینه‌های پخش', 'expense', '5', 3, None),
        ]
        for code, name, acc_type, parent_code, level, postable_override in accounts_data:
            parent = Account.objects.filter(code=parent_code).first() if parent_code else None
            # if level >= 3 and no override → postable=True; if level < 3 → postable=False
            if postable_override is None:
                postable = level >= 3
            else:
                postable = postable_override
            obj, c = Account.objects.get_or_create(
                code=code,
                defaults={
                    'name': name,
                    'type': acc_type,
                    'parent': parent,
                    'level': level,
                    'is_postable': postable,
                }
            )
            if c:
                self.stdout.write(f'  ✓ Account: {code} (level {level}, postable={postable})')
            else:
                # به‌روزرسانی level و is_postable در صورت نیاز
                changed = False
                if obj.level != level:
                    obj.level = level
                    changed = True
                if obj.is_postable != postable:
                    obj.is_postable = postable
                    changed = True
                if obj.parent_id != (parent.id if parent else None):
                    obj.parent = parent
                    changed = True
                if changed:
                    # bypass save() auto-level logic by direct update
                    Account.objects.filter(pk=obj.pk).update(
                        level=level, is_postable=postable, parent=parent
                    )
                    self.stdout.write(f'  ~ Account: {code} (updated level/postable)')

        # تفصیلی نقد و بانک (2 حساب نمونه: 103/1 صندوق، 103/2 بانک)
        cash_accounts_data = [
            ('103/1', 'صندوق نقدی', 'asset', '103', 'SEED-CASH-CASH'),
            ('103/2', 'بانک ملی', 'asset', '103', 'SEED-CASH-BANK'),
        ]
        from apps.accounting.models import Account as _Acc2
        for code, name, acc_type, parent_code, marker in cash_accounts_data:
            parent = _Acc2.objects.filter(code=parent_code).first()
            obj, c = _Acc2.objects.get_or_create(
                code=code,
                defaults={
                    'name': name,
                    'type': acc_type,
                    'parent': parent,
                    'level': 4,
                    'is_postable': True,
                    'description': f'{marker} | تفصیلی نقد',
                }
            )
            if c:
                self.stdout.write(f'  ✓ Detail Account: {code} ({name})')

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

        # =============================================================
        # بخش‌های افزوده‌شده — هفته ۵
        # =============================================================
        from django.utils import timezone

        # ----- (۱) لات‌های نزدیک به انقضا — NEAR-EXP-001..005 -----
        try:
            near_exp_specs = [
                ('NEAR-EXP-001', 'P001', 1),
                ('NEAR-EXP-002', 'P002', 2),
                ('NEAR-EXP-003', 'P003', 4),
                ('NEAR-EXP-004', 'P004', 5),
                ('NEAR-EXP-005', 'P005', 6),
            ]
            near_exp_created = 0
            for batch_no, prod_code, exp_days in near_exp_specs:
                try:
                    prod = Product.objects.get(code=prod_code)
                except Product.DoesNotExist:
                    self.stdout.write(f'  ! near-expiry: product {prod_code} missing, skip')
                    continue
                lot, c = InventoryLot.objects.get_or_create(
                    product=prod,
                    warehouse=wh,
                    batch_no=batch_no,
                    defaults={
                        'production_date': today - timedelta(days=2),
                        'expiry_date': today + timedelta(days=exp_days),
                        'initial_qty': Decimal('500'),
                        'current_qty': Decimal('500'),
                        'weighted_avg_cost': Decimal('25000'),
                        'status': InventoryLot.LotStatus.ACTIVE,
                    },
                )
                if c:
                    near_exp_created += 1
                    # ساخت StockBalance برای لات جدید
                    sb, sb_c = StockBalance.objects.get_or_create(
                        product=prod, warehouse=wh,
                        defaults={
                            'total_qty': Decimal('500'),
                            'total_value': Decimal('500') * Decimal('25000'),
                        },
                    )
                    if sb_c:
                        self.stdout.write(
                            f'  ✓ StockBalance for near-expiry: {prod.code}'
                        )
                    self.stdout.write(
                        f'  ✓ NearExpiryLot: {batch_no} (محصول {prod_code}، انقضا +{exp_days} روز)'
                    )
            self.stdout.write(f'  → near-expiry lots created/verified: {near_exp_created}')
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'  ! near-expiry section failed: {e}'))

        # ----- (۲) ۸ فروش نمونه (۵ امانی + ۳ قطعی) -----
        try:
            from apps.sales.services import SalesService
            from apps.sales.models import SalesHeader

            existing_seed_sales = SalesHeader.objects.filter(
                notes__contains=self.SEED_MARKER_SALE
            ).count()
            if existing_seed_sales >= 8:
                self.stdout.write(
                    f'  ~ sales: {existing_seed_sales} already seeded, skipping'
                )
            else:
                # تنوع محصولات و فروشگاه‌ها برای پوشش گزارش‌ها
                sale_specs = [
                    # (store_code, prod_code, qty, unit_price, sales_type, days_ago, marker_seq)
                    ('S001', 'P001', 5, 50000, 'consignment', 1, 1),
                    ('S002', 'P002', 8, 55000, 'consignment', 3, 2),
                    ('S003', 'P003', 6, 60000, 'consignment', 5, 3),
                    ('S004', 'P004', 10, 65000, 'consignment', 8, 4),
                    ('S005', 'P005', 4, 70000, 'consignment', 12, 5),
                    ('S006', 'P011', 5, 100000, 'firm', 6, 6),
                    ('S007', 'P012', 7, 105000, 'firm', 10, 7),
                    ('S008', 'P013', 3, 110000, 'firm', 15, 8),
                ]
                sales_created = 0
                for store_code, prod_code, qty, price, stype, days_ago, seq in sale_specs:
                    try:
                        store = Store.objects.get(code=store_code)
                        prod = Product.objects.get(code=prod_code)
                        sale_date = today - timedelta(days=days_ago)
                        marker = f'{self.SEED_MARKER_SALE}-{seq:03d}'
                        sale = SalesService.create_sale(
                            store_id=store.id,
                            sales_type=stype,
                            sale_date=sale_date,
                            lines=[{
                                'product_id': prod.id,
                                'qty': Decimal(str(qty)),
                                'unit_price': Decimal(str(price)),
                                'warehouse_id': wh.id,
                            }],
                            distributor_id=1,
                            created_by=admin_user,
                            notes=f'{marker} | فروش نمونه seed',
                        )
                        sales_created += 1
                        self.stdout.write(
                            f'  ✓ Sale #{sale.sale_no} ({stype}) '
                            f'→ store {store_code} prod {prod_code}'
                        )
                    except Exception as e:
                        self.stdout.write(
                            self.style.WARNING(
                                f'  ! sale seq={seq} failed ({store_code}/{prod_code}): {e}'
                            )
                        )
                self.stdout.write(f'  → sales created: {sales_created}')
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'  ! sales section failed: {e}'))

        # ----- (۳) ۵ سند پخش به عوامل ۱/۲/۳ -----
        try:
            from apps.dispatch.services import DispatchService
            from apps.dispatch.models import DispatchHeader

            existing_seed_disps = DispatchHeader.objects.filter(
                notes__contains=self.SEED_MARKER_DISP
            ).count()
            if existing_seed_disps >= 5:
                self.stdout.write(
                    f'  ~ dispatches: {existing_seed_disps} already seeded, skipping'
                )
            else:
                dispatch_specs = [
                    # (distributor_code, dest_store_code, prod_code, qty, unit_price,
                    #  days_ago, target_status)
                    ('D001', 'S001', 'P001', 20, 50000, 2,
                     DispatchHeader.DispatchStatus.IN_DELIVERY),
                    ('D001', 'S002', 'P003', 15, 60000, 5,
                     DispatchHeader.DispatchStatus.ARRIVED),
                    ('D002', 'S003', 'P002', 25, 55000, 7,
                     DispatchHeader.DispatchStatus.IN_DELIVERY),
                    ('D002', 'S004', 'P004', 10, 65000, 11,
                     DispatchHeader.DispatchStatus.ARRIVED),
                    ('D003', 'S005', 'P005', 18, 70000, 15,
                     DispatchHeader.DispatchStatus.IN_DELIVERY),
                ]
                dispatches_created = 0
                for dist_code, store_code, prod_code, qty, price, days_ago, target_status in dispatch_specs:
                    try:
                        dist = Distributor.objects.get(code=dist_code)
                        store = Store.objects.get(code=store_code)
                        prod = Product.objects.get(code=prod_code)
                        dispatch_date = today - timedelta(days=days_ago)
                        marker = f'{self.SEED_MARKER_DISP}-{dist_code}-{store_code}-{prod_code}'
                        dispatch = DispatchService.create_dispatch(
                            distributor_id=dist.id,
                            dispatch_date=dispatch_date,
                            lines=[{
                                'product_id': prod.id,
                                'qty': Decimal(str(qty)),
                                'unit_price': Decimal(str(price)),
                                'dest_store_id': store.id,
                            }],
                            notes=f'{marker} | پخش نمونه seed',
                            created_by=admin_user,
                        )
                        # تغییر وضعیت به IN_DELIVERY یا ARRIVED پس از ساخت
                        dispatch.status = target_status
                        dispatch.save(update_fields=['status', 'updated_at'])
                        dispatches_created += 1
                        self.stdout.write(
                            f'  ✓ Dispatch #{dispatch.dispatch_no} '
                            f'→ {dist_code} / {store_code} / {prod_code} ({target_status})'
                        )
                    except Exception as e:
                        self.stdout.write(
                            self.style.WARNING(
                                f'  ! dispatch {dist_code}/{store_code}/{prod_code} failed: {e}'
                            )
                        )
                self.stdout.write(f'  → dispatches created: {dispatches_created}')
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'  ! dispatches section failed: {e}'))

        # ----- (۴) ۵ سند ضایعات (۲ انبار + ۲ فروشگاه + ۱ عامل پخش) -----
        try:
            from apps.inventory.services.waste_service import WasteService
            from apps.inventory.models import WasteDocument

            existing_seed_wastes = WasteDocument.objects.filter(
                reason__contains=self.SEED_MARKER_WASTE
            ).count()
            if existing_seed_wastes >= 5:
                self.stdout.write(
                    f'  ~ wastes: {existing_seed_wastes} already seeded, skipping'
                )
            else:
                # تنوع محصولات برای پوشش بهتر گزارش by_product
                waste_specs = [
                    # (waste_type, prod_code, qty, unit_cost, condition, days_ago, marker_seq,
                    #  store_code, dist_code)
                    ('warehouse',  'P001', 3, 25000, 'damaged',     2, 1, None, None),
                    ('warehouse',  'P003', 2, 30000, 'near_expiry', 5, 2, None, None),
                    ('store',      'P002', 4, 25000, 'damaged',     3, 3, 'S001', None),
                    ('store',      'P004', 1, 35000, 'expired',     9, 4, 'S002', None),
                    ('distributor','P005', 2, 40000, 'damaged',    12, 5, None, 'D001'),
                ]
                wastes_created = 0
                for (wtype, prod_code, qty, unit_cost, condition, days_ago, seq,
                     store_code, dist_code) in waste_specs:
                    try:
                        prod = Product.objects.get(code=prod_code)
                        waste_date = today - timedelta(days=days_ago)
                        marker = f'{self.SEED_MARKER_WASTE}-{seq:03d}'
                        kwargs = {
                            'waste_type': wtype,
                            'lines': [{
                                'product_id': prod.id,
                                'qty': Decimal(str(qty)),
                                'unit_cost': Decimal(str(unit_cost)),
                                'condition': condition,
                                'description': f'{marker} | خط ضایعات seed',
                            }],
                            'reason': f'{marker} | ضایعات نمونه seed ({wtype})',
                            'waste_date': waste_date,
                            'created_by': admin_user,
                        }
                        if wtype == 'warehouse':
                            kwargs['warehouse_id'] = wh.id
                        elif wtype == 'store':
                            store = Store.objects.get(code=store_code)
                            kwargs['store_id'] = store.id
                        elif wtype == 'distributor':
                            dist = Distributor.objects.get(code=dist_code)
                            kwargs['distributor_id'] = dist.id

                        waste_doc = WasteService.create_waste(**kwargs)
                        wastes_created += 1
                        loc = store_code or dist_code or 'WH-MAIN'
                        self.stdout.write(
                            f'  ✓ WasteDoc #{waste_doc.waste_no} '
                            f'({wtype} @ {loc}) prod={prod_code}'
                        )
                    except Exception as e:
                        self.stdout.write(
                            self.style.WARNING(
                                f'  ! waste seq={seq} ({wtype}/{prod_code}) failed: {e}'
                            )
                        )
                self.stdout.write(f'  → wastes created: {wastes_created}')
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'  ! wastes section failed: {e}'))

        # =============================================================
        # بخش‌های افزوده‌شده — Production Workflow (P1)
        # =============================================================
        # (۵) ۳ کارپرداز + انبارهای مواد اولیه/محصولات/کارگاه + تفصیلی حساب‌ها
        try:
            from apps.workshop.models import Contractor
            from apps.inventory.models import Warehouse

            # 5.1 — ۳ کارپرداز (C001, C002, C003)
            contractors_data = [
                ('C001', 'کارپرداز رضایی', '09123330001', 'کارگاه رضایی', 'تهران - شمال'),
                ('C002', 'کارپرداز موسوی', '09123330002', 'کارگاه موسوی', 'تهران - غرب'),
                ('C003', 'کارپرداز احمدی', '09123330003', 'کارگاه احمدی', 'کرج'),
            ]
            contractors_created = 0
            for code, name, mobile, workshop_name, address in contractors_data:
                obj, c = Contractor.objects.get_or_create(
                    code=code,
                    defaults={
                        'name': name,
                        'mobile': mobile,
                        'workshop_name': workshop_name,
                        'address': address,
                        'created_by': admin_user,
                    }
                )
                if c:
                    contractors_created += 1
                    self.stdout.write(f'  ✓ Contractor: {code} ({name})')
                else:
                    self.stdout.write(f'  ~ Contractor: {code} (exists)')
            self.stdout.write(f'  → contractors created: {contractors_created}')

            # 5.2 — ۲ انبار مواد اولیه، ۱ انبار محصولات، ۳ انبار کارگاه
            warehouses_data = [
                # (code, name, type, contractor_code, marker)
                ('WH-RAW-01', 'انبار مواد اولیه ۱', 'raw_materials', None, 'SEED-WH-RAW-01'),
                ('WH-RAW-02', 'انبار مواد اولیه ۲', 'raw_materials', None, 'SEED-WH-RAW-02'),
                ('WH-FIN-01', 'انبار محصولات', 'finished_goods', None, 'SEED-WH-FIN-01'),
                ('WH-WS-C001', 'کارگاه رضایی', 'workshop', 'C001', 'SEED-WH-WS-C001'),
                ('WH-WS-C002', 'کارگاه موسوی', 'workshop', 'C002', 'SEED-WH-WS-C002'),
                ('WH-WS-C003', 'کارگاه احمدی', 'workshop', 'C003', 'SEED-WH-WS-C003'),
            ]
            whs_created = 0
            for code, name, wtype, contractor_code, marker in warehouses_data:
                contractor = None
                if contractor_code:
                    contractor = Contractor.objects.get(code=contractor_code)
                obj, c = Warehouse.objects.get_or_create(
                    code=code,
                    defaults={
                        'name': name,
                        'type': wtype,
                        'contractor': contractor,
                        'address': f'{marker} | انبار نمونه',
                        'is_active': True,
                        'created_by': admin_user,
                    }
                )
                if c:
                    whs_created += 1
                    self.stdout.write(f'  ✓ Warehouse: {code} ({wtype})')
                else:
                    # به‌روزرسانی type و contractor در صورت نیاز
                    update_fields = []
                    if obj.type != wtype:
                        obj.type = wtype
                        update_fields.append('type')
                    if obj.contractor_id != (contractor.id if contractor else None):
                        obj.contractor = contractor
                        update_fields.append('contractor')
                    if update_fields:
                        obj.save(update_fields=update_fields + ['updated_at'])
                        self.stdout.write(f'  ~ Warehouse: {code} (updated)')
            self.stdout.write(f'  → warehouses created: {whs_created}')

            # 5.2.5 — کارکنان (Employees) — ۵ پرسنل نمونه
            try:
                from apps.workshop.models import Employee

                ws_wh_1 = Warehouse.objects.get(code='WH-WS-C001')
                ws_wh_2 = Warehouse.objects.get(code='WH-WS-C002')
                ws_wh_3 = Warehouse.objects.get(code='WH-WS-C003')

                employees_data = [
                    # (code, first, last, national_id, mobile, position, workshop_code, hire_days_ago)
                    ('EMP-001', 'علی',    'رضایی',   '0011111111', '09123330011', 'انباردار',     'WH-WS-C001', 365),
                    ('EMP-002', 'محمد',   'حسینی',   '0022222222', '09123330012', 'کارگر',        'WH-WS-C001', 300),
                    ('EMP-003', 'حسن',    'کریمی',   '0033333333', '09123330013', 'مسئول کارگاه', 'WH-WS-C002', 250),
                    ('EMP-004', 'فاطمه',  'احمدی',   '0044444444', '09123330014', 'کارگر',        'WH-WS-C002', 200),
                ]
                emps_created = 0
                for (code, first, last, natl, mobile, position,
                     ws_code, hire_days) in employees_data:
                    ws_obj = None
                    if ws_code:
                        try:
                            ws_obj = Warehouse.objects.get(code=ws_code)
                        except Warehouse.DoesNotExist:
                            ws_obj = None
                    hire_date = today - timedelta(days=hire_days)
                    obj, c = Employee.objects.get_or_create(
                        code=code,
                        defaults={
                            'first_name': first,
                            'last_name': last,
                            'national_id': natl,
                            'mobile': mobile,
                            'position': position,
                            'workshop': ws_obj,
                            'hire_date': hire_date,
                            'is_active': True,
                            'created_by': admin_user,
                        }
                    )
                    if c:
                        emps_created += 1
                        self.stdout.write(
                            f'  ✓ Employee: {code} - {first} {last} ({position})'
                        )
                self.stdout.write(f'  → employees created: {emps_created}')
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'  ! employees section failed: {e}')
                )

            # 5.3 — ۲ خرید مواد اولیه (با auto-journal + auto-lot)
            try:
                from apps.workshop.services import PurchaseService
                from apps.workshop.models import PurchaseHeader
                from apps.accounting.models import Account as _Acct

                existing_purchases = PurchaseHeader.objects.filter(
                    notes__contains=self.SEED_MARKER_WORKSHOP
                ).count()
                if existing_purchases >= 2:
                    self.stdout.write(
                        f'  ~ purchases: {existing_purchases} already seeded, skipping'
                    )
                else:
                    raw_wh_1 = Warehouse.objects.get(code='WH-RAW-01')
                    raw_wh_2 = Warehouse.objects.get(code='WH-RAW-02')
                    cash_acct = _Acct.objects.get(code='103/1')
                    prod_001 = Product.objects.get(code='P001')
                    prod_002 = Product.objects.get(code='P002')
                    prod_003 = Product.objects.get(code='P003')

                    # Purchase 1: contractor C001, WH-RAW-01, 2 lines (P001, P002)
                    purchase_1 = PurchaseService.create_purchase(
                        purchase_no='PUR-2026-0001',
                        purchase_date=today - timedelta(days=20),
                        contractor_id=Contractor.objects.get(code='C001').id,
                        warehouse_id=raw_wh_1.id,
                        cash_account_id=cash_acct.id,
                        lines=[
                            {
                                'product_id': prod_001.id,
                                'qty': Decimal('100'),
                                'unit_price': Decimal('25000'),
                                'shelf_life_days': 30,
                            },
                            {
                                'product_id': prod_002.id,
                                'qty': Decimal('80'),
                                'unit_price': Decimal('28000'),
                                'shelf_life_days': 30,
                            },
                        ],
                        notes=f'{self.SEED_MARKER_WORKSHOP}-PUR-001 | خرید نمونه ۱',
                        created_by=admin_user,
                    )
                    self.stdout.write(
                        f'  ✓ Purchase #{purchase_1.purchase_no} '
                        f'({purchase_1.total_qty} qty, {purchase_1.total_amount} rial)'
                    )

                    # Purchase 2: contractor C002, WH-RAW-02, 1 line (P003)
                    purchase_2 = PurchaseService.create_purchase(
                        purchase_no='PUR-2026-0002',
                        purchase_date=today - timedelta(days=15),
                        contractor_id=Contractor.objects.get(code='C002').id,
                        warehouse_id=raw_wh_2.id,
                        cash_account_id=cash_acct.id,
                        lines=[
                            {
                                'product_id': prod_003.id,
                                'qty': Decimal('120'),
                                'unit_price': Decimal('30000'),
                                'shelf_life_days': 45,
                            },
                        ],
                        notes=f'{self.SEED_MARKER_WORKSHOP}-PUR-002 | خرید نمونه ۲',
                        created_by=admin_user,
                    )
                    self.stdout.write(
                        f'  ✓ Purchase #{purchase_2.purchase_no} '
                        f'({purchase_2.total_qty} qty, {purchase_2.total_amount} rial)'
                    )
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'  ! purchases section failed: {e}'))

            # 5.4 — ۲ حواله کارگاه + ۱ برگشت کارگاه
            try:
                from apps.workshop.services import WorkshopService
                from apps.workshop.models import WorkshopIssue, WorkshopReturn

                existing_issues = WorkshopIssue.objects.filter(
                    notes__contains=self.SEED_MARKER_WORKSHOP
                ).count()
                if existing_issues >= 2:
                    self.stdout.write(
                        f'  ~ issues: {existing_issues} already seeded, skipping'
                    )
                else:
                    raw_wh_1 = Warehouse.objects.get(code='WH-RAW-01')
                    raw_wh_2 = Warehouse.objects.get(code='WH-RAW-02')
                    ws_wh_1 = Warehouse.objects.get(code='WH-WS-C001')
                    ws_wh_2 = Warehouse.objects.get(code='WH-WS-C002')
                    prod_001 = Product.objects.get(code='P001')
                    prod_002 = Product.objects.get(code='P002')
                    prod_003 = Product.objects.get(code='P003')

                    # Issue 1: C001, from WH-RAW-01 to WH-WS-C001, P001 qty=50
                    issue_1 = WorkshopService.create_issue(
                        issue_no='WS-2026-0001',
                        issue_date=today - timedelta(days=10),
                        contractor_id=Contractor.objects.get(code='C001').id,
                        from_warehouse_id=raw_wh_1.id,
                        to_warehouse_id=ws_wh_1.id,
                        lines=[
                            {'product_id': prod_001.id, 'qty': Decimal('50')},
                        ],
                        notes=f'{self.SEED_MARKER_WORKSHOP}-WS-001 | حواله نمونه ۱',
                        created_by=admin_user,
                    )
                    self.stdout.write(
                        f'  ✓ Issue #{issue_1.issue_no} '
                        f'({issue_1.total_qty} qty, {issue_1.total_value} rial)'
                    )

                    # Issue 2: C002, from WH-RAW-02 to WH-WS-C002, P003 qty=60
                    issue_2 = WorkshopService.create_issue(
                        issue_no='WS-2026-0002',
                        issue_date=today - timedelta(days=8),
                        contractor_id=Contractor.objects.get(code='C002').id,
                        from_warehouse_id=raw_wh_2.id,
                        to_warehouse_id=ws_wh_2.id,
                        lines=[
                            {'product_id': prod_003.id, 'qty': Decimal('60')},
                        ],
                        notes=f'{self.SEED_MARKER_WORKSHOP}-WS-002 | حواله نمونه ۲',
                        created_by=admin_user,
                    )
                    self.stdout.write(
                        f'  ✓ Issue #{issue_2.issue_no} '
                        f'({issue_2.total_qty} qty, {issue_2.total_value} rial)'
                    )

                    # Return 1: reverse part of issue 1 — return 20 of P001
                    issue_line_1 = issue_1.lines.first()
                    return_1 = WorkshopService.create_return(
                        return_no='WRT-2026-0001',
                        return_date=today - timedelta(days=5),
                        issue_id=issue_1.id,
                        lines=[
                            {'issue_line_id': issue_line_1.id, 'qty': Decimal('20')},
                        ],
                        reason=f'{self.SEED_MARKER_WORKSHOP}-WRT-001 | برگشت نمونه',
                        created_by=admin_user,
                    )
                    self.stdout.write(
                        f'  ✓ Return #{return_1.return_no} '
                        f'({return_1.total_qty} qty, {return_1.total_value} rial)'
                    )
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'  ! issues/returns section failed: {e}'))

            # 5.5 — ۱ بچ تولید تکمیل‌شده با خروج به انبار محصولات
            try:
                from apps.production.services import ProductionService
                from apps.production.models import ProductionBatch

                existing_seed_batches = ProductionBatch.objects.filter(
                    notes__contains=self.SEED_MARKER_PROD
                ).count()
                if existing_seed_batches >= 1:
                    self.stdout.write(
                        f'  ~ production batches: {existing_seed_batches} already seeded, skipping'
                    )
                else:
                    # محصول پایه P001 — بچ تولید با ورودی کارگاه
                    # برای تولید، باید یک بچ planned بسازیم، شروع کنیم، یک مصرف ثبت کنیم،
                    # سپس تکمیل کنیم.
                    prod = Product.objects.get(code='P011')  # محصول نهایی متفاوت

                    batch = ProductionService.create_batch(
                        product_id=prod.id,
                        planned_qty=Decimal('100'),
                        notes=f'{self.SEED_MARKER_PROD}-PB-001 | بچ تولید نمونه',
                        created_by=admin_user,
                    )
                    ProductionService.start_batch(
                        batch_id=batch.id,
                        started_by=admin_user,
                    )

                    # مصرف از لات‌های موجود در انبار اصلی (WH-MAIN)
                    # یا انبار مواد اولیه — در اینجا از انبار اصلی استفاده می‌کنیم چون
                    # لات‌های موجود در WH-MAIN از قبل seed شده‌اند.
                    from apps.inventory.models import InventoryLot
                    lot_to_consume = InventoryLot.objects.filter(
                        product__code='P001',
                        warehouse__code='WH-MAIN',
                        current_qty__gt=0,
                        status=InventoryLot.LotStatus.ACTIVE,
                        deleted_at__isnull=True,
                    ).order_by('expiry_date').first()
                    if lot_to_consume:
                        # مصرف ۵۰ واحد (کمتر از موجودی)
                        consume_qty = min(Decimal('50'), lot_to_consume.current_qty)
                        ProductionService.consume_material(
                            batch_id=batch.id,
                            material_lot_id=lot_to_consume.id,
                            qty=consume_qty,
                            consumed_by=admin_user,
                        )
                        self.stdout.write(
                            f'  ~ Production: consumed {consume_qty} of P001 '
                            f'from lot {lot_to_consume.batch_no}'
                        )

                    ProductionService.complete_batch(
                        batch_id=batch.id,
                        actual_qty=Decimal('80'),
                        waste_qty=Decimal('2'),
                        completed_by=admin_user,
                    )
                    self.stdout.write(
                        f'  ✓ ProductionBatch #{batch.batch_no} completed '
                        f'(actual_qty={batch.actual_qty}, cost={batch.weighted_avg_cost})'
                    )
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'  ! production section failed: {e}'))

        except Exception as e:
            self.stdout.write(self.style.WARNING(f'  ! workshop section failed: {e}'))

        # =============================================================
        # خلاصه نهایی
        # =============================================================
        from apps.sales.models import SalesHeader
        from apps.dispatch.models import DispatchHeader
        from apps.inventory.models import WasteDocument

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'✅ Data seeded!'))
        self.stdout.write(f'   Users: {User.objects.count()}')
        self.stdout.write(f'   Products: {Product.objects.count()}')
        self.stdout.write(f'   Stores: {Store.objects.count()}')
        self.stdout.write(f'   Lots: {InventoryLot.objects.count()}')
        self.stdout.write(f'   StockBalance: {StockBalance.objects.count()}')
        self.stdout.write(f'   Accounts: {Account.objects.count()}')
        self.stdout.write(f'   Sales: {SalesHeader.objects.count()}')
        self.stdout.write(f'   Dispatches: {DispatchHeader.objects.count()}')
        self.stdout.write(f'   WasteDocuments: {WasteDocument.objects.count()}')
        # Workshop section summary
        try:
            from apps.workshop.models import (
                Contractor as _C, PurchaseHeader as _P,
                WorkshopIssue as _I, WorkshopReturn as _R,
                Employee as _E,
            )
            from apps.production.models import ProductionBatch as _PB
            from apps.accounting.models import JournalHeader as _J
            from apps.products.models import Unit as _U
            self.stdout.write(f'   Contractors: {_C.objects.count()}')
            self.stdout.write(f'   Purchases: {_P.objects.count()}')
            self.stdout.write(f'   WorkshopIssues: {_I.objects.count()}')
            self.stdout.write(f'   WorkshopReturns: {_R.objects.count()}')
            self.stdout.write(f'   ProductionBatches: {_PB.objects.count()}')
            self.stdout.write(f'   Journals: {_J.objects.count()}')
            self.stdout.write(f'   Units: {_U.objects.count()}')
            self.stdout.write(f'   Employees: {_E.objects.count()}')
        except Exception:
            pass
