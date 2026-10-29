"""
Integration Tests — تست‌های API واقعی
"""
import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status


@pytest.mark.django_db
@pytest.mark.integration
class TestHealthCheck:
    """تست health check endpoints"""

    def test_health_check(self, client):
        response = client.get('/api/health/')
        assert response.status_code == 200
        data = response.json()
        assert 'status' in data
        assert 'checks' in data


@pytest.mark.django_db
@pytest.mark.integration
class TestAuthentication:
    """تست احراز هویت"""

    def test_login_success(self, admin_user):
        """ورود موفق"""
        client = APIClient()
        response = client.post('/api/auth/login/', {
            'username': 'admin_test',
            'password': 'testpass123',
        }, format='json')
        assert response.status_code == 200
        data = response.json()
        assert 'access' in data
        assert 'refresh' in data

    def test_login_wrong_password(self, admin_user):
        client = APIClient()
        response = client.post('/api/auth/login/', {
            'username': 'admin_test',
            'password': 'wrongpass',
        }, format='json')
        assert response.status_code == 401

    def test_get_me_authenticated(self, authenticated_client):
        """دریافت اطلاعات کاربر فعلی"""
        response = authenticated_client.get('/api/auth/me/')
        assert response.status_code == 200
        data = response.json()
        assert data['username'] == 'admin_test'

    def test_get_me_unauthenticated(self, api_client):
        """بدون login نباید اطلاعات بده"""
        response = api_client.get('/api/auth/me/')
        assert response.status_code == 401


@pytest.mark.django_db
@pytest.mark.integration
class TestProductsAPI:
    """تست API محصولات"""

    def test_list_products_unauthorized(self, api_client, db):
        """بدون احراز هویت لیست محصولات قابل دسترس است (پورتال عمومی)"""
        response = api_client.get('/api/products/')
        assert response.status_code == 200

    def test_create_product_unauthorized_rejected(self, api_client, db):
        """ایجاد محصول بدون احراز هویت نباید مجاز باشد"""
        from apps.products.models import ProductCategory
        cat = ProductCategory.objects.create(code='CAT-NOAUTH', name='دسته بدون احراز')
        response = api_client.post('/api/products/', {
            'code': 'P-NOAUTH',
            'name': 'محصول غیر مجاز',
            'category': cat.id,
            'unit': 'عدد',
            'shelf_life_days': 10,
            'default_price': '75000.0000',
        }, format='json')
        assert response.status_code == 401

    def test_list_products_authorized(self, authenticated_client, product):
        response = authenticated_client.get('/api/products/')
        assert response.status_code == 200
        data = response.json()
        assert 'results' in data
        assert len(data['results']) >= 1

    def test_get_product_detail(self, authenticated_client, product):
        response = authenticated_client.get(f'/api/products/{product.id}/')
        assert response.status_code == 200
        data = response.json()
        assert data['code'] == 'P-TEST-001'

    def test_create_product(self, authenticated_client, db):
        """ایجاد محصول با احراز هویت مدیر"""
        from apps.products.models import ProductCategory
        cat = ProductCategory.objects.create(code='CAT-API', name='دسته API')

        response = authenticated_client.post('/api/products/', {
            'code': 'P-API-001',
            'name': 'محصول API تست',
            'category': cat.id,
            'unit': 'عدد',
            'shelf_life_days': 10,
            'default_price': '75000.0000',
        }, format='json')
        assert response.status_code == 201, f'Body: {response.content.decode()[:500]}'
        data = response.json()
        assert data['code'] == 'P-API-001'

    def test_barcode_scan(self, authenticated_client, product, db):
        """اسکن بارکد محصول"""
        from apps.products.models import Barcode
        # پاک‌سازی هر بارکدی که ممکن است از قبل وجود داشته باشد
        Barcode.objects.filter(
            entity_type='product', entity_id=product.id,
        ).delete()
        Barcode.objects.create(
            entity_type='product',
            entity_id=product.id,
            barcode_value='6421234567890',
            qr_code_data='TEST',
        )

        response = authenticated_client.post('/api/products/barcodes/scan/', {
            'barcode_value': '6421234567890',
            'context': 'sale_draft',
        }, format='json')
        assert response.status_code == 200
        data = response.json()
        assert data['found'] is True


@pytest.mark.django_db
@pytest.mark.integration
class TestInventoryAPI:
    """تست API انبار — شامل FEFO"""

    def test_fefo_allocation(self, authenticated_client, lot_with_stock, product, main_warehouse):
        """تست endpoint FEFO"""
        response = authenticated_client.post('/api/inventory/allocate-fefo/', {
            'product_id': product.id,
            'warehouse_id': main_warehouse.id,
            'qty': '30',
        }, format='json')
        assert response.status_code == 200
        data = response.json()
        assert data['allocated'] is True
        assert data['total_allocated_qty'] == '30.000'

    def test_fefo_insufficient(self, authenticated_client, lot_with_stock, product, main_warehouse):
        """تست کمبود موجودی در endpoint"""
        response = authenticated_client.post('/api/inventory/allocate-fefo/', {
            'product_id': product.id,
            'warehouse_id': main_warehouse.id,
            'qty': '500',  # موجودی فقط ۱۰۰
        }, format='json')
        assert response.status_code == 400
        data = response.json()
        assert data['allocated'] is False

    def test_near_expiry_lots(self, authenticated_client, lot_with_stock):
        """لیست لات‌های نزدیک به انقضا"""
        response = authenticated_client.get('/api/inventory/lots/near_expiry/?days=20')
        assert response.status_code == 200


@pytest.mark.django_db
@pytest.mark.integration
class TestSalesAPI:
    """تست API فروش"""

    def test_create_sale_endpoint(self, distributor_client, store, product, main_warehouse, db,
                                    seed_accounts):
        """تست endpoint ساخت فروش با حساب‌های حسابداری seed شده"""
        from datetime import timedelta
        from django.utils import timezone
        from apps.inventory.models import InventoryLot
        today = timezone.now().date()
        InventoryLot.objects.create(
            product=product, warehouse=main_warehouse,
            batch_no='B-API', production_date=today,
            expiry_date=today + timedelta(days=15),
            initial_qty=100, current_qty=100, weighted_avg_cost=25000,
        )

        response = distributor_client.post('/api/sales/create/', {
            'store_id': store.id,
            'sales_type': 'consignment',
            'lines': [
                {'product_id': product.id, 'qty': '20', 'unit_price': '50000.0000'},
            ],
        }, format='json')
        assert response.status_code == 201
        data = response.json()
        assert data['status'] == 'posted'
        assert data['total_amount'] == '1000000.0000'

    def test_daily_report(self, authenticated_client):
        """گزارش فروش روزانه"""
        response = authenticated_client.get('/api/sales/daily_report/')
        assert response.status_code == 200
        data = response.json()
        assert 'total_amount' in data


@pytest.mark.django_db
@pytest.mark.integration
class TestStoreAPI:
    """تست API فروشگاه‌ها"""

    def test_geo_points(self, authenticated_client, store):
        """نقشه جغرافیایی"""
        store.geo_lat = '35.7219000'
        store.geo_lng = '51.3347000'
        store.save()

        response = authenticated_client.get('/api/partners/stores/geo_points/')
        assert response.status_code == 200
        data = response.json()
        assert 'results' in data

    def test_store_balance(self, authenticated_client, store):
        """مانده حساب فروشگاه"""
        response = authenticated_client.get(f'/api/partners/stores/{store.id}/balance/')
        assert response.status_code == 200
        data = response.json()
        assert 'available_credit' in data
