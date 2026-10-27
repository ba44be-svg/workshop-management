"""
Conftest for pytest — common fixtures
"""
import pytest
import pytest_django
from django.contrib.auth import get_user_model


@pytest.fixture
def user_model():
    return get_user_model()


@pytest.fixture
def admin_user(db, user_model):
    """کاربر مدیر برای تست‌ها"""
    return user_model.objects.create_user(
        username='admin_test',
        email='admin@test.local',
        password='testpass123',
        role='manager',
        phone='09120000000',
    )


@pytest.fixture
def distributor_user(db, user_model):
    return user_model.objects.create_user(
        username='distributor_test',
        email='dist@test.local',
        password='testpass123',
        role='distributor',
        phone='09121110001',
    )


@pytest.fixture
def store_owner_user(db, user_model):
    return user_model.objects.create_user(
        username='store_owner_test',
        email='store@test.local',
        password='testpass123',
        role='store_owner',
        phone='09121110002',
    )


@pytest.fixture
def api_client():
    """DRF API Client"""
    from rest_framework.test import APIClient
    return APIClient()


@pytest.fixture
def authenticated_client(api_client, admin_user):
    """API client با احراز هویت"""
    api_client.force_authenticate(user=admin_user)
    return api_client


@pytest.fixture
def distributor_client(api_client, distributor_user):
    api_client.force_authenticate(user=distributor_user)
    return api_client


@pytest.fixture
def store_owner_client(api_client, store_owner_user):
    api_client.force_authenticate(user=store_owner_user)
    return api_client


@pytest.fixture
def main_warehouse(db):
    from apps.inventory.models import Warehouse
    return Warehouse.objects.create(
        code='WH-TEST',
        name='انبار تست',
        type=Warehouse.WarehouseType.MAIN,
    )


@pytest.fixture
def product(db):
    from apps.products.models import Product, ProductCategory
    cat = ProductCategory.objects.create(code='CAT-TEST', name='دسته تست')
    return Product.objects.create(
        code='P-TEST-001',
        name='محصول تست',
        category=cat,
        unit='عدد',
        shelf_life_days=15,
        default_price=50000,
    )


@pytest.fixture
def store(db):
    from apps.partners.models import Store
    from apps.inventory.models import Warehouse
    s = Store.objects.create(
        code='S-TEST',
        name='فروشگاه تست',
        sales_model='consignment',
        tier='gold',
        credit_limit=100000000,
    )
    Warehouse.objects.create(
        code='WH-S-TEST',
        name='انبار فروشگاه تست',
        type=Warehouse.WarehouseType.STORE,
        store=s,
    )
    return s


@pytest.fixture
def lot_with_stock(db, product, main_warehouse):
    """یک لات با موجودی برای تست FEFO"""
    from datetime import date, timedelta
    from django.utils import timezone
    from apps.inventory.models import InventoryLot

    today = timezone.now().date()
    return InventoryLot.objects.create(
        product=product,
        warehouse=main_warehouse,
        batch_no='BATCH-TEST-001',
        production_date=today,
        expiry_date=today + timedelta(days=15),
        initial_qty=100,
        current_qty=100,
        weighted_avg_cost=25000,
    )


@pytest.fixture
def seed_accounts(db):
    """seed حساب‌های حسابداری برای تست‌های فروش/تولید/انبار"""
    from apps.accounting.models import Account
    accounts_data = [
        ('1', 'دارایی‌ها', 'asset', None, False),
        ('10', 'دارایی‌های جاری', 'asset', '1', False),
        ('101', 'موجودی کالا', 'asset', '10', True),
        ('102', 'حساب‌های دریافتنی', 'asset', '10', True),
        ('103', 'نقد و بانک', 'asset', '10', True),
        ('104', 'موجودی امانی', 'asset', '10', True),
        ('2', 'بدهی‌ها', 'liability', None, False),
        ('201', 'حساب‌های پرداختنی', 'liability', '2', True),
        ('3', 'حقوق صاحبان سهام', 'equity', None, False),
        ('30', 'سرمایه', 'equity', '3', True),
        ('4', 'درآمدها', 'revenue', None, False),
        ('40', 'درآمد فروش', 'revenue', '4', True),
        ('401', 'درآمد فروش امانی', 'revenue', '40', True),
        ('402', 'درآمد فروش قطعی', 'revenue', '40', True),
        ('5', 'هزینه‌ها', 'expense', None, False),
        ('50', 'بهای تمام‌شده فروش', 'expense', '5', True),
        ('51', 'ضایعات تولید', 'expense', '5', True),
        ('52', 'هزینه‌های پخش', 'expense', '5', True),
    ]
    for code, name, acc_type, parent_code, postable in accounts_data:
        parent = Account.objects.filter(code=parent_code).first() if parent_code else None
        Account.objects.get_or_create(
            code=code,
            defaults={'name': name, 'type': acc_type, 'parent': parent, 'is_postable': postable}
        )
    return Account.objects.all()
