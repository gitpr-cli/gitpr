# 0019 — Segregação entre o Auto-Seed de Runtime e o Provisionamento Explícito de Configurações de Projeto

- **Status:** Aceito
- **Data:** 2026-11-10
- **Decisores:** Natan Fiuza, Antigravity
- **Contexto:** Definição clara da fronteira de responsabilidades na inicialização de arquivos locais em repositórios (`.gitpr/conf/` e `.gitpr/skill/`), resolvendo a pendência histórica de provisionamento e esclarecendo por que o auto-seed silencioso de primeiro uso cobre exclusivamente o arquivo de base de PR (`gitpr.config.yml`).

## Contexto e Decisão

O GitPR suporta configurações versionadas de projeto que residem na raiz do repositório, garantindo que parâmetros de colaboração acompanhem o código e sejam compartilhados entre os desenvolvedores do time:
1. `.gitpr/conf/gitpr.config.yml`: define a branch base do Pull Request (conforme [ADR-015](file:///docs/plans/ADR-015-project-local-pr-base.md)) e eventuais customizações de SCM forge ([ADR-016](file:///docs/plans/ADR-016-per-provider-scm-settings.md)).
2. `.gitpr/conf/gitpr.smart-excludes.json`: define regras locais de exclusão de pathspecs para o git diff, ignorando arquivos volumosos gerados ou dependências locais antes do envio à IA.
3. `.gitpr/skill/.gitpr.linter.yml`: define regras de linting estático com expressões regulares personalizadas para a equipe.

Anteriormente, havia uma ambiguidade sobre o escopo do "seed" de repositório:
- O callback raiz (`main.py`) chamava `ensure_project_config()`, criando apenas `.gitpr/conf/gitpr.config.yml` na primeira execução de qualquer comando do GitPR dentro de um repositório git.
- O provisionamento de `.gitpr/conf/gitpr.smart-excludes.json` e `.gitpr/skill/.gitpr.linter.yml` permanecia não orquestrado de forma centralizada ou acessível via comando dedicado.

Decidimos adotar a seguinte arquitetura de **Segregação de Responsabilidades**:

### 1. Auto-Seed de Runtime (Restrito e Silencioso)
- Ocorre automaticamente no callback raiz de comandos comuns do GitPR (ex.: `gitpr`, `gitpr -c`, `gitpr -r`, `gitpr -ch`).
- **Escopo restrito:** Cria **apenas** `.gitpr/conf/gitpr.config.yml` caso não exista, preenchendo-o com a PR target base detectada (`PR_DEFAULT_BASE`, `origin/HEAD` ou `main`).
- **Motivação:** Manter o primeiro uso enxuto e não-invasivo. Gerar múltiplos arquivos locais (`smart-excludes`, `linter`, templates) de forma silenciosa polui desnecessariamente o status do Git e a árvore de trabalho (`git status`) de desenvolvedores que apenas executaram um comando de leitura ou inspeção.
- **Opt-out:** Pode ser completamente suprimido em pipelines de CI/CD que exigem working tree estritamente limpo através da variável de ambiente `GITPR_SKIP_PROJECT_CONFIG_SEED=true` (ou `1`).

### 2. Provisionamento Explícito de Projeto (`gitpr seed` e Wizard)
- Ocorre apenas mediante intenção deliberada do desenvolvedor através de:
  - Subcomando dedicado: `gitpr seed` (ou a flag equivalente `gitpr --seed` / `gitpr -sd`).
  - Wizard interativo de configuração: `gitpr --install` (reorganizado em 5 etapas, sendo a Etapa 1 dedicada a configurações locais em `.gitpr/conf/`).
  - Download de templates: `gitpr --skill` (`-s`), que automaticamente assegura a presença do `gitpr.smart-excludes.json`.
- **Escopo completo:** Semeia o trio completo de arquivos de projeto:
  - `.gitpr/conf/gitpr.config.yml`
  - `.gitpr/conf/gitpr.smart-excludes.json`
  - `.gitpr/skill/.gitpr.linter.yml`
  - Com a flag `--all` / `-a`, inclui também todos os templates de regras e prompts de IA em `.gitpr/skill/`.
- **Idempotência estrita:** Arquivos já existentes no repositório nunca são sobrescritos, preservando as customizações do time. A sobrescrita só ocorre com a passagem explícita da flag `--force` / `-f`.
- **Telemetria:** O comando `seed` é registrado no SQLite ledger sob a categoria `command="seed"`, com provedor `local` e status estruturado.

## Consequências

- **Clareza Arquitetural:** Elimina dúvidas sobre o escopo do seed automático vs. seed explícito.
- **Segurança da Árvore de Trabalho:** Comandos de rotina do GitPR não injetam arquivos secundários de configuração sem consentimento ou intenção manifesta.
- **Onboarding Padronizado:** Novos repositórios e membros de equipe contam com `gitpr seed` ou `gitpr --install` para provisionar o ambiente local em segundos.
- **Terminologia Alinhada:** Atualização no modelo de domínio (`CONTEXT.md`) separando o `Runtime project configuration seed` do `Project configuration seed` explícito.
