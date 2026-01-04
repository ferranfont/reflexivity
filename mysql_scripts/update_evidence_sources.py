"""
Update evidence table with evidenceSources and source_date columns.
Extracts filing sources from CSV files and parses dates.
"""
import pandas as pd
from sqlalchemy import create_engine, text
import glob
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'utils'))
from parse_filing_date import parse_evidence_sources_json

# --- CONFIGURATION ---
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
TABLE_NAME = "evidence"
THEMES_DIR = Path(__file__).parent.parent / "data" / "all_themes"


def add_columns_to_evidence_table():
    """Add evidenceSources and source_date columns to evidence table"""
    print("="*60)
    print("STEP 1: Adding columns to evidence table")
    print("="*60)

    connection_string = f"mysql+mysqlconnector://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    engine = create_engine(connection_string)

    with engine.connect() as conn:
        # Check if evidenceSources column exists
        result = conn.execute(text(f"SHOW COLUMNS FROM {TABLE_NAME} LIKE 'evidenceSources';"))
        sources_exists = result.fetchone() is not None

        # Check if source_date column exists
        result = conn.execute(text(f"SHOW COLUMNS FROM {TABLE_NAME} LIKE 'source_date';"))
        date_exists = result.fetchone() is not None

        if not sources_exists:
            print("Adding 'evidenceSources' column...")
            conn.execute(text(f"ALTER TABLE {TABLE_NAME} ADD COLUMN evidenceSources TEXT;"))
            conn.commit()
            print("[OK] Column 'evidenceSources' added")
        else:
            print("[INFO] Column 'evidenceSources' already exists")

        if not date_exists:
            print("Adding 'source_date' column...")
            conn.execute(text(f"ALTER TABLE {TABLE_NAME} ADD COLUMN source_date DATE;"))
            conn.commit()
            print("[OK] Column 'source_date' added")
        else:
            print("[INFO] Column 'source_date' already exists")

    print()


def extract_evidence_with_sources():
    """
    Extract evidence entries with their sources from CSV files.
    IMPORTANT: Creates ONE ROW per evidence entry (not per symbol).
    A symbol like AAPL can appear MULTIPLE times with different evidence.

    Returns list of dicts with: symbol, evidence, evidenceSources, source_date
    """
    print("="*60)
    print("STEP 2: Extracting evidence with sources from CSVs")
    print("="*60)

    all_files = list(THEMES_DIR.glob("*.csv"))
    print(f"Found {len(all_files)} theme files")

    evidence_rows = []
    files_processed = 0
    evidence_count = 0

    for csv_file in all_files:
        try:
            df = pd.read_csv(csv_file, encoding='utf-8', on_bad_lines='skip', engine='python')
            df.columns = [str(c).strip() for c in df.columns]

            # Check required columns
            required_cols = ['symbol', 'evidence', 'evidenceSources']
            if not all(col in df.columns for col in required_cols):
                continue

            # CRITICAL: Iterate EVERY ROW, even if symbol repeats
            # Each row is a separate evidence entry (different theme or company)
            for _, row in df.iterrows():
                symbol = str(row['symbol']).strip().upper()
                evidence = str(row['evidence']).strip()
                evidence_sources = str(row['evidenceSources']).strip()

                # Skip invalid
                if not symbol or symbol.lower() == 'nan':
                    continue
                if not evidence or evidence.lower() == 'nan':
                    continue
                if not evidence_sources or evidence_sources.lower() == 'nan':
                    continue

                # Parse sources to get the most recent date from THIS evidence's sources
                # The JSON can contain multiple documents (e.g., Q1, Q2, Q3 reports)
                parsed_sources = parse_evidence_sources_json(evidence_sources)

                # Get the most recent source_date from ALL filings in THIS evidence
                source_date = None
                if parsed_sources:
                    # Extract all dates and find the most recent one
                    dates = [s['source_date'] for s in parsed_sources if 'source_date' in s]
                    if dates:
                        source_date = max(dates)  # Most recent date

                # Add this evidence row (AAPL can appear multiple times!)
                evidence_rows.append({
                    'symbol': symbol,
                    'evidence': evidence,
                    'evidenceSources': evidence_sources,  # Full JSON array
                    'source_date': source_date  # Most recent date from this evidence's sources
                })
                evidence_count += 1

            files_processed += 1
            if files_processed % 100 == 0:
                print(f"Processed {files_processed} files... Found {evidence_count} evidence entries")

        except Exception as e:
            print(f"[WARN] Error reading {csv_file.name}: {e}")

    print(f"\n[OK] Extraction complete:")
    print(f"   Files processed: {files_processed}")
    print(f"   Evidence entries found: {len(evidence_rows)}")

    # Show examples of symbols with multiple entries
    from collections import Counter
    symbol_counts = Counter([row['symbol'] for row in evidence_rows])
    multi_entries = {sym: count for sym, count in symbol_counts.items() if count > 1}
    if multi_entries:
        print(f"\n   Examples of symbols with multiple evidence entries:")
        for sym, count in sorted(multi_entries.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"      {sym}: {count} entries")

    return evidence_rows


def update_evidence_table(evidence_rows):
    """Update evidence table with sources and dates"""
    print("\n" + "="*60)
    print("STEP 3: Updating evidence table")
    print("="*60)

    connection_string = f"mysql+mysqlconnector://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    engine = create_engine(connection_string)

    # First, clear the table
    with engine.connect() as conn:
        conn.execute(text(f"TRUNCATE TABLE {TABLE_NAME};"))
        conn.commit()
        print("[OK] Table truncated")

    # Create DataFrame
    df = pd.DataFrame(evidence_rows)

    # Upload to MySQL
    print(f"Uploading {len(df)} evidence entries...")
    df.to_sql(name=TABLE_NAME, con=engine, if_exists='append', index=False, chunksize=1000)

    print(f"[OK] Evidence table updated successfully")


def verify_update():
    """Verify the update"""
    print("\n" + "="*60)
    print("STEP 4: Verification")
    print("="*60)

    connection_string = f"mysql+mysqlconnector://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    engine = create_engine(connection_string)

    with engine.connect() as conn:
        # Total count
        result = conn.execute(text(f"SELECT COUNT(*) FROM {TABLE_NAME};"))
        total = result.scalar()

        # Count with sources
        result = conn.execute(text(f"SELECT COUNT(*) FROM {TABLE_NAME} WHERE evidenceSources IS NOT NULL;"))
        with_sources = result.scalar()

        # Count with dates
        result = conn.execute(text(f"SELECT COUNT(*) FROM {TABLE_NAME} WHERE source_date IS NOT NULL;"))
        with_dates = result.scalar()

        print(f"Total evidence entries: {total}")
        print(f"Entries with evidenceSources: {with_sources} ({with_sources/total*100:.1f}%)")
        print(f"Entries with source_date: {with_dates} ({with_dates/total*100:.1f}%)")

        # Sample
        print("\nSample entries with dates:")
        result = conn.execute(text(f"""
            SELECT symbol, LEFT(evidence, 80) as evidence_preview, source_date
            FROM {TABLE_NAME}
            WHERE source_date IS NOT NULL
            LIMIT 5;
        """))

        for row in result:
            print(f"  {row[0]:10} {row[2]}  {row[1]}...")


def main():
    """Main execution"""
    print("\n" + "="*60)
    print("UPDATE EVIDENCE TABLE WITH SOURCES AND DATES")
    print("="*60 + "\n")

    try:
        # Step 1: Add columns
        add_columns_to_evidence_table()

        # Step 2: Extract data
        evidence_rows = extract_evidence_with_sources()

        if not evidence_rows:
            print("\n❌ No evidence data found")
            return

        # Step 3: Update table
        update_evidence_table(evidence_rows)

        # Step 4: Verify
        verify_update()

        print("\n" + "="*60)
        print("[SUCCESS] Evidence table updated with sources and dates")
        print("="*60 + "\n")

    except Exception as e:
        print("\n" + "="*60)
        print(f"[ERROR] {e}")
        print("="*60 + "\n")
        raise


if __name__ == "__main__":
    main()
