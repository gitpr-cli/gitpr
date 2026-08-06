#!/usr/bin/env python3
"""Fix remaining untranslated keys in pt_br.json — handles newline escaping properly."""
import json, re, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

with open("langs/pt_br.json", "r", encoding="utf-8", errors="replace") as f:
    data = json.load(f)

# Step 1: Sync corrupted duplicates from clean versions
corrupted_fixes = {}
for key, value in data.items():
    if key != value:
        continue
    if re.match(r'^[a-z_]+\.py$', key):
        continue
    # Keys with embedded Python kwargs after the string
    if '", error=str(e)), fg="red' in key or '", count=len(initial_commits)), fg="green' in key \
            or '", provider=provider.capitalize()), fg="cyan' in key \
            or '", json_format=' in key or '",json_format=' in key:
        # Find the clean version
        idx = key.index('",')
        clean = key[:idx]
        if clean in data and data[clean] != clean:
            corrupted_fixes[key] = data[clean]

for k, v in corrupted_fixes.items():
    data[k] = v
print(f"Corrupted keys synced with clean version: {len(corrupted_fixes)}")

# Step 2: Direct translations for all remaining untranslated keys
# Using exact key matching from the JSON file
translations = {}

# Build the list by checking what's still untranslated
for key, value in list(data.items()):
    if key != value:
        continue
    if re.match(r'^[a-z_]+\.py$', key):
        continue
    # Already handled
    if key in corrupted_fixes:
        continue

    # Build translation based on known patterns
    t = None

    # Escape-sequence variants (\\n in JSON = literal \n in Python string)
    if key == "  1. Architecture rules for AI in '.gitpr/skill/.gitpr.pr.md' and '.gitpr/skill/.gitpr.review.md'\\n":
        t = "  1. Regras de arquitetura para IA no arquivo '.gitpr/skill/.gitpr.pr.md' e '.gitpr/skill/.gitpr.review.md'\\n"
    elif key == "  2. Local regex rules in '.gitpr/skill/.gitpr.linter.yml'\\n":
        t = "  2. Regras de regex locais no arquivo '.gitpr/skill/.gitpr.linter.yml'\\n"
    elif key.startswith("  Options: -c,--commit"):
        t = "  Opções: -c,--commit | -r,--review | -f,--fullreview | -l,--linter | -s,--skill | -u,--update | -ih,--installhooks | --install | -is,--issue | -h,--help (use -h --flag para ajuda contextual)\\n"
    elif key == "# Timeline of the investigated rule\\n\\n":
        t = "# Linha do tempo da regra investigada\\n\\n"
    elif key == "# 🚀 Pull Request Suggestion\\n\\n**Recommended Commit Message:**\\n":
        t = "# 🚀 Sugestão de Pull Request\\n\\n**Mensagem de Commit Recomendada:**\\n"
    elif key == "## 🚨 Local Static Analysis Alerts (YAML Rules)\\n\\n":
        t = "## 🚨 Alertas de Análise Estática Local (Regras YAML)\\n\\n"
    elif key == "=== AI PR HISTORY ===\\n":
        t = "=== HISTÓRICO DE PRs DA IA ===\\n"
    elif key.startswith("=== AI PR HISTORY ===\\nNo previous"):
        t = "=== HISTÓRICO DE PRs DA IA ===\\nNenhum PR anterior gerado por IA encontrado em cache para esta branch.\\n"
    elif key == "=== REGISTERED COMMITS ===\\n":
        t = "=== COMMITS REGISTRADOS ===\\n"
    elif key == "Auto-Patch":
        t = "Auto-Patch"
    elif key.startswith("Based on the following commit timeline"):
        t = "Baseado na seguinte linha do tempo de commits de uma regra de negócio, escreva um único parágrafo resumindo a idade da regra, o autor original, o número de refatorações e deduza qual era a intenção original de negócio (o motivo real da regra existir no sistema).\\n\\n"
    elif key == "Check your connection and try again.\\n":
        t = "Verifique sua conexão e tente novamente.\\n"
    elif key == "Skipped.\\n":
        t = "Pulado.\\n"
    elif key == "Status":
        t = "Status"
    elif key == "This wizard will guide you through the essential GitPR setup steps.\\n":
        t = "Este assistente irá guiá-lo pelas etapas essenciais de configuração do GitPR.\\n"
    elif key == "Timestamp":
        t = "Timestamp"
    elif key == "Tokens":
        t = "Tokens"
    elif key == "Tokens (cache)":
        t = "Tokens (cache)"
    elif key.startswith("You can now open the generated files in '.gitpr/skill/'"):
        t = "Você pode agora abrir os arquivos gerados em '.gitpr/skill/' e personalizar o comportamento da ferramenta para o seu projeto:\\n"
    elif key == "\\n---\\n\\n## 🤖 AI Code Review\\n\\n":
        t = "\\n---\\n\\n## 🤖 Code Review da IA\\n\\n"
    elif key == "\\n>> Tip: Use without --commit to generate the full PR.\\n":
        t = "\\n>> Dica: Use sem --commit para gerar o PR completo.\\n"
    elif key == "\\nNo new files were downloaded.":
        t = "\\nNenhum arquivo novo foi baixado."
    elif key == "\\nStep 2 of 4: Git Hooks":
        t = "\\nEtapa 2 de 4: Git Hooks"
    elif key == "\\nStep 3 of 4: MCP Configuration":
        t = "\\nEtapa 3 de 4: Configuração MCP"
    elif key == "\\nStep 4 of 4: API Key Configuration":
        t = "\\nEtapa 4 de 4: Configuração da Chave de API"
    elif key == "\\n⚠️ No history found for this branch.\\n":
        t = "\\n⚠️ Nenhum histórico encontrado para esta branch.\\n"
    elif key == "\\n⚠️ No new code found. Make some changes before generating the issue.\\n":
        t = "\\n⚠️ Nenhum código novo encontrado. Faça alterações antes de gerar a issue.\\n"
    elif key == "\\n⚠️ No new code found. Make some changes before starting the chat.\\n":
        t = "\\n⚠️ Nenhum código novo encontrado. Faça alterações antes de iniciar o chat.\\n"
    elif key == "\\n⚠️ No new code found. Make some changes or check your branch before running the command.\\n":
        t = "\\n⚠️ Nenhum código novo encontrado. Faça alterações ou verifique sua branch antes de executar o comando.\\n"
    elif key == "\\n⚠️ No traceable history to feed the issue.\\n":
        t = "\\n⚠️ Nenhum histórico rastreável para alimentar a issue.\\n"
    elif key == "\\n✅ Base templates successfully configured!":
        t = "\\n✅ Templates base configurados com sucesso!"
    elif key == "\\n✅ Clean code! No violations found by the local Linter.":
        t = "\\n✅ Código limpo! Nenhuma violação encontrada pelo Linter local."
    elif key == "\\n✅ Code approved with warnings. The commit will proceed.":
        t = "\\n✅ Código aprovado com avisos. O commit prosseguirá."
    elif key == "\\n✅ Setup wizard complete!":
        t = "\\n✅ Assistente de configuração concluído!"
    elif key == "\\n❌ Error: No internet connection.":
        t = "\\n❌ Erro: Sem conexão com a internet."
    elif key == "\\n❌ Error: The --input (-i) option can only be used with --review (-r) or --fullreview (-f).":
        t = "\\n❌ Erro: A opção --input (-i) só pode ser usada com --review (-r) ou --fullreview (-f)."
    elif key == "\\n📊 Local Telemetry Summary":
        t = "\\n📊 Resumo da Telemetria Local"
    elif key == "\\n📥 Starting GitPR templates configuration...":
        t = "\\n📥 Iniciando configuração dos templates do GitPR..."
    elif key == "\\n🔍 Starting Code Archeology...":
        t = "\\n🔍 Iniciando Arqueologia de Código..."
    elif key == "\\n🔐 GitHub Authentication Required":
        t = "\\n🔐 Autenticação do GitHub Necessária"
    elif key == "\\n🔧 Starting GitPR Interactive Setup Wizard...":
        t = "\\n🔧 Iniciando Assistente de Configuração Interativa do GitPR..."
    elif key == "| Data | Commit | Author | What |\\n":
        t = "| Data | Commit | Autor | O quê |\\n"
    elif key == "• Esc (Exit): Closes the application without saving.\\n\\n":
        t = "• Esc (Sair): Fecha o aplicativo sem salvar.\\n\\n"
    elif key == "• F1 (Help): Displays this instruction modal.\\n":
        t = "• F1 (Ajuda): Exibe este modal de instruções.\\n"
    elif key == "• F2 (Save Local): Generates a Markdown (.md) file with the issue.\\n":
        t = "• F2 (Salvar Local): Gera um arquivo Markdown (.md) com a issue.\\n"
    elif key == "• F3 (Create on GitHub): Creates the issue remotely via API.\\n":
        t = "• F3 (Criar no GitHub): Cria a issue remotamente via API.\\n"
    elif key == "✅ GitHub token is valid!\\n":
        t = "✅ Token do GitHub é válido!\\n"
    elif key == "✅ Update successfully completed! You will use the new version on the next run.\\n":
        t = "✅ Atualização concluída com sucesso! Na próxima execução você usará a nova versão.\\n"
    elif key == "📚 Read the complete TUI interface usage guide:\\n":
        t = "📚 Leia o guia completo de uso da interface TUI:\\n"
    elif key.startswith("🔄 Let's try again"):
        t = "🔄 Vamos tentar novamente...\\n"
    elif key == "No exclusive commits found in this branch.\\n\\n":
        t = "Nenhum commit exclusivo encontrado nesta branch.\\n\\n"
    elif key == "\\n❌ Error saving review: {error}":
        t = "\\n❌ Erro ao salvar o review: {error}"
    elif key == "\\n❌ Syntax error in .gitpr.linter.yml file:\\n{error}":
        t = "\\n❌ Erro de sintaxe no arquivo .gitpr.linter.yml:\\n{error}"
    elif key == "\\n❌ Unexpected error reading linter rules: {error}":
        t = "\\n❌ Erro inesperado ao ler as regras do linter: {error}"
    elif key == "✅ Found {count} commit(s) on the surface. Starting time travel...\\n":
        t = "✅ Encontrado(s) {count} commit(s) na superfície. Iniciando viagem no tempo...\\n"
    elif key == "🤖 GitPR is analyzing your code using {provider} ({model})...\\n":
        t = "🤖 O GitPR está analisando o seu código usando {provider} ({model})...\\n"
    elif key == "\\n📝 Commit Suggestion:\\n":
        t = "\\n📝 Sugestão de Commit:\\n"

    # AI prompt templates with embedded JSON (corrupted keys)
    elif "Generate ONLY" in key and ("json_format=" in key):
        idx = key.index('",')
        clean = key[:idx]
        if clean in data and data[clean] != clean:
            t = data[clean]

    # Download template strings
    elif key.startswith("Downloads template files (.gitpr.*.md and .gitpr.linter.yml) from the official repository into the project"):
        t = "Faz download dos arquivos de template (.gitpr.*.md e .gitpr.linter.yml) do repositório oficial para a pasta .gitpr/skill/ do projeto. Estes arquivos permitem personalizar o comportamento da IA conforme as regras da sua equipe. NUNCA sobrescreve arquivos locais existentes."

    # JSON response format strings
    elif key.startswith("You are a Software Architect. Analyze the diff and determine if it is the ORIGIN"):
        t = 'Você é um Arquiteto de Software. Analise o diff e determine se é a ORIGEM da regra (lógica nova) ou REFATORAÇÃO. Responda APENAS com JSON: {"status": "ORIGIN", "reason": "Explique o que foi introduzido"} ou {"status": "REFACTORING", "reason": "Explique o que foi alterado"}'

    elif key.startswith("Generate a Conventional Commits message (e.g."):
        t = "Gera uma mensagem no padrão Conventional Commits (ex.: 'feat: add user auth"

    if t and key in data:
        data[key] = t
        translations[key] = t

print(f"Translations applied: {len(translations)}")

# Step 3: Final count
remaining = sum(1 for k, v in data.items()
                if k == v and not re.match(r'^[a-z_]+\.py$', k))
print(f"Remaining untranslated: {remaining}")

if remaining > 0:
    print("\nStill untranslated:")
    for k in sorted(data):
        if k == data[k] and not re.match(r'^[a-z_]+\.py$', k):
            print(f"  [{k[:130]}]")

# Write
with open("langs/pt_br.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print(f"\nTotal keys: {len(data)}")
print("Done!")
