from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- CONFIGURATION ---
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
TABLE_NAME = "companies"

# Columns to drop from companies table
COLUMNS_TO_DROP = [
    'navigable',
    'conid',
    'type',
    'link_type',
    'key',
    'rank',
    'evidence',
    'description'
]

def drop_columns_from_companies():
    print(f"--- Dropping columns from {TABLE_NAME} table ---")
    
    # Connect to DB
    connection_string = f"mysql+mysqlconnector://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    engine = create_engine(connection_string)
    
    with engine.connect() as conn:
        # First, check which columns exist
        result = conn.execute(text(f"SHOW COLUMNS FROM `{TABLE_NAME}`;"))
        existing_columns = [row[0] for row in result]
        
        print(f"Existing columns: {existing_columns}")
        
        # Drop each column if it exists
        dropped = []
        not_found = []
        
        for col in COLUMNS_TO_DROP:
            if col in existing_columns:
                try:
                    conn.execute(text(f"ALTER TABLE `{TABLE_NAME}` DROP COLUMN `{col}`;"))
                    dropped.append(col)
                    print(f"✓ Dropped column: {col}")
                except Exception as e:
                    print(f"✗ Error dropping {col}: {e}")
            else:
                not_found.append(col)
                print(f"- Column not found: {col}")
        
        conn.commit()
    
    print("\n--- Summary ---")
    print(f"Dropped: {len(dropped)} columns")
    if dropped:
        print(f"  {', '.join(dropped)}")
    print(f"Not found: {len(not_found)} columns")
    if not_found:
        print(f"  {', '.join(not_found)}")
    
    print("\nSuccess! Columns removed from companies table.")

if __name__ == "__main__":
    drop_columns_from_companies()
