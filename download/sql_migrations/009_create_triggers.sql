-- ============================================================
-- 009_create_triggers.sql
-- PostgreSQL Triggers و Functions
-- کنترل توازن سند حسابداری + به‌روزرسانی خودکار موجودی
-- ============================================================

-- =====================================================
-- Function 1: کنترل توازن سند حسابداری (CRITICAL)
-- تضمین می‌کند مجموع بدهکار = مجموع بستانکار برای هر سند
-- =====================================================
CREATE OR REPLACE FUNCTION check_journal_balance()
RETURNS TRIGGER AS $$
DECLARE
    v_total_debit NUMERIC(18,4);
    v_total_credit NUMERIC(18,4);
    v_diff NUMERIC(18,4);
BEGIN
    SELECT
        COALESCE(SUM(debit), 0),
        COALESCE(SUM(credit), 0)
    INTO v_total_debit, v_total_credit
    FROM journal_lines
    WHERE journal_id = NEW.journal_id;

    v_diff := v_total_debit - v_total_credit;

    -- اختلاف بیشتر از ۱ ریال = خطا
    IF ABS(v_diff) > 1 THEN
        RAISE EXCEPTION 'Journal % not balanced. Debit: %, Credit: %, Diff: %',
            NEW.journal_id, v_total_debit, v_total_credit, v_diff;
    END IF;

    -- به‌روزرسانی مجموع در Header
    UPDATE journal_headers
       SET total_debit = v_total_debit,
           total_credit = v_total_credit,
           updated_at = NOW()
     WHERE id = NEW.journal_id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_journal_balance
AFTER INSERT OR UPDATE OR DELETE ON journal_lines
FOR EACH ROW EXECUTE FUNCTION check_journal_balance();

COMMENT ON FUNCTION check_journal_balance() IS 'کنترل توازن سند حسابداری در سطح دیتابیس';

-- =====================================================
-- Function 2: محاسبه میانگین موزون پس از ورود کالا
-- =====================================================
CREATE OR REPLACE FUNCTION update_weighted_avg()
RETURNS TRIGGER AS $$
DECLARE
    v_existing_qty NUMERIC(14,3);
    v_old_avg NUMERIC(18,4);
    v_new_avg NUMERIC(18,4);
BEGIN
    -- فقط برای حرکت‌های ورودی
    IF NEW.movement_type != 'in' THEN
        RETURN NEW;
    END IF;

    SELECT current_qty, weighted_avg_cost
      INTO v_existing_qty, v_old_avg
      FROM inventory_lots
     WHERE id = NEW.lot_id
       FOR UPDATE; -- قفل ردیف برای جلوگیری از Race Condition

    v_new_avg := ((v_existing_qty * v_old_avg) + (NEW.qty * NEW.unit_cost))
                 / (v_existing_qty + NEW.qty);

    UPDATE inventory_lots
       SET weighted_avg_cost = v_new_avg,
           current_qty = current_qty + NEW.qty,
           updated_at = NOW()
     WHERE id = NEW.lot_id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_weighted_avg
AFTER INSERT ON inventory_movements
FOR EACH ROW EXECUTE FUNCTION update_weighted_avg();

COMMENT ON FUNCTION update_weighted_avg() IS 'محاسبه میانگین موزون پس از هر ورود کالا';

-- =====================================================
-- Function 3: به‌روزرسانی موجودی تجمیعی (StockBalances)
-- =====================================================
CREATE OR REPLACE FUNCTION update_stock_balance()
RETURNS TRIGGER AS $$
DECLARE
    v_product_id BIGINT;
    v_warehouse_id BIGINT;
    v_qty_change NUMERIC(14,3);
    v_value_change NUMERIC(18,4);
BEGIN
    v_product_id := NEW.product_id;
    v_warehouse_id := NEW.warehouse_id;

    IF NEW.movement_type IN ('in', 'return') THEN
        v_qty_change := NEW.qty;
        v_value_change := NEW.qty * COALESCE(NEW.unit_cost, 0);
    ELSIF NEW.movement_type IN ('out', 'transfer') THEN
        v_qty_change := -NEW.qty;
        v_value_change := -(NEW.qty * COALESCE(NEW.unit_cost, 0));
    ELSE
        RETURN NEW;
    END IF;

    -- Upsert در stock_balances
    INSERT INTO stock_balances (product_id, warehouse_id, total_qty, total_value, updated_at)
    VALUES (v_product_id, v_warehouse_id, v_qty_change, v_value_change, NOW())
    ON CONFLICT (product_id, warehouse_id)
    DO UPDATE SET
        total_qty = stock_balances.total_qty + EXCLUDED.total_qty,
        total_value = stock_balances.total_value + EXCLUDED.total_value,
        last_lot_id = NEW.lot_id,
        updated_at = NOW();

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_stock_balance
AFTER INSERT ON inventory_movements
FOR EACH ROW EXECUTE FUNCTION update_stock_balance();

COMMENT ON FUNCTION update_stock_balance() IS 'به‌روزرسانی خودکار موجودی تجمیعی';

-- =====================================================
-- Function 4: هشدار انقضای کالا
-- =====================================================
CREATE OR REPLACE FUNCTION flag_expired_lots()
RETURNS VOID AS $$
BEGIN
    UPDATE inventory_lots
       SET status = 'expired'
     WHERE expiry_date < CURRENT_DATE
       AND status = 'active'
       AND current_qty > 0;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION flag_expired_lots() IS 'علامت‌گذاری لات‌های منقضی';

-- این Function باید به‌صورت روزانه توسط Celery Beat اجرا بشه

-- =====================================================
-- Function 5: محاسبه امتیاز وفاداری پس از هر فروش
-- =====================================================
CREATE OR REPLACE FUNCTION add_loyalty_points_after_sale()
RETURNS TRIGGER AS $$
DECLARE
    v_points INTEGER;
    v_current_balance INTEGER;
BEGIN
    -- محاسبه امتیاز: ۱ امتیاز به ازای هر ۱۰۰ هزار ریال
    v_points := (NEW.total_amount / 100000)::INTEGER;

    -- امتیاز فعلی فروشگاه
    SELECT loyalty_points INTO v_current_balance
    FROM stores WHERE id = NEW.store_id;

    -- ثبت تراکنش وفاداری
    INSERT INTO loyalty_transactions
        (store_id, points_change, reason, related_doc_type, related_doc_id, new_balance)
    VALUES
        (NEW.store_id, v_points, 'purchase', 'sale', NEW.id,
         v_current_balance + v_points);

    -- به‌روزرسانی امتیاز فروشگاه
    UPDATE stores
       SET loyalty_points = loyalty_points + v_points
     WHERE id = NEW.store_id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_loyalty_after_sale
AFTER INSERT ON sales_headers
FOR EACH ROW
WHEN (NEW.status = 'posted')
EXECUTE FUNCTION add_loyalty_points_after_sale();

COMMENT ON FUNCTION add_loyalty_points_after_sale() IS 'افزودن امتیاز وفاداری پس از هر فروش';

-- =====================================================
-- Function 6: کنترل اعتبار فروشگاه قبل از تأیید سفارش
-- =====================================================
CREATE OR REPLACE FUNCTION check_store_credit()
RETURNS TRIGGER AS $$
DECLARE
    v_credit_limit NUMERIC(18,4);
    v_current_credit NUMERIC(18,4);
BEGIN
    SELECT credit_limit, current_credit
      INTO v_credit_limit, v_current_credit
      FROM stores
     WHERE id = NEW.store_id;

    IF v_current_credit + NEW.total_amount > v_credit_limit THEN
        RAISE EXCEPTION 'Store % credit limit exceeded. Limit: %, Current: %, Order: %',
            NEW.store_id, v_credit_limit, v_current_credit, NEW.total_amount;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_check_store_credit
BEFORE INSERT OR UPDATE OF total_amount ON store_orders
FOR EACH ROW
WHEN (NEW.status IN ('submitted', 'under_review', 'approved'))
EXECUTE FUNCTION check_store_credit();

COMMENT ON FUNCTION check_store_credit() IS 'کنترل سقف اعتبار فروشگاه قبل از تأیید سفارش';

-- =====================================================
-- Function 7: تولید شماره سند خودکار
-- =====================================================
CREATE OR REPLACE FUNCTION generate_doc_number(p_prefix TEXT, p_table TEXT)
RETURNS VARCHAR AS $$
DECLARE
    v_year TEXT := EXTRACT(YEAR FROM CURRENT_DATE)::TEXT;
    v_seq INTEGER;
    v_result VARCHAR(50);
BEGIN
    -- گرفتن شماره بعدی از sequence
    EXECUTE format('SELECT nextval(%L)', p_prefix || '_seq') INTO v_seq;

    v_result := p_prefix || '-' || v_year || '-' || LPAD(v_seq::TEXT, 6, '0');
    RETURN v_result;
END;
$$ LANGUAGE plpgsql;

-- ساخت sequenceها
CREATE SEQUENCE IF NOT EXISTS sales_seq START 1;
CREATE SEQUENCE IF NOT EXISTS dispatch_seq START 1;
CREATE SEQUENCE IF NOT EXISTS journal_seq START 1;
CREATE SEQUENCE IF NOT EXISTS transfer_seq START 1;
CREATE SEQUENCE IF NOT EXISTS return_seq START 1;
CREATE SEQUENCE IF NOT EXISTS draft_seq START 1;
CREATE SEQUENCE IF NOT EXISTS order_seq START 1;
CREATE SEQUENCE IF NOT EXISTS payment_seq START 1;

COMMENT ON FUNCTION generate_doc_number(TEXT, TEXT) IS 'تولید شماره سند خودکار با پیشوند و سال';

-- =====================================================
-- Function 8: خودکارسازی updated_at
-- =====================================================
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- اضافه کردن trigger به جداول اصلی
CREATE TRIGGER trg_update_timestamp
BEFORE UPDATE ON product_categories
FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trg_update_timestamp
BEFORE UPDATE ON products
FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trg_update_timestamp
BEFORE UPDATE ON stores
FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trg_update_timestamp
BEFORE UPDATE ON distributors
FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trg_update_timestamp
BEFORE UPDATE ON accounts
FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trg_update_timestamp
BEFORE UPDATE ON inventory_lots
FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trg_update_timestamp
BEFORE UPDATE ON sales_headers
FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trg_update_timestamp
BEFORE UPDATE ON journal_headers
FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trg_update_timestamp
BEFORE UPDATE ON sales_draft_headers
FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trg_update_timestamp
BEFORE UPDATE ON store_orders
FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- پایان فایل 009
