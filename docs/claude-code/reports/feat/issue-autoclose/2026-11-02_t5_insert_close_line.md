## Completion Report — T5: inserção idempotente da closing line

### What was done

- Criado `src/issue_autoclose/insert_close_line.py`, o consumidor da decisão
  da T4, com duas funções puras (sem `click`, sem rede, sem i18n):
  - `has_closing_reference(body, number)` — reconhece uma referência de
    fechamento já presente, exatamente no vocabulário do ADR-004:
    `close/closes/closed`, `fix/fixes/fixed`, `resolve/resolves/resolved`,
    opcionalmente `owner/repo` antes de `#N`, sem diferenciar maiúsculas. Os
    limites de palavra garantem que `#12` não casa com `#123` e que
    `disclosed #7`/`prefixed #7` não contam.
  - `insert_close_line(body, decision)` — sem decisão, devolve o corpo
    intacto; com decisão e sem referência ao mesmo número, acrescenta
    `decision.line` como parágrafo próprio (uma linha em branco de separação,
    sem espaços sobrando); corpo vazio recebe só a linha. A linha vem do
    provider (`closing_line`, T2/T4) — o módulo não monta sintaxe de forge.
- Ligação no ponto único de montagem (`src/main.py`):
  - o ramo do PR declara `close_issue_decision = None` — o seam que a T6
    passará a preencher com `resolve_close_issue`;
  - depois do bloco **Explain my PR** e antes de `markdown_content`, o corpo
    recebe `insert_close_line(pr_desc_body, close_issue_decision)`.
  - Efeito: a linha entra no `.md` local gravado em 1824, no retorno de
    `--no-publish` e em `pr_data`, que alimenta a TUI e `_publish_pr_directly`.
    O badge é anexado depois (`attach_pr_badge` → `append_badge`, que sempre
    anexa ao fim do corpo), então a linha fica imediatamente antes dele sem
    que o helper conheça badge.
- `src/issue_autoclose/__init__.py`: `insert_close_line.py` acrescentado à
  lista de módulos do pacote.
- Nenhuma chave i18n nova (a closing line é sintaxe do forge) e nenhuma
  configuração nova.

### Changed files

| File | Change type | Description |
|------|-------------|-------------|
| `src/issue_autoclose/insert_close_line.py` | feat | Detecção idempotente e inserção da closing line no corpo |
| `src/main.py` | feat | Seam `close_issue_decision` e chamada no ponto único de montagem |
| `tests/issue_autoclose/test_insert_close_line.py` | test | 19 testes (41 subtestes) para inserção, idempotência e regex |
| `src/issue_autoclose/__init__.py` | docs | Lista de módulos do pacote completa |

### Impact

- **Functionality:** ainda inativo para o usuário — `close_issue_decision` é
  `None` nesta tarefa, então o corpo do PR sai idêntico ao de antes. A T6
  troca o literal pela chamada de `resolve_close_issue` e a feature passa a
  funcionar.
- **Performance:** sem decisão, o helper retorna imediatamente, sem regex.
  Com decisão, uma varredura de regex sobre o corpo.
- **Compatibility:** nenhuma assinatura pública existente mudou; nenhum
  caminho de publicação (TUI, `--no-edit`, `--no-publish`) foi alterado.
- **Fronteira preservada:** o módulo não imprime, não importa `click` nem
  `requests`; o único consumidor é `main.py`.
- **Testes:** 19 novos métodos (41 subtestes novos); nenhuma regressão.

### Verificação da suíte

- `python -m pytest tests/issue_autoclose -q` → **94 passed, 56 subtests
  passed**.
- `python -m pytest tests/issue_autoclose tests/scm -q` → **415 passed,
  2 skipped, 74 subtests passed**.
- `python -m pytest tests/test_i18n.py -q` → **22 passed** (nenhuma chave
  criada por engano).
- Suíte ampla sem os dois arquivos de UI instáveis (`test_config_app.py`,
  `test_commit_app.py`) e com a deseleção do teste pré-existente que trava sem
  TTY: **3133 passed, 2 skipped, 1 deselected, 197 subtests passed**
  (289,20 s).
  - As duas primeiras execuções amplas tiveram 8 falhas em
    `tests/test_plugins.py` (`rules` com as 7 regras de segurança + projeto em
    vez de vazio). É o vazamento pré-existente e dependente de ordem já
    documentado nas T1–T4: um teste da suíte reescreve `SCRIPTS_LANG` em
    `~/.gitpr/.env`, o `check_and_update_hooks_scripts()` então sincroniza os
    hooks e o `load_dotenv(ENV_FILE, override=True)` traz
    `GITPR_LINTER_SECURITY='true'` para o processo, sobrepondo o pin do
    `conftest.py`. Em isolamento os 17 testes passam; depois que a marcação
    assentou (`SCRIPTS_LANG=pt_br`, `SCRIPTS_INSTALLED_LANG=pt_br`), a terceira
    execução ampla passou limpa. Alheio à T5 (os testes de plugins não importam
    `main.py` nem o pacote `issue_autoclose`).
- Nenhum `git add`, `git commit` ou `git push` — tudo permanece na árvore de
  trabalho.

### Divergências em relação ao plano

- Nenhuma de SPEC/ADR. O helper devolve a string do corpo (não um dataclass),
  como aprovado no plano: o único consumidor precisa só do corpo, e a T6 sabe
  que houve decisão por `close_issue_decision is not None`.
- O ponto físico escolhido (antes de `markdown_content`) faz a linha aparecer
  também no `.md` local e em `--no-publish`, conforme a revisão de T0 do
  ADR-004; o badge continua depois, no corpo publicado.

### Next steps

- T6: chamar `resolve_close_issue` no ramo do PR (provider/repo antes da TUI de
  stage), preencher `close_issue_decision`, adicionar `--close-issue` /
  `--no-close-issue` mutuamente exclusivos, imprimir `outcome.warning` e limpar
  o registro quando o PR for criado (ADR-007).
- T7: `GITPR_ISSUE_AUTOCLOSE` / `GITPR_ISSUE_AUTOCLOSE_TIMEOUT` no schema e na
  TUI de configuração.
- T8: métrica `issue_autoclose` (`asked`, `accepted`, `skipped_reason`).
- T9: documentação do usuário.
- Aguardar confirmação do usuário antes da T6.
