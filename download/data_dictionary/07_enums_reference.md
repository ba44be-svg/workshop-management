# تمام ENUM Type‌های PostgreSQL

> مرجع کامل تمام نوع‌های داده ENUM در دیتابیس نسخه ۲.۰

## 📋 خلاصه

| # | نام | مقادیر | استفاده در |
|---|------|--------|------|
| ۱ | `sales_type_enum` | consignment, firm | sales_headers, sales_draft_headers |
| ۲ | `doc_status_enum` | pending, reviewing, approved, rejected, posted, in_delivery, received, canceled | همه اسناد |
| ۳ | `movement_type_enum` | in, out, transfer, return, adjustment, production | inventory_movements |
| ۴ | `account_type_enum` | asset, liability, equity, revenue, expense | accounts |
| ۵ | `warehouse_type_enum` | main, store, virtual | warehouses |
| ۶ | `store_tier_enum` | regular, silver, gold, platinum | stores, pricing_rules |
| ۷ | `sales_model_enum` | consignment, firm, mixed | stores |
| ۸ | `payment_status_enum` | initiated, paid, failed, verified, refunded | payment_transactions, store_orders |
| ۹ | `gateway_enum` | zarinpal, idpay, parsian | payment_transactions |
| ۱۰ | `tax_invoice_status_enum` | draft, sent, confirmed, canceled, rejected | tax_invoices |
| ۱۱ | `barcode_entity_type_enum` | product, lot, sales_order, store_order, dispatch | barcodes |
| ۱۲ | `return_condition_enum` | sellable, expired, damaged, near_expiry | return_lines |
| ۱۳ | `user_role_enum` | manager, accountant, storekeeper, distributor, store_owner | users |
| ۱۴ | `approval_priority_enum` | low, medium, high, urgent | approval_queue |
| ۱۵ | `notification_status_enum` | queued, sent, delivered, failed, read | sms_queue, push_notifications |
| ۱۶ | `notification_channel_enum` | sms, push, both | notification_schedules |
| ۱۷ | `fiscal_period_type_enum` | monthly, quarterly, yearly | fiscal_periods |
| ۱۸ | `notification_scenario_enum` | (۱۱ مقدار) | notification_schedules |

---

## جزئیات هر ENUM

### ۱. `sales_type_enum` — نوع فروش

```sql
CREATE TYPE sales_type_enum AS ENUM ('consignment', 'firm');
```

| مقدار | توضیح |
|-------|------|
| `consignment` | فروش امانی — مالکیت تا فروش نهایی در دست کارگاه |
| `firm` | فروش قطعی — مالکیت به فروشگاه منتقل می‌شود |

---

### ۲. `doc_status_enum` — وضعیت اسناد

```sql
CREATE TYPE doc_status_enum AS ENUM (
    'pending', 'reviewing', 'approved', 'rejected', 'posted',
    'in_delivery', 'received', 'canceled'
);
```

| مقدار | توضیح | جریان |
|-------|------|------|
| `pending` | در انتظار بررسی | ۱ |
| `reviewing` | در حال بررسی توسط مدیر | ۲ |
| `approved` | تأیید شده | ۳ |
| `rejected` | رد شده | ۳ |
| `posted` | ثبت نهایی (با اثر انبار و حسابداری) | ۴ |
| `in_delivery` | در حال تحویل | — |
| `received` | دریافت شده | — |
| `canceled` | لغو شده | — |

---

### ۳. `movement_type_enum` — نوع حرکت انبار

```sql
CREATE TYPE movement_type_enum AS ENUM (
    'in', 'out', 'transfer', 'return', 'adjustment', 'production'
);
```

| مقدار | توضیح | اثر در موجودی |
|-------|------|-------------|
| `in` | ورود (خرید یا تولید) | + |
| `out` | خروج (فروش یا مصرف) | - |
| `transfer` | انتقال بین انبارها | صفر (مثبت در مقصد، منفی در مبدأ) |
| `return` | برگشت از فروشگاه | + |
| `adjustment` | تعدیل دستی (سرشماری) | ± |
| `production` | تولید (مواد اولیه به محصول) | - مواد + محصول |

---

### ۴. `account_type_enum` — نوع حساب

```sql
CREATE TYPE account_type_enum AS ENUM (
    'asset', 'liability', 'equity', 'revenue', 'expense'
);
```

| مقدار | توضیح | مثال |
|-------|------|------|
| `asset` | دارایی | ۱۰۱: موجودی کالا، ۱۰۲: حساب‌های دریافتنی |
| `liability` | بدهی | ۲۰۱: حساب‌های پرداختنی |
| `equity` | سرمایه | ۳۰: سرمایه |
| `revenue` | درآمد | ۴۰۱: درآمد فروش |
| `expense` | هزینه | ۵۰: بهای تمام‌شده فروش |

---

### ۵. `warehouse_type_enum` — نوع انبار

```sql
CREATE TYPE warehouse_type_enum AS ENUM ('main', 'store', 'virtual');
```

| مقدار | توضیح |
|-------|------|
| `main` | انبار اصلی کارگاه |
| `store` | انبار مجازی هر فروشگاه (برای مدل امانی) |
| `virtual` | انبار منطقی (مثلاً در حال انتقال) |

---

### ۶. `store_tier_enum` — لایه وفاداری فروشگاه

```sql
CREATE TYPE store_tier_enum AS ENUM ('regular', 'silver', 'gold', 'platinum');
```

| مقدار | امتیاز لازم | تخفیف | سقف اعتبار |
|-------|-----------|------|---------|
| `regular` | ۰ | ۰٪ | ۱۰۰M |
| `silver` | ۱۰۰+ | ۲٪ | ۱۵۰M |
| `gold` | ۵۰۰+ | ۵٪ | ۲۵۰M |
| `platinum` | ۱۰۰۰+ | ۸٪ | ۵۰۰M |

---

### ۷. `sales_model_enum` — مدل فروش فروشگاه

```sql
CREATE TYPE sales_model_enum AS ENUM ('consignment', 'firm', 'mixed');
```

| مقدار | توضیح |
|-------|------|
| `consignment` | فقط امانی |
| `firm` | فقط قطعی |
| `mixed` | ترکیبی (مثلاً ۸۰٪ امانی، ۲۰٪ قطعی) |

---

### ۸. `payment_status_enum` — وضعیت پرداخت آنلاین

```sql
CREATE TYPE payment_status_enum AS ENUM (
    'initiated', 'paid', 'failed', 'verified', 'refunded'
);
```

| مقدار | توضیح | مرحله جریان |
|-------|------|---------|
| `initiated` | شروع شده (Authority دریافت شد) | ۱ |
| `paid` | کاربر پرداخت کرد (Callback received) | ۲ |
| `failed` | پرداخت ناموفق یا verify نشد | ۲ |
| `verified` | تأیید نهایی (Verify API) | ۳ |
| `refunded` | بازگشت وجه | ۴ |

---

### ۹. `gateway_enum` — نوع درگاه پرداخت

```sql
CREATE TYPE gateway_enum AS ENUM ('zarinpal', 'idpay', 'parsian');
```

| مقدار | نام | API URL |
|-------|------|---------|
| `zarinpal` | زرین‌پال | https://api.zarinpal.com/v1/ |
| `idpay` | آیدی‌پی | https://api.idpay.ir/v1.1/ |
| `parsian` | بانک پارسیان | https://pec.shaparak.ir/... |

---

### ۱۰. `tax_invoice_status_enum` — وضعیت صورتحساب سامان

```sql
CREATE TYPE tax_invoice_status_enum AS ENUM (
    'draft', 'sent', 'confirmed', 'canceled', 'rejected'
);
```

| مقدار | توضیح |
|-------|------|
| `draft` | پیش‌نویس (هیچ ارسال نشده) |
| `sent` | ارسال شد (در انتظار تأیید سامان) |
| `confirmed` | تأیید شد (UID دریافت شد) |
| `canceled` | لغو شد (با رکورد جدید جایگزین) |
| `rejected` | سامان رد کرد |

---

### ۱۱. `barcode_entity_type_enum` — نوع موجودیت بارکد

```sql
CREATE TYPE barcode_entity_type_enum AS ENUM (
    'product', 'lot', 'sales_order', 'store_order', 'dispatch'
);
```

| مقدار | نوع بارکد | فرمت |
|-------|---------|------|
| `product` | محصول | EAN-13 |
| `lot` | لات | EAN-13 |
| `sales_order` | سند فروش | QR Code |
| `store_order` | سفارش فروشگاه | QR Code |
| `dispatch` | سند پخش | QR Code |

---

### ۱۲. `return_condition_enum` — وضعیت کالای برگشتی

```sql
CREATE TYPE return_condition_enum AS ENUM (
    'sellable', 'expired', 'damaged', 'near_expiry'
);
```

| مقدار | توضیح | اثر |
|-------|------|------|
| `sellable` | قابل فروش مجدد | به انبار برمی‌گردد |
| `expired` | منقضی | ضایعات (هزینه) |
| `damaged` | آسیب‌دیده | ضایعات (هزینه) |
| `near_expiry` | نزدیک به انقضا | به انبار برمی‌گردد + هشدار |

---

### ۱۳. `user_role_enum` — نقش کاربر

```sql
CREATE TYPE user_role_enum AS ENUM (
    'manager', 'accountant', 'storekeeper', 'distributor', 'store_owner'
);
```

---

### ۱۴. `approval_priority_enum` — اولویت تأیید

```sql
CREATE TYPE approval_priority_enum AS ENUM ('low', 'medium', 'high', 'urgent');
```

| مقدار | توضیح |
|-------|------|
| `low` | کم (مثلاً انتقال بین انبار) |
| `medium` | متوسط |
| `high` | بالا (مثلاً سفارش بزرگ) |
| `urgent` | فوری (مثلاً لات نزدیک به انقضا) |

---

### ۱۵. `notification_status_enum` — وضعیت اعلان

```sql
CREATE TYPE notification_status_enum AS ENUM (
    'queued', 'sent', 'delivered', 'failed', 'read'
);
```

---

### ۱۶. `notification_channel_enum` — کانال اعلان

```sql
CREATE TYPE notification_channel_enum AS ENUM ('sms', 'push', 'both');
```

| مقدار | توضیح | هزینه |
|-------|------|------|
| `sms` | فقط پیامک | ۳۰۰ ریال/پیامک |
| `push` | فقط Push Notification (Firebase) | رایگان |
| `both` | هر دو (برای اعلان‌های بحرانی) | ۳۰۰ ریال/پیامک |

---

### ۱۷. `fiscal_period_type_enum` — نوع دوره مالی

```sql
CREATE TYPE fiscal_period_type_enum AS ENUM ('monthly', 'quarterly', 'yearly');
```

---

### ۱۸. `notification_scenario_enum` — سناریوی اعلان

```sql
CREATE TYPE notification_scenario_enum AS ENUM (
    'visit_reminder', 'sale_confirmation', 'expiry_alert',
    'transfer_request', 'low_stock', 'journal_error',
    'order_approved', 'order_rejected', 'payment_success',
    'tier_upgrade', 'draft_rejected'
);
```

| مقدار | توضیح | گیرنده | کانال |
|-------|------|--------|------|
| `visit_reminder` | یادآوری سرکشی | عامل | both |
| `sale_confirmation` | تأیید فروش | فروشگاه | sms |
| `expiry_alert` | هشدار انقضا | مدیر | push |
| `transfer_request` | درخواست انتقال | فروشگاه مقصد | both |
| `low_stock` | کمبود موجودی | انباردار | push |
| `journal_error` | خطای توازن سند | حسابدار | both |
| `order_approved` | تأیید سفارش | فروشگاه | both |
| `order_rejected` | رد سفارش | فروشگاه | both |
| `payment_success` | تأیید پرداخت | فروشگاه | both |
| `tier_upgrade` | ارتقاء لایه | فروشگاه | push |
| `draft_rejected` | رد پیش‌نویس | عامل | both |

---

**پایان فایل Enums**
