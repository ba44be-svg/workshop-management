# گروه ۶: جداول سیستمی (۱۰ جدول)

> Users, Roles, Permissions, UserProfiles, ActivityLogs,
> SmsTemplates, SmsQueue, PushNotifications, NotificationSchedules, LoyaltyTransactions

## ۴۰. `users` — کاربران سیستم

| فیلد | نوع | nullable | پیش‌فرض | توضیح |
|------|------|----------|---------|------|
| `id` | BIGSERIAL | NO | auto | کلید اصلی |
| `username` | VARCHAR(150) | NO | — | نام کاربری یکتا |
| `email` | VARCHAR(254) | NO | — | ایمیل یکتا |
| `password` | VARCHAR(128) | NO | — | هش شده (PBKDF2) |
| `first_name` | VARCHAR(150) | YES | NULL | نام |
| `last_name` | VARCHAR(150) | YES | NULL | نام خانوادگی |
| `is_active` | BOOLEAN | NO | TRUE | فعال |
| `is_staff` | BOOLEAN | NO | FALSE | دسترسی به admin |
| `is_superuser` | BOOLEAN | NO | FALSE | دسترسی کامل |
| `last_login` | TIMESTAMPTZ | YES | NULL | آخرین ورود |
| `date_joined` | TIMESTAMPTZ | NO | NOW() | تاریخ عضویت |
| `role` | user_role_enum | NO | 'storekeeper' | manager/accountant/storekeeper/distributor/store_owner |
| `phone` | VARCHAR(20) | YES | NULL | موبایل یکتا |
| `fcm_token` | TEXT | YES | NULL | Firebase Cloud Messaging Token |

---

## ۴۱. `roles` — نقش‌ها

| فیلد | نوع | nullable | پیش‌فرض | توضیح |
|------|------|----------|---------|------|
| `id` | BIGSERIAL | NO | auto | کلید اصلی |
| `name` | VARCHAR(100) | NO | — | نام (مثلاً `مدیر`) |
| `code` | VARCHAR(50) | NO | — | کد یکتا (مثلاً `manager`) |
| `description` | TEXT | YES | NULL | توضیحات |
| `is_active` | BOOLEAN | NO | TRUE | فعال |

---

## ۴۲. `permissions` — دسترسی‌های per-action

| فیلد | نوع | nullable | پیش‌فرض | توضیح |
|------|------|----------|---------|------|
| `id` | BIGSERIAL | NO | auto | کلید اصلی |
| `code` | VARCHAR(100) | NO | — | کد یکتا (مثلاً `sales.can_approve`) |
| `name` | VARCHAR(200) | NO | — | نام |
| `description` | TEXT | YES | NULL | توضیحات |
| `is_active` | BOOLEAN | NO | TRUE | فعال |

---

## ۴۳. `user_profiles` — پروفایل‌های اضافه

| فیلد | نوع | nullable | پیش‌فرض | توضیح |
|------|------|----------|---------|------|
| `user_id` | BIGINT | NO | — | FK به users (PK) |
| `distributor_id` | BIGINT | YES | NULL | اگر نقش عامل پخش |
| `store_id` | BIGINT | YES | NULL | اگر نقش فروشگاه |
| `avatar_url` | VARCHAR(500) | YES | NULL | URL تصویر پروفایل |
| `phone_verified` | BOOLEAN | NO | FALSE | موبایل تأیید شده |
| `last_password_change` | DATE | YES | NULL | آخرین تغییر رمز |
| `two_factor_enabled` | BOOLEAN | NO | FALSE | احراز هویت دو عاملی |
| `two_factor_secret` | VARCHAR(200) | YES | NULL | رمز ۲FA |
| `notification_prefs` | JSONB | NO | {sms:true, push:true, email:false} | تنظیمات اعلان |

---

## ۴۴. `activity_logs` — لاگ فعالیت‌ها (Audit Trail)

| فیلد | نوع | nullable | پیش‌فرض | توضیح |
|------|------|----------|---------|------|
| `id` | BIGSERIAL | NO | auto | کلید اصلی |
| `user_id` | BIGINT | YES | NULL | FK به users |
| `action` | VARCHAR(50) | NO | — | create/update/delete/approve/login |
| `entity_type` | VARCHAR(50) | NO | — | product/sale/journal/... |
| `entity_id` | BIGINT | YES | NULL | شناسه موجودیت |
| `old_values` | JSONB | YES | NULL | مقادیر قبلی (در UPDATE) |
| `new_values` | JSONB | YES | NULL | مقادیر جدید |
| `ip_address` | INET | YES | NULL | IP کاربر |
| `user_agent` | TEXT | YES | NULL | User-Agent مرورگر |
| `created_at` | TIMESTAMPTZ | NO | NOW() | زمان |

---

## ۴۵. `sms_templates` — قالب‌های پیامک

| فیلد | نوع | nullable | پیش‌فرض | توضیح |
|------|------|----------|---------|------|
| `id` | BIGSERIAL | NO | auto | کلید اصلی |
| `code` | VARCHAR(50) | NO | — | کد یکتا (مثلاً `visit_reminder`) |
| `name` | VARCHAR(200) | NO | — | نام قالب |
| `template_text` | TEXT | NO | — | متن با placeholder‌های Jinja2 |
| `active` | BOOLEAN | NO | TRUE | فعال |

---

## ۴۶. `sms_queue` — صف ارسال پیامک

| فیلد | نوع | nullable | پیش‌فرض | توضیح |
|------|------|----------|---------|------|
| `id` | BIGSERIAL | NO | auto | کلید اصلی |
| `recipient` | VARCHAR(20) | NO | — | شماره موبایل گیرنده |
| `template_code` | VARCHAR(50) | YES | NULL | FK به sms_templates |
| `context_data` | JSONB | YES | NULL | داده‌های placeholder |
| `status` | notification_status_enum | NO | 'queued' | queued/sent/delivered/failed/read |
| `scheduled_at` | TIMESTAMPTZ | NO | NOW() | زمان برنامه‌ریزی |
| `sent_at` | TIMESTAMPTZ | YES | NULL | زمان ارسال |
| `delivered_at` | TIMESTAMPTZ | YES | NULL | زمان تحویل |
| `message_id` | VARCHAR(100) | YES | NULL | شناسه از پروایدر |
| `provider` | VARCHAR(20) | NO | 'kavenegar' | kavenegar/farapayamak |
| `retry_count` | INTEGER | NO | 0 | تعداد تلاش مجدد |
| `next_retry_at` | TIMESTAMPTZ | YES | NULL | زمان تلاش بعدی |
| `error_message` | TEXT | YES | NULL | خطا (در صورت ناموفق) |
| `related_user_id` | BIGINT | YES | NULL | کاربر هدف |
| `related_doc_type` | VARCHAR(50) | YES | NULL | سند مرجع |
| `related_doc_id` | BIGINT | YES | NULL | شناسه سند |

---

## ۴۷. `push_notifications` — لاگ Push Notification

| فیلد | نوع | nullable | پیش‌فرض | توضیح |
|------|------|----------|---------|------|
| `id` | BIGSERIAL | NO | auto | کلید اصلی |
| `user_id` | BIGINT | NO | — | FK به users |
| `title` | VARCHAR(200) | NO | — | عنوان |
| `body` | TEXT | NO | — | متن |
| `data` | JSONB | YES | NULL | داده‌های اضافه |
| `status` | notification_status_enum | NO | 'queued' | queued/sent/delivered/failed/read |
| `scheduled_at` | TIMESTAMPTZ | NO | NOW() | زمان برنامه‌ریزی |
| `sent_at` | TIMESTAMPTZ | YES | NULL | زمان ارسال |
| `delivered_at` | TIMESTAMPTZ | YES | NULL | زمان تحویل |
| `read_at` | TIMESTAMPTZ | YES | NULL | زمان خوانده‌شدن |
| `fcm_message_id` | VARCHAR(200) | YES | NULL | شناسه Firebase |
| `related_doc_type` | VARCHAR(50) | YES | NULL | سند مرجع |
| `related_doc_id` | BIGINT | YES | NULL | شناسه سند |

---

## ۴۸. `notification_schedules` — زمان‌بندی اعلان‌ها

| فیلد | نوع | nullable | پیش‌فرض | توضیح |
|------|------|----------|---------|------|
| `id` | BIGSERIAL | NO | auto | کلید اصلی |
| `scenario` | notification_scenario_enum | NO | — | visit_reminder/sale_confirmation/... |
| `recipient_type` | VARCHAR(50) | NO | — | distributor/store/manager |
| `recipient_id` | BIGINT | YES | NULL | شناسه گیرنده |
| `channel` | notification_channel_enum | NO | 'both' | sms/push/both |
| `cron_expression` | VARCHAR(50) | YES | NULL | برای زمان‌بندی (مثلاً `0 8 * * *` برای ۸ صبح) |
| `is_active` | BOOLEAN | NO | TRUE | فعال |
| `last_run_at` | TIMESTAMPTZ | YES | NULL | آخرین اجرا |
| `next_run_at` | TIMESTAMPTZ | YES | NULL | اجرای بعدی |

---

## ۴۹. `loyalty_transactions` — تراکنش‌های وفاداری

| فیلد | نوع | nullable | پیش‌فرض | توضیح |
|------|------|----------|---------|------|
| `id` | BIGSERIAL | NO | auto | کلید اصلی |
| `store_id` | BIGINT | NO | — | FK به stores |
| `points_change` | INTEGER | NO | — | مثبت (کسب) یا منفی (مصرف) |
| `reason` | VARCHAR(50) | NO | — | purchase/payment_ontime/no_return/tier_bonus |
| `related_doc_type` | VARCHAR(50) | YES | NULL | sale/payment |
| `related_doc_id` | BIGINT | YES | NULL | شناسه سند مرجع |
| `new_balance` | INTEGER | NO | — | امتیاز جدید پس از این تراکنش |
| `created_at` | TIMESTAMPTZ | NO | NOW() | زمان |

**نکته:** این جدول توسط Trigger `add_loyalty_points_after_sale()` به‌طور خودکار پر می‌شود.

---

## جداول اضافی Celery

### `celery_taskmeta` — نتایج Celery Tasks

| فیلد | نوع | nullable | پیش‌فرض | توضیح |
|------|------|----------|---------|------|
| `id` | BIGSERIAL | NO | auto | کلید اصلی |
| `task_id` | VARCHAR(155) | NO | — | UUID یکتای task |
| `status` | VARCHAR(50) | NO | — | SUCCESS/FAILURE/PENDING/STARTED |
| `result` | TEXT | YES | NULL | نتیجه (Pickle/JSON) |
| `date_done` | TIMESTAMPTZ | NO | NOW() | زمان اتمام |
| `traceback` | TEXT | YES | NULL | در صورت خطا |
| `name` | VARCHAR(155) | YES | NULL | نام task |
| `args` | TEXT | YES | NULL | آرگومان‌ها |
| `kwargs` | TEXT | YES | NULL | آرگومان‌های کلیدی |
| `worker` | VARCHAR(100) | YES | NULL | نام worker |
| `retries` | INTEGER | NO | 0 | تعداد تلاش مجدد |
| `queue` | VARCHAR(100) | YES | NULL | نام صف |

### `celery_groupmeta` — نتایج Celery Groups

### `django_session` — نشست‌ها

### `django_migrations` — ردیابی migrationهای Django

---

**پایان فایل گروه ۶**
