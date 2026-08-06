#!/usr/bin/env python3
"""Fix pt_br.json: translate all untranslated keys and handle corrupted keys."""
import json, re, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

with open("langs/pt_br.json", "r", encoding="utf-8", errors="replace") as f:
    data = json.load(f)

# ============================================================
# PART 1: Fix 34 corrupted keys — use same translation as clean version
# ============================================================
corrupted_map = {}
for key, value in data.items():
    if key == value and re.search(
        r'\)\s*,|fg\s*=\s*\"|provider\s*=\s*|error\s*=\s*str|count\s*=\s*len'
        r'|n\s*=\s*self|severity\s*=\s*\"|file_name\s*=\s*nome'
        r'|hook_name\s*=\s*hook|local_name\s*=\s*local'
        r'|filename\s*=\s*filename|active_provider|repo_name\s*=\s*repo'
        r'|input\s*=\s*input|rule_name\s*=\s*rule',
        key,
    ):
        clean = re.sub(r'",\s*\w+\s*=\s*.*$', "", key)
        corrupted_map[key] = clean

fixed_corrupted = 0
for bad_key, clean_key in corrupted_map.items():
    if clean_key in data and data[clean_key] != clean_key:
        data[bad_key] = data[clean_key]  # use existing translation
        fixed_corrupted += 1
    elif clean_key in data:
        # clean key exists but is also untranslated — will be handled in part 2
        pass
    else:
        # clean key doesn't exist — add it, will be translated in part 2
        data[clean_key] = clean_key

print(f"Corrupted keys fixed (synced with clean version): {fixed_corrupted}")

# ============================================================
# PART 2: Translate all untranslated keys (key == value, still English)
# ============================================================

translations = {
    # --- File names (stay as-is, these are module identifiers) ---
    # core.py, main.py, blame_engine.py, etc. — intentionally English

    # --- Short UI labels ---
    "Auto-Patch": "Auto-Patch",
    "Auto-Patch Msg": "Msg Auto-Patch",
    "Available Prompt Templates": "Templates de Prompt Disponíveis",
    "Blame Prompt": "Prompt de Blame",
    "Commit Message Prompt": "Prompt de Mensagem de Commit",
    "Entries": "Entradas",
    "Explore Prompt": "Prompt de Explorar",
    "F5 refresh": "Atualização F5",
    "Issue Prompt": "Prompt de Issue",
    "Language Override (--lang)": "Substituição de Idioma (--lang)",
    "Linter Prompt": "Prompt de Linter",
    "No message": "Sem mensagem",
    "PR Description Prompt": "Prompt de Descrição de PR",
    "Provider": "Provedor",
    "Providers": "Provedores",
    "Review PR Prompt": "Prompt de Revisão de PR",
    "Scanning cache files...": "Analisando arquivos de cache...",
    "Skipped.\n": "Pulado.\n",
    "Status": "Status",
    "Timestamp": "Timestamp",
    "Tokens": "Tokens",
    "Tokens (cache)": "Tokens (cache)",
    "Total duration": "Duração total",
    "Total entries": "Total de entradas",
    "Unknown": "Desconhecido",
    "\n📝 Commit Suggestion:\n": "\n📝 Sugestão de Commit:\n",
    "new entries": "novas entradas",

    # --- MCP / Prompt strings ---
    "Lists all available MCP prompt template URIs.": "Lista todos os URIs de templates de prompt MCP disponíveis.",
    "Prompt template: explore project context and available skills.": "Template de prompt: explorar o contexto do projeto e skills disponíveis.",
    "Prompt template: full code review of the current branch.": "Template de prompt: revisão completa de código da branch atual.",
    "Prompt template: generate a Conventional Commits message.": "Template de prompt: gerar uma mensagem Conventional Commits.",
    "Prompt template: generate a Pull Request description.": "Template de prompt: gerar uma descrição de Pull Request.",
    "Prompt template: generate a structured issue from changes.": "Template de prompt: gerar uma issue estruturada das alterações.",
    "Prompt template: run the static linter on changes.": "Template de prompt: executar o linter estático nas alterações.",
    "Prompt template: trace code origin with git blame + AI.": "Template de prompt: rastrear origem de código com git blame + IA.",
    "Opens the interactive metrics dashboard (TUI).": "Abre o dashboard interativo de métricas (TUI).",
    "Start the MCP server for integration with VS Code, Cursor, Claude Desktop, etc.": "Inicia o servidor MCP para integração com VS Code, Cursor, Claude Desktop, etc.",
    "Forces the interface language for this execution (e.g.: en_us, pt_br).": "Força o idioma da interface para esta execução (ex.: en_us, pt_br).",
    "Forces the interface language for this execution (e.g.: en_us, pt_br). Overrides the GITPR_LANG environment variable and OS locale detection.": "Força o idioma da interface para esta execução (ex.: en_us, pt_br). Sobrescreve a variável GITPR_LANG e a detecção de idioma do SO.",

    # --- GitHub / Token ---
    "Token expired or invalid. Please generate a new one.": "Token expirado ou inválido. Gere um novo.",
    "No internet connection. Cannot validate GitHub token.": "Sem conexão com a internet. Não é possível validar o token do GitHub.",
    "GitHub API timeout. Check your connection and try again.": "Timeout da API do GitHub. Verifique sua conexão e tente novamente.",
    "✅ GitHub token is valid!\n": "✅ Token do GitHub é válido!\n",
    "✅ Token encrypted and safely saved in .env!": "✅ Token encriptado e salvo com segurança no .env!",
    "🔍 Validating GitHub token...": "🔍 Validando token do GitHub...",
    "🔍 Validating new token...": "🔍 Validando novo token...",
    "🔐 GitHub token expired or invalid. You'll be prompted for a new one.": "🔐 Token do GitHub expirado ou inválido. Você será solicitado a gerar um novo.",
    "🔐 No GitHub token found.": "🔐 Nenhum token do GitHub encontrado.",
    "🗑️  Expired token removed. Let's configure a new one.": "🗑️  Token expirado removido. Vamos configurar um novo.",
    "🔄 Let's try again...\n": "🔄 Vamos tentar novamente...\n",

    # --- Setup Wizard (these duplicate existing keys with slight formatting diffs) ---
    "\nStep 2 of 4: Git Hooks": "\nEtapa 2 de 4: Git Hooks",
    "\nStep 3 of 4: MCP Configuration": "\nEtapa 3 de 4: Configuração MCP",
    "\nStep 4 of 4: API Key Configuration": "\nEtapa 4 de 4: Configuração da Chave de API",
    "\n✅ Setup wizard complete!": "\n✅ Assistente de configuração concluído!",
    "\n✅ Base templates successfully configured!": "\n✅ Templates base configurados com sucesso!",
    "\n✅ Clean code! No violations found by the local Linter.": "\n✅ Código limpo! Nenhuma violação encontrada pelo Linter local.",
    "\n✅ Code approved with warnings. The commit will proceed.": "\n✅ Código aprovado com avisos. O commit prosseguirá.",
    "\n❌ Error: No internet connection.": "\n❌ Erro: Sem conexão com a internet.",
    "\n❌ Error: The --input (-i) option can only be used with --review (-r) or --fullreview (-f).": "\n❌ Erro: A opção --input (-i) só pode ser usada com --review (-r) ou --fullreview (-f).",
    "\n📊 Local Telemetry Summary": "\n📊 Resumo da Telemetria Local",
    "\n📥 Starting GitPR templates configuration...": "\n📥 Iniciando configuração dos templates do GitPR...",
    "\n🔍 Starting Code Archeology...": "\n🔍 Iniciando Arqueologia de Código...",
    "\n🔐 GitHub Authentication Required": "\n🔐 Autenticação do GitHub Necessária",
    "\n🔧 Starting GitPR Interactive Setup Wizard...": "\n🔧 Iniciando Assistente de Configuração Interativa do GitPR...",
    "\nNo new files were downloaded.": "\nNenhum arquivo novo foi baixado.",
    "\n⚠️ No history found for this branch.\n": "\n⚠️ Nenhum histórico encontrado para esta branch.\n",
    "\n⚠️ No new code found. Make some changes before generating the issue.\n": "\n⚠️ Nenhum código novo encontrado. Faça alterações antes de gerar a issue.\n",
    "\n⚠️ No new code found. Make some changes before starting the chat.\n": "\n⚠️ Nenhum código novo encontrado. Faça alterações antes de iniciar o chat.\n",
    "\n⚠️ No new code found. Make some changes or check your branch before running the command.\n": "\n⚠️ Nenhum código novo encontrado. Faça alterações ou verifique sua branch antes de executar o comando.\n",
    "\n⚠️ No traceable history to feed the issue.\n": "\n⚠️ Nenhum histórico rastreável para alimentar a issue.\n",

    # --- Generic messages ---
    "Check your connection and try again.\n": "Verifique sua conexão e tente novamente.\n",
    "This wizard will guide you through the essential GitPR setup steps.\n": "Este assistente irá guiá-lo pelas etapas essenciais de configuração do GitPR.\n",
    "✅ Update successfully completed! You will use the new version on the next run.\n": "✅ Atualização concluída com sucesso! Na próxima execução você usará a nova versão.\n",
    "📚 Read the complete TUI interface usage guide:\n": "📚 Leia o guia completo de uso da interface TUI:\n",
    "You can now open the generated files in '.gitpr/skill/' and customize the tool's behavior for your project:\n": "Você pode agora abrir os arquivos gerados em '.gitpr/skill/' e personalizar o comportamento da ferramenta para o seu projeto:\n",
    "Downloads template files (.gitpr.*.md and .gitpr.linter.yml) from the official repository into the project's .gitpr/skill/ folder. These files allow customizing the AI behavior according to your team's rules. NEVER overwrites existing local files.": "Faz download dos arquivos de template (.gitpr.*.md e .gitpr.linter.yml) do repositório oficial para a pasta .gitpr/skill/ do projeto. Estes arquivos permitem personalizar o comportamento da IA conforme as regras da sua equipe. NUNCA sobrescreve arquivos locais existentes.",

    # --- Escape-sequence variants (duplicates with \\n vs \n) ---
    "  1. Architecture rules for AI in '.gitpr/skill/.gitpr.pr.md' and '.gitpr/skill/.gitpr.review.md'\n": "  1. Regras de arquitetura para IA no arquivo '.gitpr/skill/.gitpr.pr.md' e '.gitpr/skill/.gitpr.review.md'\n",
    "  2. Local regex rules in '.gitpr/skill/.gitpr.linter.yml'\n": "  2. Regras de regex locais no arquivo '.gitpr/skill/.gitpr.linter.yml'\n",
    "  Options: -c,--commit | -r,--review | -f,--fullreview | -l,--linter | -s,--skill | -u,--update | -ih,--installhooks | --install | -is,--issue | -h,--help (use -h --flag for contextual help)\n": "  Opções: -c,--commit | -r,--review | -f,--fullreview | -l,--linter | -s,--skill | -u,--update | -ih,--installhooks | --install | -is,--issue | -h,--help (use -h --flag para ajuda contextual)\n",
    "# Timeline of the investigated rule\n\n": "# Linha do tempo da regra investigada\n\n",
    "# 🚀 Pull Request Suggestion\n\n**Recommended Commit Message:**\n": "# 🚀 Sugestão de Pull Request\n\n**Mensagem de Commit Recomendada:**\n",
    "## 🚨 Local Static Analysis Alerts (YAML Rules)\n\n": "## 🚨 Alertas de Análise Estática Local (Regras YAML)\n\n",
    "=== AI PR HISTORY ===\n": "=== HISTÓRICO DE PRs DA IA ===\n",
    "=== AI PR HISTORY ===\nNo previous AI-generated PR found in cache for this branch.\n": "=== HISTÓRICO DE PRs DA IA ===\nNenhum PR anterior gerado por IA encontrado em cache para esta branch.\n",
    "=== REGISTERED COMMITS ===\n": "=== COMMITS REGISTRADOS ===\n",
    "\n>> Tip: Use without --commit to generate the full PR.\n": "\n>> Dica: Use sem --commit para gerar o PR completo.\n",
    "\n---\n\n## 🤖 AI Code Review\n\n": "\n---\n\n## 🤖 Code Review da IA\n\n",
    "| Data | Commit | Author | What |\n": "| Data | Commit | Autor | O quê |\n",
    "• Esc (Exit): Closes the application without saving.\n\n": "• Esc (Sair): Fecha o aplicativo sem salvar.\n\n",
    "• F1 (Help): Displays this instruction modal.\n": "• F1 (Ajuda): Exibe este modal de instruções.\n",
    "• F2 (Save Local): Generates a Markdown (.md) file with the issue.\n": "• F2 (Salvar Local): Gera um arquivo Markdown (.md) com a issue.\n",
    "• F3 (Create on GitHub): Creates the issue remotely via API.\n": "• F3 (Criar no GitHub): Cria a issue remotamente via API.\n",
    "No exclusive commits found in this branch.\n\n": "Nenhum commit exclusivo encontrado nesta branch.\n\n",

    # --- AI prompt templates (long strings that are sent to AI) ---
    "Generate ONLY a JSON object in the format {json_format} for the commit message, unifying these technical summaries:\n\", json_format='{\"commit_message\": \"...\"}": "Gere APENAS um objeto JSON no formato {json_format} para a mensagem de commit, unificando estes resumos técnicos:\n\", json_format='{\"commit_message\": \"...\"}",
    "Generate ONLY a JSON object in the format {json_format} for this diff:\n\", json_format='{\"commit_message\": \"...\", \"pr_description\": \"...\"}": "Gere APENAS um objeto JSON no formato {json_format} para este diff:\n\", json_format='{\"commit_message\": \"...\", \"pr_description\": \"...\"}",
    "Generate ONLY a JSON object in the format {json_format} for this diff:\n\", json_format='{\"commit_message\": \"...\"}": "Gere APENAS um objeto JSON no formato {json_format} para este diff:\n\", json_format='{\"commit_message\": \"...\"}",
    "Generate ONLY a JSON object in the format {json_format} pointing out errors and improvements for this diff:\n\", json_format='{\"review\": \"...\"}": "Gere APENAS um objeto JSON no formato {json_format} apontando erros e melhorias para este diff:\n\", json_format='{\"review\": \"...\"}",
    "Generate ONLY a JSON object in the format {json_format} with a code review focused on improvements, using these summaries:\n\", json_format='{\"review\": \"...\"}": "Gere APENAS um objeto JSON no formato {json_format} com code review focado em melhorias, usando estes resumos:\n\", json_format='{\"review\": \"...\"}",
    "Generate ONLY a JSON object in the format {json_format} with the analysis and improvements for the entire code of this file:\n\", json_format='{\"review\": \"...\"}": "Gere APENAS um objeto JSON no formato {json_format} com análise e melhorias para o código integral deste arquivo:\n\", json_format='{\"review\": \"...\"}",
    "Unify these technical summaries and generate ONLY a JSON object in the format {json_format} describing the Pull Request:\n\", json_format='{\"commit_message\": \"...\", \"pr_description\": \"...\"}": "Unifique estes resumos técnicos e gere APENAS um objeto JSON no formato {json_format} descrevendo o Pull Request:\n\", json_format='{\"commit_message\": \"...\", \"pr_description\": \"...\"}",
    "Generate a Conventional Commits message (e.g., 'feat: add user auth": "Gera uma mensagem no padrão Conventional Commits (ex.: 'feat: add user auth",
    "You are a Software Architect. Analyze the diff and determine if it is the ORIGIN of the rule (new logic) or REFACTORING. Respond ONLY with JSON: {\"status\": \"ORIGIN\", \"reason\": \"Explain what was introduced\"} or {\"status\": \"REFACTORING\", \"reason\": \"Explain what was changed\"}": "Você é um Arquiteto de Software. Analise o diff e determine se é a ORIGEM da regra (lógica nova) ou REFATORAÇÃO. Responda APENAS com JSON: {\"status\": \"ORIGIN\", \"reason\": \"Explique o que foi introduzido\"} ou {\"status\": \"REFACTORING\", \"reason\": \"Explique o que foi alterado\"}",
    "Based on the following commit timeline of a business rule, write a single paragraph summarizing the age of the rule, the original author, the number of refactorings, and deduce what the original business intention was (the real reason the rule exists in the system).\n\n": "Baseado na seguinte linha do tempo de commits de uma regra de negócio, escreva um único parágrafo resumindo a idade da regra, o autor original, o número de refatorações e deduza qual era a intenção original de negócio (o motivo real da regra existir no sistema).\n\n",

    # --- Metrics strings ---
    "No metrics data found in ~/.gitpr/cache/prompts/": "Nenhum dado de métrica encontrado em ~/.gitpr/cache/prompts/",
    "| Data | Commit | Author | What |\n": "| Data | Commit | Autor | O quê |\n",
}

# Apply all translations
applied = 0
for key, ptbr in translations.items():
    if key in data:
        if data[key] == key:  # only overwrite if untranslated
            data[key] = ptbr
            applied += 1
    # else: key not in data, skip (was probably a corrupted key we don't need to add)

print(f"Translations applied: {applied}")

# ============================================================
# PART 3: Final count of remaining untranslated
# ============================================================
remaining = sum(1 for k, v in data.items() if k == v and not re.match(r'^[a-z_]+\.py$', k))
print(f"Remaining untranslated (excluding .py filenames): {remaining}")

# Write updated file
with open("langs/pt_br.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"\nTotal keys in pt_br.json: {len(data)}")
print("Done!")
