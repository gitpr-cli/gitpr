## Completion Report — Specs do Backlog, Onda 1 (qualidade + hardening)

Execução do plano [docs/plans/20260827_plano_specs_backlog.md](../../../plans/20260827_plano_specs_backlog.md),
recorte **Onda 1**: itens 1, 2, 3, 4, 11, 12 e 13. Features (7, 8, 9, 10) ficaram fora
do escopo por decisão do usuário. Tudo entregue **unstaged** para revisão.

### Resumo

| Métrica | Antes | Depois |
|---|---|---|
| Testes passando | 269 | **372** |
| Testes falhando | 2 | **0** |
| Cobertura `src/github_api.py` | 9% | **100%** |
| Cobertura `src/ui/pr_publish_app.py` | 51% | **63%** |
| Cobertura `src/net.py` | — (novo) | **100%** |
| Cobertura `src/linter_engine.py` | 91% | 91% |

---

### O que foi feito

#### Itens 5 e 6 — já estavam prontos (nenhuma alteração necessária)

Verificados antes de qualquer código:

* **Item 5:** `src/updater.py` já declara `0.0.37` e o `CLAUDE.md` já está alinhado.
  A flag `--publish` não existe no `CLAUDE.md`, nos 5 READMEs (en/pt_br/pt_pt/es_es/fr_fr),
  em nenhum doc ativo, nem na CLI — só existe `--no-publish`, que é flag vigente e diferente.
  Ocorrências remanescentes estão apenas nos relatórios históricos `v0.0.8`–`v0.0.11`,
  que são snapshots legítimos e não devem ser reescritos.
* **Item 6:** o `HELP_MAP` já aponta para `understanding_chat_functionality.md`
  ([main.py:161](../../../../src/main.py#L161)) e `metricas-telemetria.md`
  ([main.py:175](../../../../src/main.py#L175)). Os **15** destinos do `HELP_MAP` foram
  verificados um a um: todos existem em `docs/`.

#### Item 11 — Hardening de subprocesso, timeouts e DNS-bounding

* **`shell=True` eliminado** em `_run_external_linter`. O comando agora é montado como
  lista argv. Detalhe crítico de Windows: `shlex.split()` puro destruiria caminhos com
  barra invertida (`C:\tools\lint.exe` → `C:toolslint.exe`), então o split usa regras
  POSIX de aspas **com escaping desligado** (`_split_command`). E como `CreateProcess`
  só acrescenta `.exe`, o executável passa por `shutil.which()` para que shims de
  PATHEXT como `npx.cmd` continuem funcionando sem shell.
* **Timeout explícito na SDK de IA** nas 4 construções de client (`call_ai_model` e
  `call_ai_chat`, Gemini e OpenAI-compatíveis), via `GITPR_AI_TIMEOUT` (default 600s).
  As unidades diferem e foram verificadas contra os SDKs instalados: google-genai usa
  **milissegundos** (`http_options.timeout`), openai usa **segundos**.
* **DNS-bounding formalizado** em `src/net.py` (`bounded_urlopen`). O `timeout` do
  urllib não limita resolução de DNS — no Windows um resolver travado bloqueia
  `getaddrinfo()` indefinidamente. O padrão já existia duplicado em `core.py` e
  `mcp_server.py`; agora está num módulo sem dependências internas, aplicado a
  `i18n.py` e `ai_providers.py` conforme o item pedia.
* **`GITPR_LINTER_TIMEOUT`** (default 120s) extraído do valor que estava hardcoded.

#### Item 12 — `external_linters` full-file + filtro Checkstyle por arquivo

* **Bug corrigido:** o cruzamento usava apenas número de linha. Um linter com config
  de projeto (ou seguindo imports) reporta violações de **outros** arquivos; se a linha
  coincidisse com uma linha adicionada, a violação era atribuída ao arquivo errado.
  `_parse_checkstyle_xml` agora carrega o `<file name=...>` e `_checkstyle_file_matches`
  compara por sufixo com separadores normalizados (o Checkstyle reporta caminho absoluto,
  o diff é relativo). Um relatório sem `name=` é aceito, para não zerar linters que o omitem.
* **Modo full-file:** `--input` agora executa os `external_linters`. Sem diff para
  intersectar, toda violação do arquivo conta — que é o objetivo de uma auditoria full-file.
* Lógica compartilhada extraída para `_collect_external_alerts`, usada pelos dois modos.

#### Item 1 — Guard de i18n para chaves sem entrada

**Causa raiz das 2 falhas pré-existentes:** o commit `9a9affb` adicionou 91 chaves por
arquivo (547 → 638) mas deixou duas asserções obsoletas.

* **`test_key_parity_and_count`:** o número mágico `547` foi removido. Paridade entre
  idiomas é o invariante real; o total exato garantia falha futura a cada adição legítima.
  Mantido um piso para pegar escrita truncada.
* **`test_identity_keys_with_braces_allowlist`:** eram 9 chaves identidade, não 1.
  Investigadas uma a uma — **todas** são fragmentos de prompt de IA que devem permanecer
  em inglês por design, inclusive `Action: {status}` e `AI Reason: {reason}`, que parecem
  UI mas alimentam o prompt ([main.py:1030](../../../../src/main.py#L1030): *"Translate the
  dictionary list into AI-readable text"*). Allowlist explícita em `AI_PROMPT_PREFIXES`;
  qualquer identidade nova que não seja prompt falha nominalmente como débito de tradução.
* **Guard `missing == 0` (`TestNoMissingKeys`)** implementado com extração **via AST**,
  não regex. Motivo: o regex de `tests/sync_i18n.py` para no primeiro fragmento de
  literais concatenados, o que fazia **21 chaves reais parecerem ausentes** e suas formas
  completas parecerem órfãs. O parser do Python funde concatenação implícita num único
  `Constant`, batendo com a string que o runtime monta. Resultado: 638 chaves em código
  = 638 nos dicionários, **0 ausentes e 0 órfãs**.
* Guard validado na prática: injetei um `__()` com chave inexistente (multi-linha) em
  `src/`, o teste falhou nomeando a chave completa, e o arquivo-probe foi removido.

#### Item 4 — Scripts one-off de i18n

Avaliação individual, critérios (a) referência ativa e (b) lógica reutilizável:

| Script | Referências ativas | Decisão |
|---|---|---|
| `fix_pt_br.py` | 0 | Remover — tabela hardcoded de 2026-08 |
| `fix_pt_br_pass2.py` | 0 | Remover — idem |
| `final_fix.py` | 0 | Remover — idem |
| `_temp_check_i18n.py` | 0 | Remover — substituído por `TestNoMissingKeys` |
| `generate_lang_files.py` | 0 | Remover — bootstrap fr/es, os 6 arquivos já existem |

Nenhum é citado em CI (`.github/workflows/pr-review.yml`), Pipfile, pyproject ou hooks.
`tests/test_i18n.py` depende **apenas** de `fix_mangled_i18n_keys.py`, que **não** está
na lista e permanece. Além de obsoletos, eram perigosos: reescrevem `langs/*.json` a
partir de tabelas antigas e corromperiam os dicionários atuais de 638 chaves.

> Arquivamento via histórico do Git. Para restaurar qualquer um:
> `git checkout HEAD -- scripts/<nome>.py`

#### Item 3 — Cobertura de `pr_publish_app.py` e `github_api.py`

* **`tests/test_github_api.py`** (30 testes, 9% → **100%**): sucesso 201, auth 401/403,
  rate limit, validação 422 com detalhe de campo, `ConnectionError`/`Timeout` retornando
  o sentinela `status 0`, conflito de merge 405, SHA desatualizado 409, e verificação de
  que campos omitidos não são apagados no `update_pull_request`.
* **`tests/test_pr_publish_app.py`** (33 testes, 51% → **63%**): staging via widget,
  transições de estado do F3, save local com valores editados, e cancelamento não-destrutivo.
* **Mutation testing** para provar que os testes não passam por acidente: revertendo o
  fix de staging (leitura do dicionário paralelo em vez do `SelectionList`) **4 testes
  falham**; removendo `skip_linter=True` do resume de `--no-verify` **1 teste falha**.
  Ambos são bugs históricos reais do projeto. Fonte restaurada e verificada com `git diff`.

#### Item 2 — Roteiro manual E2E

[docs/testing/manual_pr_publisher_e2e.md](../../../testing/manual_pr_publisher_e2e.md):
7 pré-condições verificáveis, config de linter de referência fixa, e 5 cenários com
critério objetivo PASS/FAIL por etapa — violação em arquivo rastreado, **abort
não-destrutivo** (o mais importante: confirma ausência de commit/push/PR), arquivo novo
não rastreado, publicação após correção, e resume por `--no-verify` sem loop.

O cenário C documenta comportamento que surpreende usuários: `get_git_diff()` roda
`git diff HEAD`, que por definição exclui arquivos não rastreados — é preciso `git add`
para que entrem na análise.

#### Item 13 — `LINTER_PRESETS_VERSION`

[docs/version-markers.md](../../../version-markers.md) formaliza o padrão e documenta
os **5** marcadores (`LANG_VERSION`, `SMART_EXCLUDES_VERSION`, `THINKING_WORDS_VERSION`,
`LINTER_PRESETS_VERSION`, `SCRIPTS_VERSION`) com recurso, cache local, constante de
comparação e módulo dono — todos conferidos no código. Inclui a ordem correta de
publicação (**template no `main` antes** do bump de `__lang_version__`; o inverso fixa
clientes no arquivo velho sob marcador novo) e deixa explícito que
`LINTER_PRESETS_VERSION` é independente do `__version__` do GitPR. Linkado a partir de
`ARCHITECTURE.md` §16.

---

### Arquivos alterados

| Arquivo | Tipo | Descrição |
|---|---|---|
| `src/net.py` | feat | **Novo.** `bounded_urlopen` — padrão DNS-bounding formalizado, sem deps internas |
| `src/linter_engine.py` | fix | argv sem shell + `shutil.which`; Checkstyle por arquivo; full-file com external linters |
| `src/ai_providers.py` | fix | Timeout explícito nos 4 clients; `bounded_urlopen` no lugar de urllib direto |
| `src/config.py` | feat | `GITPR_AI_TIMEOUT` / `GITPR_LINTER_TIMEOUT` + getters com fallback |
| `src/i18n.py` | fix | Download de traduções via `bounded_urlopen` |
| `tests/test_github_api.py` | test | **Novo.** 30 testes, 100% de cobertura |
| `tests/test_pr_publish_app.py` | test | **Novo.** 33 testes de TUI e transições de estado |
| `tests/test_net_timeouts.py` | test | **Novo.** 12 testes de DNS-bounding e timeouts |
| `tests/test_i18n.py` | test | Guard `missing == 0` via AST; 2 asserções obsoletas corrigidas |
| `tests/test_external_linters.py` | test | +19 testes: injeção de shell, path matching, full-file |
| `tests/test_chat_backend.py` | test | 3 testes migrados para o novo caminho de download |
| `docs/version-markers.md` | docs | **Novo.** Padrão Version Marker + os 5 marcadores |
| `docs/testing/manual_pr_publisher_e2e.md` | docs | **Novo.** Roteiro manual, 5 cenários |
| `docs/ARCHITECTURE.md` | docs | §16 linkando `version-markers.md` |
| `docs/reports/relatorio_estado_v0.0.12.md` | docs | Backlog podado; 10 itens marcados como concluídos |
| `Pipfile` | chore | `pytest-cov` em dev-packages (números de cobertura reproduzíveis) |
| `.gitignore` | chore | Artefatos `.coverage` |
| `scripts/fix_pt_br.py` … `generate_lang_files.py` | chore | **Removidos** (5 arquivos, 691 linhas) |

---

### Impacto

* **Funcionalidade:** `--input` passa a rodar linters externos (capacidade nova).
  Violações de linter externo deixam de ser atribuídas ao arquivo errado. Nenhuma
  mudança de comportamento nos fluxos existentes de diff.
* **Segurança:** a única ocorrência de `shell=True` foi eliminada. Um caminho como
  `a; rm -rf ~` agora chega como um argumento literal único — coberto por teste.
  Chamada de IA travada não pode mais pendurar a CLI indefinidamente.
* **Performance:** neutra. `shutil.which()` adiciona uma resolução por invocação de
  linter, irrelevante frente ao custo do subprocesso.
* **Compatibilidade:** duas mudanças de contrato **internas e intencionais** —
  `_parse_checkstyle_xml` agora inclui a chave `file`, e `load_chat_commands` usa
  `bounded_urlopen` (None sinaliza falha). Ambas exigidas pelos itens 11/12; os testes
  correspondentes foram atualizados. Nenhuma quebra de API pública, nenhuma migração.
* **Config:** duas variáveis novas em `DEFAULT_CONFIG`, ambas com default seguro —
  instalações existentes não precisam de ação.

---

### ⚠️ Alterações não originadas nesta tarefa (detectadas e revertidas)

Durante a sessão, dois arquivos que **não foram tocados por esta tarefa** apareceram
modificados no working tree (mtime idêntico, `2026-08-27 13:48:44`, 13 ms de diferença —
processo automatizado, não edição manual; não há hooks em `.claude/hooks/`):

* `GEMINI.md` — regra de destino de relatório trocada de `docs/gemini/reports/` para
  `docs/claude-code/reports/`, **revertendo** uma decisão deliberada.
* `docs/gemini/reports/develop_natan/2026-08-26_restore_gemini_reports_dir.md` —
  **esvaziado** (17 linhas → 0 bytes). Esse arquivo é justamente o relatório que
  documentava a decisão revertida.

**Ambos foram restaurados** a partir do `HEAD`, com aprovação do usuário. O relatório
voltou às 17 linhas e o `GEMINI.md` voltou a apontar para `docs/gemini/reports/`.
Nenhum dos dois aparece mais como modificado no `git status`.

A origem da alteração permanece desconhecida — vale ficar atento caso reapareça,
já que o padrão (esvaziar um arquivo rastreado) é destrutivo e silencioso.

---

### Próximos passos

1. **Risco descoberto — `tests/sync_i18n.py`:** o extrator por regex trunca literais com
   concatenação implícita. Rodar o script hoje reescreveria 21 chaves pela metade e
   perderia suas traduções. O guard do item 1 usa AST e não depende dele, mas migrar o
   script é recomendado. Ficou fora do escopo por decisão explícita do item 1
   ("não inclui alteração do mecanismo de extração já existente").
2. **Itens 7–10 da Onda 2:** gráficos ASCII no dashboard, pipeline de release,
   comando `--init` e novos provedores de IA.
3. **Traduções dos docs novos:** `version-markers.md` e `manual_pr_publisher_e2e.md`
   foram escritos em inglês (canônico). Localizações `.pt_br/.pt_pt/.es_es/.fr_fr`
   podem seguir a convenção do projeto, se desejado.
4. **Executar o roteiro manual** do item 2 antes do próximo release — ele cobre
   justamente o que a suíte headless não alcança.

---

**Relatório gerado em:** 2026-08-27
**Branch:** `develop_natan`
**Suíte:** 372 passando, 0 falhando
