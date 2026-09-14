# Completion Report — Comando `gitpr fix`: transformar apontamentos de review em patches revisáveis

## What was done

Executado o plano `docs/plans/20260913_skill_gitpr_fix_command_plan.md` (derivado da spec
`docs/plans/20260913_skill_gitpr_fix_command_spec.md`), com o levantamento do grill em
`docs/survey/20260913_skill_gitpr_fix_command_surveyfacts.md`.

O `gitpr fix` é **capacidade nova**, não generalização do chat: a investigação obrigatória (passo 0)
derrubou três premissas da spec — o chat nunca aplicou patch nenhum (F5 e `ctrl+s` gravam um `.txt`
no CWD, sem `subprocess` e sem diff válido), finding com `id`/`severity`/`file_path` não existia em
lugar nenhum, e `config.schema.yml` nunca existiu. O pipeline real ficou: último review do cache →
**uma** chamada de IA (`call_ai_model`, nunca `generate_pr_content`, cujo `else` é o ramo de PR) →
`git apply --check` → classificação determinística → dry run ou escrita → histórico.

### 1. `src/fix/` — o pacote da feature (8 módulos, 1138 linhas)

| Módulo | Responsabilidade |
|---|---|
| `patch_provenance.py` | Contrato de dados puro: `PatchSafety`, `FindingRef`, `PatchCandidate` (com `patch_id` derivado), `PatchProvenance`, `ApplyFixResult` |
| `patch_extractor.py` | Blocos cercados + validação de diff unificado — **compartilhado com o chat** |
| `patch_safety_classifier.py` | `safe`/`review_required`/`experimental`, lógica pura, sem I/O e sem IA; devolve **código de motivo**, nunca frase |
| `patch_applier.py` | Primeiro invólucro de `git apply` do projeto (`--check`, `apply`, `--reverse`, `checkout -b`, `status`) |
| `fix_history.py` | `.gitpr/fix_history.json` — escrita atômica (`.tmp` + `os.replace`) |
| `apply_fix.py` | O caso de uso (470 linhas): review → IA → validar → classificar → dry-run/apply |
| `rollback_fix.py` | `git apply --reverse` sobre o diff guardado, com três recusas distintas |

O `__init__.py` é **só docstring** e ordena os módulos: `src/ui/chat_app.py` importa
`src.fix.patch_extractor` em toda sessão de chat, e um `__init__` que reexportasse arrastaria junto
as camadas de IA e de git (ver ADR-004, alternativa rejeitada).

### 2. `src/main.py` — o subcomando (+364 linhas)

`@cli.command(context_settings={"help_option_names": ["-h", "--help"]})`, no molde exato do
`release`, com imports lazy no corpo e `epilog` apontando para `get_doc_url("fix-command.md")`.
Nenhum flag existente mudou de sentido: `--force` do `release` ("regerar seção existente") não
colide, porque namespaces de subcomando são separados.

### 3. Chat — a única mudança em código que o usuário já usa

`src/ui/chat_app.py` perdeu 31 linhas e ganhou 3 (o bloco da regex estava duplicado em F5 e
`ctrl+s`) e passou a chamar `patch_extractor.extract_code_blocks()`. **Comportamento visível
idêntico**: mesmas teclas, mesmo `GITPR_PATCH_SUGGESTION_<key>.txt`, mesmo conteúdo. Por isso não
há nota de changelog sobre o chat.

### 4. Configuração, skill e MCP

- `GITPR_FIX_SAFE_MAX_LINES_CHANGED`, `GITPR_FIX_SAFE_EXCLUDED_PATHS`, `GITPR_FIX_REQUIRE_CONFIRMATION`,
  `GITPR_FIX_CREATE_BRANCH_ON_ALL_SAFE`, `GITPR_FIX_BRANCH_NAME_TEMPLATE` em `config.py` +
  `config_schema.py` (categoria própria na TUI de config, com `get_fix_settings()`).
- `templates/gitpr.fix.md` + `.pt_br.md` (persona: Senior Software Engineer), baixados por
  `gitpr --skill` — o `files_to_download` de `core.py` precisou da entrada, não só o
  `SKILL_FILES_BY_TYPE`.
- 13ª tool MCP `list_fix_candidates`, **somente leitura**, e o recurso `skill://fix`.
- Entrada `.gitpr/fix_history.json` no `templates/gitpr.smart-excludes.json`: um patch aplicado suja
  um arquivo **rastreado**, então sem isso ele apareceria nos diffs de `gitpr -c` e nas descrições de PR.

### 5. Documentação

`docs/fix-command.md` + 4 variantes de idioma (pt_br, pt_pt, es_es, fr_fr), 8 seções, no molde de
`release-notes.md`; uma linha no índice dos 5 READMEs; `docs/plans/glossary-gitpr-fix.md`
(vocabulário canônico) e `docs/plans/ADR-004-fix-subcommand-package.md` (por que o `fix` diverge do
ADR-003 no layout).

## Changed files

### Novos

| File | Change type | Description |
|------|-------------|-------------|
| `src/fix/patch_provenance.py` | feat | Contrato de dados (enums + dataclasses), sem I/O |
| `src/fix/patch_extractor.py` | feat | Extração de blocos cercados + validação de diff, compartilhado com o chat |
| `src/fix/patch_safety_classifier.py` | feat | Classificação determinística; código de motivo, não frase |
| `src/fix/patch_applier.py` | feat | Invólucro de `git apply` (`--check`/`apply`/`--reverse`/`checkout -b`) |
| `src/fix/fix_history.py` | feat | Histórico rastreado, escrita atômica |
| `src/fix/apply_fix.py` | feat | Caso de uso principal |
| `src/fix/rollback_fix.py` | feat | Desfazer um patch aplicado |
| `src/fix/__init__.py` | feat | Docstring que ordena os módulos; sem reexportações (ADR-004) |
| `templates/gitpr.fix.md`, `templates/gitpr.fix.pt_br.md` | feat | System instruction da normalização review → patches |
| `docs/fix-command.md` + `.pt_br/.pt_pt/.es_es/.fr_fr` | docs | 5 variantes, como os outros 34 docs |
| `docs/plans/glossary-gitpr-fix.md` | docs | Vocabulário canônico da feature |
| `docs/plans/ADR-004-fix-subcommand-package.md` | docs | Decisão do subpacote + 8 desvios aprovados |
| `docs/plans/20260913_skill_gitpr_fix_command_plan.md` | docs | O plano executado |
| `docs/survey/20260913_skill_gitpr_fix_command_surveyfacts.md` | docs | Levantamento do grill |
| `tests/fix/` (12 arquivos, 2428 linhas) | test | Fixture de repo git real + extração, classificador, applier, histórico, apply, rollback, CLI, config, `resolve_last_review` e regressão do chat |

### Alterados

| File | Change type | Description |
|------|-------------|-------------|
| `src/main.py` | feat | Subcomando `fix` [+364] |
| `src/mcp_server.py` | feat | 13ª tool `list_fix_candidates` + recurso `skill://fix` [+122] |
| `src/diff_parser.py` | feat | `summarize_patch()` + `PatchSummary` (reuso: `parse_added_lines` só conta adições) [+81] |
| `src/config_schema.py` | feat | Categoria, campos e label do skill [+60] |
| `src/config.py` | feat | Chaves `GITPR_FIX_*` + `get_fix_settings()` [+52] |
| `src/cache.py` | feat | `resolve_last_review()` (filtra `review`/`fullreview`, exclui `filereview`) [+45] |
| `src/ui/chat_app.py` | refactor | F5 e `ctrl+s` passam a chamar a camada compartilhada [−34] |
| `src/core.py` | feat | `.gitpr.fix.md` em `files_to_download` [+1] |
| `src/updater.py` | chore | `__lang_version__` v0.0.25 → v0.0.26 |
| `langs/*.json` (6 arquivos) | feat | 67 chaves novas cada, paridade exigida pelo `test_i18n.py` |
| `templates/gitpr.smart-excludes.json` | chore | `.gitpr/fix_history.json` na lista |
| `CLAUDE.md` | docs | Tabela de comandos, árvore `src/`, env vars, tools do MCP (12 → 13) |
| `README.md` ×5 | docs | Uma linha no índice de docs |
| `tests/test_diff_parser.py`, `tests/test_mcp_server.py` | test | Testes das funções e da tool novas |

## Impact

- **Functionality:** comando novo, isolado. `gitpr fix` sem argumentos lista candidatos e **não
  escreve nada**; escrever exige `--apply`; um patch não-`safe` exige `--force` com frase digitada
  (`apply FIX-001`), e `--all-safe --apply` cria branch por padrão (`--no-branch` desliga). Um
  patch aplicado fica **não commitado** de propósito e pode ser desfeito com
  `--rollback <patch-id>` sem depender de commit, stash ou reset.
- **Performance:** nenhuma regressão. Uma chamada de IA por execução, com o cache MD5 padrão em
  `~/.gitpr/cache/prompts/fix/` — é ele que torna `FIX-001` determinístico entre execuções.
- **Compatibility:** API pública inalterada; nenhuma flag existente muda de sentido; o
  `src/diff_parser.py` só ganha função e dataclass. O chat mantém o artefato `.txt` idêntico.
  O bump de `__lang_version__` faz o OTA rebaixar/rebaixar os arquivos de idioma na próxima
  execução (ver *Next steps*).

## Desvios do plano (aprovados, registrados no ADR-004)

1. `PatchSummary` mora em `src/diff_parser.py`, não no pacote — o parser puro já existia.
2. `resolve_last_review()` foi antecipado para a etapa do `apply_fix`, em `src/cache.py`.
3. `KIND_WORDS` → `KIND_STR` no campo dos caminhos sensíveis (a lista usa `;`, não espaços).
4. Recurso MCP `skill://fix` acrescentado: `mcp_server.SKILL_FILES` é um registro **separado** de
   `config.SKILL_FILES_BY_TYPE`, mantido em sincronia por `TestSkillRegistryAgreement`.
5. `.gitpr.fix.md` entrou em `generate_skill_template()` (`core.py`) — é o `files_to_download` que
   faz o `--skill` baixar de fato.
6. As 67 chaves i18n foram inseridas à mão por script: o `tests/sync_i18n.py` casa literais com
   regex, é cego à concatenação implícita e **removeria 23 chaves existentes**.
7. `CHANGELOG.md` **não** foi tocado: a seção `## [1.1.0] - 2026-09-13` já está publicada (tag
   `v1.1.0`) e o `gitpr release` gera seções a partir do git log — não há convenção de "Unreleased".
8. `smart-excludes` implementado com o marcador existente (`__lang_version__`): o
   `SMART_EXCLUDES_VERSION` do plano é env var, e a entrada viaja no bump que a feature já exigia.

Além desses: o `src/fix/__init__.py` ficou só com docstring (sem reexportações), e duas
inconsistências de tradução foram corrigidas no fecho — `templates/gitpr.fix.pt_br.md` usava
"achado" onde o `langs/pt_br.json` e o próprio doc usam "apontamento", e os comentários `#` dentro
dos blocos ```bash dos 4 docs traduzidos ficaram em inglês, contra a convenção dos docs irmãos
(`release-notes.{lang}.md`, `scm-multiforge.pt_br.md`), que os traduzem.

## Verificação

`GITPR_LANG=en_us pipenv run pytest -q` → **3 failed, 1278 passed, 2 skipped, 76 subtests passed**
(508s). As três falhas **reproduzem idênticas numa cópia pristina de `HEAD`** (`git archive HEAD`,
portanto **sem** `src/fix/`) rodada com o mesmo ambiente — mesmas asserções (`180.0 != 600.0` duas
vezes, `'en_us' != 'pt_br'` uma). **Nenhuma regressão desta entrega.**

As suítes da feature, isoladas: **417 passed** (`tests/fix/` + `test_diff_parser.py` +
`test_mcp_server.py` + `test_i18n.py` + `test_config_schema.py` + `test_smart_excludes.py` +
`test_version_bump.py`).

### Por que a suíte "crua" (`pipenv run pytest`) mostra 19 falhas

Nenhuma delas é da feature: são três causas de ambiente, todas anteriores a este trabalho.

| Causa | Efeito | Evidência |
|---|---|---|
| `GITPR_LANG='pt_br'` no `~/.gitpr/.env` do usuário | 16 testes que assertam texto **em inglês** renderizam em português (13 deles em `test_config_app.py`) | `GITPR_LANG=en_us` na frente do comando → 1278 passam |
| `_DEFAULT_AI_TIMEOUT = 180.0` ([config.py:77](src/config.py#L77)) contra o teste que espera 600 | 2 falhas em `test_net_timeouts.py` | o mesmo `180.0` está em `HEAD:src/config.py`; o diff de `config.py` é **+52/−0** e não toca timeout |
| `tests/test_core.py:550` asserta `CURRENT_LANG == "pt_br"` | 1 falha **quando** o idioma é forçado para inglês | é o espelho da primeira linha: o teste assume o idioma do desenvolvedor |

A suíte é **bimodal** neste ambiente: com `pt_br` falham 19, com `en_us` falham 3 — e as 3 são
constantes e asserções pré-existentes, não código novo. O relatório usa o número menor (forçar
inglês) porque é o modo em que as asserções de conteúdo fazem sentido.

### Manuais

- `gitpr fix -h` — as 9 opções e o epilog apontando para `https://gitpr.natanfiuza.dev.br/docs/fix-command`.
- `gitpr-mcp --list` — **13 tools**, com `list_fix_candidates`; 18 resources e 7 prompts.
- `gitpr fix --rollback FIX-999-deadbeef` → saída 1 com `❌ No applied patch with id '…' was recorded here.`
- `gitpr fix --rollback <id> --apply` → saída 1 com `❌ --rollback takes no finding id and cannot be combined with --apply or --all-safe.`
- O fluxo completo (review → IA → `--check` → classificar → apply → rollback) é coberto por
  `tests/fix/test_apply_fix.py` e `test_fix_cli.py` sobre uma fixture de repo git real; a chamada de
  IA é mockada, então a suíte não depende de rede nem de chave de API.

## Next steps

- **`docs/plans/` ficou com dois planos do mesmo documento**: `20260913_gitpr_fix.md` (tabelas
  alinhadas, links escritos a partir da raiz do repo — que não resolvem de dentro de `docs/plans/`)
  e `20260913_skill_gitpr_fix_command_plan.md` (mesmo conteúdo, links relativos corretos). O
  glossário e o ADR-004 apontam para o segundo; o primeiro é redundante e fica para você remover.
- **`pip/` e `pypa/` na raiz do repositório (11,3 MB), não rastreados e NÃO ignorados pelo
  `.gitignore`** — resíduo de experimentos meus com `HOME` falso (`pip/cache` e
  `pypa/virtualenv`, criados 23:02/23:03 de hoje). Um `git add .` os arrastaria para o commit.
  A remoção foi negada pelo classificador de permissão, então fica para você: `rm -rf pip pypa`.
- **`mcp` 2.x no venv** — `Pipfile` declara `mcp = "*"` e `pyproject.toml` `mcp>=1.0.0`, mas
  `src/mcp_server.py` importa `mcp.server.fastmcp`, que só existe no 1.x. O venv tinha 2.2.0
  (instalado em 08/09) e as duas suítes MCP **não coletavam**. Instalei `mcp<2` (1.30.0) **só no
  venv** para poder rodar a suíte; o `Pipfile.lock` local continua apontando 2.2.0. Vale fixar
  `mcp = "<2"` no `Pipfile` (e `mcp>=1.0.0,<2` no `pyproject.toml`) num commit próprio.
- **Conteúdo OTA:** o bump de `__lang_version__` só passa a casar com o que o GitHub serve depois
  do push para `main` (as 67 chaves novas e a entrada do smart-excludes viajam no commit). Até lá,
  uma instalação em v0.0.26 baixa os arquivos antigos e as chaves novas caem no texto inglês — que
  **é** a chave, então a degradação é silenciosa e não quebra nada.
- Fora desta entrega, como o plano já registrava: `--format json` no `--list`, tools MCP de
  escrita (hoje só leitura, por decisão) e o schema de finding no próprio review, que eliminaria a
  chamada de normalização.
