-- ============================================================
-- 007_create_system_tables.sql
-- گروه ۶: جداول سیستمی (Django Auth + Celery + Custom)
-- Users, Roles, Permissions, UserProfiles, ActivityLogs
-- + Loyalty & Notification & Report tables
-- ============================================================
-- نکته: برخی از این جداول توسط Django Auth خودکار ساخته می‌شوند
-- اما نسخه دستی زیر برای کنترل کامل ارائه می‌شه

-- =====================================================
-- 40. Users — کاربران سیستم (با تفاوت از Django Auth پیش‌فرض)
-- =====================================================
CREATE TABLE users (
    id                  BIGSERIAL PRIMARY KEY,
    username            VARCHAR(150) NOT NULL UNIQUE,
    email               VARCHAR(254) NOT NULL UNIQUE,
    password            VARCHAR(128) NOT NULL, -- هش شده
    first_name          VARCHAR(150),
    last_name           VARCHAR(150),
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    is_staff            BOOLEAN NOT NULL DEFAULT FALSE,
    is_superuser        BOOLEAN NOT NULL DEFAULT FALSE,
    last_login          TIMESTAMPTZ,
    date_joined         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    role                user_role_enum NOT NULL DEFAULT 'storekeeper',
    phone               VARCHAR(20) UNIQUE,
    fcm_token           TEXT, -- Firebase Cloud Messaging token
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE users IS 'کاربران سیستم با ۵ نقش اصلی';
CREATE INDEX idx_users_role ON users(role) WHERE is_active = TRUE;
CREATE INDEX idx_users_phone ON users(phone) WHERE phone IS NOT NULL;

-- =====================================================
-- 41. Roles — نقش‌ها
-- =====================================================
CREATE TABLE roles (
    id                  BIGSERIAL PRIMARY KEY,
    name                VARCHAR(100) NOT NULL UNIQUE,
    code                VARCHAR(50) NOT NULL UNIQUE,
    description         TEXT,
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE roles IS 'نقش‌های سیستم (manager, accountant, storekeeper, distributor, store_owner)';

-- =====================================================
-- 42. Permissions — دسترسی‌ها (per-action)
-- =====================================================
CREATE TABLE permissions (
    id                  BIGSERIAL PRIMARY KEY,
    code                VARCHAR(100) NOT NULL UNIQUE, -- e.g. 'sales.can_approve'
    name                VARCHAR(200) NOT NULL,
    description         TEXT,
    is_active           BOOLEAN NOT NULL DEFAULT TRUE
);

COMMENT ON TABLE permissions IS 'دسترسی‌های per-action (view, add, change, delete, approve)';

-- =====================================================
-- جدول رابط: RolePermissions
-- =====================================================
CREATE TABLE role_permissions (
    role_id             BIGINT NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    permission_id       BIGINT NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
    PRIMARY KEY (role_id, permission_id)
);

COMMENT ON TABLE role_permissions IS 'رابط نقش-دسترسی';

-- =====================================================
-- جدول رابط: UserRoles
-- =====================================================
CREATE TABLE user_roles (
    user_id             BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id             BIGINT NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    assigned_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    assigned_by         BIGINT REFERENCES users(id),
    PRIMARY KEY (user_id, role_id)
);

COMMENT ON TABLE user_roles IS 'رابط کاربر-نقش';

-- =====================================================
-- 43. UserProfiles — پروفایل‌های اضافه کاربر
-- =====================================================
CREATE TABLE user_profiles (
    user_id             BIGINT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    distributor_id      BIGINT REFERENCES distributors(id),
    store_id            BIGINT REFERENCES stores(id),
    avatar_url          VARCHAR(500),
    phone_verified      BOOLEAN NOT NULL DEFAULT FALSE,
    last_password_change DATE,
    two_factor_enabled  BOOLEAN NOT NULL DEFAULT FALSE,
    two_factor_secret   VARCHAR(200),
    notification_prefs JSONB NOT NULL DEFAULT '{"sms": true, "push": true, "email": false}',
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE user_profiles IS 'پروفایل اضافی کاربر با تنظیمات اعلان';

-- =====================================================
-- 44. ActivityLogs — لاگ فعالیت‌های مهم
-- =====================================================
CREATE TABLE activity_logs (
    id                  BIGSERIAL PRIMARY KEY,
    user_id             BIGINT REFERENCES users(id),
    action              VARCHAR(50) NOT NULL, -- create, update, delete, approve, login, etc.
    entity_type         VARCHAR(50) NOT NULL, -- product, sale, journal, etc.
    entity_id           BIGINT,
    old_values          JSONB,
    new_values          JSONB,
    ip_address          INET,
    user_agent          TEXT,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE activity_logs IS 'لاگ تمام فعالیت‌های مهم برای Audit Trail';
CREATE INDEX idx_logs_user ON activity_logs(user_id, created_at);
CREATE INDEX idx_logs_entity ON activity_logs(entity_type, entity_id);
CREATE INDEX idx_logs_action ON activity_logs(action, created_at);

-- =====================================================
-- 45. SmsTemplates — قالب‌های پیامک
-- =====================================================
CREATE TABLE sms_templates (
    id                  BIGSERIAL PRIMARY KEY,
    code                VARCHAR(50) NOT NULL UNIQUE,
    name                VARCHAR(200) NOT NULL,
    template_text       TEXT NOT NULL, -- با placeholder‌های Jinja2
    active              BOOLEAN NOT NULL DEFAULT TRUE,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE sms_templates IS 'قالب‌های پیامک با placeholder‌های Jinja2';

-- =====================================================
-- 46. SmsQueue — صف ارسال پیامک
-- =====================================================
CREATE TABLE sms_queue (
    id                  BIGSERIAL PRIMARY KEY,
    recipient           VARCHAR(20) NOT NULL,
    template_code       VARCHAR(50) REFERENCES sms_templates(code),
    context_data        JSONB,
    status              notification_status_enum NOT NULL DEFAULT 'queued',
    scheduled_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    sent_at             TIMESTAMPTZ,
    delivered_at        TIMESTAMPTZ,
    message_id          VARCHAR(100), -- از پروایدر
    provider            VARCHAR(20) NOT NULL DEFAULT 'kavenegar',
    retry_count         INTEGER NOT NULL DEFAULT 0,
    next_retry_at       TIMESTAMPTZ,
    error_message       TEXT,
    related_user_id     BIGINT REFERENCES users(id),
    related_doc_type    VARCHAR(50),
    related_doc_id      BIGINT
);

COMMENT ON TABLE sms_queue IS 'صف ارسال پیامک با Retry Exponential Backoff';
CREATE INDEX idx_sms_queue_pending ON sms_queue(status, scheduled_at) WHERE status IN ('queued', 'failed');
CREATE INDEX idx_sms_retry ON sms_queue(next_retry_at) WHERE next_retry_at IS NOT NULL;

-- =====================================================
-- 47. PushNotifications — لاگ Push Notificationها
-- =====================================================
CREATE TABLE push_notifications (
    id                  BIGSERIAL PRIMARY KEY,
    user_id             BIGINT NOT NULL REFERENCES users(id),
    title               VARCHAR(200) NOT NULL,
    body                TEXT NOT NULL,
    data                JSONB,
    status              notification_status_enum NOT NULL DEFAULT 'queued',
    scheduled_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    sent_at             TIMESTAMPTZ,
    delivered_at        TIMESTAMPTZ,
    read_at             TIMESTAMPTZ,
    fcm_message_id      VARCHAR(200),
    related_doc_type    VARCHAR(50),
    related_doc_id       BIGINT
);

COMMENT ON TABLE push_notifications IS 'لاگ Push Notification با Firebase';
CREATE INDEX idx_push_user_unread ON push_notifications(user_id, scheduled_at) WHERE status != 'read';

-- =====================================================
-- 48. NotificationSchedules — زمان‌بندی اعلان‌ها
-- =====================================================
CREATE TABLE notification_schedules (
    id                  BIGSERIAL PRIMARY KEY,
    scenario            notification_scenario_enum NOT NULL,
    recipient_type      VARCHAR(50) NOT NULL, -- distributor, store, manager, etc.
    recipient_id        BIGINT,
    channel             notification_channel_enum NOT NULL DEFAULT 'both',
    cron_expression     VARCHAR(50), -- برای زمان‌بندی
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    last_run_at         TIMESTAMPTZ,
    next_run_at         TIMESTAMPTZ,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE notification_schedules IS 'زمان‌بندی اعلان‌ها با Celery Beat';
CREATE INDEX idx_schedules_next_run ON notification_schedules(next_run_at) WHERE is_active = TRUE;

-- =====================================================
-- 49. LoyaltyTransactions — تراکنش‌های وفاداری
-- =====================================================
CREATE TABLE loyalty_transactions (
    id                  BIGSERIAL PRIMARY KEY,
    store_id            BIGINT NOT NULL REFERENCES stores(id),
    points_change       INTEGER NOT NULL, -- مثبت یا منفی
    reason              VARCHAR(50) NOT NULL, -- purchase, payment_ontime, no_return, tier_bonus
    related_doc_type    VARCHAR(50),
    related_doc_id      BIGINT,
    new_balance         INTEGER NOT NULL, -- امتیاز بعد از این تراکنش
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE loyalty_transactions IS 'تراکنش‌های امتیاز وفاداری هر فروشگاه';
CREATE INDEX idx_loyalty_store ON loyalty_transactions(store_id, created_at);

-- ============================================================
-- جداول Celery (برای Result Backend)
-- ============================================================
CREATE TABLE celery_taskmeta (
    id                  BIGSERIAL PRIMARY KEY,
    task_id             VARCHAR(155) NOT NULL UNIQUE,
    status              VARCHAR(50) NOT NULL,
    result             TEXT,
    date_done          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    traceback          TEXT,
    name                VARCHAR(155),
    args                TEXT,
    kwargs             TEXT,
    worker              VARCHAR(100),
    retries             INTEGER NOT NULL DEFAULT 0,
    queue               VARCHAR(100)
);

COMMENT ON TABLE celery_taskmeta IS 'نتایج Celery Tasks';
CREATE INDEX idx_celery_status ON celery_taskmeta(status, date_done);

CREATE TABLE celery_groupmeta (
    id                  BIGSERIAL PRIMARY KEY,
    group_id            VARCHAR(155) NOT NULL UNIQUE,
    result             TEXT,
    date_done          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =====================================================
-- Django Session Table (نسخه سفارشی برای کنترل بیشتر)
-- =====================================================
CREATE TABLE django_session (
    session_key         VARCHAR(40) NOT NULL PRIMARY KEY,
    session_data        TEXT NOT NULL,
    expire_date         TIMESTAMPTZ NOT NULL
);
CREATE INDEX idx_django_session_expiry ON django_session(expire_date);

-- =====================================================
-- Django Migrations Tracking
-- =====================================================
CREATE TABLE django_migrations (
    id                  BIGSERIAL PRIMARY KEY,
    app                 VARCHAR(255) NOT NULL,
    name                VARCHAR(255) NOT NULL,
    applied             TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_django_migrations_app ON django_migrations(app);

-- پایان فایل 007
