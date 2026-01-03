
import pandas as pd

file_path = r'd:/PYTHON/ALGOS/reflexivity/data/all_themes/agribusiness.csv'

try:
    print("Attempting to read CSV...")
    df = pd.read_csv(file_path, on_bad_lines='warn') # warn to see if rows are dropped
    
    # Strip column names just in case
    df.columns = df.columns.str.strip()
    
    print(f"Loaded {len(df)} rows.")
    print("Columns:", df.columns.tolist())
    
    # Print 'name' and 'symbol' for the first 5 rows to check alignment
    print("\n--- First 5 Rows (Name, Symbol) ---")
    print(df[['name', 'symbol']].head(5).to_string())
    
    # Check for suspicious names (too long or containing JSON chars)
    suspicious = df[df['name'].str.contains('{|}|http', na=False)]
    if not suspicious.empty:
        print("\n--- Suspicious Rows detected in 'name' column ---")
        print(suspicious[['name']].head(3).to_string())
        
except Exception as e:
    print(f"CRITICAL ERROR: {e}")
