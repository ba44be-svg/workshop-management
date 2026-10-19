-- ============================================================
-- 010_seed_initial_data.sql
-- داده‌های اولیه برای شروع کار
-- کاربران نقش‌ها، کدینگ حساب‌ها، ۳ عامل نمونه، ۳۰ محصول نمونه
-- ============================================================
-- نکته: این داده‌ها برای محیط توسعه است. در production با داده‌های واقعی جایگزین بشه

-- =====================================================
-- ۱. Roles و Permissions
-- =====================================================
INSERT INTO roles (name, code, description) VALUES
    ('مدیر', 'manager', 'دسترسی کامل سیستم'),
    ('حسابدار', 'accountant', 'ثبت سند حسابداری و گزارش‌های مالی'),
    ('انباردار', 'storekeeper', 'ثبت تولید و حرکت‌های انبار'),
    ('عامل پخش', 'distributor', 'ثبت پیش‌نویس فروش در موبایل'),
    ('فروشگاه', 'store_owner', 'ثبت سفارش و پرداخت از پورتال PWA');

-- =====================================================
-- ۲. Admin User (با رمز عبور پیش‌فرض: admin123456)
-- در production حتماً تغییر کنه!
-- =====================================================
INSERT INTO users (username, email, password, first_name, last_name, is_active, is_staff, is_superuser, role, phone) VALUES
    ('admin', 'admin@workshop.local',
     'pbkdf2_sha256$600000$abc123$xyz789',
     'مدیر', 'سیستم',
     TRUE, TRUE, TRUE, 'manager', '09120000000');

-- نقش مدیر را به admin اختصاص بده
INSERT INTO user_roles (user_id, role_id, assigned_by)
    SELECT u.id, r.id, u.id FROM users u, roles r
    WHERE u.username = 'admin' AND r.code = 'manager';

-- =====================================================
-- ۳. کاربر نمونه برای هر نقش
-- =====================================================
INSERT INTO users (username, email, password, first_name, last_name, role, phone) VALUES
    ('accountant1', 'accountant@workshop.local',
     'pbkdf2_sha256$600000$abc123$xyz789',
     'حسابدار', 'یکم',
     'accountant', '09120000001'),
    ('storekeeper1', 'storekeeper@workshop.local',
     'pbkdf2_sha256$600000$abc123$xyz789',
     'انباردار', 'یکم',
     'storekeeper', '09120000002'),
    ('distributor1', 'd1@workshop.local',
     'pbkdf2_sha256$600000$abc123$xyz789',
     'عامل', 'یکم',
     'distributor', '09120000003'),
    ('storeowner1', 'store1@workshop.local',
     'pbkdf2_sha256$600000$abc123$xyz789',
     'فروشگاه', 'نمونه',
     'store_owner', '09120000004');

-- اختصاص نقش‌ها به کاربران نمونه
INSERT INTO user_roles (user_id, role_id)
    SELECT u.id, r.id FROM users u, roles r
    WHERE u.username = 'accountant1' AND r.code = 'accountant';

INSERT INTO user_roles (user_id, role_id)
    SELECT u.id, r.id FROM users u, roles r
    WHERE u.username = 'storekeeper1' AND r.code = 'storekeeper';

INSERT INTO user_roles (user_id, role_id)
    SELECT u.id, r.id FROM users u, roles r
    WHERE u.username = 'distributor1' AND r.code = 'distributor';

INSERT INTO user_roles (user_id, role_id)
    SELECT u.id, r.id FROM users u, roles r
    WHERE u.username = 'storeowner1' AND r.code = 'store_owner';

-- =====================================================
-- ۴. کدینگ حساب‌ها (ساختار درختی)
-- =====================================================
INSERT INTO accounts (code, name, type, is_postable) VALUES
    -- دارایی‌ها
    ('1', 'دارایی‌ها', 'asset', FALSE),
    ('10', 'دارایی‌های جاری', 'asset', FALSE),
    ('101', 'موجودی کالا', 'asset', TRUE),
    ('102', 'حساب‌های دریافتنی', 'asset', TRUE),
    ('103', 'موجودی نقد و بانک', 'asset', TRUE),
    ('104', 'موجودی امانی در فروشگاه‌ها', 'asset', TRUE),
    -- بدهی‌ها
    ('2', 'بدهی‌ها', 'liability', FALSE),
    ('20', 'بدهی‌های جاری', 'liability', FALSE),
    ('201', 'حساب‌های پرداختنی', 'liability', TRUE),
    ('202', 'پیش‌دریافت از فروشگاه', 'liability', TRUE),
    -- حقوق صاحبان سهام
    ('3', 'حقوق صاحبان سهام', 'equity', FALSE),
    ('30', 'سرمایه', 'equity', TRUE),
    -- درآمد
    ('4', 'درآمدها', 'revenue', FALSE),
    ('40', 'درآمد فروش', 'revenue', TRUE),
    ('401', 'درآمد فروش امانی', 'revenue', TRUE),
    ('402', 'درآمد فروش قطعی', 'revenue', TRUE),
    -- هزینه
    ('5', 'هزینه‌ها', 'expense', FALSE),
    ('50', 'بهای تمام‌شده کالای فروش‌رفته', 'expense', TRUE),
    ('51', 'ضایعات تولید', 'expense', TRUE),
    ('52', 'هزینه‌های پخش', 'expense', TRUE),
    ('53', 'هزینه‌های اداری', 'expense', TRUE);

-- =====================================================
-- ۵. ۳ عامل پخش نمونه
-- =====================================================
INSERT INTO distributors (code, name, mobile, commission_rate) VALUES
    ('D001', 'عامل پخش مرکز', '09121110001', 5.00),
    ('D002', 'عامل پخش شمال', '09121110002', 5.00),
    ('D003', 'عامل پخش جنوب', '09121110003', 5.00);

-- =====================================================
-- ۶. ۱۰ فروشگاه نمونه (از ۲۰۰ فروشگاه فرضی)
-- =====================================================
INSERT INTO stores (code, name, address, phone, distributor_id, sales_model, tier, credit_limit, geo_lat, geo_lng) VALUES
    ('S001', 'فروشگاه نمونه ۱', 'تهران - خیابان ولیعصر', '02122001001', 1, 'consignment', 'gold', 500000000, 35.7219, 51.3347),
    ('S002', 'فروشگاه نمونه ۲', 'کرج - خیابان طالقانی', '02622001002', 1, 'mixed', 'silver', 200000000, 35.8401, 50.9391),
    ('S003', 'فروشگاه نمونه ۳', 'اصفهان - چهارباغ', '03122001003', 2, 'consignment', 'platinum', 800000000, 32.6546, 51.6680),
    ('S004', 'فروشگاه نمونه ۴', 'شیراز - خیابان زند', '07122001004', 2, 'firm', 'gold', 400000000, 29.5916, 52.5837),
    ('S005', 'فروشگاه نمونه ۵', 'مشهد - خیابان امام', '05122001005', 3, 'consignment', 'regular', 100000000, 36.2972, 59.6062),
    ('S006', 'فروشگاه نمونه ۶', 'تبریز - خیابان فردوسی', '04122001006', 3, 'mixed', 'silver', 250000000, 38.0800, 46.2919),
    ('S007', 'فروشگاه نمونه ۷', 'اهواز - کیانپارس', '06122001007', 1, 'consignment', 'regular', 150000000, 31.3181, 48.6705),
    ('S008', 'فروشگاه نمونه ۸', 'رشت - خیابان امام', '01322001008', 2, 'consignment', 'gold', 350000000, 37.2709, 49.5890),
    ('S009', 'فروشگاه نمونه ۹', 'قم - خیابان آذر', '02522001009', 3, 'firm', 'silver', 180000000, 34.6398, 50.8807),
    ('S010', 'فروشگاه نمونه ۱۰', 'یزد - خیابان شهدا', '03522001010', 2, 'consignment', 'platinum', 700000000, 31.8974, 54.3569);

-- =====================================================
-- ۷. دسته‌بندی محصولات نمونه
-- =====================================================
INSERT INTO product_categories (code, name, level) VALUES
    ('CAT01', 'گروه A', 1),
    ('CAT02', 'گروه B', 1),
    ('CAT03', 'گروه C', 1),
    ('CAT04', 'محصولات ویژه', 1);

-- زیرگروه‌ها
INSERT INTO product_categories (code, name, parent_id, level)
    SELECT 'CAT0101', 'گروه A - نوع ۱', id, 2 FROM product_categories WHERE code = 'CAT01';
INSERT INTO product_categories (code, name, parent_id, level)
    SELECT 'CAT0102', 'گروه A - نوع ۲', id, 2 FROM product_categories WHERE code = 'CAT01';

-- =====================================================
-- ۸. ۳۰ محصول نمونه
-- =====================================================
INSERT INTO products (code, name, category_id, unit, shelf_life_days, default_price, barcode) VALUES
    ('P001', 'محصول نمونه A1', 1, 'عدد', 15, 50000, '6421000000017'),
    ('P002', 'محصول نمونه A2', 1, 'عدد', 15, 55000, '6421000000024'),
    ('P003', 'محصول نمونه A3', 1, 'عدد', 15, 60000, '6421000000031'),
    ('P004', 'محصول نمونه A4', 1, 'عدد', 15, 65000, '6421000000048'),
    ('P005', 'محصول نمونه A5', 1, 'عدد', 15, 70000, '6421000000055'),
    ('P006', 'محصول نمونه A6', 1, 'عدد', 15, 75000, '6421000000062'),
    ('P007', 'محصول نمونه A7', 1, 'عدد', 15, 80000, '6421000000079'),
    ('P008', 'محصول نمونه A8', 1, 'عدد', 15, 85000, '6421000000086'),
    ('P009', 'محصول نمونه A9', 1, 'عدد', 15, 90000, '6421000000093'),
    ('P010', 'محصول نمونه A10', 1, 'عدد', 15, 95000, '6421000000109'),
    ('P011', 'محصول نمونه B1', 2, 'عدد', 15, 100000, '6421000000116'),
    ('P012', 'محصول نمونه B2', 2, 'عدد', 15, 105000, '6421000000123'),
    ('P013', 'محصول نمونه B3', 2, 'عدد', 15, 110000, '6421000000130'),
    ('P014', 'محصول نمونه B4', 2, 'عدد', 15, 115000, '6421000000147'),
    ('P015', 'محصول نمونه B5', 2, 'عدد', 15, 120000, '6421000000154'),
    ('P016', 'محصول نمونه B6', 2, 'عدد', 15, 125000, '6421000000161'),
    ('P017', 'محصول نمونه B7', 2, 'عدد', 15, 130000, '6421000000178'),
    ('P018', 'محصول نمونه B8', 2, 'عدد', 15, 135000, '6421000000185'),
    ('P019', 'محصول نمونه B9', 2, 'عدد', 15, 140000, '6421000000192'),
    ('P020', 'محصول نمونه B10', 2, 'عدد', 15, 145000, '6421000000208'),
    ('P021', 'محصول نمونه C1', 3, 'عدد', 15, 150000, '6421000000215'),
    ('P022', 'محصول نمونه C2', 3, 'عدد', 15, 155000, '6421000000222'),
    ('P023', 'محصول نمونه C3', 3, 'عدد', 15, 160000, '6421000000239'),
    ('P024', 'محصول نمونه C4', 3, 'عدد', 15, 165000, '6421000000246'),
    ('P025', 'محصول نمونه C5', 3, 'عدد', 15, 170000, '6421000000253'),
    ('P026', 'محصول نمونه C6', 3, 'عدد', 15, 175000, '6421000000260'),
    ('P027', 'محصول نمونه C7', 3, 'عدد', 15, 180000, '6421000000277'),
    ('P028', 'محصول نمونه C8', 3, 'عدد', 15, 185000, '6421000000284'),
    ('P029', 'محصول نمونه C9', 3, 'عدد', 15, 190000, '6421000000291'),
    ('P030', 'محصول نمونه C10', 3, 'عدد', 15, 195000, '6421000000307');

-- =====================================================
-- ۹. انبار اصلی کارگاه + انبار مجازی هر فروشگاه
-- =====================================================
INSERT INTO warehouses (code, name, type) VALUES
    ('WH-MAIN', 'انبار اصلی کارگاه', 'main');

-- انبار مجازی برای هر فروشگاه
INSERT INTO warehouses (code, name, type, store_id)
    SELECT 'WH-STORE-' || code, 'انبار فروشگاه ' || name, 'store', id
    FROM stores;

-- =====================================================
-- ۱۰. قالب‌های سند حسابداری خودکار
-- =====================================================
INSERT INTO journal_templates (name, source_type, template_json) VALUES
    ('فروش امانی', 'sale', '{
        "context": "consignment",
        "debit": [{"account_code": "104", "ref_field": "store_id"}],
        "credit": [{"account_code": "101", "ref_field": "warehouse_id"}]
    }'),
    ('فروش قطعی', 'sale', '{
        "context": "firm",
        "debit": [{"account_code": "102", "ref_field": "store_id"}],
        "credit": [
            {"account_code": "402", "ref_field": "total_amount"},
            {"account_code": "101", "ref_field": "total_cost"}
        ]
    }'),
    ('برگشت از فروش', 'return', '{
        "debit": [{"account_code": "101", "ref_field": "warehouse_id"}],
        "credit": [{"account_code": "102", "ref_field": "store_id"}]
    }'),
    ('پرداخت آنلاین', 'payment', '{
        "debit": [{"account_code": "103", "ref_field": "amount"}],
        "credit": [{"account_code": "102", "ref_field": "store_id"}]
    }'),
    ('انتقال بین انبارها', 'transfer', '{
        "debit": [{"account_code": "101", "ref_field": "to_warehouse_id"}],
        "credit": [{"account_code": "101", "ref_field": "from_warehouse_id"}]
    }');

-- =====================================================
-- ۱۱. قالب‌های پیامک
-- =====================================================
INSERT INTO sms_templates (code, name, template_text) VALUES
    ('visit_reminder', 'یادآوری سرکشی',
     '{{distributor_name}} عزیز، شروع سرکشی روز {{date}} ساعت {{start_time}}. اولین فروشگاه: {{first_store}}.'),
    ('sale_confirmation', 'تأیید فروش',
     '{{store_name}}، فروش به مبلغ {{total_amount}} ریال با شماره {{sale_no}} ثبت شد.'),
    ('expiry_alert', 'هشدار انقضا',
     'هشدار: {{count}} لات نزدیک به انقضا. اولویت: {{highest_priority_lot}}. وارد داشبورد شوید.'),
    ('transfer_request', 'درخواست انتقال',
     '{{from_store}} درخواست انتقال {{qty}} عدد {{product}} کرده. کد انتقال: {{transfer_no}}.'),
    ('low_stock', 'کمبود موجودی',
     'موجودی {{product}} در {{warehouse}} به {{qty}} رسید (زیر حداقل {{min_qty}}).'),
    ('journal_error', 'خطای توازن',
     'خطای توازن سند {{journal_no}}: {{diff_amount}} ریال. لطفاً بررسی کنید.'),
    ('payment_success', 'تأیید پرداخت',
     'پرداخت {{amount}} ریال دریافت شد. کد پیگیری: {{ref_id}}.'),
    ('order_approved', 'تأیید سفارش',
     'سفارش {{order_no}} شما تأیید شد. تحویل {{delivery_date}}.'),
    ('draft_rejected', 'رد پیش‌نویس',
     'پیش‌نویس {{draft_no}} رد شد. دلیل: {{reason}}.'),
    ('tier_upgrade', 'ارتقاء Tier',
     'تبریک! شما به Tier {{tier_name}} ارتقا یافتید. تخفیف {{discount}}٪ فعال است.');

-- =====================================================
-- ۱۲. دوره مالی جاری
-- =====================================================
INSERT INTO fiscal_periods (name, type, start_date, end_date) VALUES
    ('فروردین ۱۴۰۴', 'monthly', '2025-03-21', '2025-04-20'),
    ('بهار ۱۴۰۴', 'quarterly', '2025-03-21', '2025-06-21'),
    ('سال مالی ۱۴۰۴', 'yearly', '2025-03-21', '2026-03-20');

-- =====================================================
-- ۱۳. مرکزهای هزینه نمونه
-- =====================================================
INSERT INTO cost_centers (code, name, type) VALUES
    ('CC01', 'خط تولید ۱', 'production'),
    ('CC02', 'خط تولید ۲', 'production'),
    ('CC03', 'پخش', 'distribution'),
    ('CC04', 'اداری', 'administrative');

-- به‌روزرسانی FK در products
UPDATE products SET cost_center_id = 1 WHERE code LIKE 'P0%1';
UPDATE products SET cost_center_id = 2 WHERE code LIKE 'P0%2';

-- =====================================================
-- ۱۴. قیمت‌گذاری پویا برای هر لایه
-- =====================================================
INSERT INTO pricing_rules (product_id, store_tier, min_price, default_price)
    SELECT id, 'regular', default_price * 0.95, default_price FROM products;
INSERT INTO pricing_rules (product_id, store_tier, min_price, default_price)
    SELECT id, 'silver', default_price * 0.97, default_price FROM products;
INSERT INTO pricing_rules (product_id, store_tier, min_price, default_price)
    SELECT id, 'gold', default_price * 0.95, default_price FROM products;
INSERT INTO pricing_rules (product_id, store_tier, min_price, default_price)
    SELECT id, 'platinum', default_price * 0.92, default_price FROM products;

-- پایان فایل 010
