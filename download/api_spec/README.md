# Workshop Management API Specification v2.0

> OpenAPI 3.0 Specification — تمام endpointهای REST API

## 📦 محتویات

```
api_spec/
├── openapi.yaml          # OpenAPI 3.0 specification
├── README.md            # این فایل
├── postman_collection.json  # Collection برای Postman (به‌زودی)
└── examples/             # نمونه‌های Request/Response
```

## 🚀 استفاده

### مشاهده مستندات

#### روش ۱: Swagger UI
```bash
# ۱. پروژه Django رو اجرا کن
python manage.py runserver

# ۲. مرورگر را باز کن
# http://localhost:8000/api/docs/
```

#### روش ۲: ReDoc
```bash
# http://localhost:8000/api/redoc/
```

#### روش ۳: استاتیک (با Swagger Editor)
1. به https://editor.swagger.io برو
2. فایل `openapi.yaml` را در آن بارگذاری کن

#### روش ۴: با Redoc CLI
```bash
npm install -g @redocly/cli
redocly build-docs openapi.yaml -o api-docs.html
```

### تولید کلاینت‌ها

از OpenAPI spec می‌توان کلاینت‌های زیر را تولید کرد:

```bash
# نصب openapi-generator
npm install -g @openapitools/openapi-generator-cli

# تولید کلاینت TypeScript برای Next.js Frontend
openapi-generator-cli generate \
    -i openapi.yaml \
    -g typescript-axios \
    -o ./frontend-client \
    --additional-properties=supportsES6=true,withSeparateModelsAndApi=true

# تولید کلاینت JavaScript برای React Native (Mobile)
openapi-generator-cli generate \
    -i openapi.yaml \
    -g javascript \
    -o ./mobile-client

# تولید کلاینت Python برای اسکریپت‌های داخلی
openapi-generator-cli generate \
    -i openapi.yaml \
    -g python \
    -o ./python-client

# تولید کلاینت C# برای دسکتاپ (در صورت نیاز)
openapi-generator-cli generate \
    -i openapi.yaml \
    -g csharp \
    -o ./csharp-client
```

## 📊 خلاصه Endpointها

| گروه | تعداد Endpoint | نقش اصلی |
|------|-------------|----------|
| `auth` | 6 | همه |
| `products` | 4 | مدیر، انباردار |
| `inventory` | 3 (شامل FEFO) | انباردار، حسابدار |
| `production` | 3 | انباردار |
| `dispatch` | 4 | مدیر، عامل |
| `sales` | 5 (شامل برگشت) | مدیر، حسابدار |
| `transfers` | 4 (شامل suggestions) | مدیر |
| `partners` | 4 | مدیر |
| `accounting` | 5 (شامل تراز، سود و زیان) | حسابدار |
| `approval` | 2 | مدیر |
| `store-portal` | 6 | فروشگاه |
| `payments` | 5 | فروشگاه، حسابدار |
| `notifications` | 3 | همه |
| `loyalty` | 2 | مدیر |
| `barcode` | 2 | عامل |
| `tax` | 2 | حسابدار |
| `mobile` | 4 (شامل sync) | عامل |
| `reports` | 4 (شامل Heatmap) | مدیر |
| **Total** | **~68** | — |

## 🔐 احراز هویت

### دریافت Token

```http
POST /api/auth/login/
Content-Type: application/json

{
  "username": "admin",
  "password": "secret123"
}
```

### پاسخ

```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### استفاده در درخواست‌ها

```http
GET /api/products/
Authorization: JWT eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### تمدید Token

```http
POST /api/auth/refresh/
Content-Type: application/json

{
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

## 🎯 نمونه‌های کلیدی

### ۱. ثبت پیش‌نویس فروش توسط عامل (موبایل آفلاین)

```http
POST /api/mobile/drafts/
Content-Type: application/json
Authorization: JWT ...

{
  "store_id": 5,
  "sales_type": "consignment",
  "device_id": "device-uuid-abc123",
  "lines": [
    {
      "product_id": 1,
      "qty": 30,
      "unit_price": 50000,
      "barcode_scanned": "6421000000017"
    },
    {
      "product_id": 5,
      "qty": 20,
      "unit_price": 70000,
      "barcode_scanned": "6421000000055"
    }
  ]
}
```

### ۲. تخصیص FEFO (مهم‌ترین الگوریتم)

```http
POST /api/inventory/allocate-fefo/
Content-Type: application/json

{
  "product_id": 1,
  "warehouse_id": 5,
  "qty": 30,
  "sale_date": "2025-10-20"
}
```

### پاسخ

```json
{
  "allocated": true,
  "total_allocated_qty": 30,
  "allocations": [
    {
      "lot_id": 15,
      "qty": 20,
      "unit_cost": 25000,
      "expiry_date": "2025-10-25",
      "days_to_expiry": 5
    },
    {
      "lot_id": 22,
      "qty": 10,
      "unit_cost": 26800,
      "expiry_date": "2025-11-01",
      "days_to_expiry": 12
    }
  ],
  "warning": "Lot 15 expires in 5 days. Consider transfer."
}
```

### ۳. تأیید/رد سند توسط مدیر

```http
POST /api/approval/45/decide/
Content-Type: application/json
Authorization: JWT ...

{
  "decision": "approved",
  "reason": "تأیید شد",
  "notes": "حواله شماره ۱۲۳۴ صادر شد"
}
```

### ۴. ثبت سفارش توسط فروشگاه

```http
POST /api/store-portal/orders/
Content-Type: application/json
Authorization: JWT ...

{
  "lines": [
    {"product_id": 1, "qty": 50},
    {"product_id": 5, "qty": 30}
  ],
  "notes": "تحویل فردا قبل از ظهر"
}
```

### ۵. شروع پرداخت آنلاین

```http
POST /api/payments/initiate/
Content-Type: application/json

{
  "amount": 500000,
  "related_doc_type": "store_order",
  "related_doc_id": 12,
  "gateway": "zarinpal"
}
```

### ۶. Smart Reorder پیشنهادی

```http
GET /api/store-portal/smart-reorder/
Authorization: JWT ...
```

### پاسخ

```json
{
  "suggestions": [
    {
      "product_id": 1,
      "suggested_qty": 70,
      "current_stock": 8,
      "days_of_stock": 0.5,
      "confidence": 0.85
    }
  ]
}
```

## 🧪 تست با Postman

1. Postman را باز کن
2. Import → File → `openapi.yaml` را انتخاب کن
3. Postman به‌طور خودکار تمام endpointها را با schemaها وارد می‌کند
4. در Environment Variables این متغیرها را تنظیم کن:
   - `BASE_URL`: `http://localhost:8000/api`
   - `JWT_TOKEN`: (بعد از login پر می‌شود)

## 🔄 چرخه کامل فروش (سفارش → تأیید → تحویل → پرداخت)

```
1. فروشگاه:   POST /store-portal/orders/
2. مدیر:      GET  /approval/queue/
3. مدیر:      POST /approval/{id}/decide/
4. عامل:      GET  /mobile/snapshot/
5. عامل:      POST /mobile/drafts/ (تحویل کالا)
6. فروشگاه:   POST /store-portal/orders/{id}/receive/
7. فروشگاه:   POST /payments/initiate/
8. درگاه:     POST /payments/callback/zarinpal/ (Callback)
9. سیستم:     POST /tax/invoices/ (خودکار)
10. سیستم:    تولید سند حسابداری خودکار (Django Signal)
```

## 🎯 خطاهای رایج

| HTTP Status | دلیل |
|------|------|
| 400 | اعتبارسنجی ناموفق (مشاهده `field_errors`) |
| 401 | Token JWT نامعتبر یا منقضی |
| 403 | کاربر نقش مناسب ندارد |
| 404 | منبع یافت نشد |
| 409 | تعارض (مثلاً موجودی کافی نیست هنگام sync موبایل) |
| 429 | Rate Limit تجاوز شده (۱۲۰ درخواست/دقیقه) |
| 500 | خطای سرور داخلی |
| 502 | خطای درگاه پرداخت یا سامان |

## 📋 Connection

برای تست‌های تولید:
- **Base URL:** `https://api.workshop.local/api`
- **Health Check:** `https://api.workshop.local/api/health/`
- **Swagger UI:** `https://api.workshop.local/api/docs/`

## 🔗 ارتباط با سایر Artifactها

| Artifact | مسیر |
|---------|------|
| سند معماری PDF | `../bakery_erd_doc_v2.pdf` |
| SQL Migrations | `../sql_migrations/` |
| Django Starter | `../django_starter/` |

---

**نسخه:** 2.0.0 | **تاریخ:** 1404 | **OpenAPI Version:** 3.0.3
