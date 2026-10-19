# 🚀 Django Starter v2.0 — اپ‌های بحرانی توسعه‌یافته

## ✅ App‌های توسعه‌یافته (۵ از ۱۷)

| # | App | وضعیت | توضیح |
|---|------|------|------|
| ۱ | `accounts` | ✅ کامل | کاربران، نقش‌ها، احراز هویت JWT، پروفایل، Activity Log |
| ۲ | `products` | ✅ کامل | محصولات، دسته‌بندی، قیمت‌گذاری پویا، تصاویر، بارکد EAN-13 |
| ۳ | `inventory` | ✅ کامل | ⭐ قلب FEFO + میانگین موزون + ردیابی لات |
| ۴ | `sales` | ✅ کامل | فروش امانی/قطعی + برگشت + یکپارچگی حسابداری |
| ۵ | `partners` | ✅ کامل | فروشگاه‌ها + عوامل پخش + اعتبار + وفاداری + Heatmap |

## 📋 App‌های باقی‌مونده (۱۲ از ۱۷)

| # | App | فاز توسعه | شرح |
|---|------|--------|------|
| ۶ | `dispatch` | فاز ۳ | سند پخش به عامل + مسیرها |
| ۷ | `transfers` | فاز ۳ | انتقال بین فروشگاه‌ها + FEFO Suggester |
| ۸ | `production` | فاز ۲ | بچ تولید + مصرف مواد |
| ۹ | `accounting` | فاز ۴ | سند حسابداری + کنترل توازن |
| ۱۰ | `notifications` | فاز ۵ | SMS + Push Notification |
| ۱۱ | `reports` | فاز ۴ | داشبورد بلادرنگ |
| ۱۲ | `approval_workflow` | فاز ۵ | جریان تأیید مدیر |
| ۱۳ | `store_portal` | فاز ۶ | پورتال B2B فروشگاه |
| ۱۴ | `payments` | فاز ۶ | پرداخت آنلاین ۳ درگاه |
| ۱۵ | `loyalty` | فاز ۷ | وفاداری + Smart Reorder |
| ۱۶ | `barcode` | فاز ۷ | اسکن بارکد |
| ۱۷ | `saman_tax` | فاز ۶ | صورتحساب الکترونیکی |

---

## 🔥 منطق‌های بحرانی پیاده‌سازی‌شده

### ۱. الگوریتم FEFO (فایل `inventory/services/fefo_service.py`)

```python
from apps.inventory.services.fefo_service import FEFOService

# تخصیص لات برای ۳۰ عدد محصول ۱ از انبار ۱
result = FEFOService.allocate_lots(
    product_id=1,
    warehouse_id=1,
    qty_needed=30,
    sale_date='2025-10-20',
)
# → از لات‌های با نزدیک‌ترین تاریخ انقضا استفاده می‌کند
# → در صورت کمبود، InsufficientStockError پرتاب می‌شود
# → اگر انقضا نزدیک باشد، warning می‌دهد
```

### ۲. میانگین موزون (همان فایل)

```python
from apps.inventory.services.fefo_service import WeightedAverageService

# پس از ورود کالا، میانگین موزون به‌روزرسانی می‌شود
new_avg = WeightedAverageService.update_weighted_average(
    lot_id=5,
    in_qty=Decimal('50'),
    in_unit_cost=Decimal('28000'),
)
# → فرمول: (existing_qty × old_avg + in_qty × in_unit_cost) / (existing_qty + in_qty)
```

### ۳. فروش امانی/قطعی (فایل `sales/services.py`)

```python
from apps.sales.services import SalesService

sale = SalesService.create_sale(
    store_id=1,
    sales_type='consignment',  # یا 'firm'
    lines=[
        {'product_id': 1, 'qty': 30, 'unit_price': 50000},
        {'product_id': 5, 'qty': 20, 'unit_price': 70000},
    ],
    created_by=request.user,
)
# → تخصیص خودکار FEFO
# → ثبت InventoryMovements
# → ارسال سیگنال برای سند حسابداری خودکار
# → برای فروش قطعی: ارسال صورتحساب سامان (در فاز ۶)
```

### ۴. تولید بارکد EAN-13 (فایل `products/services.py`)

```python
from apps.products.services import ProductService

product = ProductService.create_product(
    code='P001',
    name='محصول نمونه A1',
    category_id=1,
    unit='عدد',
    shelf_life_days=15,
    default_price=50000,
    created_by=request.user,
)
# → بارکد EAN-13 خودکار تولید می‌شود: 6420000010017
# → ۴ قیمت‌گذاری پیش‌فرض (برای هر لایه فروشگاه)
# → Barcode رکورد در جدول barcodes ساخته می‌شود
```

### ۵. گزارش جغرافیایی Heatmap

```http
GET /api/partners/stores/geo_points/
# → مختصات همه فروشگاه‌ها + شدت فروش ۳۰ روز اخیر
# → شدت: very_high / high / medium / low
```

---

## 🧪 تست‌های پیشنهادی

پس از راه‌اندازی پروژه، این تست‌ها رو اجرا کنید:

```bash
# ۱. ساخت superuser
python manage.py createsuperuser

# ۲. اجرای سرور
python manage.py runserver

# ۳. در مرورگر: http://localhost:8000/api/docs/
#    Swagger UI برای تست API‌ها

# ۴. تست FEFO
curl -X POST http://localhost:8000/api/inventory/allocate-fefo/ \
  -H "Authorization: JWT ..." \
  -H "Content-Type: application/json" \
  -d '{"product_id": 1, "warehouse_id": 1, "qty": 30, "sale_date": "2025-10-20"}'

# ۵. تست بارکدخوان
curl -X POST http://localhost:8000/api/products/barcodes/scan/ \
  -H "Authorization: JWT ..." \
  -H "Content-Type: application/json" \
  -d '{"barcode_value": "6420000010017", "store_id": 1}'

# ۶. تست فروش
curl -X POST http://localhost:8000/api/sales/create/ \
  -H "Authorization: JWT ..." \
  -H "Content-Type: application/json" \
  -d '{
    "store_id": 1,
    "sales_type": "consignment",
    "lines": [
      {"product_id": 1, "qty": 30, "unit_price": 50000},
      {"product_id": 5, "qty": 20, "unit_price": 70000}
    ]
  }'
```

---

## 📁 ساختار فعلی

```
workshop-management/
├── backend/
│   ├── apps/
│   │   ├── accounts/        ✅ کامل (models, serializers, views, urls, admin, signals)
│   │   ├── products/        ✅ کامل (با EAN-13 generator)
│   │   ├── inventory/       ✅ کامل (با FEFO Service + میانگین موزون)
│   │   ├── sales/           ✅ کامل (با امانی/قطعی)
│   │   ├── partners/        ✅ کامل (با Heatmap Geo points)
│   │   └── ۱۲ app skeleton (در فازهای بعد)
│   ├── config/
│   │   ├── settings/        ✅
│   │   ├── urls.py          ✅
│   │   ├── celery.py        ✅
│   │   ├── wsgi.py          ✅
│   │   └── asgi.py          ✅
│   └── core/
│       ├── models.py        ✅ BaseModel با Soft Delete
│       ├── permissions.py   ✅ RBAC (۵ نقش)
│       ├── middleware.py    ✅ Activity Log
│       ├── exceptions.py    ✅ Custom exceptions
│       ├── tasks.py         ✅ Celery tasks مشترک
│       └── health_urls.py   ✅ Health check
├── deploy/                  ✅ Docker + Nginx
├── docker-compose.yml       ✅
├── requirements.txt         ✅
├── manage.py                ✅
└── README.md                ✅
```

---

## 🎯 گام بعدی

برای ادامه توسعه فاز ۲، App‌های زیر رو توسعه بدید به این ترتیب:

1. **`production`** — برای ثبت بچ تولید + ساخت لات جدید
2. **`dispatch`** — سند پخش به عامل
3. **`accounting`** — قلب یکپارچگی انبار-حسابداری (نرخ به روش‌های میانگین موزون، FEFO، امانی/قطعی)
4. **`transfers`** — انتقال FEFO بین فروشگاه‌ها

هر App رو که بخواید، بگید تا کد کاملش رو بسازم.

---

**نسخه:** 2.0.0 | **فاز:** ۱-۳ (۳۸٪ کامل) | **تاریخ:** ۱۴۰۴
