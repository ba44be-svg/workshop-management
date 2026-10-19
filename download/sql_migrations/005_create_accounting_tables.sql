-- ============================================================
-- 005_create_accounting_tables.sql
-- گروه ۴: حسابداری (۶ جدول)
-- JournalHeaders, JournalLines, FiscalPeriods, CostCenters,
-- JournalTemplates, ExchangeRates
-- ============================================================

-- =====================================================
-- 26. CostCenters — مرکز هزینه (درختی)
-- =====================================================
CREATE TABLE cost_centers (
    id                  BIGSERIAL PRIMARY KEY,
    code                VARCHAR(50) NOT NULL UNIQUE,
    name                VARCHAR(200) NOT NULL,
    parent_id           BIGINT REFERENCES cost_centers(id),
    type                VARCHAR(50) NOT NULL, -- production, dept, warehouse, etc.
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by          BIGINT,
    deleted_at          TIMESTAMPTZ
);

COMMENT ON TABLE cost_centers IS 'مرکز هزینه برای تحلیل سود/زیان دقیق';
CREATE INDEX idx_cost_centers_parent ON cost_centers(parent_id) WHERE deleted_at IS NULL;

-- به‌روزرسانی FK در products
ALTER TABLE products
    ADD CONSTRAINT fk_products_cost_center
    FOREIGN KEY (cost_center_id) REFERENCES cost_centers(id);

-- =====================================================
-- 27. FiscalPeriods — دوره‌های مالی
-- =====================================================
CREATE TABLE fiscal_periods (
    id                  BIGSERIAL PRIMARY KEY,
    name                VARCHAR(100) NOT NULL,
    type                fiscal_period_type_enum NOT NULL,
    start_date          DATE NOT NULL,
    end_date            DATE NOT NULL,
    is_closed           BOOLEAN NOT NULL DEFAULT FALSE,
    closed_at           TIMESTAMPTZ,
    closed_by           BIGINT,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_period_dates CHECK (end_date > start_date),
    UNIQUE (name)
);

COMMENT ON TABLE fiscal_periods IS 'دوره‌های مالی قابل بستن';
CREATE INDEX idx_fiscal_periods_dates ON fiscal_periods(start_date, end_date);

-- =====================================================
-- 28. JournalTemplates — قالب‌های سند خودکار
-- =====================================================
CREATE TABLE journal_templates (
    id                  BIGSERIAL PRIMARY KEY,
    name                VARCHAR(200) NOT NULL,
    source_type         VARCHAR(50) NOT NULL, -- sale, purchase, transfer, return, payment
    template_json       JSONB NOT NULL, -- {debit_accounts: [...], credit_accounts: [...]}
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by          BIGINT,
    deleted_at          TIMESTAMPTZ,
    CONSTRAINT chk_source_type CHECK (source_type IN
        ('sale', 'purchase', 'transfer', 'return', 'payment', 'production', 'manual'))
);

COMMENT ON TABLE journal_templates IS 'قالب‌های سند خودکار برای یکپارچگی انبار-حسابداری';
COMMENT ON COLUMN journal_templates.template_json IS 'JSON با ساختار: {debit: [{account_code, ref_field}], credit: [...]}';
CREATE INDEX idx_templates_source ON journal_templates(source_type) WHERE deleted_at IS NULL;

-- =====================================================
-- 29. JournalHeaders — سند حسابداری دوطرفه
-- =====================================================
CREATE TABLE journal_headers (
    id                  BIGSERIAL PRIMARY KEY,
    journal_no          VARCHAR(50) NOT NULL UNIQUE,
    date                DATE NOT NULL,
    source_type         VARCHAR(50) NOT NULL, -- sale, purchase, transfer, manual, etc.
    source_id           BIGINT, -- ارجاع به سند مبدأ (مثلاً sales_headers.id)
    total_debit         NUMERIC(18,4) NOT NULL DEFAULT 0,
    total_credit        NUMERIC(18,4) NOT NULL DEFAULT 0,
    status              VARCHAR(20) NOT NULL DEFAULT 'draft',
    period_id           BIGINT REFERENCES fiscal_periods(id),
    description         TEXT,
    reversed_by_journal_id BIGINT REFERENCES journal_headers(id), -- برای سند معکوس
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by          BIGINT,
    deleted_at          TIMESTAMPTZ,
    CONSTRAINT chk_journal_status CHECK (status IN ('draft', 'posted', 'reversed', 'canceled')),
    CONSTRAINT chk_journal_balance CHECK (total_debit = total_credit)
);

COMMENT ON TABLE journal_headers IS 'سند حسابداری دوطرفه با کنترل توازن';
CREATE INDEX idx_journal_date ON journal_headers(date) WHERE deleted_at IS NULL;
CREATE INDEX idx_journal_source ON journal_headers(source_type, source_id);
CREATE INDEX idx_journal_period ON journal_headers(period_id) WHERE deleted_at IS NULL;

-- به‌روزرسانی FK های circular
ALTER TABLE sales_headers
    ADD CONSTRAINT fk_sales_journal
    FOREIGN KEY (journal_id) REFERENCES journal_headers(id);

ALTER TABLE return_headers
    ADD CONSTRAINT fk_returns_journal
    FOREIGN KEY (journal_id) REFERENCES journal_headers(id);

-- =====================================================
-- 30. JournalLines — خطوط سند حسابداری
-- =====================================================
CREATE TABLE journal_lines (
    id                  BIGSERIAL PRIMARY KEY,
    journal_id          BIGINT NOT NULL REFERENCES journal_headers(id) ON DELETE CASCADE,
    account_id          BIGINT NOT NULL REFERENCES accounts(id),
    cost_center_id      BIGINT REFERENCES cost_centers(id),
    debit               NUMERIC(18,4) NOT NULL DEFAULT 0,
    credit              NUMERIC(18,4) NOT NULL DEFAULT 0,
    description         TEXT,
    ref_doc_type        VARCHAR(50),
    ref_doc_id          BIGINT,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_debit_credit CHECK (
        (debit > 0 AND credit = 0) OR (debit = 0 AND credit > 0)
    )
);

COMMENT ON TABLE journal_lines IS 'خطوط سند حسابداری با کنترل بدهکار یا بستانکار بودن';
CREATE INDEX idx_journal_lines_journal ON journal_lines(journal_id);
CREATE INDEX idx_journal_lines_account ON journal_lines(account_id);
CREATE INDEX idx_journal_lines_cost_center ON journal_lines(cost_center_id) WHERE cost_center_id IS NOT NULL;

-- =====================================================
-- 31. ExchangeRates — نرخ ارز
-- =====================================================
CREATE TABLE exchange_rates (
    id                  BIGSERIAL PRIMARY KEY,
    currency            VARCHAR(10) NOT NULL, -- USD, EUR, etc.
    rate                NUMERIC(18,6) NOT NULL,
    effective_date      DATE NOT NULL DEFAULT CURRENT_DATE,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by          BIGINT,
    UNIQUE (currency, effective_date),
    CONSTRAINT chk_rate CHECK (rate > 0)
);

COMMENT ON TABLE exchange_rates IS 'نرخ ارز برای گزارش‌های مالی چندارزی';
CREATE INDEX idx_exchange_rates_currency ON exchange_rates(currency, effective_date);

-- پایان فایل 005
