"""
Load Tests with Locust — تست بار سیستم
"""
from locust import HttpUser, task, between
import random


class WorkshopUser(HttpUser):
    """شبیه‌سازی کاربر سیستم"""

    wait_time = between(1, 3)  # ۱ تا ۳ ثانیه بین درخواست‌ها
    token = None

    def on_start(self):
        """ورود به سیستم و دریافت توکن"""
        response = self.client.post('/api/auth/login/', json={
            'username': 'admin',
            'password': 'admin123456',
        })
        if response.status_code == 200:
            data = response.json()
            self.token = data['access']
            self.client.headers = {
                'Authorization': f'JWT {self.token}',
                'Content-Type': 'application/json',
            }

    @task(5)
    def view_dashboard(self):
        """مشاهده داشبورد"""
        self.client.get('/api/sales/daily_report/')

    @task(3)
    def list_products(self):
        """لیست محصولات"""
        self.client.get('/api/products/')

    @task(2)
    def list_stores(self):
        """لیست فروشگاه‌ها"""
        self.client.get('/api/partners/stores/')

    @task(2)
    def view_inventory(self):
        """مشاهده انبار"""
        self.client.get('/api/inventory/lots/')

    @task(1)
    def create_sale(self):
        """ثبت فروش (فشار)"""
        self.client.post('/api/sales/create/', json={
            'store_id': random.randint(1, 10),
            'sales_type': 'consignment',
            'lines': [
                {'product_id': random.randint(1, 30), 'qty': 5, 'unit_price': 50000},
            ],
        })

    @task(1)
    def fefo_allocate(self):
        """تخصیص FEFO"""
        self.client.post('/api/inventory/allocate-fefo/', json={
            'product_id': random.randint(1, 30),
            'warehouse_id': 1,
            'qty': 10,
        })


class DistributorMobileUser(HttpUser):
    """شبیه‌سازی کاربر موبایل عامل پخش"""

    wait_time = between(2, 5)

    def on_start(self):
        response = self.client.post('/api/auth/login/', json={
            'username': 'distributor1',
            'password': 'distributor123',
        })
        if response.status_code == 200:
            self.token = response.json()['access']
            self.client.headers = {
                'Authorization': f'JWT {self.token}',
            }

    @task(10)
    def view_route(self):
        """مشاهده سبد پخش امروز"""
        self.client.get('/api/mobile/snapshot/')

    @task(5)
    def list_drafts(self):
        """لیست پیش‌نویس‌ها"""
        self.client.get('/api/mobile/drafts/')

    @task(2)
    def create_draft(self):
        """ثبت پیش‌نویس"""
        self.client.post('/api/mobile/drafts/', json={
            'store_id': 1,
            'sales_type': 'consignment',
            'lines': [
                {'product_id': 1, 'qty': 10, 'unit_price': 50000},
            ],
        })

    @task(1)
    def scan_barcode(self):
        """اسکن بارکد"""
        self.client.post('/api/products/barcodes/scan/', json={
            'barcode_value': '6420000010017',
            'context': 'sale_draft',
        })


# استفاده:
# locust -f locustfile.py --host=http://localhost:8000
# سپس به http://localhost:8089 برو
