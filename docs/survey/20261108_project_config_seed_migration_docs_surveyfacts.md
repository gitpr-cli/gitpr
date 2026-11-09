# Survey Facts — Documentação da Mudança de Fluxo: Seed de `.gitpr/conf/gitpr.config.yml`

## 1. Contexto da Tarefa
O GitPR passou a gerar automaticamente o arquivo versionável de configuração de projeto (`.gitpr/conf/gitpr.config.yml`) na primeira execução de qualquer comando dentro de um repositório Git (`src/main.py` linhas 1411–1430). 
Embora a funcionalidade desse arquivo esteja descrita nas documentações de configuração e publicação de PR, não existia uma **nota de migração / mudança de fluxo** que alertasse especificamente sobre:
- Ambientes de **CI/CD** que executam verificações de árvore de trabalho limpa (`git status --porcelain` ou `git diff --exit-code`), os quais podem quebrar se o GitPR gerar esse arquivo inesperadamente.
- Arquiteturas **monorepo**, onde o arquivo é criado e ancorado na raiz do repositório Git (`git rev-parse --show-toplevel`), exigindo alinhamento de versionamento pela equipe ou opt-out.
- A variável de ambiente **`GITPR_SKIP_PROJECT_CONFIG_SEED`**, que desativa completamente essa geração automática em runtime.

## 2. Levantamento de Fatos Técnicos no Código
1. **Ponto de ativação (`src/main.py`)**:
   - A chamada `project_seed = ensure_project_config()` é disparada na inicialização do CLI antes dos subcomandos ou flags legadas.
   - Condições de bypass atuais:
     - `help_flag` ativo (`-h` / `--help`).
     - Subcomando com ajuda solicitada (`_subcommand_help_in_argv()`).
     - Presença da variável `GITPR_SKIP_PROJECT_CONFIG_SEED` no ambiente (qualquer valor verdadeiro/não-nulo avaliado pelo `os.getenv`).
2. **Implementação de Seeding (`src/project_config.py` e `src/core.py`)**:
   - O arquivo criado é `.gitpr/conf/gitpr.config.yml`.
   - Conteúdo padrão: chave `pull_request.base_branch` apontando para `PR_DEFAULT_BASE` (se configurado) ou `main` como fallback.
   - Resolução de caminho: `project_config_path()` usa `git rev-parse --show-toplevel` para fixar o arquivo na raiz do repositório.
   - Se o `.gitignore` ignorar o arquivo, o GitPR emite um aviso (`⚠️ {path} is ignored by .gitignore and will not be versioned`).
   - Se o arquivo já existir, **nunca é sobrescrito** (`SeedResult(created=False)`).
3. **Lacuna na Documentação**:
   - `docs/pull-request-publication.md` (§9.1) menciona que o arquivo nasce na primeira chamada, mas não menciona `GITPR_SKIP_PROJECT_CONFIG_SEED`, impactos em CI ou monorepos, nem lista a variável na Seção 14 (Environment Variables).
   - `docs/config-tui.md` (§1.8) explica o painel Project, mas não aborda a variável de desativação ou implicações em pipelines automatizados.
   - `GEMINI.md` não continha menção a `GITPR_SKIP_PROJECT_CONFIG_SEED`.
   - `CONTEXT.md` define `Project configuration file`, mas não formalizava o termo `Project configuration seed`.

## 3. Decisões Acordadas na Rodada de Grill
- **Q1 (Local da Documentação):** Opção A — Atualizar as documentações centrais existentes (`docs/pull-request-publication.md` com subseção dedicada de migração/CI/monorepos e `docs/config-tui.md`).
- **Q2 (Cenários Práticos de CI e Monorepos):** Opção A — Detalhar:
  1. Quebra de clean tree check em CI (`git status --porcelain`, `git diff --exit-code`) por geração em runtime de arquivos não commitados.
  2. Uso de `GITPR_SKIP_PROJECT_CONFIG_SEED=true` em steps de CI.
  3. Comportamento em monorepos (ancoragem na raiz git, versionamento em equipe vs opt-out).
- **Q3 (Tabelas de Variáveis de Ambiente):** Opção A — Incluir `GITPR_SKIP_PROJECT_CONFIG_SEED` formalmente nas tabelas de `docs/pull-request-publication.md` (§14), `docs/config-tui.md` e `GEMINI.md`.
- **Q4 (Modelo de Domínio - `CONTEXT.md`):** Opção A — Formalizar `Project configuration seed` e `Project configuration seed opt-out` no glossário.
