#!/usr/bin/env python3
r"""One-off repair for the mangled i18n keys (value == key with captured call-site fragments).

The old extraction regex in tests/sync_i18n.py (`__\(['"](.*?)['"]\)`) captured
kwargs of the enclosing call (e.g. `fg="cyan"`, `count=len(...)`) into the
translation keys. Those keys never match at lookup time, so the messages always
fell back to English. This script:

  1. Detects the mangled keys (identity keys containing `", <kwarg>=`).
  2. Derives the clean key (text up to the first `", <kwarg>=` separator).
  3. Replaces each entry with a properly translated value.
  4. Repairs a truncated MCP prompt key (replaces it with its full runtime key).
  5. Prunes two orphan keys (unused after FileStageScreen removal).
  6. Restores es.json / fr.json parity (missing `❌ Failed to stage files: {error}`).

Translations are mined from scripts/sync_all_langs.py (FR/ES dicts) and
authored fresh for pt_br / pt_pt (and for the FR/ES keys the dicts miss).

Run from the repo root:
    python -X utf8 scripts/fix_mangled_i18n_keys.py
"""
import ast
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

REPO = Path(__file__).resolve().parent.parent
LANGS_DIR = REPO / "langs"
LANG_FILES = ["pt_br.json", "pt_pt.json", "es_es.json", "es.json", "fr_fr.json", "fr.json"]
SYNC_ALL_LANGS = REPO / "scripts" / "sync_all_langs.py"

# A mangled key is an identity key (value == key) whose text captured call-site
# fragments: a double quote followed by ", " and a kwarg assignment.
MANGLED_RE = re.compile(r'",\s+\w+=')

TRUNCATED_KEY = "Generate a Conventional Commits message (e.g., 'feat: add user auth"
FULL_MCP_KEY = (
    "Generate a Conventional Commits message (e.g., 'feat: add user auth') "
    "from the current uncommitted changes."
)

ORPHAN_KEYS = ["No files selected for staging.", "❌ Failed to stage files"]
STAGE_ERROR_KEY = "❌ Failed to stage files: {error}"
EXPECTED_COUNT = 529

# ---------------------------------------------------------------------------
# Fresh translations for the keys the FR/ES dicts in sync_all_langs.py miss.
# ---------------------------------------------------------------------------
FR_FRESH = {
    "\n⚠️ Linter generated {count} warning(s):":
        "\n⚠️ Le linter a généré {count} avertissement(s) :",
    "\n❌ Error saving review: {error}":
        "\n❌ Erreur lors de l'enregistrement de la révision : {error}",
    "\n❌ Syntax error in local .gitpr.linter.yml file:\n{error}":
        "\n❌ Erreur de syntaxe dans le fichier local .gitpr.linter.yml :\n{error}",
    "\n❌ Unexpected error reading local linter rules: {error}":
        "\n❌ Erreur inattendue lors de la lecture des règles locales du linter : {error}",
    "\n🚨 Linter found {count} error(s):":
        "\n🚨 Le linter a trouvé {count} erreur(s) :",
    "⚠️ Warning: Could not load linter plugin {file} ({error})":
        "⚠️ Attention : Impossible de charger le plugin du linter {file} ({error})",
    "✅ Found {count} commit(s) on the surface. Starting time travel...\n":
        "✅ {count} commit(s) trouvé(s) en surface. Démarrage du voyage dans le temps...\n",
    "❌ Commit failed: {output}":
        "❌ Échec du commit : {output}",
    "❌ GitHub API Error ({code}): {msg}":
        "❌ Erreur de l'API GitHub ({code}) : {msg}",
    "📋 Auto-staging {count} file(s)...":
        "📋 Ajout automatique de {count} fichier(s) au stage...",
    "🚨 Linter found {count} error(s):":
        "🚨 Le linter a trouvé {count} erreur(s) :",
    "🤖 GitPR is analyzing your code using {provider} ({model})...\n":
        "🤖 GitPR analyse votre code avec {provider} ({model})...\n",
    "Generate ONLY a JSON object in the format {json_format} for the commit message, unifying these technical summaries:\n":
        "Générez UNIQUEMENT un objet JSON au format {json_format} pour le message de commit, en unifiant ces résumés techniques :\n",
    "Generate ONLY a JSON object in the format {json_format} for this diff:\n":
        "Générez UNIQUEMENT un objet JSON au format {json_format} pour ce diff :\n",
    "Generate ONLY a JSON object in the format {json_format} pointing out errors and improvements for this diff:\n":
        "Générez UNIQUEMENT un objet JSON au format {json_format} signalant les erreurs et les améliorations pour ce diff :\n",
    "Generate ONLY a JSON object in the format {json_format} with a code review focused on improvements, using these summaries:\n":
        "Générez UNIQUEMENT un objet JSON au format {json_format} avec une révision de code axée sur les améliorations, en utilisant ces résumés :\n",
    "Generate ONLY a JSON object in the format {json_format} with the analysis and improvements for the entire code of this file:\n":
        "Générez UNIQUEMENT un objet JSON au format {json_format} avec l'analyse et les améliorations pour l'intégralité du code de ce fichier :\n",
    "Unify these technical summaries and generate ONLY a JSON object in the format {json_format} describing the Pull Request:\n":
        "Unifiez ces résumés techniques et générez UNIQUEMENT un objet JSON au format {json_format} décrivant la Pull Request :\n",
}

ES_FRESH = {
    "\n⚠️ Linter generated {count} warning(s):":
        "\n⚠️ El linter generó {count} advertencia(s):",
    "\n❌ Error saving review: {error}":
        "\n❌ Error al guardar la revisión: {error}",
    "\n❌ Syntax error in local .gitpr.linter.yml file:\n{error}":
        "\n❌ Error de sintaxis en el archivo local .gitpr.linter.yml:\n{error}",
    "\n❌ Unexpected error reading local linter rules: {error}":
        "\n❌ Error inesperado al leer las reglas locales del linter: {error}",
    "\n🚨 Linter found {count} error(s):":
        "\n🚨 El linter encontró {count} error(es):",
    "⚠️ Warning: Could not load linter plugin {file} ({error})":
        "⚠️ Advertencia: No se pudo cargar el plugin del linter {file} ({error})",
    "✅ Found {count} commit(s) on the surface. Starting time travel...\n":
        "✅ Encontrado(s) {count} commit(s) en la superficie. Iniciando viaje en el tiempo...\n",
    "❌ Commit failed: {output}":
        "❌ Falló el commit: {output}",
    "❌ GitHub API Error ({code}): {msg}":
        "❌ Error de la API de GitHub ({code}): {msg}",
    "📋 Auto-staging {count} file(s)...":
        "📋 Añadiendo {count} archivo(s) al stage automáticamente...",
    "🚨 Linter found {count} error(s):":
        "🚨 El linter encontró {count} error(es):",
    "🤖 GitPR is analyzing your code using {provider} ({model})...\n":
        "🤖 GitPR está analizando tu código usando {provider} ({model})...\n",
    "Generate ONLY a JSON object in the format {json_format} for the commit message, unifying these technical summaries:\n":
        "Genera ÚNICAMENTE un objeto JSON en el formato {json_format} para el mensaje de commit, unificando estos resúmenes técnicos:\n",
    "Generate ONLY a JSON object in the format {json_format} for this diff:\n":
        "Genera ÚNICAMENTE un objeto JSON en el formato {json_format} para este diff:\n",
    "Generate ONLY a JSON object in the format {json_format} pointing out errors and improvements for this diff:\n":
        "Genera ÚNICAMENTE un objeto JSON en el formato {json_format} señalando errores y mejoras para este diff:\n",
    "Generate ONLY a JSON object in the format {json_format} with a code review focused on improvements, using these summaries:\n":
        "Genera ÚNICAMENTE un objeto JSON en el formato {json_format} con una revisión de código centrada en mejoras, usando estos resúmenes:\n",
    "Generate ONLY a JSON object in the format {json_format} with the analysis and improvements for the entire code of this file:\n":
        "Genera ÚNICAMENTE un objeto JSON en el formato {json_format} con el análisis y las mejoras para todo el código de este archivo:\n",
    "Unify these technical summaries and generate ONLY a JSON object in the format {json_format} describing the Pull Request:\n":
        "Unifica estos resúmenes técnicos y genera ÚNICAMENTE un objeto JSON en el formato {json_format} describiendo el Pull Request:\n",
}

PT_BR = {
    "\n⚠️ Linter generated {count} warning(s):":
        "\n⚠️ Linter gerou {count} aviso(s):",
    "\n❌ Error saving review: {error}":
        "\n❌ Erro ao salvar a revisão: {error}",
    "\n❌ Syntax error in local .gitpr.linter.yml file:\n{error}":
        "\n❌ Erro de sintaxe no arquivo local .gitpr.linter.yml:\n{error}",
    "\n❌ Unexpected error reading local linter rules: {error}":
        "\n❌ Erro inesperado ao ler as regras locais do linter: {error}",
    "\n🚨 Linter found {count} error(s):":
        "\n🚨 Linter encontrou {count} erro(s):",
    "⚠️ Attention! Found {count} alerts in the Linter rules.":
        "⚠️ Atenção! Encontrados {count} alertas nas regras do Linter.",
    "⚠️ Failed to install {hook_name}: HTTP {code}":
        "⚠️ Falha ao instalar {hook_name}: HTTP {code}",
    "⚠️ Failed to install {hook_name}: {error}":
        "⚠️ Falha ao instalar {hook_name}: {error}",
    "⚠️ File {local_name} already exists in this directory. It will not be overwritten.":
        "⚠️ O arquivo {local_name} já existe neste diretório. Ele não será sobrescrito.",
    "⚠️ Warning: Could not get Git Log: {error}":
        "⚠️ Aviso: Não foi possível obter o Git Log: {error}",
    "⚠️ Warning: Could not load linter plugin {file} ({error})":
        "⚠️ Aviso: Não foi possível carregar o plugin do linter {file} ({error})",
    "⚠️ Warning: Could not move {filename} to .gitpr/skill/ ({error})":
        "⚠️ Aviso: Não foi possível mover {filename} para .gitpr/skill/ ({error})",
    "⚠️ Warning: Failed to read file {file_name} ({error})":
        "⚠️ Aviso: Falha ao ler o arquivo {file_name} ({error})",
    "✅ Found {count} commit(s) on the surface. Starting time travel...\n":
        "✅ Encontrado(s) {count} commit(s) na superfície. Iniciando viagem no tempo...\n",
    "✅ Metrics purged ({count} files removed).":
        "✅ Métricas expurgadas ({count} arquivos removidos).",
    "❌ Commit failed: {output}":
        "❌ Commit falhou: {output}",
    "❌ Error calculating diff: {error}":
        "❌ Erro ao calcular o diff: {error}",
    "❌ Error injecting into hook: {error}":
        "❌ Erro ao injetar no hook: {error}",
    "❌ Error reading file: {error}":
        "❌ Erro ao ler o arquivo: {error}",
    "❌ Error running Git: {error}":
        "❌ Erro ao executar o Git: {error}",
    "❌ Error saving file: {error}":
        "❌ Erro ao salvar o arquivo: {error}",
    "❌ Error saving report: {error}":
        "❌ Erro ao salvar o relatório: {error}",
    "❌ Error: API Key for provider '{provider}' not found.":
        "❌ Erro: Chave de API para o provedor '{provider}' não encontrada.",
    "❌ Error: API Key not configured for provider '{provider}' in the CI/CD environment.":
        "❌ Erro: Chave de API não configurada para o provedor '{provider}' no ambiente CI/CD.",
    "❌ Error: Could not determine model for provider '{provider}'.":
        "❌ Erro: Não foi possível determinar o modelo para o provedor '{provider}'.",
    "❌ Failed to apply update: {error}":
        "❌ Falha ao aplicar a atualização: {error}",
    "❌ Failed to process {local_name}: {error}":
        "❌ Falha ao processar {local_name}: {error}",
    "❌ Model configuration not found for provider {provider}.":
        "❌ Configuração de modelo não encontrada para o provedor {provider}.",
    "❌ Network error while downloading {local_name}: {error}":
        "❌ Erro de rede ao baixar {local_name}: {error}",
    "❌ The file '{file_path}' was not found.":
        "❌ O arquivo '{file_path}' não foi encontrado.",
    "❌ Unknown AI provider: {provider}":
        "❌ Provedor de IA desconhecido: {provider}",
    "📄 File Mode: Analyzing full content of '{input}'...":
        "📄 Modo Arquivo: Analisando o conteúdo completo de '{input}'...",
    "📋 Auto-staging {count} file(s)...":
        "📋 Adicionando {count} arquivo(s) ao stage automaticamente...",
    "📥 Downloading {hook_name}...":
        "📥 Baixando {hook_name}...",
    "📦 Updating scripts to {version}...":
        "📦 Atualizando scripts para {version}...",
    "🔄 Compiling history of repository '{repo_name}', branch '{branch}' against '{base_branch}'...":
        "🔄 Compilando histórico do repositório '{repo_name}', branch '{branch}' contra '{base_branch}'...",
    "🔑 API Key for {provider} not found.":
        "🔑 Chave de API para {provider} não encontrada.",
    "🤖 GitPR is analyzing your code using {provider} ({model})...\n":
        "🤖 GitPR está analisando seu código usando {provider} ({model})...\n",
    "🧠 File {file_name} (Skill) found and loaded!":
        "🧠 Arquivo {file_name} (Skill) encontrado e carregado!",
    "Generate ONLY a JSON object in the format {json_format} for the commit message, unifying these technical summaries:\n":
        "Gere APENAS um objeto JSON no formato {json_format} para a mensagem de commit, unificando estes resumos técnicos:\n",
    "Generate ONLY a JSON object in the format {json_format} for this diff:\n":
        "Gere APENAS um objeto JSON no formato {json_format} para este diff:\n",
    "Generate ONLY a JSON object in the format {json_format} pointing out errors and improvements for this diff:\n":
        "Gere APENAS um objeto JSON no formato {json_format} apontando erros e melhorias para este diff:\n",
    "Generate ONLY a JSON object in the format {json_format} with a code review focused on improvements, using these summaries:\n":
        "Gere APENAS um objeto JSON no formato {json_format} com uma revisão de código focada em melhorias, usando estes resumos:\n",
    "Generate ONLY a JSON object in the format {json_format} with the analysis and improvements for the entire code of this file:\n":
        "Gere APENAS um objeto JSON no formato {json_format} com a análise e as melhorias para todo o código deste arquivo:\n",
    "Unify these technical summaries and generate ONLY a JSON object in the format {json_format} describing the Pull Request:\n":
        "Unifique estes resumos técnicos e gere APENAS um objeto JSON no formato {json_format} descrevendo o Pull Request:\n",
    "❌ No code blocks found in message #{n}.":
        "❌ Nenhum bloco de código encontrado na mensagem #{n}.",
    "🚨 Linter found {count} error(s):":
        "🚨 Linter encontrou {count} erro(s):",
    "   Current: {current} (from .env)":
        "   Atual: {current} (do .env)",
    "Rule '{rule_name}' contains invalid Regex: {error}":
        "A regra '{rule_name}' contém Regex inválido: {error}",
    "❌ GitHub API Error ({code}): {msg}":
        "❌ Erro da API do GitHub ({code}): {msg}",
}

PT_PT = {
    "\n⚠️ Linter generated {count} warning(s):":
        "\n⚠️ Linter gerou {count} aviso(s):",
    "\n❌ Error saving review: {error}":
        "\n❌ Erro ao guardar a revisão: {error}",
    "\n❌ Syntax error in local .gitpr.linter.yml file:\n{error}":
        "\n❌ Erro de sintaxe no ficheiro local .gitpr.linter.yml:\n{error}",
    "\n❌ Unexpected error reading local linter rules: {error}":
        "\n❌ Erro inesperado ao ler as regras locais do linter: {error}",
    "\n🚨 Linter found {count} error(s):":
        "\n🚨 Linter encontrou {count} erro(s):",
    "⚠️ Attention! Found {count} alerts in the Linter rules.":
        "⚠️ Atenção! Encontrados {count} alertas nas regras do Linter.",
    "⚠️ Failed to install {hook_name}: HTTP {code}":
        "⚠️ Falha ao instalar {hook_name}: HTTP {code}",
    "⚠️ Failed to install {hook_name}: {error}":
        "⚠️ Falha ao instalar {hook_name}: {error}",
    "⚠️ File {local_name} already exists in this directory. It will not be overwritten.":
        "⚠️ O ficheiro {local_name} já existe neste diretório. Não será substituído.",
    "⚠️ Warning: Could not get Git Log: {error}":
        "⚠️ Aviso: Não foi possível obter o Git Log: {error}",
    "⚠️ Warning: Could not load linter plugin {file} ({error})":
        "⚠️ Aviso: Não foi possível carregar o plugin do linter {file} ({error})",
    "⚠️ Warning: Could not move {filename} to .gitpr/skill/ ({error})":
        "⚠️ Aviso: Não foi possível mover {filename} para .gitpr/skill/ ({error})",
    "⚠️ Warning: Failed to read file {file_name} ({error})":
        "⚠️ Aviso: Falha ao ler o ficheiro {file_name} ({error})",
    "✅ Found {count} commit(s) on the surface. Starting time travel...\n":
        "✅ Encontrado(s) {count} commit(s) à superfície. A iniciar viagem no tempo...\n",
    "✅ Metrics purged ({count} files removed).":
        "✅ Métricas expurgadas ({count} ficheiros removidos).",
    "❌ Commit failed: {output}":
        "❌ Commit falhou: {output}",
    "❌ Error calculating diff: {error}":
        "❌ Erro ao calcular o diff: {error}",
    "❌ Error injecting into hook: {error}":
        "❌ Erro ao injetar no hook: {error}",
    "❌ Error reading file: {error}":
        "❌ Erro ao ler o ficheiro: {error}",
    "❌ Error running Git: {error}":
        "❌ Erro ao executar o Git: {error}",
    "❌ Error saving file: {error}":
        "❌ Erro ao guardar o ficheiro: {error}",
    "❌ Error saving report: {error}":
        "❌ Erro ao guardar o relatório: {error}",
    "❌ Error: API Key for provider '{provider}' not found.":
        "❌ Erro: Chave de API para o fornecedor '{provider}' não encontrada.",
    "❌ Error: API Key not configured for provider '{provider}' in the CI/CD environment.":
        "❌ Erro: Chave de API não configurada para o fornecedor '{provider}' no ambiente CI/CD.",
    "❌ Error: Could not determine model for provider '{provider}'.":
        "❌ Erro: Não foi possível determinar o modelo para o fornecedor '{provider}'.",
    "❌ Failed to apply update: {error}":
        "❌ Falha ao aplicar a actualização: {error}",
    "❌ Failed to process {local_name}: {error}":
        "❌ Falha ao processar {local_name}: {error}",
    "❌ Model configuration not found for provider {provider}.":
        "❌ Configuração de modelo não encontrada para o fornecedor {provider}.",
    "❌ Network error while downloading {local_name}: {error}":
        "❌ Erro de rede ao descarregar {local_name}: {error}",
    "❌ The file '{file_path}' was not found.":
        "❌ O ficheiro '{file_path}' não foi encontrado.",
    "❌ Unknown AI provider: {provider}":
        "❌ Fornecedor de IA desconhecido: {provider}",
    "📄 File Mode: Analyzing full content of '{input}'...":
        "📄 Modo Ficheiro: A analisar o conteúdo completo de '{input}'...",
    "📋 Auto-staging {count} file(s)...":
        "📋 A adicionar {count} ficheiro(s) ao stage automaticamente...",
    "📥 Downloading {hook_name}...":
        "📥 A descarregar {hook_name}...",
    "📦 Updating scripts to {version}...":
        "📦 A actualizar scripts para {version}...",
    "🔄 Compiling history of repository '{repo_name}', branch '{branch}' against '{base_branch}'...":
        "🔄 A compilar o histórico do repositório '{repo_name}', branch '{branch}' contra '{base_branch}'...",
    "🔑 API Key for {provider} not found.":
        "🔑 Chave de API para {provider} não encontrada.",
    "🤖 GitPR is analyzing your code using {provider} ({model})...\n":
        "🤖 O GitPR está a analisar o seu código com {provider} ({model})...\n",
    "🧠 File {file_name} (Skill) found and loaded!":
        "🧠 Ficheiro {file_name} (Skill) encontrado e carregado!",
    "Generate ONLY a JSON object in the format {json_format} for the commit message, unifying these technical summaries:\n":
        "Gere APENAS um objeto JSON no formato {json_format} para a mensagem de commit, unificando estes resumos técnicos:\n",
    "Generate ONLY a JSON object in the format {json_format} for this diff:\n":
        "Gere APENAS um objeto JSON no formato {json_format} para este diff:\n",
    "Generate ONLY a JSON object in the format {json_format} pointing out errors and improvements for this diff:\n":
        "Gere APENAS um objeto JSON no formato {json_format} a apontar erros e melhorias para este diff:\n",
    "Generate ONLY a JSON object in the format {json_format} with a code review focused on improvements, using these summaries:\n":
        "Gere APENAS um objeto JSON no formato {json_format} com uma revisão de código focada em melhorias, usando estes resumos:\n",
    "Generate ONLY a JSON object in the format {json_format} with the analysis and improvements for the entire code of this file:\n":
        "Gere APENAS um objeto JSON no formato {json_format} com a análise e as melhorias para todo o código deste ficheiro:\n",
    "Unify these technical summaries and generate ONLY a JSON object in the format {json_format} describing the Pull Request:\n":
        "Unifique estes resumos técnicos e gere APENAS um objeto JSON no formato {json_format} a descrever o Pull Request:\n",
    "❌ No code blocks found in message #{n}.":
        "❌ Nenhum bloco de código encontrado na mensagem #{n}.",
    "🚨 Linter found {count} error(s):":
        "🚨 Linter encontrou {count} erro(s):",
    "   Current: {current} (from .env)":
        "   Atual: {current} (do .env)",
    "Rule '{rule_name}' contains invalid Regex: {error}":
        "A regra '{rule_name}' contém Regex inválido: {error}",
    "❌ GitHub API Error ({code}): {msg}":
        "❌ Erro da API do GitHub ({code}): {msg}",
}

# Completions for the truncated MCP prompt key (full key -> translated value).
MCP_TRANSLATIONS = {
    "pt_br": "Gera uma mensagem no padrão Conventional Commits (ex.: 'feat: add user auth') "
             "a partir das alterações atuais não commitadas.",
    "pt_pt": "Gera uma mensagem no padrão Conventional Commits (ex.: 'feat: add user auth') "
             "a partir das alterações atuais não commitadas.",
}


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def mine_translations():
    """Extracts the FR/ES dicts from scripts/sync_all_langs.py without importing
    it (its top-level code rewrites the langs/ files)."""
    src = SYNC_ALL_LANGS.read_text(encoding="utf-8")
    tree = ast.parse(src)
    mined = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in ("FR", "ES"):
                    try:
                        mined[target.id] = ast.literal_eval(node.value)
                    except (ValueError, SyntaxError, MemoryError):
                        pass
    return mined


def clean_of(key):
    """Derives the clean key: text up to the first `", <kwarg>=` separator.

    The mangled keys stored newlines double-escaped (literal backslash-n), but
    the runtime strings contain real newlines, so convert them back."""
    clean = re.split(r'",\s+\w+=', key, maxsplit=1)[0]
    return clean.replace("\\n", "\n")


def collect_code_text():
    """Raw text of all Python sources, to verify clean keys are real literals."""
    parts = []
    for path in [REPO / "main.py", REPO / "run.py"]:
        if path.exists():
            parts.append(path.read_text(encoding="utf-8", errors="replace"))
    for path in sorted((REPO / "src").rglob("*.py")):
        parts.append(path.read_text(encoding="utf-8", errors="replace"))
    return "\n".join(parts)


def transform(data, translations, lang):
    """Rebuilds the dict in key order: mangled -> clean translated entry,
    truncated key -> full translated entry, orphans dropped."""
    new = {}
    for key, value in data.items():
        if key == value and MANGLED_RE.search(key):
            clean = clean_of(key)
            if clean not in new:
                new[clean] = translations[clean]
            continue
        if key == TRUNCATED_KEY:
            new[FULL_MCP_KEY] = translations[FULL_MCP_KEY]
            continue
        if key in ORPHAN_KEYS:
            continue
        new[key] = value
    return new


def insert_stage_key(data, reference, value):
    """Inserts the stage-error key into es/fr mirroring es_es/fr_fr, keeping the
    same relative position (before its successor in the reference file)."""
    keys = list(reference.keys())
    idx = keys.index(STAGE_ERROR_KEY)
    successor = keys[idx + 1] if idx + 1 < len(keys) else None
    if successor in data:
        insert_before = successor
    else:
        insert_before = None
    out = {}
    inserted = False
    for key, v in data.items():
        if not inserted and key == insert_before:
            out[STAGE_ERROR_KEY] = value
            inserted = True
        out[key] = v
    if not inserted:
        out[STAGE_ERROR_KEY] = value
    return out


def main():
    data = {name: load_json(LANGS_DIR / name) for name in LANG_FILES}

    # --- Pre-conditions ---------------------------------------------------
    mangled_sets = []
    for name in LANG_FILES:
        mangled = {k for k, v in data[name].items() if k == v and MANGLED_RE.search(k)}
        assert len(mangled) == 51, f"{name}: expected 51 mangled keys, found {len(mangled)}"
        mangled_sets.append(mangled)
    assert len({frozenset(s) for s in mangled_sets}) == 1, "mangled key sets differ across files"

    clean_keys = {clean_of(m) for m in mangled_sets[0]}
    assert len(clean_keys) == 50, f"expected 50 distinct clean keys, found {len(clean_keys)}"
    for name in LANG_FILES:
        assert clean_keys.isdisjoint(data[name]), f"{name}: clean key already exists"

    for name in LANG_FILES:
        assert TRUNCATED_KEY in data[name], f"{name}: truncated key missing"
    for name in ("es_es.json", "fr_fr.json", "pt_br.json", "pt_pt.json"):
        assert STAGE_ERROR_KEY in data[name], f"{name}: stage-error key missing"
    for name in ("es.json", "fr.json"):
        assert STAGE_ERROR_KEY not in data[name], f"{name}: stage-error key unexpectedly present"
    for name in LANG_FILES:
        for orphan in ORPHAN_KEYS:
            assert orphan in data[name], f"{name}: orphan {orphan!r} missing"

    # --- Translation tables ------------------------------------------------
    mined = mine_translations()
    assert "FR" in mined and "ES" in mined, "could not mine FR/ES dicts from sync_all_langs.py"

    fr = {k: mined["FR"][k] for k in clean_keys if k in mined["FR"] and mined["FR"][k] != k}
    es = {k: mined["ES"][k] for k in clean_keys if k in mined["ES"] and mined["ES"][k] != k}
    fr.update(FR_FRESH)
    es.update(ES_FRESH)
    missing_fr = clean_keys - set(fr)
    missing_es = clean_keys - set(es)
    assert not missing_fr, f"missing FR translations: {sorted(missing_fr)}"
    assert not missing_es, f"missing ES translations: {sorted(missing_es)}"

    mcp_fr = mined["FR"].get(FULL_MCP_KEY)
    mcp_es = mined["ES"].get(FULL_MCP_KEY)
    assert mcp_fr and mcp_fr != FULL_MCP_KEY, "FR dict lacks the full MCP key translation"
    assert mcp_es and mcp_es != FULL_MCP_KEY, "ES dict lacks the full MCP key translation"
    fr[FULL_MCP_KEY] = mcp_fr
    es[FULL_MCP_KEY] = mcp_es
    pt_br = dict(PT_BR)
    pt_pt = dict(PT_PT)
    pt_br[FULL_MCP_KEY] = MCP_TRANSLATIONS["pt_br"]
    pt_pt[FULL_MCP_KEY] = MCP_TRANSLATIONS["pt_pt"]
    assert clean_keys.issubset(pt_br) and clean_keys.issubset(pt_pt), "pt tables must cover all clean keys"

    tables = {
        "pt_br.json": pt_br, "pt_pt.json": pt_pt,
        "es_es.json": es, "es.json": es,
        "fr_fr.json": fr, "fr.json": fr,
    }

    # --- Transform ---------------------------------------------------------
    fixed = {}
    for name in LANG_FILES:
        fixed[name] = transform(data[name], tables[name], name)

    # es/fr: add the missing stage-error key mirroring es_es/fr_fr.
    fixed["es.json"] = insert_stage_key(fixed["es.json"], fixed["es_es.json"], data["es_es.json"][STAGE_ERROR_KEY])
    fixed["fr.json"] = insert_stage_key(fixed["fr.json"], fixed["fr_fr.json"], data["fr_fr.json"][STAGE_ERROR_KEY])

    # --- Post-conditions ----------------------------------------------------
    code_text = collect_code_text()
    for key in clean_keys:
        # Source files spell newlines as escape sequences, not real characters.
        source_form = key.replace("\n", "\\n")
        assert source_form in code_text, f"clean key not found as literal in code: {key!r}"
    for name in LANG_FILES:
        remaining = {k for k, v in fixed[name].items() if k == v and MANGLED_RE.search(k)}
        assert not remaining, f"{name}: mangled keys remain: {len(remaining)}"
        assert clean_keys.issubset(fixed[name]), f"{name}: missing clean keys"
        for key in clean_keys:
            assert fixed[name][key] != key, f"{name}: untranslated clean key {key!r}"
        assert TRUNCATED_KEY not in fixed[name], f"{name}: truncated key remains"
        assert FULL_MCP_KEY in fixed[name] and fixed[name][FULL_MCP_KEY] != FULL_MCP_KEY, f"{name}: MCP key issue"
        for orphan in ORPHAN_KEYS:
            assert orphan not in fixed[name], f"{name}: orphan {orphan!r} remains"
        assert STAGE_ERROR_KEY in fixed[name], f"{name}: stage-error key missing"
        assert len(fixed[name]) == EXPECTED_COUNT, f"{name}: count {len(fixed[name])} != {EXPECTED_COUNT}"
    key_sets = [set(fixed[name]) for name in LANG_FILES]
    assert all(s == key_sets[0] for s in key_sets), "key sets differ across files"

    # --- Write ---------------------------------------------------------------
    for name in LANG_FILES:
        with open(LANGS_DIR / name, "w", encoding="utf-8") as f:
            json.dump(fixed[name], f, indent=2, ensure_ascii=False)
            f.write("\n")
        print(f"{name}: {len(data[name])} -> {len(fixed[name])} keys "
              f"({len(mangled_sets[0])} mangled replaced, 2 orphans pruned)")

    print(f"OK: all 6 files now have {EXPECTED_COUNT} identical keys, all 50 clean keys translated.")


if __name__ == "__main__":
    main()
