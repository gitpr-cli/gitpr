#!/usr/bin/env python3
"""Sync all language files with pt_br.json as the authoritative source."""
import json, re, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

with open("langs/pt_br.json", "r", encoding="utf-8") as f:
    pt_br = json.load(f)

LANG_FILES = {"pt_pt": "langs/pt_pt.json", "fr": "langs/fr.json", "es": "langs/es.json"}
langs = {}
for code, path in LANG_FILES.items():
    with open(path, "r", encoding="utf-8") as f:
        langs[code] = json.load(f)

# -----------------------------------------------------------
# PT-BR translations for fr and es (common keys)
# -----------------------------------------------------------
FR = {
    "Help": "Aide", "Save Local": "Sauvegarder Local", "Create on GitHub": "Créer sur GitHub",
    "Exit": "Quitter", "Got it": "Compris", "Refresh Diff": "Actualiser Diff",
    "Auto-Patch": "Auto-Patch", "Export": "Exporter", "Online Help": "Aide en ligne",
    "Refresh": "Actualiser", "Path": "Chemin", "Files": "Fichiers",
    "Disk usage": "Utilisation disque", "Command": "Commande", "Status": "Statut",
    "Provider": "Fournisseur", "Tokens": "Jetons", "Duration (ms)": "Durée (ms)",
    "Total events": "Total événements", "Errors": "Erreurs", "Total tokens": "Total jetons",
    "Top commands": "Commandes principales", "Providers": "Fournisseurs",
    "Range": "Période", "Showing": "Affichage", "of": "de", "events": "événements",
    "All repositories": "Tous les dépôts", "Repository": "Dépôt",
    "Timestamp": "Horodatage", "Unknown": "Inconnu",
    "auto-patch": "auto-patch", "Tokens (cache)": "Jetons (cache)",
    "Tokens (events)": "Jetons (événements)", "Cache files": "Fichiers cache",
    "Cache files found": "Fichiers cache trouvés", "Press F5 to refresh": "Appuyez sur F5 pour actualiser",
    "No message": "Aucun message", "No metrics data found in ~/.gitpr/cache/prompts/": "Aucune donnée de métrique dans ~/.gitpr/cache/prompts/",
    "Scanning cache files...": "Analyse des fichiers cache...",
    "Total duration": "Durée totale", "Total entries": "Total entrées",
    "Entries": "Entrées", "new entries": "nouvelles entrées",
    "Previous Msg": "Msg Précédent", "Next Msg": "Msg Suivant",
    "Auto-Patch Msg": "Msg Auto-Patch", "Export Msg": "Exporter Msg",
    "Available Prompt Templates": "Templates de Prompt Disponibles",
    "Blame Prompt": "Prompt Blame", "Issue Prompt": "Prompt Issue",
    "Linter Prompt": "Prompt Linter", "PR Description Prompt": "Prompt Description PR",
    "Review PR Prompt": "Prompt Révision PR", "Explore Prompt": "Prompt Explorer",
    "Commit Message Prompt": "Prompt Message Commit",
    "Language Override (--lang)": "Remplacement de langue (--lang)",
    "F5 refresh": "Actualisation F5",
}

ES = {
    "Help": "Ayuda", "Save Local": "Guardar Local", "Create on GitHub": "Crear en GitHub",
    "Exit": "Salir", "Got it": "Entendido", "Refresh Diff": "Actualizar Diff",
    "Auto-Patch": "Auto-Patch", "Export": "Exportar", "Online Help": "Ayuda en línea",
    "Refresh": "Actualizar", "Path": "Ruta", "Files": "Archivos",
    "Disk usage": "Uso en disco", "Command": "Comando", "Status": "Estado",
    "Provider": "Proveedor", "Tokens": "Tokens", "Duration (ms)": "Duración (ms)",
    "Total events": "Total eventos", "Errors": "Errores", "Total tokens": "Total tokens",
    "Top commands": "Comandos principales", "Providers": "Proveedores",
    "Range": "Intervalo", "Showing": "Mostrando", "of": "de", "events": "eventos",
    "All repositories": "Todos los repositorios", "Repository": "Repositorio",
    "Timestamp": "Timestamp", "Unknown": "Desconocido",
    "Tokens (cache)": "Tokens (caché)", "Tokens (events)": "Tokens (eventos)",
    "Cache files": "Archivos caché", "Cache files found": "Archivos caché encontrados",
    "Press F5 to refresh": "Presione F5 para actualizar",
    "No message": "Sin mensaje", "No metrics data found in ~/.gitpr/cache/prompts/": "Sin datos de métricas en ~/.gitpr/cache/prompts/",
    "Scanning cache files...": "Analizando archivos caché...",
    "Total duration": "Duración total", "Total entries": "Total entradas",
    "Entries": "Entradas", "new entries": "nuevas entradas",
    "Previous Msg": "Msg Anterior", "Next Msg": "Msg Siguiente",
    "Auto-Patch Msg": "Msg Auto-Patch", "Export Msg": "Exportar Msg",
    "Available Prompt Templates": "Plantillas de Prompt Disponibles",
    "Blame Prompt": "Prompt Blame", "Issue Prompt": "Prompt Issue",
    "Linter Prompt": "Prompt Linter", "PR Description Prompt": "Prompt Descripción PR",
    "Review PR Prompt": "Prompt Revisión PR", "Explore Prompt": "Prompt Explorar",
    "Commit Message Prompt": "Prompt Mensaje Commit",
    "Language Override (--lang)": "Sobrescritura de idioma (--lang)",
    "F5 refresh": "Actualización F5",
}

# -----------------------------------------------------------
# STEP 1: Remove corrupted keys (extra keys with code fragments)
# -----------------------------------------------------------
for code, data in langs.items():
    to_delete = []
    for k in data:
        if k not in pt_br:
            to_delete.append(k)
    for k in to_delete:
        del data[k]
    print(f"{code}.json: {len(to_delete)} chaves corrompidas removidas")

# -----------------------------------------------------------
# STEP 2: Add missing keys from pt_br
# -----------------------------------------------------------
for code, data in langs.items():
    added = 0
    for k in pt_br:
        if k not in data:
            data[k] = k  # placeholder, will translate next
            added += 1
    print(f"{code}.json: {added} chaves adicionadas")

# -----------------------------------------------------------
# STEP 3: Translate untranslated keys using pt_br as reference for pt_pt
# -----------------------------------------------------------
for code, data in langs.items():
    translated = 0
    for k, v in list(data.items()):
        if k != v:
            continue  # already translated
        if re.match(r'^[a-z_]+\.py$|^[a-z_]+\.[a-z_]+\.py$', k):
            continue  # file names

        # For pt_pt: use pt_br translation as base (adapt for European Portuguese)
        if code == "pt_pt" and k in pt_br and pt_br[k] != k:
            data[k] = pt_br[k]
            translated += 1
        # For fr/es: use translation map
        elif code == "fr" and k in FR:
            data[k] = FR[k]
            translated += 1
        elif code == "es" and k in ES:
            data[k] = ES[k]
            translated += 1
        # For technical terms common to all languages
        elif k in ("Status", "Timestamp", "Tokens", "Tokens (cache)", "Auto-Patch"):
            data[k] = k  # universal term, keep as-is

    print(f"{code}.json: {translated} traducoes aplicadas")

# -----------------------------------------------------------
# STEP 4: Write files
# -----------------------------------------------------------
for code, data in langs.items():
    with open(LANG_FILES[code], "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# -----------------------------------------------------------
# STEP 5: Final report
# -----------------------------------------------------------
print()
print("=" * 50)
print("  FINAL")
print("=" * 50)
print(f"pt_br.json: {len(pt_br)} chaves (autoridade)")
for code, data in langs.items():
    missing = set(pt_br.keys()) - set(data.keys())
    extra = set(data.keys()) - set(pt_br.keys())
    untrans = sum(1 for k, v in data.items() if k == v and not re.match(r'^[a-z_]+\.py$|^[a-z_]+\.[a-z_]+\.py$', k))
    ok = "OK" if len(missing) == 0 and len(extra) == 0 else f"M:{len(missing)} E:{len(extra)}"
    print(f"{code}.json: {len(data)} chaves [{ok}] | nao traduzidas: {untrans}")
print()
print("Sincronizacao concluida.")
