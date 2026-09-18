# Survey — review de PR remoto (`gitpr review-pr <n>`)

> Sessão `/grill-with-docs` de **2026-09-17**, branch `develop_natan`.
> Tarefa pedida: *"Execute o plano docs\plans\20260917_skill_gitpr_review_pr_spec.md"*.
> Spec de origem: [20260917_skill_gitpr_review_pr_spec.md](../plans/20260917_skill_gitpr_review_pr_spec.md).
> Plano gerado e aprovado: `C:\Users\nataniel\.claude\plans\execute-o-plano-docs-plans-20260917-skil-hashed-sun.md`.
> Base de domínio: [ADR-003](ADR-003-*.md) e [ADR-004](ADR-004-gitpr-fix-command.md) (rejeitam camadas DDD),
> [ADR-001-scm-abstraction.md](../plans/ADR-001-scm-abstraction.md) (contrato `ScmProvider`) e
> [glossary-scm-multiforge.md](../plans/glossary-scm-multiforge.md).

## 1. Contexto da tarefa

O review do GitPR (`gitpr -r` / `-f`) só opera sobre o **diff local** do working tree ou da branch atual. Isso
exclui um público inteiro: quem foi convidado a revisar o PR de outra pessoa e não tem — nem precisa ter — a
branch do autor em checkout.

A spec pede `gitpr --review-pr <n>` para revisar um PR **já aberto na forge**, buscando o diff pela API, com
publicação opcional do resultado como comentário (`--post-comment`). A intenção estratégica declarada (spec §9)
é expandir o público de "quem abre PRs" para "quem revisa PRs" — multiplicando o número de pessoas tocando o
produto dentro de uma equipe sem custo adicional de infraestrutura.

O §0 da spec exige um levantamento de fatos **antes de qualquer código**, com parada obrigatória nos passos 1–3.
Este documento é o resultado desse levantamento, e ele **derrubou quatro premissas da própria spec** (§2.1) e
encontrou **três defeitos latentes** que a feature exporia (§2.4, §2.5, §2.6).

## 2. Fatos levantados

### 2.1 — Premissas da spec que não sobreviveram ao levantamento

| Premissa da spec | Realidade verificada | Onde |
|---|---|---|
| Criar `src/application/use_cases/review_remote_pr.py` e `src/domain/review/diff_source.py` | Nenhum dos dois diretórios existe; as ADRs vigentes rejeitam explicitamente camadas DDD e mandam o código novo para pacotes-irmãos por responsabilidade | `src/` (ausência), ADR-003/ADR-004 |
| "Confirmar se `get_pull_request_diff` foi implementada" | Está implementada **e testada** nos 4 providers; é `@abstractmethod` na ABC desde o ADR-001 | `src/infrastructure/scm/base.py:153-155` |
| Atualizar `config.schema.yml` (§8.8) | O arquivo não existe; a config é dotenv plano + `DEFAULT_CONFIG` + `FIELDS` | `src/config.py`, `src/config_schema.py` |
| Reusar `render_review_result` (§5) | A função não existe; a renderização é inline no bloco de review | `src/main.py:1364-1433` |

**Consequência:** o trabalho novo real é a orquestração + a normalização do diff remoto + a superfície
CLI/MCP — não a construção das camadas que a spec supunha inexistentes.

### 2.2 — O motor de review já é agnóstico à origem do diff

| Fato | Onde |
|---|---|
| `generate_pr_content(action_folder, action_type, diff_text, provider="gemini")` recebe **uma string de diff** e devolve `{"review": "<markdown>"}` (ou `None` em falha/diff vazio) | `src/core.py:745` |
| O docstring declara "Sends the diff to the AI using System Instruction and returns a parsed JSON" — nenhuma menção a git, working tree ou branch | `src/core.py:745-748` |
| `get_skill_context(action_type="pr", quiet=False)` devolve `str` ou `""`; `review` e `fullreview` leem o mesmo `.gitpr.review.md` via `DEFAULT_SKILL_TYPE = "review"` | `src/core.py:658` |
| `split_diff_into_chunks(diff_text, max_tokens=90000)` é genérico sobre strings e corta em `^diff --git a/` | `src/core.py:715` |
| Cache: chave = `generate_md5(prompt_text)`, **só** o texto do prompt | `src/cache.py:34-37` |

**Consequência:** o passo §8.3 da spec ("refatorar o ponto de entrada do motor para aceitar `DiffSource`") é
**desnecessário** — o motor já aceita qualquer diff. `DiffSource` vira contrato de dados no pacote novo, sem
tocar na assinatura de `generate_pr_content` além de parâmetros opcionais.

### 2.3 — Infraestrutura reaproveitável para o caminho remoto

| Fato | Onde |
|---|---|
| `_resolve_scm_context()` já resolve `(provider, repo_ref)` e trata os erros de configuração | `src/main.py:2534-2575` |
| `resolve_output_path(env_var, default_pattern, safe_branch_name, current_time)` — placeholders limitados a `{branch}` e `{datetime}`; a pasta vem da env var, não do pattern | `src/core.py:427-467` |
| `parse_diff_and_lint(diff_text, is_full_file=False, file_path=None)` → `{"errors": [...], "warnings": [...]}` | `src/linter_engine.py:209` |
| `summarize_patch(diff_text)` → `PatchSummary(files, hunks, added, removed, removed_lines)` | `src/diff_parser.py` |
| Padrão de subcomando: `@cli.command(...)` + `return` no grupo quando `ctx.invoked_subcommand is not None` | `src/main.py:544-548`, `src/main.py:1971-2025` |
| `pyproject.toml` usa auto-discovery (`include = ["src", "src.*"]`) — pacote novo só precisa de `__init__.py` | `pyproject.toml` |

### 2.4 — Defeito 1: o GitLab descarta o nome do arquivo

`get_pull_request_diff` do GitLab junta `changes[].diff` e **ignora `old_path`/`new_path`**, que a API já
devolve. O campo `diff` da API do GitLab é **o corpo do hunk, sem cabeçalho** — diferente de GitHub e
Bitbucket, que devolvem patch unificado completo.

| Fato | Onde |
|---|---|
| `return "\n".join(item.get("diff", "") for item in changes if item.get("diff"))` — sem `old_path`/`new_path` | `src/infrastructure/scm/gitlab_provider.py:241-251` |
| O campo `overflow` (diff truncado por limite de tamanho) é lido e descartado | idem |
| `/changes` está **deprecado desde o GitLab 15.7** (remoção prevista na API v5); o sucessor `/diffs` é paginado e traz `collapsed`/`too_large` | GitLab REST docs (pesquisa) |
| Os testes fabricam linhas `diff --git` dentro do mock, então o defeito é **invisível para a suíte** | `tests/scm/test_gitlab_provider.py:334-359` |

**Consequências:** (a) a IA revisaria trechos órfãos sem saber a que arquivo pertencem; (b) nem o chunker
(corta em `^diff --git a/`) nem o filtro de smart excludes funcionariam; (c) com `overflow` ignorado, um MR
grande seria revisado **pela metade e sem aviso** — e publicado assim.

### 2.5 — Defeito 2: não existe `get_pull_request`, e a alternativa é enviesada e silenciosa

A spec §4.3 sugeriu obter os metadados via `list_open_pull_requests` filtrando pelo número. A verificação
mostrou que **nenhum dos quatro providers pagina essa chamada**:

| Provider | Fato | Onde |
|---|---|---|
| GitHub | lista aberta, sem `per_page`/`page`, sem ler o header `Link` | `github_provider.py:337-358` |
| GitLab | lista aberta, sem `per_page`/`page`, sem ler `X-Next-Page` | `gitlab_provider.py:253-261` |
| Bitbucket | lista aberta, sem `pagelen`, sem ler o cursor `next` | `bitbucket_provider.py:277-285` |
| Azure DevOps | lista aberta, sem `$top`, sem ler `continuationToken` | `azure_devops_provider.py:347-355` |

Como as forges ordenam do mais novo para o mais antigo, filtrar por número falha justamente nos PRs **mais
antigos** — e falha **em silêncio**: lista vazia é indistinguível de "PR não existe". Além disso a listagem só
cobre PRs **abertos**, então não distingue "mesclado" de "inexistente". GitHub estoura a página por volta de 30
PRs abertos, GitLab ~20, Bitbucket ~10.

**Consequência:** `get_pull_request(repo, pr_id)` entra no contrato. A recomendação inicial do grill era **não**
adicionar o método — foi revertida quando esta verificação chegou, e a reversão foi explicitada ao usuário.

**Achado de passagem, fora do escopo desta entrega:** `check_existing_pull_request` tem a **mesma** falha de
paginação e é alcançável em produção — o PR Publisher o chama antes do push
(`src/ui/pr_publish_app.py:1209`), então num repositório movimentado ele não acha um PR já aberto e o usuário
cria uma **duplicata**. Registrado, não corrigido aqui.

### 2.6 — Defeito 3: `gitpr fix` re-deriva o diff localmente

| Fato | Onde |
|---|---|
| `reviewed_diff(record, quiet=False)` chama `get_git_diff()` / `get_git_full_diff()` em vez de usar o diff que foi revisado | `src/fix/apply_fix.py:110-122` |
| `resolve_last_review(repo_name, branch_name)` faz glob em `~/.gitpr/cache/prompts/review/*.json` e filtra por repo+branch+action_type+`response.review` não-vazio | `src/cache.py:91-128` |
| `REVIEW_ACTION_TYPES = ("review", "fullreview")` | `src/cache.py:88` |

**Consequência:** um review remoto parearia contra a árvore local errada — o patch seria aplicado sobre um
diff que não é o revisado. A correção é gravar o diff no próprio registro de cache.

### 2.7 — Restrições duras de i18n e de contrato

| Fato | Onde |
|---|---|
| Toda chave `__()` nova precisa existir nos **seis** `langs/*.json` | `tests/test_i18n.py:233-243` |
| Chave nova contendo `{}` deixada como identidade (valor == chave) **reprova**, salvo prefixo em `AI_PROMPT_PREFIXES` | `tests/test_i18n.py:177-213` |
| Paridade exata do conjunto de chaves entre os seis arquivos | `tests/test_i18n.py:125-136` |
| `sync_i18n.py` insere chave faltante como `key = key` (inglês) nos seis — a tradução passa a ser obrigatória | `tests/sync_i18n.py:105` |
| `REVIEW_ACTION_TYPES` não precisa mudar: o review remoto usa `action_type="review"` e é encontrado pelo `resolve_last_review` | `src/cache.py:88-128` |
| O gate do linter externo é só `if external_linters and modified_files:` — **não existe** forma de pedir "só YAML" | `src/linter_engine.py:247` e `:303` |
| `_run_external_linter` roda `subprocess.run` **sem `cwd=`** e anexa o `file_path` relativo ao argv — resolve contra o diretório de trabalho atual | `src/linter_engine.py` |
| `HELP_MAP` é só para flags do grupo raiz — uma entrada para subcomando seria código morto; o espelho correto é `context_settings` + `epilog` com `get_doc_url("review-pr.md")` | `src/main.py:77-237` |
| `tests/test_config_cli.py:36-45` é o único teste que toca `cli.commands` e usa `assertIn` — aditivo é seguro; não há teste de contagem de flags nem snapshot de `--help` | `tests/test_config_cli.py:36-45` |
| Subcomandos **não** herdam flags do grupo raiz e nunca chamam `check_unstaged_files` | `src/main.py:544-548` |
| `docs/plans/` tem **ADR-002 duplicado** (release-subcommand e reviewer-suggestion) — o próximo número livre é **ADR-005** | `docs/plans/` |
| Convenção de docs: `<name>.md` = EN, `<name>.pt_br.md` = tradução | `docs/` |
| Fixture de teste de git real: `GitRepoTestCase` (setUp em tmpdir, `write`, `commit`, `patch_for`, `seed`) | `tests/fix/git_fixture.py` |

### 2.8 — Comparação local vs remoto (o que muda e o que não muda)

| Aspecto | Review local (`-r`) | Review de PR remoto |
|---|---|---|
| Origem do diff | `git diff HEAD` / `git diff origin/base...HEAD` | `get_pull_request_diff(repo, n)` |
| Motor de IA | `generate_pr_content` | **o mesmo** |
| Skill aplicada | `.gitpr.review.md` via `get_skill_context("review")` | **a mesma** |
| Map-reduce | `split_diff_into_chunks` | **o mesmo** |
| Smart excludes | pathspec `:(exclude)` no argv do git | filtra seções do patch (não há git envolvido) |
| Linter externo | roda contra arquivos locais | **desligado** (arquivos locais são de outra revisão) |
| Saída | `.gitpr/reports/review/*.txt` | a mesma pasta e o mesmo pattern |
| Chave de cache | `md5(prompt)` | `md5(prompt + cache_scope)` — escopo distingue a origem |

## 3. Decisões do grill (7 rodadas)

### Rodada 1 — forma da entrega

| # | Questão | Decisão |
|---|---|---|
| Q1 | Onde mora o código novo? | **Pacote `src/review/`** (espelha `src/fix/`, ADR-004) — não as camadas DDD da spec |
| Q2 | Flag no grupo raiz ou subcomando? | **Subcomando `gitpr review-pr <n>`** — **diverge da spec §1/§5** |
| Q3 | `DiffSource` entra no motor? | **Não** — contrato apenas; o motor já é agnóstico |
| Q4 | Azure, que devolve um resumo e não um diff? | **Falhar rápido** com erro claro, antes de qualquer chamada de IA |

### Rodada 2 — superfície e saída

| # | Questão | Decisão |
|---|---|---|
| Q5 | Quais flags? | **`--post-comment` + `--provider`** (sem `--lang`, sem `--quiet`) |
| Q6 | Onde mora a renderização? | **Extrair para `src/review/render.py`**, compartilhada com o fluxo local |
| Q7 | Como detectar forge sem diff revisável? | **Atributo de capacidade na ABC + validação do conteúdo** como rede de segurança |
| Q8 | Corpo do comentário | **Review + rodapé de proveniência** (versão, provider, número do PR) — **sem SHA** |

### Rodada 3 — correções e durabilidade

| # | Questão | Decisão |
|---|---|---|
| Q9 | Corrigir o GitLab nesta entrega? | **Sim** — a feature depende disso para funcionar |
| Q10 | `gitpr fix` sobre um review remoto | **Gravar o diff revisado** no registro de cache; `reviewed_diff()` prefere o gravado |
| Q11 | Comentário duplicado em reexecução? | **Sempre novo comentário** (o contrato não tem `update_comment`); rodapé sem SHA |
| Q12 | Quantos módulos no pacote? | **4** com responsabilidade única + `tests/review/` |

### Rodada 4 — escopo da correção do GitLab, MCP e linter

| # | Questão | Decisão |
|---|---|---|
| Q13 | Até onde vai a correção do GitLab? | **Cabeçalhos sintéticos + tratar `overflow`** (sem migrar para `/diffs`) |
| Q14 | Entra tool MCP nesta entrega? | **Sim** (usuário divergiu da recomendação de adiar) |
| Q15 | Linter externo em PR remoto? | **Desligado** — só regras YAML |

### Rodada 5 — contrato da tool MCP e destino da saída

| # | Questão | Decisão |
|---|---|---|
| Q16 | A tool MCP publica comentário? | **Não** — read-only, seguindo o precedente de `list_fix_candidates` |
| Q17 | O comando grava arquivo? | **Sim** — paridade com o `-r`, sem imprimir o review no terminal |

### Rodada 6 — contrato SCM

| # | Questão | Decisão |
|---|---|---|
| Q18 | Adicionar `get_pull_request` à ABC? | **Sim** — método **concreto** com default `ScmNotSupportedError` (padrão de `create_release`), implementado nos 4 providers |

### Reformulações e correções registradas (transparência)

1. **A Q4 (rodada 1) afirmou que o rodapé do comentário mostraria `commit abc123f`.** `PullRequestResult` **não
   carrega SHA** — nenhum dos quatro providers extrai `head.sha`. O erro foi **divulgado proativamente** ao
   usuário na rodada seguinte e a decisão virou "rodapé sem SHA".
2. **A recomendação da Q8 original estava errada.** Eu recomendei *"não adicionar método ao contrato; usar
   `list_open_pull_requests` + filtro pelo número"*, assumindo que a listagem devolvia todos os PRs abertos. A
   verificação de §2.5 provou o contrário: nenhum provider pagina, a falha é enviesada para os PRs antigos e é
   silenciosa. A recomendação foi **revertida**, o erro explicitado como *"Minha recomendação da Q8 estava
   errada"*, e a questão foi reformulada na Q18.
3. **O `WebFetch` da documentação do GitLab voltou truncado** e não respondeu nenhuma das quatro perguntas
   pendentes. Resolvido com `WebSearch`, que confirmou: `/changes` deprecado desde 15.7; `old_path`/`new_path`
   presentes por change; `diff` é corpo de hunk puro; `/diffs` é paginado e traz `collapsed`/`too_large`;
   `/changes` traz `overflow`.

### Não-objetivos (explícitos)

- Revisão incremental (só o que mudou desde o último review) — spec §1 declara fora de escopo.
- Comentários inline por linha — mapeado como feature própria em outra análise.
- Forges além dos quatro já cobertos pela abstração.
- Nenhuma chave de configuração nova (a spec §6 sugeria `remote_pr_auto_comment` — descartada).
- Correção do bug de paginação de `list_open_pull_requests` / `check_existing_pull_request`.
- Migração do GitLab de `/changes` para `/diffs`.
- Nada muda no fluxo local: com `cache_scope=""` a chave MD5 local permanece **byte a byte** idêntica.

## 4. Resultado

Plano aprovado em plan mode após 7 rodadas de grill, com 14 decisões fechadas, 10 etapas de implementação na
ordem de execução, e verificação cobrindo os 8 critérios de aceite da spec §7 mais a não-regressão das suítes
de review local e de `gitpr fix`.

A spec §8 pede "um commit/PR isolado por etapa", mas o `CLAUDE.md` do projeto **proíbe commits** — tudo fica na
árvore de trabalho para revisão do usuário.
