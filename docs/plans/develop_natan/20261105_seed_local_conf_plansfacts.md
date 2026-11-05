# Plan Facts — Seed de .gitpr/conf/ Local e Templates de Configuração

**Data:** 2026-11-05  
**Branch:** `develop_natan`  
**Task:** `seed_local_conf`  

---

## 1. Escopo da Implementação

Implementar o mecanismo oficial de inicialização e semeadura de configurações locais do projeto no GitPR:
1. Refatorar e enriquecer a semeadura de arquivos locais (`_seed_local_smart_excludes` e `seed_project_configuration`).
2. Criar o subcomando `gitpr seed` e a flag top-level `--seed` / `-sd` (com flags `--force` e `--all`).
3. Integrar o seed de `.gitpr/conf/` na execução do `gitpr -s` / `--skill`.
4. Reestruturar o wizard `gitpr --install` para 5 passos, introduzindo o passo de configuração local do projeto e a opção de configurar linters externos.
5. Adicionar telemetria no SQLite ledger para o comando `seed`.
6. Criar suíte completa de testes unitários para o seed.

---

## 2. Componentes e Alterações

### 2.1 Orquestração do Seed (`src/core.py`)
- Refatorar `_seed_local_smart_excludes()` para aceitar `force=False` e retornar um dataclass/dict com status estruturado (`created: bool, path: Path, already_existed: bool, error: str`).
- Criar a função pública `seed_project_configuration(force=False, include_all_skills=False, quiet=False) -> dict`:
  - Garante `.gitpr/conf/gitpr.config.yml` via `ensure_project_config()`.
  - Garante `.gitpr/conf/gitpr.smart-excludes.json` via `_seed_local_smart_excludes()`.
  - Garante `.gitpr/skill/.gitpr.linter.yml` via `download_skill_file()`.
  - Se `include_all_skills=True`, executa o download de todos os templates de IA.
  - Imprime sumário formatado no console com ícones e status claros.
- Em `generate_skill_template()`, invocar `_seed_local_smart_excludes()`.
- Em `run_install_wizard()`, reorganizar para 5 etapas:
  - **Step 1 of 5: Project Local Configuration** (`.gitpr/conf/`)
  - **Step 2 of 5: Skill Templates & Linter** (`.gitpr/skill/`) com pergunta opt-in para linters externos
  - **Step 3 of 5: Git Hooks**
  - **Step 4 of 5: MCP Configuration**
  - **Step 5 of 5: API Key Configuration**

### 2.2 CLI & Despacho (`src/main.py`)
- Adicionar subcomando `@cli.command("seed")`:
  - Flags: `--force` / `-f` e `--all` / `-a`.
  - Dispara `seed_project_configuration(...)`.
  - Registra métrica `log_command_metric(command="seed", status="success", provider="local")`.
- Adicionar flag `--seed` / `-sd` no comando raiz (`@click.option("--seed", "-sd", is_flag=True, ...)`).
- Atualizar banner e mensagens de ajuda contextual.

### 2.3 Internacionalização (`langs/*.json`)
- Adicionar strings localizadas em inglês (fallback) e nos arquivos de tradução (`pt_br.json`, `pt_pt.json`, `es_es.json`, `fr_fr.json`).

### 2.4 Testes (`tests/test_seed_command.py`)
- Teste de idempotência (primeira execução cria, segunda execução relata existência).
- Teste de `--force` sobrescrevendo conteúdo padrão.
- Teste de chamada via subcomando `gitpr seed` e via flag `--seed`.
- Teste de integração do seed no `gitpr -s` (`generate_skill_template`).
- Teste do wizard `run_install_wizard` refletindo os 5 passos.
- Teste de métricas registradas no ledger SQLite.
