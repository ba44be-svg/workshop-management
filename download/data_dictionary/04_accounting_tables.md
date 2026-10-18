# گروه ۴: حسابداری (۶ جدول)

> JournalHeaders, JournalLines, FiscalPeriods, CostCenters,
> JournalTemplates, ExchangeRates

## ۲۶. `cost_centers` — مرکز هزینه (درختی)

| فیلد | نوع | nullable | پیش‌فرض | توضیح |
|------|------|----------|---------|------|
| `id` | BIGSERIAL | NO | auto | کلید اصلی |
| `code` | VARCHAR(50) | NO | — | کد یکتا (مثلاً `CC01`) |
| `name` | VARCHAR(200) | NO | — | نام |
| `parent_id` | BIGINT | YES | NULL | ارجاع به والد |
| `type` | VARCHAR(50) | NO | — | production/dept/warehouse/distribution/administrative |
| `is_active` | BOOLEAN | NO | TRUE | فعال |

---

## ۲۷. `fiscal_periods` — دوره‌های مالی

| فیلد | نوع | nullable | پیش‌فرض | توضیح |
|------|------|----------|---------|------|
| `id` | BIGSERIAL | NO | auto | کلید اصلی |
| `name` | VARCHAR(100) | NO | — | نام یکتا (مثلاً `فروردین ۱۴۰۴`) |
| `type` | fiscal_period_type_enum | NO | — | monthly/quarterly/yearly |
| `start_date` | DATE | NO | — | تاریخ شروع |
| `end_date` | DATE | NO | — | تاریخ پایان |
| `is_closed` | BOOLEAN | NO | FALSE | بسته شده (قفل) |
| `closed_at` | TIMESTAMPTZ | YES | NULL | زمان بستن |
| `closed_by` | BIGINT | YES | NULL | کاربر بسته‌کننده |

**نکته:** وقتی دوره بسته بشه، هیچ سند جدیدی نمی‌تونه به این دوره اضافه بشه.

---

## ۲۸. `journal_templates` — قالب‌های سند خودکار ⭐

| فیلد | نوع | nullable | پیش‌فرض | توضیح |
|------|------|----------|---------|------|
| `id` | BIGSERIAL | NO | auto | کلید اصلی |
| `name` | VARCHAR(200) | NO | — | نام قالب |
| `source_type` | VARCHAR(50) | NO | — | sale/purchase/transfer/return/payment/production/manual |
| `template_json` | JSONB | NO | — | ساختار debit/credit |
| `is_active` | BOOLEAN | NO | TRUE | فعال |

**مثال `template_json`:**
```json
{
    "context": "consignment",
    "debit": [{"account_code": "104", "ref_field": "store_id"}],
    "credit": [{"account_code": "101", "ref_field": "warehouse_id"}]
}
```

**نکته:** این جدول قلب یکپارچگی انبار-حسابداری است. وقتی فروش ثبت می‌شه، سیستم قالب مناسب را بر اساس `source_type` و `context` پیدا می‌کنه و سند حسابداری خودکار می‌سازه.

---

## ۲۹. `journal_headers` — سند حسابداری دوطرفه ⭐

| فیلد | نوع | nullable | پیش‌فرض | توضیح |
|------|------|----------|---------|------|
| `id` | BIGSERIAL | NO | auto | کلید اصلی |
| `journal_no` | VARCHAR(50) | NO | — | شماره یکتا |
| `date` | DATE | NO | — | تاریخ سند |
| `source_type` | VARCHAR(50) | NO | — | sale/purchase/transfer/manual/... |
| `source_id` | BIGINT | YES | NULL | شناسه سند مبدأ |
| `total_debit` | NUMERIC(18,4) | NO | 0 | مجموع بدهکار |
| `total_credit` | NUMERIC(18,4) | NO | 0 | مجموع بستانکار |
| `status` | VARCHAR(20) | NO | 'draft' | draft/posted/reversed/canceled |
| `period_id` | BIGINT | YES | NULL | FK به fiscal_periods |
| `description` | TEXT | YES | NULL | توضیحات |
| `reversed_by_journal_id` | BIGINT | YES | NULL | سند معکوس (Self-Reference) |

**Constraint‌ها:**
- `CHECK (total_debit = total_credit)` — ⭐ تضمین توازن در سطح DB

**نکته:** این constraint اصلی‌ترین تضمین صحت حسابداری است. Trigger `check_journal_balance()` پس از هر تغییر در `journal_lines` این چک را مجدداً انجام می‌دهد.

---

## ۳۰. `journal_lines` — خطوط سند حسابداری

| فیلد | نوع | nullable | پیش‌فرض | توضیح |
|------|------|----------|---------|------|
| `id` | BIGSERIAL | NO | auto | کلید اصلی |
| `journal_id` | BIGINT | NO | — | FK به journal_headers (CASCADE) |
| `account_id` | BIGINT | NO | — | FK به accounts |
| `cost_center_id` | BIGINT | YES | NULL | FK به cost_centers |
| `debit` | NUMERIC(18,4) | NO | 0 | مبلغ بدهکار |
| `credit` | NUMERIC(18,4) | NO | 0 | مبلغ بستانکار |
| `description` | TEXT | YES | NULL | توضیحات خط |
| `ref_doc_type` | VARCHAR(50) | YES | NULL | نوع سند مرجع |
| `ref_doc_id` | BIGINT | YES | NULL | شناسه سند مرجع |

**Constraint:**
- `CHECK ((debit > 0 AND credit = 0) OR (debit = 0 AND credit > 0))` — هر خط یا بدهکار یا بستانکار (نه هر دو)

**Trigger:** پس از INSERT/UPDATE/DELETE، Trigger `check_journal_balance()` مجموع را محاسبه و چک می‌کند.

---

## ۳۱. `exchange_rates` — نرخ ارز

| فیلد | نوع | nullable | پیش‌فرض | توضیح |
|------|------|----------|---------|------|
| `id` | BIGSERIAL | NO | auto | کلید اصلی |
| `currency` | VARCHAR(10) | NO | — | USD/EUR/... |
| `rate` | NUMERIC(18,6) | NO | — | نرخ به ریال |
| `effective_date` | DATE | NO | CURRENT_DATE | تاریخ اعتبار |
| `created_by` | BIGINT | YES | NULL | کاربر |

**Constraint:**
- `UNIQUE(currency, effective_date)`
- `CHECK (rate > 0)`

---

**پایان فایل گروه ۴**
