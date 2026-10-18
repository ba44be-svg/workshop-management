#!/usr/bin/env python3
"""Renumber sections 9-15 to 14-20 in v2 HTML."""
from pathlib import Path
import re

src = Path('/home/z/my-project/scripts/bakery_erd_doc_v2.html')
text = src.read_text(encoding='utf-8')

# Map old section numbers to new numbers (Persian numerals)
section_map = {
    # Old "SECTION 09" (FEFO Transfer Suggester) → "SECTION 14"
    ('SECTION 09', 'FEFO Transfer Suggester'): 'SECTION 14',
    # Old "SECTION 10" (SMS) → "SECTION 15"
    ('SECTION 10', 'SMS'): 'SECTION 15',
    # Old "SECTION 11" (Frontend) → "SECTION 16"
    ('SECTION 11', 'Frontend'): 'SECTION 16',
    # Old "SECTION 12" (Roadmap) → "SECTION 17"
    ('SECTION 12', 'Roadmap'): 'SECTION 17',
    # Old "SECTION 13" (Testing & DevOps) → "SECTION 18"
    ('SECTION 13', 'Testing'): 'SECTION 18',
    # Old "SECTION 14" (Risk Analysis) → "SECTION 19"
    ('SECTION 14', 'Risk'): 'SECTION 19',
    # Old "SECTION 15" (Conclusion) → "SECTION 20"
    ('SECTION 15', 'Conclusion'): 'SECTION 20',
}

# Renumber section tags
for (old_tag, _), new_tag in section_map.items():
    if old_tag in text:
        text = text.replace(old_tag, new_tag)
        print(f"  {old_tag} → {new_tag}")

# Renumber sub-section numbers (۹.۱ → ۱۴.۱, etc.)
# Note: We need to do this ONLY for sections AFTER our inserted ones (sections 14-20)
# Since our new sections 9-13 already use ۹.۱, ۱۰.۱, etc. (their own sub-sections),
# we can't blanket-replace "۹.۱" with "۱۴.۱".
#
# Strategy: find the section starting from "SECTION 14" (was 09)
# and only replace subsection numbers within that section.

# Approach: split text by section markers, then process each section separately
import re

# Find positions of all section markers
section_pattern = re.compile(r'<!-- ============ SECTION \d+:')
matches = list(section_pattern.finditer(text))
print(f"\n  Found {len(matches)} section markers")

# Define what to replace for each old section (now with new section number)
# For each section that was renumbered, find the appropriate content block
# and update subsection numbers

# Find the block boundaries - from this SECTION marker to next SECTION marker
# or to the ending

# Simpler: search for the section's chapter-header and replace within it
# But that's complex. Let me use a different approach.

# Approach: Find each section's start position and process from there
# to next section's start

def find_section_range(text, section_num):
    """Find start and end position of section N."""
    start_marker = f'<!-- ============ SECTION {section_num}:'
    start_pos = text.find(start_marker)
    if start_pos == -1:
        return None
    # Find next section or ending marker
    next_section_pos = text.find('<!-- ============ SECTION', start_pos + 1)
    ending_pos = text.find('<!-- ============ ENDING', start_pos)
    candidates = [p for p in [next_section_pos, ending_pos] if p != -1]
    end_pos = min(candidates) if candidates else len(text)
    return (start_pos, end_pos)

# Sub-section numbers to update for each section (Persian numerals)
subsections_map = {
    14: [9, '۹.۱', '۹.۲', '۹.۳'],     # FEFO Transfer had 9.1, 9.2, 9.3 (now 14)
    15: [10, '۱۰.۱', '۱۰.۲', '۱۰.۳'], # SMS
    16: [11, '۱۱.۱', '۱۱.۲', '۱۱.۳', '۱۱.۴'],  # Frontend
    17: [12, '۱۲.۱', '۱۲.۲', '۱۲.۳'],  # Roadmap
    18: [13, '۱۳.۱', '۱۳.۲', '۱۳.۳'],  # Testing
    19: [14, '۱۴.۱', '۱۴.۲', '۱۴.۳'],  # Risk
    # Section 20 (Conclusion) has no subsections
}

# Persian number mapping
def to_persian_num(n):
    persian_digits = '۰۱۲۳۴۵۶۷۸۹'
    return ''.join(persian_digits[int(d)] for d in str(n))

# Process each section
for new_section_num, info in subsections_map.items():
    old_section_num = info[0]
    old_subsec_prefixes = info[1:]
    new_section_persian = to_persian_num(new_section_num)
    
    # Find this section's range
    section_range = find_section_range(text, new_section_num)
    if section_range is None:
        print(f"  Section {new_section_num} not found, skipping")
        continue
    
    start, end = section_range
    section_text = text[start:end]
    
    # Replace each subsection prefix (e.g., "۹.۱" → "۱۴.۱")
    for old_prefix in old_subsec_prefixes:
        # Extract subsection number (last digit)
        subsec_num = old_prefix.split('.')[-1]
        new_prefix = f'{new_section_persian}.{subsec_num}'
        if old_prefix in section_text:
            section_text = section_text.replace(old_prefix, new_prefix)
            print(f"  {old_prefix} → {new_prefix}")
    
    # Replace back in original text
    text = text[:start] + section_text + text[end:]

# Save
src.write_text(text, encoding='utf-8')
print(f"\nDone. Saved to {src}")
