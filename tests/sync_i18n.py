import ast
import json
import os
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SRC_DIRS = [REPO / "src", REPO / "run.py"]
LANGS_DIR = REPO / "langs"
LANG_FILES = ["pt_br.json", "pt_pt.json", "es_es.json", "fr_fr.json", "es.json", "fr.json"]


def _extract_keys(source, keys):
    """Extracts every __("literal") translation key from Python source using AST.

    Handles single and double quotes, escape sequences, nested calls, kwargs,
    and folds implicit string concatenations (__("a " "b") and multi-line literals)
    into the single combined string that runtime lookup expects.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)):
            continue
        if node.func.id != "__" or not node.args:
            continue
        first = node.args[0]
        if isinstance(first, ast.Constant) and isinstance(first.value, str):
            keys.add(first.value)


def scan_file(filepath, keys):
    """Scans a single .py file, adding every __() string literal to `keys`."""
    try:
        path = Path(filepath)
        content = path.read_text(encoding="utf-8", errors="replace")
        _extract_keys(content, keys)
    except Exception as e:
        print(f"Error scanning {filepath}: {e}")


def scan_dir(directory, keys):
    for path in Path(directory).rglob("*.py"):
        scan_file(path, keys)


def scan(keys):
    """Scans every Python source in SRC_DIRS, collecting keys into `keys`."""
    for path in SRC_DIRS:
        if path.is_file():
            scan_file(path, keys)
        elif path.is_dir():
            scan_dir(path, keys)


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

    # List sorted to keep the json ordered
    sorted_keys = sorted(list(keys_in_code))

    for lang_file in LANG_FILES:
        filepath = LANGS_DIR / lang_file
        if not filepath.exists():
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
