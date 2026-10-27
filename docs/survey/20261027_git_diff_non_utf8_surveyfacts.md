# Survey — UnicodeDecodeError ao ler diff não-UTF8

## Contexto da tarefa

Ao executar `gitpr` em `C:\Users\nataniel\projetos\gjb\SIG-Novo`, o comando
imprimiu um traceback de `UnicodeDecodeError` dentro de
`subprocess._readerthread` (`'utf-8' codec can't decode byte 0xfa in position
14715`) logo após a mensagem de sincronização com o remoto, e em seguida
respondeu "⚠️ Nenhum código novo encontrado". O repositório contém arquivos
legados em Latin-1; o diff inteiro era descartado e a falha ficava invisível.

## Fatos levantados

### Causa raiz

- `src/core.py:1496` (`get_git_full_diff`) executava
  `git diff -U1 -w -M -B <merge-base> -- <SMART_EXCLUDES>` com
  `capture_output=True, text=True, encoding="utf-8", check=True` e **sem**
  `errors="replace"`. O byte `0xFA` (e também `0xE7`, reproduzido no teste)
  derrubava o reader thread do `subprocess`.
- No Python 3.13/Windows, a morte do reader thread não levanta exceção no
  chamador: `CompletedProcess.returncode` continua 0 e `stdout` volta `None`.
  `get_git_full_diff()` devolve `None`.
- `src/main.py:1445` (`if not diff_text or not diff_text.strip()`) tratava
  `None` e `""` da mesma forma, emitindo a mensagem de "nenhum código novo".
- O `except subprocess.CalledProcessError` de `get_git_full_diff` não cobria
  `UnicodeDecodeError`; o `git fetch` estava em modo bytes (sem decoder), mas
  seu `e.stderr` aparecia como `b'...'` na mensagem vermelha.

### Auditoria de call sites

Varredura AST de todos os `subprocess.run` em `src/`: 54 chamadas diretas em 18
arquivos. Dez eram decodificação de texto sem `errors=`:

- `src/core.py`: 1441 (`symbolic-ref`), 1475 (`merge-base`), 1496 (`diff`),
  2041 (`merge-base`), 2051 (`git log`)
- `src/cache.py`: 23 e 26 (`git config user.name/email`)
- `src/issue_engine.py`: 22 (`git remote -v`)
- `src/main.py`: 1320 e 1323 (`git config user.name/email`)

`src/core.py:1465` (`git fetch`) estava em modo bytes. Os demais já seguiam a
regra ou eram modo bytes deliberado com decodificação explícita
(`patch_applier.py:87`).

### Fluxo e consumidores

- `get_git_full_diff` é usado por `main.py:1433` (`--fullreview`),
  `main.py:1442` (PR padrão), `main.py:5146` (`risk`), `mcp_server.py:496/687/745/1431`
  e `fix/apply_fix.py:130`.
- `get_git_diff` (commit/review) também devolve `None` em falha
  (`core.py:551-561`), e o mesmo bloco de checagem em `main.py` serve os quatro
  fluxos.
- `gitpr risk` tem mensagem própria e foi deixado fora do escopo; MCP coage
  `None` para `""` e também não foi alterado.
- Hooks: `scripts/prepare-commit-msg-template.sh` chama
  `gitpr --commit --quiet --hook`; um exit não-zero ali abortaria o commit do
  usuário.

### Versão e CHANGELOG

- `pyproject.toml` lê a versão via `attr = "src.updater.__version__"`:
  `src/updater.py:10` é a fonte única.
- O release engine ancora a próxima release no *hash do bullet mais novo* da
  seção anterior do changelog (`_previous_block`); uma seção escrita à mão sem
  hash não serve de âncora e pode duplicar o commit na release seguinte.

### Testes

- Fixture real existente: `tests/fix/git_fixture.py` (`GitRepoTestCase`,
  `tempfile.mkdtemp`, `core.autocrlf=false`, `commit.gpgsign=false`).
- `tests/__init__.py` existe; `tests/conftest.py` fixa `GITPR_LANG=en_us`,
  `GITPR_SKIP_UPDATE_CHECK=true`.
- Padrão de CLI: `unittest` + `click.testing.CliRunner` + `patch("src.main.<nome>")`
  (`tests/test_risk_cli.py`). `--no-unstaged-check` evita a TUI de unstaged.
- `gitpr release --force` regenera uma seção existente; a âncora pula a própria
  versão e usa a anterior.
- Suítes i18n (3) e badge (7) já falhavam antes desta task — registrado no plano
  de 2026-10-18.

## Rodadas de decisão

### Rodada 1

- **Abrangência:** todos os call sites de decodificação sem `errors` (10) +
  `git fetch` em text mode. (Recomendado e aceito.)
- **Falha silenciosa:** incluir guarda distinguindo falha de git de diff vazio.
  (Recomendado e aceito.)
- **Teste:** repositório git real com arquivo Latin-1. (Recomendado e aceito.)
- **Release:** bump 1.4.2 + CHANGELOG. (Aceito; recomendação era só código.)

### Rodada 2

- **Exit code:** erro + exit 1. (Recomendado e aceito.)
- **Escopo da guarda:** PR/review/fullreview no bloco compartilhado, sem
  `gitpr risk`. (Recomendado e aceito.)
- **CHANGELOG:** placeholder sem hash e regeneração posterior com
  `gitpr release --force`. (Recomendado e aceito.)

### Refinamentos do agente de planejamento

- São 10 sites, não 9; o bug devolve `None`, não `""`.
- `--hook` precisa falhar aberto (`return`) para não abortar commits.
- Sem chave i18n nova; paridade dos seis arquivos não é afetada.
- Não bumpar `__lang_version__`/`__scripts_version__`.
- Teste precisa de `chdir` com cleanup LIFO e `redirect_stdout` por causa do
  cp1252 no Windows.

## Execução

- `src/core.py`: encoding/errors em 5 chamadas + fetch em text mode.
- `src/cache.py`, `src/issue_engine.py`, `src/main.py`: encoding/errors nos 5
  sites restantes.
- `src/main.py`: guarda `None` → hook fail-open ou `click.exceptions.Exit(1)`;
  checagem de vazio passou a ser `if not diff_text.strip()`.
- `tests/test_full_diff_encoding.py`: repo real com origin bare, arquivo Latin-1
  commitado e assert de `U+FFFD`.
- `tests/test_diff_failure_cli.py`: None → exit 1; vazio → exit 0 com mensagem;
  `--hook` → exit 0 sem mensagem.
- `src/updater.py`: `1.4.2`; `CHANGELOG.md`: seção 1.4.2 placeholder.

## Verificação

- 3 testes novos passam.
- `tests/fix`: 204 passam.
- `tests/test_updater.py`, `test_release_engine.py`, `test_changelog_builder.py`:
  98 passam; âncora de 1.4.2 resolve para 1.4.1.
- Suíte completa: 2951 passam, 10 falham — 3 i18n e 7 badge, pré-existentes.
- Smoke no SIG-Novo: `str`, 339.292 caracteres, `U+FFFD` presente, sem traceback.
