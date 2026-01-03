import pandas as pd
import os

# --- CONFIGURATION ---
SUMMARY_FILE = "data/industry_summary_offline.csv"
THEMES_DIR = "data/all_themes"

def add_industry_id_to_csvs():
    print("--- Adding 'industry_id' to Theme CSVs ---")
    
    if not os.path.exists(SUMMARY_FILE):
        print(f"Summary file not found: {SUMMARY_FILE}")
        return

    # 1. Load mapping
    summary_df = pd.read_csv(SUMMARY_FILE)
    
    # We need Filename -> industry_id map
    if 'Filename' not in summary_df.columns or 'industry_id' not in summary_df.columns:
        print("Error: Required columns 'Filename' or 'industry_id' missing in summary.")
        return
        
    file_map = dict(zip(summary_df['Filename'], summary_df['industry_id']))
    
    print(f"Loaded mapping for {len(file_map)} files.")
    
    count = 0
    errors = 0
    skipped = 0
    
    # 2. Iterate and Update
    for filename, ind_id in file_map.items():
        filepath = os.path.join(THEMES_DIR, filename)
        
        if not os.path.exists(filepath):
            # print(f"File not found: {filename}")
            skipped += 1
            continue
            
        try:
            df = pd.read_csv(filepath)
            
            # Add or Update column
            df['industry_id'] = ind_id
            
            # Optional: Reorder to put industry_id near the start?
            # User didn't explicitly ask for position, but usually ID cols are first.
            # Current order: symbol, theme_id, ...
            # Let's try: symbol, industry_id, theme_id, ...
            
            cols = df.columns.tolist()
            if 'industry_id' in cols:
                cols.remove('industry_id')
                
            # Insert logic
            target_index = 1 # After symbol (0)
            if 'symbol' in cols and cols.index('symbol') == 0:
                pass 
            elif 'Symbol' in cols and cols.index('Symbol') == 0:
                pass
            else:
                target_index = 0
                
            cols.insert(target_index, 'industry_id')
            
            df = df[cols]
            df.to_csv(filepath, index=False)
            count += 1
            
        except Exception as e:
            print(f"Error updating {filename}: {e}")
            errors += 1
            
        if count % 50 == 0 and count > 0:
            print(f"Updated {count} files...")

    print(f"Done. Updated {count} files. Skipped {skipped}. Errors: {errors}")

if __name__ == "__main__":
    add_industry_id_to_csvs()
