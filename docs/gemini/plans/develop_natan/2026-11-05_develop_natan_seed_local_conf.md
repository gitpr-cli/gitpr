# Plano de Implementação — Seed de .gitpr/conf/ Local e Templates de Configuração

**Data:** 2026-11-05  
**Branch:** `develop_natan`  
**Task:** `seed_local_conf`  
**Autor:** Natan Fiuza (Pair Programming com Antigravity / Gemini)

---

## 1. Visão Geral e Objetivos

Resolver a pendência registrada em `docs/reports/relatorio_estado_v0.0.22.md` referente ao seed de templates de configuração local do projeto.
Atualmente, `.gitpr/conf/gitpr.config.yml` já possui um semeador dedicado (`ensure_project_config()`), mas `.gitpr/conf/gitpr.smart-excludes.json` e `.gitpr/skill/.gitpr.linter.yml` careciam de um comando direto e de uma etapa explícita no wizard de instalação (`gitpr --install`), além de não serem semeados conjuntamente pelo comando `--skill`.

---

## 2. Decisões Consolidadas

1. **Entrada e Interface:**
   - Criação do subcomando `gitpr seed` e da flag top-level `--seed` / `-sd`.
   - Adição da etapa explícita *"Step 1 of 5: Project Local Configuration"* no wizard `gitpr --install`.
   - Inclusão do seed de `.gitpr/conf/` na execução do `gitpr -s` / `--skill`.
2. **Escopo dos Arquivos:**
   - `.gitpr/conf/gitpr.config.yml`: PR target base branch.
   - `.gitpr/conf/gitpr.smart-excludes.json`: Exclusões locais de diff.
   - `.gitpr/skill/.gitpr.linter.yml`: Regras do linter estático.
   - Suporte a `--all` para incluir os 12 templates markdown de IA.
3. **Idempotência:**
   - NUNCA sobrescreve arquivos existentes por padrão; relata se foram criados ou preservados.
   - Suporte a `--force` para recriar arquivos com o template inicial padrão.
4. **Linters Externos:**
   - Pergunta opt-in no wizard `gitpr --install` para acionar `run_linter_setup_wizard()` (ESLint, PHPCS, Stylelint).
5. **Telemetria:**
   - Registro de `command="seed"`, `provider="local"` no SQLite ledger.

---

## 3. Arquitetura de Mudanças

```
src/
├── core.py             # Refatoração de _seed_local_smart_excludes() + nova seed_project_configuration()
│                       # Integração do seed em generate_skill_template() e expansão do run_install_wizard()
├── main.py             # Subcomando `seed`, flag `--seed`, help e telemetria
langs/                  # Dicionários de internacionalização atualizados (chaves em en_us, pt_br, pt_pt, es_es, fr_fr)
tests/
└── test_seed_command.py # Suíte de testes unitários dedicada para o comando seed e seus fluxos
```

---

## 4. Plano de Verificação

- **Testes Unitários:** Execução via `pytest tests/test_seed_command.py tests/test_install_wizard.py tests/test_skill_command.py -v`.
- **Suíte Completa:** Execução de `pytest` geral para garantir regressão zero.
- **Verificação Manual:**
  - Rodar `gitpr seed` em repositório temporário e validar criação dos arquivos e idempotência.
  - Testar `gitpr seed --force`.
  - Testar `gitpr --install` observando a transição de 5 etapas.
