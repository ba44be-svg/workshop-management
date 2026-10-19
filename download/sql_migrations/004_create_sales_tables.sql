-- ============================================================
-- 004_create_sales_tables.sql
-- گروه ۳: فروش و پخش (۱۲ جدول)
-- DispatchHeaders/Lines, SalesHeaders/Lines, ReturnHeaders/Lines,
-- TransferHeaders/Lines, Routes, Vehicles, PricingRules, SalesPersonVisits
-- ============================================================

-- =====================================================
-- 14. Vehicles — خودروهای پخش
-- =====================================================
CREATE TABLE vehicles (
    id                  BIGSERIAL PRIMARY KEY,
    plate               VARCHAR(20) NOT NULL UNIQUE,
    capacity            NUMERIC(14,3) NOT NULL,
    driver_name         VARCHAR(200),
    fuel_card           VARCHAR(50),
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by          BIGINT,
    deleted_at          TIMESTAMPTZ
);

COMMENT ON TABLE vehicles IS 'خودروهای پخش با ظرفیت';

-- به‌روزرسانی FK در distributors
ALTER TABLE distributors
    ADD CONSTRAINT fk_distributors_vehicle
    FOREIGN KEY (vehicle_id) REFERENCES vehicles(id);

-- =====================================================
-- 15. Routes — مسیرهای هر عامل در هر روز هفته
-- =====================================================
CREATE TABLE routes (
    id                  BIGSERIAL PRIMARY KEY,
    distributor_id      BIGINT NOT NULL REFERENCES distributors(id),
    day_of_week         SMALLINT NOT NULL, -- 0=شنبه ... 6=جمعه
    store_sequence      JSONB NOT NULL, -- [{store_id, expected_time, ...}]
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by          BIGINT,
    deleted_at          TIMESTAMPTZ,
    UNIQUE (distributor_id, day_of_week),
    CONSTRAINT chk_day CHECK (day_of_week BETWEEN 0 AND 6)
);

COMMENT ON TABLE routes IS 'مسیر هر عامل در هر روز هفته با ترتیب فروشگاه‌ها';
CREATE INDEX idx_routes_distributor_day ON routes(distributor_id, day_of_week) WHERE deleted_at IS NULL;

-- به‌روزرسانی FK در distributors
ALTER TABLE distributors
    ADD CONSTRAINT fk_distributors_route
    FOREIGN KEY (default_route_id) REFERENCES routes(id);

-- =====================================================
-- 16. PricingRules — قیمت‌گذاری پویا بر اساس لایه فروشگاه
-- =====================================================
CREATE TABLE pricing_rules (
    id                  BIGSERIAL PRIMARY KEY,
    product_id          BIGINT NOT NULL REFERENCES products(id),
    store_tier          store_tier_enum NOT NULL,
    min_price           NUMERIC(18,4) NOT NULL,
    default_price       NUMERIC(18,4) NOT NULL,
    effective_date      DATE NOT NULL DEFAULT CURRENT_DATE,
    expires_at          DATE,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by          BIGINT,
    deleted_at          TIMESTAMPTZ,
    CONSTRAINT chk_min_le_default CHECK (min_price <= default_price),
    UNIQUE (product_id, store_tier, effective_date)
);

COMMENT ON TABLE pricing_rules IS 'قیمت‌گذاری پویا بر اساس لایه فروشگاه';
CREATE INDEX idx_pricing_lookup ON pricing_rules(product_id, store_tier, effective_date) WHERE deleted_at IS NULL;

-- =====================================================
-- 17. DispatchHeaders — سند پخش به عامل
-- =====================================================
CREATE TABLE dispatch_headers (
    id                  BIGSERIAL PRIMARY KEY,
    dispatch_no         VARCHAR(50) NOT NULL UNIQUE,
    distributor_id      BIGINT NOT NULL REFERENCES distributors(id),
    dispatch_date       DATE NOT NULL,
    total_qty           NUMERIC(14,3) NOT NULL DEFAULT 0,
    total_amount        NUMERIC(18,4) NOT NULL DEFAULT 0,
    status              doc_status_enum NOT NULL DEFAULT 'pending',
    vehicle_id          BIGINT REFERENCES vehicles(id),
    notes               TEXT,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by          BIGINT,
    deleted_at          TIMESTAMPTZ,
    CONSTRAINT chk_dispatch_status CHECK (status IN ('pending', 'in_delivery', 'arrived', 'canceled'))
);

COMMENT ON TABLE dispatch_headers IS 'سند پخش به عامل با وضعیت (pending → in_delivery → arrived)';
CREATE INDEX idx_dispatch_distributor ON dispatch_headers(distributor_id, dispatch_date) WHERE deleted_at IS NULL;
CREATE INDEX idx_dispatch_status ON dispatch_headers(status) WHERE deleted_at IS NULL;

-- =====================================================
-- 18. DispatchLines — اقلام پخش با مقصد هر فروشگاه
-- =====================================================
CREATE TABLE dispatch_lines (
    id                  BIGSERIAL PRIMARY KEY,
    dispatch_id         BIGINT NOT NULL REFERENCES dispatch_headers(id) ON DELETE CASCADE,
    product_id          BIGINT NOT NULL REFERENCES products(id),
    lot_id              BIGINT REFERENCES inventory_lots(id),
    qty                 NUMERIC(14,3) NOT NULL,
    unit_price          NUMERIC(18,4) NOT NULL,
    dest_store_id       BIGINT NOT NULL REFERENCES stores(id),
    line_total          NUMERIC(18,4) GENERATED ALWAYS AS (qty * unit_price) STORED,
    CONSTRAINT chk_dispatch_qty CHECK (qty > 0)
);

COMMENT ON TABLE dispatch_lines IS 'اقلام پخش با مقصد هر فروشگاه';
CREATE INDEX idx_dispatch_lines_dispatch ON dispatch_lines(dispatch_id);
CREATE INDEX idx_dispatch_lines_store ON dispatch_lines(dest_store_id);

-- =====================================================
-- 19. SalesHeaders — سند فروش (امانی/قطعی)
-- =====================================================
CREATE TABLE sales_headers (
    id                  BIGSERIAL PRIMARY KEY,
    sale_no             VARCHAR(50) NOT NULL UNIQUE,
    store_id            BIGINT NOT NULL REFERENCES stores(id),
    sale_date           DATE NOT NULL,
    sales_type          sales_type_enum NOT NULL,
    total_amount        NUMERIC(18,4) NOT NULL DEFAULT 0,
    total_cost          NUMERIC(18,4) NOT NULL DEFAULT 0,
    total_profit        NUMERIC(18,4) GENERATED ALWAYS AS (total_amount - total_cost) STORED,
    status              doc_status_enum NOT NULL DEFAULT 'posted',
    journal_id          BIGINT, -- FK به journal_headers (در فایل ۰۰۵)
    tax_invoice_id      BIGINT, -- FK به tax_invoices (در فایل ۰۰۶)
    dispatch_id         BIGINT REFERENCES dispatch_headers(id),
    distributor_id      BIGINT REFERENCES distributors(id),
    notes               TEXT,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by          BIGINT,
    deleted_at          TIMESTAMPTZ
);

COMMENT ON TABLE sales_headers IS 'سند فروش امانی/قطعی با ارجاع به سند حسابداری و صورتحساب سامان';
CREATE INDEX idx_sales_store_date ON sales_headers(store_id, sale_date) WHERE deleted_at IS NULL;
CREATE INDEX idx_sales_type ON sales_headers(sales_type) WHERE deleted_at IS NULL;
CREATE INDEX idx_sales_status ON sales_headers(status) WHERE deleted_at IS NULL;

-- =====================================================
-- 20. SalesLines — اقلام فروش با لات مشخص (FEFO)
-- =====================================================
CREATE TABLE sales_lines (
    id                  BIGSERIAL PRIMARY KEY,
    sale_id              BIGINT NOT NULL REFERENCES sales_headers(id) ON DELETE CASCADE,
    product_id          BIGINT NOT NULL REFERENCES products(id),
    lot_id              BIGINT REFERENCES inventory_lots(id), -- برای FEFO
    qty                 NUMERIC(14,3) NOT NULL,
    unit_price           NUMERIC(18,4) NOT NULL,
    unit_cost            NUMERIC(18,4) NOT NULL,
    line_total           NUMERIC(18,4) GENERATED ALWAYS AS (qty * unit_price) STORED,
    CONSTRAINT chk_sales_qty CHECK (qty > 0)
);

COMMENT ON TABLE sales_lines IS 'اقلام فروش با لات مشخص برای ردیابی FEFO';
CREATE INDEX idx_sales_lines_sale ON sales_lines(sale_id);
CREATE INDEX idx_sales_lines_lot ON sales_lines(lot_id);

-- =====================================================
-- 21. ReturnHeaders — برگشت از فروشگاه
-- =====================================================
CREATE TABLE return_headers (
    id                  BIGSERIAL PRIMARY KEY,
    return_no           VARCHAR(50) NOT NULL UNIQUE,
    store_id            BIGINT NOT NULL REFERENCES stores(id),
    return_date         DATE NOT NULL,
    original_sale_id    BIGINT REFERENCES sales_headers(id),
    total_qty           NUMERIC(14,3) NOT NULL DEFAULT 0,
    reason              TEXT,
    status              doc_status_enum NOT NULL DEFAULT 'pending',
    journal_id          BIGINT, -- FK به journal_headers (معکوس)
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by          BIGINT,
    deleted_at          TIMESTAMPTZ
);

COMMENT ON TABLE return_headers IS 'برگشت از فروشگاه با علت';
CREATE INDEX idx_returns_store ON return_headers(store_id, return_date) WHERE deleted_at IS NULL;
CREATE INDEX idx_returns_orig_sale ON return_headers(original_sale_id) WHERE original_sale_id IS NOT NULL;

-- =====================================================
-- 22. ReturnLines — اقلام برگشت با وضعیت
-- =====================================================
CREATE TABLE return_lines (
    id                  BIGSERIAL PRIMARY KEY,
    return_id            BIGINT NOT NULL REFERENCES return_headers(id) ON DELETE CASCADE,
    product_id           BIGINT NOT NULL REFERENCES products(id),
    lot_id               BIGINT REFERENCES inventory_lots(id),
    qty                  NUMERIC(14,3) NOT NULL,
    condition            return_condition_enum NOT NULL DEFAULT 'sellable',
    notes                TEXT,
    CONSTRAINT chk_return_qty CHECK (qty > 0)
);

COMMENT ON TABLE return_lines IS 'اقلام برگشت با وضعیت تعیین‌کننده ضایعات';
CREATE INDEX idx_return_lines_return ON return_lines(return_id);
CREATE INDEX idx_return_lines_condition ON return_lines(condition);

-- =====================================================
-- 23. TransferHeaders — انتقال بین دو فروشگاه
-- =====================================================
CREATE TABLE transfer_headers (
    id                  BIGSERIAL PRIMARY KEY,
    transfer_no         VARCHAR(50) NOT NULL UNIQUE,
    from_store_id       BIGINT NOT NULL REFERENCES stores(id),
    to_store_id         BIGINT NOT NULL REFERENCES stores(id),
    transfer_date       DATE NOT NULL,
    status              doc_status_enum NOT NULL DEFAULT 'pending',
    initiator_id        BIGINT, -- FK به users
    receiver_id         BIGINT, -- FK به users
    reason              TEXT,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by          BIGINT,
    deleted_at          TIMESTAMPTZ,
    CONSTRAINT chk_different_stores CHECK (from_store_id != to_store_id)
);

COMMENT ON TABLE transfer_headers IS 'انتقال بین دو فروشگاه با تأیید دوطرفه';
CREATE INDEX idx_transfers_stores ON transfer_headers(from_store_id, to_store_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_transfers_status ON transfer_headers(status) WHERE deleted_at IS NULL;

-- =====================================================
-- 24. TransferLines — اقلام انتقال
-- =====================================================
CREATE TABLE transfer_lines (
    id                  BIGSERIAL PRIMARY KEY,
    transfer_id          BIGINT NOT NULL REFERENCES transfer_headers(id) ON DELETE CASCADE,
    product_id           BIGINT NOT NULL REFERENCES products(id),
    lot_id               BIGINT REFERENCES inventory_lots(id),
    qty                  NUMERIC(14,3) NOT NULL,
    expiry_date          DATE,
    CONSTRAINT chk_transfer_qty CHECK (qty > 0)
);

COMMENT ON TABLE transfer_lines IS 'اقلام انتقال با لات و تاریخ انقضا';
CREATE INDEX idx_transfer_lines_transfer ON transfer_lines(transfer_id);

-- =====================================================
-- 25. SalesPersonVisits — ردیابی سرکشی روزانه عامل
-- =====================================================
CREATE TABLE salesperson_visits (
    id                  BIGSERIAL PRIMARY KEY,
    distributor_id      BIGINT NOT NULL REFERENCES distributors(id),
    store_id            BIGINT NOT NULL REFERENCES stores(id),
    visit_date          DATE NOT NULL,
    check_in_time       TIMESTAMPTZ,
    check_out_time      TIMESTAMPTZ,
    sales_count         INTEGER NOT NULL DEFAULT 0,
    sales_amount        NUMERIC(18,4) NOT NULL DEFAULT 0,
    geo_lat_checkin     NUMERIC(10, 7),
    geo_lng_checkin     NUMERIC(10, 7),
    notes               TEXT,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (distributor_id, store_id, visit_date)
);

COMMENT ON TABLE salesperson_visits IS 'ردیابی سرکشی روزانه عامل با GPS و زمان ورود/خروج';
CREATE INDEX idx_visits_date ON salesperson_visits(visit_date);
CREATE INDEX idx_visits_distributor ON salesperson_visits(distributor_id, visit_date);

-- پایان فایل 004
