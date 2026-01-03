import pandas as pd
import os

SUMMARY_FILE = "data/industry_summary_offline.csv"
THEMES_DIR = "data/all_themes"

def refactor_ids():
    print("--- Refactoring Theme IDs (Short Code) ---")
    
    if not os.path.exists(SUMMARY_FILE):
        print("Summary file not found.")
        return

    df = pd.read_csv(SUMMARY_FILE)
    
    # Expected columns currently: theme_id (AG_BIO), industry_id (AG), theme_code (BIO)
    if 'theme_code' not in df.columns:
        print("Column 'theme_code' not found. Did you run split_theme_codes.py?")
        return

    # Check for global uniqueness of the short code
    # If duplicates exist, warnings should be issued, but we proceed as requested.
    duplicates = df[df.duplicated('theme_code', keep=False)]
    if not duplicates.empty:
        print("WARNING: The new 'theme_id' (formerly theme_code) is NOT unique globally.")
        print("The following codes appear multiple times (in different industries?):")
        print(duplicates[['industry_id', 'theme_code', 'Theme']])
        print("Proceeding anyway as requested...")
    
    # 1. Update Summary
    # Drop old 'theme_id' (AG_BIO)
    if 'theme_id' in df.columns:
        df.drop(columns=['theme_id'], inplace=True)
        
    # Rename 'theme_code' -> 'theme_id'
    df.rename(columns={'theme_code': 'theme_id'}, inplace=True)
    
    # Reorder: industry_id, theme_id, Industry, Theme...
    cols = ['industry_id', 'theme_id', 'Industry', 'Theme', 'Companies_Count', 'Filename', 'Match_Info']
    existing = [c for c in cols if c in df.columns] + [c for c in df.columns if c not in cols]
    df = df[existing]
    
    df.to_csv(SUMMARY_FILE, index=False)
    print(f"Updated {SUMMARY_FILE}.")
    
    # 2. Update Individual Files
    # We need to map Filename -> New Short Theme ID
    file_to_id = dict(zip(df['Filename'], df['theme_id']))
    
    print("Updating individual theme CSVs...")
    files_updated = 0
    for filename, new_id in file_to_id.items():
        filepath = os.path.join(THEMES_DIR, filename)
        if os.path.exists(filepath):
            try:
                sub_df = pd.read_csv(filepath)
                # update theme_id column
                sub_df['theme_id'] = new_id
                
                # Check if we should add industry_id? User didn't ask, but let's keep it simple.
                # Just update theme_id.
                
                sub_df.to_csv(filepath, index=False)
                files_updated += 1
            except Exception as e:
                pass
                
    print(f"Updated {files_updated} theme files.")

if __name__ == "__main__":
    refactor_ids()
