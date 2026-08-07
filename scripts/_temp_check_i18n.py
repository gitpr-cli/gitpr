import json
import re
import sys

# Force UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

with open('langs/pt_br.json', encoding='utf-8') as f:
    existing = json.load(f)

with open('src/main.py', encoding='utf-8') as f:
    content = f.read()

# Match __("...") or __('...') — handle escaped quotes inside
# Use a simpler approach: find __( then match until the closing ) accounting for nested parens in format strings
pattern = r'__\(("(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\')'
matches = re.findall(pattern, content)

keys_from_main = []
for m in matches:
    val = m[1:-1]  # strip outer quotes
    # unescape
    val = val.replace('\\n', '\n').replace('\\t', '\t').replace('\\"', '"').replace("\\'", "'")
    keys_from_main.append(val)

unique_keys = list(dict.fromkeys(keys_from_main))
missing = [k for k in unique_keys if k not in existing]

print(f'Unique __() keys in main.py: {len(unique_keys)}')
print(f'Missing from pt_br.json: {len(missing)}')
print()
for i, k in enumerate(missing, 1):
    # Use ascii-safe repr for display
    r = repr(k)
    print(f'{i}. {r}')
    # Also print the actual key length for debugging
    print(f'   len={len(k)} ends_with_newline={k.endswith(chr(10))}')
