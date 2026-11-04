## Completion Report — T6: integração do issue-autoclose no fluxo `gitpr`

### What was done

- **Flags de CLI** (`src/main.py`), declaradas depois de `--explain` e
  recebidas pelo `cli()`:
  - `--close-issue` — aceita a linha sem perguntar (a verificação no forge
    continua acontecendo);
  - `--no-close-issue` — pula a feature nesta execução (nenhum registro lido,
    nenhuma chamada ao forge).
  - Exclusividade validada **logo após `log_usage()`** e antes de
    `ensure_ledger`, do seed do arquivo de projeto e do gate de update: erro
    de uso não pode disparar pergunta de migração nem escrever arquivo.
    Mensagem vermelha em stderr e `Exit(1)`; `not help_flag` mantém
    `gitpr -h --close-issue --no-close-issue` mostrando a ajuda.
- **`_prepare_close_issue(flags, base, may_ask)`** — helper inserido ao lado
  de `_resolve_scm_context`, com imports locais (padrão do `main.py`):
  - `disabled` → `(None, None, None)` sem tocar em nada;
  - **uma** leitura local (`IssueRegistry.load()`); sem registro e sem erro →
    retorno imediato, sem resolver provider nem chamar o forge (não-regressão,
    SPEC #8);
  - com registro (ou erro de leitura): `_resolve_scm_context()` **uma única
    vez**, guardado em `scm_context` — inclusive `(None, None)` em falha, para
    a mensagem de erro não sair duas vezes;
  - branch-alvo lida barato (`resolve_pull_request_base(base,
    verify=False)`, dentro de try/except) **somente** quando a pergunta pode
    acontecer (`may_ask and not flags.accept`), servindo apenas ao aviso do
    ADR-005 — a resolução validada (origem + picker + gravação) continua em
    `_resolve_pr_target`, onde a publicação acontece;
  - `resolve_close_issue(...)` recebe `flags`, `is_tty=may_ask`,
    `target_branch` e `ask=` ligado a `click.confirm`;
  - `outcome.warning` impresso **exatamente uma vez** (amarelo, stderr);
  - devolve `(decision, registry, scm_context)`.
- **Ligação no fluxo**: o seam `close_issue_decision = None` da T5 foi
  substituído pela chamada, colocada **antes de `check_unstaged_files`** —
  portanto antes da TUI de stage e da geração da descrição (ADR-005). No ponto
  onde o SCM era resolvido, `provider, repo_ref = scm_context or
  _resolve_scm_context()`: a tupla `(None, None)` é truthy, então a falha
  resolvida cedo é reutilizada e o erro não é impresso de novo.
- **Limpeza do registro (ADR-007)**:
  - `_clear_close_issue_record(registry, decision)` — não faz nada sem
    registry ou sem decisão (recusa, no-TTY, issue fechada/PR/inexistente,
    outro repositório); qualquer exceção do `clear()` é engolida;
  - `_publish_pr_directly` passou a devolver `bool`: `False` nos dois ramos de
    falha (401 e erro de API), `True` depois da mensagem de sucesso. O ramo
    `--no-edit` limpa o registro apenas quando recebe `True`; o único outro
    chamador (teste de badge) ignora o retorno — compatível;
  - caminho TUI: limpeza depois de `app.run()` e do bloco de reauth, quando
    `app.body_published`;
  - `--no-publish` não publica, então não limpa (o `.md` e o corpo recebem a
    linha, conforme o ADR-004).
- **`PrPublishApp.body_published`** (`src/ui/pr_publish_app.py`): `False` no
  `__init__`; `True` na criação real (`_publish_pr_from_progress`) e na
  atualização bem-sucedida de PR existente (`_push_and_exit`, dentro do `try`
  de `update_pull_request`). O ramo "No, Just Open Existing" também marca
  `final_action = "created"`, mas **não** publica o corpo — por isso o sinal
  dedicado, e não `final_action`.
- **i18n**: 3 chaves novas nos 6 arquivos `langs/*.json`, inseridas na ordem
  alfabética, com CRLF e `indent=2` preservados (1690 chaves por arquivo):
  - `"Adds the closing line (close #N) to the Pull Request description without asking; the issue is still checked."`
  - `"Skips the automatic issue closure for this run (no record is read and no forge call is made)."`
  - `"❌ --close-issue and --no-close-issue cannot be used together."`

### Changed files

| File | Change type | Description |
|------|-------------|-------------|
| `src/main.py` | feat | Flags e exclusividade, `_prepare_close_issue`, reuso do `scm_context`, `_clear_close_issue_record`, `_publish_pr_directly` → bool, limpeza nos dois caminhos de publicação |
| `src/ui/pr_publish_app.py` | feat | `body_published` (init, criação, atualização) |
| `langs/{es,es_es,fr,fr_fr,pt_br,pt_pt}.json` | feat | 3 chaves novas traduzidas em cada arquivo |
| `tests/issue_autoclose/test_close_issue_wiring.py` | test | 19 testes: helper, flags/CLI, `_publish_pr_directly`, limpeza |
| `tests/test_pr_publish_app.py` | test | `body_published` na criação, na atualização e no "just open existing" |
| `docs/claude-code/plans/feat/issue-autoclose/2026-11-02_feat_issue_autoclose_t6_close_issue_cli.md` | docs | Cópia do plano aprovado (regra do CLAUDE.md) |

### Impact

- **Functionality:** a feature passa a funcionar ponta a ponta no fluxo
  padrão do PR: com registro local para o repositório e issue aberta, a
  pergunta acontece antes da TUI de stage, a linha entra no corpo (já via
  `insert_close_line`, T5) e o registro é esquecido apenas quando o corpo foi
  realmente publicado. Sem registro, o fluxo é idêntico ao anterior — a única
  diferença é uma leitura de arquivo local.
- **Performance:** uma leitura de YAML local por execução do ramo PR; rede
  apenas quando há registro (uma verificação `get_issue`, timeout de 5 s) e
  uma resolução de provider reutilizada pelo resto do fluxo.
- **Compatibility:** nenhuma assinatura pública mudou; `_publish_pr_directly`
  agora devolve `bool`, e os chamadores existentes ignoram o retorno. Chaves
  novas de i18n exigem os 6 arquivos atualizados — feito. A pergunta não
  aparece em CliRunner/hook (`is_tty=may_ask` falso), então a suíte não
  trava.
- **Fronteira preservada:** nenhum `requests` novo fora dos providers; o
  registro em `.gitpr/conf/github.yml` não contém token; nenhum log imprime
  token.

### Verificação da suíte

- `python -m pytest tests/issue_autoclose/test_close_issue_wiring.py -q` →
  **19 passed**.
- `python -m pytest tests/test_pr_publish_app.py -q` → **59 passed**.
- `python -m pytest tests/test_i18n.py -q` → **22 passed**.
- `python -m pytest tests/issue_autoclose tests/scm -q` → **434 passed,
  2 skipped, 74 subtests passed**.
- `python -m pytest tests/badge tests/test_diff_failure_cli.py -q` →
  **86 passed**.
- Suíte ampla sem os dois arquivos de UI instáveis (`test_config_app.py`,
  `test_commit_app.py`) e com a deseleção do teste pré-existente que trava
  sem TTY: **3145 passed, 2 skipped, 1 deselected, 197 subtests passed** e
  **8 falhas em `tests/test_plugins.py`** (`TestLoadLinterRulesWithPlugins`:
  `rules` com as 7 regras de segurança em vez de vazio). É o vazamento
  pré-existente e dependente de ordem já documentado nas T1–T5:
  `check_and_update_hooks_scripts()` dispara o sync de hooks (marcador
  `SCRIPTS_INSTALLED_LANG='en_us'` ≠ `SCRIPTS_LANG='pt_br'` no `~/.gitpr/.env`
  real), e o `load_dotenv(ENV_FILE, override=True)` da linha 1754 traz
  `GITPR_LINTER_SECURITY='true'` para o processo, sobrepondo o pin do
  `conftest.py`. Verificações de isolamento:
  - `python -m pytest tests/test_plugins.py -q` → **17 passed**;
  - `python -m pytest tests/issue_autoclose/test_close_issue_wiring.py
    tests/test_plugins.py -q` → **36 passed**;
  - `python -m pytest tests/test_diff_failure_cli.py tests/test_plugins.py -q`
    → **20 passed**.
  Ou seja, o arquivo novo da T6 não é a origem do vazamento; ele depende do
  estado do `~/.gitpr/.env` da máquina e do download de hooks.

### Divergências em relação ao plano

- **`PrContext` não existe.** O SPEC da T6 diz "guardar o resultado em
  `PrContext`", mas `src/` não tem esse objeto (busca por `PrContext`/
  `pr_context` não retorna nada). Mantive o padrão da T5: a decisão vive na
  variável local do ramo do PR, consumida por `insert_close_line` e pela
  limpeza. Criar um contexto novo só para carregar duas variáveis seria
  abstração de uso único.
- **Branch-alvo antecipada é leitura barata**, como aprovado na pergunta do
  plano: a resolução validada (com picker e gravação do arquivo do projeto)
  continua no ponto de publicação. O "reutilizada" do ADR-005 é honrado pelo
  provider/`repo_ref` via `scm_context`.
- **401 na verificação inicial:** aviso do ADR-003 e registro mantido; o
  token só é pedido depois (fluxo atual) e o corpo sai sem a linha nesta
  execução — comportamento especificado para verificação falha.
- **Ctrl+C no prompt do navegador de `_publish_pr_directly`:** o `True` só
  retorna depois dessa pergunta, então um Ctrl+C exato ali mantém o registro
  apesar de o PR ter sido criado. Borda aceita no plano (conservadora:
  prefere manter a registrar a esquecer cedo demais).
- Nenhuma divergência de SPEC/ADR além das acima.

### Next steps

- T7: `GITPR_ISSUE_AUTOCLOSE` / `GITPR_ISSUE_AUTOCLOSE_TIMEOUT` no schema e
  na TUI `config`; ligar `enabled`/`timeout` no `_prepare_close_issue`.
- T8: métrica `issue_autoclose` (`asked`, `accepted`, `skipped_reason`) e
  i18n restante.
- T9: documentação de usuário e entradas no help contextual (`HELP_MAP`).
- Commit sugerido (isolado):
  `feat: wire issue autoclose into the PR flow`
- Aguardar confirmação do usuário antes da T7.
