import pandas as pd
import os
import glob

# --- CONFIGURATION ---
THEMES_DIR = "data/all_themes"
COLUMN_TO_REMOVE = "navigable"

def remove_column_from_csvs():
    print(f"--- Bulk Removing Column '{COLUMN_TO_REMOVE}' in Theme CSVs ---")
    
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
            
            # Check if column exists
            if COLUMN_TO_REMOVE in df.columns:
                df.drop(columns=[COLUMN_TO_REMOVE], inplace=True)
                df.to_csv(filepath, index=False)
                count += 1
            else:
                # Column not found, nothing to do
                skipped += 1
            
        except Exception as e:
            print(f"Error processing {os.path.basename(filepath)}: {e}")
            errors += 1
            
        if (count + skipped + errors) % 50 == 0 and (count + skipped + errors) > 0:
            print(f"Processed {count + skipped + errors} files...")

    print(f"Done. Removed '{COLUMN_TO_REMOVE}' from {count} files. Skipped {skipped} (not found). Errors: {errors}")

if __name__ == "__main__":
    remove_column_from_csvs()
