import pandas as pd
import os
import glob

# --- CONFIGURATION ---
THEMES_DIR = "data/all_themes"

def reorder_symbol_third():
    print("--- Bulk Reordering: symbol -> 3rd position (between theme_id and industry) ---")
    
    if not os.path.exists(THEMES_DIR):
        print(f"Directory not found: {THEMES_DIR}")
        return

    csv_files = glob.glob(os.path.join(THEMES_DIR, "*.csv"))
    print(f"Found {len(csv_files)} files. Processing...")

    count = 0
    errors = 0
    skipped = 0
    
    priority_order = ['industry_id', 'theme_id', 'symbol', 'industry']
    
    for filepath in csv_files:
        try:
            # Read CSV
            df = pd.read_csv(filepath)
            cols = df.columns.tolist()
            
            # Normalize symbol naming for detection but keep original case for column list
            # Actually, let's just find the columns present
            
            present_priority = []
            
            # Helper to find actual column name case-insensitively or exact
            def find_col(name, columns):
                if name in columns:
                    return name
                # fallback common case
                if name == 'symbol' and 'Symbol' in columns:
                    return 'Symbol'
                return None

            # 1. industry_id
            c_ind_id = find_col('industry_id', cols)
            
            # 2. theme_id
            c_thm_id = find_col('theme_id', cols)
            
            # 3. symbol
            c_sym = find_col('symbol', cols)
            
            # 4. industry (was 'type')
            c_ind = find_col('industry', cols)
            
            # Construct new order
            new_order = []
            
            if c_ind_id: new_order.append(c_ind_id)
            if c_thm_id: new_order.append(c_thm_id)
            if c_sym: new_order.append(c_sym)
            if c_ind: new_order.append(c_ind)
            
            # Add remaining columns
            for c in cols:
                if c not in new_order:
                    new_order.append(c)
            
            # Check if order actually changes
            if new_order != cols:
                df = df[new_order]
                df.to_csv(filepath, index=False)
                count += 1
            else:
                skipped += 1
            
        except Exception as e:
            print(f"Error processing {os.path.basename(filepath)}: {e}")
            errors += 1
            
        if (count + skipped + errors) % 50 == 0 and (count + skipped + errors) > 0:
            print(f"Processed {count + skipped + errors} files...")

    print(f"Done. Reordered {count} files. Skipped {skipped}. Errors: {errors}")

if __name__ == "__main__":
    reorder_symbol_third()
