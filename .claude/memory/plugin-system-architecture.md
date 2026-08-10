---
name: plugin-system-architecture
description: Arquitetura do sistema de plugins globais — linter aditivo + prompts MCP dinâmicos com factory closures
metadata:
  type: project
  source: docs/claude-code/reports/develop_natan/2026-08-09_plugin_system.md
  date: 2026-08-09
  branch: develop_natan
---

O sistema de plugins do GitPR permite estender linter e prompts MCP globalmente (todos os projetos)
sem duplicar configuração. Dois diretórios em `~/.gitpr/plugins/`:

- **`linter/`**: Arquivos `.yml`/`.yaml` com regras no mesmo formato do `.gitpr.linter.yml` local.
  Carregados aditivamente por `load_linter_rules()` — regras globais são concatenadas às locais,
  nunca substituem. YAML mal formatado mostra warning amarelo e é pulado sem quebrar o fluxo.

- **`prompts/`**: Arquivos `.md` registrados dinamicamente como recursos MCP (`prompt://plugin/<nome>`)
  e prompts MCP (`Plugin: <nome>`) na inicialização do servidor. Usa factory functions
  (`make_resource_handler`, `make_prompt_handler`) dentro de `_register_plugin_prompts()` para
  evitar late-binding — sem a factory, todas as closures apontariam para o último arquivo do loop.

**Why:** Antes, regras de linter e prompts de IA só podiam ser definidos por projeto (`.gitpr/skill/`),
exigindo duplicação para padrões pessoais como "nunca commitar console.log" ou "sempre auditar
segurança". O sistema de plugins resolve isso com uma camada global aditiva que não interfere
nos padrões do time (local). A factory pattern foi essencial para o registro MCP dinâmico porque
Python amarra closures de loop ao escopo externo (late-binding).

**How to apply:** Para adicionar um novo tipo de plugin, seguir o padrão:
1. Criar subpasta em `~/.gitpr/plugins/<tipo>/` via `setup_environment()`.
2. Adicionar função de discovery `get_<tipo>_plugins()` em `config.py`.
3. No ponto de consumo, iterar sobre os plugins e fazer merge aditivo (nunca substitutivo).
4. Tratar erros silenciosamente — plugin malformado nunca deve quebrar o fluxo principal.

Ver também: [[mcp-server-isolation]], [[skill-folder-auto-migration]]
