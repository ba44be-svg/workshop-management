-- ============================================================
-- 008_create_indexes.sql
-- ایندکس‌های عملکرد برای کوئری‌های پرتکرار
-- ============================================================
-- این فایل بعد از ساخت همه جداول اجرا بشه

-- =====================================================
-- Indexes برای FEFO (مهم‌ترین کوئری سیستم)
-- =====================================================

-- کوئری: انتخاب لات‌های فعال بر اساس تاریخ انقضا
-- ایندکس idx_lots_fefo در فایل ۰۰۳ ساخته شده

-- Index برای جستجوی لات‌های در حال انقضا (برای Transfer Suggester)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_lots_near_expiry
    ON inventory_lots(product_id, expiry_date)
    WHERE status = 'active' AND current_qty > 0 AND deleted_at IS NULL;

-- Index برای محاسبه میانگین فروش روزانه (Smart Reorder)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sales_lines_reorder
    ON sales_lines(product_id, sale_id);

-- =====================================================
-- Indexes برای گزارش‌گیری حسابداری
-- ============================================================

-- کوئری: تراز آزمایشی (Trial Balance)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_journal_lines_account_date
    ON journal_lines(account_id, journal_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_journal_headers_date_status
    ON journal_headers(date, status)
    WHERE deleted_at IS NULL;

-- کوئری: گردش حساب هر فروشگاه
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sales_store_date_status
    ON sales_headers(store_id, sale_date, status)
    WHERE deleted_at IS NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_payment_store_date
    ON payment_transactions(store_id, paid_at)
    WHERE status = 'verified';

-- =====================================================
-- Indexes برای Approval Workflow (تست‌های بحرانی)
-- ============================================================

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_approval_pending_priority
    ON approval_queue(status, priority, requested_at)
    WHERE status = 'pending';

-- =====================================================
-- Indexes برای گزارش‌های فروش و Heatmap
-- ============================================================

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sales_date_type
    ON sales_headers(sale_date, sales_type)
    WHERE deleted_at IS NULL AND status = 'posted';

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_dispatch_distributor_date
    ON dispatch_headers(distributor_id, dispatch_date)
    WHERE deleted_at IS NULL;

-- =====================================================
-- Indexes برای push notification (شمارش Unread)
-- ============================================================

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_push_user_unread
    ON push_notifications(user_id, scheduled_at)
    WHERE status NOT IN ('read', 'failed');

-- =====================================================
-- Indexes برای Activity Log (پرس‌وجوی اخیر)
-- ============================================================

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_activity_logs_recent
    ON activity_logs(user_id, created_at DESC);

-- =====================================================
-- Indexes برای جستجوی Full-Text روی محصولات
-- ============================================================

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_products_search
    ON products
    USING gin (to_tsvector('simple', name))
    WHERE deleted_at IS NULL AND is_active = TRUE;

-- =====================================================
-- Partial Indexes برای Soft Delete
-- ============================================================

-- (در فایل‌های قبلی ساخته شده ولی اینجا تأیید می‌کنیم)
-- اکثر کوئری‌ها فیلتر deleted_at IS NULL دارند،
-- ایندکس‌های Partial فقط روی داده‌های فعال ساخته می‌شن.

-- =====================================================
-- Indexes برای Multi-Tenant (در صورت توسعه آینده)
-- ============================================================
-- در نسخه فعلی Multi-Tenant نیستیم اما این Indexها برای آینده آماده‌ست

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_stores_active_geo
    ON stores(geo_lat, geo_lng)
    WHERE is_active = TRUE AND deleted_at IS NULL;

-- =====================================================
-- Composite Indexes برای گزارش‌های تحلیلی
-- ============================================================

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_daily_sales_summary
    ON sales_headers(sale_date, store_id, sales_type)
    WHERE deleted_at IS NULL AND status = 'posted';

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_daily_dispatch_summary
    ON dispatch_headers(dispatch_date, distributor_id)
    WHERE deleted_at IS NULL;

-- =====================================================
-- Indexes برای ProductionBatches (Query عملکرد تولید)
-- ============================================================

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_batches_status_date
    ON production_batches(status, start_at)
    WHERE deleted_at IS NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_lots_active_by_expiry
    ON inventory_lots(expiry_date, current_qty)
    WHERE status = 'active' AND deleted_at IS NULL;

-- پایان فایل 008
