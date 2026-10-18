#!/usr/bin/env python3
"""Step 5-6: Update Section 3 (Django Apps) and Section 4 (ERD)."""
from pathlib import Path
import re

src = Path('/home/z/my-project/scripts/bakery_erd_doc_v2.html')
text = src.read_text(encoding='utf-8')

# ============================================================
# STEP 5: Section 3 (Django Apps) updates
# ============================================================
print("STEP 5: Django Apps section updates...")

# 5.1 Update intro paragraph and apps table
text = text.replace(
    '<p>بک‌اند Django به ۱۱ ماژول مستقل (App) تقسیم می‌شود که هر کدام یک Domain مشخص کسب‌وکار را پوشش می‌دهند. این ماژولار بودن دو فایده اصلی دارد: (۱) جداسازی واضح مسئولیت‌ها که تیم توسعه می‌تواند هم‌زمان روی چند ماژول کار کند، و (۲) امکان استخراج آینده به Microservice در صورت رشد شدید حجم. هر App دارای مدل‌های مختصر به خود، Service Layer برای منطق کسب‌وکار، و Repository Pattern برای دسترسی به داده است.</p>',
    '<p>بک‌اند Django به ۱۷ ماژول مستقل (App) تقسیم می‌شود که هر کدام یک Domain مشخص کسب‌وکار را پوشش می‌دهند. این ماژولار بودن دو فایده اصلی دارد: (۱) جداسازی واضح مسئولیت‌ها که تیم توسعه می‌تواند هم‌زمان روی چند ماژول کار کند، و (۲) امکان استخراج آینده به Microservice در صورت رشد شدید حجم. هر App دارای مدل‌های مختصر به خود، Service Layer برای منطق کسب‌وکار، و Repository Pattern برای دسترسی به داده است. شش App جدید نسبت به نسخه ۱.۰ برای پشتیبانی از موبایل عوامل، پورتال فروشگاه‌ها، پرداخت آنلاین و قابلیت‌های هوشمند اضافه شده‌اند.</p>'
)

# 5.2 Replace apps table — add 6 new apps
old_apps_rows = """<tr>
    <td><code>products</code></td>
    <td>محصولات و دسته‌بندی</td>
    <td>تعریف محصول، دسته‌بندی، واحد، فرمول تولید، قیمت‌گذاری.</td>
    <td>Product, ProductCategory, Unit, BOM, Price</td>
</tr>"""
new_apps_rows = """<tr>
    <td><code>products</code></td>
    <td>محصولات و دسته‌بندی</td>
    <td>تعریف محصول، دسته‌بندی، واحد، فرمول تولید، قیمت‌گذاری، آپلود تصاویر کاتالوگ، تولید بارکد.</td>
    <td>Product, ProductCategory, Unit, BOM, Price, ProductImage, Barcode</td>
</tr>"""
text = text.replace(old_apps_rows, new_apps_rows)

# Update partners app
text = text.replace(
    """<tr>
    <td><code>partners</code></td>
    <td>فروشگاه‌ها و عوامل</td>
    <td>مدیریت ۲۰۰ فروشگاه، ۳ عامل پخش، مشتریان آنلاین، اعتبار هر فروشگاه.</td>
    <td>Store, Distributor, Customer, PartnerCredit</td>
</tr>""",
    """<tr>
    <td><code>partners</code></td>
    <td>فروشگاه‌ها و عوامل</td>
    <td>مدیریت ۲۰۰ فروشگاه، ۳ عامل پخش، مشتریان آنلاین، اعتبار و امتیاز وفاداری هر فروشگاه.</td>
    <td>Store, Distributor, Customer, PartnerCredit, LoyaltyPoint</td>
</tr>"""
)
# Update notifications app
text = text.replace(
    """<tr>
    <td><code>notifications</code></td>
    <td>اعلان و پیامک</td>
    <td>صف پیامک، قالب پیام، تاریخچه ارسال، زمان‌بندی یادآوری سرکشی.</td>
    <td>SmsTemplate, SmsQueue, SmsLog, NotificationSchedule</td>
</tr>""",
    """<tr>
    <td><code>notifications</code></td>
    <td>اعلان و پیامک</td>
    <td>صف پیامک، Push Notification (Firebase)، قالب پیام، تاریخچه ارسال، زمان‌بندی یادآوری سرکشی.</td>
    <td>SmsTemplate, SmsQueue, SmsLog, PushNotification, NotificationSchedule</td>
</tr>"""
)
# Update reports app
text = text.replace(
    """<tr>
    <td><code>reports</code></td>
    <td>گزارش و داشبورد</td>
    <td>گزارش فروش روزانه/ماهانه، ضایعات، سود و زیان، داشبورد بلادرنگ.</td>
    <td>ReportDefinition, SavedReport, DashboardWidget</td>
</tr>
</tbody>""",
    """<tr>
    <td><code>reports</code></td>
    <td>گزارش و داشبورد</td>
    <td>گزارش فروش روزانه/ماهانه، ضایعات، سود و زیان، داشبورد بلادرنگ، گزارش جغرافیایی Heatmap.</td>
    <td>ReportDefinition, SavedReport, DashboardWidget, GeoReport</td>
</tr>
<tr>
    <td><code>approval_workflow</code></td>
    <td>جریان تأیید</td>
    <td>مدیریت صف تأیید مدیر برای پیش‌نویس‌های فروش عامل و سفارش‌های فروشگاه، با reason در صورت رد.</td>
    <td>ApprovalQueue, ApprovalDecision, ApprovalRule</td>
</tr>
<tr>
    <td><code>store_portal</code></td>
    <td>پورتال فروشگاه</td>
    <td>سفارش آنلاین فروشگاه، پیگیری سفارش، کاتالوگ، گزارش خرید، مانده حساب.</td>
    <td>StoreOrder, StoreOrderLine, StoreNotification, StoreDashboard</td>
</tr>
<tr>
    <td><code>payments</code></td>
    <td>پرداخت و درگاه</td>
    <td>یکپارچگی با ۳ درگاه (زرین‌پال، آیدی‌پی، پارسیان)، تراکنش‌های آنلاین، ثبت چک و نقدی، تسویه.</td>
    <td>PaymentTransaction, PaymentGateway, CheckPayment, CashReceipt</td>
</tr>
<tr>
    <td><code>loyalty</code></td>
    <td>وفاداری و Smart Reorder</td>
    <td>محاسبه امتیاز پویای هر فروشگاه، پیشنهاد سفارش هوشمند، تخفیف خودکار VIP.</td>
    <td>LoyaltyTier, LoyaltyTransaction, ReorderSuggestion, DiscountRule</td>
</tr>
<tr>
    <td><code>barcode</code></td>
    <td>بارکد و QR</td>
    <td>تولید بارکد برای هر محصول/لات/سفارش، اسکن از موبایل، ردیابی چرخه زندگی.</td>
    <td>Barcode, BarcodeScan, QrCode</td>
</tr>
<tr>
    <td><code>saman_tax</code></td>
    <td>صورت‌حساب الکترونیکی</td>
    <td>یکپارچگی با سامانه مالیاتی سامان، تولید و ارسال فاکتور، دریافت UID، کنترل وضعیت.</td>
    <td>TaxInvoice, TaxInvoiceStatus, SamanConfig</td>
</tr>
</tbody>"""
)

# 5.3 Update RBAC section (4 → 5 roles)
text = text.replace(
    '<p>سیستم نقش‌ها با ۴ نقش اصلی طراحی شده است که هر کدام مجموعه مشخصی از Permission‌ها دارند. این نقش‌ها در جدول <code>Role</code> تعریف و در <code>Permission</code> به‌صورت دقیق (per-action: view, add, change, delete, approve) کنترل می‌شوند. پیاده‌سازی از طریق یک Middleware سفارشی و DRF Permission Class انجام می‌شود که در هر درخواست، نقش کاربر و Permission مورد نیاز را بررسی می‌کند.</p>',
    '<p>سیستم نقش‌ها با ۵ نقش اصلی طراحی شده است که هر کدام مجموعه مشخصی از Permission‌ها دارند. این نقش‌ها در جدول <code>Role</code> تعریف و در <code>Permission</code> به‌صورت دقیق (per-action: view, add, change, delete, approve) کنترل می‌شوند. پیاده‌سازی از طریق یک Middleware سفارشی و DRF Permission Class انجام می‌شود که در هر درخواست، نقش کاربر و Permission مورد نیاز را بررسی می‌کند. نقش جدید <code>StoreOwner</code> نسبت به نسخه ۱.۰ اضافه شده تا دسترسی‌های فروشگاه‌ها به پورتال B2B کنترل بشه.</p>'
)
# Update roles table — replace 4 roles with 5
text = text.replace(
    """<tr>
    <td><strong>مدیر</strong></td>
    <td>تمام گزارش‌ها، تأیید انتقال FEFO، تنظیمات سیستم، تعریف محصول و کاربر.</td>
    <td>دسترسی به اسناد حسابداری فقط در حالت Read. عدم امکان ویرایش سند ثبت‌شده (فقط معکوس).</td>
</tr>
<tr>
    <td><strong>حسابدار</strong></td>
    <td>ثبت سند دستی، کنترل توازن، تسویه روزانه، گزارش‌های مالی.</td>
    <td>عدم دسترسی به تعریف محصول، عدم تغییر در موجودی انبار (فقط مشاهده).</td>
</tr>
<tr>
    <td><strong>انباردار</strong></td>
    <td>ثبت تولید، ثبت ورود/خروج کالا، تأیید انتقال بین انبارها.</td>
    <td>عدم دسترسی به قیمت‌گذاری، عدم مشاهده سود و زیان، عدم دسترسی به کاربران.</td>
</tr>
<tr>
    <td><strong>عامل پخش</strong></td>
    <td>مشاهده سبد پخش روزانه، ثبت فروش امانی/قطعی، ثبت برگشت، مشاهده موجودی فروشگاه.</td>
    <td>عدم دسترسی به بهای تمام‌شده، عدم تغییر قیمت، فقط فروشگاه‌های اختصاص‌یافته.</td>
</tr>
</tbody>""",
    """<tr>
    <td><strong>مدیر</strong></td>
    <td>تمام گزارش‌ها، تأیید/رد پیش‌نویس‌های عامل و سفارش‌های فروشگاه، تأیید انتقال FEFO، تنظیمات سیستم، تعریف محصول و کاربر.</td>
    <td>دسترسی به اسناد حسابداری فقط در حالت Read. عدم امکان ویرایش سند ثبت‌شده (فقط معکوس).</td>
</tr>
<tr>
    <td><strong>حسابدار</strong></td>
    <td>ثبت سند دستی، کنترل توازن، تسویه روزانه، گزارش‌های مالی، تأیید پرداخت‌های آنلاین.</td>
    <td>عدم دسترسی به تعریف محصول، عدم تغییر در موجودی انبار (فقط مشاهده).</td>
</tr>
<tr>
    <td><strong>انباردار</strong></td>
    <td>ثبت تولید، ثبت ورود/خروج کالا، تأیید انتقال بین انبارها، بارگیری سفارش‌ها.</td>
    <td>عدم دسترسی به قیمت‌گذاری، عدم مشاهده سود و زیان، عدم دسترسی به کاربران.</td>
</tr>
<tr>
    <td><strong>عامل پخش</strong></td>
    <td>ثبت پیش‌نویس فروش (Draft)، ثبت تحویل امانی، مشاهده سبد پخش روزانه، اسکن بارکد، مشاهده موجودی فروشگاه‌های اختصاص‌یافته.</td>
    <td>فروش به‌صورت پیش‌نویس است تا مدیر تأیید کند. عدم دسترسی به بهای تمام‌شده.</td>
</tr>
<tr>
    <td><strong>فروشگاه (StoreOwner)</strong></td>
    <td>ثبت سفارش آنلاین، مشاهده کاتالوگ، پرداخت آنلاین بدهی، مشاهده گزارش خرید و مانده حساب، درخواست برگشت.</td>
    <td>فقط سفارش برای خود فروشگاه. سقف اعتبار در سفارش اعمال می‌شود. تأیید نهایی سفارش توسط مدیر لازم است.</td>
</tr>
</tbody>"""
)

print(f"  After Section 3 updates: length = {len(text)}")

# ============================================================
# STEP 6: Section 4 (ERD) updates
# ============================================================
print("\nSTEP 6: ERD section updates...")

# 6.1 Update overview stats
text = text.replace(
    '<h2 class="subsection-title">۴.۱ نمای کلی ۴۱ جدول</h2>',
    '<h2 class="subsection-title">۴.۱ نمای کلی ۴۹ جدول</h2>'
)
text = text.replace(
    '<p>پایگاه داده مرکزی شامل ۴۱ جدول است که در ۵ گروه منطقی دسته‌بندی شده‌اند. این دسته‌بندی بر اساس Domain کسب‌وکار انجام شده و با ساختار Appهای Django (بخش ۳) هماهنگ است. تمام جداول از کلید اصلی <code>id</code> (BIGINT AUTO_INCREMENT)، فیلدهای ردیابی <code>created_at</code>، <code>updated_at</code>، <code>created_by</code> و در صورت نیاز <code>deleted_at</code> (Soft Delete) استفاده می‌کنند.</p>',
    '<p>پایگاه داده مرکزی شامل ۴۹ جدول است که در ۶ گروه منطقی دسته‌بندی شده‌اند. ۸ جدول جدید نسبت به نسخه ۱.۰ برای پشتیبانی از موبایل عوامل، پورتال فروشگاه‌ها، پرداخت آنلاین، بارکد و سامان اضافه شده‌اند. تمام جداول از کلید اصلی <code>id</code> (BIGINT AUTO_INCREMENT)، فیلدهای ردیابی <code>created_at</code>، <code>updated_at</code>، <code>created_by</code> و در صورت نیاز <code>deleted_at</code> (Soft Delete) استفاده می‌کنند.</p>'
)
text = text.replace(
    '<div class="section-subtitle">۴۱ جدول در ۵ گروه منطقی با روابط کلیدی و کنترل‌های یکپارچگی</div>',
    '<div class="section-subtitle">۴۹ جدول در ۶ گروه منطقی با روابط کلیدی و کنترل‌های یکپارچگی</div>'
)
# Add second stat grid row
text = text.replace(
    """<div class="stat-grid">
    <div class="stat-card">
        <div class="stat-value">۶</div>
        <div class="stat-label">جدول پایه</div>
    </div>
    <div class="stat-card">
        <div class="stat-value">۷</div>
        <div class="stat-label">انبار و تولید</div>
    </div>
    <div class="stat-card">
        <div class="stat-value">۱۲</div>
        <div class="stat-label">فروش و پخش</div>
    </div>
</div>""",
    """<div class="stat-grid">
    <div class="stat-card">
        <div class="stat-value">۶</div>
        <div class="stat-label">جدول پایه</div>
    </div>
    <div class="stat-card">
        <div class="stat-value">۷</div>
        <div class="stat-label">انبار و تولید</div>
    </div>
    <div class="stat-card">
        <div class="stat-value">۱۲</div>
        <div class="stat-label">فروش و پخش</div>
    </div>
</div>
<div class="stat-grid" style="margin-top: -8px;">
    <div class="stat-card">
        <div class="stat-value">۶</div>
        <div class="stat-label">حسابداری</div>
    </div>
    <div class="stat-card">
        <div class="stat-value">۸</div>
        <div class="stat-label">موبایل و پورتال (جدید)</div>
    </div>
    <div class="stat-card">
        <div class="stat-value">۱۰</div>
        <div class="stat-label">سیستمی</div>
    </div>
</div>"""
)

# 6.2 Add new subsection 4.6 (mobile/portal tables) and renumber old 4.6/4.7 to 4.7/4.8
text = text.replace(
    """<h2 class="subsection-title">۴.۶ گروه ۵ — جداول سیستمی (۱۰ جدول)</h2>""",
    """<h2 class="subsection-title">۴.۶ گروه ۵ — موبایل، پورتال و پرداخت (۸ جدول جدید)</h2>
<p>این ۸ جدول برای پشتیبانی از قابلیت‌های جدید نسخه ۲.۰ اضافه شده‌اند. این جداول چرخه کامل از پیش‌نویس موبایل عامل تا پرداخت آنلاین و صورت‌حساب الکترونیکی را پوشش می‌دهند. هر سند در این گروه دارای جریان تأیید مشخصی است که در بخش ۹ و ۱۰ به‌طور کامل توضیح داده شده است.</p>

<div class="erd-group">
    <div class="erd-entity erd-entity-strong">SalesDraftHeaders (پیش‌نویس عامل)</div>
    <div class="erd-entity erd-entity-strong">SalesDraftLines</div>
    <div class="erd-entity erd-entity-strong">ApprovalQueue (صف تأیید)</div>
    <div class="erd-entity erd-entity-strong">StoreOrders (سفارش فروشگاه)</div>
    <div class="erd-entity erd-entity-strong">StoreOrderLines</div>
    <div class="erd-entity erd-entity-strong">PaymentTransactions (تراکنش آنلاین)</div>
    <div class="erd-entity erd-entity-strong">TaxInvoices (صورت‌حساب سامان)</div>
    <div class="erd-entity erd-entity-strong">Barcodes (بارکد/QR)</div>
</div>

<table>
<thead>
<tr>
    <th style="width: 22%;">جدول</th>
    <th style="width: 36%;">فیلدهای کلیدی</th>
    <th style="width: 42%;">توضیح</th>
</tr>
</thead>
<tbody>
<tr>
    <td><code>SalesDraftHeaders</code></td>
    <td>id, draft_no, distributor_id, store_id, draft_date, sales_type, status (pending/reviewing/approved/rejected), total_amount, sync_status (offline/synced), device_id</td>
    <td>پیش‌نویس فروش ثبت‌شده توسط عامل در گوشی. تا تأیید مدیر هیچ اثر انبار و حسابداری ندارد.</td>
</tr>
<tr>
    <td><code>SalesDraftLines</code></td>
    <td>id, draft_id, product_id, lot_id (nullable), qty, unit_price, barcode_scanned, manual_entry</td>
    <td>اقلام پیش‌نویس با اطلاعات اسکن بارکد یا ورود دستی.</td>
</tr>
<tr>
    <td><code>ApprovalQueue</code></td>
    <td>id, ref_doc_type (sales_draft/store_order/transfer), ref_doc_id, requested_by, assigned_to, status, decision_reason, decided_at, priority</td>
    <td>صف مرکزی تأیید مدیر. هر سند منتظر تأیید، یک رکورد در این جدول می‌سازد.</td>
</tr>
<tr>
    <td><code>StoreOrders</code></td>
    <td>id, order_no, store_id, order_date, status, total_amount, total_qty, payment_status, expected_delivery, delivery_address</td>
    <td>سفارش ثبت‌شده توسط فروشگاه از پورتال PWA. پس از تأیید مدیر به سند پخش تبدیل می‌شود.</td>
</tr>
<tr>
    <td><code>StoreOrderLines</code></td>
    <td>id, order_id, product_id, qty, unit_price, line_total, is_smart_suggestion</td>
    <td>اقلام سفارش. اگر اقلم از پیشنهاد Smart Reorder آمده باشد، flag می‌خورد.</td>
</tr>
<tr>
    <td><code>PaymentTransactions</code></td>
    <td>id, transaction_no, store_id, gateway (zarinpal/idpay/parsian), amount, status (initiated/paid/failed/verified), authority, ref_id, paid_at, related_doc_type, related_doc_id</td>
    <td>تراکنش‌های پرداخت آنلاین با تفاوت Authority (قبل از پرداخت) و RefID (پس از پرداخت).</td>
</tr>
<tr>
    <td><code>TaxInvoices</code></td>
    <td>id, store_id, sales_id, saman_uid, invoice_status (draft/sent/confirmed/canceled), header_data (JSON), body_data (JSON), sent_at, confirmed_at</td>
    <td>صورت‌حساب الکترونیکی سامان. header_data و body_data ساختار JSON استاندارد سامان.</td>
</tr>
<tr>
    <td><code>Barcodes</code></td>
    <td>id, entity_type (product/lot/sales_order/store_order), entity_id, barcode_value (EAN-13), qr_code_data, created_at</td>
    <td>بارکد و QR برای هر موجودیت قابل اسکن. در فاز ۷ تولید می‌شود.</td>
</tr>
</tbody>
</table>

<h2 class="subsection-title">۴.۷ گروه ۶ — جداول سیستمی (۱۰ جدول)</h2>"""
)

# 6.3 Update relations subsection (renumber 4.7 → 4.8 and add new relations)
text = text.replace(
    '<h2 class="subsection-title">۴.۷ روابط کلیدی ERD</h2>',
    '<h2 class="subsection-title">۴.۸ روابط کلیدی ERD</h2>'
)
text = text.replace(
    '<p>روابط بین جداول در نمودار ERD پیچیده است (با ۴۱ جدول، بیش از ۶۰ رابطه وجود دارد). در اینجا روابط بحرانی که منطق کسب‌وکار را شکل می‌دهند خلاصه شده‌اند. روابط دیگر از طریق Foreign Key‌های مشخص شده در جداول بالا قابل استنباط هستند:</p>',
    '<p>روابط بین جداول در نمودار ERD پیچیده است (با ۴۹ جدول، بیش از ۸۰ رابطه وجود دارد). در اینجا روابط بحرانی که منطق کسب‌وکار را شکل می‌دهند خلاصه شده‌اند. روابط دیگر از طریق Foreign Key‌های مشخص شده در جداول بالا قابل استنباط هستند:</p>'
)
# Add new relations at end of <ul>
text = text.replace(
    '    <li><strong>TransferHeaders ↔ Stores (دو بار):</strong> از from_store و to_store. یک سند انتقال بین دو فروشگاه.</li>\n</ul>',
    """    <li><strong>TransferHeaders ↔ Stores (دو بار):</strong> از from_store و to_store. یک سند انتقال بین دو فروشگاه.</li>
    <li><strong>SalesDraftHeaders ↔ ApprovalQueue:</strong> یک به یک. هر پیش‌نویس عامل، یک رکورد در صف تأیید می‌سازد. پس از تأیید، رکورد SalesHeader ایجاد می‌شود.</li>
    <li><strong>StoreOrders ↔ ApprovalQueue:</strong> یک به یک. هر سفارش فروشگاه وارد صف تأیید می‌شود.</li>
    <li><strong>StoreOrders ↔ PaymentTransactions:</strong> یک به چند. چندین پرداخت ممکن است برای یک سفارش انجام شود (مثلاً ۵۰٪ آنلاین، ۵۰٪ چکی).</li>
    <li><strong>SalesHeaders ↔ TaxInvoices:</strong> یک به یک. هر فروش قطعی پس از commit، یک صورت‌حساب سامان می‌سازد.</li>
    <li><strong>Barcodes ↔ (Product/Lot/SalesOrder):</strong> چندریختی (Polymorphic). هر بارکد به یکی از موجودیت‌ها ارجاع می‌دهد (entity_type + entity_id).</li>
    <li><strong>Stores ↔ LoyaltyPoint:</strong> یک به چند. هر فروشگاه چندین تراکنش وفاداری دارد که امتیاز پویای فعلی محاسبه می‌شود.</li>
</ul>"""
)

print(f"  After Section 4 updates: length = {len(text)}")

src.write_text(text, encoding='utf-8')
print(f"\n  Saved (Step 5-6 complete). Length: {len(text)}")
