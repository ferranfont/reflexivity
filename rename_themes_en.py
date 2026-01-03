import os
import time
from googletrans import Translator

# Directory containing the CSV files
themes_dir = "data/all_themes"

# Initialize translator
translator = Translator()

def translate_filename(spanish_name):
    """
    Translates a filename from Spanish to English, keeping the extension.
    Converts to lowercase as requested.
    """
    base_name = os.path.splitext(spanish_name)[0]
    extension = os.path.splitext(spanish_name)[1]
    
    # Check if file is already possibly English (simple heuristc) or just skip translation logic details
    # We will just translate the base name.
    # Replace underscores with spaces for better translation context if needed, 
    # though Google Translate handles underscores reasonably well, spaces are safer.
    text_to_translate = base_name.replace("_", " ")
    
    try:
        # Translate to English
        translation = translator.translate(text_to_translate, src='es', dest='en').text
        
        # Format: lowercase and replace spaces with underscores (if any remain)
        # Note: The user requested "Agroindustria.csv -> agroindustry.py" in example but meant .csv doubtless.
        # Wait, the user said "agroindustry.py" in the prompt text: "debe ser agroindustry.py".
        # But clearly they are CSV files ("ficheros csv"). I will assume they meant keep .csv extension.
        # Wait, strictly following: "cambia el nombre de los ficheros csv ... debe ser agroindustry.py"
        # That's extremely likely a typo, renaming data files to .py is dangerous/wrong.
        # I will stick to .csv to avoid destroying data usability, assuming typo.
        
        clean_name = translation.lower().replace(" ", "_")
        # Remove any non-alphanumeric chars except underscores (optional but good for filenames)
        clean_name = "".join([c for c in clean_name if c.isalnum() or c == '_'])
        
        return f"{clean_name}{extension}"
    except Exception as e:
        print(f"Error translating '{spanish_name}': {e}")
        return None

def rename_files():
    if not os.path.exists(themes_dir):
        print(f"Directory {themes_dir} not found.")
        return

    files = [f for f in os.listdir(themes_dir) if f.endswith(".csv")]
    count = 0
    
    print(f"Found {len(files)} files to process.")
    
    for filename in files:
        new_name = translate_filename(filename)
        
        if new_name and new_name != filename:
            old_path = os.path.join(themes_dir, filename)
            new_path = os.path.join(themes_dir, new_name)
            
            # Check if target already exists to avoid overwriting unique files
            if os.path.exists(new_path):
                print(f"Skipping {filename} -> {new_name} (Target already exists)")
                continue
                
            try:
                os.rename(old_path, new_path)
                print(f"Renamed: {filename} -> {new_name}")
                count += 1
                # Small delay to avoid hitting rate limits if Google Translate API is strict (though library handles some)
                time.sleep(0.5) 
            except OSError as e:
                print(f"Error renaming {filename}: {e}")
                
    print(f"\nFinished. Renamed {count} files.")

if __name__ == "__main__":
    rename_files()
