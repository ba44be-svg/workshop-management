# گروه ۱: جداول پایه (۶ جدول)

> Products, ProductCategories, Stores, Distributors, Customers, Accounts

## ۱. `product_categories` — دسته‌بندی محصولات

دسته‌بندی درختی محصولات (مثلاً: کیک → کیک کرمی → کیک کرمی کوچک).

| فیلد | نوع | nullable | پیش‌فرض | توضیح |
|------|------|----------|---------|------|
| `id` | BIGSERIAL | NO | auto | کلید اصلی |
| `code` | VARCHAR(50) | NO | — | کد یکتا (مثلاً `CAT01`) |
| `name` | VARCHAR(200) | NO | — | نام دسته |
| `parent_id` | BIGINT | YES | NULL | ارجاع به والد (Self-Reference) |
| `level` | SMALLINT | NO | 1 | سطح درخت (۱-۵) |
| `is_active` | BOOLEAN | NO | TRUE | فعال/غیرفعال |
| `created_at` | TIMESTAMPTZ | NO | NOW() | زمان ساخت |
| `updated_at` | TIMESTAMPTZ | NO | NOW() | آخرین به‌روزرسانی |
| `created_by` | BIGINT | YES | NULL | کاربر سازنده (FK به users) |
| `deleted_at` | TIMESTAMPTZ | YES | NULL | Soft Delete timestamp |

**Constraint‌ها:**
- `UNIQUE(code)`
- `CHECK (level BETWEEN 1 AND 5)`

**ایندکس‌ها:**
- `idx_categories_parent` روی `parent_id` WHERE `deleted_at IS NULL`
- `idx_categories_code` روی `code`

---

## ۲. `products` — محصولات

جدول اصلی محصولات کارگاه.

| فیلد | نوع | nullable | پیش‌فرض | توضیح |
|------|------|----------|---------|------|
| `id` | BIGSERIAL | NO | auto | کلید اصلی |
| `code` | VARCHAR(50) | NO | — | کد یکتای محصول (مثلاً `P001`) |
| `name` | VARCHAR(200) | NO | — | نام محصول |
| `category_id` | BIGINT | NO | — | FK به product_categories |
| `unit` | VARCHAR(20) | NO | 'عدد' | واحد اندازه‌گیری |
| `shelf_life_days` | SMALLINT | NO | — | مدت ماندگاری به روز |
| `default_price` | NUMERIC(18,4) | NO | — | قیمت پایه (ریال) |
| `cost_center_id` | BIGINT | YES | NULL | FK به cost_centers |
| `barcode` | VARCHAR(50) | YES | NULL | بارکد EAN-13 یکتا |
| `description` | TEXT | YES | NULL | توضیحات |
| `is_active` | BOOLEAN | NO | TRUE | فعال/غیرفعال |

**Constraint‌ها:**
- `UNIQUE(code)`, `UNIQUE(barcode)`
- `CHECK (shelf_life_days > 0)`
- `CHECK (default_price >= 0)`

**ایندکس‌ها:**
- GIN index روی `name` برای جستجوی fuzzy (pg_trgm)
- B-tree روی `category_id`، `barcode`

---

## ۳. `stores` — فروشگاه‌ها

۲۰۰+ فروشگاه فیزیکی.

| فیلد | نوع | nullable | پیش‌فرض | توضیح |
|------|------|----------|---------|------|
| `id` | BIGSERIAL | NO | auto | کلید اصلی |
| `code` | VARCHAR(50) | NO | — | کد یکتا (مثلاً `S001`) |
| `name` | VARCHAR(200) | NO | — | نام |
| `address` | TEXT | YES | NULL | آدرس کامل |
| `phone` | VARCHAR(20) | YES | NULL | شماره تماس |
| `geo_lat` | NUMERIC(10,7) | YES | NULL | عرض جغرافیایی |
| `geo_lng` | NUMERIC(10,7) | YES | NULL | طول جغرافیایی |
| `distributor_id` | BIGINT | YES | NULL | FK به distributors |
| `sales_model` | sales_model_enum | NO | 'consignment' | امانی/قطعی/ترکیبی |
| `tier` | store_tier_enum | NO | 'regular' | لایه وفاداری |
| `credit_limit` | NUMERIC(18,4) | NO | 0 | سقف اعتبار (ریال) |
| `current_credit` | NUMERIC(18,4) | NO | 0 | اعتبار فعلی استفاده‌شده |
| `loyalty_points` | INTEGER | NO | 0 | امتیاز وفاداری |
| `is_active` | BOOLEAN | NO | TRUE | فعال/غیرفعال |

**Constraint‌ها:**
- `UNIQUE(code)`
- `CHECK (credit_limit >= 0)`

**ایندکس‌ها:**
- روی `distributor_id`، `tier`، `(geo_lat, geo_lng)` برای Heatmap

---

## ۴. `distributors` — عوامل پخش

| فیلد | نوع | nullable | پیش‌فرض | توضیح |
|------|------|----------|---------|------|
| `id` | BIGSERIAL | NO | auto | کلید اصلی |
| `code` | VARCHAR(50) | NO | — | کد یکتا |
| `name` | VARCHAR(200) | NO | — | نام عامل |
| `mobile` | VARCHAR(20) | NO | — | موبایل یکتا |
| `vehicle_id` | BIGINT | YES | NULL | FK به vehicles |
| `default_route_id` | BIGINT | YES | NULL | FK به routes |
| `commission_rate` | NUMERIC(5,2) | NO | 5.00 | درصد پورسانت |
| `is_active` | BOOLEAN | NO | TRUE | فعال/غیرفعال |

**Constraint‌ها:**
- `UNIQUE(code)`, `UNIQUE(mobile)`
- `CHECK (commission_rate BETWEEN 0 AND 50)`

---

## ۵. `customers` — مشتریان آنلاین

| فیلد | نوع | nullable | پیش‌فرض | توضیح |
|------|------|----------|---------|------|
| `id` | BIGSERIAL | NO | auto | کلید اصلی |
| `type` | VARCHAR(20) | NO | — | individual/business/platform |
| `name` | VARCHAR(200) | NO | — | نام |
| `phone` | VARCHAR(20) | YES | NULL | شماره تماس |
| `platform` | VARCHAR(50) | YES | NULL | instagram/snapp/website |
| `platform_user_id` | VARCHAR(200) | YES | NULL | شناسه روی پلتفرم |
| `credit_limit` | NUMERIC(18,4) | NO | 0 | سقف اعتبار |
| `is_active` | BOOLEAN | NO | TRUE | فعال/غیرفعال |

---

## ۶. `accounts` — کدینگ حساب‌ها

جدول درختی کدینگ حسابداری با ۵ نوع اصلی.

| فیلد | نوع | nullable | پیش‌فرض | توضیح |
|------|------|----------|---------|------|
| `id` | BIGSERIAL | NO | auto | کلید اصلی |
| `code` | VARCHAR(20) | NO | — | کد یکتا (مثلاً `1010`) |
| `name` | VARCHAR(200) | NO | — | نام حساب |
| `type` | account_type_enum | NO | — | asset/liability/equity/revenue/expense |
| `parent_id` | BIGINT | YES | NULL | ارجاع به والد (Self-Reference) |
| `is_active` | BOOLEAN | NO | TRUE | فعال/غیرفعال |
| `is_postable` | BOOLEAN | NO | TRUE | قابل ثبت سند یا فقط گروه‌بندی |
| `description` | TEXT | YES | NULL | توضیحات |

**Constraint‌ها:**
- `UNIQUE(code)`
- `CHECK (code ~ '^[0-9]+$')` — فقط رقم
- FK `parent_id` → accounts(id) ON DELETE RESTRICT

**مثال ساختار:**
```
1 (دارایی) — is_postable=FALSE (گروه)
├── 10 (دارایی‌های جاری) — is_postable=FALSE
│   ├── 101 (موجودی کالا) — is_postable=TRUE
│   │   └── 1011 (محصول نمونه A) — is_postable=TRUE
│   └── 102 (حساب‌های دریافتنی) — is_postable=TRUE
```

---

**پایان فایل گروه ۱**
