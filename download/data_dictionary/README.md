# Data Dictionary — فرهنگ داده‌های نسخه ۲.۰

> توضیح فیلد به فیلد تمام ۴۹ جدول پایگاه داده

## 📦 محتویات

```
data_dictionary/
├── README.md                           # این فایل — فهرست و راهنما
├── 01_base_tables.md                   # ۶ جدول پایه
├── 02_inventory_tables.md              # ۷ جدول انبار و تولید
├── 03_sales_tables.md                   # ۱۲ جدول فروش و پخش
├── 04_accounting_tables.md              # ۶ جدول حسابداری
├── 05_mobile_portal_tables.md          # ۸ جدول موبایل و پرداخت (جدید)
├── 06_system_tables.md                  # ۱۰ جدول سیستمی
├── 07_enums_reference.md                # تمام ENUM type‌ها
└── 08_relationships.md                  # روابط کلیدی ERD
```

## 📊 خلاصه جداول

| گروه | تعداد جدول | شرح |
|------|----------|------|
| ۱. پایه | ۶ | Products, ProductCategories, Stores, Distributors, Customers, Accounts |
| ۲. انبار و تولید | ۷ | Warehouses, InventoryLots, InventoryMovements, StockBalances, ProductionBatches, ProductionConsumption, ProductionOutputs |
| ۳. فروش و پخش | ۱۲ | DispatchHeaders/Lines, SalesHeaders/Lines, ReturnHeaders/Lines, TransferHeaders/Lines, Routes, Vehicles, PricingRules, SalesPersonVisits |
| ۴. حسابداری | ۶ | JournalHeaders, JournalLines, FiscalPeriods, CostCenters, JournalTemplates, ExchangeRates |
| ۵. موبایل و پرداخت | ۸ | SalesDraftHeaders/Lines, ApprovalQueue, StoreOrders/Lines, PaymentTransactions, TaxInvoices, Barcodes |
| ۶. سیستمی | ۱۰ | Users, Roles, Permissions, UserProfiles, ActivityLogs, SmsTemplates, SmsQueue, PushNotifications, NotificationSchedules, LoyaltyTransactions |
| **مجموع** | **۴۹** | |

## 🎯 نحوه استفاده از Data Dictionary

هر فیلد در این فرهنگ به فرمت زیر توضیح داده شده:

| فیلد | نوع | nullable | پیش‌فرض | توضیح |
|------|------|----------|---------|------|
| `id` | BIGSERIAL | NO | auto | کلید اصلی |
| `name` | VARCHAR(200) | NO | — | نام |

### تخلص‌ها
- **nullable: NO** = فیلد اجباری
- **nullable: YES** = فیلد اختیاری (می‌تونه NULL باشه)
- **پیش‌فرض**: مقدار پیش‌فرض هنگام INSERT اگر فیلد مقداردهی نشه

## 🔑 قراردادهای طراحی

### ۱. کلید اصلی
همه جداول از `BIGSERIAL PRIMARY KEY` با نام `id` استفاده می‌کنند (auto-increment).

### ۲. Audit Trail
همه جداول اصلی این فیلدها را دارند:
- `created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()` — زمان ساخت
- `updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()` — زمان آخرین به‌روزرسانی
- `created_by BIGINT` — کاربری که رکورد را ساخته (FK به users)
- `deleted_at TIMESTAMPTZ` — Soft Delete (در صورت پاک کردن، این فیلد پر می‌شه)

### ۳. کلید خارجی (Foreign Key)
- نام‌گذاری: `<entity>_id` (مثلاً `store_id`, `product_id`)
- سیاست DELETE: `ON DELETE RESTRICT` به‌طور پیش‌فرض (جلوگیری از حذف رکورد ارجاع‌شده)
- در روابط خاص: `ON DELETE CASCADE` (مثلاً در Header-Line)

### ۴. ایندکس‌ها
- ایندکس روی کلید خارجی: همیشه
- ایندکس روی `deleted_at IS NULL`: برای جداول با Soft Delete
- ایندکس مرکب: برای کوئری‌های پرتکرار (مثلاً FEFO)

### ۵. محدودیت‌ها (Constraints)
- `UNIQUE`: برای کدهای یکتا (مثلاً `code`, `username`)
- `CHECK`: برای اعتبارسنجی مقدار (مثلاً `qty > 0`)
- `FOREIGN KEY`: برای روابط

## 🔗 ارتباط با سایر Artifactها

| Artifact | مسیر |
|---------|------|
| سند معماری PDF | `../bakery_erd_doc_v2.pdf` |
| SQL Migrations | `../sql_migrations/` (کد واقعی) |
| Django Starter | `../django_starter/` (Django Models) |
| API Specification | `../api_spec/` (Schemas) |

## 📋 گام‌های بعدی

پس از مطالعه این Data Dictionary:
1. تیم توسعه می‌تونه با درک کامل ساختار، شروع به توسعه Django Models کنه
2. تیم DB می‌تونه ایندکس‌های اضافی را بر اساس نیازهای کوئری اضافه کنه
3. تیم API می‌تونه Serializer‌های متناسب با هر جدول بسازه
4. در طول توسعه، اگر فیلد جدیدی اضافه بشه، این Data Dictionary باید به‌روز بشه

## 🔍 جستجوی سریع

برای پیدا کردن سریع یک جدول:

```bash
# در Linux/Mac
grep -l "table_name" *.md

# مثال: پیدا کردن همه ارجاعات به users
grep "users" *.md | head -20
```

یا می‌تونی فهرست زیر رو بررسی کنی و فایل مربوطه رو باز کنی.

## 📋 فهرست جداول (الفبایی)

| # | نام جدول | گروه | فایل توضیح |
|---|---------|------|---------|
| ۱ | accounts | ۴ | 04_accounting_tables.md |
| ۲ | accounts.activity_logs | ۶ | 06_system_tables.md |
| ۳ | accounts (Django auth) | ۶ | 06_system_tables.md |
| ۴ | approval_queue | ۵ | 05_mobile_portal_tables.md |
| ۵ | barcodes | ۵ | 05_mobile_portal_tables.md |
| ۶ | barcode_scans | ۵ | 05_mobile_portal_tables.md |
| ۷ | celery_groupmeta | ۶ | 06_system_tables.md |
| ۸ | celery_taskmeta | ۶ | 06_system_tables.md |
| ۹ | cost_centers | ۴ | 04_accounting_tables.md |
| ۱۰ | customers | ۱ | 01_base_tables.md |
| ۱۱ | dispatch_headers | ۳ | 03_sales_tables.md |
| ۱۲ | dispatch_lines | ۳ | 03_sales_tables.md |
| ۱۳ | django_session | ۶ | 06_system_tables.md |
| ۱۴ | exchange_rates | ۴ | 04_accounting_tables.md |
| ۱۵ | fiscal_periods | ۴ | 04_accounting_tables.md |
| ۱۶ | inventory_lots | ۲ | 02_inventory_tables.md |
| ۱۷ | inventory_movements | ۲ | 02_inventory_tables.md |
| ۱۸ | journal_headers | ۴ | 04_accounting_tables.md |
| ۱۹ | journal_lines | ۴ | 04_accounting_tables.md |
| ۲۰ | journal_templates | ۴ | 04_accounting_tables.md |
| ۲۱ | loyalty_transactions | ۶ | 06_system_tables.md |
| ۲۲ | notification_schedules | ۶ | 06_system_tables.md |
| ۲۳ | payment_transactions | ۵ | 05_mobile_portal_tables.md |
| ۲۴ | pricing_rules | ۳ | 03_sales_tables.md |
| ۲۵ | product_categories | ۱ | 01_base_tables.md |
| ۲۶ | products | ۱ | 01_base_tables.md |
| ۲۷ | production_batches | ۲ | 02_inventory_tables.md |
| ۲۸ | production_consumption | ۲ | 02_inventory_tables.md |
| ۲۹ | production_outputs | ۲ | 02_inventory_tables.md |
| ۳۰ | push_notifications | ۶ | 06_system_tables.md |
| ۳۱ | return_headers | ۳ | 03_sales_tables.md |
| ۳۲ | return_lines | ۳ | 03_sales_tables.md |
| ۳۳ | role_permissions | ۶ | 06_system_tables.md |
| ۳۴ | roles | ۶ | 06_system_tables.md |
| ۳۵ | routes | ۳ | 03_sales_tables.md |
| ۳۶ | sales_draft_headers | ۵ | 05_mobile_portal_tables.md |
| ۳۷ | sales_draft_lines | ۵ | 05_mobile_portal_tables.md |
| ۳۸ | sales_headers | ۳ | 03_sales_tables.md |
| ۳۹ | sales_lines | ۳ | 03_sales_tables.md |
| ۴۰ | salesperson_visits | ۳ | 03_sales_tables.md |
| ۴۱ | sms_queue | ۶ | 06_system_tables.md |
| ۴۲ | sms_templates | ۶ | 06_system_tables.md |
| ۴۳ | stock_balances | ۲ | 02_inventory_tables.md |
| ۴۴ | store_orders | ۵ | 05_mobile_portal_tables.md |
| ۴۵ | store_order_lines | ۵ | 05_mobile_portal_tables.md |
| ۴۶ | stores | ۱ | 01_base_tables.md |
| ۴۷ | tax_invoices | ۵ | 05_mobile_portal_tables.md |
| ۴۸ | transfer_headers | ۳ | 03_sales_tables.md |
| ۴۹ | transfer_lines | ۳ | 03_sales_tables.md |
| اضافی | users | ۶ | 06_system_tables.md |
| اضافی | user_profiles | ۶ | 06_system_tables.md |
| اضافی | user_roles | ۶ | 06_system_tables.md |
| اضافی | vehicles | ۳ | 03_sales_tables.md |
| اضافی | warehouses | ۲ | 02_inventory_tables.md |
| اضافی | permissions | ۶ | 06_system_tables.md |

> نکته: شماره‌گذاری از ۱ تا ۴۹ هست. جدول‌های اضافی (دسترسی سریع، رابط، کمکی) در شمارش اصلی حساب نمی‌شوند.

---

**نسخه:** 2.0.0 | **تاریخ:** 1404 | **توسعه توسط:** تیم ارشد مهندسی نرم‌افزار
