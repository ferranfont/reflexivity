
file_path = r'd:/PYTHON/ALGOS/reflexivity/data/all_themes/agribusiness.csv'

print("Checking for odd quote counts...")

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    quote_count = line.count('"')
    if quote_count % 2 != 0:
        print(f"Line {i+1} has ODD quotes ({quote_count}):")
        print(line[:100] + "...")
