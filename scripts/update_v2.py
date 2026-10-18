#!/usr/bin/env python3
"""Update v2 HTML: replace cake-related terms with generic product terms."""
import re
from pathlib import Path

src = Path('/home/z/my-project/scripts/bakery_erd_doc_v2.html')
text = src.read_text(encoding='utf-8')

# Order matters: longer phrases first to avoid partial matches
replacements = [
    # Title in HTML <title> tag
    ('نرم‌افزار مدیریت تولید و پخش کیک‌پزی',
     'نرم‌افزار مدیریت تولید و پخش کارگاه تولیدی'),
    # Cover title
    ('نرم‌افزار جامع مدیریت تولید و پخش کیک‌پزی',
     'نرم‌افزار جامع مدیریت تولید و پخش کارگاه تولیدی'),
    # Workshop naming
    ('کارگاه کیک‌پزی', 'کارگاه تولیدی'),
    ('صنعت کیک‌پزی', 'صنعت تولید'),
    ('کسب‌وکار کیک‌پزی', 'کسب‌وکار تولیدی'),
    ('تولید کیک‌پزی', 'تولید کارگاهی'),
    # Specific examples in lists
    ('۳۰ نوع کیک با دسته‌بندی‌های مختلف (کرمی، شکلاتی، میوه‌ای، ویژه مناسبتی)',
     '۳۰ نوع محصول با دسته‌بندی‌های مختلف (گروه A، گروه B، گروه C، ویژه مناسبتی)'),
    ('۳۰ نوع کیک با تاریخ انقضای کوتاه',
     '۳۰ نوع محصول با تاریخ انقضای کوتاه'),
    # Generic cake references
    ('هر کیک بین ۱۲ تا ۱۵ روز ماندگاری', 'هر محصول بین ۱۲ تا ۱۵ روز ماندگاری'),
    # Category tree example
    ('کیک کرمی → کیک کرمی کوچک', 'گروه A → گروه A - نوع ۱'),
    # Coding example
    ('۱۰۱۱ → کیک کرمی', '۱۰۱۱ → محصول نمونه A'),
    # Numeric example in weighted average section
    ('چرخه تولید و فروش کیک کرمی کوچک', 'چرخه تولید و فروش محصول نمونه A'),
    # Traceability questions
    ('این کیک که در فروشگاه X فروخته شد', 'این محصول که در فروشگاه X فروخته شد'),
    ('کیفیت یک کیک', 'کیفیت یک محصول'),
    # Industry mention
    ('صنایع غذایی و دارویی حیاتی است زیرا تضمین می‌کند کالاهای با مدت ماندگاری کمتر اول خروج کنند',
     'صنایع حساس به انقضا (غذایی، دارویی، بهداشتی) حیاتی است زیرا تضمین می‌کند کالاهای با مدت ماندگاری کمتر اول خروج کنند'),
]

count = 0
for old, new in replacements:
    if old in text:
        n = text.count(old)
        text = text.replace(old, new)
        print(f"  [{n}x] {old[:50]}... → {new[:50]}...")
        count += n

# Verify no "کیک" remains
remaining = text.count('کیک')
print(f"\nRemaining 'کیک' instances: {remaining}")

# Save
src.write_text(text, encoding='utf-8')
print(f"\nDone. {count} total replacements. Saved to {src}")
