"""
Generate summary titles for evidence entries using BART (offline).
Adds 'head_title' column to evidence table.
Uses facebook/bart-large-cnn for high-quality summarization.
"""
from sqlalchemy import create_engine, text
from transformers import pipeline
import warnings
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Suppress warnings
warnings.filterwarnings('ignore')

# --- CONFIGURATION ---
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
TABLE_NAME = "evidence"

# BART Configuration
MODEL_NAME = "facebook/bart-large-cnn"
MAX_TITLE_LENGTH = 200  # Maximum characters for title (increased from 100)
MIN_SUMMARY_LENGTH = 15  # Minimum words for BART summary (increased from 10)
MAX_SUMMARY_LENGTH = 50  # Maximum words for BART summary (increased from 30)


def setup_summarizer():
    """
    Initialize BART summarizer (offline after first download).
    Downloads model on first run (~1.5GB), then cached locally.
    """
    print("Initializing BART summarizer...")
    print(f"Model: {MODEL_NAME}")
    print("(First run will download ~1.5GB model, then cached locally)\n")

    summarizer = pipeline(
        "summarization",
        model=MODEL_NAME,
        device=-1  # Use CPU (-1), change to 0 for GPU
    )

    return summarizer


def generate_title(text, summarizer, max_length=100):
    """
    Generate a concise title from evidence text using BART.

    Args:
        text: str - Full evidence text
        summarizer: transformers pipeline
        max_length: int - Maximum characters for title

    Returns:
        str - Generated title (natural language, not extractive)
    """
    if not text or len(text.strip()) < 20:
        return "Sin descripción disponible"

    try:
        # BART works better with shorter inputs (max 1024 tokens)
        # Truncate to ~500 words if needed
        words = text.split()
        if len(words) > 500:
            text = ' '.join(words[:500])

        # Generate summary using BART
        summary = summarizer(
            text,
            max_length=MAX_SUMMARY_LENGTH,
            min_length=MIN_SUMMARY_LENGTH,
            do_sample=False,
            truncation=True
        )

        # Extract summary text
        title = summary[0]['summary_text'].strip()

        # Truncate if too long
        if len(title) > max_length:
            title = title[:max_length].rsplit(' ', 1)[0] + "..."

        # Capitalize first letter
        if title:
            title = title[0].upper() + title[1:]

        return title

    except Exception as e:
        # Fallback: use first 100 chars
        print(f"[WARN] Error generating title: {e}")
        fallback = text[:max_length].strip()
        if len(text) > max_length:
            fallback += "..."
        return fallback


def add_head_title_column():
    """Add head_title column to evidence table"""
    print("="*60)
    print("STEP 1: Adding head_title column")
    print("="*60)

    connection_string = f"mysql+mysqlconnector://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    engine = create_engine(connection_string)

    with engine.connect() as conn:
        # Check if column exists
        result = conn.execute(text(f"SHOW COLUMNS FROM {TABLE_NAME} LIKE 'head_title';"))
        exists = result.fetchone() is not None

        if not exists:
            print("Adding 'head_title' column...")
            conn.execute(text(f"ALTER TABLE {TABLE_NAME} ADD COLUMN head_title TEXT;"))
            conn.commit()
            print("[OK] Column added")
        else:
            print("[INFO] Column already exists")

    print()


def generate_all_titles():
    """Generate titles for all evidence entries using BART"""
    print("="*60)
    print("STEP 2: Generating titles with BART")
    print("="*60)

    connection_string = f"mysql+mysqlconnector://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    engine = create_engine(connection_string)

    # Initialize BART summarizer once (downloads model on first run)
    summarizer = setup_summarizer()
    print("[OK] BART model loaded and ready\n")

    # Get all evidence entries
    with engine.connect() as conn:
        result = conn.execute(text(f"SELECT COUNT(*) FROM {TABLE_NAME};"))
        total = result.scalar()
        print(f"Total evidence entries to process: {total}\n")

        # Process in batches
        batch_size = 100
        processed = 0
        updated = 0

        for offset in range(0, total, batch_size):
            # Fetch batch
            query = text(f"""
                SELECT symbol, evidence
                FROM {TABLE_NAME}
                LIMIT :limit OFFSET :offset
            """)

            batch = conn.execute(query, {"limit": batch_size, "offset": offset}).fetchall()

            # Generate titles for batch
            for row in batch:
                symbol = row[0]
                evidence = row[1]

                # Generate title
                title = generate_title(evidence, summarizer)

                # Update database
                update_query = text(f"""
                    UPDATE {TABLE_NAME}
                    SET head_title = :title
                    WHERE symbol = :symbol AND evidence = :evidence
                """)

                conn.execute(update_query, {
                    "title": title,
                    "symbol": symbol,
                    "evidence": evidence
                })

                updated += 1
                processed += 1

            # Commit batch
            conn.commit()

            # Progress
            print(f"Processed: {processed}/{total} ({processed/total*100:.1f}%) - Updated: {updated}")

    print(f"\n[OK] All titles generated")
    print(f"   Total processed: {processed}")
    print(f"   Total updated: {updated}")


def verify_titles():
    """Verify title generation"""
    print("\n" + "="*60)
    print("STEP 3: Verification")
    print("="*60)

    connection_string = f"mysql+mysqlconnector://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    engine = create_engine(connection_string)

    with engine.connect() as conn:
        # Count with titles
        result = conn.execute(text(f"SELECT COUNT(*) FROM {TABLE_NAME} WHERE head_title IS NOT NULL;"))
        with_titles = result.scalar()

        result = conn.execute(text(f"SELECT COUNT(*) FROM {TABLE_NAME};"))
        total = result.scalar()

        print(f"Evidence entries with titles: {with_titles}/{total} ({with_titles/total*100:.1f}%)")

        # Show samples
        print("\nSample titles:")
        result = conn.execute(text(f"""
            SELECT symbol, head_title, LEFT(evidence, 80) as preview
            FROM {TABLE_NAME}
            WHERE head_title IS NOT NULL
            LIMIT 5;
        """))

        for row in result:
            print(f"\n  [{row[0]}]")
            print(f"  Title: {row[1]}")
            print(f"  Evidence: {row[2]}...")


def main():
    """Main execution"""
    print("\n" + "="*60)
    print("GENERATE EVIDENCE TITLES WITH BART (OFFLINE)")
    print("="*60 + "\n")
    print("Using facebook/bart-large-cnn for high-quality summarization")
    print("First run: Downloads ~1.5GB model (cached for future use)")
    print("Processing time: ~2-3 seconds per evidence entry")
    print("="*60 + "\n")

    try:
        # Step 1: Add column
        add_head_title_column()

        # Step 2: Generate titles
        generate_all_titles()

        # Step 3: Verify
        verify_titles()

        print("\n" + "="*60)
        print("[SUCCESS] Evidence titles generated")
        print("="*60 + "\n")

    except Exception as e:
        print("\n" + "="*60)
        print(f"[ERROR] {e}")
        print("="*60 + "\n")
        raise


if __name__ == "__main__":
    main()
