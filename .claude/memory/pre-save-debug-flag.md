---
name: pre-save-debug-flag
description: Flag oculta --pre-save que dumps payload completo da IA em JSON antes do envio
metadata:
  type: reference
  source: docs/claude-code/reports/develop_natan/2026-07-18_pre_save_option.md
  date: 2026-07-18
  branch: develop_natan
---

A flag oculta `--pre-save` (não aparece no `--help`) dumps o payload completo da IA
(system instruction + user prompt + provider/model + contagem de caracteres) em um
arquivo JSON no diretório atual ANTES de enviar a requisição ao modelo. A chamada
procede normalmente depois (save-and-continue, não dry-run).

Arquivo: `_{action}-{datetime}.json` — ex: `_pr_desc-20260718150334633166.json`.
Microssegundos no timestamp previnem colisões quando o blame engine faz várias chamadas.

A interceptação ocorre no choke point único em `src/ai_providers.py`, cobrindo
TODOS os engines: PR, commit, review, issue, blame (classification + summary) e chat TUI.

O toggle é feito via `set_pre_save()` (module-level), evitando propagar parâmetro
por todas as assinaturas de função. Em cache hit, NENHUM arquivo é gerado (correto:
não há payload outgoing para inspecionar).

**Why:** Criado para diagnosticar problemas com prompts muito grandes. As contagens
de caracteres (`system_instruction_chars`, `prompt_chars`, `total_chars`) foram
incluídas especificamente para esse fim.

**How to apply:**
1. `gitpr --pre-save` ativa o dump para todas as operações daquela execução
2. Para forçar dump quando há cache hit, limpar `~/.gitpr/cache/prompts/`
3. O dump acontece UMA vez antes do retry loop (retries reenviam payload idêntico)
4. Falha ao escrever o dump é silenciosa — ferramenta de debug nunca quebra o pipeline
5. Adicionar `action=` kwarg em novas chamadas a `call_ai_model()` para rastreabilidade
