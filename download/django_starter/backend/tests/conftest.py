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
    return Store.objects.create(
        code='S-TEST',
        name='فروشگاه تست',
        sales_model='consignment',
        tier='gold',
        credit_limit=100000000,
    )


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
