-- ============================================================
-- 003_create_inventory_tables.sql
-- گروه ۲: انبار و تولید (۷ جدول)
-- Warehouses, InventoryLots, InventoryMovements, StockBalances,
-- ProductionBatches, ProductionConsumption, ProductionOutputs
-- ============================================================

-- =====================================================
-- 7. Warehouses — انبارها (اصلی + مجازی فروشگاه‌ها)
-- =====================================================
CREATE TABLE warehouses (
    id                  BIGSERIAL PRIMARY KEY,
    code                VARCHAR(50) NOT NULL UNIQUE,
    name                VARCHAR(200) NOT NULL,
    type                warehouse_type_enum NOT NULL,
    store_id            BIGINT REFERENCES stores(id), -- برای انبار مجازی
    address             TEXT,
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by          BIGINT,
    deleted_at          TIMESTAMPTZ,
    CONSTRAINT chk_warehouse_type_store
        CHECK ((type = 'store' AND store_id IS NOT NULL)
            OR (type IN ('main', 'virtual') AND store_id IS NULL))
);

COMMENT ON TABLE warehouses IS 'انبار اصلی + انبار مجازی هر فروشگاه';
CREATE UNIQUE INDEX idx_warehouses_store_unique
    ON warehouses(store_id)
    WHERE type = 'store' AND deleted_at IS NULL;

-- =====================================================
-- 8. InventoryLots — لات‌های انبار (هر بچ تولید = ۱ لات)
-- =====================================================
CREATE TABLE inventory_lots (
    id                  BIGSERIAL PRIMARY KEY,
    product_id          BIGINT NOT NULL REFERENCES products(id),
    warehouse_id        BIGINT NOT NULL REFERENCES warehouses(id),
    batch_no            VARCHAR(50) NOT NULL,
    production_date     DATE NOT NULL,
    expiry_date         DATE NOT NULL,
    initial_qty         NUMERIC(14,3) NOT NULL,
    current_qty         NUMERIC(14,3) NOT NULL,
    weighted_avg_cost   NUMERIC(18,4) NOT NULL DEFAULT 0,
    status              VARCHAR(20) NOT NULL DEFAULT 'active',
    production_batch_id BIGINT, -- FK به production_batches (پایین)
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by          BIGINT,
    deleted_at          TIMESTAMPTZ,
    CONSTRAINT chk_qty_nonneg CHECK (initial_qty >= 0 AND current_qty >= 0),
    CONSTRAINT chk_dates CHECK (expiry_date >= production_date),
    CONSTRAINT chk_lot_status CHECK (status IN ('active', 'expired', 'disposed', 'returned')),
    UNIQUE (product_id, warehouse_id, batch_no)
);

COMMENT ON TABLE inventory_lots IS 'لات‌های موجودی با ردیابی بچ و میانگین موزون';
COMMENT ON COLUMN inventory_lots.expiry_date IS 'تاریخ انقضا — معیار اصلی FEFO';
CREATE INDEX idx_lots_fefo ON inventory_lots
    (product_id, warehouse_id, expiry_date, current_qty)
    WHERE deleted_at IS NULL AND status = 'active';
CREATE INDEX idx_lots_expiry ON inventory_lots(expiry_date)
    WHERE current_qty > 0 AND deleted_at IS NULL;
CREATE INDEX idx_lots_product_warehouse ON inventory_lots(product_id, warehouse_id)
    WHERE current_qty > 0;

-- =====================================================
-- 9. InventoryMovements — حرکت‌های انبار (تاریخچه کامل)
-- =====================================================
CREATE TABLE inventory_movements (
    id                  BIGSERIAL PRIMARY KEY,
    lot_id              BIGINT NOT NULL REFERENCES inventory_lots(id),
    product_id          BIGINT NOT NULL REFERENCES products(id),
    warehouse_id        BIGINT NOT NULL REFERENCES warehouses(id),
    movement_type       movement_type_enum NOT NULL,
    qty                 NUMERIC(14,3) NOT NULL,
    unit_cost           NUMERIC(18,4),
    ref_doc_type        VARCHAR(50) NOT NULL, -- sale, production, transfer, return
    ref_doc_id          BIGINT,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by          BIGINT,
    CONSTRAINT chk_qty_nonzero CHECK (qty != 0)
);

COMMENT ON TABLE inventory_movements IS 'تاریخچه کامل حرکت‌های انبار با ارجاع به سند مبدأ';
CREATE INDEX idx_movements_lot ON inventory_movements(lot_id);
CREATE INDEX idx_movements_product_wh ON inventory_movements(product_id, warehouse_id);
CREATE INDEX idx_movements_ref ON inventory_movements(ref_doc_type, ref_doc_id);
CREATE INDEX idx_movements_created ON inventory_movements(created_at);

-- =====================================================
-- 10. StockBalances — موجودی تجمیعی (Cache برای عملکرد)
-- =====================================================
CREATE TABLE stock_balances (
    id                  BIGSERIAL PRIMARY KEY,
    product_id          BIGINT NOT NULL REFERENCES products(id),
    warehouse_id        BIGINT NOT NULL REFERENCES warehouses(id),
    total_qty           NUMERIC(14,3) NOT NULL DEFAULT 0,
    total_value         NUMERIC(18,4) NOT NULL DEFAULT 0,
    last_lot_id         BIGINT REFERENCES inventory_lots(id),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_balance_qty CHECK (total_qty >= 0),
    UNIQUE (product_id, warehouse_id)
);

COMMENT ON TABLE stock_balances IS 'موجودی تجمیعی هر محصول در هر انبار (Cache)';
CREATE INDEX idx_balances_low_stock ON stock_balances(product_id, warehouse_id) WHERE total_qty = 0;

-- =====================================================
-- 11. ProductionBatches — بچ‌های تولید
-- =====================================================
CREATE TABLE production_batches (
    id                  BIGSERIAL PRIMARY KEY,
    batch_no            VARCHAR(50) NOT NULL UNIQUE,
    product_id          BIGINT NOT NULL REFERENCES products(id),
    planned_qty         NUMERIC(14,3) NOT NULL,
    actual_qty          NUMERIC(14,3) NOT NULL DEFAULT 0,
    waste_qty           NUMERIC(14,3) NOT NULL DEFAULT 0,
    start_at            TIMESTAMPTZ,
    end_at              TIMESTAMPTZ,
    status              VARCHAR(20) NOT NULL DEFAULT 'planned',
    weighted_avg_cost   NUMERIC(18,4) NOT NULL DEFAULT 0,
    notes               TEXT,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by          BIGINT,
    deleted_at          TIMESTAMPTZ,
    CONSTRAINT chk_batch_status CHECK (status IN ('planned', 'in_progress', 'completed', 'canceled')),
    CONSTRAINT chk_batch_qty CHECK (planned_qty > 0 AND actual_qty >= 0 AND waste_qty >= 0)
);

COMMENT ON TABLE production_batches IS 'بچ‌های تولید با مقدار برنامه‌ریزی، واقعی و ضایعات';
CREATE INDEX idx_batches_product ON production_batches(product_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_batches_status ON production_batches(status) WHERE deleted_at IS NULL;

-- به‌روزرسانی FK در inventory_lots
ALTER TABLE inventory_lots
    ADD CONSTRAINT fk_lots_production_batch
    FOREIGN KEY (production_batch_id) REFERENCES production_batches(id);

-- =====================================================
-- 12. ProductionConsumption — مصرف مواد اولیه برای هر بچ
-- =====================================================
CREATE TABLE production_consumption (
    id                  BIGSERIAL PRIMARY KEY,
    batch_id             BIGINT NOT NULL REFERENCES production_batches(id) ON DELETE CASCADE,
    material_lot_id     BIGINT NOT NULL REFERENCES inventory_lots(id),
    qty_consumed         NUMERIC(14,3) NOT NULL,
    cost_at_consumption NUMERIC(18,4) NOT NULL,
    consumed_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by          BIGINT,
    CONSTRAINT chk_consumption_qty CHECK (qty_consumed > 0)
);

COMMENT ON TABLE production_consumption IS 'مواد اولیه مصرفی برای هر بچ تولید';
CREATE INDEX idx_consumption_batch ON production_consumption(batch_id);
CREATE INDEX idx_consumption_lot ON production_consumption(material_lot_id);

-- =====================================================
-- 13. ProductionOutputs — خروج محصول نهایی از بچ تولید
-- =====================================================
CREATE TABLE production_outputs (
    id                  BIGSERIAL PRIMARY KEY,
    batch_id             BIGINT NOT NULL REFERENCES production_batches(id) ON DELETE CASCADE,
    product_id          BIGINT NOT NULL REFERENCES products(id),
    qty_produced         NUMERIC(14,3) NOT NULL,
    qty_waste            NUMERIC(14,3) NOT NULL DEFAULT 0,
    lot_id              BIGINT NOT NULL REFERENCES inventory_lots(id), -- لات تولید‌شده
    output_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by          BIGINT,
    CONSTRAINT chk_output_qty CHECK (qty_produced > 0 AND qty_waste >= 0)
);

COMMENT ON TABLE production_outputs IS 'خروج محصول نهایی با تولید لات جدید';
CREATE INDEX idx_outputs_batch ON production_outputs(batch_id);
CREATE INDEX idx_outputs_lot ON production_outputs(lot_id);

-- پایان فایل 003
