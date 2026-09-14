# Plano — `gitpr fix`: aplicar sugestões de review como diff revisável

## Contexto

A spec [20260913_skill_gitpr_fix_command_spec.md](../../docs/plans/20260913_skill_gitpr_fix_command_spec.md) pede um comando de primeira classe (`gitpr fix`) para aplicar sugestões de review como diff revisável, com dry-run por padrão. O objetivo é reduzir a distância entre "a IA achou um problema" e "o problema está corrigido".

A investigação obrigatória (passo 0 da spec) **derrubou três premissas** do documento, e o plano abaixo parte do que o código realmente é:

| Premissa da spec | Realidade verificada |
|---|---|
| O chat aplica patches (F5 / `ctrl+shift+s`), de forma não-revisável | O chat **nunca aplica nada**. F5 ([chat_app.py:600](../../src/ui/chat_app.py#L600)) e `ctrl+s` ([chat_app.py:400](../../src/ui/chat_app.py#L400)) extraem blocos cercados com uma regex e gravam `GITPR_PATCH_SUGGESTION_<key>.txt` no CWD — texto concatenado que **nem é um unified diff**. Sem `subprocess`, sem validação, sem proveniência. A spec §8 ("gap de segurança no chat") não existe; a §11 ("generalizar o que já funciona") também não. |
| Existe finding com `id`/`severity`/`file_path`/`line` | **Não existe** em lugar nenhum. O review devolve um envelope JSON de uma chave: `{"review": "<Markdown livre>"}` ([core.py:806-812](../../src/core.py#L806-L812)). `gitpr fix SEC-001` não tem fonte de verdade. |
| Atualizar `config.schema.yml` | O arquivo **nunca existiu** e foi rejeitado pelo [ADR-001](../../docs/plans/ADR-001-scm-abstraction.md) ("só dotenv plano + Fernet"). |

Consequência de desenho: `gitpr fix` é **capacidade nova**, não generalização. O que é genuinamente reaproveitável do chat são ~30 linhas da regex de blocos cercados; o resto (contrato de IA novo, primeira abstração de `git apply` do projeto) é construção nova.

## Decisões fechadas no grill

| # | Decisão |
|---|---|
| 1 | **Escopo:** spec completa (etapas 1–11). |
| 2 | **Layout:** pacote `src/fix/` (nomes de arquivo da spec), sem camadas DDD. |
| 3 | **Chat:** extrair só o helper de blocos cercados; comportamento do chat **inalterado** (`.txt` no CWD). |
| 4 | **`--force`:** implementado, exigindo frase digitada (não `y/n`). |
| 5 | **Findings:** chamada nova de IA sobre o último review; IDs `FIX-001..N` atribuídos por nós. |
| 6 | **Histórico:** `.gitpr/fix_history.json`, **rastreado no git** (como a spec escreve). |
| 7 | **`--all-safe` sozinho não escreve:** só seleciona o conjunto; escrever exige `--apply`. |
| 8 | **Branch:** `--all-safe --apply` cria `fix/gitpr-{datetime}` por padrão; `--no-branch` desliga. |
| 9 | **Árvore suja:** avisa/confirma só quando o patch toca arquivo já modificado. |
| 10 | **Skill:** template novo `.gitpr.fix.md` (+ variante pt_br). |
| 11 | **Docs:** 5 variantes de idioma, como os outros 34 docs. |
| 12 | **Extra:** expor `--list`/dry-run no MCP como tool **read-only**; sem `--format json`, sem tool de escrita. |

## Correção de rota obrigatória

**A chamada de IA do `fix` NÃO pode passar por `generate_pr_content`.** O `if/elif` de [core.py:774-825](../../src/core.py#L774-L825) termina num `else` que é o **ramo de PR**: um action type desconhecido devolveria `{"commit_message", "pr_description"}` silenciosamente errado. Chamar `call_ai_model` direto de `src/fix/`.

## Arquivos

### Novos

```
src/fix/__init__.py                       # re-exports (espelha src/infrastructure/scm/__init__.py)
src/fix/patch_extractor.py                # blocos cercados (movido do chat) + validação de diff
src/fix/patch_safety_classifier.py        # SAFE / REVIEW_REQUIRED / EXPERIMENTAL — puro, sem I/O
src/fix/patch_provenance.py               # dataclasses do contrato
src/fix/patch_applier.py                  # git apply --check/apply/--reverse, checkout -b, status
src/fix/fix_history.py                    # leitura/escrita de .gitpr/fix_history.json
src/fix/apply_fix.py                      # use case: review -> IA -> classificar -> dry-run/apply
src/fix/rollback_fix.py                   # use case: histórico -> git apply --reverse
templates/gitpr.fix.md  + .pt_br.md       # skill template da persona de normalização
docs/fix-command.md + 4 variantes         # pt_br, pt_pt, es_es, fr_fr
docs/plans/glossary-gitpr-fix.md          # vocabulário canônico
docs/plans/ADR-004-fix-subcommand-package.md   # por que `fix` difere de `release` no layout
tests/fix/git_fixture.py                  # repo git temporário (padrão de tests/test_suggest_reviewers.py)
tests/fix/test_patch_extractor.py
tests/fix/test_patch_safety_classifier.py
tests/fix/test_apply_fix.py
tests/fix/test_rollback_fix.py
tests/fix/test_fix_cli.py
tests/fix/test_chat_shared_extractor.py   # regressão F5 / ctrl+s
docs/plans/20260913_skill_gitpr_fix_command_plan.md      # este plano
docs/survey/20260913_skill_gitpr_fix_command_surveyfacts.md   # levantamento do grill
docs/claude-code/reports/develop_natan/2026-09-13_gitpr_fix_command.md  # relatório obrigatório
```

### Alterados

| Arquivo | Mudança |
|---|---|
| [src/diff_parser.py](../../src/diff_parser.py) | **Reuso:** adicionar `summarize_patch()` (arquivos, nº de hunks, linhas adicionadas/removidas, texto das removidas). O `parse_added_lines` existente só conta adições — insuficiente para o critério de linhas alteradas e para a heurística de assinatura removida. |
| [src/cache.py](../../src/cache.py) | `resolve_last_review(repo, branch)` — espelha `get_cached_pr_descriptions` (glob em `~/.gitpr/cache/prompts/review/*.json`, filtra repo+branch, ordena por `datetime`). Filtra `action_type` para `review`/`fullreview` — **exclui `filereview`**, que é auditoria de arquivo único e não tem diff de branch. Os três caem na mesma pasta ([core.py:757-764](../../src/core.py#L757-L764)). |
| [src/config.py](../../src/config.py) | Chaves `GITPR_FIX_*` em `DEFAULT_CONFIG`; `get_fix_settings()`; `SKILL_FILES_BY_TYPE["fix"] = ".gitpr.fix.md"`. |
| [src/config_schema.py](../../src/config_schema.py) | `Category` do fix, `ConfigField`s das chaves e o label do skill — o [test_config_schema.py](../../tests/test_config_schema.py) exige paridade com `DEFAULT_CONFIG` e `SKILL_FILES_BY_TYPE`, e falha até isso estar completo. |
| [src/main.py](../../src/main.py) | Subcomando `@cli.command` `fix`, no molde exato do `release` ([main.py:1587-1653](../../src/main.py#L1587-L1653)): `context_settings={"help_option_names": ["-h","--help"]}`, `epilog` com `get_doc_url("fix-command.md")`, imports lazy dentro do corpo. |
| [src/ui/chat_app.py](../../src/ui/chat_app.py) | F5 e `ctrl+s` passam a chamar `patch_extractor.extract_code_blocks()`; o bloco duplicado (`:409-437` e `:616-647`) vira uma função só. Nome do arquivo e formato de saída **iguais aos de hoje**. |
| [src/mcp_server.py](../../src/mcp_server.py) | 13ª tool `list_fix_candidates` (read-only). |
| `langs/*.json` (6) | Chaves novas; paridade exigida pelo `tests/test_i18n.py`. |
| [CLAUDE.md](../../CLAUDE.md) | Tabela de comandos, árvore `src/`, env vars, tabela de tools do MCP (12 → 13). `GEMINI.md` **não** espelha essas tabelas (verificado) — fica intacto. |
| [CHANGELOG.md](../../CHANGELOG.md) | Entrada da feature. Sem nota de mudança de comportamento do chat — não há mudança de comportamento. |
| `README.md` ×5 | Uma linha no índice de docs, como o `release` em [README.md:419](README.md#L419). |
| `templates/gitpr.smart-excludes.json` | **Consequência da decisão 6** (ver Riscos): excluir `.gitpr/fix_history.json` dos diffs de IA + bump do `SMART_EXCLUDES_VERSION` no [updater.py](../../src/updater.py). Item removível se você preferir não mexer. |

## Contrato de dados

Mantém os nomes da spec §3; `PatchSummary` é o acréscimo exigido pelos fatos.

```python
# src/fix/patch_provenance.py
class PatchSafety(str, Enum):
    SAFE = "safe"
    REVIEW_REQUIRED = "review_required"
    EXPERIMENTAL = "experimental"

@dataclass
class FindingRef:      # id, file_path, line_start, line_end, severity, category, message
@dataclass
class PatchSummary:    # files: list[str]; hunks: int; added: int; removed: int; removed_lines: list[str]
@dataclass
class PatchCandidate:  # finding, diff_unified, safety, safety_reason, suggested_test, provenance
@dataclass
class PatchProvenance: # finding_id, ai_provider, ai_model, prompt_version, generated_at, gitpr_version
@dataclass
class ApplyFixResult:  # applied, branch_created, files_changed, patch_id, dry_run_diff, warnings
```

`patch_id = f"{finding_id}-{md5(diff_unified)[:8]}"` — estável e endereçável pelo `--rollback`.

## Pipeline

1. **Resolver o review.** `resolve_last_review(repo, branch)` → registro mais recente do cache. Ausente: erro claro (`rode gitpr -r primeiro`), nunca um `None` silencioso.
2. **Obter ou gerar o patch.** Se o review já contém um bloco de diff por finding, usa. Senão, **uma** chamada de IA com review + diff atual pedindo `{"findings": [...]}`.
   - Diff atual re-derivado com a **mesma função que produziu o review** (`get_git_diff()` para `review`, `get_git_full_diff()` para `fullreview`), selecionada pelo `action_type` do registro — o patch tem que aplicar na árvore de agora, não na de quando o review rodou.
   - `system_instruction = get_skill_context("fix", quiet=quiet)`; JSON forçado pelo `call_ai_model` (o transporte já força `response_mime_type`/`response_format`).
   - Cache MD5 existente na pasta `fix`, com `repo`/`branch` no registro — é ele que torna `FIX-001` determinístico entre invocações (temperatura 0.0 + cache devolvem exatamente o mesmo JSON). **Nenhum arquivo novo de findings.**
3. **Validar sintaticamente.** `git apply --check` contra a árvore atual. Falha → `EXPERIMENTAL` + warning. Nada é aplicado sem passar aqui.
4. **Classificar** (`patch_safety_classifier.py`, determinístico, sem IA):
   - `EXPERIMENTAL`: falhou no passo 3 · multi-arquivo · baixa confiança declarada pela IA.
   - `SAFE`: 1 hunk · ≤ `safe_max_lines_changed` · nenhum arquivo em `safe_excluded_paths` · nenhuma linha removida com cara de chamada pré-existente (`\w+\s*\(`).
   - `REVIEW_REQUIRED`: passou no passo 3 e não é `SAFE`.
5. **Proveniência** — provider, modelo, `prompt_version`, `gitpr_version`, timestamp.
6. **Dry-run (default):** diff + classificação no terminal via `click.secho` (o projeto não usa `rich`); nada tocado.
7. **`--apply`:** confirmação com o diff na tela · `--yes` pula o `y/n` · `--force` exige a frase digitada (e é a **única** porta para um `EXPERIMENTAL`, com aviso de baixa confiança) · aviso extra se algum arquivo alvo estiver sujo · branch quando aplicável · `git apply` · entrada no histórico.
8. **`--all-safe`:** seleciona só os `SAFE`; os demais aparecem no resumo final como "não aplicados — use `gitpr fix <id> --apply`".

## Superfície de CLI

| Comando | Efeito |
|---|---|
| `gitpr fix` | Sem id e sem `--all-safe` → lista candidatos (equivale a `--list`); nada é aplicado. |
| `gitpr fix --list` | Lista findings com patch disponível + classificação + resumo. |
| `gitpr fix <id>` | Dry-run daquele finding. |
| `gitpr fix <id> --apply` | Aplica, com confirmação. |
| `gitpr fix --all-safe --apply` | Aplica só os `SAFE`, em branch nova por padrão. |
| `--create-branch <nome>` / `--no-branch` | Sobrescreve / desliga a branch automática. |
| `--yes` / `--force` | Pula o `y/n` / frase digitada, respectivamente. |
| `--rollback <patch-id>` | Reverte um patch aplicado. |

Nomes livres: nenhum dos flags existe hoje no projeto. `--force` já existe no subcomando `release` com outro sentido — namespaces de subcomando não colidem.

## Rollback

`rollback_fix(patch_id)` lê o histórico, confere que a **branch atual é a mesma** em que o patch foi aplicado (senão erro claro) e roda `git apply --reverse` sobre o diff armazenado. O diff completo é persistido justamente para não depender de commit. Se a árvore mudou de forma incompatível, o reverse falha e o erro é reportado — o arquivo não é corrompido.

## Configuração (dotenv plano — ADR-001)

| Chave | Default | Tipo |
|---|---|---|
| `GITPR_FIX_SAFE_MAX_LINES_CHANGED` | `5` | int |
| `GITPR_FIX_SAFE_EXCLUDED_PATHS` | `database/migrations/**;**/*.ci.yml;docker/**;terraform/**;.github/workflows/**` | `KIND_WORDS` (`;`) |
| `GITPR_FIX_REQUIRE_CONFIRMATION` | `true` | bool |
| `GITPR_FIX_CREATE_BRANCH_ON_ALL_SAFE` | `true` | bool |
| `GITPR_FIX_BRANCH_NAME_TEMPLATE` | `fix/gitpr-{datetime}` | `KIND_TEMPLATE` |

Duas notas de fidelidade: a lista de paths sensíveis é **config nova** — o `gitpr.smart-excludes.json` é sobre ruído de diff (lockfiles, minificados), conceito diferente, então não há reuso ali. E o template usa `{datetime}` porque o vocabulário de placeholders do projeto é `("branch", "datetime")` ([config_schema.py:75](../../src/config_schema.py#L75)); o `{date}` da spec não existe.

## MCP (13ª tool, read-only)

`list_fix_candidates(finding_id=None)` devolve findings + classificação + diff. Nunca aplica. A chamada de IA roda com `quiet=True` — o stdout do MCP é o stream JSON-RPC e é monkey-patchado. Atualizar a tabela de tools do `CLAUDE.md` (12 → 13).

## Testes (critério de aceite da spec §9)

Fixture de repo git real compartilhada em `tests/fix/git_fixture.py`, no padrão já existente de [test_suggest_reviewers.py:239-282](../../tests/test_suggest_reviewers.py#L239-L282) (`tempfile.mkdtemp` + `addCleanup` + `_git()` com `core.autocrlf=false` e `commit.gpgsign=false`). Estilo `unittest.TestCase`, como os outros 38 arquivos.

1. Extração: formato real da resposta, resposta malformada → `None`/erro tratado, nunca exceção.
2. Classificador: matriz por critério isolado + combinações; **falha no `git apply --check` sempre `EXPERIMENTAL`**, independente dos demais.
3. Dry-run nunca escreve: `git status --porcelain` idêntico antes e depois.
4. `--all-safe` seletivo: conjunto misto → só `SAFE` aplicado; demais no resumo.
5. Branch: criada a partir do `HEAD` correto, patch aplicado nela, branch original intacta.
6. Proveniência: todo patch aplicado gera entrada com todos os campos preenchidos.
7. Rollback: sucesso volta ao estado anterior; falha por modificação externa dá erro claro sem corromper.
8. Não-duplicação: F5 e `ctrl+s` chamam a camada compartilhada, sem regex própria.
9. Regressão do chat: mesmo resultado visível ao usuário (mesmas teclas, mesmo `.txt`).

## Ordem de execução

Cada etapa é um passo revisável; **nada é commitado** (regra do `CLAUDE.md`) — as mudanças ficam na árvore de trabalho na ordem abaixo, para você fatiar os commits.

0. Salvar este plano em `docs/plans/` e o survey em `docs/survey/`.
1. `src/diff_parser.py`: `summarize_patch()` + testes.
2. `patch_extractor.py` extraído do chat; chat passa a chamá-lo, comportamento intacto + teste de regressão.
3. `patch_safety_classifier.py` (puro) + matriz de testes.
4. `patch_applier.py` + testes com o fixture de repo real.
5. `patch_provenance.py` + `fix_history.py` + testes.
6. `apply_fix.py` + testes de integração ponta a ponta.
7. `rollback_fix.py` + testes de sucesso e falha.
8. `resolve_last_review()` em `cache.py` + testes.
9. Subcomando `gitpr fix` no `main.py` + i18n.
10. Config: `DEFAULT_CONFIG`, `config_schema.py`, `get_fix_settings()` + testes de paridade.
11. Skill template `gitpr.fix.md` (+ pt_br) + `SKILL_FILES_BY_TYPE` + label.
12. Tool MCP + `CLAUDE.md`.
13. Docs ×5, README ×5, CHANGELOG.
14. Glossário + ADR-004.
15. Suite completa + relatório de conclusão.

O chat é tocado **cedo** (etapa 2) de propósito: é a única mudança em código que o usuário já usa, e fazê-la antes mantém o resto — que é código novo — isolado de risco de regressão.

## Verificação

- `pipenv run pytest -v` — suite inteira verde, incluindo `test_i18n.py`, `test_config_schema.py` e os novos `tests/fix/`.
- Manual, em repo de fixture: `gitpr -r` → `gitpr fix --list` → `gitpr fix FIX-001` (dry-run, confirmar árvore limpa) → `--apply` (conferir histórico) → `--rollback` (conferir retorno ao estado anterior).
- Chat: `gitpr -ch`, F5 e `ctrl+s` — mesmo `.txt` de antes.
- `gitpr-mcp --list` mostra 13 tools; `gitpr-mcp --tool list_fix_candidates` responde sem aplicar nada.
- `gitpr -h` e `gitpr fix -h` mostram o subcomando e o epilog apontando para o doc.

## Riscos e impacto

- **`.gitpr/fix_history.json` rastreado (decisão 6) tem uma consequência concreta:** aplicar um patch deixa o arquivo modificado, e ele passa a aparecer nos diffs de `gitpr -c` e na descrição de PR. A mitigação incluída é a entrada no `smart-excludes` (etapa 8 do quadro de alterados) — se você preferir, é o item mais fácil de remover do plano.
- **Mudança de comportamento do chat: nenhuma.** A dedup é invisível; o artefato `.txt` continua igual. Por isso não há nota de changelog sobre o chat.
- **Não-objetivo explícito:** o literal i18n corrompido `"Ctrlhift+S"` ([chat_app.py:78](../../src/ui/chat_app.py#L78)) fica como está. É bug pré-existente com histórico próprio (ADR-002-reviewer-suggestion), mexe em chaves dos 6 `langs/*.json` e não é meu para corrigir nesta entrega.
- **Compatibilidade:** API pública inalterada. Nenhuma flag existente muda de sentido. `src/diff_parser.py` só ganha função nova.
- **Segurança:** nenhum patch chega à árvore sem passar por `git apply --check`; lote nunca aplica na branch atual por padrão; `EXPERIMENTAL` só via `--apply` individual + frase digitada.

## Próximos passos (fora desta entrega)

- `--format json` no `--list` (padrão do `release`).
- Tools MCP de escrita — hoje só leitura, por decisão.
- Auditoria de equipe sobre o `fix_history.json` (o tier Team citado na spec §11) e o schema de finding no review, que eliminaria a chamada de normalização.
