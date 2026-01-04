import pandas as pd
from sqlalchemy import create_engine, text
import os
import glob
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- CONFIGURATION ---
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
TABLE_NAME = "evidence"
THEMES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "all_themes")

def extract_and_upload_evidence():
    print("--- Extracting Evidence from Themes ---")
    
    # 1. Connect to DB
    connection_string = f"mysql+mysqlconnector://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    engine = create_engine(connection_string)
    
    # 2. Iterate all CSVs
    all_files = glob.glob(os.path.join(THEMES_DIR, "*.csv"))
    print(f"Found {len(all_files)} theme files.")
    
    # Collect evidence rows
    evidence_rows = []
    
    count_files = 0
    count_evidence = 0
    
    for filename in all_files:
        try:
            # Use python engine for more robust parsing
            df = pd.read_csv(filename, encoding='utf-8', on_bad_lines='skip', engine='python')
            
            # CRITICAL: Strip whitespace from column names!
            df.columns = [str(c).strip() for c in df.columns]
            
            # Check if required columns exist
            if 'symbol' not in df.columns or 'evidence' not in df.columns:
                continue
            
            # Iterate rows and extract evidence
            for _, row in df.iterrows():
                symbol = str(row['symbol']).strip()
                evidence = str(row['evidence']).strip()
                
                # Skip if symbol or evidence is invalid/empty
                if not symbol or symbol.lower() == 'nan' or not evidence or evidence.lower() == 'nan':
                    continue
                
                # Add to list
                evidence_rows.append({
                    'symbol': symbol,
                    'evidence': evidence
                })
                count_evidence += 1
            
        except Exception as e:
            print(f"Error reading {os.path.basename(filename)}: {e}")
            
        count_files += 1
        if count_files % 100 == 0:
            print(f"Read {count_files} files... Found {count_evidence} evidence entries so far.")

    if not evidence_rows:
        print("No evidence data found.")
        return

    print(f"Total evidence entries found: {count_evidence}")
    
    # 3. Create DataFrame
    evidence_df = pd.DataFrame(evidence_rows)
    
    # 4. Upload to MySQL
    print(f"Uploading to table '{TABLE_NAME}'...")
    
    # 'replace' drops the table if exists and creates new one
    evidence_df.to_sql(name=TABLE_NAME, con=engine, if_exists='replace', index=False, chunksize=1000)
    
    # 5. Post-processing: Create indexes
    with engine.connect() as conn:
        # Create index on symbol for faster lookups
        conn.execute(text(f"CREATE INDEX idx_symbol ON {TABLE_NAME} (symbol(50));"))
        print("Index created on symbol column.")

    print("Success! Evidence table created and data uploaded.")
    print(f"Total evidence entries in database: {len(evidence_df)}")

if __name__ == "__main__":
    extract_and_upload_evidence()
