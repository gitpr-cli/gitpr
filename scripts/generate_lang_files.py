#!/usr/bin/env python3
"""Generate fr.json and es.json language files based on pt_br.json structure."""
import json
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

with open("langs/pt_br.json", "r", encoding="utf-8", errors="replace") as f:
    pt_br = json.load(f)

# Core translations for the 89 audited keys from core.py/updater.py
# plus all other keys from pt_br.json
# French translations
fr_translations = {
    # === core.py / updater.py keys (audited scope) ===
    "⚠️ Warning: Git detected new untracked files:": "⚠️ Attention : Git a détecté de nouveaux fichiers non suivis :",
    "💡 Tip: Use 'git add <file>' to include them in the GitPR analysis.": "💡 Astuce : Utilisez 'git add <fichier>' pour les inclure dans l'analyse GitPR.",
    "❌ Error running Git: {error}": "❌ Erreur lors de l'exécution de Git : {error}",
    "❌ Git not found. Make sure it is installed and in the PATH.": "❌ Git introuvable. Assurez-vous qu'il est installé et dans le PATH.",
    "🧠 File {file_name} (Skill) found and loaded!": "🧠 Fichier {file_name} (Skill) trouvé et chargé !",
    "⚠️ Warning: Failed to read file {file_name} ({error})": "⚠️ Attention : Échec de la lecture du fichier {file_name} ({error})",
    "⚠️ No diff found. Make some changes before running the command.": "⚠️ Aucun diff trouvé. Effectuez des modifications avant d'exécuter la commande.",
    "⚡ Response retrieved from local cache.": "⚡ Réponse récupérée du cache local.",
    "❌ Error: API Key for provider '{provider}' not found.": "❌ Erreur : Clé API pour le fournisseur '{provider}' introuvable.",
    "🤖 GitPR is analyzing your code using {provider} ({model})...": "🤖 GitPR analyse votre code avec {provider} ({model})...",
    "📥 Downloading {hook_name}...": "📥 Téléchargement de {hook_name}...",
    "✅ Git Hooks successfully installed!": "✅ Git Hooks installés avec succès !",
    "🔍 Starting Code Archeology...": "🔍 Démarrage de l'Archéologie de Code...",
    "📍 File: {file_path} (Lines: {start_line} to {end_line})": "📍 Fichier : {file_path} (Lignes : {start_line} à {end_line})",
    "⚠️ No traceable commits found in these lines.": "⚠️ Aucun commit traçable trouvé dans ces lignes.",
    "📂 Selected file: {file_path}": "📂 Fichier sélectionné : {file_path}",
    "❌ The file '{file_path}' was not found.": "❌ Le fichier '{file_path}' est introuvable.",
    "✅ Success! File '{output_filename}' generated in current folder.": "✅ Succès ! Le fichier '{output_filename}' a été généré dans le dossier actuel.",
    "core.py": "core.py",
    "📚 Understand why: https://github.com/natanfiuza/gitpr/blob/main/docs/untracked-files.md\n": "📚 Comprendre pourquoi : https://github.com/natanfiuza/gitpr/blob/main/docs/untracked-files.md\n",
    "You are a Git expert. Generate concise commit messages.": "Vous êtes un expert Git. Générez des messages de commit concis.",
    "Generate ONLY a JSON object in the format {json_format} for this diff:\n": "Générez UNIQUEMENT un objet JSON au format {json_format} pour ce diff :\n",
    "You are a Senior Software Architect. Focus on pointing out improvements.": "Vous êtes un Architecte Logiciel Senior. Concentrez-vous sur les améliorations.",
    "Generate ONLY a JSON object in the format {json_format} with the analysis and improvements for the entire code of this file:\n": "Générez UNIQUEMENT un objet JSON au format {json_format} avec l'analyse et les améliorations pour tout le code de ce fichier :\n",
    "Generate ONLY a JSON object in the format {json_format} pointing out errors and improvements for this diff:\n": "Générez UNIQUEMENT un objet JSON au format {json_format} signalant les erreurs et améliorations pour ce diff :\n",
    "You are a Tech Lead writing clean and technical PR descriptions.": "Vous êtes un Tech Lead rédigeant des descriptions de PR propres et techniques.",
    "❌ Error: Could not determine model for provider '{provider}'.": "❌ Erreur : Impossible de déterminer le modèle pour le fournisseur '{provider}'.",
    "🤖 GitPR is analyzing your code using {provider} ({model})...\n": "🤖 GitPR analyse votre code avec {provider} ({model})...\n",
    "\n📥 Starting GitPR templates configuration...": "\n📥 Démarrage de la configuration des templates GitPR...",
    "⚠️ File {local_name} already exists in this directory. It will not be overwritten.": "⚠️ Le fichier {local_name} existe déjà. Il ne sera pas écrasé.",
    "Downloading {local_name}...": "Téléchargement de {local_name}...",
    "❌ Network error while downloading {local_name}: {error}": "❌ Erreur réseau lors du téléchargement de {local_name} : {error}",
    "❌ Failed to process {local_name}: {error}": "❌ Échec du traitement de {local_name} : {error}",
    "\n✅ Base templates successfully configured!": "\n✅ Templates de base configurés avec succès !",
    "📦 Skill file {filename} moved to .gitpr/skill/": "📦 Fichier skill {filename} déplacé vers .gitpr/skill/",
    "⚠️ Warning: Could not move {filename} to .gitpr/skill/ ({error})": "⚠️ Attention : Impossible de déplacer {filename} vers .gitpr/skill/ ({error})",
    "You can now open the generated files in '.gitpr/skill/' and customize the tool's behavior for your project:\n": "Vous pouvez maintenant ouvrir les fichiers générés dans '.gitpr/skill/' et personnaliser le comportement de l'outil pour votre projet :\n",
    "  1. Architecture rules for AI in '.gitpr/skill/.gitpr.pr.md' and '.gitpr/skill/.gitpr.review.md'\n": "  1. Règles d'architecture pour l'IA dans '.gitpr/skill/.gitpr.pr.md' et '.gitpr/skill/.gitpr.review.md'\n",
    "  2. Local regex rules in '.gitpr/skill/.gitpr.linter.yml'\n": "  2. Règles regex locales dans '.gitpr/skill/.gitpr.linter.yml'\n",
    "\nNo new files were downloaded.": "\nAucun nouveau fichier n'a été téléchargé.",
    "⚠️ Warning: Remote main branch not detected. Assuming 'main' as default fallback.": "⚠️ Attention : Branche principale distante non détectée. Utilisation de 'main' par défaut.",
    "🔄 Synchronizing with remote repository (git fetch)...": "🔄 Synchronisation avec le dépôt distant (git fetch)...",
    "❌ Error calculating diff: {error}": "❌ Erreur lors du calcul du diff : {error}",
    "❌ Error: .git folder not found. Run at the project root.": "❌ Erreur : Dossier .git introuvable. Exécutez à la racine du projet.",
    "⚠️ Failed to install {hook_name}: {error}": "⚠️ Échec de l'installation de {hook_name} : {error}",
    "🔄 Compiling history of repository '{repo_name}', branch '{branch}' against '{base_branch}'...": "🔄 Compilation de l'historique du dépôt '{repo_name}', branche '{branch}' contre '{base_branch}'...",
    "Repository: {repo_name}\nBranch History Summary: {branch}\n\n": "Dépôt : {repo_name}\nRésumé de l'historique de la branche : {branch}\n\n",
    "=== REGISTERED COMMITS ===\n": "=== COMMITS ENREGISTRÉS ===\n",
    "No exclusive commits found in this branch.\n\n": "Aucun commit exclusif trouvé dans cette branche.\n\n",
    "⚠️ Warning: Could not get Git Log: {error}": "⚠️ Attention : Impossible d'obtenir le Git Log : {error}",
    "=== AI PR HISTORY ===\nNo previous AI-generated PR found in cache for this branch.\n": "=== HISTORIQUE DES PRs IA ===\nAucune PR générée par IA trouvée dans le cache pour cette branche.\n",
    "main.py": "main.py",
    # === New hooks versioning keys (2026-08-05) ===
    "🔍 Checking hook scripts version...": "🔍 Vérification de la version des scripts de hooks...",
    "   Current: {current} (from .env)": "   Actuelle : {current} (du .env)",
    "   Latest: {latest} (from code)": "   Dernière : {latest} (du code)",
    "📦 Updating scripts to {version}...": "📦 Mise à jour des scripts vers {version}...",
    "   Detected language: {lang}": "   Langue détectée : {lang}",
    "⚠️ Failed to install {hook_name}: HTTP {code}": "⚠️ Échec de l'installation de {hook_name} : HTTP {code}",
    "✅ Scripts synced successfully!": "✅ Scripts synchronisés avec succès !",
    "none": "aucune",
    # === updater.py keys ===
    "[notice] A new release of gitpr is available: {current_version} -> {latest_version}": "[notice] Une nouvelle version de gitpr est disponible : {current_version} -> {latest_version}",
    "[notice] To update, run: gitpr --update": "[notice] Pour mettre à jour, exécutez : gitpr --update",
    "[notice] To update, run: pip install --upgrade gitpr-cli": "[notice] Pour mettre à jour, exécutez : pip install --upgrade gitpr-cli",
    "💡 Since you installed via PIP, update by running: pip install --upgrade gitpr-cli": "💡 Puisque vous avez installé via PIP, mettez à jour avec : pip install --upgrade gitpr-cli",
    "❌ Could not check for updates at this moment.": "❌ Impossible de vérifier les mises à jour pour le moment.",
    "\n🚀 New GitPR version found (v{latest_version})!": "\n🚀 Nouvelle version de GitPR trouvée (v{latest_version}) !",
    "Downloading update in background...": "Téléchargement de la mise à jour en arrière-plan...",
    "✅ You are already using the latest version of GitPR.": "✅ Vous utilisez déjà la dernière version de GitPR.",
    "✅ Update successfully completed! You will use the new version on the next run.\n": "✅ Mise à jour terminée avec succès ! Vous utiliserez la nouvelle version au prochain lancement.\n",
    "❌ Failed to apply update: {error}": "❌ Échec de l'application de la mise à jour : {error}",
}

# For all other keys from pt_br.json not in our audit scope,
# keep the key as both key and value (English fallback)
for key in pt_br:
    if key not in fr_translations:
        fr_translations[key] = key  # English fallback

# Write fr.json
with open("langs/fr.json", "w", encoding="utf-8") as f:
    json.dump(fr_translations, f, ensure_ascii=False, indent=2)
print(f"fr.json: {len(fr_translations)} keys written")

# --- Spanish translations ---
es_translations = {
    # === core.py / updater.py keys (audited scope) ===
    "⚠️ Warning: Git detected new untracked files:": "⚠️ Aviso: Git detectó nuevos archivos no rastreados:",
    "💡 Tip: Use 'git add <file>' to include them in the GitPR analysis.": "💡 Consejo: Use 'git add <archivo>' para incluirlos en el análisis de GitPR.",
    "❌ Error running Git: {error}": "❌ Error al ejecutar Git: {error}",
    "❌ Git not found. Make sure it is installed and in the PATH.": "❌ Git no encontrado. Asegúrese de que esté instalado y en el PATH.",
    "🧠 File {file_name} (Skill) found and loaded!": "🧠 ¡Archivo {file_name} (Skill) encontrado y cargado!",
    "⚠️ Warning: Failed to read file {file_name} ({error})": "⚠️ Aviso: Error al leer el archivo {file_name} ({error})",
    "⚠️ No diff found. Make some changes before running the command.": "⚠️ No se encontró diff. Realice algunos cambios antes de ejecutar el comando.",
    "⚡ Response retrieved from local cache.": "⚡ Respuesta recuperada de la caché local.",
    "❌ Error: API Key for provider '{provider}' not found.": "❌ Error: Clave API para el proveedor '{provider}' no encontrada.",
    "🤖 GitPR is analyzing your code using {provider} ({model})...": "🤖 GitPR está analizando su código usando {provider} ({model})...",
    "📥 Downloading {hook_name}...": "📥 Descargando {hook_name}...",
    "✅ Git Hooks successfully installed!": "✅ ¡Git Hooks instalados con éxito!",
    "🔍 Starting Code Archeology...": "🔍 Iniciando Arqueología de Código...",
    "📍 File: {file_path} (Lines: {start_line} to {end_line})": "📍 Archivo: {file_path} (Líneas: {start_line} a {end_line})",
    "⚠️ No traceable commits found in these lines.": "⚠️ No se encontraron commits rastreables en estas líneas.",
    "📂 Selected file: {file_path}": "📂 Archivo seleccionado: {file_path}",
    "❌ The file '{file_path}' was not found.": "❌ El archivo '{file_path}' no fue encontrado.",
    "✅ Success! File '{output_filename}' generated in current folder.": "✅ ¡Éxito! El archivo '{output_filename}' fue generado en la carpeta actual.",
    "core.py": "core.py",
    "📚 Understand why: https://github.com/natanfiuza/gitpr/blob/main/docs/untracked-files.md\n": "📚 Entienda por qué: https://github.com/natanfiuza/gitpr/blob/main/docs/untracked-files.md\n",
    "You are a Git expert. Generate concise commit messages.": "Eres un experto en Git. Genera mensajes de commit concisos.",
    "Generate ONLY a JSON object in the format {json_format} for this diff:\n": "Genera SOLO un objeto JSON en el formato {json_format} para este diff:\n",
    "You are a Senior Software Architect. Focus on pointing out improvements.": "Eres un Arquitecto de Software Senior. Enfócate en señalar mejoras.",
    "Generate ONLY a JSON object in the format {json_format} with the analysis and improvements for the entire code of this file:\n": "Genera SOLO un objeto JSON en el formato {json_format} con el análisis y mejoras para todo el código de este archivo:\n",
    "Generate ONLY a JSON object in the format {json_format} pointing out errors and improvements for this diff:\n": "Genera SOLO un objeto JSON en el formato {json_format} señalando errores y mejoras para este diff:\n",
    "You are a Tech Lead writing clean and technical PR descriptions.": "Eres un Tech Lead redactando descripciones de PR limpias y técnicas.",
    "❌ Error: Could not determine model for provider '{provider}'.": "❌ Error: No se pudo determinar el modelo para el proveedor '{provider}'.",
    "🤖 GitPR is analyzing your code using {provider} ({model})...\n": "🤖 GitPR está analizando su código usando {provider} ({model})...\n",
    "\n📥 Starting GitPR templates configuration...": "\n📥 Iniciando la configuración de plantillas de GitPR...",
    "⚠️ File {local_name} already exists in this directory. It will not be overwritten.": "⚠️ El archivo {local_name} ya existe. No se sobrescribirá.",
    "Downloading {local_name}...": "Descargando {local_name}...",
    "❌ Network error while downloading {local_name}: {error}": "❌ Error de red al descargar {local_name}: {error}",
    "❌ Failed to process {local_name}: {error}": "❌ Error al procesar {local_name}: {error}",
    "\n✅ Base templates successfully configured!": "\n✅ ¡Plantillas base configuradas con éxito!",
    "📦 Skill file {filename} moved to .gitpr/skill/": "📦 Archivo skill {filename} movido a .gitpr/skill/",
    "⚠️ Warning: Could not move {filename} to .gitpr/skill/ ({error})": "⚠️ Aviso: No se pudo mover {filename} a .gitpr/skill/ ({error})",
    "You can now open the generated files in '.gitpr/skill/' and customize the tool's behavior for your project:\n": "Ahora puede abrir los archivos generados en '.gitpr/skill/' y personalizar el comportamiento de la herramienta para su proyecto:\n",
    "  1. Architecture rules for AI in '.gitpr/skill/.gitpr.pr.md' and '.gitpr/skill/.gitpr.review.md'\n": "  1. Reglas de arquitectura para IA en '.gitpr/skill/.gitpr.pr.md' y '.gitpr/skill/.gitpr.review.md'\n",
    "  2. Local regex rules in '.gitpr/skill/.gitpr.linter.yml'\n": "  2. Reglas regex locales en '.gitpr/skill/.gitpr.linter.yml'\n",
    "\nNo new files were downloaded.": "\nNo se descargaron archivos nuevos.",
    "⚠️ Warning: Remote main branch not detected. Assuming 'main' as default fallback.": "⚠️ Aviso: Rama principal remota no detectada. Usando 'main' como valor predeterminado.",
    "🔄 Synchronizing with remote repository (git fetch)...": "🔄 Sincronizando con el repositorio remoto (git fetch)...",
    "❌ Error calculating diff: {error}": "❌ Error al calcular el diff: {error}",
    "❌ Error: .git folder not found. Run at the project root.": "❌ Error: Carpeta .git no encontrada. Ejecute en la raíz del proyecto.",
    "⚠️ Failed to install {hook_name}: {error}": "⚠️ Error al instalar {hook_name}: {error}",
    "🔄 Compiling history of repository '{repo_name}', branch '{branch}' against '{base_branch}'...": "🔄 Compilando historial del repositorio '{repo_name}', rama '{branch}' contra '{base_branch}'...",
    "Repository: {repo_name}\nBranch History Summary: {branch}\n\n": "Repositorio: {repo_name}\nResumen del Historial de la Rama: {branch}\n\n",
    "=== REGISTERED COMMITS ===\n": "=== COMMITS REGISTRADOS ===\n",
    "No exclusive commits found in this branch.\n\n": "No se encontraron commits exclusivos en esta rama.\n\n",
    "⚠️ Warning: Could not get Git Log: {error}": "⚠️ Aviso: No se pudo obtener el Git Log: {error}",
    "=== AI PR HISTORY ===\nNo previous AI-generated PR found in cache for this branch.\n": "=== HISTORIAL DE PRs DE IA ===\nNo se encontró PR generado por IA en caché para esta rama.\n",
    "main.py": "main.py",
    # === New hooks versioning keys (2026-08-05) ===
    "🔍 Checking hook scripts version...": "🔍 Verificando versión de scripts de hooks...",
    "   Current: {current} (from .env)": "   Actual: {current} (de .env)",
    "   Latest: {latest} (from code)": "   Última: {latest} (del código)",
    "📦 Updating scripts to {version}...": "📦 Actualizando scripts a {version}...",
    "   Detected language: {lang}": "   Idioma detectado: {lang}",
    "⚠️ Failed to install {hook_name}: HTTP {code}": "⚠️ Error al instalar {hook_name}: HTTP {code}",
    "✅ Scripts synced successfully!": "✅ ¡Scripts sincronizados con éxito!",
    "none": "ninguna",
    # === updater.py keys ===
    "[notice] A new release of gitpr is available: {current_version} -> {latest_version}": "[notice] Una nueva versión de gitpr está disponible: {current_version} -> {latest_version}",
    "[notice] To update, run: gitpr --update": "[notice] Para actualizar, ejecute: gitpr --update",
    "[notice] To update, run: pip install --upgrade gitpr-cli": "[notice] Para actualizar, ejecute: pip install --upgrade gitpr-cli",
    "💡 Since you installed via PIP, update by running: pip install --upgrade gitpr-cli": "💡 Ya que instaló via PIP, actualice ejecutando: pip install --upgrade gitpr-cli",
    "❌ Could not check for updates at this moment.": "❌ No se pudieron verificar actualizaciones en este momento.",
    "\n🚀 New GitPR version found (v{latest_version})!": "\n🚀 ¡Nueva versión de GitPR encontrada (v{latest_version})!",
    "Downloading update in background...": "Descargando actualización en segundo plano...",
    "✅ You are already using the latest version of GitPR.": "✅ Ya está usando la última versión de GitPR.",
    "✅ Update successfully completed! You will use the new version on the next run.\n": "✅ ¡Actualización completada con éxito! Usará la nueva versión en la próxima ejecución.\n",
    "❌ Failed to apply update: {error}": "❌ Error al aplicar la actualización: {error}",
}

# For all other keys
for key in pt_br:
    if key not in es_translations:
        es_translations[key] = key  # English fallback

# Write es.json
with open("langs/es.json", "w", encoding="utf-8") as f:
    json.dump(es_translations, f, ensure_ascii=False, indent=2)
print(f"es.json: {len(es_translations)} keys written")
