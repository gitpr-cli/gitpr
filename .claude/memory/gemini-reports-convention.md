---
name: gemini-reports-convention
description: GEMINI.md exige relatório de conclusão em docs/gemini/reports/ para cada tarefa Gemini
metadata:
  type: project
  source: docs/gemini/reports/develop_natan/2026-08-03_create_gemini_md.md
  date: 2026-08-03
  branch: develop_natan
---

O arquivo `GEMINI.md` na raiz do projeto estabelece regras para assistentes de
codificação Gemini, espelhando o papel do `CLAUDE.md` para Claude. Uma regra
mandatória de alta prioridade exige que toda tarefa de desenvolvimento concluída
pelo Gemini gere um relatório em:

```
docs/gemini/reports/{branch}/{date}_{task_name}.md
```

Este padrão é análogo ao diretório `docs/claude-code/reports/` usado pelo Claude
Code, criando dois fluxos paralelos de documentação histórica. Ambos os diretórios
são varridos pelo `/reports-to-memory` para extração de fatos e geração de
memórias atômicas.

O `GEMINI.md` cobre os mesmos módulos e convenções do `CLAUDE.md` (Ollama AI
Provider, MCP Server, Chat TUI interativo, Telemetria/Dashboard, Setup Wizard `--install`,
i18n 5 idiomas) mas é mantido independentemente — alterações em um não atualizam
automaticamente o outro.

**Why:** O projeto usa múltiplos assistentes de IA (Claude e Gemini) e cada um
precisa de seu próprio rulebook. A separação `CLAUDE.md` / `GEMINI.md` evita
conflitos de instruções e permite que cada assistente tenha regras específicas
do seu ecossistema, mantendo a consistência nos relatórios de conclusão.

**How to apply:**
1. `CLAUDE.md` e `GEMINI.md` devem ser mantidos em sincronia quando novos comandos
   ou mudanças de arquitetura são introduzidos
2. Relatórios do Gemini seguem o mesmo padrão de nomenclatura dos relatórios do
   Claude: `{YYYY-MM-DD}_{taskname}.md`
3. Ambos os diretórios de relatórios são fontes de entrada para `/reports-to-memory`
4. Features documentadas em um rulebook devem ser espelhadas no outro
