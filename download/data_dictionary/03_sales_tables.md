# گروه ۳: فروش و پخش (۱۲ جدول)

> DispatchHeaders/Lines, SalesHeaders/Lines, ReturnHeaders/Lines,
> TransferHeaders/Lines, Routes, Vehicles, PricingRules, SalesPersonVisits

## ۱۴. `vehicles` — خودروهای پخش

| فیلد | نوع | nullable | پیش‌فرض | توضیح |
|------|------|----------|---------|------|
| `id` | BIGSERIAL | NO | auto | کلید اصلی |
| `plate` | VARCHAR(20) | NO | — | پلاک یکتا |
| `capacity` | NUMERIC(14,3) | NO | — | ظرفیت (کیلوگرم/تعداد) |
| `driver_name` | VARCHAR(200) | YES | NULL | نام راننده |
| `fuel_card` | VARCHAR(50) | YES | NULL | کارت سوخت |
| `is_active` | BOOLEAN | NO | TRUE | فعال |

---

## ۱۵. `routes` — مسیرهای هر عامل در هر روز هفته

| فیلد | نوع | nullable | پیش‌فرض | توضیح |
|------|------|----------|---------|------|
| `id` | BIGSERIAL | NO | auto | کلید اصلی |
| `distributor_id` | BIGINT | NO | — | FK به distributors |
| `day_of_week` | SMALLINT | NO | — | ۰=شنبه تا ۶=جمعه |
| `store_sequence` | JSONB | NO | — | لیست فروشگاه‌ها با ترتیب و زمان |
| `is_active` | BOOLEAN | NO | TRUE | فعال |

**مثال `store_sequence`:**
```json
[
    {"store_id": 1, "store_name": "بنک...", "expected_time": "08:30"},
    {"store_id": 5, "store_name": "سوپر رها", "expected_time": "09:15"}
]
```

---

## ۱۶. `pricing_rules` — قیمت‌گذاری پویا

| فیلد | نوع | nullable | پیش‌فرض | توضیح |
|------|------|----------|---------|------|
| `id` | BIGSERIAL | NO | auto | کلید اصلی |
| `product_id` | BIGINT | NO | — | FK به products |
| `store_tier` | store_tier_enum | NO | — | regular/silver/gold/platinum |
| `min_price` | NUMERIC(18,4) | NO | — | حداقل قیمت (نمی‌تون پایین‌تر بره) |
| `default_price` | NUMERIC(18,4) | NO | — | قیمت پیش‌فرض |
| `effective_date` | DATE | NO | CURRENT_DATE | تاریخ شروع اعتبار |
| `expires_at` | DATE | YES | NULL | تاریخ انقضای قیمت |

---

## ۱۷. `dispatch_headers` — سند پخش به عامل

| فیلد | نوع | nullable | پیش‌فرض | توضیح |
|------|------|----------|---------|------|
| `id` | BIGSERIAL | NO | auto | کلید اصلی |
| `dispatch_no` | VARCHAR(50) | NO | — | شماره یکتا |
| `distributor_id` | BIGINT | NO | — | FK به distributors |
| `dispatch_date` | DATE | NO | — | تاریخ پخش |
| `total_qty` | NUMERIC(14,3) | NO | 0 | مجموع تعداد |
| `total_amount` | NUMERIC(18,4) | NO | 0 | مبلغ کل |
| `status` | doc_status_enum | NO | 'pending' | pending/in_delivery/arrived/canceled |
| `vehicle_id` | BIGINT | YES | NULL | FK به vehicles |
| `notes` | TEXT | YES | NULL | یادداشت |

---

## ۱۸. `dispatch_lines` — اقلام پخش با مقصد

| فیلد | نوع | nullable | پیش‌فرض | توضیح |
|------|------|----------|---------|------|
| `id` | BIGSERIAL | NO | auto | کلید اصلی |
| `dispatch_id` | BIGINT | NO | — | FK به dispatch_headers (CASCADE) |
| `product_id` | BIGINT | NO | — | FK به products |
| `lot_id` | BIGINT | YES | NULL | FK به inventory_lots (لات مشخص) |
| `qty` | NUMERIC(14,3) | NO | — | تعداد |
| `unit_price` | NUMERIC(18,4) | NO | — | قیمت واحد |
| `dest_store_id` | BIGINT | NO | — | FK به stores (مقصد) |
| `line_total` | NUMERIC(18,4) | GENERATED | qty × unit_price | محاسبه خودکار |

---

## ۱۹. `sales_headers` — سند فروش (امانی/قطعی)

| فیلد | نوع | nullable | پیش‌فرض | توضیح |
|------|------|----------|---------|------|
| `id` | BIGSERIAL | NO | auto | کلید اصلی |
| `sale_no` | VARCHAR(50) | NO | — | شماره یکتا |
| `store_id` | BIGINT | NO | — | FK به stores |
| `sale_date` | DATE | NO | — | تاریخ فروش |
| `sales_type` | sales_type_enum | NO | — | consignment/firm |
| `total_amount` | NUMERIC(18,4) | NO | 0 | مبلغ کل (فروش) |
| `total_cost` | NUMERIC(18,4) | NO | 0 | بهای تمام‌شده |
| `total_profit` | NUMERIC(18,4) | GENERATED | total_amount - total_cost | سود خودکار |
| `status` | doc_status_enum | NO | 'posted' | وضعیت سند |
| `journal_id` | BIGINT | YES | NULL | FK به journal_headers |
| `tax_invoice_id` | BIGINT | YES | NULL | FK به tax_invoices (سامان) |
| `dispatch_id` | BIGINT | YES | NULL | FK به dispatch_headers |
| `distributor_id` | BIGINT | YES | NULL | FK به distributors |

---

## ۲۰. `sales_lines` — اقلام فروش با لات (FEFO)

| فیلد | نوع | nullable | پیش‌فرض | توضیح |
|------|------|----------|---------|------|
| `id` | BIGSERIAL | NO | auto | کلید اصلی |
| `sale_id` | BIGINT | NO | — | FK به sales_headers (CASCADE) |
| `product_id` | BIGINT | NO | — | FK به products |
| `lot_id` | BIGINT | YES | NULL | FK به inventory_lots (⭐ ردیابی FEFO) |
| `qty` | NUMERIC(14,3) | NO | — | تعداد |
| `unit_price` | NUMERIC(18,4) | NO | — | قیمت فروش |
| `unit_cost` | NUMERIC(18,4) | NO | — | بهای تمام‌شده (میانگین موزون) |
| `line_total` | NUMERIC(18,4) | GENERATED | qty × unit_price | محاسبه خودکار |

---

## ۲۱. `return_headers` — برگشت از فروشگاه

| فیلد | نوع | nullable | پیش‌فرض | توضیح |
|------|------|----------|---------|------|
| `id` | BIGSERIAL | NO | auto | کلید اصلی |
| `return_no` | VARCHAR(50) | NO | — | شماره یکتا |
| `store_id` | BIGINT | NO | — | FK به stores |
| `return_date` | DATE | NO | — | تاریخ |
| `original_sale_id` | BIGINT | YES | NULL | FK به sales_headers (ارجاع) |
| `total_qty` | NUMERIC(14,3) | NO | 0 | تعداد کل |
| `reason` | TEXT | YES | NULL | دلیل برگشت |
| `status` | doc_status_enum | NO | 'pending' | وضعیت |
| `journal_id` | BIGINT | YES | NULL | FK (سند معکوس) |

---

## ۲۲. `return_lines` — اقلام برگشت با وضعیت

| فیلد | نوع | nullable | پیش‌فرض | توضیح |
|------|------|----------|---------|------|
| `id` | BIGSERIAL | NO | auto | کلید اصلی |
| `return_id` | BIGINT | NO | — | FK به return_headers (CASCADE) |
| `product_id` | BIGINT | NO | — | FK به products |
| `lot_id` | BIGINT | YES | NULL | FK به inventory_lots |
| `qty` | NUMERIC(14,3) | NO | — | تعداد |
| `condition` | return_condition_enum | NO | 'sellable' | sellable/expired/damaged/near_expiry |
| `notes` | TEXT | YES | NULL | یادداشت |

**نکته:** فیلد `condition` تعیین می‌کنه کالا به انبار برگرده یا به‌عنوان ضایعات ثبت بشه.

---

## ۲۳. `transfer_headers` — انتقال بین دو فروشگاه

| فیلد | نوع | nullable | پیش‌فرض | توضیح |
|------|------|----------|---------|------|
| `id` | BIGSERIAL | NO | auto | کلید اصلی |
| `transfer_no` | VARCHAR(50) | NO | — | شماره یکتا |
| `from_store_id` | BIGINT | NO | — | FK به stores (مبدأ) |
| `to_store_id` | BIGINT | NO | — | FK به stores (مقصد) |
| `transfer_date` | DATE | NO | — | تاریخ |
| `status` | doc_status_enum | NO | 'pending' | وضعیت |
| `initiator_id` | BIGINT | YES | NULL | کاربر آغازگر |
| `receiver_id` | BIGINT | YES | NULL | کاربر گیرنده (تأیید) |
| `reason` | TEXT | YES | NULL | دلیل |

**Constraint:**
- `CHECK (from_store_id != to_store_id)` — مبدأ و مقصد نباید یکی باشن

---

## ۲۴. `transfer_lines` — اقلام انتقال

| فیلد | نوع | nullable | پیش‌فرض | توضیح |
|------|------|----------|---------|------|
| `id` | BIGSERIAL | NO | auto | کلید اصلی |
| `transfer_id` | BIGINT | NO | — | FK به transfer_headers (CASCADE) |
| `product_id` | BIGINT | NO | — | FK به products |
| `lot_id` | BIGINT | YES | NULL | FK به inventory_lots |
| `qty` | NUMERIC(14,3) | NO | — | تعداد |
| `expiry_date` | DATE | YES | NULL | تاریخ انقضا (snapshot) |

---

## ۲۵. `salesperson_visits` — ردیابی سرکشی

| فیلد | نوع | nullable | پیش‌فرض | توضیح |
|------|------|----------|---------|------|
| `id` | BIGSERIAL | NO | auto | کلید اصلی |
| `distributor_id` | BIGINT | NO | — | FK به distributors |
| `store_id` | BIGINT | NO | — | FK به stores |
| `visit_date` | DATE | NO | — | تاریخ |
| `check_in_time` | TIMESTAMPTZ | YES | NULL | زمان ورود |
| `check_out_time` | TIMESTAMPTZ | YES | NULL | زمان خروج |
| `sales_count` | INTEGER | NO | 0 | تعداد فروش در این سرکشی |
| `sales_amount` | NUMERIC(18,4) | NO | 0 | مبلغ فروش |
| `geo_lat_checkin` | NUMERIC(10,7) | YES | NULL | موقعیت ورود |
| `geo_lng_checkin` | NUMERIC(10,7) | YES | NULL | موقعیت ورود |
| `notes` | TEXT | YES | NULL | یادداشت |

**Constraint:**
- `UNIQUE(distributor_id, store_id, visit_date)` — یک سرکشی در روز

---

**پایان فایل گروه ۳**
