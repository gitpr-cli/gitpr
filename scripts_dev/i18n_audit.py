"""Audit i18n: find __() keys missing from langs/pt_br.json and show usage context."""
import ast
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
LANG_FILE = ROOT / "langs" / "pt_br.json"

lang_keys = set(json.loads(LANG_FILE.read_text(encoding="utf-8")).keys())

used = {}  # key -> set of (file, line, source_line)
for py in sorted(SRC.rglob("*.py")):
    try:
        text = py.read_text(encoding="utf-8")
        tree = ast.parse(text)
    except SyntaxError as e:
        print(f"SYNTAX ERROR {py}: {e}", file=sys.stderr)
        continue
    lines = text.splitlines()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        fn = node.func
        is_i18n = (isinstance(fn, ast.Name) and fn.id == "__") or (
            isinstance(fn, ast.Attribute) and fn.attr == "__"
        )
        if not is_i18n:
            continue
        if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
            key = node.args[0].value
            used.setdefault(key, []).append((str(py.relative_to(ROOT)), node.lineno))

missing = {k: v for k, v in used.items() if k not in lang_keys}

print(f"TOTAL unique __() keys in code: {len(used)}")
print(f"MISSING from pt_br.json: {len(missing)}")

if "--dump" in sys.argv:
    Path(ROOT / "scripts_dev" / "i18n_missing.json").write_text(
        json.dumps(missing, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("dumped to scripts_dev/i18n_missing.json")

if "--ctx" in sys.argv:
    full = "--full" in sys.argv
    for key, usages in sorted(missing.items()):
        for rel, lineno in usages:
            py = ROOT / rel
            text = py.read_text(encoding="utf-8")
            tree = ast.parse(text)
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                fn = node.func
                is_i18n = (isinstance(fn, ast.Name) and fn.id == "__") or (
                    isinstance(fn, ast.Attribute) and fn.attr == "__"
                )
                if not is_i18n or node.lineno != lineno:
                    continue
                seg = ast.get_source_segment(text, node)
                seg = seg.replace("\n", "\\n")
                print(f"=== {rel}:{lineno} ===")
                print(f"  {seg[:400]}")
                break
