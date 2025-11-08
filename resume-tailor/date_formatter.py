"""
Date Format Standardization Utility
Converts various date formats to PDF-compatible "MMM YYYY - MMM YYYY"
"""

import re
from datetime import datetime
from typing import Optional

# Month abbreviations mapping
MONTH_ABBREV = {
    'january': 'Jan', 'february': 'Feb', 'march': 'Mar', 'april': 'Apr',
    'may': 'May', 'june': 'Jun', 'july': 'Jul', 'august': 'Aug',
    'september': 'Sep', 'october': 'Oct', 'november': 'Nov', 'december': 'Dec',
    'jan': 'Jan', 'feb': 'Feb', 'mar': 'Mar', 'apr': 'Apr',
    'jun': 'Jun', 'jul': 'Jul', 'aug': 'Aug', 'sep': 'Sep',
    'oct': 'Oct', 'nov': 'Nov', 'dec': 'Dec'
}


def standardize_date(date_str: str) -> str:
    """
    Standardize date string to "MMM YYYY - MMM YYYY" or "MMM YYYY - Present" format
    
    Handles various input formats:
    - "2019-2025" → "Jan 2019 - Dec 2025"
    - "Oct 2019 – Present" → "Oct 2019 - Present"
    - "October 2019 - January 2025" → "Oct 2019 - Jan 2025"
    - "2024" → "2024" (single year, unchanged)
    - "Oct 2019 — Present" → "Oct 2019 - Present" (normalize dashes)
    
    Args:
        date_str: Input date string in various formats
        
    Returns:
        Standardized date string in PDF-compatible format
    """
    if not date_str:
        return ""
    
    # Strip whitespace
    date_str = date_str.strip()
    
    # Already in correct format? Return as-is
    if re.match(r'^[A-Z][a-z]{2} \d{4} - ([A-Z][a-z]{2} \d{4}|Present)$', date_str):
        return date_str
    
    # Normalize: Handle "Current" → "Present"
    date_str = re.sub(r'\b(Current|current)\b', 'Present', date_str)
    
    # Normalize dashes: em-dash, en-dash → hyphen
    date_str = date_str.replace('–', '-').replace('—', '-').replace('−', '-')
    
    # Pattern 1: YYYY-YYYY or YYYY - YYYY
    match = re.match(r'^(\d{4})\s*-\s*(\d{4})$', date_str)
    if match:
        start_year, end_year = match.groups()
        return f"Jan {start_year} - Dec {end_year}"
    
    # Pattern 2: YYYY - Present
    match = re.match(r'^(\d{4})\s*-\s*(Present|present)', date_str, re.IGNORECASE)
    if match:
        year = match.group(1)
        return f"Jan {year} - Present"
    
    # Pattern 3: Month YYYY - Month YYYY
    match = re.match(
        r'^([A-Za-z]+)\s+(\d{4})\s*-\s*([A-Za-z]+)\s+(\d{4})$',
        date_str
    )
    if match:
        start_month, start_year, end_month, end_year = match.groups()
        start_month_abbr = MONTH_ABBREV.get(start_month.lower(), start_month[:3].capitalize())
        end_month_abbr = MONTH_ABBREV.get(end_month.lower(), end_month[:3].capitalize())
        return f"{start_month_abbr} {start_year} - {end_month_abbr} {end_year}"
    
    # Pattern 4: Month YYYY - Present
    match = re.match(
        r'^([A-Za-z]+)\s+(\d{4})\s*-\s*(Present|present)',
        date_str,
        re.IGNORECASE
    )
    if match:
        month, year = match.groups()[:2]
        month_abbr = MONTH_ABBREV.get(month.lower(), month[:3].capitalize())
        return f"{month_abbr} {year} - Present"
    
    # Pattern 5: MM/YYYY - MM/YYYY
    match = re.match(r'^(\d{1,2})/(\d{4})\s*-\s*(\d{1,2})/(\d{4})$', date_str)
    if match:
        start_month, start_year, end_month, end_year = match.groups()
        start_month_num = int(start_month)
        end_month_num = int(end_month)
        
        start_month_name = datetime(2000, start_month_num, 1).strftime('%b')
        end_month_name = datetime(2000, end_month_num, 1).strftime('%b')
        
        return f"{start_month_name} {start_year} - {end_month_name} {end_year}"
    
    # Pattern 6: Just YYYY (single year, keep as-is)
    if re.match(r'^\d{4}$', date_str):
        return date_str
    
    # Pattern 7: Just Month YYYY (single date)
    match = re.match(r'^([A-Za-z]+)\s+(\d{4})$', date_str)
    if match:
        month, year = match.groups()
        month_abbr = MONTH_ABBREV.get(month.lower(), month[:3].capitalize())
        return f"{month_abbr} {year}"
    
    # Fallback: return original with warning
    print(f"Warning: Could not standardize date format: '{date_str}'")
    return date_str


def extract_year_from_date(date_str: str) -> Optional[str]:
    """
    Extract first year found in date string
    
    Args:
        date_str: Date string in any format
        
    Returns:
        Year as string (e.g., "2024") or None if not found
    """
    if not date_str:
        return None
    
    match = re.search(r'\d{4}', date_str)
    return match.group(0) if match else None


def is_present_date(date_str: str) -> bool:
    """
    Check if date string indicates current/present employment
    
    Args:
        date_str: Date string to check
        
    Returns:
        True if date indicates current employment
    """
    if not date_str:
        return False
    
    return bool(re.search(r'\b(Present|present|Current|current)\b', date_str))


# Test cases
if __name__ == "__main__":
    test_cases = [
        ("2019-2025", "Jan 2019 - Dec 2025"),
        ("Oct 2019 – Present", "Oct 2019 - Present"),
        ("October 2019 - January 2025", "Oct 2019 - Jan 2025"),
        ("2024", "2024"),
        ("Jan 2020 - Present", "Jan 2020 - Present"),  # Already correct
        ("2019 - Current", "Jan 2019 - Present"),
        ("01/2020 - 12/2024", "Jan 2020 - Dec 2024"),
        ("March 2021", "Mar 2021"),
        ("october 2019 — present", "Oct 2019 - Present"),
    ]
    
    print("Testing date standardization:")
    print("="*70)
    
    for input_date, expected in test_cases:
        result = standardize_date(input_date)
        status = "✓" if result == expected else "✗"
        print(f"{status} '{input_date}' → '{result}'")
        if result != expected:
            print(f"  Expected: '{expected}'")
    
    print("\nTesting year extraction:")
    print("="*70)
    test_year_cases = [
        ("Oct 2019 - Jan 2025", "2019"),
        ("2024", "2024"),
        ("No year here", None),
    ]
    
    for input_date, expected_year in test_year_cases:
        result = extract_year_from_date(input_date)
        status = "✓" if result == expected_year else "✗"
        print(f"{status} '{input_date}' → '{result}'")
