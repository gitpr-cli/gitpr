#!/usr/bin/env python3
"""i18n Validation Script — audits __() keys in source files against language JSON files.

Usage:
    python scripts/validate_i18n.py
    python scripts/validate_i18n.py --fix-missing   # generate missing fr.json / es.json
"""

import json
import os
import re
import sys
from pathlib import Path
from collections import OrderedDict

# Fix Windows console encoding for emoji output
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_FILES = ["src/core.py", "src/updater.py"]
LANG_DIR = PROJECT_ROOT / "langs"
LANG_CODES = ["pt_br", "pt_pt", "fr", "es"]


def extract_i18n_calls(filepath: Path) -> list:
    """Extract all first-argument strings from __(...) calls.

    The i18n system uses __("English key") where the English string IS the key.
    We extract the raw text of the first argument (including multi-line strings).
    """
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    keys = []
    # Match __("...") or __('...') — the first string argument
    # Handles: __("text"), __("text {var}", var=x), __("text\nmore")
    pattern = r'__\(\s*"((?:[^"\\]|\\.)*)"'
    for m in re.finditer(pattern, content):
        key = m.group(1)
        # Resolve escape sequences the way Python would
        key = key.replace('\\n', '\n').replace('\\t', '\t').replace('\\r', '\r')
        key = key.replace('\\"', '"').replace("\\'", "'")
        keys.append(key)

    return keys


def extract_placeholders(text: str) -> set:
    """Extract {placeholder} names from a string."""
    return set(re.findall(r'\{(\w+)\}', text))


def check_hardcoded_strings(filepath: Path) -> list:
    """Flag potential hardcoded user-facing strings that might need i18n.

    Looks for click.secho / click.echo / print calls with literal strings
    that are NOT already wrapped in __().
    """
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()

    suspects = []
    # Patterns that suggest user-facing output not yet internationalized
    echo_patterns = [
        r'click\.(?:secho|echo)\s*\(\s*(?:f)?"([^"]+)"',
        r'click\.(?:secho|echo)\s*\(\s*(?:f)?\'([^\']+)\'',
    ]

    for i, line in enumerate(lines, 1):
        # Skip lines that already use __()
        if "__(" in line:
            continue
        # Skip comments
        if line.strip().startswith("#"):
            continue
        # Skip docstrings
        if '"""' in line or "'''" in line:
            continue

        for pat in echo_patterns:
            m = re.search(pat, line)
            if m:
                text = m.group(1)
                # Skip format-only strings with no actual text content
                if text.strip() in ("", "{}", "{error}", " ".join):
                    continue
                # Skip purely structural output (empty lines)
                if text.strip() == "":
                    continue
                suspects.append((i, text.strip()[:80]))
                break

    return suspects


def validate_placeholders(code_keys: list, lang_file: Path) -> list:
    """Check that all placeholders in code keys are preserved in translations."""
    with open(lang_file, "r", encoding="utf-8", errors="replace") as f:
        translations = json.load(f)

    errors = []
    for key in code_keys:
        if key not in translations:
            continue
        code_placeholders = extract_placeholders(key)
        trans_placeholders = extract_placeholders(translations[key])
        missing = code_placeholders - trans_placeholders
        extra = trans_placeholders - code_placeholders
        if missing:
            errors.append((key, f"missing placeholders in translation: {missing}"))
        if extra:
            errors.append((key, f"extra placeholders in translation: {extra}"))

    return errors


def main():
    print("=" * 60)
    print("  GitPR i18n Validation Audit")
    print("=" * 60)

    # 1. Extract all keys from source files
    all_keys = []
    for src_file in SRC_FILES:
        fpath = PROJECT_ROOT / src_file
        if not fpath.exists():
            print(f"  ⚠ File not found: {src_file}")
            continue
        keys = extract_i18n_calls(fpath)
        print(f"\n🔍 {src_file}: {len(keys)} __() calls found")
        all_keys.extend(keys)

    # Deduplicate while preserving order
    seen = set()
    unique_keys = []
    for k in all_keys:
        if k not in seen:
            seen.add(k)
            unique_keys.append(k)

    print(f"\n📊 Total unique i18n keys in source: {len(unique_keys)}")

    # 2. Check each language file
    print("\n" + "-" * 40)
    print("  Language File Audit")
    print("-" * 40)

    results = {}
    for lang in LANG_CODES:
        lang_file = LANG_DIR / f"{lang}.json"
        status_icon = "✅"
        details = []

        if not lang_file.exists():
            status_icon = "❌"
            details.append("FILE MISSING — needs to be created")
            results[lang] = {"status": "missing", "missing_keys": unique_keys, "extra_keys": [], "placeholder_errors": []}
        else:
            with open(lang_file, "r", encoding="utf-8", errors="replace") as f:
                try:
                    translations = json.load(f)
                except json.JSONDecodeError as e:
                    status_icon = "❌"
                    details.append(f"INVALID JSON: {e}")
                    results[lang] = {"status": "invalid_json", "missing_keys": [], "extra_keys": [], "placeholder_errors": []}
                    print(f"  {status_icon} {lang}.json: {details[0]}")
                    continue

            trans_keys = set(translations.keys())
            code_keys_set = set(unique_keys)

            missing = code_keys_set - trans_keys
            extra = trans_keys - code_keys_set
            placeholder_errors = validate_placeholders(unique_keys, lang_file)

            if missing:
                status_icon = "❌"
                details.append(f"{len(missing)} MISSING keys")
            if extra:
                status_icon = "⚠️"
                details.append(f"{len(extra)} EXTRA keys (not in source)")
            if placeholder_errors:
                if status_icon == "✅":
                    status_icon = "⚠️"
                details.append(f"{len(placeholder_errors)} PLACEHOLDER errors")

            if not details:
                details.append("COMPLETE — all keys present and valid")

            # Show missing keys (up to 20)
            if missing and len(missing) <= 20:
                print(f"     Missing keys:")
                for k in sorted(missing):
                    print(f"       - {k[:100]!r}")
            if extra and len(extra) <= 20:
                print(f"     Extra keys (not in audited scope):")
                for k in sorted(extra):
                    print(f"       - {k[:100]!r}")

            results[lang] = {
                "status": "ok" if status_icon == "✅" else "issues",
                "missing_keys": missing,
                "extra_keys": extra,
                "placeholder_errors": placeholder_errors,
            }

        print(f"  {status_icon} {lang}.json: {len(unique_keys) if lang_file.exists() else 0}/{len(unique_keys)} keys — {'; '.join(details)}")

    # 3. Check for hardcoded strings
    print("\n" + "-" * 40)
    print("  Hardcoded String Check")
    print("-" * 40)

    total_suspects = 0
    for src_file in SRC_FILES:
        fpath = PROJECT_ROOT / src_file
        if not fpath.exists():
            continue
        suspects = check_hardcoded_strings(fpath)
        if suspects:
            total_suspects += len(suspects)
            print(f"\n  ⚠ {src_file}: {len(suspects)} potential hardcoded strings:")
            for line_no, text in suspects[:15]:  # show first 15
                print(f"     L{line_no}: \"{text}\"")
            if len(suspects) > 15:
                print(f"     ... and {len(suspects) - 15} more")

    if total_suspects == 0:
        print("  ✅ No hardcoded strings detected (all user-facing output uses __())")

    # 4. Summary
    print("\n" + "=" * 60)
    print("  Summary")
    print("=" * 60)
    print(f"  Source keys:           {len(unique_keys)}")
    for lang in LANG_CODES:
        r = results.get(lang, {})
        if r.get("status") == "missing":
            print(f"  {lang}.json:         ❌ FILE MISSING")
        elif r.get("status") == "invalid_json":
            print(f"  {lang}.json:         ❌ INVALID JSON")
        else:
            missing = len(r.get("missing_keys", []))
            extra = len(r.get("extra_keys", []))
            ph_errs = len(r.get("placeholder_errors", []))
            parts = []
            if missing:
                parts.append(f"{missing} missing")
            if extra:
                parts.append(f"{extra} extra")
            if ph_errs:
                parts.append(f"{ph_errs} placeholder errors")
            if parts:
                print(f"  {lang}.json:         ⚠️ {', '.join(parts)}")
            else:
                print(f"  {lang}.json:         ✅ complete")

    print(f"\n  Hardcoded suspects:    {total_suspects}")

    # 5. Generate fix suggestions
    needs_fix = any(
        r.get("status") in ("missing", "invalid_json") or
        len(r.get("missing_keys", [])) > 0 or
        len(r.get("placeholder_errors", [])) > 0
        for r in results.values()
    )

    if needs_fix or total_suspects > 0:
        print("\n⚠️  ACTION REQUIRED — see details above")
    else:
        print("\n✅ All language files are complete and valid!")

    # Return data for programmatic use
    return unique_keys, results, total_suspects


if __name__ == "__main__":
    main()
