import pandas as pd
import os
import re
from fuzzywuzzy import process

# --- CONFIGURATION ---
REFERENCE_FILE = "data/trends_by_sector.csv"
THEMES_DIR = "data/all_themes"
OUTPUT_FILE = "outputs/industry_summary_offline.csv"

def normalize_text(text):
    """Normalize text for better matching: lowercase, remove special chars."""
    if not isinstance(text, str):
        return ""
    # Remove file extension if present
    text = text.replace(".csv", "")
    # Replace underscores with spaces
    text = text.replace("_", " ")
    # Lowercase
    text = text.lower()
    # Remove non-alphanumeric (keep spaces)
    text = re.sub(r'[^a-z0-9 ]', '', text)
    return text.strip()

def count_companies(filepath):
    """Count lines in CSV minus header."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            # -1 for header, but handle empty files
            lines = sum(1 for _ in f)
            return max(0, lines - 1)
    except Exception:
        return 0

def main():
    # 1. Load Reference Data
    # The separator seems to be comma based on the view_file output
    try:
        ref_df = pd.read_csv(REFERENCE_FILE)
        # Ensure columns exist
        if 'sector' not in ref_df.columns or 'trend' not in ref_df.columns:
            print("Reference file missing required columns.")
            return
    except Exception as e:
        print(f"Error loading reference file: {e}")
        return

    # Create a lookup dictionary: Normalized Trend Name -> Sector
    # We use this to find the sector for our files
    ref_df['trend_norm'] = ref_df['trend'].apply(normalize_text)
    
    # We also keep a list of valid trend names for fuzzy matching
    valid_trends = ref_df['trend_norm'].tolist()
    
    # Map back to real data
    trend_to_sector = dict(zip(ref_df['trend_norm'], ref_df['sector']))
    trend_to_real_name = dict(zip(ref_df['trend_norm'], ref_df['trend']))

    # 2. Process Local Files
    if not os.path.exists(THEMES_DIR):
        print(f"Themes directory {THEMES_DIR} not found.")
        return

    files = [f for f in os.listdir(THEMES_DIR) if f.endswith(".csv")]
    results = []
    
    print(f"Processing {len(files)} files...")
    
    for filename in files:
        # Get count
        filepath = os.path.join(THEMES_DIR, filename)
        count = count_companies(filepath)
        
        # Determine Theme Name and Industry
        file_norm = normalize_text(filename)
        
        # Exact match attempt
        if file_norm in trend_to_sector:
            industry = trend_to_sector[file_norm]
            theme_name = trend_to_real_name[file_norm]
            match_type = "Exact"
        else:
            # Fuzzy match
            # "agribusiness" vs "agribusiness" is exact
            # "semiconductor materials" vs "semiconductor materials" is exact
            # "consumier staples" (typo) -> fuzzy
            
            best_match, score = process.extractOne(file_norm, valid_trends)
            
            if score >= 80: # Threshold for accepting a match
                industry = trend_to_sector[best_match]
                theme_name = trend_to_real_name[best_match]
                match_type = f"Fuzzy ({score})"
            else:
                # If no good match found in reference, mark as Unclassified or Unknown
                # But since the user said the csv has "errors", maybe we stick to the filename
                industry = "Unclassified"
                theme_name = filename.replace(".csv", "").replace("_", " ").title()
                match_type = "None"

        results.append({
            'Industry': industry,
            'Theme': theme_name,
            'Companies_Count': count,
            'Filename': filename,
            'Match_Info': match_type
        })
        
    # 3. Create DataFrame and Save
    final_df = pd.DataFrame(results)
    
    # Sort for better readability: Industry -> Count (desc)
    final_df = final_df.sort_values(by=['Industry', 'Companies_Count'], ascending=[True, False])
    
    final_df.to_csv(OUTPUT_FILE, index=False)
    
    print(f"Done! Processed {len(files)} themes.")
    print(f"Summary saved to: {OUTPUT_FILE}")
    print("\nTop 5 Industries by Theme Count:")
    print(final_df['Industry'].value_counts().head())
    print("\nSample Rows:")
    print(final_df[['Industry', 'Theme', 'Companies_Count']].head(10))

if __name__ == "__main__":
    main()
