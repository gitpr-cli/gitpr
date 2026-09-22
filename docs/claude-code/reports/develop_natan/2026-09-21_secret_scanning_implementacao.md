## Completion Report — Implementação do Secret Scanning no linter

> Este arquivo é o relatório da **implementação**. O relatório do desenho
> (sessão de grill) é [2026-09-21_gitpr_secret_scanning.md](2026-09-21_gitpr_secret_scanning.md);
> o nome foi separado para não sobrescrever aquele.

### What was done

O desenho aprovado em `docs/plans/20260921_skill_gitpr_secret_scanning_plan.md`
foi implementado por completo, com as seis correções que a verificação da sessão
anterior encontrou (item por item abaixo, em "Desvios do plano").

1. **As sete regras** (`src/security_ruleset.py`, novo): cinco de nível `error`
   (AWS access key ID, token do GitHub, token do Slack, chave de API do Google,
   bloco de chave privada) e duas de `warning` (connection string de banco com
   credenciais, atribuição genérica de credencial com filtro de placeholders).
   Todas com `extensions: ["*"]` e regex em raw string.
2. **O motor** (`src/linter_engine.py`): `"*"` em `extensions` passou a significar
   "todo arquivo, inclusive os sem sufixo". Regra com `extensions: ["py"]` e regra
   sem a chave `extensions` mantêm o comportamento anterior.
3. **O merge** (`src/config.py`): `load_linter_rules()` estende a lista com o
   ruleset depois das regras do projeto e dos plugins, que ficam intactos.
4. **As duas chaves** em `DEFAULT_CONFIG` e no `config_schema.py` (categoria
   `linter`, `KIND_BOOL` e `KIND_STR`).
5. **i18n:** 11 chaves novas em cada um dos 6 arquivos (7 mensagens de regra +
   rótulo e descrição das 2 chaves de config), redigidas em pt_br, pt_pt, es_es/es
   e fr_fr/fr.
6. **`tests/test_security_ruleset.py`** (novo, 61 testes) e o pin no
   `tests/conftest.py`.
7. **Documentação:** `docs/linter-regras-customizadas.md` (§2 ganhou `level` e o
   curinga `"*"`; §7 nova, sobre o ruleset) e `docs/git-hooks-locais.md` (§2,
   fazendo a promessa de "senhas" virar verdade), ambas em EN e pt_br; a seção do
   linter no `CLAUDE.md` com as duas variáveis na lista de ambiente; a nota de
   release no `CHANGELOG.md`.

**Nenhuma alteração foi commitada** — tudo no working tree, como manda o
`CLAUDE.md`.

### Changed files

Somente o que **esta** tarefa alterou:

| File | Change type | Description |
|------|-------------|-------------|
| `src/security_ruleset.py` | feat | **Novo.** As sete regras, docstring explicando por que vivem no pacote |
| `src/linter_engine.py` | feat | `"*"` em `extensions` = todo arquivo, inclusive sem sufixo |
| `src/config.py` | feat | Duas chaves em `DEFAULT_CONFIG` (hunk de `+48,5`) e o merge no fim de `load_linter_rules()` (`+617,12`) |
| `src/config_schema.py` | feat | Dois `ConfigField` na categoria `linter`, `KIND_BOOL` e `KIND_STR` |
| `tests/test_security_ruleset.py` | test | **Novo.** 61 testes: forma, compilação, positivos/negativos, placeholders, roteamento de nível, curinga, merge, default, não-eco, integração, traduções |
| `tests/conftest.py` | test | `GITPR_LINTER_SECURITY=false` pinado antes de qualquer import de projeto, com o parágrafo que explica as três razões |
| `langs/{pt_br,pt_pt,es_es,es,fr_fr,fr}.json` | feat | +11 chaves por arquivo (1140 → 1151), CRLF preservado |
| `docs/linter-regras-customizadas.md` + `.pt_br.md` | docs | `level` e `"*"` documentados; §7 nova com a tabela das regras, as duas chaves de escape e as lacunas |
| `docs/git-hooks-locais.md` + `.pt_br.md` | docs | Seção sobre a varredura embutida; `--no-verify` contrastado com o opt-out por config |
| `CLAUDE.md` | docs | Seção "Static local linter" e as duas chaves na lista de variáveis de ambiente |
| `CHANGELOG.md` | docs | Seção `## [1.3.0] - 2026-09-21` |
| `docs/claude-code/reports/develop_natan/2026-09-21_secret_scanning_implementacao.md` | docs | Este relatório |

#### Atenção: a árvore carrega mais duas tarefas não commitadas

`git status` mostra arquivos que **não** são desta tarefa e já estavam no working
tree antes dela. Para os commits saírem atômicos como o `CLAUDE.md` pede:

| Arquivo | Tarefa de origem |
|---------|------------------|
| `src/i18n.py`, `tests/test_core.py`, `tests/test_metrics.py`, `tests/test_config_app.py`, `.github/workflows/tests.yml` | [Suíte determinística e CI](2026-09-21_suite_deterministica_e_ci.md) |
| `tests/test_net_timeouts.py`, e o hunk `@@ -289 +294 @@` de `src/config.py` | [AI timeout default drift](2026-09-21_ai_timeout_default_drift.md) |
| `docs/plans/20260919_split_atomic_commits_hunk.md` (+185 linhas) | `feat(split)` — documentação do comando de commits atômicos |
| `tests/conftest.py` | **as duas**: os três pins de idioma/log/update são da suíte determinística; o quarto, `GITPR_LINTER_SECURITY`, é desta tarefa |

O `tests/conftest.py` não dá para separar por hunk sem reescrever o docstring; se
a intenção for um commit por tarefa, ele vai inteiro no primeiro ou no último.

### Desvios do plano aprovado, e por quê

1. **`get_config()` não existe** — o snippet do plano produziria `NameError`. O
   merge usa `_env_bool_default_true()` e `load_dotenv(ENV_FILE)` + `os.getenv()`.
2. **`tests/sync_i18n.py` não foi rodado.** É a armadilha documentada em
   `.claude/memory/i18n-sync-canonicos-roundtrip.md` (23 chaves destruídas em
   2026-09-05 e 2026-09-13). No lugar: script cirúrgico de duas passagens —
   valida os 6 arquivos inteiros em memória, e só escreve se nenhum falhar. Cada
   arquivo foi antes verificado como round-trip byte a byte fiel do próprio
   parse, o que é o que garante que o merge não perde valor existente.
3. **`(?i)` global trocado por `(?i:...)` com escopo**, que não depende da posição
   no padrão.
4. **As fixtures de segredo são montadas por fragmentos concatenados**, inclusive
   a palavra-chave: `CREDENTIAL_LINE = "pass" + 'word = "{}"'`. Medido — duas
   linhas do arquivo de teste casavam com a própria regra genérica (o f-string que
   montava a linha de credencial a partir de um `{value}`, e o literal do teste de
   sufixo), e o hook deste repositório rodaria sobre elas.
   **A primeira versão deste relatório caiu na mesma armadilha**: ao listar as
   linhas bloqueantes dos documentos do plano, ela citava os literais por extenso e
   passou a ter duas linhas de `error` e três de aviso. Foi reescrita com a forma
   ilustrativa (`AKIA…`, `-----BEGIN … PRIVATE KEY-----`), e a varredura de hoje
   sobre os 18 arquivos que escrevi — com as sete regras reais — fecha em **0
   ocorrências**. É a medida de quão fácil é pisar nisso: nem um documento que
   existe justamente para explicar o problema escapou dele de primeira.

### Verification

| # | Verificação | Critério do plano | Resultado medido |
|---|-------------|-------------------|------------------|
| 1 | `pytest tests/test_config_schema.py tests/test_plugins.py tests/badge/` | verde — o pin segurou os três | **223 passed** (junto com o módulo novo e o `test_i18n`) |
| 2 | `pytest tests/test_security_ruleset.py -q` | verde | **61 passed** |
| 3 | `pytest tests/test_i18n.py -q` | paridade, sem órfãs | verde |
| 4 | `git diff --stat langs/` | +7 por arquivo, valores intactos | **+11 chaves por arquivo** (7 mensagens + 4 de config), 1140 → 1151 nos 6; `added=11 removed=0 preexisting-changed=0` |
| 5 | `pytest tests/ -q` + mtime do perfil | verde, perfil intocado | **1837 passed, 2 skipped** (baseline 1776 + 61); `~/.gitpr/.env` e `~/.gitpr/langs/*.json` com mtime e tamanho **idênticos** |
| 6 | E2E em repo de rascunho | exit 0 limpo; exit 1 com segredo; hook aborta; opt-out passa | todos os cinco casos confirmados (abaixo) |
| 7 | O relatório do E2E não repete o valor | não ecoa | `grep` pelo valor nos relatórios gerados e no stdout: **0 ocorrências** |
| 8 | Primeira execução real semeia as chaves | as duas no `~/.gitpr/.env` | já ocorrido — ver "Achados", item 4 |

**E2E, medido no repo de rascunho** (com `gitpr` instalado em modo editable sobre
esta árvore, ou seja, o hook usou o código novo):

| Caso | Comando | Resultado |
|------|---------|-----------|
| A | `app.py`/`clean.py` limpos, staged | exit **0** |
| B | `aws_access_key_id = "AKIA…"` em `leak.py` | exit **1**, relatório `.md` gravado, mensagem nomeia arquivo e linha |
| C | mesmo diff com `GITPR_LINTER_SECURITY=false` | exit **0** |
| D | `password = "…"` com valor real (warning) | exit **0**, e o alerta aparece no relatório |
| E | `id_rsa` (sem extensão) com bloco de chave privada + `.env` | exit **1** — o curinga `["*"]` funciona de fato |
| F | `GITPR_LINTER_SECURITY_DISABLED_RULES=sec-private-key-block` | exit **0** — só aquela regra saiu |
| G | `git commit` com o erro staged, hook instalado | **`🚨 COMMIT BLOCKED!`**, exit 1, `HEAD` inalterado |
| H | `git commit` com o opt-out | commit passa, `HEAD` avança |

### Impact

- **Functionality:** mudança de comportamento **por padrão**. Um commit que
  passava pode passar a ser bloqueado por cinco categorias de padrão
  determinístico. É o ponto central da nota de release, e é o que o ADR-007 §3
  aprovou como opt-out (`GITPR_LINTER_SECURITY`, fail-open: só `false`/`0`/`no`/
  `off`/`n` desliga).
- **Performance:** irrelevante. Sete regex locais, sem rede e sem IA, avaliadas
  sobre as linhas adicionadas do diff — o mesmo laço que já percorria as regras
  do projeto.
- **Compatibility:** o schema de regra não mudou; regras existentes seguem válidas
  e `extensions` sem `"*"` se comporta como antes. Duas consequências a registrar:
  (a) as duas chaves novas passam a ser semeadas no `~/.gitpr/.env` pelo
  `setup_environment()` na próxima execução; (b) `src/branding/badge_data.py`
  lia lista vazia de regras como "linter não configurado", e com o ruleset ligado
  um projeto que nunca rodou `--skill` passa a receber uma medição em vez de
  nenhum badge — o invariante do módulo sobrevive (lista vazia de alertas
  continua significando "verificou e não achou").

### Achados que você precisa decidir

1. **Os documentos do plano vão bloquear o seu commit.** São arquivos não
   rastreados, e `get_git_diff()` usa `git diff HEAD` — então, no instante em que
   você der `git add` neles, o hook os analisa e **três linhas de nível `error`**
   derrubam o commit:

   | Arquivo:linha | Regra | Conteúdo |
   |---|---|---|
   | `docs/plans/20260921_skill_gitpr_secret_scanning_plan.md:115` | `sec-aws-access-key` | um `printf` que escreve `aws_access_key_id = "AKIA…"` no `app.py` |
   | `docs/plans/20260921_skill_gitpr_secret_scanning_plan_new.md:16` | `sec-aws-access-key` | o item 4, que cita a chave de exemplo da AWS por extenso entre aspas |
   | `docs/plans/20260921_skill_gitpr_secret_scanning_spec.md:26` | `sec-private-key-block` | o cabeçalho `-----BEGIN … PRIVATE KEY-----` no meio da prosa |

   Há ainda dois avisos (não bloqueiam): `_plan_new.md:125` e
   `spec.md:27`, ambos uma URL de banco de dados com usuário e senha. É a mesma armadilha que o plano
   previu para as fixtures de teste, aplicada aos próprios documentos. Não toquei
   neles: são o registro da sessão de grill e o desenho aprovado. As saídas são
   encurtar os literais para a forma ilustrativa (`AKIA…`, `-----BEGIN … PRIVATE
   KEY-----`), que é o que passei a usar na documentação que escrevi, ou commitar
   esse lote com `--no-verify`. Diga qual e eu faço.
2. **Três das cinco variantes de idioma dos docs ficaram velhas.** O plano
   aprovado cobria `.md` + `.pt_br.md`; existem também `.pt_pt.md`, `.es_es.md` e
   `.fr_fr.md` de cada um dos dois documentos, que seguem descrevendo o linter sem
   `level` e sem o ruleset. O `get_doc_url()` só serve EN e pt_br, que é o que
   sustenta o recorte — mas a lacuna é real.
3. **Um aviso do próprio linter deste repositório no meu comentário.** A regra
   `check-ia-indice` (`^\s*#\s*\d+\.`) acusa `src/config.py:617`,
   `# 3. Security ruleset (embedded; opt-out via config)`. Mantive de propósito:
   o arquivo já numera `# 1.` e `# 2.` nas linhas 574 e 599, e a regra só dispara
   na minha por ser a única linha nova. Trocar por um comentário sem número
   silenciaria o aviso quebrando o paralelismo do bloco. Se preferir o aviso zero,
   é uma linha.
4. **As duas chaves já estão no seu `~/.gitpr/.env`**, com os valores default
   (`'true'` e `''`). Elas foram semeadas pelas execuções de verificação do CLI
   que fiz durante o trabalho — é exatamente o comportamento documentado na linha
   8 do plano e não altera nada (o valor semeado é igual ao default), mas foi
   escrito na sua máquina real e por isso está aqui em vez de ficar implícito.
5. **A suíte não exercita o default de produção.** Com o pin em `false`, o
   caminho "ligado por ambiente" só é coberto pelos testes explícitos do módulo
   novo e pelo E2E. É o mesmo recorte que o `GITPR_LANG=en_us` já impõe.
6. **`__version__` continua `1.2.0`.** A seção do CHANGELOG antecipa `1.3.0`; o
   bump é seu, no corte da release.
7. **O `docs/linter-regras-customizadas.pt_br.md` tem escapes literais** (`\#`,
   `\-`, `\[`) dentro dos blocos YAML, defeito pré-existente do arquivo (o mesmo
   provavelmente nas outras variantes). Não mexi, mas a linha `level` que inseri
   ficou sem comentário à direita justamente para não decidir entre imitar o
   escape e destoar dele.

### Next steps

- Decidir o item 1 (os literais nos documentos do plano) antes de commitar.
- Separar os commits por tarefa, conforme a tabela de atribuição acima.
- Bump de `__version__` para `1.3.0` no corte da release; revalidar o portão de
  atualização obrigatória, que depende de `__version__`.
- Traduzir as três variantes de doc restantes, se quiser paridade de idiomas.
