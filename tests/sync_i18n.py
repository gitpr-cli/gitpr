import os
import re
import json
import ast

SRC_DIRS = ['src', 'main.py', 'run.py']
LANG_FILES = ['pt_br.json', 'pt_pt.json', 'es_es.json', 'fr_fr.json', 'es.json', 'fr.json']

# Captures only the string literal of __("...") calls. Deliberately does NOT
# require a trailing ")": that requirement ran the match past kwargs
# (e.g. __("...", count=len(x)), fg="red") and mangled keys.
# Known limitations (accepted): adjacent literals __("a" "b") yield only "a";
# multi-line literals are captured up to the first line's closing quote.
PATTERN = re.compile(r'__\(\s*(["\'])(?:\\.|(?!\1).)*\1')


def scan_file(filepath, keys):
    """Scans a single .py file, adding every __() string literal to `keys`.

    Literals are parsed with ast.literal_eval so escape sequences resolve to
    the exact runtime string the translation lookup compares against.
    """
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
            # Handle potential multi-line matching or just basic matching.
            # Usually translations are on a single line.
            for m in PATTERN.finditer(content):
                # The capture group is the opening quote; the whole match is
                # __('body', so slice from the quote to get the full literal.
                literal = m.group(0)[m.start(1) - m.start():]
                try:
                    keys.add(ast.literal_eval(literal))
                except (ValueError, SyntaxError):
                    keys.add(literal[1:-1])  # Fallback: raw body without quotes
    except Exception as e:
        print(f"Error scanning {filepath}: {e}")


def scan_dir(directory, keys):
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                scan_file(os.path.join(root, file), keys)


def scan(keys):
    """Scans every Python source in SRC_DIRS, collecting keys into `keys`."""
    for d in SRC_DIRS:
        if os.path.isfile(d):
            scan_file(d, keys)
        elif os.path.isdir(d):
            scan_dir(d, keys)


def _live_key(key):
    """Maps a stored key to its runtime form (real escape characters).

    Keys written double-escaped (literal backslash-n, backslash-quote) never
    match the strings the code produces, so the rebuild lookups happen on the
    unescaped form.
    """
    return key.replace("\\n", "\n").replace("\\r", "\r").replace("\\'", "'")


if __name__ == "__main__":
    keys_in_code = set()
    scan(keys_in_code)

    if not keys_in_code:
        print("No active keys found in codebase. Aborting without changes.")
        raise SystemExit(1)

    langs_dir = 'langs'

    # List sorted to keep the json ordered
    sorted_keys = sorted(list(keys_in_code))

    for lang_file in LANG_FILES:
        filepath = os.path.join(langs_dir, lang_file)
        if not os.path.exists(filepath):
            print(f"File not found: {filepath}")
            continue

        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Legacy files may spell newlines as literal backslash-n sequences,
        # which never match the runtime strings. Indexing by the unescaped
        # form lets those entries migrate to their live keys instead of being
        # dropped (and their translations lost).
        live_index = {_live_key(k): v for k, v in data.items()}

        new_data = {}

        for key in sorted_keys:
            if key in live_index:
                new_data[key] = live_index[key]
            else:
                new_data[key] = key  # Default to English key if translation is missing

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(new_data, f, indent=2, ensure_ascii=False)
            f.write("\n")

        print(f"Updated {lang_file} successfully.")

    print(f"Total active keys found in codebase: {len(sorted_keys)}")
