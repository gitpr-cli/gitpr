# Plan Facts — Segregação entre Auto-Seed de Runtime e Provisionamento Explícito de Configuração

**Data:** 2026-11-10  
**Branch:** `develop_natan`  
**Task:** `seed_conf_segregation`  

---

## 1. Escopo e Objetivos

Formalizar e consolidar a fronteira arquitetural entre o **Auto-Seed de Runtime** e o **Provisionamento Explícito de Projeto**, eliminando ambiguidades herdadas de relatórios anteriores (`relatorio_estado_v0.0.22.md:898`):
1. Documentar no [ADR-0019](file:///docs/adr/0019-project-configuration-seed-segregation.md) a decisão de manter o auto-seed silencioso restrito exclusivamente a `.gitpr/conf/gitpr.config.yml`.
2. Reforçar o papel de `gitpr seed`, `gitpr --seed` e do wizard de 5 etapas (`gitpr --install`) como os mecanismos canônicos para provisionamento do conjunto completo de configurações locais (`gitpr.config.yml`, `gitpr.smart-excludes.json` e `.gitpr.linter.yml`).
3. Refinar o glossário de termos ubíquos em `CONTEXT.md` para distinguir `Runtime project configuration seed` de `Project configuration seed`.
4. Garantir a conformidade dos testes automatizados e regras de governança.

---

## 2. Componentes e Entregas

### 2.1 Decisão Arquitetural (ADR)
- Criação de `docs/adr/0019-project-configuration-seed-segregation.md` definindo:
  - Runtime Auto-Seed: escopo cirúrgico e silencioso, motivado pela prevenção de poluição do Git working tree.
  - Provisionamento Explícito: via `gitpr seed` e `gitpr --install`, garantindo idempotência e `--force`.
  - Mecanismos de opt-out para ambientes de CI/CD (`GITPR_SKIP_PROJECT_CONFIG_SEED=true`).

### 2.2 Modelagem de Domínio (`CONTEXT.md`)
- Desambiguação de termos:
  - `Runtime project configuration seed`: criação automática em tempo de execução de `gitpr.config.yml`.
  - `Project configuration seed`: provisionamento deliberado e explícito do trio de configuração local.

### 2.3 Verificação e Testes
- Suíte `tests/test_seed_command.py` validando os fluxos do subcomando `gitpr seed`, flag `--seed`, `--force`, `--all` e métricas do ledger.
- Suíte `tests/test_project_config.py` validando o comportamento isolado de `ensure_project_config()`.
