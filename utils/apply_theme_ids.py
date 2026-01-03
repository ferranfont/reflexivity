import pandas as pd
import os
import re

# --- CONFIGURATION ---
SUMMARY_FILE = "data/industry_summary_offline.csv"
THEMES_DIR = "data/all_themes"

INDUSTRY_MAP = {
    "Agriculture": "AG",
    "Automotive": "AU",
    "Consumer and Retail": "CR",
    "Defense and Aerospace": "DA",
    "Energy and Utilities": "EU",
    "Entertainment and Media": "EM",
    "Financials": "FI",
    "Health": "HE",
    "Hospitality": "HO",
    "Industrial": "IN",
    "Materials and Mining": "MM",
    "Professional Services": "PS",
    "Real Estate": "RE",
    "Technology": "TE",
    "Telecommunications": "TC",
    "Transportation and Logistics": "TL",
    "Other": "OT",
    "Unclassified": "UN"
}

def get_clean_chars(text, length=3):
    clean = re.sub(r'[^a-zA-Z0-9]', '', str(text)).upper()
    return clean[:length].ljust(length, 'X')

def generate_codes(df):
    """Generates a list of unique codes corresponding to the dataframe rows."""
    used_codes = set()
    codes = []
    
    for _, row in df.iterrows():
        industry = row.get("Industry", "")
        theme = row.get("Theme", "")
        
        ind_code = INDUSTRY_MAP.get(industry, "ZZ")
        if ind_code == "ZZ" and industry:
            ind_code = get_clean_chars(industry, 2)
            
        thm_code = get_clean_chars(theme, 3)
        base_code = f"{ind_code}_{thm_code}"
        
        final_code = base_code
        counter = 1
        while final_code in used_codes:
            # Collision resolution strategy:
            # Try to grab different chars or append number
            prefix_part = base_code[:-1] 
            final_code = f"{prefix_part}{counter}"
            counter += 1
            if counter > 9:
                final_code = f"{base_code}_{counter}"
        
        used_codes.add(final_code)
        codes.append(final_code)
    return codes

def main():
    print("--- Applying Theme Codes to ALL Files ---")
    
    # 1. Read Summary
    if not os.path.exists(SUMMARY_FILE):
        print(f"File not found: {SUMMARY_FILE}")
        return
    
    df = pd.read_csv(SUMMARY_FILE)
    print(f"Loaded summary with {len(df)} rows.")
    
    # 2. Generate Codes
    df['theme_id'] = generate_codes(df)
    
    # Reorder columns to put theme_id first or near Theme
    # Assuming columns: Industry,Theme,Companies_Count,Filename,Match_Info
    cols = ['theme_id', 'Industry', 'Theme', 'Companies_Count', 'Filename', 'Match_Info']
    # Handle cases where cols might differ slightly, blindly reindex intersect
    existing_cols = [c for c in cols if c in df.columns] + [c for c in df.columns if c not in cols]
    df = df[existing_cols]
    
    # 3. Save Summary with IDs
    df.to_csv(SUMMARY_FILE, index=False)
    print(f"Updated {SUMMARY_FILE} with theme_ids.")
    
    # 4. Update Individual CSVs
    print("Updating individual theme CSVs...")
    count = 0
    errors = 0
    
    for _, row in df.iterrows():
        filename = row['Filename']
        t_id = row['theme_id']
        
        file_path = os.path.join(THEMES_DIR, filename)
        
        if os.path.exists(file_path):
            try:
                sub_df = pd.read_csv(file_path)
                # specific request: "add that code to each one of the themes"
                sub_df['theme_id'] = t_id
                sub_df.to_csv(file_path, index=False)
                count += 1
            except Exception as e:
                print(f"Error updating {filename}: {e}")
                errors += 1
        else:
            # print(f"Warning: Theme file {filename} not found.")
            pass
            
        if count % 50 == 0:
            print(f"Processed {count} files...")

    print(f"Finished. Updated {count} files. Errors: {errors}")

if __name__ == "__main__":
    main()
