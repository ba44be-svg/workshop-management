# روابط کلیدی ERD — نسخه ۲.۰

> تمام روابط Foreign Key بین ۴۹ جدول

## 📊 آمار

- **۴۹ جدول اصلی**
- **۸۰+ رابط FK (Foreign Key)**
- **۵ رابط Self-Reference** (درخت‌ها)
- **۶ رابط Polymorphic** (ارائه عمومی)
- **۸ رابط One-to-One**

---

## ۱. روابط بحرانی کسب‌وکار

### ۱.۱. `inventory_lots` ↔ `sales_lines` — ردیابی FEFO
```
inventory_lots (1) ←——— (M) sales_lines
```
**توضیح:** هر خط فروش به یک لات مشخص ارجاع می‌دهد تا ردیابی FEFO قابل اجرا باشد.

---

### ۱.۲. `production_batches` ↔ `inventory_lots` — تولید لات
```
production_batches (1) ←——— (1) inventory_lots
```
**توضیح:** هر بچ تولید، یک لات جدید در `inventory_lots` ایجاد می‌کند.

---

### ۱.۳. `sales_headers` ↔ `journal_headers` — سند حسابداری خودکار
```
sales_headers (1) ——— (0..1) journal_headers
```
**توضیح:** هر سند فروش پس از commit، یک سند حسابداری خودکار تولید می‌کند (با سیگنال Django).

---

### ۱.۴. `stores` ↔ `warehouses` — انبار مجازی فروشگاه
```
stores (1) ——— (0..1) warehouses  [WHERE warehouses.type = 'store']
```
**توضیح:** هر فروشگاه یک انبار مجازی (Virtual Warehouse) برای مدل امانی دارد.

---

### ۱.۵. `distributors` ↔ `stores` — چند به چند (از طریق routes)
```
distributors (1) ←——— (M) routes ←——— (M) stores
```
**توضیح:** هر عامل چند فروشگاه را سرو می‌کند و هر فروشگاه ممکن است توسط چند عامل در روزهای مختلف سرو شود.

---

### ۱.۶. `sales_draft_headers` ↔ `approval_queue` — جریان تأیید
```
sales_draft_headers (1) ——— (0..1) approval_queue
```
**توضیح:** هر پیش‌نویس عامل، یک رکورد در صف تأیید می‌سازد. پس از تأیید، رکورد `sales_headers` ایجاد می‌شود.

---

### ۱.۷. `store_orders` ↔ `approval_queue` — جریان تأیید
```
store_orders (1) ——— (0..1) approval_queue
```

---

### ۱.۸. `store_orders` ↔ `payment_transactions` — پرداخت‌های سفارش
```
store_orders (1) ←——— (M) payment_transactions
```
**توضیح:** چندین پرداخت ممکن است برای یک سفارش انجام شود (مثلاً ۵۰٪ آنلاین، ۵۰٪ چکی).

---

### ۱.۹. `sales_headers` ↔ `tax_invoices` — صورتحساب سامان
```
sales_headers (1) ——— (0..1) tax_invoices
```
**توضیح:** هر فروش قطعی پس از commit، یک صورتحساب الکترونیکی سامان می‌سازد.

---

### ۱.۱۰. `barcodes` ↔ `(Product|Lot|SalesOrder|...)` — چندریختی
```
barcodes.entity_type + entity_id → polymorphic reference
```
**توضیح:** هر بارکد به یکی از ۵ موجودیت (product, lot, sales_order, store_order, dispatch) ارجاع می‌دهد.

---

### ۱.۱۱. `stores` ↔ `loyalty_transactions` — امتیاز وفاداری
```
stores (1) ←——— (M) loyalty_transactions
```
**توضیح:** هر فروشگاه چندین تراکنش وفاداری دارد که امتیاز پویای فعلی محاسبه می‌شود.

---

## ۲. روابط درختی (Self-Reference)

### ۲.۱. `product_categories.parent_id → product_categories.id`
```
product_categories (parent) ←——— (M) product_categories (children)
```
**ساختار:** ۳-۵ سطح درختی برای دسته‌بندی محصولات.

---

### ۲.۲. `accounts.parent_id → accounts.id`
```
accounts (parent) ←——— (M) accounts (children)
```
**ساختار:** کدینگ درختی حساب‌ها با ۵ نوع اصلی (دارایی، بدهی، سرمایه، درآمد، هزینه).

---

### ۲.۳. `cost_centers.parent_id → cost_centers.id`
```
cost_centers (parent) ←——— (M) cost_centers (children)
```
**ساختار:** مرکز هزینه درختی (مثلاً تولید > خط ۱ > ایستگاه A).

---

### ۲.۴. `journal_headers.reversed_by_journal_id → journal_headers.id`
```
journal_headers (original) ——— (0..1) journal_headers (reversal)
```
**توضیح:** یک سند معکوس به سند اصلی ارجاع می‌دهد.

---

### ۲.۵. `accounts(parent_id)` در حسابداری — خودارائه‌ای
**(با شماره ۲.۲ پوشش داده شد)**

---

## ۳. روابط Header-Line (ساختار استاندارد)

| Header | Line | رابطه |
|--------|------|------|
| `dispatch_headers` | `dispatch_lines` | 1:M (CASCADE) |
| `sales_headers` | `sales_lines` | 1:M (CASCADE) |
| `return_headers` | `return_lines` | 1:M (CASCADE) |
| `transfer_headers` | `transfer_lines` | 1:M (CASCADE) |
| `journal_headers` | `journal_lines` | 1:M (CASCADE) |
| `sales_draft_headers` | `sales_draft_lines` | 1:M (CASCADE) |
| `store_orders` | `store_order_lines` | 1:M (CASCADE) |
| `production_batches` | `production_consumption` | 1:M (CASCADE) |
| `production_batches` | `production_outputs` | 1:M (CASCADE) |

**نکته:** در تمام Header-Line، سیاست DELETE روی header = CASCADE است تا با حذف header، تمام line‌ها هم پاک بشن.

---

## ۴. روابط Polymorphic (چندریختی)

### ۴.۱. `inventory_movements.ref_doc_type + ref_doc_id`
```
inventory_movements.ref_doc_type IN ('sale', 'production', 'transfer', 'return', '...')
ref_doc_id → شناسه سند مرجع
```
**توضیح:** هر حرکت انبار به یک سند مختلفی ارجاع می‌دهد (sale → sales_headers.id, production → production_batches.id, ...).

---

### ۴.۲. `journal_lines.ref_doc_type + ref_doc_id`
**(مشابه ۴.۱)**

---

### ۴.۳. `barcodes.entity_type + entity_id`
```
barcodes.entity_type IN ('product', 'lot', 'sales_order', 'store_order', 'dispatch')
```

---

### ۴.۴. `approval_queue.ref_doc_type + ref_doc_id`
```
approval_queue.ref_doc_type IN ('sales_draft', 'store_order', 'transfer')
```

---

### ۴.۵. `payment_transactions.related_doc_type + related_doc_id`
```
payment_transactions.related_doc_type IN ('store_order', 'manual', ...)
```

---

### ۴.۶. `notification_schedules.recipient_type + recipient_id`
```
notification_schedules.recipient_type IN ('distributor', 'store', 'manager', ...)
```

---

## ۵. روابط User-centric

### ۵.۱. روابط در `users`

| جدول | فیلد | ارجاع به |
|------|------|---------|
| `users` | `id` | (PK) |
| `users` | `created_by` | self (کاربر سازنده) |
| `activity_logs` | `user_id` | users.id |
| `activity_logs` | `created_by` | users.id |
| `user_profiles` | `user_id` | users.id (PK) |
| `user_roles` | `user_id` | users.id |
| `user_roles` | `assigned_by` | users.id |
| `push_notifications` | `user_id` | users.id |
| `sales_draft_headers` | `created_by` | users.id |
| `approval_queue` | `requested_by` | users.id |
| `approval_queue` | `assigned_to` | users.id |
| `approval_queue` | `decided_by` | users.id |
| `salesperson_visits` | (implicit through distributor_id) | |
| `transfer_headers` | `initiator_id` | users.id |
| `transfer_headers` | `receiver_id` | users.id |
| `cost_centers` | `created_by` | users.id |
| `fiscal_periods` | `closed_by` | users.id |

---

## ۶. روابط Identity (One-to-One)

| جدول A | جدول B | نوع |
|--------|--------|------|
| `users` | `user_profiles` | 1:1 (هر کاربر یک پروفایل) |
| `stores` | `warehouses` | 1:1 (هر فروشگاه یک انبار مجازی WHERE type='store') |
| `sales_headers` | `journal_headers` | 1:0..1 (اختیاری — فقط فروش‌های posted) |
| `sales_headers` | `tax_invoices` | 1:0..1 (اختیاری — فقط فروش‌های قطعی) |
| `sales_draft_headers` | `approval_queue` | 1:0..1 |
| `store_orders` | `approval_queue` | 1:0..1 |

---

## ۷. نمودار مرور کلی

```
                              ┌──────────────────┐
                              │     users         │
                              └────────┬─────────┘
                                       │
                ┌──────────────────────┼──────────────────┐
                │                       │                   │
                ▼                        ▼                   ▼
        ┌──────────────┐         ┌──────────────┐         ┌──────────────┐
        │distributors  │         │ stores       │         │activity_logs │
        └──────┬───────┘         └──────┬───────┘         └──────────────┘
               │                          │
               │                          │
               │                          │
        ┌──────▼───────┐         ┌──────▼───────┐
        │  routes      │         │ warehouses   │
        └──────────────┘         └──────┬───────┘
                                         │
                                         │
                                  ┌──────▼───────┐
                                  │inventory_lots│ ← FEFO
                                  └──────┬───────┘
                                         │
              ┌──────────────────────────┼──────────────────────────┐
              │                           │                           │
              ▼                            ▼                            ▼
        ┌──────────────┐         ┌──────────────┐         ┌──────────────┐
        │sales_draft_  │         │sales_lines   │         │production_   │
        │headers       │         │              │         │outputs       │
        └──────┬───────┘         └──────────────┘         └──────────────┘
               │
        ┌──────▼───────┐
        │approval_queue│
        └──────┬───────┘
               │
        ┌──────▼───────┐         ┌──────────────┐         ┌──────────────┐
        │sales_headers │ ───────→│journal_      │ ───────→│tax_invoices  │
        │              │         │headers       │         │(سامان)       │
        └──────────────┘         └──────────────┘         └──────────────┘
                                          │
                                          ▼
                                  ┌──────────────┐
                                  │journal_lines │
                                  └──────────────┘
```

---

## ۸. نکات طراحی روابط

### ۸.۱. سیاست‌های حذف

| سیاست | استفاده | دلیل |
|------|---------|------|
| `ON DELETE CASCADE` | Header → Line | حذف header تمام خطوط را هم پاک می‌کند |
| `ON DELETE RESTRICT` | همه روابط دیگر | جلوگیری از حذف رکورد ارجاع‌شده |
| `ON DELETE SET NULL` | created_by, decided_by | رکورد audit بدون کاربر باقی می‌ماند |

### ۸.۲. ایندکس‌های کلیدی FK

همه ستون‌های FK ایندکس دارند:
- `idx_lots_product_warehouse` روی `inventory_lots(product_id, warehouse_id)`
- `idx_sales_lines_lot` روی `sales_lines(lot_id)` (برای trace-back FEFO)
- `idx_journal_lines_journal` روی `journal_lines(journal_id)`

### ۸.۳. کنترل یکپارچگی در سطح Application

برای روابط polymorphic (که FK واقعی نیستند)، کنترل یکپارچگی در لایه Django Service انجام می‌شود:
```python
# مثال: کنترل یکپارچگی inventory_movements
def create_movement(ref_doc_type, ref_doc_id, ...):
    # اعتبارسنجی سند مرجع
    if ref_doc_type == 'sale':
        SalesHeader.objects.get(id=ref_doc_id)
    elif ref_doc_type == 'production':
        ProductionBatch.objects.get(id=ref_doc_id)
    # ... و غیره
```

---

**پایان فایل روابط**
