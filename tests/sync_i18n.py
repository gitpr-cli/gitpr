import os
import re
import json

src_dirs = ['src', 'main.py', 'run.py']
pattern = re.compile(r'__\([\'"](.*?)[\'"]\)')

keys_in_code = set()

def scan_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
            # Handle potential multi-line matching or just basic matching.
            # Usually translations are on a single line.
            matches = pattern.findall(content)
            for match in matches:
                keys_in_code.add(match)
    except Exception as e:
        print(f"Error scanning {filepath}: {e}")

def scan_dir(directory):
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                scan_file(os.path.join(root, file))

# Scan all python files
for d in src_dirs:
    if os.path.isfile(d):
        scan_file(d)
    elif os.path.isdir(d):
        scan_dir(d)

langs_dir = 'langs'
lang_files = ['pt_br.json', 'pt_pt.json', 'es_es.json', 'fr_fr.json', 'es.json','fr.json']

# List sorted to keep the json ordered
sorted_keys = sorted(list(keys_in_code))

for lang_file in lang_files:
    filepath = os.path.join(langs_dir, lang_file)
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        continue
        
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    new_data = {}
    
    for key in sorted_keys:
        if key in data:
            new_data[key] = data[key]
        else:
            new_data[key] = key  # Default to English key if translation is missing

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(new_data, f, indent=2, ensure_ascii=False)
        
    print(f"Updated {lang_file} successfully.")

print(f"Total active keys found in codebase: {len(sorted_keys)}")
