# Plano: Help Contextual para GitPR CLI

## Contexto

Atualmente `gitpr -h` usa `@click.help_option` que intercepta antes do `cli()` rodar — impossível saber quais outras flags foram passadas junto. O objetivo é permitir `gitpr -h --issue` mostrando help específico daquela feature + link para a doc detalhada no GitHub.

## Abordagem

1. **Trocar `@click.help_option` por flag regular** — `-h`/`--help` vira `is_flag=True`, permitindo que o corpo do `cli()` veja `help=True` junto com as outras flags
2. **Dispatcher de help contextual** — primeiro bloco do `cli()`: se `help=True`, varre as flags ativas, seleciona a mais prioritária e mostra help + URL da doc
3. **Criar docs faltantes** — 7 novos arquivos em `docs/` para as flags que ainda não têm documentação dedicada

## Mapeamento flag → doc

| Flag                                  | Doc                                  | Status   |
| ------------------------------------- | ------------------------------------ | -------- |
| `--issue`, `--history`                | `docs/issue-tui-help.md`             | ✅ existe |
| `--linter`                            | `docs/linter-regras-customizadas.md` | ✅ existe |
| `--installhooks`                      | `docs/git-hooks-locais.md`           | ✅ existe |
| `--review`, `--fullreview`, `--input` | `docs/code-review-ia.md`             | ❌ criar  |
| `--commit`                            | `docs/commit-message-ia.md`          | ❌ criar  |
| `--blame`                             | `docs/blame-arqueologo.md`           | ❌ criar  |
| `--skill`                             | `docs/skill-template.md`             | ❌ criar  |
| `--update`                            | `docs/auto-update.md`                | ❌ criar  |
| `--provider`                          | `docs/providers-ia.md`               | ❌ criar  |
| *(padrão/sem flags)*                  | `docs/pr-descricao-padrao.md`        | ❌ criar  |

## Alterações em `src/main.py`

1. **Linha 38**: Remove `@click.help_option('-h', '--help', ...)`, adiciona `@click.option('-h', '--help', is_flag=True, help='...')`
2. **Linha 48**: Muda `--input` de `type=click.Path(exists=True)` para `type=click.Path()` (evita erro de validação quando usado com `-h`)
3. **Linha 53**: Adiciona `help` ao final da assinatura de `cli()`
4. **Após `print_banner()`**: Insere dicionários `HELP_MAP` (flag → título, descrição, URL) e `HELP_PRIORITY` (flag → prioridade numérica)
5. **Início do `cli()`**: Insere dispatcher de help contextual (~40 linhas):
   - Se `help=True` e nenhuma outra flag → imprime help padrão via `ctx.get_help()`
   - Se `help=True` + flags → seleciona a mais prioritária, mostra título + descrição + URL da doc no GitHub
   - Múltiplas flags → dica para usar `-h` com uma flag por vez
6. **Validação do `--input`**: Adiciona guard `not help` + `os.path.exists()` explícito (já que removemos `exists=True`)

## Comportamento esperado

| Comando                     | Resultado                                                           |
| --------------------------- | ------------------------------------------------------------------- |
| `gitpr -h`                  | Help padrão do Click (todas as opções)                              |
| `gitpr -h --issue`          | Título + descrição de Issue + link `issue-tui-help.md`              |
| `gitpr -h --linter`         | Título + descrição do Linter + link `linter-regras-customizadas.md` |
| `gitpr -h --installhooks`   | Título + descrição dos Hooks + link `git-hooks-locais.md`           |
| `gitpr -h -c`               | Título + descrição de Commit + link `commit-message-ia.md`          |
| `gitpr -h --issue --blame`  | Help de Issue (maior prioridade) + dica                             |
| `gitpr -h -i algum_arquivo` | Help de Input/Review + link `code-review-ia.md`                     |

## Novos arquivos de documentação (7 docs)

Cada doc segue o padrão dos existentes: português, tabelas, blocos de código bash, ~2-4 KB.

1. **`docs/code-review-ia.md`** — `-r`/`-f`/`-i`: modos de review, diff local vs completo, auditoria de arquivo, integração com linter
2. **`docs/commit-message-ia.md`** — `-c`: Conventional Commits, integração com hook prepare-commit-msg, customização via `.gitpr.commit.md`
3. **`docs/blame-arqueologo.md`** — `-b`: formatos de sintaxe, profundidade de rastreamento, integração com `--issue`
4. **`docs/skill-template.md`** — `-s`: o que são skills, templates disponíveis, customização, não-sobrescrita
5. **`docs/auto-update.md`** — `-u`: hot-swap, verificação diária, pip vs binário
6. **`docs/pr-descricao-padrao.md`** — modo padrão: fluxo completo, fetch → diff → IA → `.md`
7. **`docs/providers-ia.md`** — `-p`: Gemini vs DeepSeek, configuração, modelos, fallback

## Ordem de implementação

1. Criar os 7 arquivos de doc em `docs/`
2. Alterar `src/main.py` (help flag + dispatcher + HELP_MAP + validação input)
3. Atualizar README.md com links para os novos docs
4. Testar: `gitpr -h`, `gitpr -h --issue`, `gitpr -h --linter`, `gitpr -h -c`, etc.

## Verificação

- `pipenv run python src/main.py -h` → help padrão Click
- `pipenv run python src/main.py -h --issue` → help contextual + URL
- `pipenv run python src/main.py -h --linter` → help contextual + URL
- `pipenv run python src/main.py -h --installhooks` → help contextual + URL
- Comandos normais (`-c`, `-r`, `-is`) continuam funcionando
- `pipenv run pytest -v` sem regressões
