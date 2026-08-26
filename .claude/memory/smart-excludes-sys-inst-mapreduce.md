---
name: smart-excludes-sys-inst-mapreduce
description: Lista de docs excluídos pelo Smart Excludes vai no sys_inst, não no corpo do prompt, para sobreviver ao Map-Reduce
metadata:
  type: project
  source: docs/claude-code/reports/develop_natan/2026-08-19_feedback_skill_smart_excludes_issue_blame.md
  date: 2026-08-19
  branch: develop_natan
---

Quando o Smart Excludes remove documentação do diff, a IA ainda precisa saber que aqueles
arquivos mudaram. A lista ("Changed documentation (content excluded from diff): ...") é
injetada nas **instruções de sistema** (`sys_inst`), nunca no corpo do prompt.

**Why:** O corpo do prompt é fatiado pelo Map-Reduce em diffs gigantes — cada chunk veria
só um pedaço, ou nenhum. O `sys_inst` acompanha **todas** as chamadas, inclusive cada
chunk do Map-Reduce. A paridade com `generate_pr_content()` foi mantida de propósito para
que os fluxos não divirjam.

Aplicado em `src/issue_engine.py` (fluxo `gitpr -is` com contexto diff) em 2026-08-19,
alinhando-o ao fluxo de PR que já fazia isso.

**How to apply:**
- Qualquer metadado que a IA precise ver por inteiro (lista de arquivos, política, persona)
  vai no `sys_inst`; só o conteúdo fatiável vai no corpo.
- Ao adicionar um fluxo novo que consome diff, copie o par: seção no `sys_inst` +
  mensagens "📄 N documentation file(s) excluded from diff (Smart Excludes)." e link
  "Learn more".
- Carregamento de skill segue a mesma lógica de escopo: no blame a skill é lida **uma vez**
  em `run_blame_analysis()` e passada por parâmetro a `analyze_commit_with_ai()`, em vez de
  uma leitura (e uma mensagem) por commit. Modos `return_data=True` (usados por `-is -b` e
  pelo MCP) carregam em silêncio.
- Ver [[smart-excludes-remote-control]], [[smart-excludes-local-projeto]] e [[skill-folder-auto-migration]].
