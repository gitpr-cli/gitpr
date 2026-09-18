# ADR-005 — Review de PR remoto como subcomando `gitpr review-pr`, com `DiffSource` fora do motor

- **Status:** Aceito
- **Data:** 2026-09-17
- **Contexto:** spec [20260917_skill_gitpr_review_pr_spec.md](20260917_skill_gitpr_review_pr_spec.md) §1 e §3, grill rodadas 1–6
- **Glossário:** [glossary-review-pr.md](glossary-review-pr.md)

## Contexto

A spec pede que o GitPR revise um pull request **já aberto na forge**, buscando o
diff pela API, sem exigir checkout da branch. Ela propõe três coisas que o grill
derrubou ou reformulou:

1. **uma flag** (`--review-pr <n>`) na CLI existente;
2. um tipo **`DiffSource` que atravessa o motor de review** — `generate_pr_content`
   passaria a receber a origem junto do diff, e o motor decidiria o que fazer com ela;
3. uma árvore em camadas DDD (`src/application/use_cases/`, `src/domain/review/`).

O [ADR-003](ADR-003-gitpr-release-flat-modules.md) já havia rejeitado camadas DDD,
e o [ADR-004](ADR-004-fix-subcommand-package.md) fixou o critério do subpacote para
features com consumidor externo. O [ADR-002](ADR-002-gitpr-release-subcommand.md)
já havia fixado o subcomando como forma de adicionar capacidade ao lado das flags.

O grill também verificou uma premissa de custo da spec: **o motor de review já é
agnóstico à origem**. `generate_pr_content(action, action_type, diff_text, provider)`
recebe uma string de diff e não pergunta de onde ela veio; `split_diff_into_chunks`
é genérico sobre texto; `parse_diff_and_lint` recebe o mesmo texto. Ou seja: a
feature é **orquestração, normalização e superfície**, não um segundo motor.

## Decisão

1. **Subcomando `gitpr review-pr <n>`**, não flag. A capacidade tem contrato
   próprio — um número obrigatório, publicação opcional, uma recusa que precisa
   de mensagem própria ("não existe" ≠ "fechado") — e flags do grupo raiz não são
   herdadas por subcomandos, o que mantém as opções do PR publisher e do review
   local intocadas. É o mesmo caminho do `release` (ADR-002) e do `fix` (ADR-004).

2. **`DiffSource` é contrato de fronteira, não de motor.** O dataclass carrega
   origem, conteúdo, identificador, número do PR, `RepoRef` e branches; o motor
   continua recebendo **uma string**. `generate_pr_content` ganha apenas dois
   parâmetros opcionais — `cache_scope=""` e `store_diff=False` — com defaults
   que preservam o caminho local byte a byte. A razão é a mesma que fez o motor
   ser reusável: um motor que pergunta a origem começa a ramificar por origem, e
   a paridade entre os dois fluxos (que é o critério de pronto da spec) deixa de
   ser estrutural para virar disciplina.

3. **Pacote `src/review/`**, quatro módulos de responsabilidade única:
   `diff_source.py` (dados puros), `diff_normalizer.py` (normalização,
   validação e smart excludes em Python), `render.py` (o artefato, extraído do
   `main.py` e **compartilhado** com os fluxos locais) e `remote_pr.py` (a
   orquestração). Mesmo critério do ADR-004: subpacote porque há consumidor
   externo — a tool MCP `review_remote_pr` importa o orquestrador sem passar
   pela CLI.

4. **Read-only por padrão.** Sem `--post-comment`, a forge é apenas lida; a tool
   MCP não tem a opção. Publicar num PR alheio é ato deliberado, não efeito
   colateral de rodar uma revisão.

### Alternativas consideradas

| Alternativa | Veredito |
|---|---|
| Flag `--review-pr <n>` no grupo raiz | **Rejeitada.** `--provider` e o número obrigatório colidiriam com o significado que já têm no grupo raiz, e o `cli()` do grupo roda `check_unstaged_files` para ações de IA — que aqui não se aplica (o diff não vem da árvore). O subcomando isola as duas coisas sem condicional nova no caminho legado. |
| `DiffSource` recebido por `generate_pr_content` | **Rejeitada.** Duplicaria no motor um conhecimento que nenhum outro chamador tem, e o caminho local passaria a construir um `DiffSource` só para satisfazer a assinatura. |
| `src/application/use_cases/` + `src/domain/review/` | **Rejeitada** pelo ADR-003 e pelo ADR-004: o projeto não tem camadas DDD, e os dois subpacotes existentes existem por motivo estrutural. |
| Módulos flat na raiz de `src/` (como o `release`) | **Rejeitada** pelo critério do ADR-004: `remote_pr` tem consumidor externo (a tool MCP) e a normalização de diff é um conjunto coeso que não pertence ao `core.py`. |
| Migrar o provider GitLab para o endpoint `/diffs` | **Rejeitada** nesta entrega. Resolveria os cabeçalhos na origem, mas é uma troca de endpoint de um provider em produção, com fixtures novas e risco de regressão em fluxo alheio a esta feature. A síntese de cabeçalhos resolve o defeito com o que a API **já devolve**; a migração fica como possibilidade futura. |
| Comentário inline por linha, ou revisão incremental | **Fora de escopo**, como a spec §1 define. |

### Desvios assumidos em relação à spec

| Ponto da spec | O que foi feito | Por quê |
|---|---|---|
| "`provider` é uma instância de provider de IA" | `ai_provider` é o **nome** (`"gemini"`) | Nenhum objeto de provider existe no código: `ai_providers.call_ai_model` constrói o que precisa a partir do nome e da chave configurada. Aceitar instância seria inventar um tipo para satisfazer uma assinatura. |
| "o resultado carrega `comment_url`" | Não carrega | `ScmProvider.add_comment` devolve `None` por contrato e nenhuma forge relê o comentário criado; o campo só poderia conter um palpite. |
| "criar `ReviewResult` compartilhado com o review local" | `review` é a string que o fluxo local já grava | O review local nunca teve esse tipo — tem um dict com chave `"review"`. Criar o tipo agora seria refatorar o fluxo local dentro de uma entrega que promete não tocá-lo. |
| "atualizar `config.schema.yml`" | Nada a atualizar | O arquivo não existe: a config é dotenv plano + `DEFAULT_CONFIG` + `config_schema.py`. E a feature não introduz chave nova. |
| "reusar `render_review_result`" | Ele foi **extraído** (`src/review/render.py`) e agora é compartilhado | Ele não existia como função: a renderização estava inline no `main.py`. Extrair era pré-requisito da paridade, não reuso. |
| "corrigir o GitLab" (implícito: migrar para `/diffs`) | Cabeçalhos sintéticos + erro em `overflow` | Ver a alternativa rejeitada acima. |

## Consequências

**Positivas:**
- A paridade entre review local e remoto é **estrutural**: mesmas funções de
  prompt, cache, linter e renderização. Um `.txt` remoto e um local do mesmo
  diff só diferem no nome do arquivo.
- Os fluxos locais não mudaram de comportamento: `cache_scope=""` e
  `store_diff=False` mantêm as chaves MD5 existentes, e o `gitpr fix` cai no
  caminho antigo quando o registro não tem diff.
- Dois defeitos latentes foram corrigidos por necessidade da feature: o GitLab
  perdia o nome do arquivo em `get_pull_request_diff` (a IA revisaria hunks
  órfãos) e ignorava `overflow` (publicaria meia revisão sem aviso); e o
  `get_pull_request` passou a existir, tornando "não existe" distinguível de
  "mesclado".

**Negativas / custos:**
- `src/review/` é o quarto subpacote de `src/`; o `pyproject.toml` continua
  dependendo de descoberta automática (`__init__.py` presente).
- O review remoto localiza o cache por **repositório + branch local** (é o que o
  `gitpr fix` resolve), então revisar o PR #123 estando em `develop` arquiva a
  revisão sob `develop`. As branches do PR ficam registradas dentro da entrada,
  mas não a endereçam.
- O linter externo não roda no fluxo remoto (`skip_external=True`): o bridge
  executa binários contra arquivos em disco, que ali seriam a árvore do usuário
  e não o PR revisado — publicar esses alertas como comentário seria lintar a
  revisão errada.
- `generate_pr_content` ainda injeta metadados locais no prompt (a lista de
  documentação alterada, via `get_changed_docs_list()`), que num review remoto
  descrevem a árvore do usuário e não o PR. É ruído de contexto, não incorreção
  da revisão; corrigir exigiria um caminho de prompt ciente da origem — o que
  esta decisão justamente evita.
