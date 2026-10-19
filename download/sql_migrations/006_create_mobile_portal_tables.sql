-- ============================================================
-- 006_create_mobile_portal_tables.sql
-- گروه ۵: موبایل، پورتال و پرداخت (۸ جدول جدید)
-- SalesDraftHeaders/Lines, ApprovalQueue, StoreOrders/Lines,
-- PaymentTransactions, TaxInvoices, Barcodes
-- ============================================================

-- =====================================================
-- 32. SalesDraftHeaders — پیش‌نویس فروش ثبت‌شده توسط عامل
-- =====================================================
CREATE TABLE sales_draft_headers (
    id                  BIGSERIAL PRIMARY KEY,
    draft_no           VARCHAR(50) NOT NULL UNIQUE,
    distributor_id     BIGINT NOT NULL REFERENCES distributors(id),
    store_id            BIGINT NOT NULL REFERENCES stores(id),
    draft_date          DATE NOT NULL,
    sales_type          sales_type_enum NOT NULL,
    status              doc_status_enum NOT NULL DEFAULT 'pending',
    total_amount        NUMERIC(18,4) NOT NULL DEFAULT 0,
    sync_status         VARCHAR(20) NOT NULL DEFAULT 'offline', -- offline/synced
    device_id           VARCHAR(100),
    device_signature    VARCHAR(200), -- برای امنیت آفلاین
    notes               TEXT,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by          BIGINT,
    deleted_at          TIMESTAMPTZ,
    CONSTRAINT chk_draft_sync CHECK (sync_status IN ('offline', 'synced', 'failed')),
    CONSTRAINT chk_draft_status CHECK (status IN
        ('pending', 'reviewing', 'approved', 'rejected', 'posted'))
);

COMMENT ON TABLE sales_draft_headers IS 'پیش‌نویس فروش ثبت‌شده توسط عامل (در انتظار تأیید مدیر)';
CREATE INDEX idx_drafts_pending ON sales_draft_headers(distributor_id, status, draft_date) WHERE deleted_at IS NULL;
CREATE INDEX idx_drafts_store ON sales_draft_headers(store_id, draft_date) WHERE deleted_at IS NULL;
CREATE INDEX idx_drafts_sync ON sales_draft_headers(sync_status) WHERE sync_status != 'synced';

-- =====================================================
-- 33. SalesDraftLines — اقلام پیش‌نویس عامل
-- =====================================================
CREATE TABLE sales_draft_lines (
    id                  BIGSERIAL PRIMARY KEY,
    draft_id            BIGINT NOT NULL REFERENCES sales_draft_headers(id) ON DELETE CASCADE,
    product_id          BIGINT NOT NULL REFERENCES products(id),
    lot_id              BIGINT REFERENCES inventory_lots(id), -- nullable چون ممکنه عامل انتخاب نکرده
    qty                 NUMERIC(14,3) NOT NULL,
    unit_price          NUMERIC(18,4) NOT NULL,
    barcode_scanned     VARCHAR(50), -- اگر با بارکد ثبت شده
    manual_entry        BOOLEAN NOT NULL DEFAULT FALSE,
    line_total          NUMERIC(18,4) GENERATED ALWAYS AS (qty * unit_price) STORED,
    CONSTRAINT chk_draft_qty CHECK (qty > 0)
);

COMMENT ON TABLE sales_draft_lines IS 'اقلام پیش‌نویس با اطلاعات اسکن بارکد یا ورود دستی';
CREATE INDEX idx_draft_lines_draft ON sales_draft_lines(draft_id);

-- =====================================================
-- 34. ApprovalQueue — صف مرکزی تأیید مدیر
-- =====================================================
CREATE TABLE approval_queue (
    id                  BIGSERIAL PRIMARY KEY,
    ref_doc_type        VARCHAR(50) NOT NULL, -- sales_draft, store_order, transfer
    ref_doc_id          BIGINT NOT NULL,
    requested_by        BIGINT, -- FK به users
    requested_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    assigned_to         BIGINT, -- FK به users (مدیر)
    status              doc_status_enum NOT NULL DEFAULT 'pending',
    priority            approval_priority_enum NOT NULL DEFAULT 'medium',
    decision_reason     TEXT,
    decided_at          TIMESTAMPTZ,
    decided_by          BIGINT, -- FK به users
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_approval_status CHECK (status IN
        ('pending', 'reviewing', 'approved', 'rejected', 'posted')),
    UNIQUE (ref_doc_type, ref_doc_id)
);

COMMENT ON TABLE approval_queue IS 'صف مرکزی تأیید مدیر برای پیش‌نویس عامل و سفارش فروشگاه';
CREATE INDEX idx_approval_pending ON approval_queue(status, priority, requested_at) WHERE status = 'pending';
CREATE INDEX idx_approval_assigned ON approval_queue(assigned_to) WHERE assigned_to IS NOT NULL;

-- =====================================================
-- 35. StoreOrders — سفارش‌های ثبت‌شده توسط فروشگاه
-- =====================================================
CREATE TABLE store_orders (
    id                  BIGSERIAL PRIMARY KEY,
    order_no            VARCHAR(50) NOT NULL UNIQUE,
    store_id            BIGINT NOT NULL REFERENCES stores(id),
    order_date          DATE NOT NULL,
    status              doc_status_enum NOT NULL DEFAULT 'submitted',
    total_amount        NUMERIC(18,4) NOT NULL DEFAULT 0,
    total_qty           NUMERIC(14,3) NOT NULL DEFAULT 0,
    payment_status      payment_status_enum NOT NULL DEFAULT 'initiated',
    expected_delivery   DATE,
    delivery_address    TEXT,
    dispatch_id         BIGINT, -- FK به dispatch_headers (پس از تأیید)
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by          BIGINT,
    deleted_at          TIMESTAMPTZ,
    CONSTRAINT chk_order_status CHECK (status IN
        ('cart', 'submitted', 'under_review', 'approved', 'rejected', 'in_delivery', 'received', 'canceled'))
);

COMMENT ON TABLE store_orders IS 'سفارش ثبت‌شده توسط فروشگاه از پورتال PWA';
CREATE INDEX idx_orders_store ON store_orders(store_id, order_date) WHERE deleted_at IS NULL;
CREATE INDEX idx_orders_status ON store_orders(status) WHERE deleted_at IS NULL;
CREATE INDEX idx_orders_payment ON store_orders(payment_status) WHERE deleted_at IS NULL;

-- =====================================================
-- 36. StoreOrderLines — اقلام سفارش فروشگاه
-- =====================================================
CREATE TABLE store_order_lines (
    id                  BIGSERIAL PRIMARY KEY,
    order_id            BIGINT NOT NULL REFERENCES store_orders(id) ON DELETE CASCADE,
    product_id          BIGINT NOT NULL REFERENCES products(id),
    qty                 NUMERIC(14,3) NOT NULL,
    unit_price          NUMERIC(18,4) NOT NULL,
    line_total          NUMERIC(18,4) GENERATED ALWAYS AS (qty * unit_price) STORED,
    is_smart_suggestion BOOLEAN NOT NULL DEFAULT FALSE, -- اگر از Smart Reorder آمده
    notes               TEXT,
    CONSTRAINT chk_order_qty CHECK (qty > 0)
);

COMMENT ON TABLE store_order_lines IS 'اقلام سفارش فروشگاه با flag برای Smart Reorder';
CREATE INDEX idx_order_lines_order ON store_order_lines(order_id);
CREATE INDEX idx_order_lines_smart ON store_order_lines(product_id) WHERE is_smart_suggestion = TRUE;

-- =====================================================
-- 37. PaymentTransactions — تراکنش‌های پرداخت آنلاین
-- =====================================================
CREATE TABLE payment_transactions (
    id                  BIGSERIAL PRIMARY KEY,
    transaction_no      VARCHAR(50) NOT NULL UNIQUE,
    store_id            BIGINT NOT NULL REFERENCES stores(id),
    gateway             gateway_enum NOT NULL,
    amount              NUMERIC(18,4) NOT NULL,
    status              payment_status_enum NOT NULL DEFAULT 'initiated',
    authority           VARCHAR(200), -- کد Authority قبل از پرداخت
    ref_id              VARCHAR(100), -- کد پیگیری پس از پرداخت
    paid_at             TIMESTAMPTZ,
    related_doc_type    VARCHAR(50) NOT NULL, -- store_order, manual, etc.
    related_doc_id      BIGINT,
    journal_id          BIGINT, -- FK به journal_headers (سند حسابداری پرداخت)
    description         TEXT,
    gateway_response    JSONB, -- پاسخ کامل درگاه
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by          BIGINT,
    CONSTRAINT chk_payment_amount CHECK (amount > 0)
);

COMMENT ON TABLE payment_transactions IS 'تراکنش‌های پرداخت آنلاین با ۳ درگاه';
CREATE INDEX idx_payment_store ON payment_transactions(store_id, created_at);
CREATE INDEX idx_payment_status ON payment_transactions(status);
CREATE INDEX idx_payment_related ON payment_transactions(related_doc_type, related_doc_id);

-- =====================================================
-- 38. TaxInvoices — صورتحساب الکترونیکی سامان
-- =====================================================
CREATE TABLE tax_invoices (
    id                  BIGSERIAL PRIMARY KEY,
    store_id            BIGINT NOT NULL REFERENCES stores(id),
    sales_id            BIGINT REFERENCES sales_headers(id), -- اختیاری
    saman_uid            VARCHAR(200) UNIQUE, -- UID دریافت از سامان
    invoice_status       tax_invoice_status_enum NOT NULL DEFAULT 'draft',
    header_data          JSONB NOT NULL, -- استاندارد سامان
    body_data            JSONB NOT NULL, -- لیست اقلام
    sent_at              TIMESTAMPTZ,
    confirmed_at         TIMESTAMPTZ,
    rejection_reason    TEXT,
    retry_count          INTEGER NOT NULL DEFAULT 0,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by          BIGINT
);

COMMENT ON TABLE tax_invoices IS 'صورت‌حساب الکترونیکی سامان';
CREATE INDEX idx_tax_invoice_sales ON tax_invoices(sales_id) WHERE sales_id IS NOT NULL;
CREATE INDEX idx_tax_invoice_status ON tax_invoices(invoice_status);

-- به‌روزرسانی FK در sales_headers
ALTER TABLE sales_headers
    ADD CONSTRAINT fk_sales_tax_invoice
    FOREIGN KEY (tax_invoice_id) REFERENCES tax_invoices(id);

-- =====================================================
-- 39. Barcodes — بارکد و QR برای هر موجودیت
-- =====================================================
CREATE TABLE barcodes (
    id                  BIGSERIAL PRIMARY KEY,
    entity_type          barcode_entity_type_enum NOT NULL,
    entity_id           BIGINT NOT NULL,
    barcode_value       VARCHAR(50) NOT NULL UNIQUE, -- EAN-13
    qr_code_data        TEXT NOT NULL, -- محتوای QR (URL یا JSON)
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by          BIGINT,
    UNIQUE (entity_type, entity_id)
);

COMMENT ON TABLE barcodes IS 'بارکد و QR Code برای هر موجودیت قابل اسکن';
CREATE INDEX idx_barcodes_entity ON barcodes(entity_type, entity_id);
CREATE INDEX idx_barcodes_value ON barcodes(barcode_value);

-- =====================================================
-- جدول کمکی: BarcodeScans — لاگ اسکن‌ها از موبایل
-- =====================================================
CREATE TABLE barcode_scans (
    id                  BIGSERIAL PRIMARY KEY,
    barcode_id          BIGINT REFERENCES barcodes(id),
    barcode_value       VARCHAR(50) NOT NULL, -- در صورت نبودن در جدول
    scanned_by          BIGINT, -- FK به users
    scan_context        VARCHAR(50), -- sale_draft, transfer, inventory_check
    ref_doc_type        VARCHAR(50),
    ref_doc_id          BIGINT,
    scanned_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    device_id           VARCHAR(100)
);

COMMENT ON TABLE barcode_scans IS 'لاگ تمام اسکن‌های بارکد از موبایل';
CREATE INDEX idx_scans_user ON barcode_scans(scanned_by, scanned_at);
CREATE INDEX idx_scans_value ON barcode_scans(barcode_value);

-- پایان فایل 006
