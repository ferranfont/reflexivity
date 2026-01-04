import pandas as pd
from sqlalchemy import create_engine, text
import re
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- CONFIGURATION ---
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
TABLE_NAME = "theme_summary"

# Explicit mapping to ensure unique 2-letter prefixes for Industries
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
    "Other": "OT", # Should be empty but adding just in case
    "Unclassified": "UN"
}

def get_clean_chars(text, length=3):
    """Extract first 'length' alphanumeric chars, upper case."""
    clean = re.sub(r'[^a-zA-Z0-9]', '', str(text)).upper()
    return clean[:length].ljust(length, 'X')

def update_codes():
    print("--- Generating XX_XXX Codes for Themes ---")
    connection_string = f"mysql+mysqlconnector://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    engine = create_engine(connection_string)
    
    with engine.connect() as conn:
        # Fetch all data
        result = conn.execute(text(f"SELECT Industry, Theme FROM {TABLE_NAME}"))
        rows = result.fetchall()
        
        print(f"Processing {len(rows)} themes...")
        
        used_codes = set()
        updates = []
        
        for row in rows:
            industry = row[0]
            theme = row[1]
            
            # 1. Industry Prefix (2 chars)
            ind_code = INDUSTRY_MAP.get(industry, "ZZ")
            if ind_code == "ZZ" and industry:
                # Fallback if industry not in map
                ind_code = get_clean_chars(industry, 2)
            
            # 2. Theme Suffix (3 chars)
            thm_code = get_clean_chars(theme, 3)
            
            # 3. Combine
            base_code = f"{ind_code}_{thm_code}"
            
            # 4. Ensure Uniqueness
            # If AG_BIO exists, try AG_BIO1, AG_BIO2... ideally keeping it short but unique.
            # User asked for 3 chars for theme. If duplicate, we might need to modify the 3rd char or append.
            # Let's start with base_code.
            
            final_code = base_code
            counter = 1
            while final_code in used_codes:
                # Collision resolution
                # Try to use next letters of theme name if available?
                # Or just append number? user asked for XX_XXX format.
                # Let's try to grab more chars from theme if possible to make the 3 chars unique
                # But 'get_clean_chars' only returned 3.
                
                # Extended strategy:
                # If 'AG_BIO' is taken, try to find a variant.
                # Variant 1: try 4th char of theme name?
                # Variant 2: Append number. 'AG_BI1'
                
                suffix = str(counter)
                # Cut one char from theme code to make room for number?
                # XX_XX1
                prefix_part = base_code[:-1] 
                final_code = f"{prefix_part}{suffix}"
                counter += 1
                
                if counter > 9:
                    # If we have > 9 collisions, expand?
                    final_code = f"{base_code}_{counter}"
            
            used_codes.add(final_code)
            updates.append({"code": final_code, "theme": theme})
            
        # Commit updates
        print("Pushing updates to DB...")
        try:
            for up in updates:
                stmt = text(f"UPDATE {TABLE_NAME} SET theme_id = :code WHERE Theme = :theme")
                conn.execute(stmt, up)
            conn.commit()
            print("Successfully updated theme_ids.")
            
        except Exception as e:
            conn.rollback()
            print(f"Error: {e}")

    # Verify
    with engine.connect() as conn:
        print("\nSample Data:")
        result = conn.execute(text(f"SELECT Industry, Theme, theme_id FROM {TABLE_NAME} LIMIT 15"))
        for row in result:
            print(f"{row[0]} | {row[1]} -> {row[2]}")

if __name__ == "__main__":
    update_codes()
