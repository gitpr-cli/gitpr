# Plano — `gitpr review-pr <n>` (review de PR remoto já aberto)

## Contexto

A spec [20260917_skill_gitpr_review_pr_spec.md](docs/plans/20260917_skill_gitpr_review_pr_spec.md) pede que o GitPR revise um PR **já aberto na forge**, buscando o diff pela API — sem exigir que o revisor tenha feito checkout da branch. Hoje o review (`gitpr -r` / `-f`) só opera sobre o diff local, o que exclui quem foi convidado a revisar o PR de outra pessoa.

O grill (§0 da spec, obrigatório) revelou que **boa parte do trabalho já existe**: `get_pull_request_diff` está implementada e testada nos 4 providers, o motor de review (`generate_pr_content`) já recebe uma string de diff e é agnóstico à origem, e o map-reduce é genérico sobre texto. O trabalho novo real é a orquestração, a normalização do diff remoto e a superfície de CLI/MCP.

O grill também corrigiu **quatro premissas erradas da spec**:

| Premissa da spec                                          | Realidade verificada                                                                    |
| --------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| Criar `src/application/use_cases/` e `src/domain/review/` | Não existem; ADR-003 e ADR-004 rejeitam explicitamente camadas DDD                      |
| "Confirmar ou implementar `get_pull_request_diff`"        | Já existe na ABC ([base.py:154](src/infrastructure/scm/base.py#L154)) e nos 4 providers |
| Atualizar `config.schema.yml`                             | Não existe; config é dotenv plano + `DEFAULT_CONFIG` + `config_schema.py`               |
| Reusar `render_review_result`                             | Não existe; a renderização é inline em [main.py:1364-1433](src/main.py#L1364-L1433)     |

E encontrou **três defeitos latentes** que a feature exporia:

1. **GitLab descarta o nome do arquivo.** [gitlab_provider.py:241-251](src/infrastructure/scm/gitlab_provider.py#L241-L251) junta `changes[].diff` e ignora `old_path`/`new_path`, que a API já devolve. O `diff` do GitLab é só o hunk — a IA revisaria trechos órfãos sem saber a que arquivo pertencem, e nem o chunker nem o filtro de excludes funcionariam. O campo `overflow` (diff cortado por limite de tamanho) também é ignorado: um MR grande seria revisado pela metade **sem aviso**, e publicado assim.
2. **`get_pull_request` não existe.** A única alternativa (`list_open_pull_requests` + filtro por número) busca **uma página só** nos 4 providers, sem `per_page`/`page`/cursor. Como as forges ordenam do mais novo para o mais antigo, a falha é enviesada para os PRs mais antigos, é **silenciosa** (lista vazia = indistinguível de "não existe") e só cobre PRs abertos — não distingue mesclado de inexistente.
3. **`gitpr fix` re-deriva o diff localmente.** [apply_fix.py:110-122](src/fix/apply_fix.py#L110-L122) chama `get_git_diff()` em vez de usar o diff que foi revisado, então um review remoto parearia com a árvore errada.

Decisões de arquitetura tomadas no grill, todas alinhadas aos ADRs vigentes: pacote `src/review/` (espelha `src/fix/`, ADR-004), `DiffSource` como contrato **sem entrar no motor** (que já é agnóstico), e subcomando em vez de flag (ADR-002).

---

## Decisões fechadas

| #   | Decisão                                                                                                            |
| --- | ------------------------------------------------------------------------------------------------------------------ |
| 1   | Pacote `src/review/` com 4 módulos de responsabilidade única                                                       |
| 2   | Subcomando `gitpr review-pr <n>` com `--post-comment` e `--provider`                                               |
| 3   | `DiffSource` como contrato; `generate_pr_content` **não** muda de assinatura (só ganha parâmetros opcionais)       |
| 4   | Azure: falha rápida via atributo de capacidade na ABC + validação do conteúdo                                      |
| 5   | Renderização extraída e compartilhada com o fluxo local                                                            |
| 6   | Comentário = review + rodapé de proveniência (sem SHA — `PullRequestResult` não o carrega); sempre comentário novo |
| 7   | GitLab: cabeçalhos sintéticos + tratamento de `overflow` (sem migrar para `/diffs`)                                |
| 8   | `gitpr fix` passa a preferir o diff gravado no registro de cache                                                   |
| 9   | Linter externo não roda em PR remoto (só regras YAML)                                                              |
| 10  | Tool MCP `review_remote_pr` **read-only** (segue o precedente de `list_fix_candidates`)                            |
| 11  | Saída: grava `.txt` igual ao `-r`, sem imprimir o review no terminal                                               |
| 12  | `get_pull_request` concreto na ABC + implementação nos 4 providers                                                 |
| 13  | Nenhuma chave de configuração nova                                                                                 |
| 14  | Docs EN + pt_br (os outros locales ficam para um passo de tradução)                                                |

---

## Etapas

### 0. Levantamento
Gravar `docs/survey/20260917_skill_gitpr_review_pr_surveyfacts.md` no formato dos cinco arquivos existentes: H1, blockquote (sessão, data, branch, tarefa verbatim, plano, base de domínio), `## 1. Contexto da tarefa`, `## 2. Fatos levantados` com tabelas `| Fato | Onde |` citando `path:line`.

### 1. Contrato SCM — `get_pull_request` e capacidade de diff
- [base.py](src/infrastructure/scm/base.py): adicionar **método concreto** (não `@abstractmethod`) `get_pull_request(self, repo: RepoRef, pr_id: str | int) -> PullRequestResult` com default levantando `ScmNotSupportedError` — mesmo padrão de `create_release` ([base.py:206-219](src/infrastructure/scm/base.py#L206-L219)). Sendo concreto, `tests/scm/test_contract.py:64-76` continua verde.
- Adicionar o atributo de classe `supports_reviewable_diff = True` na ABC; `False` em [azure_devops_provider.py](src/infrastructure/scm/azure_devops_provider.py).
- Implementar `get_pull_request` nos 4 providers (um GET cada): GitHub `GET /repos/{o}/{r}/pulls/{n}`, GitLab `GET .../merge_requests/{iid}`, Bitbucket `GET .../pullrequests/{n}`, Azure `GET .../pullrequests/{n}`. Reusar os mapeadores `_to_result` existentes.
- **GitLab** [get_pull_request_diff](src/infrastructure/scm/gitlab_provider.py#L241-L251): emitir `diff --git a/{old_path} b/{new_path}` + `--- a/{old_path}` + `+++ b/{new_path}` antes de cada hunk, e levantar `ScmProviderError` quando a resposta trouxer `overflow: true`.
- Atualizar os fixtures de teste do GitLab — os atuais fabricam linhas `diff --git` no mock, então não capturam o defeito.

### 2. Parsing puro — `src/diff_parser.py`
Adicionar um divisor de seções por arquivo (não existe hoje). Precedente do ADR-004: parsing puro de diff unificado mora aqui, não no pacote da feature. Expor uma dataclass `PatchSection(path, text)` no estilo de `PatchSummary`, e reusar os helpers privados existentes (`_header_path`, `_strip_diff_prefix`, `_remember_file`, [diff_parser.py:111-240](src/diff_parser.py#L111-L240)).

### 3. Pacote `src/review/`
- `diff_source.py` — `DiffOrigin` (enum) e `DiffSource` (dataclass) conforme spec §3. Dados puros, sem I/O.
- `diff_normalizer.py` — filtra seções cujo caminho casa com os padrões brutos de smart-excludes, usando `split_patch_sections`. Precisa de um acessor de padrões **brutos** ao lado de `_load_smart_excludes` / `_get_raw_docs_patterns` em [core.py:162-333](src/core.py#L162-L333) (hoje só existe o pathspec `:(exclude)`, inaplicável a um diff vindo da API). Respeitar `GITPR_SKIP_SMART_EXCLUDES`.
- `render.py` — `render_review_result(content, linter_results, output_filename) -> str`: compõe alertas + conteúdo e grava o `.txt`. Extraído de [main.py:1407-1430](src/main.py#L1407-L1430); o fluxo local passa a chamá-lo sem mudança de comportamento.
- `remote_pr.py` — `review_remote_pr(pr_number, scm_provider, ai_provider, repo_ref, post_comment=False, skill_context=None) -> ReviewRemotePrResult` conforme spec §3.

### 4. Motor de review — alterações **aditivas**
Em [generate_pr_content](src/core.py#L745), acrescentar apenas parâmetros opcionais, com defaults que preservam o caminho local byte a byte:
- `cache_scope=""` — concatenado **só** nas chamadas de cache ([core.py:873](src/core.py#L873) e [core.py:1062](src/core.py#L1062)), **nunca** no prompt enviado à IA. Com `""` a chave MD5 é idêntica à de hoje: zero invalidação de cache local.
- `store_diff=False` — repassa o diff para `save_cached_response`, que ganha um campo de topo opcional `"diff"`. O caminho local passa `True` (decisão 8), o que também remove a fragilidade atual do `fix`.

O campo vai no topo do registro, **não** em `response["meta_raw"]` — `meta_raw` é slot de telemetria (tokens/duração), lido só por `src/metrics.py`.

### 5. `gitpr fix`
[apply_fix.py:110-122](src/fix/apply_fix.py#L110-L122): `reviewed_diff()` passa a preferir `record.get("diff")` e cai no comportamento atual quando ausente — registros antigos seguem funcionando. `REVIEW_ACTION_TYPES` ([cache.py:88](src/cache.py#L88)) não muda: o review remoto usa `action_type="review"`, então `resolve_last_review` o encontra.

### 6. Linter
[parse_diff_and_lint](src/linter_engine.py#L209) ganha `skip_external=False`, gateando os dois pontos de chamada ([linter_engine.py:247](src/linter_engine.py#L247) e [linter_engine.py:303](src/linter_engine.py#L303)). Forma de retorno inalterada (`{"errors": [], "warnings": []}`). O caminho remoto passa `skip_external=True` — o bridge roda um binário contra arquivos **locais**, que estão na revisão errada, e isso iria para um comentário público.

### 7. Subcomando CLI
Em [main.py](src/main.py), espelhando [fix()](src/main.py#L1971-L2025):
- `@cli.command(context_settings={"help_option_names": ["-h", "--help"]}, epilog=...)` apontando para `get_doc_url("review-pr.md")`.
- `@click.argument("pr_number", type=int)`, `--post-comment` (flag), `--provider` (default `None`, caindo em `get_ai_provider()`).
- Reusar [`_resolve_scm_context()`](src/main.py#L2534-L2575) para provider + `RepoRef`; se não resolver, erro apontando para `--init`.
- **Não** chamar `check_unstaged_files` (subcomandos não chamam, e o diff não vem da árvore local).
- Saída via `resolve_output_path("OUTPUT_FILE_NAME_REVIEW", ...)` com `{branch}` = branch de origem do PR sanitizada — sem env var nova.
- `--post-comment` só publica se o review veio não-vazio; falha nunca posta.

### 8. Tool MCP
`review_remote_pr(pr_number, provider="")` em [mcp_server.py](src/mcp_server.py), read-only, reusando `src/review/remote_pr.py` e registrada com `@mcp.tool(...)`. Não escreve artefato `.txt` (tools MCP não escrevem) e não adiciona skill type — logo a obrigação do ADR-004 item 4 não se aplica.

### 9. Documentação e i18n
- `docs/review-pr.md` + `docs/review-pr.pt_br.md` (convenção `foo.md` / `foo.<locale>.md`).
- `README.md` + `README.pt_br.md`.
- `docs/plans/glossary-review-pr.md` (glossário: definindo *diff revisável*, *review de PR remoto*, *DiffSource*, *origem do diff*) e `docs/plans/ADR-005-review-pr-subcommand.md` — a divergência subcomando-vs-flag da spec §1 e o "DiffSource sem entrar no motor" são decisões que um leitor futuro vai querer justificadas. Seguir o cabeçalho dos ADRs existentes (Status/Data/Contexto/Glossário).
- `CLAUDE.md`: tabela de comandos + tabela de tools MCP (13 → 14).
- Rodar `python tests/sync_i18n.py` e **traduzir** as chaves novas nos 6 `langs/*.json`. Restrição dura de [test_i18n.py:177-243](tests/test_i18n.py#L177-L243): chave nova com `{}` deixada como identidade **reprova a suíte**, e toda chave `__()` nova precisa existir nos seis arquivos.

### 10. Testes — `tests/review/`
`test_diff_source.py`, `test_diff_normalizer.py`, `test_remote_pr.py`, `test_review_pr_cli.py` (estilo `unittest.TestCase`, CLI via `CliRunner` contra `src.main.cli`, `requests` patchado no módulo do provider, como em [tests/scm/](tests/scm/)). Cobrir os critérios de aceite da spec §7: paridade de pipeline local vs remoto, map-reduce em diff remoto grande, ausência de colisão de cache, `add_comment` chamado só com `--post-comment`, PR inexistente/fechado sem nenhuma chamada de IA (validado por mock), e Azure falhando antes da IA.

---

## Verificação

```bash
# Não-regressão primeiro — é a etapa mais sensível
python -m pytest tests/ -v

# Suítes novas
python -m pytest tests/review/ tests/scm/ -v

# Paridade local vs remoto (mesmo diff, mesmo resultado)
python -m pytest tests/review/test_remote_pr.py -k parity -v

# i18n: chaves presentes nos 6 arquivos e traduzidas
python -m pytest tests/test_i18n.py -v
```

Pontas soltas manuais, contra um repositório real com PR aberto:

```bash
gitpr review-pr <n>                    # grava .gitpr/reports/review/*.txt
gitpr review-pr <n> --provider deepseek
gitpr review-pr <n> --post-comment     # comentário aparece no PR
gitpr fix --list                       # acha o review remoto e usa o diff gravado
gitpr -r                               # fluxo local inalterado
gitpr review-pr <n> --help             # epilog com link da doc
gitpr-mcp --list                       # 14 tools registradas
```

Criteria de pronto: `gitpr review-pr <n>` funciona de ponta a ponta, a saída é visualmente idêntica à do review local exceto pelos metadados de origem, e a suíte inteira passa — em especial os testes já existentes de review local e de `fix`.

---

## Observações fora de escopo

- **Bug latente de paginação.** `list_open_pull_requests` e `check_existing_pull_request` buscam uma página só nos 4 providers. O segundo é alcançável em produção: o PR Publisher o chama antes do push ([pr_publish_app.py:1209](src/ui/pr_publish_app.py#L1209)), então num repositório movimentado ele não acha um PR já aberto e o usuário cria uma **duplicata**. Não é corrigido aqui; fica registrado.
- **`ADR-002` duplicado** em `docs/plans/` (`ADR-002-gitpr-release-subcommand.md` e `ADR-002-reviewer-suggestion.md`) — o novo ADR usa o número 005 para não colidir.
- **A spec §8 pede um commit isolado por etapa, mas o CLAUDE.md proíbe commits.** Tudo fica na árvore de trabalho para você revisar e commitar; o diff será agrupado por etapa na descrição final.
- Revisão incremental (só o que mudou desde o último review) e comentários inline por linha continuam fora de escopo, como a spec §1 define.
- Nenhuma chave de config nova, então nada a registrar em `DEFAULT_CONFIG` nem em `config_schema.py`.
