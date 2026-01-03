
import pandas as pd
import os

target_file = r'd:/PYTHON/ALGOS/reflexivity/data/all_themes/car_rental_integration.csv'

try:
    print(f"Reading {target_file}...")
    df = pd.read_csv(target_file, encoding='utf-8')
    
    # 1. Clean Column Names
    df.columns = df.columns.str.strip()
    
    # 2. Drop duplicates if any
    original_len = len(df)
    df.drop_duplicates(inplace=True)
    if len(df) < original_len:
        print(f"Removed {original_len - len(df)} duplicate rows.")
    
    # 3. Clean string data (strip spaces)
    df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
    
    # 4. Save back
    df.to_csv(target_file, index=False, encoding='utf-8')
    print("File cleaned and saved successfully.")
    
    # Verify content
    print("First 3 rows:")
    print(df.head(3).to_string())

except Exception as e:
    print(f"Error processing file: {e}")
