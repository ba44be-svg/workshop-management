-- ============================================================
-- 001_create_extensions.sql
-- نصب extensionهای مورد نیاز PostgreSQL
-- ============================================================

-- برای UUID‌های سفارشی (بهتر از BIGINT در برخی جاها)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- برای عملیات روی داده‌های JSONB (سامان Tax Invoiceها)
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- برای full-text search (در صورت نیاز به جستجوی محصولات)
CREATE EXTENSION IF NOT EXISTS "unaccent";

-- برای pg_trgm (جستجوی fuzzy روی نام محصولات و فروشگاه‌ها)
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- ============================================================
-- تعریف ENUM type‌های مشترک
-- ============================================================

-- نوع فروش: امانی یا قطعی
CREATE TYPE sales_type_enum AS ENUM ('consignment', 'firm');

-- وضعیت سند: pending, reviewing, approved, rejected, posted
CREATE TYPE doc_status_enum AS ENUM (
    'pending', 'reviewing', 'approved', 'rejected', 'posted',
    'in_delivery', 'received', 'canceled'
);

-- نوع حرکت انبار
CREATE TYPE movement_type_enum AS ENUM (
    'in', 'out', 'transfer', 'return', 'adjustment', 'production'
);

-- نوع حساب (کدینگ)
CREATE TYPE account_type_enum AS ENUM (
    'asset', 'liability', 'equity', 'revenue', 'expense'
);

-- نوع انبار: اصلی، فروشگاه، مجازی
CREATE TYPE warehouse_type_enum AS ENUM ('main', 'store', 'virtual');

-- لایه فروشگاه (برای Loyalty)
CREATE TYPE store_tier_enum AS ENUM ('regular', 'silver', 'gold', 'platinum');

-- مدل فروش فروشگاه
CREATE TYPE sales_model_enum AS ENUM ('consignment', 'firm', 'mixed');

-- وضعیت تراکنش پرداخت آنلاین
CREATE TYPE payment_status_enum AS ENUM (
    'initiated', 'paid', 'failed', 'verified', 'refunded'
);

-- نوع درگاه پرداخت
CREATE TYPE gateway_enum AS ENUM ('zarinpal', 'idpay', 'parsian');

-- وضعیت صورتحساب سامان
CREATE TYPE tax_invoice_status_enum AS ENUM (
    'draft', 'sent', 'confirmed', 'canceled', 'rejected'
);

-- نوع موجودیت بارکد
CREATE TYPE barcode_entity_type_enum AS ENUM (
    'product', 'lot', 'sales_order', 'store_order', 'dispatch'
);

-- شرط کالا برگشتی
CREATE TYPE return_condition_enum AS ENUM (
    'sellable', 'expired', 'damaged', 'near_expiry'
);

-- نوع کاربر
CREATE TYPE user_role_enum AS ENUM (
    'manager', 'accountant', 'storekeeper', 'distributor', 'store_owner'
);

-- اولویت تأیید
CREATE TYPE approval_priority_enum AS ENUM ('low', 'medium', 'high', 'urgent');

-- وضعیت ارسال اعلان
CREATE TYPE notification_status_enum AS ENUM (
    'queued', 'sent', 'delivered', 'failed', 'read'
);

-- نوع اعلان
CREATE TYPE notification_channel_enum AS ENUM ('sms', 'push', 'both');

-- نوع دوره مالی
CREATE TYPE fiscal_period_type_enum AS ENUM ('monthly', 'quarterly', 'yearly');

-- سناریوی قالب اعلان
CREATE TYPE notification_scenario_enum AS ENUM (
    'visit_reminder', 'sale_confirmation', 'expiry_alert',
    'transfer_request', 'low_stock', 'journal_error',
    'order_approved', 'order_rejected', 'payment_success',
    'tier_upgrade', 'draft_rejected'
);

COMMENT ON EXTENSION "uuid-ossp" IS 'تولید UUID';
COMMENT ON EXTENSION pgcrypto IS 'رمزنگاری رمز عبور و توکن‌ها';
COMMENT ON EXTENSION unaccent IS 'حذف لهجه برای full-text search';
COMMENT ON EXTENSION pg_trgm IS 'جستجوی fuzzy سه‌حرفی برای نام محصولات';

-- پایان فایل 001
