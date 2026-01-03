import pandas as pd
import os

SUMMARY_FILE = "data/industry_summary_offline.csv"

def split_codes():
    print("--- Splitting Theme ID into Industry ID and Theme Code ---")
    
    if not os.path.exists(SUMMARY_FILE):
        print(f"File not found: {SUMMARY_FILE}")
        return

    df = pd.read_csv(SUMMARY_FILE)
    
    if 'theme_id' not in df.columns:
        print("Error: 'theme_id' column missing. Run apply_theme_ids.py first.")
        return

    # Split logic
    # Assumes format XX_XXX or XX_XXX_X
    # We want "AG" and "BIO" from "AG_BIO"
    
    def get_industry_id(tid):
        return tid.split('_')[0] if isinstance(tid, str) else ""

    def get_theme_code(tid):
        parts = tid.split('_')
        if len(parts) > 1:
            # Join the rest in case of extra underscore, though our generator uses single split usually
            return "_".join(parts[1:]) 
        return ""

    df['industry_id'] = df['theme_id'].apply(get_industry_id)
    df['theme_code'] = df['theme_id'].apply(get_theme_code)
    
    # Reorder columns
    # We want: theme_id, industry_id, theme_code, Industry, Theme, ...
    cols = ['theme_id', 'industry_id', 'theme_code', 'Industry', 'Theme', 'Companies_Count', 'Filename', 'Match_Info']
    existing = [c for c in cols if c in df.columns] + [c for c in df.columns if c not in cols]
    
    df = df[existing]
    
    df.to_csv(SUMMARY_FILE, index=False)
    print(f"Updated {SUMMARY_FILE} with split columns.")
    print(df.head())

if __name__ == "__main__":
    split_codes()
