#!/usr/bin/env python3
"""Step 7-8: Insert 5 new sections and renumber old 9-15 to 14-20."""
from pathlib import Path
import re

src = Path('/home/z/my-project/scripts/bakery_erd_doc_v2.html')
text = src.read_text(encoding='utf-8')

# ============================================================
# STEP 7: Renumber old sections 9-15 → 14-20
# (Use reverse order + placeholder to avoid collisions)
# ============================================================
print("STEP 7: Renumbering old sections 9-15 → 14-20...")

# We need to do this BEFORE inserting new sections to avoid collisions.
# Use placeholder approach: replace "SECTION 0X" with "__PLACE_X__"
# then replace "__PLACE_X__" with the final new number.

# But the issue: existing v1 has:
# - SECTION 09 (FEFO Transfer Suggester)
# - SECTION 10 (SMS)
# - SECTION 11 (Frontend)
# - SECTION 12 (Roadmap)
# - SECTION 13 (Testing & DevOps)
# - SECTION 14 (Risk Analysis)
# - SECTION 15 (Conclusion)

# Map: 09→14, 10→15, 11→16, 12→17, 13→18, 14→19, 15→20

# Strategy: replace each with placeholder, then placeholder with new number
# To avoid collision (e.g., 09→14, then 14→19 - the second would also catch the renamed 09)

# Use reverse order with placeholders
phase1 = [
    # Find each "SECTION 0X" and replace with placeholder
    ('SECTION 09', '__SECTION_PH_14__'),
    ('SECTION 10', '__SECTION_PH_15__'),
    ('SECTION 11', '__SECTION_PH_16__'),
    ('SECTION 12', '__SECTION_PH_17__'),
    ('SECTION 13', '__SECTION_PH_18__'),
    ('SECTION 14', '__SECTION_PH_19__'),
    ('SECTION 15', '__SECTION_PH_20__'),
]
for old, new in phase1:
    if old in text:
        text = text.replace(old, new)
        print(f"  {old} → {new}")

phase2 = [
    ('__SECTION_PH_14__', 'SECTION 14'),
    ('__SECTION_PH_15__', 'SECTION 15'),
    ('__SECTION_PH_16__', 'SECTION 16'),
    ('__SECTION_PH_17__', 'SECTION 17'),
    ('__SECTION_PH_18__', 'SECTION 18'),
    ('__SECTION_PH_19__', 'SECTION 19'),
    ('__SECTION_PH_20__', 'SECTION 20'),
]
for old, new in phase2:
    text = text.replace(old, new)
    print(f"  {old} → {new}")

# Also rename comment markers
# Comment format: <!-- ============ SECTION 9: ... ============ -->
# (without leading zero)
comment_replacements = [
    ('<!-- ============ SECTION 9: FEFO Transfer', '<!-- ============ SECTION 14: FEFO Transfer'),
    ('<!-- ============ SECTION 10: SMS', '<!-- ============ SECTION 15: SMS'),
    ('<!-- ============ SECTION 11: Frontend', '<!-- ============ SECTION 16: Frontend'),
    ('<!-- ============ SECTION 12: Roadmap', '<!-- ============ SECTION 17: Roadmap'),
    ('<!-- ============ SECTION 13: Testing', '<!-- ============ SECTION 18: Testing'),
    ('<!-- ============ SECTION 14: Risk', '<!-- ============ SECTION 19: Risk'),
    ('<!-- ============ SECTION 15: Conclusion', '<!-- ============ SECTION 20: Conclusion'),
]
for old, new in comment_replacements:
    if old in text:
        text = text.replace(old, new)
        print(f"  {old[:60]} → {new[:60]}")

# Sub-section numbers (Persian numerals)
# Need to update within each renamed section's block
# Sub-section numbers per section (use unique strings):
# ۹.۱, ۹.۲, ۹.۳ → ۱۴.۱, ۱۴.۲, ۱۴.۳
# ۱۰.۱, ۱۰.۲, ۱۰.۳ → ۱۵.۱, ۱۵.۲, ۱۵.۳
# ۱۱.۱, ۱۱.۲, ۱۱.۳, ۱۱.۴ → ۱۶.۱, ۱۶.۲, ۱۶.۳, ۱۶.۴
# ۱۲.۱, ۱۲.۲, ۱۲.۳ → ۱۷.۱, ۱۷.۲, ۱۷.۳
# ۱۳.۱, ۱۳.۲, ۱۳.۳ → ۱۸.۱, ۱۸.۲, ۱۸.۳
# ۱۴.۱, ۱۴.۲, ۱۴.۳ → ۱۹.۱, ۱۹.۲, ۱۹.۳
# ۱۵ has no sub-sections (Conclusion)

# Since we now have "SECTION 14" (FEFO) after renaming, find its range and update
# sub-section numbers within that range

def find_block_range(text, section_num):
    """Find start and end position of a SECTION block."""
    start_marker = f'<!-- ============ SECTION {section_num}:'
    start_pos = text.find(start_marker)
    if start_pos == -1:
        return None
    # Find next SECTION marker
    next_pos = text.find('<!-- ============ SECTION', start_pos + 1)
    ending_pos = text.find('<!-- ============ ENDING', start_pos)
    candidates = [p for p in [next_pos, ending_pos] if p != -1]
    end_pos = min(candidates) if candidates else len(text)
    return (start_pos, end_pos)

# Persian numerals
def to_persian(n):
    digits = '۰۱۲۳۴۵۶۷۸۹'
    return ''.join(digits[int(d)] for d in str(n))

# Map: old_subsection_prefix → new_section_num
# Section 14 (FEFO): had 9.1, 9.2, 9.3
# Section 15 (SMS): had 10.1, 10.2, 10.3
# Section 16 (Frontend): had 11.1, 11.2, 11.3, 11.4
# Section 17 (Roadmap): had 12.1, 12.2, 12.3
# Section 18 (Testing): had 13.1, 13.2, 13.3
# Section 19 (Risk): had 14.1, 14.2, 14.3
# Section 20 (Conclusion): no sub-sections

subsection_updates = [
    # (new_section_num, old_subsection_prefix, old_subsec_number)
    (14, '۹.', '۹.۱', '۹.۲', '۹.۳'),
    (15, '۱۰.', '۱۰.۱', '۱۰.۲', '۱۰.۳'),
    (16, '۱۱.', '۱۱.۱', '۱۱.۲', '۱۱.۳', '۱۱.۴'),
    (17, '۱۲.', '۱۲.۱', '۱۲.۲', '۱۲.۳'),
    (18, '۱۳.', '۱۳.۱', '۱۳.۲', '۱۳.۳'),
    (19, '۱۴.', '۱۴.۱', '۱۴.۲', '۱۴.۳'),
]

for info in subsection_updates:
    new_section = info[0]
    subsec_prefixes = info[2:]  # e.g., ('۹.۱', '۹.۲', '۹.۳')
    new_section_persian = to_persian(new_section)
    
    block_range = find_block_range(text, new_section)
    if block_range is None:
        print(f"  Section {new_section} block not found, skipping subsection renumber")
        continue
    
    start, end = block_range
    block_text = text[start:end]
    
    for old_prefix in subsec_prefixes:
        # Extract the subsec number (after the dot)
        subsec_num = old_prefix.split('.')[1]
        new_prefix = f'{new_section_persian}.{subsec_num}'
        if old_prefix in block_text:
            block_text = block_text.replace(old_prefix, new_prefix)
            print(f"  {old_prefix} → {new_prefix} (in Section {new_section})")
    
    text = text[:start] + block_text + text[end:]

# ============================================================
# STEP 8: Insert 5 NEW sections after Section 8 (Auto-Journal)
# ============================================================
print("\nSTEP 8: Inserting 5 new sections (9-13)...")

# Find insertion point: after the last table of Section 8 (Auto-Journal)
# The last table of Section 8 ends with this content:
insertion_marker = """<tr>
    <td>۸</td>
    <td>Notification Service</td>
    <td>ارسال پیامک تأیید به عامل پخش و در صورت لزوم به فروشگاه.</td>
</tr>
</tbody>
</table>"""

if insertion_marker not in text:
    print("ERROR: insertion marker not found!")
else:
    new_sections = """

<!-- ============ SECTION 9: Distributor Mobile + Approval Workflow ============ -->
<div class="chapter-header">
    <div class="section-tag">SECTION 09</div>
    <div class="section-title">اپلیکیشن موبایل عوامل پخش + جریان تأیید</div>
    <div class="section-subtitle">React Native با بارکدخوان نیتیو، حالت آفلاین و جریان ۴ مرحله‌ای تأیید مدیر</div>
    <div class="divider"></div>
</div>

<h2 class="subsection-title">۹.۱ چرا React Native؟</h2>
<p>انتخاب React Native به‌جای PWA برای اپ عوامل پخش بر اساس سه معیار کلیدی انجام شده: (۱) <strong>بارکدخوان سریع</strong> — هر عامل روزانه ۲۰۰+ بار بارکد می‌زنه، تفاوت ۲ ثانیه‌ای PWA در هر بار جمعاً ۷ دقیقه اتلاف زمان در روز است؛ (۲) <strong>حالت آفلاین پیشرفته</strong> — عوامل در مناطق با اینترنت ناپایدار حرکت می‌کنند و نیاز به ثبت فروش بدون قطعی دارند؛ (۳) <strong>Push Notification پایدار</strong> — یادآوری سرکشی بحرانی است و باید حتی در حالت بسته بودن اپ هم دریافت بشه. React Native با Firebase Cloud Messaging این تضمین را می‌دهد.</p>

<p>React Native امکان دسترسی کامل به سخت‌افزار گوشی (دوربین پیشرفته، GPS با دقت بالا، بلوتوث برای پرینتر دستی، NFC) را فراهم می‌کند. همچنین با یک کد JavaScript، هم نسخه Android و هم iOS تولید می‌شود که هزینه توسعه را نسبت به توسعه جداگانه نیتیو کاهش می‌دهد. انتشار نسخه جدید نیازمند مرور App Store/Google Play (۳-۷ روز) است که باید در نقشه راه لحاظ شود.</p>

<h2 class="subsection-title">۹.۲ جریان ۴ مرحله‌ای تأیید فروش</h2>
<p>با اضافه شدن موبایل عامل، مدل فروش از «ثبت مستقیم» به «ثبت پیش‌نویس + تأیید مدیر» تغییر می‌کند. این تغییر اعمال کنترل مدیریت روی تمام فروش‌های روزانه را قبل از اثر انبار و حسابداری فراهم می‌کند و از خطاهای عمدی یا سهوی عامل جلوگیری می‌کند. جریان چهار مرحله‌ای زیر برای تمام فروش‌ها اعمال می‌شود:</p>

<table>
<thead>
<tr>
    <th style="width: 8%;">مرحله</th>
    <th style="width: 18%;">وضعیت</th>
    <th style="width: 32%;">عمل</th>
    <th style="width: 42%;">اثر سیستم</th>
</tr>
</thead>
<tbody>
<tr>
    <td>۱</td>
    <td><code>pending</code></td>
    <td>عامل در گوشی پیش‌نویس فروش (Draft) ثبت می‌کند. ممکن است آفلاین باشد.</td>
    <td>در گوشی ذخیره می‌شود. وقتی آنترنت برگرده با سرور sync می‌شود. هیچ اثر در DB مرکزی ندارد.</td>
</tr>
<tr>
    <td>۲</td>
    <td><code>reviewing</code></td>
    <td>مدیر در داشبورد وب، پیش‌نویس‌های pending را باز می‌کند.</td>
    <td>یک رکورد در ApprovalQueue ساخته می‌شود با assigned_to=مدیر. پیش‌نویس قفل می‌شود.</td>
</tr>
<tr>
    <td>۳</td>
    <td><code>approved</code> یا <code>rejected</code></td>
    <td>مدیر تأیید یا با reason رد می‌کند.</td>
    <td>اگر تأیید: پیش‌نویس به SalesHeader تبدیل، FEFO اجرا، سند حسابداری ساخته، پیامک به فروشگاه. اگر رد: عامل در اپ پیام دریافت می‌کند.</td>
</tr>
<tr>
    <td>۴</td>
    <td><code>posted</code></td>
    <td>سیستم خودکار، اثرات نهایی را اعمال می‌کند.</td>
    <td>Inventory Movements ثبت، JournalLines ساخته، TaxInvoice برای فروش قطعی ارسال می‌شود.</td>
</tr>
</tbody>
</table>

<h2 class="subsection-title">۹.۳ معماری آفلاین و همگام‌سازی</h2>
<p>اپ موبایل عامل باید در مناطق با اینترنت ناپایدار هم قابل استفاده باشد. معماری آفلاین به این صورت کار می‌کند: هر صبح هنگام شروع روز، اپ آخرین وضعیت موجودی هر فروشگاه اختصاص‌یافته، لیست محصولات، قیمت‌ها و مسیرها را در SQLite محلی گوشی ذخیره می‌کند (Snapshot روزانه). در طول روز، عامل می‌تواند پیش‌نویس فروش بسازد، بارکد بزند و حتی بدون اینترنت کار کند. تمام داده‌ها در IndexedDB محلی ذخیره می‌شوند.</p>

<p>وقتی اینترنت برمی‌گردد، یک Background Service به‌صورت خودکار تمام پیش‌نویس‌های pending را با سرور همگام می‌کند. در صورت بروز تعارض (مثلاً موجودی عامل گفته ۵۰ عدد، اما در سرور فقط ۳۰ عدد باقی مانده چون فروشگاه از منبع دیگری کالا خریده)، خطا لاگ و به مدیر اطلاع داده می‌شود. عامل باید منتظر تأیید مدیر بماند تا تصمیم‌گیری نهایی بشه.</p>

<div class="callout">
    <div class="callout-title">تولید بارکد هنگام ثبت</div>
    <p class="callout-body">هر پیش‌نویس پس از sync شدن، یک بارکد QR دریافت می‌کند که عامل می‌تواند آن را روی رسید چاپ‌شده (با پرینتر بلوتوث دستی) قرار دهد. این QR به مدیر اجازه می‌دهد هنگام بازبینی، با اسکن کد، فوری به جزئیات پیش‌نویس دسترسی پیدا کند.</p>
</div>

<!-- ============ SECTION 10: Store Portal + Online Payment ============ -->
<div class="chapter-header">
    <div class="section-tag">SECTION 10</div>
    <div class="section-title">پورتال فروشگاه‌ها (PWA) + پرداخت آنلاین</div>
    <div class="section-subtitle">B2B Portal با سفارش، کاتالوگ تصویری، پرداخت آنلاین و گزارش‌گیری خودخدمتی</div>
    <div class="divider"></div>
</div>

<h2 class="subsection-title">۱۰.۱ معماری پورتال PWA</h2>
<p>پورتال فروشگاه‌ها یک PWA سبک توسعه داده می‌شود که از طریق URL در مرورگر گوشی یا دسکتاپ قابل دسترسی است. انتخاب PWA به‌جای Native به این دلیل است: (۱) نصب آسان بدون نیاز به دانلود از App Store؛ (۲) آپدیت فوری هنگام انتشار نسخه جدید؛ (۳) حجم کار سبک‌تر از اپ عامل (فقط سفارش، پرداخت، گزارش). PWA با Service Worker و Cache API می‌تواند کاتالوگ محصولات و لیست قیمت‌ها را آفلاین نمایش دهد (بدون نیاز به اینترنت زنده).</p>

<p>پورتال شامل ۵ صفحه اصلی است: داشبورد (مانده حساب + سفارش‌های اخیر)، کاتالوگ محصولات (با تصاویر و توضیحات)، سبد خرید و ثبت سفارش، پرداخت (آنلاین/چکی/نقدی)، و گزارش (خرید ماهانه + گردش حساب + اقلام امانی). تمام صفحات با dir="rtl" و تقویم جلالی طراحی شده‌اند.</p>

<h2 class="subsection-title">۱۰.۲ جریان سفارش و تأیید</h2>
<p>هر فروشگاه می‌تواند سفارش ثبت کند که در نهایت به سند پخش تبدیل می‌شود. جریان سفارش شامل ۶ مرحله است. این جریان تضمین می‌کند که سفارش‌ها قبل از تحویل، هم از نظر موجودی و هم از نظر اعتبار فروشگاه کنترل شوند:</p>

<table>
<thead>
<tr>
    <th style="width: 8%;">مرحله</th>
    <th style="width: 22%;">وضعیت</th>
    <th style="width: 35%;">عمل</th>
    <th style="width: 35%;">اثر سیستم</th>
</tr>
</thead>
<tbody>
<tr>
    <td>۱</td>
    <td><code>cart</code></td>
    <td>فروشگاه اقلام را به سبد اضافه می‌کند (با کلیک یا Smart Suggestion).</td>
    <td>در Session ذخیره می‌شود. اعتبار سنجی اولیه در فرانت‌اند.</td>
</tr>
<tr>
    <td>۲</td>
    <td><code>submitted</code></td>
    <td>فروشگاه سفارش را ثبت می‌کند.</td>
    <td>رکورد StoreOrder ساخته می‌شود با status=submitted. وارد ApprovalQueue می‌شود.</td>
</tr>
<tr>
    <td>۳</td>
    <td><code>under_review</code></td>
    <td>مدیر سفارش را بازبینی می‌کند. کنترل اعتبار و موجودی.</td>
    <td>اگر اعتبار کافی نباشد، مدیر می‌تواند سفارش را اصلاح یا رد کند.</td>
</tr>
<tr>
    <td>۴</td>
    <td><code>approved</code></td>
    <td>مدیر سفارش را تأیید می‌کند.</td>
    <td>سند DispatchHeader ساخته می‌شود. عامل پخش در اپ خودش می‌بیند.</td>
</tr>
<tr>
    <td>۵</td>
    <td><code>in_delivery</code></td>
    <td>عامل سفارش را بارگیری و به فروشگاه تحویل می‌دهد.</td>
    <td>Push Notification به فروشگاه: «سفارش شما در مسیر است».</td>
</tr>
<tr>
    <td>۶</td>
    <td><code>received</code></td>
    <td>فروشگاه در پورتال تأیید می‌کند که دریافت کرده.</td>
    <td>سند SalesHeader ساخته. اثر انبار و حسابداری اعمال می‌شود.</td>
</tr>
</tbody>
</table>

<h2 class="subsection-title">۱۰.۳ درگاه پرداخت آنلاین</h2>
<p>یکپارچگی با ۳ درگاه پرداخت (زرین‌پال، آیدی‌پی، پارسیان) با الگوی Abstract Factory انجام شده تا در صورت قطع یکی، به‌صورت خودکار به دیگری سوییچ شود. هر درگاه یک کلاس جداگانه دارد که از <code>PaymentGatewayInterface</code> ارث می‌برد. انتخاب درگاه پیش‌فرض در تنظیمات سیستم تعریف می‌شود و در صورت خطای یک درگاه، به‌صورت خودکار به fallback منتقل می‌شود.</p>

<div class="code-block"># payments/services/payment_service.py
class PaymentService:
    GATEWAYS = {
        'zarinpal': ZarinpalGateway,
        'idpay': IDPayGateway,
        'parsian': ParsianGateway,
    }
    
    def initiate_payment(self, store_id, amount, related_doc):
        gateway_name = self._select_gateway(amount)
        gateway = self.GATEWAYS[gateway_name]()
        # ساخت رکورد تراکنش با status=initiated
        tx = PaymentTransaction.objects.create(
            store_id=store_id, amount=amount,
            gateway=gateway_name, status='initiated',
            related_doc_type=related_doc._meta.model_name,
            related_doc_id=related_doc.id,
        )
        # درخواست Authority از درگاه
        result = gateway.request_authority(
            amount=amount,
            callback_url=f"{settings.SITE_URL}/payments/callback/{tx.id}/",
            description=f"پرداخت سفارش {related_doc.order_no}",
        )
        tx.authority = result['authority']
        tx.save()
        return {'redirect_url': result['redirect_url'], 'transaction_id': tx.id}
    
    def verify_payment(self, transaction_id, status, authority):
        tx = PaymentTransaction.objects.get(id=transaction_id)
        gateway = self.GATEWAYS[tx.gateway]()
        if status != 'OK':
            tx.status = 'failed'; tx.save()
            return False
        result = gateway.verify(authority=authority, amount=tx.amount)
        if result['verified']:
            tx.status = 'verified'; tx.ref_id = result['ref_id']
            tx.paid_at = timezone.now(); tx.save()
            # اعمال در حسابداری: بستانکار از فروشگاه، بدهکار به بانک
            self._create_payment_journal(tx)
            if tx.related_doc_type == 'storeorder':
                StoreOrder.objects.filter(id=tx.related_doc_id).update(
                    payment_status='paid')
            send_push_notification.delay(store_id=tx.store_id,
                template='payment_success',
                context={'amount': tx.amount, 'ref_id': tx.ref_id})
            return True
        return False</div>

<h2 class="subsection-title">۱۰.۴ کاتالوگ تصویری محصولات</h2>
<p>هر محصول در جدول <code>Products</code> می‌تواند چندین تصویر داشته باشد که در جدول <code>ProductImages</code> ذخیره می‌شوند. تصاویر در Object Storage (MinIO یا S3) نگه‌داری می‌شوند و URL آن‌ها در دیتابیس ذخیره می‌گردد. فرانت‌اند Next.js با استفاده از <code>next/image</code> تصاویر را در چندین رزولوشن (thumbnail، medium، large) تولید و در CDN کش می‌کند تا بارگذاری سریع در گوشی‌های موبایل تضمین شود.</p>

<div class="callout callout-success">
    <div class="callout-title">بهینه‌سازی تصاویر</div>
    <p class="callout-body">تصاویر قبل از ذخیره در Object Storage با کتابخانه Pillow به ۳ رزولوشن پردازش می‌شوند: thumbnail (150x150) برای لیست، medium (400x400) برای جزئیات، و original برای پنجره بزرگ. فرمت WebP با کیفیت ۸۰٪ حجم فایل را تا ۶۰٪ کاهش می‌دهد بدون افت کیفیت محسوس.</p>
</div>

<!-- ============ SECTION 11: Barcode/QR + Smart Reorder + Geo Heatmap ============ -->
<div class="chapter-header">
    <div class="section-tag">SECTION 11</div>
    <div class="section-title">بارکد/QR، Smart Reorder و گزارش جغرافیایی</div>
    <div class="section-subtitle">سه قابلیت تحلیلی و عملیاتی برای افزایش سرعت و کاهش خطا</div>
    <div class="divider"></div>
</div>

<h2 class="subsection-title">۱۱.۱ بارکد و QR Code</h2>
<p>هر محصول، لات و سند در سیستم یک بارکد یکتا دریافت می‌کند. بارکدها به دو فرمت تولید می‌شوند: <strong>EAN-13</strong> (بارکد خطی سنتی) برای محصولات و لات‌ها که با بارکدخوان‌های فیزیکی هم خوانا است، و <strong>QR Code</strong> برای اسناد (سفارش، پیش‌نویس، رسید) که با گوشی موبایل اسکن می‌شوند. انتخاب فرمت بر اساس نوع موجودیت و نحوه استفاده انجام می‌شود. بارکدها در فاز ۷ به‌صورت خودکار توسط یک Celery Task تولید می‌شوند.</p>

<p>در اپ موبایل عامل، بارکدخوان نیتیو با کتابخانه <code>react-native-vision-camera</code> پیاده‌سازی شده که از تشخیص چند بارکد هم‌زمان و حالت اسکن سریع پشتیبانی می‌کند. هنگام اسکن بارکد محصول در حال ثبت پیش‌نویس فروش، سیستم به‌طور خودکار محصول را شناسایی، قیمت مخصوص آن فروشگاه را از جدول <code>PricingRules</code> می‌خواند و در سبد اضافه می‌کند. این کار سرعت ثبت فروش را ۳ برابر افزایش می‌دهد.</p>

<h2 class="subsection-title">۱۱.۲ الگوریتم Smart Reorder</h2>
<p>سیستم Smart Reorder با تحلیل داده‌های فروش هفتگی گذشته، به فروشگاه‌ها پیشنهاد سفارش می‌دهد. این پیشنهادها در پورتال PWA نمایش داده می‌شوند و فروشگاه می‌تواند با یک کلیک آن‌ها را به سبد اضافه کند. این قابلیت از یک الگوریتم پیش‌بینی ساده اما مؤثر استفاده می‌کند که در مرحله اول روی داده‌های موجود کار می‌کند و در آینده با ML می‌تواند بهبود یابد:</p>

<div class="code-block"># loyalty/services/smart_reorder.py
def generate_reorder_suggestions(store_id: int):
    """تولید پیشنهاد سفارش برای یک فروشگاه بر اساس داده‌های ۲ هفته گذشته."""
    today = timezone.now().date()
    last_14_days = today - timedelta(days=14)
    
    # نرخ فروش روزانه هر محصول در این فروشگاه
    sales_velocity = (
        SalesLine.objects
        .filter(sale__store_id=store_id, sale__sale_date__gte=last_14_days)
        .values('product_id')
        .annotate(daily_rate=Sum('qty') / 14.0)
    )
    
    suggestions = []
    for item in sales_velocity:
        product_id = item['product_id']
        daily_rate = item['daily_rate']
        if daily_rate &lt;= 0:
            continue
        # موجودی فعلی این محصول در این فروشگاه
        current_stock = (
            InventoryLot.objects
            .filter(product_id=product_id, warehouse__store_id=store_id, current_qty__gt=0)
            .aggregate(total=Sum('current_qty'))['total'] or 0
        )
        # Days of Stock
        dos = current_stock / daily_rate if daily_rate > 0 else 999
        # اگر موجودی کمتر از ۳ روز است، پیشنهاد سفارش
        if dos &lt; 3:
            suggested_qty = max(int(daily_rate * 7), 10)
            # بررسی محدودیت اعتبار فروشگاه
            store = Store.objects.get(id=store_id)
            if not check_credit_limit(store, suggested_qty * product.default_price):
                suggested_qty = adjust_to_credit_limit(store, suggested_qty)
            suggestions.append(ReorderSuggestion(
                store_id=store_id, product_id=product_id,
                suggested_qty=suggested_qty, daily_rate=daily_rate,
                current_stock=current_stock, days_of_stock=dos,
                confidence_score=calculate_confidence(daily_rate, dos),
            ))
    return sorted(suggestions, key=lambda x: x.days_of_stock)</div>

<h2 class="subsection-title">۱۱.۳ گزارش جغرافیایی Heatmap</h2>
<p>گزارش جغرافیایی به مدیر امکان می‌دهد توزیع فروش را روی نقشه ایران به‌صورت بصری مشاهده کند. هر فروشگاه با مختصات GPS در جدول <code>Stores</code> ذخیره شده و حجم فروش هر فروشگاه در ماه جاری به رنگ هر نقطه تبدیل می‌شود. رنگ از سبز (کم‌فروش) تا قرمز (پرفروش) متغیر است. این دید بصری به مدیر کمک می‌کند مناطق با پتانسیل رشد را شناسایی کند و منابع عامل پخش را بهینه تخصیص دهد.</p>

<p>پیاده‌سازی با استفاده از کتابخانه <code>react-leaflet</code> در فرانت‌اند و یک API اختصاصی در بک‌اند انجام می‌شود. API فروش‌های تجمیعی ماهانه را بر اساس فروشگاه برمی‌گرداند. برای عملکرد بالا، نتیجه کوئری به‌صورت ۱۵ دقیقه‌ای در Redis کش می‌شود. این گزارش در داشبورد مدیر در فاز ۷ پیاده‌سازی خواهد شد.</p>

<!-- ============ SECTION 12: Saman Tax + Loyalty ============ -->
<div class="chapter-header">
    <div class="section-tag">SECTION 12</div>
    <div class="section-title">صورت‌حساب الکترونیکی سامان + وفاداری فروشگاه‌ها</div>
    <div class="section-subtitle">یکپارچگی با سامانه مالیاتی و برنامه امتیاز پویا</div>
    <div class="divider"></div>
</div>

<h2 class="subsection-title">۱۲.۱ صورت‌حساب الکترونیکی (سامان)</h2>
<p>از سال ۱۴۰۳، تمام کسب‌وکارهای ایرانی موظف به ارسال صورت‌حساب الکترونیکی به سامانه پایانه‌های مالیاتی (سامان) هستند. این سرویس برای تمام فروش‌های قطعی (Firm Sale) که در آن مالکیت به فروشگاه منتقل می‌شود، باید فعال باشد. فروش‌های امانی (Consignment) تا زمان فروش نهایی به مصرف‌کننده نیازی به صورت‌حساب ندارند.</p>

<p>یکپارچگی با سامان از طریق REST API رسمی انجام می‌شود. هر فروش قطعی پس از commit، به‌صورت خودکار در جدول <code>TaxInvoices</code> یک رکورد می‌سازد با status=draft، سپس با API سامان به‌عنوان یک پیش‌نویس ارسال می‌شود، UID دریافت و در دیتابیس ذخیره می‌گردد. در صورت تأیید سامان، status به confirmed تغییر می‌کند. در صورت نیاز به اصلاح، با ارسال یک رکورد جدید با نوع اصلاحیه انجام می‌شود.</p>

<div class="callout callout-warning">
    <div class="callout-title">تأخیر احتمالی سامان</div>
    <p class="callout-body">سامان ممکن است در زمان ارسال با تأخیر یا خطا پاسخ دهد. در این حالت، یک Celery Task تلاش مجدد با Exponential Backoff انجام می‌دهد. اگر پس از ۵ تلاش ناموفق باشد، به مدیر اطلاع داده می‌شود تا به‌صورت دستی ارسال شود. فروش در دیتابیس قبلاً commit شده و صورتحساب سامان جداگانه ثبت می‌گردد.</p>
</div>

<h2 class="subsection-title">۱۲.۲ برنامه وفاداری فروشگاه‌ها</h2>
<p>هر فروشگاه بر اساس رفتار خود (حجم خرید، به موقع پرداخت، عدم برگشت) امتیاز پویا جمع می‌کند. این امتیاز در سه لایه (Tier) دسته‌بندی می‌شود که هر کدام تخفیف یا مزیت متفاوتی دارند. این الگو انگیزه رفتار بهتر فروشگاه‌ها را افزایش می‌دهد و در عین حال به کسب‌وکار اجازه می‌دهد تخفیف‌های استراتژیک به فروشگاه‌های ارزشمند بدهد.</p>

<table>
<thead>
<tr>
    <th style="width: 14%;">Tier</th>
    <th style="width: 18%;">امتیاز لازم</th>
    <th style="width: 30%;">مزیت</th>
    <th style="width: 38%;">شرط کسب</th>
</tr>
</thead>
<tbody>
<tr>
    <td><strong>Silver</strong></td>
    <td>۱۰۰+ امتیاز</td>
    <td>تخفیف ۲٪ روی تمام سفارش‌ها، اولویت در تحویل</td>
    <td>خرید ماهانه &gt; ۵۰ میلیون، عدم تأخیر در پرداخت &gt; ۳۰ روز</td>
</tr>
<tr>
    <td><strong>Gold</strong></td>
    <td>۵۰۰+ امتیاز</td>
    <td>تخفیف ۵٪، اولویت در سفارش‌های پرفروش، Push Notification ویژه</td>
    <td>خرید ماهانه &gt; ۲۰۰ میلیون، عدم تأخیر &gt; ۱۵ روز، نرخ برگشت &lt; ۵٪</td>
</tr>
<tr>
    <td><strong>Platinum</strong></td>
    <td>۱۰۰۰+ امتیاز</td>
    <td>تخفیف ۸٪، اعتبار افزایش ۵۰٪، دسترسی به محصولات ویژه</td>
    <td>خرید ماهانه &gt; ۵۰۰ میلیون، عدم تأخیر &gt; ۷ روز، نرخ برگشت &lt; ۲٪</td>
</tr>
</tbody>
</table>

<p>محاسبه امتیاز هر ماه به‌صورت خودکار توسط یک Celery Task شبانه انجام می‌شود. هر تراکنش (خرید، پرداخت به موقع، عدم برگشت) به امتیاز اضافه و در جدول <code>LoyaltyTransaction</code> ذخیره می‌شود. ارتقاء یا تنزل Tier به‌صورت خودکار اتفاق می‌افتد و فروشگاه با Push Notification آگاه می‌شود.</p>

<!-- ============ SECTION 13: Push Notifications ============ -->
<div class="chapter-header">
    <div class="section-tag">SECTION 13</div>
    <div class="section-title">Push Notification و یکپارچگی Firebase</div>
    <div class="section-subtitle">ارسال اعلان موبایل رایگان و سریع به عوامل و فروشگاه‌ها</div>
    <div class="divider"></div>
</div>

<h2 class="subsection-title">۱۳.۱ چرا Firebase Cloud Messaging؟</h2>
<p>پیامک از پروایدرهای ایرانی هزینه‌بر است (هر پیامک حدود ۳۰۰ ریال) و در حجم بالا (مثلاً ۵۰ هزار پیام در ماه) هزینه قابل توجهی می‌شود. Firebase Cloud Messaging (FCM) رایگان است و Push Notification را به اپ‌های Android و iOS می‌فرستد. برای اپ Native (React Native) که در فاز ۵ توسعه می‌یابد، FCM بهترین انتخاب است. برای PWA فروشگاه‌ها از Web Push API استفاده می‌شود که FCM هم از آن پشتیبانی می‌کند.</p>

<p>این روش دو مزیت اصلی دارد: (۱) هزینه‌های پیامک کاهش ۷۰-۸۰٪ می‌یابد زیرا اکثر اعلان‌ها از طریق Push ارسال می‌شوند؛ (۲) Push Notification می‌تواند تصویر، دکمه‌های اکشن و لینک به صفحه خاص داشته باشد که پیامک متنی نمی‌تواند. برای اعلان‌های بحرانی (مثلاً یادآوری سرکشی عامل که اگر جا بیافتد ضرر بزرگی دارد)، هم Push و هم SMS به‌صورت موازی ارسال می‌شوند تا اطمینان از دریافت ۱۰۰٪ باشد.</p>

<h2 class="subsection-title">۱۳.۲ سناریوهای Push Notification</h2>
<p>جدول زیر سناریوهای اصلی Push Notification و قالب هر کدام را نشان می‌دهد. هر قالب در جدول <code>PushTemplates</code> ذخیره و قابل ویرایش از طریق Admin Django است:</p>

<table>
<thead>
<tr>
    <th style="width: 22%;">سناریو</th>
    <th style="width: 14%;">دریافت‌کننده</th>
    <th style="width: 64%;">متن و دکمه اکشن</th>
</tr>
</thead>
<tbody>
<tr>
    <td>یادآوری سرکشی</td>
    <td>عامل</td>
    <td>«{{distributor_name}}، شروع سرکشی ساعت {{start_time}}. اولین فروشگاه: {{first_store}}.» + دکمه «شروع»</td>
</tr>
<tr>
    <td>تأیید سفارش</td>
    <td>فروشگاه</td>
    <td>«سفارش {{order_no}} شما تأیید شد. تحویل فردا.» + دکمه «مشاهده»</td>
</tr>
<tr>
    <td>رد پیش‌نویس</td>
    <td>عامل</td>
    <td>«پیش‌نویس {{draft_no}} رد شد. دلیل: {{reason}}.» + دکمه «اصلاح»</td>
</tr>
<tr>
    <td>تأیید پرداخت</td>
    <td>فروشگاه</td>
    <td>«پرداخت {{amount}} ریال دریافت شد. کد پیگیری: {{ref_id}}.» + دکمه «رسید»</td>
</tr>
<tr>
    <td>ارتقاء Tier</td>
    <td>فروشگاه</td>
    <td>«تبریک! شما به Tier {{tier_name}} ارتقا یافتید. تخفیف {{discount}}٪ از همین سفارش فعال است.» + دکمه «سفارش جدید»</td>
</tr>
<tr>
    <td>هشدار انقضای کالا</td>
    <td>مدیر</td>
    <td>«{{count}} لات نزدیک به انقضا. اولویت: {{highest}}.» + دکمه «داشبورد»</td>
</tr>
<tr>
    <td>خطای توازن سند</td>
    <td>حسابدار</td>
    <td>«سند {{journal_no}} نامتوازن است. اختلاف: {{diff}}.» + دکمه «بررسی»</td>
</tr>
</tbody>
</table>

<h2 class="subsection-title">۱۳.۳ پیاده‌سازی FCM در بک‌اند</h2>
<p>سرویس Push در بک‌اند با Firebase Admin SDK پیاده‌سازی می‌شود. هر کاربر هنگام ورود به اپ، توکن FCM خود را در جدول <code>UserProfiles.fcm_token</code> ذخیره می‌کند. وقتی سیستمی می‌خواهد Push بفرستد، توکن کاربر را می‌خواند و با SDK به Firebase می‌فرستد. Firebase خودش به دستگاه کاربر تحویل می‌دهد. در صورت خطا (مثلاً توکن منقضی شده)، سیستم توکن را از دیتابیس حذف می‌کند تا حجم دیتابیس کنترل شود.</p>

<div class="code-block"># notifications/services/push_service.py
from firebase_admin import messaging, initialize_app
import firebase_admin

firebase_admin.initialize_app()

class PushService:
    def send_to_user(self, user_id, title, body, data=None):
        """ارسال Push به یک کاربر."""
        profile = UserProfile.objects.get(user_id=user_id)
        if not profile.fcm_token:
            return False
        message = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            data=data or {},
            token=profile.fcm_token,
            android=messaging.AndroidConfig(priority='high'),
            apns=messaging.APNSConfig(payload=messaging.APNSPayload(
                aps=messaging.Aps(badge=1, sound='default'))),
        )
        try:
            messaging.send(message)
            return True
        except messaging.UnregisteredError:
            profile.fcm_token = None
            profile.save()
            return False
        except Exception as e:
            logger.error(f"FCM send failed: {e}")
            return False</div>

<div class="callout">
    <div class="callout-title">استراتژی دوگانه Push + SMS</div>
    <p class="callout-body">برای اعلان‌های بحرانی (یادآوری سرکشی، خطای توازن، رد سفارش)، هر دو روش Push و SMS به‌صورت موازی ارسال می‌شوند. این تضمین می‌کند حتی اگر گوشی کاربر خاموش یا بدون اینترنت باشد، پیامک دریافت شود. برای اعلان‌های غیر بحرانی (مثلاً اطلاع از ارتقاء Tier)، فقط Push ارسال می‌شود تا هزینه کاهش یابد.</p>
</div>

"""
    text = text.replace(insertion_marker, insertion_marker + new_sections)
    print("  Inserted 5 new sections (9-13)")

print(f"\n  After Step 7-8: length = {len(text)}")
src.write_text(text, encoding='utf-8')
print(f"  Saved.")
