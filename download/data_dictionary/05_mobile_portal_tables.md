# گروه ۵: موبایل، پورتال و پرداخت (۸ جدول جدید)

> SalesDraftHeaders/Lines, ApprovalQueue, StoreOrders/Lines,
> PaymentTransactions, TaxInvoices, Barcodes

## ۳۲. `sales_draft_headers` — پیش‌نویس فروش عامل ⭐

پیش‌نویس فروش ثبت‌شده توسط عامل در موبایل. تا تأیید مدیر هیچ اثر انبار و حسابداری ندارد.

| فیلد | نوع | nullable | پیش‌فرض | توضیح |
|------|------|----------|---------|------|
| `id` | BIGSERIAL | NO | auto | کلید اصلی |
| `draft_no` | VARCHAR(50) | NO | — | شماره یکتا |
| `distributor_id` | BIGINT | NO | — | FK به distributors |
| `store_id` | BIGINT | NO | — | FK به stores |
| `draft_date` | DATE | NO | — | تاریخ پیش‌نویس |
| `sales_type` | sales_type_enum | NO | — | consignment/firm |
| `status` | doc_status_enum | NO | 'pending' | pending/reviewing/approved/rejected/posted |
| `total_amount` | NUMERIC(18,4) | NO | 0 | مبلغ کل |
| `sync_status` | VARCHAR(20) | NO | 'offline' | offline/synced/failed |
| `device_id` | VARCHAR(100) | YES | NULL | شناسه دستگاه موبایل |
| `device_signature` | VARCHAR(200) | YES | NULL | امضای امنیتی |
| `notes` | TEXT | YES | NULL | یادداشت |

---

## ۳۳. `sales_draft_lines` — اقلام پیش‌نویس

| فیلد | نوع | nullable | پیش‌فرض | توضیح |
|------|------|----------|---------|------|
| `id` | BIGSERIAL | NO | auto | کلید اصلی |
| `draft_id` | BIGINT | NO | — | FK به sales_draft_headers (CASCADE) |
| `product_id` | BIGINT | NO | — | FK به products |
| `lot_id` | BIGINT | YES | NULL | FK به inventory_lots (nullable چون ممکنه عامل انتخاب نکرده) |
| `qty` | NUMERIC(14,3) | NO | — | تعداد |
| `unit_price` | NUMERIC(18,4) | NO | — | قیمت واحد |
| `barcode_scanned` | VARCHAR(50) | YES | NULL | اگر با بارکد ثبت شده |
| `manual_entry` | BOOLEAN | NO | FALSE | ورود دستی (نه بارکد) |
| `line_total` | NUMERIC(18,4) | GENERATED | qty × unit_price | محاسبه خودکار |

---

## ۳۴. `approval_queue` — صف مرکزی تأیید مدیر ⭐

| فیلد | نوع | nullable | پیش‌فرض | توضیح |
|------|------|----------|---------|------|
| `id` | BIGSERIAL | NO | auto | کلید اصلی |
| `ref_doc_type` | VARCHAR(50) | NO | — | sales_draft/store_order/transfer |
| `ref_doc_id` | BIGINT | NO | — | شناسه سند مرجع |
| `requested_by` | BIGINT | YES | NULL | کاربر درخواست‌کننده |
| `requested_at` | TIMESTAMPTZ | NO | NOW() | زمان درخواست |
| `assigned_to` | BIGINT | YES | NULL | مدیر مسئول |
| `status` | doc_status_enum | NO | 'pending' | pending/reviewing/approved/rejected |
| `priority` | approval_priority_enum | NO | 'medium' | low/medium/high/urgent |
| `decision_reason` | TEXT | YES | NULL | دلیل تصمیم (در صورت رد) |
| `decided_at` | TIMESTAMPTZ | YES | NULL | زمان تصمیم |
| `decided_by` | BIGINT | YES | NULL | مدیر تصمیم‌گیرنده |

**Constraint:**
- `UNIQUE(ref_doc_type, ref_doc_id)` — هر سند فقط یک رکورد در صف

**نکته:** این جدول مرکز کنترل مدیر است. هر سند منتظر تأیید، یک رکورد در این جدول دارد.

---

## ۳۵. `store_orders` — سفارش‌های ثبت‌شده توسط فروشگاه

| فیلد | نوع | nullable | پیش‌فرض | توضیح |
|------|------|----------|---------|------|
| `id` | BIGSERIAL | NO | auto | کلید اصلی |
| `order_no` | VARCHAR(50) | NO | — | شماره یکتا |
| `store_id` | BIGINT | NO | — | FK به stores |
| `order_date` | DATE | NO | — | تاریخ سفارش |
| `status` | doc_status_enum | NO | 'submitted' | cart → submitted → under_review → approved/rejected → in_delivery → received |
| `total_amount` | NUMERIC(18,4) | NO | 0 | مبلغ کل |
| `total_qty` | NUMERIC(14,3) | NO | 0 | تعداد کل |
| `payment_status` | payment_status_enum | NO | 'initiated' | initiated/paid/failed/verified/refunded |
| `expected_delivery` | DATE | YES | NULL | تاریخ تحویل مورد انتظار |
| `delivery_address` | TEXT | YES | NULL | آدرس تحویل |
| `dispatch_id` | BIGINT | YES | NULL | FK به dispatch_headers (پس از تأیید) |

---

## ۳۶. `store_order_lines` — اقلام سفارش فروشگاه

| فیلد | نوع | nullable | پیش‌فرض | توضیح |
|------|------|----------|---------|------|
| `id` | BIGSERIAL | NO | auto | کلید اصلی |
| `order_id` | BIGINT | NO | — | FK به store_orders (CASCADE) |
| `product_id` | BIGINT | NO | — | FK به products |
| `qty` | NUMERIC(14,3) | NO | — | تعداد |
| `unit_price` | NUMERIC(18,4) | NO | — | قیمت واحد |
| `line_total` | NUMERIC(18,4) | GENERATED | qty × unit_price | محاسبه خودکار |
| `is_smart_suggestion` | BOOLEAN | NO | FALSE | اگر از Smart Reorder آمده |
| `notes` | TEXT | YES | NULL | یادداشت |

---

## ۳۷. `payment_transactions` — تراکنش‌های پرداخت آنلاین ⭐

| فیلد | نوع | nullable | پیش‌فرض | توضیح |
|------|------|----------|---------|------|
| `id` | BIGSERIAL | NO | auto | کلید اصلی |
| `transaction_no` | VARCHAR(50) | NO | — | شماره یکتا |
| `store_id` | BIGINT | NO | — | FK به stores |
| `gateway` | gateway_enum | NO | — | zarinpal/idpay/parsian |
| `amount` | NUMERIC(18,4) | NO | — | مبلغ (ریال) |
| `status` | payment_status_enum | NO | 'initiated' | initiated/paid/failed/verified/refunded |
| `authority` | VARCHAR(200) | YES | NULL | کد Authority (قبل از پرداخت) |
| `ref_id` | VARCHAR(100) | YES | NULL | کد پیگیری (پس از پرداخت) |
| `paid_at` | TIMESTAMPTZ | YES | NULL | زمان پرداخت |
| `related_doc_type` | VARCHAR(50) | NO | — | store_order/manual |
| `related_doc_id` | BIGINT | YES | NULL | شناسه سند مرجع |
| `journal_id` | BIGINT | YES | NULL | FK به journal_headers |
| `description` | TEXT | YES | NULL | توضیحات |
| `gateway_response` | JSONB | YES | NULL | پاسخ کامل درگاه |

**نکته:** جریان پرداخت:
1. initiate → status=initiated + authority دریافت می‌شه
2. کاربر به درگاه می‌ره و پرداخت می‌کنه
3. درگاه callback می‌زنه به status=paid
4. سیستم verify می‌کنه → status=verified + ref_id
5. سند حسابداری خودکار ساخته می‌شه

---

## ۳۸. `tax_invoices` — صورتحساب الکترونیکی سامان ⭐

| فیلد | نوع | nullable | پیش‌فرض | توضیح |
|------|------|----------|---------|------|
| `id` | BIGSERIAL | NO | auto | کلید اصلی |
| `store_id` | BIGINT | NO | — | FK به stores |
| `sales_id` | BIGINT | YES | NULL | FK به sales_headers (اختیاری) |
| `saman_uid` | VARCHAR(200) | YES | NULL | UID دریافت از سامان (یکتا) |
| `invoice_status` | tax_invoice_status_enum | NO | 'draft' | draft/sent/confirmed/canceled/rejected |
| `header_data` | JSONB | NO | — | استاندارد سامان (اطلاعات فروشنده/خریدار) |
| `body_data` | JSONB | NO | — | استاندارد سامان (لیست اقلام) |
| `sent_at` | TIMESTAMPTZ | YES | NULL | زمان ارسال |
| `confirmed_at` | TIMESTAMPTZ | YES | NULL | زمان تأیید سامان |
| `rejection_reason` | TEXT | YES | NULL | دلیل رد (در صورت رد) |
| `retry_count` | INTEGER | NO | 0 | تعداد تلاش مجدد |

**نکته:** فایل‌های JSON با ساختار رسمی سامان (طبق مستندات) ساخته می‌شوند. در صورت خطای سامان، Celery Task با Exponential Backoff تلاش مجدد می‌کند.

---

## ۳۹. `barcodes` — بارکد و QR Code

| فیلد | نوع | nullable | پیش‌فرض | توضیح |
|------|------|----------|---------|------|
| `id` | BIGSERIAL | NO | auto | کلید اصلی |
| `entity_type` | barcode_entity_type_enum | NO | — | product/lot/sales_order/store_order/dispatch |
| `entity_id` | BIGINT | NO | — | شناسه موجودیت |
| `barcode_value` | VARCHAR(50) | NO | — | بارکد EAN-13 یکتا |
| `qr_code_data` | TEXT | NO | — | محتوای QR (URL یا JSON) |
| `created_at` | TIMESTAMPTZ | NO | NOW() | زمان ساخت |
| `created_by` | BIGINT | YES | NULL | کاربر |

**Constraint:**
- `UNIQUE(entity_type, entity_id)` — هر موجودیت یک بارکد
- `UNIQUE(barcode_value)` — هر بارکد یکتا

---

## جدول کمکی: `barcode_scans`

لاگ تمام اسکن‌های بارکد از موبایل.

| فیلد | نوع | nullable | پیش‌فرض | توضیح |
|------|------|----------|---------|------|
| `id` | BIGSERIAL | NO | auto | کلید اصلی |
| `barcode_id` | BIGINT | YES | NULL | FK به barcodes (اگر بارکد شناخته شده) |
| `barcode_value` | VARCHAR(50) | NO | — | مقدار اسکن‌شده |
| `scanned_by` | BIGINT | YES | NULL | کاربر اسکن‌کننده |
| `scan_context` | VARCHAR(50) | YES | NULL | sale_draft/transfer/inventory_check |
| `ref_doc_type` | VARCHAR(50) | YES | NULL | سند مرجع |
| `ref_doc_id` | BIGINT | YES | NULL | شناسه سند مرجع |
| `scanned_at` | TIMESTAMPTZ | NO | NOW() | زمان اسکن |
| `device_id` | VARCHAR(100) | YES | NULL | شناسه دستگاه |

---

**پایان فایل گروه ۵**
