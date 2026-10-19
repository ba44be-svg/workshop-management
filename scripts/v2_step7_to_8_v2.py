#!/usr/bin/env python3
"""Step 7-8 (revised): Renumber old sections and insert new ones from file."""
from pathlib import Path
import re

src = Path('/home/z/my-project/scripts/bakery_erd_doc_v2.html')
text = src.read_text(encoding='utf-8')

# ============================================================
# STEP 7: Renumber old sections 9-15 → 14-20
# Use placeholder approach to avoid collisions
# ============================================================
print("STEP 7: Renumbering old sections 9-15 → 14-20...")

# Phase 1: Replace each "SECTION 0X" with placeholder
phase1_replacements = [
    ('SECTION 09', '__SECTION_PH_14__'),
    ('SECTION 10', '__SECTION_PH_15__'),
    ('SECTION 11', '__SECTION_PH_16__'),
    ('SECTION 12', '__SECTION_PH_17__'),
    ('SECTION 13', '__SECTION_PH_18__'),
    ('SECTION 14', '__SECTION_PH_19__'),
    ('SECTION 15', '__SECTION_PH_20__'),
]
for old, new in phase1_replacements:
    if old in text:
        n = text.count(old)
        text = text.replace(old, new)
        print(f"  {old} → {new} ({n} occurrences)")

# Phase 2: Replace placeholder with final section number
phase2_replacements = [
    ('__SECTION_PH_14__', 'SECTION 14'),
    ('__SECTION_PH_15__', 'SECTION 15'),
    ('__SECTION_PH_16__', 'SECTION 16'),
    ('__SECTION_PH_17__', 'SECTION 17'),
    ('__SECTION_PH_18__', 'SECTION 18'),
    ('__SECTION_PH_19__', 'SECTION 19'),
    ('__SECTION_PH_20__', 'SECTION 20'),
]
for old, new in phase2_replacements:
    text = text.replace(old, new)
    print(f"  {old} → {new}")

# Renumber comment markers
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
        print(f"  Renamed comment: {old[:60]}...")

# Helper functions for sub-section renumbering
def find_block_range(text, section_num):
    """Find start and end position of a SECTION block."""
    start_marker = f'<!-- ============ SECTION {section_num}:'
    start_pos = text.find(start_marker)
    if start_pos == -1:
        return None
    next_pos = text.find('<!-- ============ SECTION', start_pos + 1)
    ending_pos = text.find('<!-- ============ ENDING', start_pos)
    candidates = [p for p in [next_pos, ending_pos] if p != -1]
    end_pos = min(candidates) if candidates else len(text)
    return (start_pos, end_pos)

def to_persian(n):
    digits = '۰۱۲۳۴۵۶۷۸۹'
    return ''.join(digits[int(d)] for d in str(n))

# Sub-section numbers to update within each renumbered section block
subsection_updates = [
    (14, ('۹.۱', '۹.۲', '۹.۳')),    # FEFO Transfer (was section 9)
    (15, ('۱۰.۱', '۱۰.۲', '۱۰.۳')),  # SMS (was section 10)
    (16, ('۱۱.۱', '۱۱.۲', '۱۱.۳', '۱۱.۴')),  # Frontend (was section 11)
    (17, ('۱۲.۱', '۱۲.۲', '۱۲.۳')),  # Roadmap (was section 12)
    (18, ('۱۳.۱', '۱۳.۲', '۱۳.۳')),  # Testing (was section 13)
    (19, ('۱۴.۱', '۱۴.۲', '۱۴.۳')),  # Risk (was section 14)
    # Section 20 (Conclusion) has no sub-sections
]

print("\n  Renumbering sub-sections...")
for new_section, subsec_prefixes in subsection_updates:
    new_section_persian = to_persian(new_section)
    block_range = find_block_range(text, new_section)
    if block_range is None:
        print(f"    Section {new_section} block not found, skipping")
        continue
    start, end = block_range
    block_text = text[start:end]
    for old_prefix in subsec_prefixes:
        subsec_num = old_prefix.split('.')[1]
        new_prefix = f'{new_section_persian}.{subsec_num}'
        if old_prefix in block_text:
            block_text = block_text.replace(old_prefix, new_prefix)
            print(f"    {old_prefix} → {new_prefix}")
    text = text[:start] + block_text + text[end:]

# ============================================================
# STEP 8: Insert 5 NEW sections after Section 8 (Auto-Journal)
# ============================================================
print("\nSTEP 8: Inserting 5 new sections (9-13)...")

# Read new sections content from file
new_sections_file = Path('/home/z/my-project/scripts/new_sections.html')
new_sections = new_sections_file.read_text(encoding='utf-8')

# Find insertion point: after Section 8's last table
insertion_marker = """<tr>
    <td>۸</td>
    <td>Notification Service</td>
    <td>ارسال پیامک تأیید به عامل پخش و در صورت لزوم به فروشگاه.</td>
</tr>
</tbody>
</table>"""

if insertion_marker not in text:
    print("  ERROR: insertion marker not found!")
else:
    text = text.replace(insertion_marker, insertion_marker + new_sections)
    print("  Inserted 5 new sections (9-13)")

print(f"\n  After Step 7-8: length = {len(text)}")
src.write_text(text, encoding='utf-8')
print(f"  Saved.")
