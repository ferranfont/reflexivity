
import csv

file_path = r'd:/PYTHON/ALGOS/reflexivity/data/all_themes/agribusiness.csv'

print(f"Scanning {file_path} for column count mismatches...")

header_cols = 14

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if not line.strip(): continue
    
    try:
        # Use simple split first to see if it's wildly off, but csv.reader is the truth
        reader = csv.reader([line], skipinitialspace=True)
        row = next(reader)
        
        if len(row) != header_cols:
            print(f"Line {i+1} has {len(row)} columns (expected {header_cols})")
            # Print first few chars to identify
            print(f"Start: {line[:50]}...")
            
    except csv.Error as e:
        print(f"CSV Error line {i+1}: {e}")
