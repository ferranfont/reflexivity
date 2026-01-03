
import re

file_path = r'd:/PYTHON/ALGOS/reflexivity/data/all_themes/agribusiness.csv'
output_path = r'd:/PYTHON/ALGOS/reflexivity/data/all_themes/agribusiness_fixed.csv'

print("Analyzing agribusiness.csv...")

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

header = lines[0].strip()
print("Header:", header)
# Clean header
clean_cols = [c.strip() for c in header.split(',')]
print("Clean Cols:", clean_cols)

fixed_lines = []
# Add clean header
fixed_lines.append(",".join(clean_cols))

# Regex to split by comma (ignoring quotes)
split_pattern = re.compile(r',(?=(?:[^"]*"[^"]*")*[^"]*$)')

for i, line in enumerate(lines[1:]):
    line = line.strip()
    if not line: continue
    
    parts = split_pattern.split(line)
    
    # We expect 14 columns
    if len(parts) < 14:
        # Pad with empty strings if needed (rare case for last cols)
        parts.extend([''] * (14 - len(parts)))
    
    # Clean parts (strip spaces outside quotes)
    clean_parts = [p.strip() for p in parts]
    
    # Validation
    # part 0: type -> agriculture
    # part 1: link_type -> agribusiness
    # part 3: name -> Should confirm it's not JSON
    
    name_val = clean_parts[3]
    if '{' in name_val and 'http' in name_val:
        print(f"CRITICAL: Row {i+2} parsed 'name' as JSON/URL!")
        print(f"Raw Line: {line}")
        print(f"Parsed Name: {name_val}")
        # Attempt to recover? 
        # Maybe the comma splitter failed?
    
    # Enforce type/link_type just in case
    clean_parts[0] = 'agriculture'
    clean_parts[1] = 'agribusiness'
    
    # Reconstruct line
    # We need to be careful not to double-quote already quoted strings
    # But stripped parts might still have quotes.
    # Safe approach: if it doesn't have quotes and has comma, Quote it.
    # If it has quotes, keep them.
    
    final_parts = []
    for p in clean_parts:
        if ',' in p and not (p.startswith('"') and p.endswith('"')):
            p = f'"{p}"'
        final_parts.append(p)
        
    fixed_lines.append(",".join(final_parts))

with open(output_path, 'w', encoding='utf-8') as f:
    f.write("\n".join(fixed_lines))

print(f"\nSaved fixed file to {output_path}")

# Now replace the original
import shutil
shutil.move(output_path, file_path)
print("Replaced original file.")
