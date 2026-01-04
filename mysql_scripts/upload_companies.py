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
TABLE_NAME = "companies"
THEMES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "all_themes")

# Columns to EXCLUDE from the upload
EXCLUDE_COLS = {'industry_id', 'theme_id', 'industry', 'theme', 'evidenceSources'}

def extract_and_upload_companies():
    print("--- Extracting Unique Companies from Themes (New Requirements) ---")
    
    # 1. Connect to DB
    connection_string = f"mysql+mysqlconnector://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    engine = create_engine(connection_string)
    
    # 2. Iterate all CSVs
    all_files = glob.glob(os.path.join(THEMES_DIR, "*.csv"))
    print(f"Found {len(all_files)} theme files.")
    
    # We'll use a list to collect DataFrames then concat (more efficient than appending rows)
    df_list = []
    
    count_files = 0
    for filename in all_files:
        try:
            # Use python engine for more robust parsing
            df = pd.read_csv(filename, encoding='utf-8', on_bad_lines='skip', engine='python')
            
            # CRITICAL: Strip whitespace from column names!
            df.columns = [str(c).strip() for c in df.columns]
            
            # Drop excluded columns if they exist
            cols_to_drop = [c for c in df.columns if c in EXCLUDE_COLS]
            df.drop(columns=cols_to_drop, inplace=True)
            
            # Filter out invalid symbols (length > 50 implies parsing error or garbage)
            if 'symbol' in df.columns:
                 # Ensure symbol is string and strip whitespace
                 df['symbol'] = df['symbol'].astype(str).str.strip()
                 # Remove rows with invalid symbols
                 df = df[df['symbol'].str.len() <= 50]
                 df = df[df['symbol'] != 'nan']
                 df = df[df['symbol'] != '']
            
            # Add to list
            df_list.append(df)
            
        except Exception as e:
            print(f"Error reading {os.path.basename(filename)}: {e}")
            
        count_files += 1
        if count_files % 100 == 0:
            print(f"Read {count_files} files...")

    if not df_list:
        print("No data found.")
        return

    # 3. Concatenate
    print("Concatenating data...")
    full_df = pd.concat(df_list, ignore_index=True)
    
    print(f"Total rows before deduplication: {len(full_df)}")
    
    # 4. Deduplicate
    # User said "no dupliques ninguna compañia". Logic: Unique Symbol.
    # We keep the first occurrence.
    if 'symbol' in full_df.columns:
        full_df.drop_duplicates(subset=['symbol'], keep='first', inplace=True)
    else:
        print("Warning: 'symbol' column not found. Deduplicating by all columns.")
        full_df.drop_duplicates(inplace=True)
        
    print(f"Unique companies after deduplication: {len(full_df)}")
    
    # 5. Upload to MySQL
    
    # 5. Upload to MySQL
    print(f"Uploading to table '{TABLE_NAME}'...")
    
    # 'replace' drops the table if exists and creates new one
    # consistent with "borra antes las columnas de la tabla actual"
    full_df.to_sql(name=TABLE_NAME, con=engine, if_exists='replace', index=False, chunksize=1000)
    
    # 6. Post-processing: Set Primary Key
    # If 'symbol' exists, make it PK
    if 'symbol' in full_df.columns:
        with engine.connect() as conn:
            # We often need to specify length for VARCHAR PK
            conn.execute(text(f"ALTER TABLE {TABLE_NAME} MODIFY symbol VARCHAR(50) NOT NULL PRIMARY KEY;"))
            # Basic index on ib_conid if exists (TEXT columns need length for index)
            if 'ib_conid' in full_df.columns:
                 # Check if ib_conid is numeric or text
                 conn.execute(text(f"CREATE INDEX idx_ib_conid ON {TABLE_NAME} (ib_conid(20));"))

    print("Success! Table created and data uploaded.")
    print(f"Total companies in database: {len(full_df)}")

if __name__ == "__main__":
    extract_and_upload_companies()
