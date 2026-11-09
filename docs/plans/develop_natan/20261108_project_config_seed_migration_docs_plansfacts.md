# Plano de Execução — Documentação da Mudança de Fluxo: Seed de `.gitpr/conf/gitpr.config.yml`

## Objetivo
Documentar a mudança de fluxo arquitetural decorrente do seed automático de `.gitpr/conf/gitpr.config.yml` em tempo de execução, orientando especificamente usuários de CI/CD e monorepos sobre a criação do arquivo e como desativá-lo através de `GITPR_SKIP_PROJECT_CONFIG_SEED`.

## Mudanças Planejadas

### 1. `docs/pull-request-publication.md`
- **Seção 9 (Base Branch Configuration):**
  - Atualizar a subseção **9.1 (The Project File)** com alerta de mudança de fluxo e criação automática.
  - Adicionar nova subseção **9.4 (Migration & Workflow Note: CI/CD, Monorepos and Clean Trees)**:
    - Explicar por que pipelines com `git diff --exit-code` ou `git status --porcelain` podem falhar se o arquivo for criado no step de execução (ex: `gitpr -l` ou `gitpr -r`).
    - Explicar como desativar o seed via `GITPR_SKIP_PROJECT_CONFIG_SEED=true` ou `1`.
    - Explicar o comportamento em monorepos (ancoragem no topo do repositório Git via `git rev-parse --show-toplevel`) e recomendação de versionar na raiz ou configurar no `.gitignore`.
    - Apresentar exemplos de configuração de CI (GitHub Actions e GitLab CI).
- **Seção 14 (Environment Variables):**
  - Adicionar `GITPR_SKIP_PROJECT_CONFIG_SEED` na tabela com valor padrão (`false`/não definido) e descrição de uso.

### 2. `docs/config-tui.md`
- **Seção 1.8 (The Project Section):**
  - Incluir nota de atenção sobre o seed automático e a variável `GITPR_SKIP_PROJECT_CONFIG_SEED` para ambientes automatizados e monorepos.
- **Seção 4 (Environment Variables / Advanced):**
  - Documentar `GITPR_SKIP_PROJECT_CONFIG_SEED`.

### 3. `CONTEXT.md`
- Adicionar os termos canônicos no glossário de domínio:
  - **Project configuration seed**: A criação automática do arquivo de configuração do projeto (`.gitpr/conf/gitpr.config.yml`) na primeira execução dentro de um repositório git.
  - **Project configuration seed opt-out**: A desativação explícita do seed via variável de ambiente `GITPR_SKIP_PROJECT_CONFIG_SEED=true`, essencial para ambientes de CI que exigem working tree limpo.

### 4. `GEMINI.md`
- Atualizar a listagem de variáveis de ambiente sob "User configuration" para incluir `GITPR_SKIP_PROJECT_CONFIG_SEED`.

## Critérios de Aceitação e Verificação
- Documentação técnica detalhada e precisa em relação ao código-fonte (`src/main.py` e `src/project_config.py`).
- Links internos e markdown formatados no padrão GitHub.
- Nenhuma quebra de testes automatizados (`pytest tests/`).
