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
TABLE_NAME = "rank"
THEMES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "all_themes")

def extract_and_upload_ranks():
    print("--- Extracting Ranks from Themes ---")
    
    # 1. Connect to DB
    connection_string = f"mysql+mysqlconnector://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    engine = create_engine(connection_string)
    
    # 2. Iterate all CSVs
    all_files = glob.glob(os.path.join(THEMES_DIR, "*.csv"))
    print(f"Found {len(all_files)} theme files.")
    
    # Collect rank rows
    rank_rows = []
    
    count_files = 0
    count_ranks = 0
    
    for filename in all_files:
        try:
            # Use python engine for more robust parsing
            df = pd.read_csv(filename, encoding='utf-8', on_bad_lines='skip', engine='python')
            
            # CRITICAL: Strip whitespace from column names!
            df.columns = [str(c).strip() for c in df.columns]
            
            # Check if required columns exist
            if 'symbol' not in df.columns or 'rank' not in df.columns:
                continue
            
            # Get theme name from filename (remove .csv extension)
            theme_name = os.path.splitext(os.path.basename(filename))[0]
            
            # Iterate rows and extract rank info
            for _, row in df.iterrows():
                symbol = str(row['symbol']).strip()
                rank_value = row['rank']
                
                # Skip if symbol is invalid/empty
                if not symbol or symbol.lower() == 'nan':
                    continue
                
                # Skip if rank is null/nan
                if pd.isna(rank_value):
                    continue
                
                # Convert rank to int if possible
                try:
                    rank_value = int(rank_value)
                except (ValueError, TypeError):
                    # If can't convert, skip this entry
                    continue
                
                # Add to list
                rank_rows.append({
                    'symbol': symbol,
                    'theme': theme_name,
                    'rank': rank_value
                })
                count_ranks += 1
            
        except Exception as e:
            print(f"Error reading {os.path.basename(filename)}: {e}")
            
        count_files += 1
        if count_files % 100 == 0:
            print(f"Read {count_files} files... Found {count_ranks} rank entries so far.")

    if not rank_rows:
        print("No rank data found.")
        return

    print(f"Total rank entries found: {count_ranks}")
    
    # 3. Create DataFrame
    rank_df = pd.DataFrame(rank_rows)
    
    # 4. Upload to MySQL
    print(f"Uploading to table '{TABLE_NAME}'...")
    
    # 'replace' drops the table if exists and creates new one
    rank_df.to_sql(name=TABLE_NAME, con=engine, if_exists='replace', index=False, chunksize=1000)
    
    # 5. Post-processing: Create indexes
    with engine.connect() as conn:
        # Create index on symbol for faster lookups
        conn.execute(text(f"CREATE INDEX idx_symbol ON `{TABLE_NAME}` (symbol(50));"))
        # Create index on theme for filtering by theme
        conn.execute(text(f"CREATE INDEX idx_theme ON `{TABLE_NAME}` (theme(100));"))
        print("Indexes created on symbol and theme columns.")

    print("Success! Rank table created and data uploaded.")
    print(f"Total rank entries in database: {len(rank_df)}")

if __name__ == "__main__":
    extract_and_upload_ranks()
