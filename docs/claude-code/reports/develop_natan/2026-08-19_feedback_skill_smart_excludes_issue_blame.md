## Completion Report — Feedback de Skill e Smart Excludes nos fluxos Issue e Blame

### What was done
- `get_skill_context()` agora suporta `action_type="blame"` (`.gitpr.blame.md`), mantendo o fallback legacy `.gitpr.md` e o tratamento de erro com mensagem.
- Fluxo issue (`gitpr -is`): a skill `.gitpr/skill/.gitpr.issue.md` é carregada via `get_skill_context("issue")`, exibindo "🧠 File ... (Skill) found and loaded!" com a persona Software Architect como fallback (substitui a leitura manual silenciosa com `resolve_skill_path`).
- Fluxo issue (`gitpr -is`, contexto diff): lista de documentação alterada (Smart Excludes) é injetada nas instruções de sistema enviadas à IA ("Changed documentation (content excluded from diff): ..."), com as mensagens "📄 N documentation file(s) excluded from diff (Smart Excludes)." e link "Learn more" — paridade exata com o fluxo de PR (`generate_pr_content`).
- Fluxo blame (`gitpr -b`): a skill `.gitpr/skill/.gitpr.blame.md` é carregada uma única vez em `run_blame_analysis()` via `get_skill_context("blame")` e passada por parâmetro a `analyze_commit_with_ai(commit_hash, file_path, sys_inst)`, evitando a mensagem repetida por commit. Modos silenciosos (`return_data=True`, usados por `-is -b` e MCP) continuam sem imprimir e preservam a carga silenciosa interna.
- Correção de bug latente em `get_skill_context()`: `nome_arquivo` era referenciado no `except` sem estar definido quando o próprio `open()` falhava (`UnboundLocalError`) — exposto pelo novo caminho blame que passa por esse handler.
- Testes novos: `tests/test_issue_engine.py` (4 testes: skill carregada e usada como sys_inst, fallback de persona, seção de docs excluídos + mensagem, contextos não-diff ignoram docs) e classe `TestBlameSkillLoading` em `tests/test_blame_metrics.py` (3 testes: skill carregada 1x e repassada à IA, modo return_data silencioso, fallback silencioso sem skill).

### Changed files
| File | Change type | Description |
|------|-------------|-------------|
| src/core.py | feat/fix | Suporte a `action_type="blame"` em `get_skill_context()`; fix do `UnboundLocalError` no handler de erro |
| src/issue_engine.py | feat/refactor | Skill issue via `get_skill_context("issue")` com feedback visual; seção de docs excluídos (Smart Excludes) no contexto diff |
| src/blame_engine.py | feat | Skill blame carregada 1x em `run_blame_analysis()` e passada por parâmetro a `analyze_commit_with_ai` |
| tests/test_issue_engine.py | test | Novo arquivo com 4 testes do fluxo issue |
| tests/test_blame_metrics.py | test | Nova classe `TestBlameSkillLoading` com 3 testes |

### Impact
- **Functionality:** `gitpr -is` passa a exibir feedback visual de skill e Smart Excludes (antes silenciosos); a IA recebe a lista de docs excluídos do diff (paridade com PR). `gitpr -b` exibe a mensagem de skill uma única vez por execução. O resumo executivo do blame permanece inalterado (fora de escopo).
- **Performance:** Nenhum impacto relevante — apenas uma chamada a mais de `get_changed_docs_list()` (subprocess `git diff --name-only`) no fluxo issue com contexto diff; a carga de arquivo da skill no blame passou de N leituras por commit para 1 por execução.
- **Compatibility:** Nenhuma quebra de API pública. `analyze_commit_with_ai` ganhou parâmetro opcional `sys_inst=None` (retrocompatível). Modos `return_data` (issue blame e MCP) mantêm o comportamento silencioso anterior. A decisão de injetar a seção de docs no `sys_inst` (e não no corpo do prompt) segue a paridade exata com o fluxo PR e garante cobertura também no Map-Reduce.

### Next steps (if applicable)
- Traduzir em `langs/pt_br.json` as chaves "Changed documentation (content excluded from diff):" e "📄 {count} documentation file(s) excluded from diff (Smart Excludes)." (hoje caem no fallback inglês) — seguindo a memória de bump de `__lang_version__` pós-merge.
- Teste `test_pr_publish_linter_modal.py::test_no_verify_flow_skips_linter_and_commits` apresentou falha intermitente na suíte completa (passa isolado) — timing de `pilot.pause(0.6)` do Textual sob carga; não relacionado a esta tarefa, mas candidato a investigação de flakiness.

### Validation
- `python -m pytest tests/test_issue_engine.py tests/test_blame_metrics.py -v` → 11 passed.
- `python -m pytest tests/` → 270 passed, 1 failed (flaky de timing, passa isolado — ver acima).
- Smoke test real: `get_skill_context('blame')` imprime "🧠 Arquivo .gitpr.blame.md (Skill) encontrado e carregado!" e retorna o conteúdo (646 chars).
- `python run.py -h` exibe o help normalmente.
