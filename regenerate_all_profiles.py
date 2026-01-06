"""
Regenerate all existing company profile HTML files
"""
import os
from pathlib import Path
from show_company_profile import generate_company_profile_html

def main():
    html_dir = Path(__file__).parent / "html"

    # Find all existing profile files
    profile_files = list(html_dir.glob("*_profile.html"))

    # Extract symbols from filenames
    symbols = []
    for file in profile_files:
        symbol = file.stem.replace("_profile", "")
        symbols.append(symbol)

    print(f"Found {len(symbols)} company profiles to regenerate")
    print("=" * 60)

    success_count = 0
    error_count = 0

    for i, symbol in enumerate(symbols, 1):
        try:
            print(f"[{i}/{len(symbols)}] Regenerating: {symbol}...", end=' ')
            path = generate_company_profile_html(symbol)
            if path:
                print("OK")
                success_count += 1
            else:
                print("FAILED")
                error_count += 1
        except Exception as e:
            print(f"ERROR: {e}")
            error_count += 1

    print("=" * 60)
    print(f"SUCCESS: {success_count}")
    print(f"ERRORS: {error_count}")
    print(f"TOTAL: {len(symbols)}")

if __name__ == "__main__":
    main()
