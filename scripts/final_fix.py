#!/usr/bin/env python3
"""Final fix: remove PT-BR-as-key bug, fix curly quote variants, sync pairs."""
import json, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Step 1: Fix pt_br.json — remove PT-BR key accidentally used as key
with open("langs/pt_br.json", "r", encoding="utf-8") as f:
    pt_br = json.load(f)

bad_key = "Regra '{rule_name}' contém Regex inválida: {error}"
if bad_key in pt_br:
    del pt_br[bad_key]
    print(f"Removed bad PT-BR-as-key from pt_br")

with open("langs/pt_br.json", "w", encoding="utf-8") as f:
    json.dump(pt_br, f, ensure_ascii=False, indent=2)

# Step 2: Fix all other files
for code in ["pt_pt", "es", "fr", "es_es", "fr_fr"]:
    with open(f"langs/{code}.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    # Remove bad key
    if bad_key in data:
        del data[bad_key]

    # Fix keys with curly quotes
    fixes_curly = {
        "Downloads template files (.gitpr.*.md and .gitpr.linter.yml) from the official repository to the project root. These files allow customizing the AI behavior according to your team’s rules. NEVER overwrites existing local files.": {
            "fr": "Télécharge les fichiers de template (.gitpr.*.md et .gitpr.linter.yml) du dépôt officiel à la racine du projet. Ces fichiers permettent de personnaliser le comportement de l'IA selon les règles de votre équipe. N'ÉCRASE JAMAIS les fichiers locaux existants.",
            "es": "Descarga archivos de plantilla (.gitpr.*.md y .gitpr.linter.yml) del repositorio oficial a la raíz del proyecto. Estos archivos permiten personalizar el comportamiento de la IA según las reglas de su equipo. NUNCA sobrescribe archivos locales existentes.",
        },
        "You can now open the generated files and customize the tool’s behavior for your project:\n": {
            "fr": "Vous pouvez maintenant ouvrir les fichiers générés et personnaliser le comportement de l'outil pour votre projet :\n",
            "es": "Ahora puede abrir los archivos generados y personalizar el comportamiento de la herramienta para su proyecto:\n",
        },
    }

    lang_base = {"es": "es", "es_es": "es", "fr": "fr", "fr_fr": "fr", "pt_pt": "pt"}[code]
    translated = 0
    for k, lang_fixes in fixes_curly.items():
        if k in data and data[k] == k and lang_base in lang_fixes:
            data[k] = lang_fixes[lang_base]
            translated += 1

    with open(f"langs/{code}.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"{code}.json: {len(data)} keys | fixed: {translated}")

# Step 3: Make es==es_es and fr==fr_fr identical
for base, alias in [("es", "es_es"), ("fr", "fr_fr")]:
    with open(f"langs/{base}.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    with open(f"langs/{alias}.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# Step 4: Final report
print()
print("=" * 55)
print("  FINAL STATE")
print("=" * 55)
for fname in ["pt_br.json", "pt_pt.json", "es.json", "fr.json", "es_es.json", "fr_fr.json"]:
    with open(f"langs/{fname}", "r", encoding="utf-8") as f:
        data = json.load(f)
    untrans = [(k, v) for k, v in data.items() if k == v and not k.endswith(".py")]
    # Only keys with REAL code fragments (not embedded JSON in string content)
    real_bad = 0
    for k in data:
        if '", error=' in k or '", count=' in k or '", provider=' in k or '", n=' in k or 'fg="' in k:
            real_bad += 1

    print(f"{fname:15s}: {len(data):4d} keys | code_frags:{real_bad} | untranslated:{len(untrans)}")
    if untrans:
        for k, v in untrans:
            print(f"  [{k[:90]}]")
    print()
