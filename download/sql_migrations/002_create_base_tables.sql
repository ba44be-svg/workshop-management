-- ============================================================
-- 002_create_base_tables.sql
-- گروه ۱: جداول پایه (۶ جدول)
-- Products, ProductCategories, Stores, Distributors, Customers, Accounts
-- ============================================================

-- =====================================================
-- 1. ProductCategories — دسته‌بندی محصولات (درختی)
-- =====================================================
CREATE TABLE product_categories (
    id              BIGSERIAL PRIMARY KEY,
    code            VARCHAR(50) NOT NULL UNIQUE,
    name            VARCHAR(200) NOT NULL,
    parent_id       BIGINT REFERENCES product_categories(id) ON DELETE CASCADE,
    level           SMALLINT NOT NULL DEFAULT 1,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by      BIGINT, -- FK to Users (جدول ۰۰۷)
    deleted_at      TIMESTAMPTZ,
    CONSTRAINT chk_category_level CHECK (level BETWEEN 1 AND 5)
);

COMMENT ON TABLE product_categories IS 'دسته‌بندی محصولات با ساختار درختی';
COMMENT ON COLUMN product_categories.level IS 'سطح درخت: ۱=ریشه، ۲=زیرگروه، ۳=زیر-زیرگروه';
CREATE INDEX idx_categories_parent ON product_categories(parent_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_categories_code ON product_categories(code);

-- =====================================================
-- 2. Products — جدول محصولات
-- =====================================================
CREATE TABLE products (
    id                  BIGSERIAL PRIMARY KEY,
    code                VARCHAR(50) NOT NULL UNIQUE,
    name                VARCHAR(200) NOT NULL,
    category_id         BIGINT NOT NULL REFERENCES product_categories(id),
    unit                VARCHAR(20) NOT NULL DEFAULT 'عدد',
    shelf_life_days     SMALLINT NOT NULL,
    default_price       NUMERIC(18,4) NOT NULL,
    cost_center_id      BIGINT, -- FK to cost_centers (جدول ۰۰۵)
    barcode             VARCHAR(50) UNIQUE,
    description         TEXT,
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by          BIGINT,
    deleted_at          TIMESTAMPTZ,
    CONSTRAINT chk_shelf_life CHECK (shelf_life_days > 0),
    CONSTRAINT chk_price CHECK (default_price >= 0)
);

COMMENT ON TABLE products IS 'محصولات تولیدی با مدت ماندگاری و قیمت پایه';
COMMENT ON COLUMN products.shelf_life_days IS 'تعداد روز ماندگاری از تولید';
CREATE INDEX idx_products_category ON products(category_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_products_barcode ON products(barcode) WHERE barcode IS NOT NULL;
CREATE INDEX idx_products_name_trgm ON products USING gin (name gin_trgm_ops);

-- =====================================================
-- 3. Stores — فروشگاه‌ها (۲۰۰ فروشگاه فیزیکی)
-- =====================================================
CREATE TABLE stores (
    id                  BIGSERIAL PRIMARY KEY,
    code                VARCHAR(50) NOT NULL UNIQUE,
    name                VARCHAR(200) NOT NULL,
    address             TEXT,
    phone               VARCHAR(20),
    geo_lat             NUMERIC(10, 7),
    geo_lng             NUMERIC(10, 7),
    distributor_id      BIGINT, -- FK to distributors (پایین)
    sales_model         sales_model_enum NOT NULL DEFAULT 'consignment',
    tier                store_tier_enum NOT NULL DEFAULT 'regular',
    credit_limit        NUMERIC(18,4) NOT NULL DEFAULT 0,
    current_credit      NUMERIC(18,4) NOT NULL DEFAULT 0,
    loyalty_points      INTEGER NOT NULL DEFAULT 0,
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by          BIGINT,
    deleted_at          TIMESTAMPTZ,
    CONSTRAINT chk_credit_limit CHECK (credit_limit >= 0)
);

COMMENT ON TABLE stores IS 'فروشگاه‌های فیزیکی با مدل فروش و امتیاز وفاداری';
COMMENT ON COLUMN stores.geo_lat IS 'عرض جغرافیایی برای Heatmap';
COMMENT ON COLUMN stores.geo_lng IS 'طول جغرافیایی برای Heatmap';
CREATE INDEX idx_stores_distributor ON stores(distributor_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_stores_tier ON stores(tier) WHERE deleted_at IS NULL;
CREATE INDEX idx_stores_geo ON stores(geo_lat, geo_lng) WHERE geo_lat IS NOT NULL;

-- =====================================================
-- 4. Distributors — عوامل پخش (۳ عامل)
-- =====================================================
CREATE TABLE distributors (
    id                  BIGSERIAL PRIMARY KEY,
    code                VARCHAR(50) NOT NULL UNIQUE,
    name                VARCHAR(200) NOT NULL,
    mobile              VARCHAR(20) NOT NULL UNIQUE,
    vehicle_id          BIGINT, -- FK به جدول vehicles (در فایل ۰۰۴)
    default_route_id    BIGINT, -- FK به routes (در فایل ۰۰۴)
    commission_rate     NUMERIC(5,2) NOT NULL DEFAULT 5.00,
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by          BIGINT,
    deleted_at          TIMESTAMPTZ,
    CONSTRAINT chk_commission CHECK (commission_rate BETWEEN 0 AND 50)
);

COMMENT ON TABLE distributors IS 'عوامل پخش با درصد پورسانت و مسیر پیش‌فرض';
CREATE INDEX idx_distributors_mobile ON distributors(mobile);

-- به‌روزرسانی FK stores.distributor_id
ALTER TABLE stores
    ADD CONSTRAINT fk_stores_distributor
    FOREIGN KEY (distributor_id) REFERENCES distributors(id);

-- =====================================================
-- 5. Customers — مشتریان آنلاین (اینستاگرام، سایت، اسنپ‌فود)
-- =====================================================
CREATE TABLE customers (
    id                  BIGSERIAL PRIMARY KEY,
    type                VARCHAR(20) NOT NULL,
    name                VARCHAR(200) NOT NULL,
    phone               VARCHAR(20),
    platform            VARCHAR(50), -- instagram, snapp, website, etc.
    platform_user_id    VARCHAR(200),
    credit_limit        NUMERIC(18,4) NOT NULL DEFAULT 0,
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by          BIGINT,
    deleted_at          TIMESTAMPTZ,
    CONSTRAINT chk_customer_type CHECK (type IN ('individual', 'business', 'platform'))
);

COMMENT ON TABLE customers IS 'مشتریان آنلاین از پلتفرم‌های مختلف';
CREATE INDEX idx_customers_platform ON customers(platform) WHERE platform IS NOT NULL;

-- =====================================================
-- 6. Accounts — کدینگ حساب‌ها (درختی با ۵ نوع اصلی)
-- =====================================================
CREATE TABLE accounts (
    id                  BIGSERIAL PRIMARY KEY,
    code                VARCHAR(20) NOT NULL UNIQUE,
    name                VARCHAR(200) NOT NULL,
    type                account_type_enum NOT NULL,
    parent_id           BIGINT REFERENCES accounts(id) ON DELETE RESTRICT,
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    is_postable         BOOLEAN NOT NULL DEFAULT TRUE,
    description         TEXT,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by          BIGINT,
    deleted_at          TIMESTAMPTZ,
    CONSTRAINT chk_code_format CHECK (code ~ '^[0-9]+$')
);

COMMENT ON TABLE accounts IS 'کدینگ درختی حساب‌ها با ۵ نوع اصلی';
COMMENT ON COLUMN accounts.is_postable IS 'اگر FALSE یعنی گروه است و قابل ثبت سند نیست';
CREATE INDEX idx_accounts_parent ON accounts(parent_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_accounts_type ON accounts(type) WHERE deleted_at IS NULL;

-- پایان فایل 002
