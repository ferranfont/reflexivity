"""
Regenerate all theme detail pages with the updated template
"""
import pandas as pd
from pathlib import Path
import sys
import os

# Add parent directory to path to allow importing modules from root
sys.path.append(str(Path(__file__).parent.parent))

from show_theme import generate_theme_html

# Set BASE_DIR to the project root (up one level from data_update)
BASE_DIR = Path(__file__).parent.parent
SUMMARY_FILE = BASE_DIR / "data" / "industry_summary_offline.csv"

def main():
    print("Regenerating all theme detail pages...")

    if not SUMMARY_FILE.exists():
        print(f"Error: {SUMMARY_FILE} not found")
        return

    df = pd.read_csv(SUMMARY_FILE)
    themes = sorted(df['Theme'].dropna().unique())

    total = len(themes)
    print(f"Found {total} themes to regenerate\n")

    success_count = 0
    error_count = 0
    errors = []

    for i, theme in enumerate(themes, 1):
        try:
            print(f"[{i}/{total}] Generating: {theme}...", end=' ')
            path = generate_theme_html(theme)
            if path:
                print("OK")
                success_count += 1
            else:
                print("SKIP (no data)")
                error_count += 1
                errors.append(f"{theme} - No data found")
        except Exception as e:
            print(f"ERROR: {e}")
            error_count += 1
            errors.append(f"{theme} - {str(e)}")

    print("\n" + "="*60)
    print(f"Regeneration complete!")
    print(f"Success: {success_count}/{total}")
    print(f"Errors: {error_count}/{total}")

    if errors and len(errors) <= 20:
        print("\nErrors:")
        for err in errors:
            print(f"  - {err}")

if __name__ == '__main__':
    main()
