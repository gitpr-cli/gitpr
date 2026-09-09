# Plano — Skill `.gitpr.release.md` (templates 5 idiomas) + ajustes do fluxo `gitpr release`

## Context

Tarefa nova (grill `/grill-with-docs` 2026-09-08, sobre a feature `gitpr release` já implementada na v1). O usuário pediu: criar a skill de release em `.gitpr/skill` com template em `templates/` em **5 idiomas** (EN + pt_br, pt_pt, es_es, fr_fr); instruções para gerar o release **editáveis pelo usuário**; **auto-download na primeira execução** do `release` respeitando o idioma (comportamento novo — as outras skills só baixam via `-s`); salvar resultado também em `.gitpr/reports/release`; **perguntar** quando a versão for sugerida; ~~verificar updater.py::__version__~~ (**CANCELADO pelo usuário** — a sugestão de versão permanece derivada de tags, como na v1).

Decisões do grill (rodadas 1–2, todas confirmadas):

| #   | Decisão                                                                                                                                                                                                                                                                                                                                                                                                              |
| --- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| R1  | 5 arquivos de template novos: `templates/gitpr.release.md` (EN) + `.pt_br/.pt_pt/.es_es/.fr_fr.md` (tradução manual inteira, padrão da família `gitpr.issue.*`)                                                                                                                                                                                                                                                      |
| R2  | Registrar `release` no downloader `-s` (`files_to_download` em `core.py:1106-1114`), com sufixo de idioma de `CURRENT_LANG`, nunca sobrescrevendo                                                                                                                                                                                                                                                                    |
| R3  | `.gitpr.release.md` = **system_instruction** do resumo executivo (único ponto de IA do fluxo), com fallback na persona embutida traduzida; `get_skill_context()` ganha `quiet=` (hoje o "🧠 File ... found and loaded!" via secho sujaria o stdout JSON)                                                                                                                                                              |
| R4  | **Auto-download na primeira execução do `release`**: se `.gitpr/skill/.gitpr.release.md` não existir → tenta baixar a variante do idioma (timeout curto, nunca lança, nunca sobrescreve, só línguas com template); em `--format json` NÃO baixa (contrato stdout-only "sem tocar arquivos"); mensagens = chaves existentes do `-s`. Local: camada CLI (`main.py`), nunca no engine (testes do engine não tocam rede) |
| R5  | Após o upsert do CHANGELOG.md da raiz (Q8 mantido), gravar **artefato por execução** em `.gitpr/reports/release/{branch}_{datetime}_RELEASE.md` (padrão das outras engines via `resolve_output_path` + nova chave `OUTPUT_FILE_NAME_RELEASE`); falha → warning amarelo não-fatal; json mode não escreve nada; upsert com erro → exit 1 antes do artefato                                                             |
| R6  | Sem `--version` e com sugestão: prompt interativo "❓ Use the suggested version {v}? [Y/n]" (default aceita); recusar → prompt para digitar outra (valida semver, laço); **silêncio em `--format json`/quiet e quando stdin não é TTY**; `--version` explícito pula; `auto_bump=false` mantém erro atual; prompt acontece **antes** da chamada de IA                                                                  |
| R7  | **Cancelado** — nenhuma leitura de `updater.py`/arquivos de versão (baseline = tags, v1 intacta)                                                                                                                                                                                                                                                                                                                     |
| R8  | MCP mínimo: `release` no `SKILL_FILES` (mcp_server.py:913-920) + handler `skill://release` (padrão dos demais, com name/description `__()`). SEM família `gitpr.prompt.release.*`, sem PROMPT_FILES                                                                                                                                                                                                                  |

## Mudanças por arquivo

### Novos — `templates/gitpr.release.md` + 4 variantes
Conteúdo EN (modelo = `gitpr.issue.md`): sem frontmatter; abertura de persona "You are a Release Manager responsible for writing the executive summary of a software release for the project CHANGELOG."; contrato rígido `You MUST ONLY return a valid JSON object in the following format: {"summary": "..."}` (chave `summary` fixa, **não traduzida**); regras: idioma conforme o pedido do usuário; foco em impacto para o usuário final; linguagem de changelog concisa, nunca inventar fatos; NUNCA identificadores de código (nomes de variáveis/arquivos/funções/hashes); parágrafo único de 3–6 frases, sem listas; descrever somente os commits listados (1 por linha, mais recentes primeiro — exatamente o formato do prompt do engine, release_engine.py:175-186). Traduções inteiras por arquivo (vozes: pt_br informal, pt_pt europeu — "utilizadores/linguagem especificada", es_es — "Eres un Release Manager responsable...", fr_fr — "Vous êtes un Release Manager chargé de rédiger..."). Nenhum `{placeholder}`, nenhuma chave i18n.

### Edit — `src/core.py`
- `get_skill_context(action_type="pr", quiet=False)` (650-703): entrada explícita `elif action_type == "release": target_file = ".gitpr.release.md"` (o `else` → `.gitpr.review.md` permanece); envolver os 2 `click.secho` (684-690, 693-700) em `if not quiet:`.
- `_OUTPUT_FOLDER_MAP` (412-420): `"OUTPUT_FILE_NAME_RELEASE": "release",`.
- **Novo** `download_skill_file(local_name, remote_name, timeout=5, warn_on_exists=True, quiet=False)` — helper único por arquivo (resolve_skill_path; existe → mensagem amarela existente e `return False`, nunca sobrescreve; urlopen base `_SKILL_BASE_URL` constante extraída de 1095; escreve `encoding="utf-8", errors="replace"` — a linha atual 1142 não tem `errors`, corrige-se no movimento; mensagens iguais às atuais: "Downloading {local_name}...", "❌ Network error...", "❌ Failed to process..."; **nunca lança**; retorna True só quando baixou).
- `generate_skill_template()` (1086-1182): corpo do laço (1122-1164) vira chamada a `download_skill_file` (contagem preservada); `files_to_download` ganha `".gitpr.release.md": f"gitpr.release{lang_suffix}.md"`; banners finais inalterados.
- **Novo** `ensure_release_skill_template(quiet=False)`: gate de idioma suportado (`""`, `.pt_br`, `.pt_pt`, `.es_es`, `.fr_fr` — evita 404 ruidosos em locales arbitrários), chama `download_skill_file(".gitpr.release.md", f"gitpr.release{lang_suffix}.md", timeout=3, warn_on_exists=False, quiet=quiet)`.

### Edit — `src/config.py`
- `DEFAULT_CONFIG` (16-62), após `"OUTPUT_FILE_NAME_LINTER"`: `"OUTPUT_FILE_NAME_RELEASE": "{branch}_{datetime}_RELEASE.md",`. `get_release_settings()` inalterado.

### Edit — `src/release_engine.py`
- Imports: `import sys`; `from src.core import get_skill_context` (sem ciclo — core não importa release_engine).
- `_generate_summary()` (206-270): `skill_context = get_skill_context("release", quiet=quiet)`; se vazio → persona atual `__("You are a Release Manager. ...")` (fallback preservado). (Cache continua keyed no prompt — sem impacto.)
- `generate_release_notes(...)`: parâmetro aditivo `ask_version=False` após `auto_bump=True`. No ramo da sugestão (347-354), após o "📈 Suggested version: ...": `if ask_version and not quiet and _stdin_is_interactive(): target_version = _ask_about_suggested_version(suggestion)`.
- **Novos helpers** (acima de `generate_release_notes`): `_stdin_is_interactive()` (try/isatty, exc → False) e `_ask_about_suggested_version(suggestion)`: `click.confirm(__("❓ Use the suggested version {version}?"), default=True)` → aceita; senão laço `click.prompt(__("✏️ Type another version (semantic versioning, ex.: 1.2.3)"))`, valida `parse_semver_tag` (aceita `v`, limpa espaços), erro de validação reutiliza a chave existente "❌ Invalid target version '{version}'...".

### Edit — `src/main.py`
- Import top-level de `ensure_release_skill_template` (bloco `from src.core import` ~25-40).
- Docstring do `release` (1656-1668): 1 frase sobre o auto-download da skill e o papel de system instruction.
- Corpo (após avisos 1686-1697, antes do `try:` 1699): `if not json_mode: ensure_release_skill_template()`.
- Chamada de `generate_release_notes` (1700-1707): `ask_version=not json_mode`.
- Artefato R5 (após mensagem de status 1734-1745, antes do `echo("")` 1747): bloco try/except best-effort — `get_current_branch()` → branch safe (`/` `\` → `-`) → `resolve_output_path("OUTPUT_FILE_NAME_RELEASE", "{branch}_{datetime}_RELEASE.md", safe_branch, datetime.now().strftime("%Y%m%d%H%M%S"))` → escreve `result.markdown` (`errors="replace"`) → `click.secho(__("📄 Release notes artifact saved to: {path}"), fg="blue", dim=True)`; except → `__("⚠️ Warning: Could not save the release notes artifact: {error}")` amarelo, não relança. (Imports já existentes em main.py: `get_current_branch`, `resolve_output_path`, `os`, `datetime`.)

### Edit — `src/mcp_server.py`
- `SKILL_FILES` (913-920): `"release": ".gitpr.release.md",`.
- Novo handler após `get_skill_blame` (1083-1090): `@mcp.resource(uri="skill://release", name=__("Release Notes Template"), description=__("Custom AI instructions for the gitpr release executive summary."), mime_type="text/markdown")` → `_read_resource_file(".gitpr.release.md")`. (`skill://list` já deriva de SKILL_FILES — ganha a entrada automaticamente.)

### Novas chaves i18n (adicionar e traduzir nos 6 arquivos: pt_br, pt_pt, es_es, es, fr_fr, fr — paridade obrigatória; chaves com `{}` NÃO podem ficar identity)
1. `❓ Use the suggested version {version}?`
2. `✏️ Type another version (semantic versioning, ex.: 1.2.3)`
3. `📄 Release notes artifact saved to: {path}`
4. `⚠️ Warning: Could not save the release notes artifact: {error}`
5. `Release Notes Template` (MCP name; modelo: "Issue Template")
6. `Custom AI instructions for the gitpr release executive summary.` (MCP description)

Reuso (sem chaves novas): mensagens do `-s` (R4), "🧠 File ... found and loaded!"/"⚠️ Warning: Failed to read file..." (R3), "❌ Invalid target version..." (R6). Processo: editar fontes → `python tests/sync_i18n.py` (uma vez) → traduzir as 6 chaves manualmente → não rodar o sync de novo.

### Docs (cirúrgico)
- `CLAUDE.md`: tipos de skill (+release, ~L274), árvore `templates/` (+5 linhas gitpr.release*), recursos MCP "16"→"17" e lista `skill://{...}` +release (~L379), lista de env (~L288, opcional).
- `docs/skill-template.md`: tabela de consumo + `.gitpr.release.md` e linha `gitpr release`.
- **Entregáveis obrigatórios**: `docs/survey/20260908_skill_release_template_surveyfacts.md` (contexto, tabela R1–R8, relatório de fatos) e relatório de conclusão `docs/claude-code/reports/develop_natan/2026-09-08_skill_release_template.md`.

## Testes
- `tests/test_release_engine.py` (estender, idioma do arquivo): skill como system_instruction (conteúdo custom vs fallback persona; quiet carrega sem mensagem); prompt R6 (aceitar; recusar+digitar; laço até válido; não-TTY → sem prompt; `ask_version=False` default; quiet → sem prompt) — patchear `click.confirm/click.prompt` e `sys.stdin` isatty.
- `tests/test_skill_command.py` (estender): `-s` inclui `gitpr.release.md` (EN e sufixo `.pt_br` com `CURRENT_LANG` patchado).
- `tests/test_skill_context.py` (novo, unittest): `get_skill_context("release")` → `.gitpr.release.md`; unknown action continua review; `quiet=True` suprime mensagens.
- `tests/test_release_cli.py` (novo, CliRunner): markdown baixa skill + escreve changelog + artefato (conteúdo == `result.markdown`); upsert falha → exit 1 sem artefato; json puro (sem download/escrita); `ask_version` propagado (`True` markdown / `False` json).
- `tests/test_mcp_server.py` (estender): `skill://release` em `list_skills`, handler existe, missing file → not_found JSON.

## Fora de escopo
- R7 (nada de updater.py); família `gitpr.prompt.release.*`; traduzir as demais skills; corrigir staleness não relacionado (URLs antigas em docs, árvore de templates, docs do .env); os 6 testes pré-existentes quebrados (locale/EN e timeout) — não corrigir.

## Verificação
1. `python -m pytest tests/test_release_engine.py tests/test_skill_command.py tests/test_skill_context.py tests/test_release_cli.py tests/test_mcp_server.py tests/test_i18n.py -q` verdes.
2. Smoke E2E em **cópia temporária** do repo (não no gitpr real — o smoke criaria `.gitpr/skill/.gitpr.release.md` e viciaria os testes de engine com arquivo real): `gitpr release` (1ª execução baixa a skill no idioma, prompt de versão, grava CHANGELOG.md na raiz + artefato em `.gitpr/reports/release/`); 2ª execução sem re-baixar; `--format json` → stdout parseia como JSON puro e não toca arquivos; versão duplicada sem `--force` → exit 1 e sem artefato.
3. Suíte completa: apenas as **6 falhas pré-existentes conhecidas** (nada novo). `gitpr-mcp --list` contém `skill://release`.
4. Nenhum `git commit/add/push` — tudo na working tree.
