
import csv

file_path = r'd:/PYTHON/ALGOS/reflexivity/data/all_themes/agribusiness.csv'

print(f"Scanning {file_path} for errors...")

with open(file_path, 'r', encoding='utf-8') as f:
    # Just read lines to keep it simple, we will feed them to csv.reader one by one
    lines = f.readlines()

for i, line in enumerate(lines):
    # Skip empty lines
    if not line.strip():
        continue
        
    try:
        # csv.reader expects an iterable of lines
        reader = csv.reader([line], skipinitialspace=True)
        row = next(reader)
        # If we get here, it parsed. Check if number of columns is consistent?
        # Header has 14 columns.
        if len(row) != 14:
            # Maybe just a warning, but could be the shift source
            pass 
    except csv.Error as e:
        print(f"ERROR on line {i+1}: {e}")
        print(f"Content: {line}")
        # Stop after first error to let me fix it
        break
    except Exception as e:
        print(f"Unexpected error line {i+1}: {e}")
