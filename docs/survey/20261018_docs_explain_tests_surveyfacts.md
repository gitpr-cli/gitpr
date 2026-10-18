# Survey — Documentar `explain` e `tests` (5 idiomas)

## Contexto da tarefa

`explain` e `tests` são os dois únicos recursos do produto sem tópico próprio em `docs/`. As duas features da janela anterior (`check-ci` e `editor-extension`) foram entregues com o guia canônico em inglês e as variantes `.pt_br`, `.pt_pt`, `.es_es` e `.fr_fr`. A documentação existente de `explain` aponta para `pull-request-publication.md`, que não menciona a feature; `tests` não tem link de documentação.

## Fatos levantados

### Superfície de `explain`

- Comando `gitpr explain` em `src/main.py:4933-4995`, com `--provider` (`metavar="<name>"`, sem `click.Choice`).
- Analisa o diff local via `get_git_diff()` (`git diff -U1 -w -M -B HEAD`, com `SMART_EXCLUDES`) e imprime o guia no terminal; não grava arquivo e não publica.
- A flag raiz `--explain` (`src/main.py:558-565`, dest `explain_flag`) só age no fluxo padrão de PR (`src/main.py:1606-1612`): usa `get_git_full_diff()` contra a base remota, anexa `explanation.markdown` ao `.md` local e ao corpo publicado, antes do badge.
- `GITPR_EXPLAIN_BY_DEFAULT` (`src/config.py:476-484`) aceita `true/1/yes/y`, padrão `false`; está no `config_schema.py:534-543`, mas não é semeado por `setup_environment()` (`DEFAULT_CONFIG` não o contém).
- O mesmo recurso aparece no MCP (`generate_pr_description(explain=true)`, `src/mcp_server.py:725-788`) e na extensão VS Code (`gitpr.generatePrExplain`, `extensions/vscode/src/extension.ts:56-57`).
- Skill registrada em `src/config.py:178` (`.gitpr.explain.md`), baixada pelo `--skill` (`src/core.py:1406`) e presente em `templates/gitpr.explain.*.md` nos 5 idiomas. `get_skill_context("explain", quiet=True)` (`src/application/use_cases/generate_pr_explanation.py:40`) com fallback embutido.
- Modelo avançado (`get_api_model(..., task_complexity="advanced")`), resposta JSON, 3 tentativas/2 s, temperatura 0. Sem cache de prompt e sem registro no ledger.
- Formato: `## 🧐 Reviewer Guide (Explain My PR)`, seções What changes / Why it changes / Where to focus review / Regression Risk; placeholders `[FILL: ...]`/`[PREENCHER`/`[TODO`/`[REQUIRED` em `what`/`why` marcam `has_sufficient_evidence=False`.
- `gitpr -h --explain` está quebrado: o `HELP_MAP` usa a chave `"explain"` (`src/main.py:261-267`), mas o callback raiz tem o parâmetro `explain_flag` (`src/main.py:639`); o dispatcher procura `locals()["explain"]` (`src/main.py:687-692`). `--mentor` tem o mesmo defeito (`mentor_flag`), fora do escopo.

### Superfície de `tests generate`

- Grupo `tests` (`src/main.py:4758-4765`) e subcomando `generate` (`4769-4802`), sem epilog e sem entrada no `HELP_MAP`; `gitpr -h --tests` é rejeitado pelo Click.
- Flags: `--file`, `--finding`, `--framework`, `--apply`, `--provider`.
- Resolução do alvo (`src/main.py:4811-4851`): sem flags, `get_git_diff()`; `--file`, `git diff HEAD -- <arquivo>` com fallback para o conteúdo bruto do arquivo; `--finding`, o último review via `resolve_review`/`collect_candidates`/`find_candidate` do `src/fix/apply_fix.py`.
- Domínio `src/domain/tests_generation/`: `framework_detector.py` (PHP → JS/TS → Python, primeira correspondência, só na raiz), `test_scaffold_builder.py` (convenções Pest/PHPUnit, Jest/Vitest, pytest; `already_exists`), `test_content_types.py`.
- Use case `generate_test_file.py`: skill `.gitpr.tests.md`, modelo avançado, envelope JSON `{content, covered_scenarios, warnings}`, fallback de texto bruto, validação sintática `php -l` / `node --check` / `py_compile` (pulada se o binário não existe; falha vira warning e não bloqueia a escrita), sem cache e sem chunking.
- `--apply` (`src/main.py:4899-4930`): dry-run sempre primeiro; confirmação de sobrescrita (padrão No) e de escrita (padrão Yes); cria diretórios; não roda `git add` nem os testes gerados.
- Skill `tests` registrada em `src/config.py:177`, baixada pelo `--skill` (`src/core.py:1405`) e presente em `templates/gitpr.tests.*.md` nos 5 idiomas.
- O `/tests` do chat não compartilha o motor na maioria dos casos: `process_chat_command` substitui o slash command pelo texto do prompt antes da verificação em `src/ui/chat_app.py:544-545`; o caminho estruturado só dispara para um comando não reconhecido no idioma ativo.

### Defeitos de runtime confirmados por reprodução

1. `call_ai_model` devolve `dict` (`src/ai_providers.py:202-216`), mas:
   - `src/application/use_cases/generate_test_file.py:192` faz `json.loads(ai_raw)` e, no `except`, `ai_raw.strip()` → `AttributeError: 'dict' object has no attribute 'strip'`.
   - `src/domain/pr/explain_section_builder.py:89-106` faz o mesmo via `parse_explain_payload`.
   - Os testes mascaravam o contrato porque mockavam uma string JSON (`tests/application/use_cases/test_generate_pr_explanation.py`, `tests/test_explain_command.py`, `tests/application/use_cases/test_generate_test_file.py`, `tests/test_tests_command.py`).
2. `--finding` acessa `cand.finding.suggested_test` e `cand.diff` (`src/main.py:4827-4828`), mas `FindingRef` não tem `suggested_test` e `PatchCandidate` expõe `suggested_test` e `diff_unified` (`src/fix/patch_provenance.py:26-70`). O erro é engolido e a geração continua só com `"Finding ID: <id>"`.
3. Sem chave de IA, `generate_pr_explanation` devolve um markdown de aviso (`src/application/use_cases/generate_pr_explanation.py:27-35`); o standalone sai com exit 0 e o `--explain` anexa o aviso ao corpo do PR.

### Documentação e links existentes

- `README.md:146` (tests, sem link), `README.md:148` (explain → `pull-request-publication.md`), `README.md:165` (`--explain`, sem link); mesmas linhas nos 4 READMEs traduzidos, com variantes de redação no `fr_fr`.
- `HELP_MAP["explain"]` e o epilog de `gitpr explain` apontam para `pull-request-publication.md`, que não menciona `explain`.
- `docs/ARCHITECTURE.md` (e variantes) lista guias de features antigas e já não inclui `check-ci`, `editor-extension`, `risk-scoring`, `policy-packs`, `baseline`, `split`, `fix` nem `release-notes`; não será atualizado nesta task.

## Decisões da sessão

1. Nomes `explain-pr.md` e `tests-generate.md`.
2. `explain-pr.md` cobre standalone, `--explain`, `GITPR_EXPLAIN_BY_DEFAULT`, skill e referência a MCP/extensão; `tests-generate.md` cobre só o CLI.
3. Wiring: `HELP_MAP`, epilogs de `explain`, do grupo `tests` e de `generate`, e correção de `-h --explain`.
4. READMEs nos 5 idiomas; `ARCHITECTURE.md` intocado.
5. Guia técnico completo, com exemplos.
6. Seção de limitações explícita.
7. Tradução integral nos 5 idiomas.
8. Correções de runtime incluídas (dict/str, `--finding`, mocks e regressões).
9. Sem chave: aviso no terminal, seção omitida no PR, exit 1 no standalone.

## Itens herdados registrados (fora do escopo)

- `gitpr -h --mentor` tem o mesmo defeito de nome de parâmetro.
- `/tests` do chat não delega ao motor de geração.
- `explain` e `tests` não registram métricas no ledger.
- `docs/ARCHITECTURE.md` está desatualizado em relação a vários tópicos recentes.
- O bullet do `--skill` nos READMEs não lista `.gitpr.explain.md` nem `.gitpr.tests.md`.
