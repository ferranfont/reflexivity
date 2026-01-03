import pandas as pd
import os
import glob

# --- CONFIGURATION ---
THEMES_DIR = "data/all_themes"

def reorder_columns_in_csvs():
    print("--- Bulk Reordering Columns (Symbol First, Theme_ID Second) in Theme CSVs ---")
    
    if not os.path.exists(THEMES_DIR):
        print(f"Directory not found: {THEMES_DIR}")
        return

    csv_files = glob.glob(os.path.join(THEMES_DIR, "*.csv"))
    print(f"Found {len(csv_files)} files. Processing...")

    count = 0
    errors = 0
    skipped = 0
    
    for filepath in csv_files:
        try:
            # Read CSV
            df = pd.read_csv(filepath)
            
            cols = df.columns.tolist()
            
            # Find key columns
            symbol_col = None
            if 'symbol' in cols:
                symbol_col = 'symbol'
            elif 'Symbol' in cols:
                symbol_col = 'Symbol'
                
            theme_id_col = None
            if 'theme_id' in cols:
                theme_id_col = 'theme_id'
            
            # Logic to reorder
            new_order = []
            
            # 1. Symbol
            if symbol_col:
                new_order.append(symbol_col)
                
            # 2. Theme ID
            if theme_id_col:
                new_order.append(theme_id_col)
                
            # 3. Rest
            for c in cols:
                if c != symbol_col and c != theme_id_col:
                    new_order.append(c)
            
            # Only save if order changed or we just want to ensure consistency
            if new_order != cols:
                df = df[new_order]
                df.to_csv(filepath, index=False)
                count += 1
            else:
                skipped += 1
            
        except Exception as e:
            print(f"Error processing {os.path.basename(filepath)}: {e}")
            errors += 1
            
        if (count + skipped + errors) % 50 == 0:
            print(f"Processed {count + skipped + errors} files...")

    print(f"Done. Reordered {count} files. Skipped {skipped} (already correct). Errors: {errors}")

if __name__ == "__main__":
    reorder_columns_in_csvs()
