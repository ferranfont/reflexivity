
import os

themes_dir = r"d:/PYTHON/ALGOS/reflexivity/data/all_themes"

def count_companies_in_themes(directory):
    total_companies = 0
    file_count = 0
    
    if not os.path.exists(directory):
        print(f"Directory not found: {directory}")
        return

    files = [f for f in os.listdir(directory) if f.endswith(".csv")]
    
    print(f"Counting companies in {len(files)} theme files...")
    
    for filename in files:
        filepath = os.path.join(directory, filename)
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                # Subtract 1 for the header, ensure non-negative
                company_count = max(0, len(lines) - 1)
                total_companies += company_count
                file_count += 1
        except Exception as e:
            print(f"Error reading {filename}: {e}")

    print("-" * 30)
    print(f"Total Files Processed: {file_count}")
    print(f"Total Companies (sum of lines): {total_companies}")
    print("-" * 30)

if __name__ == "__main__":
    count_companies_in_themes(themes_dir)
