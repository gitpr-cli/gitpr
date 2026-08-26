# Feedback visual de Skill e Smart Excludes nos fluxos Issue e Blame do GitPR CLI

## Contexto

Ao executar `gitpr -is` (flag `--issue`), o usuário não vê feedback de duas funcionalidades que estão ativas mas silenciosas:

1. **Smart Excludes** — a exclusão de lock files, `*.min.js`, svg e arquivos de documentação é aplicada ao diff via pathspec do Git, mas a mensagem "📄 N documentation file(s) excluded from diff (Smart Excludes)." e a seção "Changed documentation (content excluded from diff):" enviada no prompt da IA existem apenas no fluxo de PR (`generate_pr_content`), nunca no fluxo de issue.
2. **Skill** — o arquivo `.gitpr/skill/.gitpr.issue.md` é carregado como System Instruction no fluxo issue (e `.gitpr.blame.md` no fluxo blame), porém sem nenhuma mensagem de confirmação, ao contrário do fluxo de PR, que imprime "🧠 File ... (Skill) found and loaded!".

## Comportamento Esperado

1. Ao rodar `gitpr -is` com a skill presente em `.gitpr/skill/.gitpr.issue.md`:
   - Exibir "🧠 File .gitpr.issue.md (Skill) found and loaded!".
2. Ao rodar `gitpr -is` com arquivos de documentação alterados no diff:
   - Exibir "📄 N documentation file(s) excluded from diff (Smart Excludes)." + link "Learn more".
   - Incluir a lista "Changed documentation (content excluded from diff):" no prompt enviado à IA (paridade com o fluxo PR).
3. Ao rodar `gitpr -b` (blame):
   - Exibir "🧠 File .gitpr.blame.md (Skill) found and loaded!" **uma única vez**, mesmo analisando múltiplos commits.

## Escopo

Mudanças em `C:\Users\nataniel\projetos\python\gitpr`:

- `src/core.py` — adicionar suporte a `action_type="blame"` em `get_skill_context()`.
- `src/issue_engine.py` — carregar skill via `get_skill_context("issue")` (mensagem + tratamento de erro) mantendo a persona default como fallback; adicionar seção de docs excluídos no prompt quando `context_type == "diff"`.
- `src/blame_engine.py` — carregar a skill de blame uma única vez em `run_blame_analysis()` via `get_skill_context("blame")` e passá-la a `analyze_commit_with_ai` por parâmetro (evita mensagem repetida por commit).
- Testes novos em `tests/test_issue_engine.py` e classe nova em `tests/test_blame_metrics.py`.

Fora de escopo: traduções i18n (chaves existem com fallback inglês), o `sys_inst` do resumo executivo do blame, e mudanças nos fluxos de PR/commit/review (que já exibem as mensagens).
