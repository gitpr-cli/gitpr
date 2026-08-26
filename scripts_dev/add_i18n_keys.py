"""Add the 91 missing i18n keys to all language dictionaries (langs/*.json).

83 UI strings get real translations; 8 AI-prompt keys stay English by design
(prompts are never translated — they feed the AI models directly).
Run once; safe to re-run (skips keys already present).
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LANGS = ROOT / "langs"

# AI prompts — must stay in English by design (identity entries, same in all languages)
PROMPTS_EN = [
    "Analyze the diff of commit {commit_hash} and return the requested JSON.\n\n",
    "Generate ONLY a JSON object in the format {json_format} containing a technical summary of what was changed in this part ({idx}) of the diff:\n",
    "Generate the requested JSON object following the system instructions to {target_action}\n\n",
    "Repository: {repo_name}\nBranch History Summary: {branch}\n\n",
    "You are a Senior Software Engineer acting as a Pair Programmer. Analyze the code provided and answer the user's questions clearly, objectively, and technically. Use Markdown to format code blocks. The current git diff is:\n\n{diff}",
    "[{date}] Commit {hash} by {author}:",
    "Action: {status}",
    "AI Reason: {reason}",
]

# UI strings — translated per language: pt_br, es, fr, pt_pt
UI_TRANSLATIONS = {
    "\n**Summary:** {summary}\n": {
        "pt_br": "\n**Resumo:** {summary}\n",
        "es": "\n**Resumen:** {summary}\n",
        "fr": "\n**Résumé :** {summary}\n",
        "pt_pt": "\n**Resumo:** {summary}\n",
    },
    "\n[{date}] {icon} {status}: By {author} (Commit: {hash})": {
        "pt_br": "\n[{date}] {icon} {status}: Por {author} (Commit: {hash})",
        "es": "\n[{date}] {icon} {status}: Por {author} (Commit: {hash})",
        "fr": "\n[{date}] {icon} {status} : Par {author} (Commit : {hash})",
        "pt_pt": "\n[{date}] {icon} {status}: Por {author} (Commit: {hash})",
    },
    "\n⚠️ The Linter generated {count} best practice warning(s):": {
        "pt_br": "\n⚠️ O Linter gerou {count} aviso(s) de boas práticas:",
        "es": "\n⚠️ El Linter generó {count} aviso(s) de buenas prácticas:",
        "fr": "\n⚠️ Le Linter a généré {count} avertissement(s) de bonnes pratiques :",
        "pt_pt": "\n⚠️ O Linter gerou {count} aviso(s) de boas práticas:",
    },
    "\n✅ Code Review successfully generated: '{output_filename}'": {
        "pt_br": "\n✅ Revisão de Código gerada com sucesso: '{output_filename}'",
        "es": "\n✅ Revisión de Código generada con éxito: '{output_filename}'",
        "fr": "\n✅ Révision de Code générée avec succès : '{output_filename}'",
        "pt_pt": "\n✅ Revisão de Código gerada com sucesso: '{output_filename}'",
    },
    "\n✅ Success! The file '{output_filename}' was generated in the current folder.": {
        "pt_br": "\n✅ Sucesso! O arquivo '{output_filename}' foi gerado na pasta atual.",
        "es": "\n✅ ¡Éxito! El archivo '{output_filename}' fue generado en la carpeta actual.",
        "fr": "\n✅ Succès ! Le fichier '{output_filename}' a été généré dans le dossier actuel.",
        "pt_pt": "\n✅ Sucesso! O ficheiro '{output_filename}' foi gerado na pasta atual.",
    },
    "\n❌ Error: The file '{input}' was not found.": {
        "pt_br": "\n❌ Erro: O arquivo '{input}' não foi encontrado.",
        "es": "\n❌ Error: El archivo '{input}' no fue encontrado.",
        "fr": "\n❌ Erreur : Le fichier '{input}' est introuvable.",
        "pt_pt": "\n❌ Erro: O ficheiro '{input}' não foi encontrado.",
    },
    "\n💬 Custom Prompts ({count}):": {
        "pt_br": "\n💬 Prompts Personalizados ({count}):",
        "es": "\n💬 Prompts Personalizados ({count}):",
        "fr": "\n💬 Prompts Personnalisés ({count}) :",
        "pt_pt": "\n💬 Prompts Personalizados ({count}):",
    },
    "\n📜 Consolidated Rule History (Lines {start_line}-{end_line}):": {
        "pt_br": "\n📜 Histórico Consolidado da Regra (Linhas {start_line}-{end_line}):",
        "es": "\n📜 Historial Consolidado de la Regla (Líneas {start_line}-{end_line}):",
        "fr": "\n📜 Historique Consolidé de la Règle (Lignes {start_line}-{end_line}) :",
        "pt_pt": "\n📜 Histórico Consolidado da Regra (Linhas {start_line}-{end_line}):",
    },
    "\n🔍 Linter Packs ({count}):": {
        "pt_br": "\n🔍 Pacotes de Linter ({count}):",
        "es": "\n🔍 Paquetes de Linter ({count}):",
        "fr": "\n🔍 Packs Linter ({count}) :",
        "pt_pt": "\n🔍 Pacotes de Linter ({count}):",
    },
    "\n🚀 New GitPR version found (v{latest_version})!": {
        "pt_br": "\n🚀 Nova versão do GitPR encontrada (v{latest_version})!",
        "es": "\n🚀 ¡Nueva versión de GitPR encontrada (v{latest_version})!",
        "fr": "\n🚀 Nouvelle version de GitPR trouvée (v{latest_version}) !",
        "pt_pt": "\n🚀 Nova versão do GitPR encontrada (v{latest_version})!",
    },
    "\n🚨 Validation failed! Found {count} critical error(s):": {
        "pt_br": "\n🚨 Validação falhou! {count} erro(s) crítico(s) encontrado(s):",
        "es": "\n🚨 ¡Validación fallida! {count} error(es) crítico(s) encontrado(s):",
        "fr": "\n🚨 Échec de la validation ! {count} erreur(s) critique(s) trouvée(s) :",
        "pt_pt": "\n🚨 Validação falhou! {count} erro(s) crítico(s) encontrado(s):",
    },
    "\r⚠️ API instability ({provider}). Retrying ({attempt}/{max_retries})...": {
        "pt_br": "\r⚠️ Instabilidade na API ({provider}). Tentando novamente ({attempt}/{max_retries})...",
        "es": "\r⚠️ Inestabilidad en la API ({provider}). Reintentando ({attempt}/{max_retries})...",
        "fr": "\r⚠️ Instabilité de l'API ({provider}). Nouvelle tentative ({attempt}/{max_retries})...",
        "pt_pt": "\r⚠️ Instabilidade na API ({provider}). A tentar novamente ({attempt}/{max_retries})...",
    },
    "\r❌ Critical error contacting {provider} API after {max_retries} attempts: {error}": {
        "pt_br": "\r❌ Erro crítico ao contactar a API do {provider} após {max_retries} tentativas: {error}",
        "es": "\r❌ Error crítico al contactar la API de {provider} tras {max_retries} intentos: {error}",
        "fr": "\r❌ Erreur critique en contactant l'API {provider} après {max_retries} tentatives : {error}",
        "pt_pt": "\r❌ Erro crítico ao contactar a API do {provider} após {max_retries} tentativas: {error}",
    },
    "\r❌ Critical error in Chat API ({provider}): {error}": {
        "pt_br": "\r❌ Erro crítico na API de Chat ({provider}): {error}",
        "es": "\r❌ Error crítico en la API de Chat ({provider}): {error}",
        "fr": "\r❌ Erreur critique dans l'API Chat ({provider}) : {error}",
        "pt_pt": "\r❌ Erro crítico na API de Chat ({provider}): {error}",
    },
    "   └─ AI Analysis: {reason}": {
        "pt_br": "   └─ Análise da IA: {reason}",
        "es": "   └─ Análisis de la IA: {reason}",
        "fr": "   └─ Analyse de l'IA : {reason}",
        "pt_pt": "   └─ Análise da IA: {reason}",
    },
    '   └─ Message: "{message}"': {
        "pt_br": '   └─ Mensagem: "{message}"',
        "es": '   └─ Mensaje: "{message}"',
        "fr": '   └─ Message : "{message}"',
        "pt_pt": '   └─ Mensagem: "{message}"',
    },
    "  🤖 Consulting AI ({api_model}) about commit {commit_hash}...": {
        "pt_br": "  🤖 Consultando IA ({api_model}) sobre o commit {commit_hash}...",
        "es": "  🤖 Consultando a la IA ({api_model}) sobre el commit {commit_hash}...",
        "fr": "  🤖 Consultation de l'IA ({api_model}) à propos du commit {commit_hash}...",
        "pt_pt": "  🤖 A consultar a IA ({api_model}) sobre o commit {commit_hash}...",
    },
    "  🤖 Consulting AI ({api_model}) for the Executive Summary...": {
        "pt_br": "  🤖 Consultando IA ({api_model}) para o Resumo Executivo...",
        "es": "  🤖 Consultando a la IA ({api_model}) para el Resumen Ejecutivo...",
        "fr": "  🤖 Consultation de l'IA ({api_model}) pour le Résumé Exécutif...",
        "pt_pt": "  🤖 A consultar a IA ({api_model}) para o Resumo Executivo...",
    },
    "**File:** `{file_path}` (Lines {start_line}-{end_line})\n\n": {
        "pt_br": "**Arquivo:** `{file_path}` (Linhas {start_line}-{end_line})\n\n",
        "es": "**Archivo:** `{file_path}` (Líneas {start_line}-{end_line})\n\n",
        "fr": "**Fichier :** `{file_path}` (Lignes {start_line}-{end_line})\n\n",
        "pt_pt": "**Ficheiro:** `{file_path}` (Linhas {start_line}-{end_line})\n\n",
    },
    ">> Selected file: {file_path}": {
        "pt_br": ">> Arquivo selecionado: {file_path}",
        "es": ">> Archivo seleccionado: {file_path}",
        "fr": ">> Fichier sélectionné : {file_path}",
        "pt_pt": ">> Ficheiro selecionado: {file_path}",
    },
    "An open Pull Request already exists for this branch.\n\nPush and update the existing PR?": {
        "pt_br": "Já existe um Pull Request aberto para esta branch.\n\nFazer push e atualizar o PR existente?",
        "es": "Ya existe un Pull Request abierto para esta rama.\n\n¿Hacer push y actualizar el PR existente?",
        "fr": "Un Pull Request ouvert existe déjà pour cette branche.\n\nPousser et mettre à jour le PR existant ?",
        "pt_pt": "Já existe um Pull Request aberto para esta branch.\n\nFazer push e atualizar o PR existente?",
    },
    "Failed to connect to GitHub: {error}": {
        "pt_br": "Falha ao conectar ao GitHub: {error}",
        "es": "Error al conectar con GitHub: {error}",
        "fr": "Échec de la connexion à GitHub : {error}",
        "pt_pt": "Falha ao ligar ao GitHub: {error}",
    },
    "Failed to validate token: {error}": {
        "pt_br": "Falha ao validar o token: {error}",
        "es": "Error al validar el token: {error}",
        "fr": "Échec de la validation du jeton : {error}",
        "pt_pt": "Falha ao validar o token: {error}",
    },
    "File not found: {file_path}": {
        "pt_br": "Arquivo não encontrado: {file_path}",
        "es": "Archivo no encontrado: {file_path}",
        "fr": "Fichier introuvable : {file_path}",
        "pt_pt": "Ficheiro não encontrado: {file_path}",
    },
    "Full code review of all changes in the current branch against origin/main. Runs the full review tool and linter, then composes a comprehensive report.": {
        "pt_br": "Revisão de código completa de todas as alterações da branch atual contra a origin/main. Executa a ferramenta de full review e o linter e então compõe um relatório abrangente.",
        "es": "Revisión de código completa de todos los cambios de la rama actual contra origin/main. Ejecuta la herramienta de revisión completa y el linter, y luego compone un informe completo.",
        "fr": "Révision de code complète de tous les changements de la branche actuelle par rapport à origin/main. Exécute l'outil de révision complète et le linter, puis compose un rapport complet.",
        "pt_pt": "Revisão de código completa de todas as alterações da branch atual contra a origin/main. Executa a ferramenta de full review e o linter e depois compõe um relatório abrangente.",
    },
    "Generate a Conventional Commits commit message from the current git diff using AI. Returns a message like 'feat: add user authentication'.": {
        "pt_br": "Gera uma mensagem de commit no padrão Conventional Commits a partir do git diff atual usando IA. Retorna uma mensagem como 'feat: add user authentication'.",
        "es": "Genera un mensaje de commit en el estándar Conventional Commits a partir del git diff actual usando IA. Devuelve un mensaje como 'feat: add user authentication'.",
        "fr": "Génère un message de commit au format Conventional Commits à partir du git diff actuel en utilisant l'IA. Renvoie un message comme 'feat: add user authentication'.",
        "pt_pt": "Gera uma mensagem de commit no padrão Conventional Commits a partir do git diff atual usando IA. Devolve uma mensagem como 'feat: add user authentication'.",
    },
    "Generate a complete Pull Request description (title + body) from all changes in the current branch.": {
        "pt_br": "Gera uma descrição completa de Pull Request (título + corpo) a partir de todas as alterações da branch atual.",
        "es": "Genera una descripción completa de Pull Request (título + cuerpo) a partir de todos los cambios de la rama actual.",
        "fr": "Génère une description complète de Pull Request (titre + corps) à partir de tous les changements de la branche actuelle.",
        "pt_pt": "Gera uma descrição completa de Pull Request (título + corpo) a partir de todas as alterações da branch atual.",
    },
    "Generate a complete Pull Request description (title + body) from the full diff against origin/main. Uses AI to create a structured, professional PR document.": {
        "pt_br": "Gera uma descrição completa de Pull Request (título + corpo) a partir do diff completo contra a origin/main. Usa IA para criar um documento de PR estruturado e profissional.",
        "es": "Genera una descripción completa de Pull Request (título + cuerpo) a partir del diff completo contra origin/main. Usa IA para crear un documento de PR estructurado y profesional.",
        "fr": "Génère une description complète de Pull Request (titre + corps) à partir du diff complet par rapport à origin/main. Utilise l'IA pour créer un document de PR structuré et professionnel.",
        "pt_pt": "Gera uma descrição completa de Pull Request (título + corpo) a partir do diff completo contra a origin/main. Usa IA para criar um documento de PR estruturado e profissional.",
    },
    "Generate a structured Issue (What / Why / Where / How) from code context using AI. Supports three modes: diff (current changes), history (branch history), or blame (file region).": {
        "pt_br": "Gera uma Issue estruturada (O Que / Por Que / Onde / Como) a partir do contexto do código usando IA. Suporta três modos: diff (alterações atuais), history (histórico da branch) ou blame (região do arquivo).",
        "es": "Genera una Issue estructurada (Qué / Por Qué / Dónde / Cómo) a partir del contexto del código usando IA. Admite tres modos: diff (cambios actuales), history (historial de la rama) o blame (región del archivo).",
        "fr": "Génère une Issue structurée (Quoi / Pourquoi / Où / Comment) à partir du contexte du code en utilisant l'IA. Prend en charge trois modes : diff (changements actuels), history (historique de la branche) ou blame (région du fichier).",
        "pt_pt": "Gera uma Issue estruturada (O Que / Por Que / Onde / Como) a partir do contexto do código usando IA. Suporta três modos: diff (alterações atuais), history (histórico da branch) ou blame (região do ficheiro).",
    },
    "Generate a structured issue (What / Why / Where / How) from the current uncommitted changes.": {
        "pt_br": "Gera uma issue estruturada (O Que / Por Que / Onde / Como) a partir das alterações não commitadas atuais.",
        "es": "Genera una issue estructurada (Qué / Por Qué / Dónde / Cómo) a partir de los cambios sin commitear actuales.",
        "fr": "Génère une issue structurée (Quoi / Pourquoi / Où / Comment) à partir des changements non commités actuels.",
        "pt_pt": "Gera uma issue estruturada (O Que / Por Que / Onde / Como) a partir das alterações não commitadas atuais.",
    },
    "Get current branch info, repository name, and list available skill templates for the project.": {
        "pt_br": "Obtém a branch atual, o nome do repositório e lista os templates de skill disponíveis para o projeto.",
        "es": "Obtiene la rama actual, el nombre del repositorio y lista las plantillas de skill disponibles para el proyecto.",
        "fr": "Obtient la branche actuelle, le nom du dépôt et liste les templates de skill disponibles pour le projet.",
        "pt_pt": "Obtém a branch atual, o nome do repositório e lista os templates de skill disponíveis para o projeto.",
    },
    "Get only the unstaged git diff (git diff without HEAD — compares the index against the working tree). Excludes staged changes. Untracked files are not shown; use list_unstaged_files for them.": {
        "pt_br": "Obtém apenas o git diff não staged (git diff sem HEAD — compara o index com a árvore de trabalho). Exclui alterações staged. Arquivos untracked não são exibidos; use list_unstaged_files para eles.",
        "es": "Obtiene solo el git diff sin staged (git diff sin HEAD — compara el índice con el árbol de trabajo). Excluye cambios staged. Los archivos untracked no se muestran; use list_unstaged_files para ellos.",
        "fr": "Obtient uniquement le git diff non stagé (git diff sans HEAD — compare l'index avec l'arbre de travail). Exclut les changements stagés. Les fichiers untracked ne sont pas affichés ; utilisez list_unstaged_files pour eux.",
        "pt_pt": "Obtém apenas o git diff não staged (git diff sem HEAD — compara o index com a árvore de trabalho). Exclui alterações staged. Ficheiros untracked não são exibidos; use list_unstaged_files para eles.",
    },
    "Get the current uncommitted git diff (git diff HEAD — includes both staged and unstaged changes). ": {
        "pt_br": "Obtém o git diff atual não commitado (git diff HEAD — inclui alterações staged e não staged). ",
        "es": "Obtiene el git diff actual sin commitear (git diff HEAD — incluye cambios staged y no staged). ",
        "fr": "Obtient le git diff actuel non commité (git diff HEAD — inclut les changements stagés et non stagés). ",
        "pt_pt": "Obtém o git diff atual não commitado (git diff HEAD — inclui alterações staged e não staged). ",
    },
    "Get the full diff of the current branch against the remote base branch (origin/main or origin/master). Runs git fetch first.": {
        "pt_br": "Obtém o diff completo da branch atual contra a branch base remota (origin/main ou origin/master). Executa git fetch primeiro.",
        "es": "Obtiene el diff completo de la rama actual contra la rama base remota (origin/main u origin/master). Ejecuta git fetch primero.",
        "fr": "Obtient le diff complet de la branche actuelle par rapport à la branche de base distante (origin/main ou origin/master). Exécute git fetch en premier.",
        "pt_pt": "Obtém o diff completo da branch atual contra a branch base remota (origin/main ou origin/master). Executa git fetch primeiro.",
    },
    "GitPR — Intelligent PR Automation and AI Code Review. Generate commit messages, review code, run linters, trace code origins, and create issues — all from your IDE.": {
        "pt_br": "GitPR — Automação Inteligente de PRs e Revisão de Código com IA. Gere mensagens de commit, revise código, execute linters, rastreie origens de código e crie issues — tudo a partir do seu IDE.",
        "es": "GitPR — Automatización Inteligente de PRs y Revisión de Código con IA. Genere mensajes de commit, revise código, ejecute linters, rastree orígenes de código y cree issues — todo desde su IDE.",
        "fr": "GitPR — Automatisation Intelligente des PR et Révision de Code par IA. Générez des messages de commit, révisez du code, exécutez des linters, tracez les origines du code et créez des issues — le tout depuis votre IDE.",
        "pt_pt": "GitPR — Automação Inteligente de PRs e Revisão de Código com IA. Gere mensagens de commit, reveja código, execute linters, rastreie origens de código e crie issues — tudo a partir do seu IDE.",
    },
    "Interactive prompt is unavailable in MCP mode. Configure your API keys in ~/.gitpr/.env before using MCP tools.": {
        "pt_br": "O prompt interativo não está disponível no modo MCP. Configure suas chaves de API em ~/.gitpr/.env antes de usar as ferramentas MCP.",
        "es": "El prompt interactivo no está disponible en modo MCP. Configure sus claves de API en ~/.gitpr/.env antes de usar las herramientas MCP.",
        "fr": "L'invite interactive n'est pas disponible en mode MCP. Configurez vos clés API dans ~/.gitpr/.env avant d'utiliser les outils MCP.",
        "pt_pt": "O prompt interativo não está disponível no modo MCP. Configure as suas chaves de API em ~/.gitpr/.env antes de usar as ferramentas MCP.",
    },
    "Investigate the history of a specific file region using git blame + AI to trace where business rules came from.": {
        "pt_br": "Investiga o histórico de uma região específica de arquivo usando git blame + IA para rastrear de onde vieram as regras de negócio.",
        "es": "Investiga el historial de una región específica de archivo usando git blame + IA para rastrear de dónde vinieron las reglas de negocio.",
        "fr": "Enquête sur l'historique d'une région de fichier spécifique en utilisant git blame + IA pour retracer l'origine des règles métier.",
        "pt_pt": "Investiga o histórico de uma região específica de ficheiro usando git blame + IA para rastrear de onde vieram as regras de negócio.",
    },
    "List uncommitted file changes categorized as new (untracked), modified (unstaged modifications) or deleted. Returns structured JSON.": {
        "pt_br": "Lista alterações de arquivos não commitadas categorizadas como novas (untracked), modificadas (modificações unstaged) ou excluídas. Retorna JSON estruturado.",
        "es": "Lista cambios de archivos sin commitear categorizados como nuevos (untracked), modificados (modificaciones sin staged) o eliminados. Devuelve JSON estructurado.",
        "fr": "Liste les changements de fichiers non commités catégorisés comme nouveaux (untracked), modifiés (modifications non stagées) ou supprimés. Renvoie un JSON structuré.",
        "pt_pt": "Lista alterações de ficheiros não commitadas categorizadas como novas (untracked), modificadas (modificações unstaged) ou excluídas. Devolve JSON estruturado.",
    },
    "Merge failed with status {status}.\n\n👉 {pr_url}\n\nError: {error}": {
        "pt_br": "Falha no merge com status {status}.\n\n👉 {pr_url}\n\nErro: {error}",
        "es": "El merge falló con estado {status}.\n\n👉 {pr_url}\n\nError: {error}",
        "fr": "Échec du merge avec le statut {status}.\n\n👉 {pr_url}\n\nErreur : {error}",
        "pt_pt": "Falha no merge com status {status}.\n\n👉 {pr_url}\n\nErro: {error}",
    },
    "Msg #{n} focused | Ctrl+S: Auto-Patch | Ctrlhift+E: Export": {
        "pt_br": "Msg #{n} em foco | Ctrl+S: Auto-Patch | Ctrl+Shift+E: Exportar",
        "es": "Msg #{n} enfocada | Ctrl+S: Auto-Patch | Ctrl+Shift+E: Exportar",
        "fr": "Msg nº {n} au focus | Ctrl+S : Auto-Patch | Ctrl+Shift+E : Exporter",
        "pt_pt": "Msg #{n} em foco | Ctrl+S: Auto-Patch | Ctrl+Shift+E: Exportar",
    },
    "Open PR in Browser": {
        "pt_br": "Abrir PR no Navegador",
        "es": "Abrir PR en el Navegador",
        "fr": "Ouvrir le PR dans le Navigateur",
        "pt_pt": "Abrir PR no Navegador",
    },
    "Perform a full AI code review comparing the entire current branch against origin/main. Runs git fetch automatically.": {
        "pt_br": "Realiza uma revisão de código completa com IA comparando toda a branch atual contra a origin/main. Executa git fetch automaticamente.",
        "es": "Realiza una revisión de código completa con IA comparando toda la rama actual contra origin/main. Ejecuta git fetch automáticamente.",
        "fr": "Effectue une révision de code complète par IA en comparant toute la branche actuelle à origin/main. Exécute automatiquement git fetch.",
        "pt_pt": "Realiza uma revisão de código completa com IA comparando toda a branch atual contra a origin/main. Executa git fetch automaticamente.",
    },
    "Perform an AI code review on uncommitted local changes (git diff HEAD). Returns structured feedback with issues and improvement suggestions.": {
        "pt_br": "Realiza uma revisão de código com IA nas alterações locais não commitadas (git diff HEAD). Retorna feedback estruturado com issues e sugestões de melhoria.",
        "es": "Realiza una revisión de código con IA sobre los cambios locales sin commitear (git diff HEAD). Devuelve comentarios estructurados con issues y sugerencias de mejora.",
        "fr": "Effectue une révision de code par IA sur les changements locaux non commités (git diff HEAD). Renvoie un retour structuré avec des issues et des suggestions d'amélioration.",
        "pt_pt": "Realiza uma revisão de código com IA nas alterações locais não commitadas (git diff HEAD). Devolve feedback estruturado com issues e sugestões de melhoria.",
    },
    "Pull Request has merge conflicts that must be resolved manually.\n\n👉 {pr_url}\n\nError: {error}": {
        "pt_br": "O Pull Request tem conflitos de merge que devem ser resolvidos manualmente.\n\n👉 {pr_url}\n\nErro: {error}",
        "es": "El Pull Request tiene conflictos de merge que deben resolverse manualmente.\n\n👉 {pr_url}\n\nError: {error}",
        "fr": "Le Pull Request présente des conflits de merge qui doivent être résolus manuellement.\n\n👉 {pr_url}\n\nErreur : {error}",
        "pt_pt": "O Pull Request tem conflitos de merge que devem ser resolvidos manualmente.\n\n👉 {pr_url}\n\nErro: {error}",
    },
    "Resource '{filename}' not found. Run 'gitpr --skill' to download templates.": {
        "pt_br": "Recurso '{filename}' não encontrado. Execute 'gitpr --skill' para baixar os templates.",
        "es": "Recurso '{filename}' no encontrado. Ejecute 'gitpr --skill' para descargar las plantillas.",
        "fr": "Ressource '{filename}' introuvable. Exécutez 'gitpr --skill' pour télécharger les templates.",
        "pt_pt": "Recurso '{filename}' não encontrado. Execute 'gitpr --skill' para descarregar os templates.",
    },
    "Run AI-powered git blame analysis on a file region to trace the origin of business rules. Classifies each commit as ORIGIN (first introduction) or REFACTORING (later change).": {
        "pt_br": "Executa análise de git blame com IA em uma região de arquivo para rastrear a origem das regras de negócio. Classifica cada commit como ORIGIN (primeira introdução) ou REFACTORING (alteração posterior).",
        "es": "Ejecuta análisis de git blame con IA en una región de archivo para rastrear el origen de las reglas de negocio. Clasifica cada commit como ORIGIN (primera introducción) o REFACTORING (cambio posterior).",
        "fr": "Exécute une analyse git blame assistée par IA sur une région de fichier pour retracer l'origine des règles métier. Classe chaque commit comme ORIGIN (première introduction) ou REFACTORING (changement ultérieur).",
        "pt_pt": "Executa análise de git blame com IA numa região de ficheiro para rastrear a origem das regras de negócio. Classifica cada commit como ORIGIN (primeira introdução) ou REFACTORING (alteração posterior).",
    },
    "Run the static linter (.gitpr.linter.yml rules) on current uncommitted changes and report violations.": {
        "pt_br": "Executa o linter estático (regras do .gitpr.linter.yml) nas alterações não commitadas atuais e reporta violações.",
        "es": "Ejecuta el linter estático (reglas de .gitpr.linter.yml) sobre los cambios sin commitear actuales y reporta violaciones.",
        "fr": "Exécute le linter statique (règles .gitpr.linter.yml) sur les changements non commités actuels et signale les violations.",
        "pt_pt": "Executa o linter estático (regras do .gitpr.linter.yml) nas alterações não commitadas atuais e reporta violações.",
    },
    "Run the static local linter (regex-based rules from .gitpr.linter.yml) on the current git diff. Returns error and warning counts with detailed messages.": {
        "pt_br": "Executa o linter estático local (regras baseadas em regex do .gitpr.linter.yml) no git diff atual. Retorna contagens de erros e avisos com mensagens detalhadas.",
        "es": "Ejecuta el linter estático local (reglas basadas en regex de .gitpr.linter.yml) sobre el git diff actual. Devuelve recuentos de errores y advertencias con mensajes detallados.",
        "fr": "Exécute le linter statique local (règles basées sur regex de .gitpr.linter.yml) sur le git diff actuel. Renvoie les compteurs d'erreurs et d'avertissements avec des messages détaillés.",
        "pt_pt": "Executa o linter estático local (regras baseadas em regex do .gitpr.linter.yml) no git diff atual. Devolve contagens de erros e avisos com mensagens detalhadas.",
    },
    "Scanning cache files... {done} / {total}": {
        "pt_br": "Analisando arquivos de cache... {done} / {total}",
        "es": "Analizando archivos de caché... {done} / {total}",
        "fr": "Analyse des fichiers de cache... {done} / {total}",
        "pt_pt": "A analisar ficheiros de cache... {done} / {total}",
    },
    "Unexpected response from GitHub (HTTP {code})": {
        "pt_br": "Resposta inesperada do GitHub (HTTP {code})",
        "es": "Respuesta inesperada de GitHub (HTTP {code})",
        "fr": "Réponse inattendue de GitHub (HTTP {code})",
        "pt_pt": "Resposta inesperada do GitHub (HTTP {code})",
    },
    "[notice] A new release of gitpr is available: {current_version} -> {latest_version}": {
        "pt_br": "[notice] Uma nova versão do gitpr está disponível: {current_version} -> {latest_version}",
        "es": "[notice] Una nueva versión de gitpr está disponible: {current_version} -> {latest_version}",
        "fr": "[notice] Une nouvelle version de gitpr est disponible : {current_version} -> {latest_version}",
        "pt_pt": "[notice] Uma nova versão do gitpr está disponível: {current_version} -> {latest_version}",
    },
    "{count} file(s) not staged. Select which ones to add:": {
        "pt_br": "{count} arquivo(s) não estão no stage. Selecione quais adicionar:",
        "es": "{count} archivo(s) no están en stage. Seleccione cuáles añadir:",
        "fr": "{count} fichier(s) non stagé(s). Sélectionnez lesquels ajouter :",
        "pt_pt": "{count} ficheiro(s) não estão no stage. Selecione quais adicionar:",
    },
    "ℹ️ {count} file(s) are not staged. They will still be included in this analysis.": {
        "pt_br": "ℹ️ {count} arquivo(s) não estão no stage. Eles ainda serão incluídos nesta análise.",
        "es": "ℹ️ {count} archivo(s) no están en stage. Aun así se incluirán en este análisis.",
        "fr": "ℹ️ {count} fichier(s) ne sont pas stagé(s). Ils seront quand même inclus dans cette analyse.",
        "pt_pt": "ℹ️ {count} ficheiro(s) não estão no stage. Ainda assim serão incluídos nesta análise.",
    },
    "⏳ Analyzing batch {current}/{total}...": {
        "pt_br": "⏳ Analisando lote {current}/{total}...",
        "es": "⏳ Analizando lote {current}/{total}...",
        "fr": "⏳ Analyse du lot {current}/{total}...",
        "pt_pt": "⏳ A analisar lote {current}/{total}...",
    },
    "⚠️ GitHub token is no longer valid: {error_msg}": {
        "pt_br": "⚠️ O token do GitHub não é mais válido: {error_msg}",
        "es": "⚠️ El token de GitHub ya no es válido: {error_msg}",
        "fr": "⚠️ Le jeton GitHub n'est plus valide : {error_msg}",
        "pt_pt": "⚠️ O token do GitHub já não é válido: {error_msg}",
    },
    "⚠️ The provided token is also invalid: {error_msg}": {
        "pt_br": "⚠️ O token informado também é inválido: {error_msg}",
        "es": "⚠️ El token proporcionado también es inválido: {error_msg}",
        "fr": "⚠️ Le jeton fourni est également invalide : {error_msg}",
        "pt_pt": "⚠️ O token informado também é inválido: {error_msg}",
    },
    "⚠️ {count} file(s) are not staged and will NOT be included in the commit.": {
        "pt_br": "⚠️ {count} arquivo(s) não estão no stage e NÃO serão incluídos no commit.",
        "es": "⚠️ {count} archivo(s) no están en stage y NO se incluirán en el commit.",
        "fr": "⚠️ {count} fichier(s) ne sont pas stagé(s) et ne seront PAS inclus dans le commit.",
        "pt_pt": "⚠️ {count} ficheiro(s) não estão no stage e NÃO serão incluídos no commit.",
    },
    "⚡ Auto-Patch: Code extracted and saved to {file}!": {
        "pt_br": "⚡ Auto-Patch: Código extraído e salvo em {file}!",
        "es": "⚡ Auto-Patch: ¡Código extraído y guardado en {file}!",
        "fr": "⚡ Auto-Patch : Code extrait et enregistré dans {file} !",
        "pt_pt": "⚡ Auto-Patch: Código extraído e guardado em {file}!",
    },
    "✅ Issue saved locally: {output_filename}": {
        "pt_br": "✅ Issue salva localmente: {output_filename}",
        "es": "✅ Issue guardada localmente: {output_filename}",
        "fr": "✅ Issue enregistrée localement : {output_filename}",
        "pt_pt": "✅ Issue guardada localmente: {output_filename}",
    },
    "✅ Issue successfully created on GitHub:\n👉 {issue_url}": {
        "pt_br": "✅ Issue criada com sucesso no GitHub:\n👉 {issue_url}",
        "es": "✅ Issue creada con éxito en GitHub:\n👉 {issue_url}",
        "fr": "✅ Issue créée avec succès sur GitHub :\n👉 {issue_url}",
        "pt_pt": "✅ Issue criada com sucesso no GitHub:\n👉 {issue_url}",
    },
    "✅ Metrics exported: {count} events.": {
        "pt_br": "✅ Métricas exportadas: {count} eventos.",
        "es": "✅ Métricas exportadas: {count} eventos.",
        "fr": "✅ Métriques exportées : {count} événements.",
        "pt_pt": "✅ Métricas exportadas: {count} eventos.",
    },
    "✅ PR merged successfully:\n👉 {pr_url}": {
        "pt_br": "✅ Merge do PR concluído com sucesso:\n👉 {pr_url}",
        "es": "✅ Merge del PR completado con éxito:\n👉 {pr_url}",
        "fr": "✅ Merge du PR effectué avec succès :\n👉 {pr_url}",
        "pt_pt": "✅ Merge do PR concluído com sucesso:\n👉 {pr_url}",
    },
    "✅ PR saved locally: {output_filename}": {
        "pt_br": "✅ PR salvo localmente: {output_filename}",
        "es": "✅ PR guardado localmente: {output_filename}",
        "fr": "✅ PR enregistré localement : {output_filename}",
        "pt_pt": "✅ PR guardado localmente: {output_filename}",
    },
    "✅ PR successfully created on GitHub:\n👉 {pr_url}": {
        "pt_br": "✅ PR criado com sucesso no GitHub:\n👉 {pr_url}",
        "es": "✅ PR creado con éxito en GitHub:\n👉 {pr_url}",
        "fr": "✅ PR créé avec succès sur GitHub :\n👉 {pr_url}",
        "pt_pt": "✅ PR criado com sucesso no GitHub:\n👉 {pr_url}",
    },
    "✅ PR updated:\n👉 {pr_url}": {
        "pt_br": "✅ PR atualizado:\n👉 {pr_url}",
        "es": "✅ PR actualizado:\n👉 {pr_url}",
        "fr": "✅ PR mis à jour :\n👉 {pr_url}",
        "pt_pt": "✅ PR atualizado:\n👉 {pr_url}",
    },
    "✅ Unified report successfully saved: '{output_filename}'": {
        "pt_br": "✅ Relatório unificado salvo com sucesso: '{output_filename}'",
        "es": "✅ Informe unificado guardado con éxito: '{output_filename}'",
        "fr": "✅ Rapport unifié enregistré avec succès : '{output_filename}'",
        "pt_pt": "✅ Relatório unificado guardado com sucesso: '{output_filename}'",
    },
    "✅ {count} file(s) added to stage.": {
        "pt_br": "✅ {count} arquivo(s) adicionado(s) ao stage.",
        "es": "✅ {count} archivo(s) añadido(s) al stage.",
        "fr": "✅ {count} fichier(s) ajouté(s) au stage.",
        "pt_pt": "✅ {count} ficheiro(s) adicionado(s) ao stage.",
    },
    "❌ Failed to connect to GitHub: {error}": {
        "pt_br": "❌ Falha ao conectar ao GitHub: {error}",
        "es": "❌ Error al conectar con GitHub: {error}",
        "fr": "❌ Échec de la connexion à GitHub : {error}",
        "pt_pt": "❌ Falha ao ligar ao GitHub: {error}",
    },
    "❌ GitHub API Error ({status_code}): {response_text}": {
        "pt_br": "❌ Erro na API do GitHub ({status_code}): {response_text}",
        "es": "❌ Error de la API de GitHub ({status_code}): {response_text}",
        "fr": "❌ Erreur de l'API GitHub ({status_code}) : {response_text}",
        "pt_pt": "❌ Erro na API do GitHub ({status_code}): {response_text}",
    },
    "❌ Maximum attempts ({max}) reached. Cannot proceed without a valid token.": {
        "pt_br": "❌ Número máximo de tentativas ({max}) atingido. Não é possível prosseguir sem um token válido.",
        "es": "❌ Número máximo de intentos ({max}) alcanzado. No se puede continuar sin un token válido.",
        "fr": "❌ Nombre maximal de tentatives ({max}) atteint. Impossible de continuer sans un jeton valide.",
        "pt_pt": "❌ Número máximo de tentativas ({max}) atingido. Não é possível prosseguir sem um token válido.",
    },
    "❌ Merge Conflict": {
        "pt_br": "❌ Conflito de Merge",
        "es": "❌ Conflicto de Merge",
        "fr": "❌ Conflit de Merge",
        "pt_pt": "❌ Conflito de Merge",
    },
    "❌ Merge Failed": {
        "pt_br": "❌ Falha no Merge",
        "es": "❌ Fallo del Merge",
        "fr": "❌ Échec du Merge",
        "pt_pt": "❌ Falha no Merge",
    },
    "❌ Push failed: {error}": {
        "pt_br": "❌ Falha no push: {error}",
        "es": "❌ Fallo en el push: {error}",
        "fr": "❌ Échec du push : {error}",
        "pt_pt": "❌ Falha no push: {error}",
    },
    "📄 {count} documentation file(s) excluded from diff (Smart Excludes).": {
        "pt_br": "📄 {count} arquivo(s) de documentação excluído(s) do diff (Smart Excludes).",
        "es": "📄 {count} archivo(s) de documentación excluido(s) del diff (Smart Excludes).",
        "fr": "📄 {count} fichier(s) de documentation exclu(s) du diff (Smart Excludes).",
        "pt_pt": "📄 {count} ficheiro(s) de documentação excluído(s) do diff (Smart Excludes).",
    },
    "📋 Attempt {attempt} of {max}": {
        "pt_br": "📋 Tentativa {attempt} de {max}",
        "es": "📋 Intento {attempt} de {max}",
        "fr": "📋 Tentative {attempt} sur {max}",
        "pt_pt": "📋 Tentativa {attempt} de {max}",
    },
    "📍 File: {file_path} (Lines: {start_line} to {end_line})": {
        "pt_br": "📍 Arquivo: {file_path} (Linhas: {start_line} a {end_line})",
        "es": "📍 Archivo: {file_path} (Líneas: {start_line} a {end_line})",
        "fr": "📍 Fichier : {file_path} (Lignes : {start_line} à {end_line})",
        "pt_pt": "📍 Ficheiro: {file_path} (Linhas: {start_line} a {end_line})",
    },
    "📝 Pre-save: AI payload saved to {filename}": {
        "pt_br": "📝 Pre-save: Payload da IA salvo em {filename}",
        "es": "📝 Pre-save: Payload de la IA guardado en {filename}",
        "fr": "📝 Pré-enregistrement : payload de l'IA enregistré dans {filename}",
        "pt_pt": "📝 Pre-save: Payload da IA guardado em {filename}",
    },
    "📤 Message #{n} exported to {file}!": {
        "pt_br": "📤 Mensagem #{n} exportada para {file}!",
        "es": "📤 ¡Mensaje #{n} exportado a {file}!",
        "fr": "📤 Message nº {n} exporté vers {file} !",
        "pt_pt": "📤 Mensagem #{n} exportada para {file}!",
    },
    "📤 Session exported successfully to {file}!": {
        "pt_br": "📤 Sessão exportada com sucesso para {file}!",
        "es": "📤 ¡Sesión exportada con éxito a {file}!",
        "fr": "📤 Session exportée avec succès vers {file} !",
        "pt_pt": "📤 Sessão exportada com sucesso para {file}!",
    },
    "📦 Huge diff detected! Processing in {count} batches (Map-Reduce)...": {
        "pt_br": "📦 Diff gigante detectado! Processando em {count} lotes (Map-Reduce)...",
        "es": "📦 ¡Diff enorme detectado! Procesando en {count} lotes (Map-Reduce)...",
        "fr": "📦 Énorme diff détecté ! Traitement en {count} lots (Map-Reduce)...",
        "pt_pt": "📦 Diff gigante detetado! A processar em {count} lotes (Map-Reduce)...",
    },
    "📦 Skill file {filename} moved to .gitpr/skill/": {
        "pt_br": "📦 Arquivo de skill {filename} movido para .gitpr/skill/",
        "es": "📦 Archivo skill {filename} movido a .gitpr/skill/",
        "fr": "📦 Fichier skill {filename} déplacé vers .gitpr/skill/",
        "pt_pt": "📦 Ficheiro de skill {filename} movido para .gitpr/skill/",
    },
    "🤖 Structuring Issue using {provider} ({api_model})...": {
        "pt_br": "🤖 Estruturando Issue usando {provider} ({api_model})...",
        "es": "🤖 Estructurando Issue usando {provider} ({api_model})...",
        "fr": "🤖 Structuration de l'Issue avec {provider} ({api_model})...",
        "pt_pt": "🤖 A estruturar Issue usando {provider} ({api_model})...",
    },
    "🧪 Auto-Patch: Code extracted from message #{n} and saved to {file}!": {
        "pt_br": "🧪 Auto-Patch: Código extraído da mensagem #{n} e salvo em {file}!",
        "es": "🧪 Auto-Patch: ¡Código extraído del mensaje #{n} y guardado en {file}!",
        "fr": "🧪 Auto-Patch : Code extrait du message nº {n} et enregistré dans {file} !",
        "pt_pt": "🧪 Auto-Patch: Código extraído da mensagem #{n} e guardado em {file}!",
    },
}


def build_table():
    """key -> {pt_br, es, fr, pt_pt} for all 91 keys."""
    table = {}
    for key in PROMPTS_EN:
        table[key] = {lang: key for lang in ("pt_br", "es", "fr", "pt_pt")}
    table.update(UI_TRANSLATIONS)
    assert len(table) == 91, f"expected 91 keys, got {len(table)}"
    return table


LANG_FILES = {
    "pt_br.json": "pt_br",
    "pt_pt.json": "pt_pt",
    "es.json": "es",
    "es_es.json": "es",
    "fr.json": "fr",
    "fr_fr.json": "fr",
}


def main():
    table = build_table()
    for filename, lang in LANG_FILES.items():
        path = LANGS / filename
        raw = path.read_text(encoding="utf-8", errors="replace")
        data = json.loads(raw)
        added = 0
        for key, values in table.items():
            value = values[lang]
            if key not in data:
                data[key] = value
                added += 1
        # json.dump reproduces the existing file formatting byte-for-byte
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")
        print(f"{filename}: +{added} keys -> {len(data)} total")


if __name__ == "__main__":
    main()
