# گروه ۲: انبار و تولید (۷ جدول)

> Warehouses, InventoryLots, InventoryMovements, StockBalances,
> ProductionBatches, ProductionConsumption, ProductionOutputs

## ۷. `warehouses` — انبارها

انبار اصلی کارگاه + انبار مجازی هر فروشگاه (برای مدل امانی).

| فیلد | نوع | nullable | پیش‌فرض | توضیح |
|------|------|----------|---------|------|
| `id` | BIGSERIAL | NO | auto | کلید اصلی |
| `code` | VARCHAR(50) | NO | — | کد یکتا (مثلاً `WH-MAIN`) |
| `name` | VARCHAR(200) | NO | — | نام |
| `type` | warehouse_type_enum | NO | — | main/store/virtual |
| `store_id` | BIGINT | YES | NULL | FK به stores (فقط برای type=store) |
| `address` | TEXT | YES | NULL | آدرس |
| `is_active` | BOOLEAN | NO | TRUE | فعال/غیرفعال |

**Constraint‌ها:**
- `UNIQUE(code)`
- `CHECK`: اگر `type=store` پس `store_id` نباید NULL باشد

**نکته:** هر فروشگاه در جدول stores یک انبار مجازی در این جدول می‌سازیم با `type=store` و `store_id` ارجاع به همان فروشگاه.

---

## ۸. `inventory_lots` — لات‌های موجودی ⭐ قلب FEFO

هر بچ تولید = یک لات در این جدول. تاریخ انقضا معیار FEFO است.

| فیلد | نوع | nullable | پیش‌فرض | توضیح |
|------|------|----------|---------|------|
| `id` | BIGSERIAL | NO | auto | کلید اصلی |
| `product_id` | BIGINT | NO | — | FK به products |
| `warehouse_id` | BIGINT | NO | — | FK به warehouses |
| `batch_no` | VARCHAR(50) | NO | — | شماره بچ (مثلاً `BATCH-2025-001`) |
| `production_date` | DATE | NO | — | تاریخ تولید |
| `expiry_date` | DATE | NO | — | ⭐ تاریخ انقضا (معیار FEFO) |
| `initial_qty` | NUMERIC(14,3) | NO | — | مقدار اولیه |
| `current_qty` | NUMERIC(14,3) | NO | — | مقدار فعلی (کاهشی) |
| `weighted_avg_cost` | NUMERIC(18,4) | NO | 0 | بهای تمام‌شده میانگین موزون |
| `status` | VARCHAR(20) | NO | 'active' | active/expired/disposed/returned |
| `production_batch_id` | BIGINT | YES | NULL | FK به production_batches |

**Constraint‌ها:**
- `UNIQUE(product_id, warehouse_id, batch_no)` — یک بچ در هر انبار یکتاست
- `CHECK (initial_qty >= 0 AND current_qty >= 0)`
- `CHECK (expiry_date >= production_date)`

**ایندکس‌های بحرانی:**
- `idx_lots_fefo` روی `(product_id, warehouse_id, expiry_date, current_qty)` WHERE `deleted_at IS NULL AND status = 'active'`
  - ایندکس مرکب مهم‌ترین ایندکس سیستم است، برای الگوریتم FEFO استفاده می‌شود
- `idx_lots_expiry` روی `expiry_date` WHERE `current_qty > 0`

---

## ۹. `inventory_movements` — حرکت‌های انبار

تاریخچه کامل تمام ورودی/خروجی/انتقال/برگشت.

| فیلد | نوع | nullable | پیش‌فرض | توضیح |
|------|------|----------|---------|------|
| `id` | BIGSERIAL | NO | auto | کلید اصلی |
| `lot_id` | BIGINT | NO | — | FK به inventory_lots |
| `product_id` | BIGINT | NO | — | FK به products (برای کوئری سریع) |
| `warehouse_id` | BIGINT | NO | — | FK به warehouses |
| `movement_type` | movement_type_enum | NO | — | in/out/transfer/return/adjustment/production |
| `qty` | NUMERIC(14,3) | NO | — | مقدار (مثبت یا منفی) |
| `unit_cost` | NUMERIC(18,4) | YES | NULL | هزینه واحد در لحظه حرکت |
| `ref_doc_type` | VARCHAR(50) | NO | — | نوع سند مبدأ (sale/production/transfer) |
| `ref_doc_id` | BIGINT | YES | NULL | شناسه سند مبدأ |
| `created_at` | TIMESTAMPTZ | NO | NOW() | زمان حرکت |
| `created_by` | BIGINT | YES | NULL | کاربر |

**Constraint‌ها:**
- `CHECK (qty != 0)` — حرکت نباید صفر باشد

**Trigger:**
- پس از INSERT، تابع `update_weighted_avg()` میانگین موزون را محاسبه می‌کند
- پس از INSERT، تابع `update_stock_balance()` موجودی تجمیعی را به‌روزرسانی می‌کند

---

## ۱۰. `stock_balances` — موجودی تجمیعی (Cache)

برای عملکرد بالا در کوئری‌های پرتکرار.

| فیلد | نوع | nullable | پیش‌فرض | توضیح |
|------|------|----------|---------|------|
| `id` | BIGSERIAL | NO | auto | کلید اصلی |
| `product_id` | BIGINT | NO | — | FK به products |
| `warehouse_id` | BIGINT | NO | — | FK به warehouses |
| `total_qty` | NUMERIC(14,3) | NO | 0 | مجموع موجودی |
| `total_value` | NUMERIC(18,4) | NO | 0 | ارزش کل (موجودی × میانگین موزون) |
| `last_lot_id` | BIGINT | YES | NULL | آخرین لات تعامل‌شده |
| `updated_at` | TIMESTAMPTZ | NO | NOW() | آخرین به‌روزرسانی |

**Constraint‌ها:**
- `UNIQUE(product_id, warehouse_id)` — یک رکورد به ازای هر محصول+انبار
- `CHECK (total_qty >= 0)`

**نکته:** این جدول توسط Trigger به‌طور خودکار به‌روزرسانی می‌شود. هیچ INSERT دستی لازم نیست.

---

## ۱۱. `production_batches` — بچ‌های تولید

| فیلد | نوع | nullable | پیش‌فرض | توضیح |
|------|------|----------|---------|------|
| `id` | BIGSERIAL | NO | auto | کلید اصلی |
| `batch_no` | VARCHAR(50) | NO | — | شماره بچ یکتا |
| `product_id` | BIGINT | NO | — | FK به products |
| `planned_qty` | NUMERIC(14,3) | NO | — | مقدار برنامه‌ریزی‌شده |
| `actual_qty` | NUMERIC(14,3) | NO | 0 | مقدار واقعی تولیدشده |
| `waste_qty` | NUMERIC(14,3) | NO | 0 | ضایعات |
| `start_at` | TIMESTAMPTZ | YES | NULL | زمان شروع |
| `end_at` | TIMESTAMPTZ | YES | NULL | زمان پایان |
| `status` | VARCHAR(20) | NO | 'planned' | planned/in_progress/completed/canceled |
| `weighted_avg_cost` | NUMERIC(18,4) | NO | 0 | بهای تمام‌شده نهایی |
| `notes` | TEXT | YES | NULL | یادداشت |

---

## ۱۲. `production_consumption` — مصرف مواد اولیه

مواد اولیه مصرفی برای هر بچ تولید (با هزینه لحظه‌ای).

| فیلد | نوع | nullable | پیش‌فرض | توضیح |
|------|------|----------|---------|------|
| `id` | BIGSERIAL | NO | auto | کلید اصلی |
| `batch_id` | BIGINT | NO | — | FK به production_batches (CASCADE) |
| `material_lot_id` | BIGINT | NO | — | FK به inventory_lots |
| `qty_consumed` | NUMERIC(14,3) | NO | — | مقدار مصرف‌شده |
| `cost_at_consumption` | NUMERIC(18,4) | NO | — | هزینه واحد در لحظه مصرف |
| `consumed_at` | TIMESTAMPTZ | NO | NOW() | زمان مصرف |
| `created_by` | BIGINT | YES | NULL | کاربر |

**Constraint‌ها:**
- `CHECK (qty_consumed > 0)`

---

## ۱۳. `production_outputs` — خروج محصول نهایی

خروج محصول نهایی از بچ تولید با ساخت لات جدید.

| فیلد | نوع | nullable | پیش‌فرض | توضیح |
|------|------|----------|---------|------|
| `id` | BIGSERIAL | NO | auto | کلید اصلی |
| `batch_id` | BIGINT | NO | — | FK به production_batches (CASCADE) |
| `product_id` | BIGINT | NO | — | FK به products |
| `qty_produced` | NUMERIC(14,3) | NO | — | مقدار تولیدشده |
| `qty_waste` | NUMERIC(14,3) | NO | 0 | ضایعات |
| `lot_id` | BIGINT | NO | — | FK به inventory_lots (لات جدید) |
| `output_at` | TIMESTAMPTZ | NO | NOW() | زمان خروج |

**نکته:** پس از INSERT در این جدول، Trigger مربوطه یک رکورد جدید در `inventory_lots` با `current_qty = qty_produced` می‌سازد.

---

**پایان فایل گروه ۲**
