import pandas as pd
import os
import re
from fuzzywuzzy import process

# --- CONFIGURATION ---
REFERENCE_FILE = "data/trends_by_sector.csv"
THEMES_DIR = "data/all_themes"

def normalize_text(text):
    """Normalize text for better matching."""
    if not isinstance(text, str):
        return ""
    text = text.replace(".csv", "")
    text = text.replace("_", " ")
    text = text.lower()
    text = re.sub(r'[^a-z0-9 ]', '', text)
    return text.strip()

def load_reference_mapping():
    """Load the mapping from Reference file (Trend -> Sector)."""
    try:
        ref_df = pd.read_csv(REFERENCE_FILE)
    except Exception as e:
        print(f"Error loading reference file: {e}")
        return None, None

    # Normalize trend names for matching
    ref_df['trend_norm'] = ref_df['trend'].apply(normalize_text)
    
    # Dictionary: Normalized Trend -> Sector
    trend_to_sector = dict(zip(ref_df['trend_norm'], ref_df['sector']))
    
    # List of valid normalized trends for fuzzy matching
    valid_trends = ref_df['trend_norm'].tolist()
    
    return trend_to_sector, valid_trends

def get_industry_for_file(filename, trend_to_sector, valid_trends):
    """Determine Industry from Filename using the mapping."""
    file_norm = normalize_text(filename)
    
    # 1. Exact Match
    if file_norm in trend_to_sector:
        return trend_to_sector[file_norm]
    
    # 2. Fuzzy Match
    best_match, score = process.extractOne(file_norm, valid_trends)
    if score >= 80: # Confidence threshold
        return trend_to_sector[best_match]
        
    return "Unclassified"

def update_csv_files():
    if not os.path.exists(THEMES_DIR):
        print("Themes directory not found.")
        return

    # Load mapping
    trend_to_sector, valid_trends = load_reference_mapping()
    if not trend_to_sector:
        return

    files = [f for f in os.listdir(THEMES_DIR) if f.endswith(".csv")]
    count = 0
    
    print(f"Updating {len(files)} files...")
    
    for filename in files:
        file_path = os.path.join(THEMES_DIR, filename)
        
        # 1. Get Industry
        industry = get_industry_for_file(filename, trend_to_sector, valid_trends)
        
        # 2. Get Theme Name (from filename)
        # e.g. "agribusiness" from "agribusiness.csv"
        theme_name = os.path.splitext(filename)[0].lower() # Keep underscores if present, or spaces?
        # User example: "agribusiness.csv" -> "agribusiness"
        # If filename is "Consumer_Brands.csv" -> "consumer_brands"? 
        # User said "extracted from the name of the csv". Usually they are snake_case now.
        
        try:
            # Read CSV
            df = pd.read_csv(file_path)
            
            # Check if columns exist
            if 'type' not in df.columns or 'link_type' not in df.columns:
                print(f"Skipping {filename}: Missing 'type' or 'link_type' columns.")
                continue
            
            # Update columns
            # type -> Industry (lowercase)
            df['type'] = industry.lower()
            
            # link_type -> Theme Name (lowercase)
            df['link_type'] = theme_name
            
            # Save back
            df.to_csv(file_path, index=False)
            count += 1
            
            if count % 50 == 0:
                print(f"Processed {count} files...")
                
        except Exception as e:
            print(f"Error processing {filename}: {e}")

    print(f"Finished. Updated {count} files.")

if __name__ == "__main__":
    update_csv_files()
