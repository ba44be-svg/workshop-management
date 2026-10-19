# SQL Migration Scripts — نرم‌افزار مدیریت تولید و پخش کارگاه‌های تولیدی

> نسخه ۲.۰ — شامل ۴۹ جدول PostgreSQL با Indexes، Triggers و داده‌های اولیه

## 📦 محتویات

این پوشه شامل ۱۰ فایل SQL + Makefile است که به‌ترتیب زیر اجرا می‌شوند:

| فایل | شرح | تعداد جدول |
|------|------|----------|
| `001_create_extensions.sql` | نصب extension‌ها و تعریف ENUM type‌ها | — |
| `002_create_base_tables.sql` | جداول پایه | ۶ |
| `003_create_inventory_tables.sql` | انبار و تولید | ۷ |
| `004_create_sales_tables.sql` | فروش و پخش | ۱۲ |
| `005_create_accounting_tables.sql` | حسابداری دوطرفه | ۶ |
| `006_create_mobile_portal_tables.sql` | موبایل، پورتال و پرداخت (جدید) | ۸ |
| `007_create_system_tables.sql` | کاربران، اعلان، وفاداری | ۱۰ |
| `008_create_indexes.sql` | ایندکس‌های عملکرد | — |
| `009_create_triggers.sql` | Triggers و Functions | — |
| `010_seed_initial_data.sql` | داده‌های اولیه | — |

**مجموع: ۴۹ جدول اصلی + چندین جدول کمکی**

## 🚀 شروع سریع

### روش ۱: استفاده از Makefile (توصیه می‌شود)

```bash
# ۱. متغیرهای محیطی رو تنظیم کن (اختیاری)
export DB_NAME=workshop_db
export DB_USER=workshop_user
export DB_PASSWORD=workshop_password
export DB_HOST=localhost
export DB_PORT=5432

# ۲. ساخت دیتابیس و اجرای همه migrationها + seed
make init

# یا به‌صورت مرحله‌ای:
make migrate    # فقط migrationها
make seed       # فقط داده‌های اولیه

# ۳. ورود به psql برای بررسی
make psql

# ۴. تأیید ساختار دیتابیس
make verify
```

### روش ۲: اجرای دستی

```bash
# ۱. ساخت کاربر و دیتابیس
sudo -u postgres psql -c "CREATE USER workshop_user WITH PASSWORD 'workshop_password';"
sudo -u postgres psql -c "CREATE DATABASE workshop_db WITH OWNER workshop_user ENCODING 'UTF8';"

# ۲. اجرای migrationها به‌ترتیب
for f in 001_*.sql 002_*.sql 003_*.sql 004_*.sql 005_*.sql \
         006_*.sql 007_*.sql 008_*.sql 009_*.sql 010_*.sql; do
    PGPASSWORD=workshop_password psql -h localhost -U workshop_user -d workshop_db -1 -f $f
done
```

### روش ۳: با Docker Compose

```bash
# راه‌اندازی PostgreSQL در Docker
make docker-up
# این دستور به‌طور خودکار migrationها و seed رو اجرا می‌کنه
```

## ✅ تأیید نصب

پس از اجرای `make init`، با `make verify` ساختار رو تأیید کنید. خروجی مورد انتظار:

```
table_count = 49 (یا بیشتر به‌خاطر جداول رابط)
users_count = 5 (admin + 4 کاربر نمونه)
products_count = 30
stores_count = 10
```

## 📊 جداول اصلی

### گروه ۱: جداول پایه (۶)
- `products` — ۳۰+ محصول با بارکد و مدت ماندگاری
- `product_categories` — دسته‌بندی درختی
- `stores` — ۲۰۰+ فروشگاه با GPS و امتیاز وفاداری
- `distributors` — عوامل پخش با مسیر و پورسانت
- `customers` — مشتریان آنلاین از پلتفرم‌های مختلف
- `accounts` — کدینگ درختی حساب‌ها (۵ نوع: دارایی، بدهی، سرمایه، درآمد، هزینه)

### گروه ۲: انبار و تولید (۷)
- `warehouses` — انبار اصلی + مجازی هر فروشگاه
- `inventory_lots` — لات‌ها با تاریخ انقضا (FEFO)
- `inventory_movements` — تاریخچه حرکت‌ها
- `stock_balances` — موجودی تجمیعی (Cache)
- `production_batches` — بچ‌های تولید
- `production_consumption` — مصرف مواد اولیه
- `production_outputs` — خروج محصول نهایی

### گروه ۳: فروش و پخش (۱۲)
- `dispatch_headers` / `dispatch_lines` — سند پخش به عامل
- `sales_headers` / `sales_lines` — سند فروش (امانی/قطعی)
- `return_headers` / `return_lines` — برگشت از فروشگاه
- `transfer_headers` / `transfer_lines` — انتقال بین دو فروشگاه
- `routes` — مسیرهای هر عامل در روز هفته
- `vehicles` — خودروهای پخش
- `pricing_rules` — قیمت‌گذاری پویا بر اساس لایه
- `salesperson_visits` — ردیابی سرکشی روزانه

### گروه ۴: حسابداری (۶)
- `journal_headers` / `journal_lines` — سند حسابداری دوطرفه
- `fiscal_periods` — دوره‌های مالی قابل بستن
- `cost_centers` — مرکز هزینه برای تحلیل سود/زیان
- `journal_templates` — قالب‌های سند خودکار
- `exchange_rates` — نرخ ارز

### گروه ۵: موبایل، پورتال و پرداخت (۸ جدول جدید)
- `sales_draft_headers` / `sales_draft_lines` — پیش‌نویس فروش عامل
- `approval_queue` — صف تأیید مدیر
- `store_orders` / `store_order_lines` — سفارش فروشگاه
- `payment_transactions` — تراکنش‌های پرداخت آنلاین
- `tax_invoices` — صورتحساب الکترونیکی سامان
- `barcodes` — بارکد و QR Code

### گروه ۶: سیستمی (۱۰ + جداول رابط)
- `users` / `roles` / `permissions` — احراز هویت و RBAC
- `user_profiles` / `user_roles` / `role_permissions` — پروفایل و نقش‌ها
- `activity_logs` — لاگ فعالیت‌ها برای Audit Trail
- `sms_templates` / `sms_queue` / `push_notifications` / `notification_schedules` — اعلان
- `loyalty_transactions` — تراکنش‌های وفاداری

## 🔧 Triggers و Functions مهم

| نام | عملکرد |
|------|------|
| `check_journal_balance()` | تضمین توازن سند حسابداری در سطح DB |
| `update_weighted_avg()` | محاسبه میانگین موزون پس از هر ورود کالا |
| `update_stock_balance()` | به‌روزرسانی خودکار موجودی تجمیعی |
| `add_loyalty_points_after_sale()` | افزودن امتیاز وفاداری پس از هر فروش |
| `check_store_credit()` | کنترل سقف اعتبار فروشگاه قبل از تأیید سفارش |
| `flag_expired_lots()` | علامت‌گذاری لات‌های منقضی |
| `generate_doc_number()` | تولید شماره سند خودکار |
| `update_updated_at()` | خودکارسازی فیلد updated_at |

## 🎯 کوئری‌های پرکاربرد

### ۱. انتخاب لات‌ها بر اساس FEFO
```sql
SELECT id, batch_no, expiry_date, current_qty, weighted_avg_cost
FROM inventory_lots
WHERE product_id = 1
  AND warehouse_id = 1
  AND current_qty > 0
  AND status = 'active'
  AND expiry_date > CURRENT_DATE
ORDER BY expiry_date, production_date;
```

### ۲. مانده حساب هر فروشگاه
```sql
SELECT s.code, s.name,
       COALESCE(SUM(sh.total_amount), 0) AS total_sales,
       COALESCE(SUM(pt.amount), 0) FILTER (WHERE pt.status = 'verified') AS total_paid
FROM stores s
LEFT JOIN sales_headers sh ON sh.store_id = s.id AND sh.status = 'posted'
LEFT JOIN payment_transactions pt ON pt.store_id = s.id
GROUP BY s.code, s.name;
```

### ۳. گزارش ضایعات ماهانه
```sql
SELECT DATE_TRUNC('month', end_at) AS month,
       product_id, p.name,
       SUM(waste_qty) AS total_waste,
       SUM(actual_qty) AS total_produced,
       ROUND(SUM(waste_qty) * 100.0 / SUM(actual_qty), 2) AS waste_pct
FROM production_batches pb
JOIN products p ON p.id = pb.product_id
WHERE pb.status = 'completed'
  AND pb.end_at >= date_trunc('month', CURRENT_DATE) - INTERVAL '6 months'
GROUP BY month, product_id, p.name
ORDER BY month DESC, waste_pct DESC;
```

### ۴. لات‌های در حال انقضا (برای Transfer Suggester)
```sql
SELECT il.id, p.name AS product_name, s.name AS store_name,
       il.expiry_date, il.current_qty,
       (il.expiry_date - CURRENT_DATE) AS days_to_expiry
FROM inventory_lots il
JOIN products p ON p.id = il.product_id
JOIN warehouses w ON w.id = il.warehouse_id
JOIN stores s ON s.id = w.store_id
WHERE il.expiry_date <= CURRENT_DATE + INTERVAL '5 days'
  AND il.current_qty > 0
  AND il.status = 'active'
ORDER BY il.expiry_date;
```

## 📋 نکات مهم

### ۱. امنیت در Production
- ⚠️ حتماً رمز عبور پیش‌فرض `admin` رو تغییر بده
- 🔒 از متغیرهای environment برای credentials استفاده کن
- 🔥 `is_superuser=TRUE` رو فقط برای admin واقعی نگه دار

### ۲. Performance
- ایندکس‌های `CONCURRENTLY` ساخته شده‌اند (عدم قفل‌گذاری جدول)
- کوئری‌های FEFO از Index `idx_lots_fefo` استفاده می‌کنند
- گزارش‌های ماهانه از Index `idx_daily_sales_summary` بهره می‌برند

### ۳. Maintenance
- 📅 هر شب `flag_expired_lots()` رو اجرا کن (با Celery Beat)
- 🗑️ Soft Delete فعال است — هیچ داده‌ای فیزیکی حذف نمی‌شود
- 💾 بکاپ روزانه با `make backup`

### ۴. Docker Compose
اگر از Docker استفاده می‌کنی، فایل `docker-compose.yml` اینجاست:

```yaml
version: '3.8'
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: workshop_db
      POSTGRES_USER: workshop_user
      POSTGRES_PASSWORD: workshop_password
    ports: ['5432:5432']
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./sql_migrations:/docker-entrypoint-initdb.d
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U workshop_user -d workshop_db"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
```

## 🔗 ارتباط با سایر Artifactها

این migrationها بر اساس سند معماری نسخه ۲.۰ ساخته شده‌اند:

- 📄 [سند معماری نسخه ۲.۰ (PDF)](../bakery_erd_doc_v2.pdf) — طراحی مفهومی
- 📝 [سند معماری نسخه ۲.۰ (HTML)](../bakery_erd_doc_v2.html) — قابل ویرایش
- 📋 [نسخه Word](../bakery_erd_doc_v2.docx) — برای تیم فنی

## 🐞 رفع مشکلات

### خطای "Permission denied for relation"
```sql
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO workshop_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO workshop_user;
```

### خطای "Trigger function not found"
ترتیب اجرای فایل‌ها مهم است. حتماً `001` اول اجرا بشه.

### خطای "Circular foreign key"
این فایل‌ها به‌گونه‌ای طراحی شده‌اند که FK های circular با ALTER TABLE اضافه می‌شوند تا مشکل پیش نیاید.

## 📞 پشتیبانی

برای سؤالات فنی یا گزارش باگ، با تیم توسعه در ارتباط باشید.

---

**نسخه:** ۲.۰ | **تاریخ:** ۱۴۰۴ | **توسعه توسط:** تیم ارشد مهندسی نرم‌افزار
