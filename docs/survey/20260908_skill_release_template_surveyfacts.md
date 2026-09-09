# Survey — Skill `.gitpr.release.md` (5 idiomas) + ajustes do fluxo `gitpr release`

- **Data:** 2026-09-08
- **Task:** `skill_release_template`
- **Skill de origem:** `grill-with-docs` (rodadas de perguntas 1–2)
- **Objeto:** feature `gitpr release` já implementada na v1 (código não commitado na working tree)

## Contexto da tarefa

Pedido original do usuário (verbatim):

> - Crie o arquivo com a skill `.gitpr.release.md` em `.gitpr/skill`
> - O arquivo deve ficar em: `templates\gitpr.release.md`
> - O arquivo de template da skill deve estar em 5 idiomas
> - O skill deve ter as instruções para gerar o release podendo ser alterado pelo usuário
> - Fazer o download, usando a flag release pela primeira vez, respeitando o idioma do usuário, como é feito nas outras skills
> - Quando rodar release salvar o resultado em `.gitpr/reports/release`
> - Quando for sugerir a versão bump, perguntar ao usuário se ele quer usar a sugerida ou informar outra
> - Verificar em `updater.py::__version__` para sugerir o bump da versão — **CANCELADO pelo usuário** na rodada 1 ("desconciderar esta opção, não olhar para updater.py")

## Decisões das rodadas (R1–R8)

| # | Decisão | Status |
|---|---------|--------|
| R1 | 5 arquivos de template novos: `templates/gitpr.release.md` (EN) + `.pt_br`, `.pt_pt`, `.es_es`, `.fr_fr` (tradução manual inteira, sem placeholders, sem chaves i18n) | Implementado |
| R2 | Registrar `release` no downloader `-s` (`files_to_download` em `core.py`), sufixo de idioma de `CURRENT_LANG`, nunca sobrescreve | Implementado |
| R3 | `.gitpr.release.md` = `system_instruction` do resumo executivo; `get_skill_context()` ganhou `quiet=` (silencia "🧠 ... found and loaded!" — obrigatório para stdout JSON) | Implementado |
| R4 | Auto-download na primeira execução do `release` (camada CLI em `main.py`, nunca no engine; NÃO roda em `--format json`; línguas limitadas a EN/pt_br/pt_pt/es_es/fr_fr; falha de rede não-fatal) | Implementado |
| R5 | Artefato por execução em `.gitpr/reports/release/{branch}_{datetime}_RELEASE.md` via `resolve_output_path` + chave `OUTPUT_FILE_NAME_RELEASE`; falha → warning amarelo não-fatal; erro de upsert → exit 1 **antes** do artefato | Implementado |
| R6 | Prompt interativo na versão sugerida (default aceita; recusar → digitar outra, validada por semver, laço); silêncio em json/quiet e stdin não-TTY; prompt **antes** da chamada de IA | Implementado |
| R7 | ~~Verificar `updater.py::__version__` para o bump~~ — **CANCELADO**: sugestão permanece derivada das tags git (baseline v1 intacta); nenhuma leitura de arquivos de versão | Cancelado |
| R8 | MCP mínimo: `release` no `SKILL_FILES` + handler `skill://release` (name/description via `__()`); SEM família `gitpr.prompt.release.*` | Implementado |

## Fatos levantados (relatório)

1. **Pipeline do release (v1):** commits entre a última tag alcançável e HEAD → classificação Conventional Commits → sugestão semver → (opcional) resumo executivo de IA → upsert no `CHANGELOG.md` da raiz. O único ponto de IA do fluxo é o resumo executivo — foi onde a skill se encaixou (R3).
2. **Naming local das skills:** download grava nomes locais SEM sufixo (`.gitpr.release.md`), remotos COM sufixo (`gitpr.release.pt_br.md`); base `https://raw.githubusercontent.com/natanfiuza/gitpr/main/templates/`.
3. **`CURRENT_LANG` é binding de módulo** capturado no import (`from src.i18n import CURRENT_LANG`) — `set_lang()` não o atualiza em módulos que já o importaram; testes precisam de `monkeypatch.setattr("src.core.CURRENT_LANG", ...)`.
4. **`call_ai_model` passa `system_instruction` POSICIONALMENTE** (args[4]) — testes capturam `args[4]`.
5. **Imports dentro da função `release()` (main.py)** — testes de CLI precisam patchear atributos de módulo (`src.release_engine.*`, `src.config.get_release_settings`); nomes importados no topo de main.py são patchados em `src.main.*`.
6. **`tests/sync_i18n.py` é DESTRUTIVO**: scanner por regex trunca chaves com concatenação implícita (`__("a " "b")`) que o AST de `tests/test_i18n.py` dobra corretamente. NUNCA rodar; adicionar chaves por edição JSON direta (indent=2, `ensure_ascii=False`).
7. **Sem ciclo de import:** `core.py` não importa `release_engine.py` — o `from src.core import get_skill_context` adicionado ao engine é seguro.
8. **Falha de IA no resumo não aborta o release** ("AI summary failed: changelog generated without a summary.") — relevante para o smoke test sem chave de API.
9. **Locales do template de release:** o download automático cobre apenas EN + pt_br/pt_pt/es_es/fr_fr (evita 404 em locales arbitrários). Vozes por arquivo: pt_br informal, pt_pt europeu ("utilizadores"), es_es/es idênticos, fr_fr tipografia francesa (" : ").
10. **Versão sugerida mantém o prefixo `v`** quando derivada de tag (`v1.2.3` + fix → sugestão `v1.2.4`; seção do changelog `## [v1.2.4]`); `--version` explícito aceita `1.0.0` sem `v`.
11. **MCP `--list` (CLI) tem catálogo estático espelhado** dos decorators — além do handler `skill://release` foi preciso adicionar a entrada estática em `_build_tools_catalog()` (recursos 16 → 17); `skill://list` (runtime) deriva de `SKILL_FILES` e ganha a entrada automaticamente.
12. **Dívida pré-existente (fora de escopo):** `tests/test_i18n.py::test_no_missing_keys` falha com 40 chaves "missing" na working tree — todas pertencem ao código release-v1 **não commitado** (ex.: "❓ Publish release {version} on {provider}?"), ausentes dos 6 arquivos `langs/*.json` desde antes desta tarefa (em HEAD a645def o teste passa). As 6 chaves novas desta tarefa foram adicionadas traduzidas nos 6 arquivos. Não traduzir as 40 (escopo).
