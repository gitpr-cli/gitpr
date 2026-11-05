# Survey Facts — Seed de .gitpr/conf/ Local e Templates de Configuração

**Data:** 2026-11-05  
**Branch:** `develop_natan`  
**Task:** `seed_local_conf`  
**Origem:** Item herdado de `docs/reports/relatorio_estado_v0.0.22.md:898` (*"Seed de `.gitpr/conf/` local: o seed do smart-excludes e do linter continua pendente como subcomando próprio ou etapa do wizard — o `gitpr.config.yml` agora cobre só a base do PR"*).

---

## 1. Contexto e Estado Atual

1. **Repositório e Arquivos Locais (.gitpr/conf/ e .gitpr/skill/):**
   - `.gitpr/conf/gitpr.config.yml`: arquivo versionado contendo a branch base do PR (`ensure_project_config()` em `src/project_config.py`).
   - `.gitpr/conf/gitpr.smart-excludes.json`: arquivo versionado contendo exclusões de pathspec do git diff locais do projeto. A função `_seed_local_smart_excludes()` já existia em `src/core.py`, mas funcionava apenas de forma silenciosa e best-effort dentro de `_load_smart_excludes()`, sem exposição explícita de status ou chamada garantida no setup.
   - `.gitpr/skill/.gitpr.linter.yml`: arquivo de regras regex do linter local, atualmente baixado via `generate_skill_template()` (`gitpr --skill`).
   - `.gitpr/conf/github.yml`: arquivo unversionado de estado da última issue criada (`src/issue_engine.py`).

2. **Wizard Interativo (`gitpr --install`):**
   - Atualmente executa em 4 passos:
     1. Skill Templates (`generate_skill_template()`)
     2. Git Hooks (`install_git_hooks()`)
     3. MCP Configuration (`_run_install("auto")`)
     4. API Key Configuration
   - Semeia silenciosamente `gitpr.config.yml` antes do passo 1, mas não oferece feedback estruturado nem semeia `gitpr.smart-excludes.json`.
   - Não expõe opção para configuração de linters externos (`run_linter_setup_wizard()`).

3. **Flag `--skill` (`gitpr -s`):**
   - Baixa os templates para `.gitpr/skill/`, mas não acionava `_seed_local_smart_excludes()`, violando a diretriz histórica de `GEMINI.md:613`.

---

## 2. Decisões do Grill (Rodadas 1 a 3)

| Decisão | Tópico | Opção Escolhida | Justificativa |
|---|---|---|---|
| **D1 (Q1)** | Superfície de entrada | **Integração Tripla** (Wizard, `--skill` e comando/flag direto) | Cobre os três modos de uso do desenvolvedor (guiado, download de templates e atalho rápido). |
| **D2 (Q2)** | Localização e escopo dos arquivos | **`.gitpr/conf/` + `.gitpr/skill/` preservados** | `.gitpr/conf/` para configurações de projeto (`gitpr.config.yml`, `gitpr.smart-excludes.json`) e `.gitpr/skill/` para templates de prompts e `.gitpr.linter.yml`. |
| **D3 (Q3)** | Política de sobrescrita | **Idempotente estrito** | Nunca sobrescreve arquivos locais existentes por padrão; relata se foram criados ou mantidos. Suporta `--force` explícito. |
| **D4 (Q4)** | Sintaxe do comando direto | **Subcomando `gitpr seed` + flag `--seed`** | Máxima ergonomia e alinhamento com a arquitetura híbrida de subcomandos Click e flags do GitPR. |
| **D5 (Q5)** | Organização no Wizard | **5 passos dedicados** | Passo 1 exclusivo para *Project Local Configuration* (`.gitpr/conf/`), seguido de *Skill Templates*, *Git Hooks*, *MCP* e *API Key*. |
| **D6 (Q6)** | Linters externos no Wizard | **Pergunta opt-in (`default=False`)** | Permite ao usuário acionar `run_linter_setup_wizard()` se desejar bridge para ESLint/PHPCS/Stylelint, sem poluir o fluxo padrão. |
| **D7 (Q7)** | Escopo de arquivos de `gitpr seed` | **Configurações locais de projeto** | Semeia `gitpr.config.yml`, `gitpr.smart-excludes.json` e `.gitpr.linter.yml`. Flag `--all` baixa também os templates de IA. |
| **D8 (Q8)** | Telemetria | **Registrar no Ledger** | `command="seed"`, `provider="local"`, status `success`/`error`. |

---

## 3. Fatos Técnicos Levantados no Código

1. **`src/project_config.py`**:
   - Possui `ensure_project_config(path, start_dir, default_branch) -> SeedResult(created, path, ignored, error)`.
   - Já possui infraestrutura limpa de retorno de status.

2. **`src/core.py`**:
   - `_seed_local_smart_excludes(project_root)`: pode ser refatorada para retornar um resultado estruturado (`created: bool, path: Path, already_exists: bool, error: str`).
   - `download_skill_file(local_name, remote_name)`: baixa templates individuais sob demanda.
   - `generate_skill_template()`: itera pelos templates; deve chamar a semeadura de `.gitpr/conf/`.
   - `run_install_wizard()`: orquestra os passos de instalação interativa.

3. **`src/linter_wizard.py`**:
   - `run_linter_setup_wizard()`: interativo, pode ser chamado opcionalmente pelo `run_install_wizard()`.

4. **`src/main.py`**:
   - Ponto de despacho Click: adicionar subcomando `seed` e flag `--seed` / `-sd`.
   - Telemetria via `log_command_metric(command="seed", status="success", provider="local")`.
