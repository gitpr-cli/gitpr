# Completion Report — Limpeza: `PR_AUTO_PUBLISH` morta + §5 da doc da TUI

## What was done

- Investigada a variável `PR_AUTO_PUBLISH`, que aparecia na categoria **Desconhecidas** da tela `gitpr config` e levantou a dúvida legítima *"ela publica PR automaticamente, não deveria estar em Pull Request?"*. **Provada morta:** `grep -rni 'auto_publish' src/` → **zero ocorrências**, e ela também não está no `DEFAULT_CONFIG` — o GitPR atual não a semeia mais.
- Recuperada a origem da morte: a remoção foi **deliberada e planejada**. [docs/plans/20260807_altera_interface_pullrequest_auto_claudecode.md:226](docs/plans/20260807_altera_interface_pullrequest_auto_claudecode.md#L226) §3g manda removê-la — *"já que publicação agora é padrão"*. O código foi removido; sobraram **duas mentiras de documentação** e a linha órfã no `.env` do usuário.
- Identificado o **substituto real**: a flag `--no-edit` ([src/main.py:1487](src/main.py#L1487) → `_auto_commit_and_publish`, [src/main.py:2219](src/main.py#L2219)). Publicar virou o fluxo padrão; hoje se escolhe *como* — TUI (padrão), `--no-publish` (só o `.md` local) ou `--no-edit` (auto-commit + POST direto). **Nenhuma env var controla isso.**
- **Não** foi adicionada à seção Pull Request: um switch que grava no arquivo e não muda nada é o modo de falha que a própria tela existe para impedir.
- Removido o token `` `PR_AUTO_PUBLISH`, `` da lista de env vars do `CLAUDE.md` — era essa linha que fazia a chave parecer viva e sustentava a premissa de que ela publica PRs.
- Corrigida a **§5 da doc da TUI nas 5 versões**: o título prometia "fora da tela" para chaves que na verdade aparecem, read-only, em Desconhecidas.
- Removida a linha órfã do `~/.gitpr/.env` usando `remove_config_value()` — a função do próprio projeto, não um `sed`.

## Changed files

| File | Change type | Description |
|------|-------------|-------------|
| CLAUDE.md | fix | Removido `PR_AUTO_PUBLISH` da lista de env vars (linha 294). Ela não existe em nenhum arquivo do `src/` — a doc anunciava uma chave inexistente desde agosto/2026 |
| docs/config-tui.md | docs | §5 retitulada "Deliberately Not Editable"; frase de abertura ligando à §4; linha nova para `PR_AUTO_PUBLISH`; linha de `CI`/`GITHUB_ACTIONS` precisada |
| docs/config-tui.pt_br.md | docs | Mesma correção — "Deliberadamente Não Editável" |
| docs/config-tui.pt_pt.md | docs | Mesma correção — "Deliberadamente Não Editável" |
| docs/config-tui.es_es.md | docs | Mesma correção — "Deliberadamente No Editables" |
| docs/config-tui.fr_fr.md | docs | Mesma correção — "Délibérément Non Éditables" |
| ~/.gitpr/.env | chore | Removida a linha 25 (`PR_AUTO_PUBLISH='false'`). Fora do repositório |

As 5 docs mantêm paridade estrutural exata após a mudança: **161 linhas, 12 títulos, 52 linhas de tabela, 4 fences** em cada uma.

## Impact

- **Functionality:** nenhuma. **Zero linhas de `src/` foram tocadas** — a tela estava correta. `Desconhecidas` é o comportamento projetado: o glossário define que uma chave desconhecida "may belong to a newer GitPR, a plugin, or a shell script of the user's", então a tela a preserva intacta em vez de oferecer remoção.
- **Performance:** nenhum.
- **Compatibility:** nenhuma. `PR_AUTO_PUBLISH` nunca foi lida, então removê-la do `.env` não altera comportamento algum em runtime. A remoção deixa 2 chaves não declaradas em vez de 3.

## Verification

1. `grep -c 'PR_AUTO_PUBLISH' CLAUDE.md` → **0**.
2. `grep -n '^## 5\.' docs/config-tui*.md` → as 5 com o título novo, nenhuma ainda dizendo "Fora da Tela" / "Hors de l'Écran".
3. `diff` do `.env` antes/depois → **exatamente uma linha removida** (`25d24`), comentários e ordem intactos.
4. Recálculo de Desconhecidas contra o `.env` real → **2** chaves (`GITPR_SCM_TOKEN`, `GITPR_SHOW_LOGS`), antes 3.
5. Suíte completa: **6 failed, 911 passed, 2 skipped, 33 subtests** — idêntico ao resultado anterior a esta mudança. Nenhuma regressão.

## Next steps (if applicable)

- **`GITPR_SHOW_LOGS` continua chave morta** — declarada em `DEFAULT_CONFIG`, semeada em todo `.env`, prometida no `CHANGELOG.md` e documentada em `docs/pull-request-publication.md`, e **lida em lugar nenhum**. Diferente de `PR_AUTO_PUBLISH`, ela ainda é semeada hoje. Decidir: implementar ou remover. Ficou fora do escopo desta limpeza.
- As 6 falhas pré-existentes da suíte seguem sem correção (ver Notas).

## Notas (pré-existentes / fora do escopo)

1. **6 falhas pré-existentes da suíte**, as mesmas já registradas no relatório da feature `gitpr config` e confirmadas contra um `git archive HEAD` em diretório temporário: `test_chat_backend::test_api_exception`, `test_main_suggest_reviewers::test_flag_appears_in_contextual_help`, `test_suggest_reviewers::TestFormatHelpers` (×2) — assumem saída em inglês e quebram com o locale pt_BR da máquina — e `test_net_timeouts::TestTimeoutConfig` (×2), que esperam timeout 600 enquanto `_DEFAULT_AI_TIMEOUT` é `180.0` no HEAD.
2. **Backup do `.env`** criado antes da remoção em `/tmp/gitpr_env_backup_20260912_072357.env`. Reverter é readicionar a linha `PR_AUTO_PUBLISH='false'`.
3. **Registros históricos intocados** por decisão: `docs/claude-code/reports/2026-08-06_pr_publish_github.md` e `docs/plans/20260807_*` documentam o que era verdade na época — reescrevê-los seria falsificar histórico. O survey `docs/survey/20260912_gitpr_config_tui_surveyfacts.md` (fato #34) já registrava corretamente que a chave não existe em `src/`.
4. **`GEMINI.md` verificado**: não lista `PR_AUTO_PUBLISH` (0 ocorrências). Nenhum `langs/*.json` a menciona — nada a traduzir.
5. **Nenhum `git commit`/`git add`/`git push`** foi executado — todas as alterações permanecem na working tree para revisão (regra do CLAUDE.md).
