#!/usr/bin/env python3
"""Comprehensive v2 update script - apply all changes atomically."""
import re
from pathlib import Path

src = Path('/home/z/my-project/scripts/bakery_erd_doc_v2.html')
text = src.read_text(encoding='utf-8')
orig_len = len(text)

# ============================================================
# STEP 1: Global text replacements (cake → product)
# ============================================================
print("STEP 1: Global text replacements...")
text_replacements = [
    ('نرم‌افزار مدیریت تولید و پخش کیک‌پزی',
     'نرم‌افزار مدیریت تولید و پخش کارگاه تولیدی'),
    ('نرم‌افزار جامع مدیریت تولید و پخش کیک‌پزی',
     'نرم‌افزار جامع مدیریت تولید و پخش کارگاه‌های تولیدی'),
    ('کارگاه کیک‌پزی', 'کارگاه تولیدی'),
    ('صنعت کیک‌پزی', 'صنعت تولید'),
    ('کسب‌وکار کیک‌پزی', 'کسب‌وکار تولیدی'),
    ('تولید کیک‌پزی', 'تولید کارگاهی'),
    ('۳۰ نوع کیک با دسته‌بندی‌های مختلف (کرمی، شکلاتی، میوه‌ای، ویژه مناسبتی)',
     '۳۰ نوع محصول با دسته‌بندی‌های مختلف (گروه A، گروه B، گروه C، ویژه مناسبتی)'),
    ('۳۰ نوع کیک با تاریخ انقضای کوتاه',
     '۳۰ نوع محصول با تاریخ انقضای کوتاه'),
    ('هر کیک بین ۱۲ تا ۱۵ روز ماندگاری', 'هر محصول بین ۱۲ تا ۱۵ روز ماندگاری'),
    ('کیک کرمی → کیک کرمی کوچک', 'گروه A → گروه A - نوع ۱'),
    ('۱۰۱۱ → کیک کرمی', '۱۰۱۱ → محصول نمونه A'),
    ('چرخه تولید و فروش کیک کرمی کوچک', 'چرخه تولید و فروش محصول نمونه A'),
    ('این کیک که در فروشگاه X فروخته شد', 'این محصول که در فروشگاه X فروخته شد'),
    ('کیفیت یک کیک', 'کیفیت یک محصول'),
    ('صنایع غذایی و دارویی حیاتی است زیرا تضمین می‌کند کالاهای با مدت ماندگاری کمتر اول خروج کنند',
     'صنایع حساس به انقضا (غذایی، دارویی، بهداشتی) حیاتی است زیرا تضمین می‌کند کالاهای با مدت ماندگاری کمتر اول خروج کنند'),
]
for old, new in text_replacements:
    if old in text:
        n = text.count(old)
        text = text.replace(old, new)
        print(f"  [{n}x] {old[:50]}...")

# ============================================================
# STEP 2: Cover & badge updates
# ============================================================
print("\nSTEP 2: Cover updates...")
text = text.replace(
    '<div class="cover-badge">سند فنی / نسخه ۱.۰</div>',
    '<div class="cover-badge">سند فنی / نسخه ۲.۰</div>'
)
text = text.replace(
    '<div class="cover-title">نرم‌افزار جامع مدیریت تولید و پخش کارگاه‌های تولیدی</div>',
    '<div class="cover-title">نرم‌افزار جامع مدیریت تولید و پخش کارگاه‌های تولیدی</div>'
)
text = text.replace(
    '<div class="cover-subtitle">سند معماری فنی، طراحی پایگاه داده (ERD) و نقشه راه اجرایی برای جایگزینی سیستم شکننده فعلی با یک پلتفرم پایدار، چندکاربره و تحت وب.</div>',
    '<div class="cover-subtitle">سند معماری فنی، طراحی پایگاه داده (ERD) و نقشه راه اجرایی برای جایگزینی سیستم شکننده فعلی با یک پلتفرم پایدار، چندکاربره و تحت وب — شامل اپلیکیشن موبایل عوامل پخش (Native) و پورتال B2B فروشگاه‌ها (PWA).</div>'
)
text = text.replace(
    """        <span class="cover-tag">RTL / Vazirmatn</span>
        <span class="cover-tag">FEFO / Weighted Avg</span>
        <span class="cover-tag">Multi-tenant</span>""",
    """        <span class="cover-tag">React Native</span>
        <span class="cover-tag">PWA (Store)</span>
        <span class="cover-tag">Zarinpal/Saman</span>
        <span class="cover-tag">Barcode/QR</span>
        <span class="cover-tag">Firebase Push</span>"""
)

# ============================================================
# STEP 3: Executive Summary updates
# ============================================================
print("\nSTEP 3: Executive Summary updates...")
# Add note about v2
text = text.replace(
    '<p>این سند معماری برای طراحی و پیاده‌سازی یک <strong>نرم‌افزار جامع مدیریت تولید و پخش</strong> برای یک کارگاه تولیدی متوسط‌بزرگ تهیه شده است. هدف اصلی پروژه جایگزینی یک فایل نرم‌افزاری شکننده فعلی با یک سیستم پایدار، چندکاربره و تحت وب است که بتواند منطق پیچیده تولید، انبار، فروش و حسابداری را در یک پلتفرم یکپارچه مدیریت کند.</p>',
    '<p>این سند معماری برای طراحی و پیاده‌سازی یک <strong>نرم‌افزار جامع مدیریت تولید و پخش</strong> برای یک کارگاه تولیدی متوسط‌بزرگ تهیه شده است. هدف اصلی پروژه جایگزینی یک فایل نرم‌افزاری شکننده فعلی با یک سیستم پایدار، چندکاربره و تحت وب است. نسخه ۲.۰ این سند با اضافه شدن دو رابط موبایل (اپ Native برای عوامل پخش و پورتال PWA برای فروشگاه‌ها) و ۸ قابلیت تکمیلی، پلتفرم را از یک سیستم داخلی به یک بازار تجاری B2B تبدیل می‌کند.</p>'
)
# Update stats
text = text.replace(
    """<div class="stat-grid">
    <div class="stat-card">
        <div class="stat-value">۴۱</div>
        <div class="stat-label">جدول پایگاه داده</div>
    </div>
    <div class="stat-card">
        <div class="stat-value">۸ ماه</div>
        <div class="stat-label">مدت توسعه</div>
    </div>
    <div class="stat-card">
        <div class="stat-value">۶</div>
        <div class="stat-label">فاز اجرایی</div>
    </div>
</div>""",
    """<div class="stat-grid">
    <div class="stat-card">
        <div class="stat-value">۴۹</div>
        <div class="stat-label">جدول پایگاه داده</div>
    </div>
    <div class="stat-card">
        <div class="stat-value">۱۰ ماه</div>
        <div class="stat-label">مدت توسعه</div>
    </div>
    <div class="stat-card">
        <div class="stat-value">۸</div>
        <div class="stat-label">فاز اجرایی</div>
    </div>
</div>"""
)
# Update tech paragraph
text = text.replace(
    '<p>از نظر فنی، سیستم با <strong>Django 4.2 + Django REST Framework</strong> در بک‌اند، <strong>PostgreSQL 16</strong> به‌عنوان پایگاه داده مرکزی، و <strong>Next.js 14 + TypeScript + Tailwind RTL</strong> در فرانت‌اند پیاده‌سازی می‌شود. Redis برای کش و صف Celery برای کارهای پس‌زمینه (ارسال پیامک، گزارش‌گیری، هشدار انقضا) استفاده خواهد شد. تمام ۴۱ جدول کسب‌وکار در یک پایگاه داده مرکزی با پشتیبانی کامل از ACID و تراکنش‌های دوطرفه طراحی شده‌اند.</p>',
    '<p>از نظر فنی، سیستم با <strong>Django 4.2 + Django REST Framework</strong> در بک‌اند، <strong>PostgreSQL 16</strong> به‌عنوان پایگاه داده مرکزی، و <strong>Next.js 14 + TypeScript + Tailwind RTL</strong> در فرانت‌اند وب پیاده‌سازی می‌شود. برای عوامل پخش، <strong>اپ React Native</strong> با بارکدخوان نیتیو و حالت آفلاین پیشرفته ارائه می‌شود. برای فروشگاه‌ها، یک <strong>پورتال PWA</strong> با قابلیت سفارش آنلاین، پرداخت از طریق درگاه‌های زرین‌پال/آیدی‌پی/پارسیان و گزارش‌گیری خودکار طراحی شده. Redis برای کش و صف Celery برای کارهای پس‌زمینه (ارسال پیامک، Push Notification، گزارش‌گیری، هشدار انقضا) استفاده خواهد شد. تمام ۴۹ جدول کسب‌وکار در یک پایگاه داده مرکزی با پشتیبانی کامل از ACID و تراکنش‌های دوطرفه طراحی شده‌اند.</p>'
)
# Update roadmap paragraph
text = text.replace(
    '<p>نقشه راه توسعه شش‌فازی در هشت ماه شامل: (۱) بن‌بست و مدل پایه، (۲) تولید و انبار، (۳) فروش و پخش، (۴) حسابداری و گزارش، (۵) موبایل و اعلان، و (۶) تست و بهینه‌سازی است. این فازبندی به تیم اجازه می‌دهد در هر مرحله یک MVP قابل دمو تحویل دهد و در عین حال ریسک‌های فنی را در همان مراحل اولیه شناسایی کند.</p>',
    '<p>نقشه راه توسعه هشت‌فازی در ده ماه شامل: (۱) بن‌بست و مدل پایه، (۲) تولید و انبار، (۳) فروش و پخش، (۴) حسابداری و گزارش، (۵) موبایل عامل (React Native) با جریان تأیید، (۶) پورتال فروشگاه (PWA) با پرداخت آنلاین، (۷) بارکد/QR و Smart Reorder، (۸) تست، بهینه‌سازی و یکپارچگی‌های نهایی است. این فازبندی به تیم اجازه می‌دهد در هر مرحله یک MVP قابل دمو تحویل دهد و در عین حال ریسک‌های فنی را در همان مراحل اولیه شناسایی کند.</p>'
)
# Replace key benefits with new features list
text = text.replace(
    """<div class="callout">
    <div class="callout-title">مزایای کلیدی</div>
    <p class="callout-body">سیستم پیشنهادی به‌طور خودکار اسناد حسابداری دوطرفه را به محض ثبت فروش یا خرید تولید می‌کند، کالاهای نزدیک به انقضا را شناسایی و انتقال از فروشگاه‌های کم‌فروش به پرفروش را پیشنهاد می‌دهد، و با ارسال پیامک خودکار، یادآوری سرکشی به عوامل پخش را مدیریت می‌کند. این مزایا در یک پلتفرم با پشتیبانی کامل از RTL، تقویم شمسی و دسترسی چندکاربره همگرا شده‌اند.</p>
</div>""",
    """<div class="callout">
    <div class="callout-title">قابلیت‌های جدید نسخه ۲.۰</div>
    <p class="callout-body">این نسخه با اضافه شدن ۸ قابلیت تکمیلی، ارزش کسب‌وکار را به طور قابل توجهی افزایش می‌دهد: (۱) مدیریت اعتبار فروشگاه با سقف پویا، (۲) بارکد و QR Code برای هر محصول/لات/سفارش، (۳) یکپارچگی با سامانه مالیاتی سامان برای صورت‌حساب الکترونیکی، (۴) درگاه پرداخت آنلاین (زرین‌پال، آیدی‌پی، پارسیان)، (۵) سیستم Smart Reorder بر اساس نرخ فروش، (۶) برنامه وفاداری فروشگاه‌ها با امتیاز پویا، (۷) گزارش جغرافیایی Heatmap، و (۸) Push Notification با Firebase Cloud Messaging.</p>
</div>"""
)

# ============================================================
# STEP 4: Section 2 (Architecture) updates
# ============================================================
print("\nSTEP 4: Architecture updates...")
text = text.replace(
    """        <div class="arch-boxes">
            <div class="arch-box primary">Next.js 14 (SSR/CSR)</div>
            <div class="arch-box primary">PWA Mobile (عوامل پخش)</div>
            <div class="arch-box">Tailwind CSS RTL</div>
            <div class="arch-box">Vazirmatn Font</div>
            <div class="arch-box">Jalaali-js Calendar</div>
        </div>""",
    """        <div class="arch-boxes">
            <div class="arch-box primary">Next.js 14 (Admin Web)</div>
            <div class="arch-box primary">React Native (عوامل پخش)</div>
            <div class="arch-box primary">PWA (فروشگاه‌ها)</div>
            <div class="arch-box">Tailwind CSS RTL</div>
            <div class="arch-box">Vazirmatn Font</div>
            <div class="arch-box">Jalaali-js Calendar</div>
            <div class="arch-box">Barcode Scanner (Native)</div>
            <div class="arch-box">Firebase Push</div>
        </div>"""
)
text = text.replace(
    """        <div class="arch-boxes">
            <div class="arch-box primary">Inventory Service</div>
            <div class="arch-box primary">Production Service</div>
            <div class="arch-box primary">Sales &amp; Dispatch Service</div>
            <div class="arch-box primary">Accounting Service</div>
            <div class="arch-box primary">Notification Service</div>
            <div class="arch-box">Reporting Service</div>
        </div>""",
    """        <div class="arch-boxes">
            <div class="arch-box primary">Inventory Service</div>
            <div class="arch-box primary">Production Service</div>
            <div class="arch-box primary">Sales &amp; Dispatch Service</div>
            <div class="arch-box primary">Approval Workflow Service</div>
            <div class="arch-box primary">Store Portal Service</div>
            <div class="arch-box primary">Payments Service</div>
            <div class="arch-box primary">Accounting Service</div>
            <div class="arch-box primary">Notification Service (SMS+Push)</div>
            <div class="arch-box primary">Loyalty &amp; Smart Reorder</div>
            <div class="arch-box">Reporting &amp; Geo Service</div>
        </div>"""
)
text = text.replace(
    """        <div class="arch-boxes">
            <div class="arch-box primary">PostgreSQL 16 (41 Tables)</div>
            <div class="arch-box">Redis (Cache &amp; Sessions)</div>
            <div class="arch-box">MinIO / S3 (Files)</div>
        </div>""",
    """        <div class="arch-boxes">
            <div class="arch-box primary">PostgreSQL 16 (49 Tables)</div>
            <div class="arch-box">Redis (Cache &amp; Sessions)</div>
            <div class="arch-box">MinIO / S3 (Files &amp; Images)</div>
            <div class="arch-box">Firebase Firestore (Mobile Sync)</div>
        </div>"""
)
text = text.replace(
    """        <div class="arch-boxes">
            <div class="arch-box">Kavenegar SMS API</div>
            <div class="arch-box">Farapayamak (Backup)</div>
            <div class="arch-box">Instagram Graph API</div>
            <div class="arch-box">SnappFood API</div>
        </div>""",
    """        <div class="arch-boxes">
            <div class="arch-box">Kavenegar SMS API</div>
            <div class="arch-box">Farapayamak (Backup)</div>
            <div class="arch-box">Zarinpal Payment</div>
            <div class="arch-box">IDPay Payment</div>
            <div class="arch-box">Parsian Bank Gateway</div>
            <div class="arch-box">Saman Tax (e-Invoice)</div>
            <div class="arch-box">Firebase Cloud Messaging</div>
            <div class="arch-box">Google Maps API</div>
        </div>"""
)

print(f"\n  After Step 4: text length = {len(text)} (was {orig_len})")

src.write_text(text, encoding='utf-8')
print(f"\n  Saved (Step 1-4 complete). Length: {len(text)}")
