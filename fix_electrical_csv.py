
import os

target_file = r'd:/PYTHON/ALGOS/reflexivity/data/all_themes/electrical_components_and_equipment.csv'

with open(target_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
# Keep header
new_lines.append(lines[0])

# Process rest
for i, line in enumerate(lines[1:]):
    # Find the position of the second comma to preserve the rest of the line exactly
    first_comma = line.find(',')
    if first_comma == -1:
        # Should not happen in a valid CSV row, but just in case keeping it
        new_lines.append(line)
        continue
        
    second_comma = line.find(',', first_comma + 1)
    if second_comma == -1:
        new_lines.append(line)
        continue
        
    # Construct new line: new_type, new_link_type, rest_of_line
    # type = industrial
    # link_type = electrical_components_and_equipment
    
    rest_of_line = line[second_comma + 1:] 
    new_line = f"industrial, electrical_components_and_equipment,{rest_of_line}"
    new_lines.append(new_line)

with open(target_file, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print(f"Successfully updated {len(new_lines)} lines in {target_file}")
