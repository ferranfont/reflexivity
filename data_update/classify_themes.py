import pandas as pd
import os
import re
from fuzzywuzzy import process

# --- CONFIGURATION ---
# We use the current Valid Summary as the "Truth" source for future classifications.
# If IBKR adds new themes, we try to match them against existing patterns or fuzzy match known ones.
REFERENCE_FILE = "../data/industry_summary_offline.csv" 
THEMES_DIR = "../data/all_themes"
OUTPUT_FILE = "../data/industry_summary_offline.csv" # Overwrite the main summary? Or create a new one?
# Ideally, we create a NEW one, and user reviews it.
# But for now, let's output to "updated_summary.csv" in this folder to be safe.
OUTPUT_FILE_SAFE = "updated_industry_summary.csv"

def normalize_text(text):
    """Normalize text for better matching."""
    if not isinstance(text, str):
        return ""
    text = text.replace(".csv", "")
    text = text.replace("_", " ")
    text = text.lower()
    text = re.sub(r'[^a-z0-9 ]', '', text)
    return text.strip()

def count_companies(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = sum(1 for _ in f)
            return max(0, lines - 1)
    except:
        return 0

def main():
    print("--- Theme Auto-Classifier ---")
    print(f"Reading reference classification from: {REFERENCE_FILE}")
    
    # 1. Load Reference (The Manual "Gold Standard")
    if not os.path.exists(REFERENCE_FILE):
        print("Reference file not found!")
        return

    ref_df = pd.read_csv(REFERENCE_FILE)
    
    # Create Maps: ThemeName -> Industry
    # Assuming columns: Industry, Theme, Companies_Count, Filename, Match_Info
    # We normalized "Theme" usually matches the filename logic roughly.
    
    # Map from "Theme Name" (exact) to "Industry"
    theme_to_industry = dict(zip(ref_df['Theme'].str.lower(), ref_df['Industry']))
    
    # Map from "Filename" (exact) to "Industry" (Strongest link)
    filename_to_industry = dict(zip(ref_df['Filename'], ref_df['Industry']))
    
    # Valid Industries list
    valid_industries = ref_df['Industry'].unique().tolist()
    
    print(f"Loaded {len(theme_to_industry)} validated theme classifications.")

    # 2. Process Files in Data Dir
    files = [f for f in os.listdir(THEMES_DIR) if f.endswith(".csv")]
    results = []
    
    print(f"Scanning {len(files)} files in {THEMES_DIR}...")
    
    for filename in files:
        filepath = os.path.join(THEMES_DIR, filename)
        count = count_companies(filepath)
        
        # Strategies to classify:
        # A) Known Filename? (Best)
        # B) Known Theme Name text?
        # C) Fuzzy Match against Known Themes?
        
        industry = "Unclassified"
        theme_name = filename.replace(".csv", "").replace("_", " ").title()
        match_info = "New"
        
        # A. Known Filename
        if filename in filename_to_industry:
            industry = filename_to_industry[filename]
            match_info = "Known File"
        else:
            # B. Fuzzy match against known File names (as proxy for theme)
            # Normalize current filename
            norm_name = normalize_text(filename)
            known_filenames = list(filename_to_industry.keys())
            
            # Simple fuzzy extraction
            best_match, score = process.extractOne(filename, known_filenames)
            
            if score >= 85:
                industry = filename_to_industry[best_match]
                match_info = f"Fuzzy Match File ({score}%)"
            else:
                # Fallback: Default to "Unclassified" (or maybe prompt AI in future)
                match_info = "Unknown"

        results.append({
            'Industry': industry,
            'Theme': theme_name,
            'Companies_Count': count,
            'Filename': filename,
            'Match_Info': match_info
        })
        
    # 3. Save
    out_df = pd.DataFrame(results)
    out_df = out_df.sort_values(by=['Industry', 'Companies_Count'], ascending=[True, False])
    
    out_df.to_csv(OUTPUT_FILE_SAFE, index=False)
    print(f"Done. Classified {len(results)} themes.")
    print(f"Saved update proposal to: {OUTPUT_FILE_SAFE}")
    print("Review this file. If correct, rename it to replace 'data/industry_summary_offline.csv'.")

if __name__ == "__main__":
    main()
