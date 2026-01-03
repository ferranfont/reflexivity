import pandas as pd
import os
import glob

# --- CONFIGURATION ---
THEMES_DIR = "data/all_themes"

# Column Mapping
# Old -> New
RENAME_MAP = {
    "type": "industry",
    "link_type": "theme",
    "key": "isin_code"
}

def rename_columns_in_csvs():
    print("--- Bulk Renaming Columns in Theme CSVs ---")
    
    if not os.path.exists(THEMES_DIR):
        print(f"Directory not found: {THEMES_DIR}")
        return

    csv_files = glob.glob(os.path.join(THEMES_DIR, "*.csv"))
    print(f"Found {len(csv_files)} files. Processing...")

    count = 0
    errors = 0
    
    for filepath in csv_files:
        try:
            # clean variable names
            renamed = False
            
            # Read CSV
            df = pd.read_csv(filepath)
            
            # Check if columns exist before renaming to avoid errors or partial updates
            # Actually rename method ignores missing columns by default unless errors='raise'
            
            # Check what will be renamed for logging
            cols_before = set(df.columns)
            
            # Rename
            df.rename(columns=RENAME_MAP, inplace=True)
            
            cols_after = set(df.columns)
            
            # Only save if changes happened
            if cols_before != cols_after:
                df.to_csv(filepath, index=False)
                count += 1
            
        except Exception as e:
            print(f"Error processing {os.path.basename(filepath)}: {e}")
            errors += 1
            
        if count % 50 == 0 and count > 0:
            print(f"Renamed columns in {count} files...")

    print(f"Done. Renamed columns in {count} files. Errors: {errors}")

if __name__ == "__main__":
    rename_columns_in_csvs()
