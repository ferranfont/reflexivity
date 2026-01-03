import pandas as pd
import os
import glob

# --- CONFIGURATION ---
THEMES_DIR = "data/all_themes"

def reorder_columns_in_csvs():
    print("--- Bulk Reordering Columns (Symbol First) in Theme CSVs ---")
    
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
            
            # Identify symbol column (handle case sensitivity if needed, but prefer 'symbol')
            # Based on previous tasks, valid col should be 'symbol'
            target_col = 'symbol'
            
            if target_col not in df.columns:
                # Try fallback just in case
                if 'Symbol' in df.columns:
                    target_col = 'Symbol'
                else:
                    # print(f"Skipping {os.path.basename(filepath)}: 'symbol' column not found.")
                    skipped += 1
                    continue
            
            # Reorder
            cols = df.columns.tolist()
            
            # Only reorder if not already first
            if cols[0] != target_col:
                cols.remove(target_col)
                cols.insert(0, target_col)
                
                df = df[cols]
                df.to_csv(filepath, index=False)
                count += 1
            else:
                # Already first
                pass
            
        except Exception as e:
            print(f"Error processing {os.path.basename(filepath)}: {e}")
            errors += 1
            
        if (count + skipped + errors) % 50 == 0:
            print(f"Processed {count + skipped + errors} files...")

    print(f"Done. Reordered {count} files. Skipped {skipped}. Errors: {errors}")

if __name__ == "__main__":
    reorder_columns_in_csvs()
