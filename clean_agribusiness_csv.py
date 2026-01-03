
import pandas as pd
import csv

target_file = r'd:/PYTHON/ALGOS/reflexivity/data/all_themes/agribusiness.csv'

try:
    print(f"Cleaning {target_file}...")

    # Load with flexible engine to prevent parser errors
    # quoting=csv.QUOTE_MINIMAL assumes standard double-quote behavior
    # skipinitialspace=True helps if there are spaces after commas
    df = pd.read_csv(target_file, encoding='utf-8', skipinitialspace=True, engine='python')

    # 1. Clean Column Names
    df.columns = df.columns.str.strip()

    # 2. Check for potentially shifted rows
    # If duplicates or bad headers caused issues, we clean them.
    original_len = len(df)
    df.drop_duplicates(inplace=True)
    if len(df) < original_len:
        print(f"Removed {original_len - len(df)} duplicate rows.")

    # 3. Clean string data (strip spaces)
    df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)

    # 4. Save cleanly
    # quoting=csv.QUOTE_ALL will quote everything, ensuring commas inside fields don't break subsequent reads
    df.to_csv(target_file, index=False, encoding='utf-8', quoting=csv.QUOTE_ALL)
    print("File cleaned and saved successfully with QUOTE_ALL.")
    
    # 5. Verify the critical columns for the first row
    print("\n--- First Row Verification ---")
    row0 = df.iloc[0]
    print(f"Name: {row0['name']}")
    print(f"Symbol: {row0['symbol']}")
    print(f"Type: {row0['type']}")
    print(f"Link Type: {row0['link_type']}")

except Exception as e:
    print(f"Error processing file: {e}")
