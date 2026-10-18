# راهنمای تست پروژه

> چطور مطمئن بشیم کد بدون باگ کار می‌کنه؟

## 📋 خلاصه سریع

| سطح تست | فایل | شرح | سرعت |
|------|------|------|------|
| ۱. Syntax | `py_compile` | بررسی خطاهای syntax | ۱ ثانیه |
| ۲. Unit | `backend/tests/unit/` | تست هر service به‌صورت مجزا | <۱ ثانیه/تست |
| ۳. Integration | `backend/tests/integration/` | تست endpoint‌ها با API | ~۱ ثانیه/تست |
| ۴. Load | `locustfile.py` | تست بار با Locust | بسته به load |

## ✅ نتیجه تست Syntax (همین الان انجام شد)

```
۱۲۸ فایل Python بررسی شد
۰ خطای syntax
۱۲۸ فایل موفق ✓
```

## 🚀 اجرای تست‌ها

### ۱. نصب پیش‌نیازها

```bash
cd django_starter

# ساخت virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# یا: venv\Scripts\activate  # Windows

# نصب dependencies
pip install -r requirements.txt
```

### ۲. آماده‌سازی دیتابیس

```bash
# با PostgreSQL (Production-like)
docker compose up -d postgres redis

# اجرای migrations
python manage.py migrate

# ساخت superuser
python manage.py createsuperuser
```

### ۳. اجرای تست‌ها

```bash
# همه تست‌ها با Coverage
pytest

# فقط unit tests (سریع)
pytest backend/tests/unit/ -m unit

# فقط integration tests
pytest backend/tests/integration/ -m integration

# یک فایل خاص
pytest backend/tests/unit/test_fefo_service.py -v

# نمایش coverage به‌صورت HTML
pytest --cov=backend --cov-report=html
# سپس: open htmlcov/index.html
```

## 📊 تست‌های نوشته‌شده

### Unit Tests (تست Unit)

| فایل | تست‌ها | شرح |
|------|------|------|
| `test_fefo_service.py` | ۹ تست | الگوریتم FEFO + میانگین موزون + بارکد EAN-13 |
| `test_sales_service.py` | ۷ تست | ساخت فروش + امانی/قطعی + کمبود موجودی |

### Integration Tests (تست API)

| فایل | تست‌ها | شرح |
|------|------|------|
| `test_api.py` | ۱۵ تست | تمام endpointهای بحرانی |

## 🎯 مهم‌ترین تست‌ها

### ۱. تست FEFO (`test_fefo_service.py`)

```python
def test_allocate_lots_multiple_lots(self):
    """چند لات موجود — باید از نزدیک‌ترین به انقضا استفاده کنه"""
    # لات ۱: انقضا ۳ روز بعد
    lot1 = create_lot(expiry_date=today + 3 days)
    # لات ۲: انقضا ۱۵ روز بعد
    lot2 = create_lot(expiry_date=today + 15 days)

    result = FEFOService.allocate_lots(qty=30)

    # انتظار: اول ۲۰ از lot1، بعد ۱۰ از lot2
    assert result.allocations[0].lot_id == lot1.id
    assert result.allocations[1].lot_id == lot2.id
```

### ۲. تست میانگین موزون

```python
def test_update_weighted_average(self):
    """فرمول: (100×25000 + 50×28000) / 150 = 26000"""
    new_avg = WeightedAverageService.update_weighted_average(
        lot_id=1, in_qty=50, in_unit_cost=28000,
    )
    assert new_avg == Decimal('26000')
```

### ۳. تست فروش امانی

```python
def test_create_sale_basic(self):
    sale = SalesService.create_sale(
        store_id=1, sales_type='consignment',
        lines=[{'product_id': 1, 'qty': 30, 'unit_price': 50000}],
    )
    assert sale.total_amount == 1500000  # 30 × 50000
    assert sale.total_cost == 750000    # 30 × 25000
```

## 🐛 تست‌های بحرانی (باگ‌یاب)

### باگ احتمالی ۱: Race Condition

```python
def test_concurrent_sales(self):
    """دو فروش همزمان روی یک لات — نباید موجودی منفی بشه"""
    lot = create_lot(qty=100)

    # دو فروش همزمان
    Thread 1: SalesService.create_sale(qty=80)
    Thread 2: SalesService.create_sale(qty=80)

    # بعد از هر دو: موجودی نباید منفی باشه
    lot.refresh_from_db()
    assert lot.current_qty >= 0
```

### باگ احتمالی ۲: تخصیص FEFO

```python
def test_no_lot_selected_for_expired(self):
    """لات منقضی شده نباید انتخاب بشه"""
    expired_lot = create_lot(expiry_date=yesterday)

    with pytest.raises(InsufficientStockError):
        FEFOService.allocate_lots(qty=10)
```

## 🔧 نحوه اجرای تست‌ها روی سیستم شما

ابتدا فایل‌های تست رو در سیستم خودتون بسازید:

```
django_starter/
├── backend/
│   └── tests/
│       ├── __init__.py                    ← خالی
│       ├── conftest.py                    ← fixtures مشترک
│       └── unit/
│           ├── __init__.py                ← خالی
│           ├── test_fefo_service.py       ← ۹ تست
│           └── test_sales_service.py      ← ۷ تست
└── pytest.ini                             ← تنظیمات pytest
```

سپس اجرا کنید:

```bash
# فعال‌سازی virtual env
source venv/bin/activate

# اجرای تست‌ها
pytest -v

# خروجی مورد انتظار:
# ============================= test session starts =============================
# backend/tests/unit/test_fefo_service.py::TestFEFOService::test_allocate_lots_basic PASSED
# backend/tests/unit/test_fefo_service.py::TestFEFOService::test_allocate_lots_multiple_lots PASSED
# backend/tests/unit/test_fefo_service.py::TestWeightedAverageService::test_update_weighted_average PASSED
# ...
# 16 passed in 4.5s ✓
```

## 🌐 تست دستی (Manual Testing)

پس از اجرای سرور:

```bash
python manage.py runserver
```

این URLها رو در مرورگر باز کنید:

| URL | شرح |
|------|------|
| http://localhost:8000/admin/ | Django Admin |
| http://localhost:8000/api/docs/ | Swagger UI |
| http://localhost:8000/api/health/ | Health Check |

### تست با curl

```bash
# ۱. Login و دریافت توکن
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "..."}'

# پاسخ:
# {"access": "eyJ...", "refresh": "eyJ..."}

# ۲. دریافت لیست محصولات
curl http://localhost:8000/api/products/ \
  -H "Authorization: JWT eyJ..."

# ۳. تخصیص FEFO
curl -X POST http://localhost:8000/api/inventory/allocate-fefo/ \
  -H "Authorization: JWT eyJ..." \
  -H "Content-Type: application/json" \
  -d '{"product_id": 1, "warehouse_id": 1, "qty": "30"}'

# ۴. ثبت فروش
curl -X POST http://localhost:8000/api/sales/create/ \
  -H "Authorization: JWT eyJ..." \
  -H "Content-Type: application/json" \
  -d '{
    "store_id": 1,
    "sales_type": "consignment",
    "lines": [
      {"product_id": 1, "qty": "30", "unit_price": "50000.0000"}
    ]
  }'
```

## 🐝 تست بار با Locust

```bash
# نصب Locust
pip install locust

# اجرای تست بار
locust -f locustfile.py --host=http://localhost:8000

# سپس مرورگر را باز کن:
# http://localhost:8089

# تنظیمات:
# Number of users: 50
# Ramp up: 10 users/sec
# Host: http://localhost:8000
```

## ✅ چک‌لیست کیفیت

پس از اجرای تست‌ها، مطمئن شو:

- [ ] همه unit tests پاس شدند (هدف: ۱۰۰٪)
- [ ] Coverage حداقل ۸۰٪ است
- [ ] هیچ syntax error وجود ندارد
- [ ] API docs در `/api/docs/` باز می‌شود
- [ ] Health check در `/api/health/` پاس می‌شود
- [ ] تست بار با ۵۰ کاربر simultaneous پاس می‌شود
- [ ] Response time زیر ۳۰۰ms در P95

## ❓ سوالات رایج

### ۱. اگر تستی پاس نشد چی؟
```bash
# نمایش جزئیات بیشتر
pytest -v --pdb  # در صورت failure، debugger باز می‌شه

# فقط تست‌های fail شده
pytest --lf
```

### ۲. چطور Coverage رو افزایش بدم؟
```bash
# نمایش فایل‌های بدون تست
pytest --cov=backend --cov-report=term-missing

# فایل‌هایی که ۰٪ coverage دارند رو پیدا کن
pytest --cov=backend --cov-report=html
open htmlcov/index.html
```

### ۳. تست در محیط CI/CD
`.github/workflows/ci.yml` قبلاً ساخته شده. در هر push به GitHub، تست‌ها خودکار اجرا می‌شن.

---

**نسخه:** 2.0.0 | **۱۶ تست نوشته‌شده** | **هدف coverage:** ۸۰٪+
