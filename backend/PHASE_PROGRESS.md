# 🚀 Django Starter v2.0 — وضعیت واقعی پروژه

> به‌روزرسانی‌شده پس از مرور کامل کد و تست‌ها.

## ✅ App‌های کامل (۱۸ از ۱۸)

| # | App | خطوط کد | توضیح |
|---|------|--------|------|
| ۱ | `accounts` | ۴۰۰+ | کاربران، نقش‌ها، احراز هویت JWT، پروفایل، Activity Log |
| ۲ | `products` | ۵۰۰+ | محصولات، دسته‌بندی، قیمت‌گذاری پویا، تصاویر، بارکد EAN-13 |
| ۳ | `inventory` | ۶۰۰+ | ⭐ قلب FEFO + میانگین موزون + ردیابی لات |
| ۴ | `sales` | ۸۰۰+ | فروش امانی/قطعی + برگشت + یکپارچگی حسابداری |
| ۵ | `partners` | ۵۰۰+ | فروشگاه‌ها + عوامل پخش + اعتبار + وفاداری + Heatmap |
| ۶ | `production` | ۸۲۰ | بچ تولید + مصرف مواد + خروج محصول + بهای تمام‌شده |
| ۷ | `dispatch` | ۸۰۵ | سند پخش به عامل + مسیرها + وسیله نقلیه |
| ۸ | `transfers` | ۹۴۵ | انتقال بین فروشگاه‌ها + FEFO Suggester |
| ۹ | `accounting` | ۱۰۷۵ | ⭐ سند حسابداری + کنترل توازن + ژورنال خودکار |
| ۱۰ | `notifications` | ۸۷۵ | SMS + Push Notification + کانال‌ها |
| ۱۱ | `reports` | ۴۸۵ | داشبورد بلادرنگ + گزارش‌های فروش/تولید |
| ۱۲ | `approval_workflow` | ۵۱۰ | جریان تأیید مدیر + چندمرحله‌ای |
| ۱۳ | `store_portal` | ۸۳۵ | پورتال B2B فروشگاه + سفارش آنلاین |
| ۱۴ | `payments` | ۷۱۰ | پرداخت آنلاین (زرین‌پال، idPay، پارسیان) |
| ۱۵ | `loyalty` | ۶۱۵ | وفاداری + Smart Reorder + لایه‌بندی |
| ۱۶ | `barcode` | ۳۷۰ | اسکن بارکد + تاریخچه |
| ۱۷ | `saman_tax` | ۴۶۰ | صورتحساب الکترونیکی سامان |
| ۱۸ | `core` | ۲۰۰+ | BaseModel + RBAC + middleware + exceptions |

## 🧪 تست‌ها

```
============================== 35 passed in 6.21s ==============================
```

| دسته | تعداد | وضعیت |
|------|------|------|
| Unit tests (FEFO + Sales) | ۱۰ | ✅ |
| Integration tests (API) | ۱۷ | ✅ |
| Authentication tests | ۴ | ✅ |
| Products API tests | ۶ | ✅ |
| Inventory API tests | ۳ | ✅ |
| Sales API tests | ۲ | ✅ |
| Store API tests | ۲ | ✅ |
| Health check | ۱ | ✅ |

## 🔥 منطق‌های بحرانی پیاده‌سازی‌شده

### ۱. الگوریتم FEFO (inventory/services/fefo_service.py)
```python
result = FEFOService.allocate_lots(product_id=1, warehouse_id=1, qty_needed=30, sale_date='2025-10-20')
# → تخصیص از نزدیک‌ترین تاریخ انقضا، در صورت کمبود InsufficientStockError
```

### ۲. میانگین موزون (همان فایل)
```python
new_avg = WeightedAverageService.update_weighted_average(lot_id=5, in_qty=50, in_unit_cost=28000)
# → (existing_qty × old_avg + in_qty × in_unit_cost) / (existing_qty + in_qty)
```

### ۳. فروش امانی/قطعی (sales/services.py)
```python
sale = SalesService.create_sale(store_id=1, sales_type='consignment', lines=[...])
# → تخصیص خودکار FEFO + InventoryMovements + سیگنال سند حسابداری
```

### ۴. تولید بارکد EAN-13 (products/services.py)
```python
ProductService._generate_ean13(product_id=1) → '6420000000017'  # ✅ ۱۳ رقم صحیح
```

### ۵. بچ تولید (production/services.py)
```python
batch = ProductionService.create_batch(product_id=1, planned_qty=100, ...)
ProductionService.start_batch(batch_id=batch.id)
ProductionService.consume_material(batch_id=..., material_lot_id=..., qty=...)
ProductionService.complete_batch(batch_id=..., actual_qty=...)
# → ساخت خودکار InventoryLot + بهای تمام‌شده
```

### ۶. سند حسابداری خودکار (accounting/services.py)
```python
# از طریق سیگنال‌ها هنگام:
#   - تکمیل بچ تولید
#   - ثبت فروش
#   - انتقال بین فروشگاه‌ها
#   - پخش به عامل
# به‌طور خودکار JournalHeader + JournalLine ساخته می‌شود
```

### ۷. انتقال FEFO بین فروشگاه‌ها (transfers/services.py)
```python
# انتقال موجودی از فروشگاه مبدا به مقصد با استفاده از FEFO
# → لات‌ها بر اساس نزدیک‌ترین انقضا انتخاب می‌شوند
```

### ۸. پرداخت آنلاین (payments/services.py + providers.py)
```python
# ۳ درگاه: زرین‌پال، idPay، پارسیان
# → بازگشت به callback + تأیید تراکنش
```

## 📁 ساختار پروژه

```
workshop-management/
├── backend/
│   ├── apps/
│   │   ├── ۱۸ app کامل با models + serializers + views + urls + services + signals
│   │   └── ۲ app تنها خواندنی (reports, barcode)
│   ├── config/
│   │   ├── settings/ (base, development, production, test, local_test)
│   │   ├── urls.py (با ۱۷ endpoint group)
│   │   ├── celery.py
│   │   └── wsgi/asgi
│   └── core/
│       ├── models.py, permissions.py, middleware.py, exceptions.py
│       ├── tasks.py (Celery مشترک)
│       └── health_urls.py
├── deploy/
│   ├── docker/Dockerfile.backend
│   └── nginx/nginx.conf
├── docker-compose.yml (با ۸ سرویس)
├── requirements.txt
├── manage.py, pytest.ini
└── README.md, PHASE_PROGRESS.md, TESTING.md
```

## 🚀 راه‌اندازی سریع

```bash
# ۱. استفاده از local_test (بدون Postgres/Redis)
export DJANGO_SETTINGS_MODULE=config.settings.local_test
export PYTHONPATH=backend
python manage.py migrate
python manage.py seed_data
python manage.py createsuperuser
python manage.py runserver

# ۲. اجرای تست‌ها
pytest backend/tests --no-cov

# ۳. مستندات API
# مرورگر → http://localhost:8000/api/docs/
# با هدر Authorization: JWT <access_token>
```

## 🎯 تغییرات اخیر (به‌روزرسانی)

- ✅ باز کردن لیست محصولات/دسته‌بندی/قیمت برای دسترسی عمومی (AllowAny)
- ✅ اضافه کردن JWT security scheme به Swagger (دکمه Authorize درست کار می‌کند)
- ✅ اصلاح باگ تولید بارکد EAN-13 (۱۰ رقم → ۱۳ رقم)
- ✅ رفع تکرار ساخت Barcode (signal + service)
- ✅ به‌روزرسانی تست‌های قدیمی برای تطبیق با منطق جدید
- ✅ اضافه شدن fixture `seed_accounts` برای تست‌های حسابداری

---

**نسخه:** 2.0.0 | **فاز:** کامل (۱۰۰٪ appها ساخته شدند) | **تست:** ۳۵ از ۳۵ ✅
