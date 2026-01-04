"""
Parse filing names to extract metadata and calculate source dates.
Handles SEC filing naming conventions: ticker-QXYZ-TYPE or ticker-FYYZ-TYPE
"""
import re
from datetime import date

def parse_filing_name(filing_name):
    """
    Parse filing name to extract components.

    Args:
        filing_name: str like "de-Q324-10-Q" or "aapl-FY24-10-K"

    Returns:
        dict with keys: ticker, quarter, year, fiscal_year, type, source_date
        Returns None if parsing fails

    Examples:
        >>> parse_filing_name("de-Q324-10-Q")
        {'ticker': 'DE', 'quarter': 'Q3', 'year': 2024, 'fiscal_year': 2024,
         'type': '10-Q', 'source_date': '2024-09-30'}

        >>> parse_filing_name("aapl-FY24-10-K")
        {'ticker': 'AAPL', 'quarter': 'FY', 'year': 2024, 'fiscal_year': 2024,
         'type': '10-K', 'source_date': '2024-12-31'}
    """
    if not filing_name:
        return None

    # Pattern: ticker-PERIOD-TYPE
    # PERIOD can be: Q124, Q225, FY24, etc.
    # TYPE can be: 10-Q, 10-K, 8-K, etc.
    pattern = r'^([A-Za-z]+)-(Q[1-4]|FY)(\d{2,4})-(.+)$'

    match = re.match(pattern, filing_name, re.IGNORECASE)
    if not match:
        return None

    ticker = match.group(1).upper()
    period = match.group(2).upper()  # Q1, Q2, Q3, Q4, or FY
    year_str = match.group(3)
    filing_type = match.group(4).upper()

    # Parse year (handle both 2-digit and 4-digit years)
    if len(year_str) == 2:
        year = 2000 + int(year_str)
    else:
        year = int(year_str)

    # Determine quarter and calculate source_date
    if period == 'FY':
        quarter = 'FY'
        # Fiscal year reports are typically filed after year end
        # Use December 31st as default
        source_date = date(year, 12, 31)
    elif period == 'Q1':
        quarter = 'Q1'
        # Q1 ends March 31
        source_date = date(year, 3, 31)
    elif period == 'Q2':
        quarter = 'Q2'
        # Q2 ends June 30
        source_date = date(year, 6, 30)
    elif period == 'Q3':
        quarter = 'Q3'
        # Q3 ends September 30
        source_date = date(year, 9, 30)
    elif period == 'Q4':
        quarter = 'Q4'
        # Q4 ends December 31
        source_date = date(year, 12, 31)
    else:
        return None

    return {
        'ticker': ticker,
        'quarter': quarter,
        'year': year,
        'fiscal_year': year,
        'type': filing_type,
        'source_date': source_date.strftime('%Y-%m-%d')
    }


def get_quarter_end_date(quarter, year):
    """
    Get the end date for a given quarter and year.

    Args:
        quarter: str like 'Q1', 'Q2', 'Q3', 'Q4', or 'FY'
        year: int like 2024

    Returns:
        date object representing the quarter end date
    """
    quarter_ends = {
        'Q1': (3, 31),
        'Q2': (6, 30),
        'Q3': (9, 30),
        'Q4': (12, 31),
        'FY': (12, 31)
    }

    if quarter not in quarter_ends:
        return None

    month, day = quarter_ends[quarter]
    return date(year, month, day)


def parse_evidence_sources_json(sources_json_str):
    """
    Parse evidenceSources JSON string and extract filing information.

    Args:
        sources_json_str: str like "[{'name': 'de-Q324-10-Q', 'url': '...'}]"

    Returns:
        list of dicts with parsed filing info and URLs
    """
    import json
    import ast

    if not sources_json_str or sources_json_str == 'nan':
        return []

    try:
        # Try parsing as JSON first
        sources = json.loads(sources_json_str)
    except:
        try:
            # Fallback: parse as Python literal (single quotes)
            sources = ast.literal_eval(sources_json_str)
        except:
            return []

    if not isinstance(sources, list):
        return []

    parsed_sources = []
    for source in sources:
        if not isinstance(source, dict) or 'name' not in source:
            continue

        filing_info = parse_filing_name(source['name'])
        if filing_info:
            filing_info['url'] = source.get('url', '')
            filing_info['filing_name'] = source['name']
            parsed_sources.append(filing_info)

    return parsed_sources


if __name__ == "__main__":
    # Test cases
    test_cases = [
        "de-Q324-10-Q",
        "aapl-FY24-10-K",
        "msft-Q125-10-Q",
        "tsla-Q225-10-Q",
        "invalid-name"
    ]

    print("Testing parse_filing_name():")
    print("=" * 80)

    for test in test_cases:
        result = parse_filing_name(test)
        print(f"\nInput:  {test}")
        if result:
            print(f"Output: {result}")
        else:
            print(f"Output: None (parsing failed)")

    print("\n" + "=" * 80)
    print("\nTesting parse_evidence_sources_json():")
    print("=" * 80)

    test_json = "[{'name': 'de-Q324-10-Q', 'url': 'https://example.com/de-Q324-10-Q.html'}, {'name': 'de-Q225-10-Q', 'url': 'https://example.com/de-Q225-10-Q.html'}]"

    result = parse_evidence_sources_json(test_json)
    print(f"\nInput JSON: {test_json}")
    print(f"\nParsed sources ({len(result)} found):")
    for i, source in enumerate(result, 1):
        print(f"\n  Source {i}:")
        for key, value in source.items():
            print(f"    {key:15} {value}")
