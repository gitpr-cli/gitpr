# Plano — Corrigir diff não-UTF8 e a falha silenciosa do git

## Contexto

Rodando `gitpr` em `C:\Users\nataniel\projetos\gjb\SIG-Novo`, o comando imprimiu
`UnicodeDecodeError: 'utf-8' codec can't decode byte 0xfa in position 14715`
dentro de `subprocess._readerthread`, logo depois de "🔄 Sincronizando com o
repositório remoto (git fetch)...", e em seguida exibiu a mensagem enganosa
"⚠️ Nenhum código novo encontrado".

Cadeia comprovada:

1. `src/core.py:1496` — `get_git_full_diff()` roda
   `git diff -U1 -w -M -B <merge-base> -- <SMART_EXCLUDES>` com
   `text=True, encoding="utf-8"` e **sem `errors="replace"`**. O conteúdo Latin-1
   do repositório (byte `0xFA` = `ú`) entra no diff e derruba o reader thread.
   No Python 3.13/Windows o `subprocess.run(..., check=True)` retorna
   `CompletedProcess(returncode=0, stdout=None)` — nenhuma exceção chega ao
   chamador — e `get_git_full_diff()` devolve `None`.
2. `src/main.py:1445` — `if not diff_text or not diff_text.strip()` trata falha
   (`None`) e diff vazio (`""`) da mesma forma, imprimindo "Nenhum código novo
   encontrado".

O `CLAUDE.md` já declara `errors='replace'` como regra absoluta para toda leitura
de git/arquivo; a chamada viola a regra. O mesmo defeito existe em outros 9 pontos
que decodificam saída do git sem `errors` (o repo SIG-Novo estouraria em
`git log`, `git blame`, `git config` etc. na sequência).

## Decisões (grilling)

- Corrigir **todos os 10 call sites** que decodificam sem `errors="replace"`,
  mais o `git fetch` (modo bytes → text mode), sem refactor para helper novo.
- Guarda no bloco compartilhado de PR/review/fullreview/commit: `None` = falha do
  git → **exit 1**; diff vazio → mensagem atual, exit 0. Em `--hook`, falhar
  aberto (`return`) para não abortar o commit do usuário. `gitpr risk` e tools
  MCP ficam intactos.
- Teste de regressão com **repositório git real** e arquivo Latin-1 commitado.
- **Bump 1.4.2** + seção 1.4.2 no CHANGELOG como placeholder (sem link de commit);
  `gitpr release --force` regenera com hashes depois que o commit existir.

## Implementação

### 1. Varredura de encoding (10 sites + fetch)

Manter `text=True` onde já existe; adicionar `encoding="utf-8", errors="replace"`:

| Arquivo:linha | Comando |
| --- | --- |
| src/core.py:1441 | `git symbolic-ref refs/remotes/origin/HEAD` |
| src/core.py:1475 | `git merge-base origin/<base> HEAD` |
| src/core.py:1496 | `git diff -U1 -w -M -B ...` (**bug**) |
| src/core.py:2041 | `git merge-base origin/<base> HEAD` |
| src/core.py:2051 | `git log <ancestor>..HEAD ...` |
| src/cache.py:23 | `git config user.name` |
| src/cache.py:26 | `git config user.email` |
| src/issue_engine.py:22 | `git remote -v` |
| src/main.py:1320 | `git config user.name` |
| src/main.py:1323 | `git config user.email` |

E `src/core.py:1465` (`git fetch origin`): adicionar
`text=True, encoding="utf-8", errors="replace"` para que `e.stderr` seja `str`
(hoje a mensagem vermelha imprime `b'...'`) e nenhuma leitura possa levantar.

Não tocar nos demais ~44 call sites: já seguem a regra ou são modo bytes com
decodificação explícita (`patch_applier.py:87`).

### 2. Guarda de falha no CLI

Em `src/main.py:1444-1452`, substituir a checagem atual:

```python
# A git failure is not an empty diff. get_git_full_diff()/get_git_diff()
# return None when git fails; folding that into "no new code found" hides it.
# Exit non-zero so scripts can tell the two apart. Hook mode fails open: a
# non-zero prepare-commit-msg hook makes git abort the user's commit.
if diff_text is None:
    if hook:
        return
    raise click.exceptions.Exit(1)

# CRITICAL: Warn the user before exiting if there are no changes
if not diff_text.strip():
    ... mensagem existente ...
    return
```

- Cobre PR, `--fullreview`, `--review` e o fluxo de commit (todos convergem neste
  bloco; `get_git_diff` também devolve `None` em falha). O `--hook` fica de fora
  do exit 1.
- O padrão `raise click.exceptions.Exit(1)` já é usado em `release`
  (`src/main.py:1898`).
- Não alterar `gitpr risk` (`src/main.py:5146`), MCP nem `fix/apply_fix.py`.
- Nenhuma chave i18n nova: a mensagem vermelha de erro já existe.

### 3. Testes

**`tests/test_full_diff_encoding.py`** — repo real via
`tests/fix/git_fixture.py` (`GitRepoTestCase`):

- `setUp`: criar bare repo temporário (`git init --bare -b main <path>`) como
  `origin`; commit semente; `git remote add origin`; `git push -u origin main`;
  `git remote set-head origin -a` e assertar `symbolic-ref
  refs/remotes/origin/HEAD == refs/remotes/origin/main`; checkout `-b feature`;
  escrever `legacy_encoding.py` em modo binário com `b"# aten\xe7\xe3o:
  conte\xfado legado\nVALUE = 1\n"` (byte `0xFA` real); commitar.
- Teste: `os.chdir(self.dir)` com `addCleanup` de restauração registrado
  **depois** do cleanup de `rmtree` (LIFO no Windows), `patch("src.core.SMART_EXCLUDES", [])`
  e `contextlib.redirect_stdout(io.StringIO())` (emoji do `click.secho` não
  codifica em cp1252 fora do capture do pytest). Chamar `get_git_full_diff()`,
  assertar `is not None`, que o diff menciona `legacy_encoding.py` e contém
  `"conte\ufffddo"` (byte substituído por U+FFFD). Evitar `assertIn` com o diff
  inteiro na mensagem de falha.
- Red-first: rodar antes da correção e ver falhar em `assertIsNotNone`.

**`tests/test_diff_failure_cli.py`** — `CliRunner` + `patch("src.main.get_git_full_diff", return_value=None)`,
`patch("src.main.setup_environment")` e `patch("src.main.check_and_update_hooks_scripts")`,
invocando `["--no-unstaged-check"]` (evita a TUI de unstaged):
- `None` → `exit_code == 1` e `"No new code found"` ausente.
- `""` → `exit_code == 0` e mensagem presente (protege a distinção).
- `--hook` + `get_git_diff` `None` → `exit_code == 0` e mensagem ausente
  (fail-open).

`tests/conftest.py` já fixa `GITPR_LANG=en_us` e desliga o gate de update.

### 4. Versão e CHANGELOG

- `src/updater.py:10`: `__version__ = "1.4.2"` (fonte única; `pyproject.toml` lê
  via `attr`). Não mexer em `__lang_version__` nem `__scripts_version__` (sem
  mudança de idioma/hooks; bumpar forçaria OTA).
- `CHANGELOG.md`: inserir antes de `## [1.4.1]` a seção 1.4.2 com Summary e
  Bug Fixes.

Placeholder consciente: sem hash/link (o commit não existe) e sem token em forma
de hash, para não virar âncora falsa. Depois de commitar, `gitpr release --force`
regenera a seção ancorando em 1.4.1.

### 5. Artefatos obrigatórios

- `docs/survey/20261027_git_diff_non_utf8_surveyfacts.md` (contexto, fatos,
  rodadas e decisões).
- `docs/plans/develop_natan/20261027_git_diff_non_utf8_plansfacts.md` (este plano).
- `docs/claude-code/reports/develop_natan/2026-10-27_git_diff_non_utf8.md`
  (completion report no formato do CLAUDE.md).

## Verificação

1. `python -m pytest tests/test_full_diff_encoding.py tests/test_diff_failure_cli.py -v`
2. `python -m pytest tests/test_i18n.py tests/test_risk_cli.py tests/test_mcp_server.py -q`
   (nenhuma chave i18n nova; risk/MCP intactos).
3. `python -m pytest tests/fix -q` e `python -m pytest -q` (regressão completa).
4. `python -c "from src.updater import __version__; print(__version__)"` → `1.4.2`.
5. Sanidade da âncora: `_previous_block(_read_changelog('CHANGELOG.md'), '1.4.2')`
   deve devolver `1.4.1`.
6. Prova no repo que falhou (somente leitura + `git fetch`), com
   `PYTHONIOENCODING=utf-8` e `PYTHONPATH` apontando para o GitPR:
   `cd C:\Users\nataniel\projetos\gjb\SIG-Novo` e chamar
   `get_git_full_diff()`; conferir `str` não vazio, com `\ufffd`, sem traceback.
7. `git status --short` / `git diff --stat` — nada commitado nem staged.

## Riscos / notas

- **Hook mode**: sem `if hook: return`, um exit 1 no `prepare-commit-msg`
  abortaria o commit do usuário. O fail-open é obrigatório.
- **i18n**: `tests/test_i18n.py` exige paridade nos seis `langs/*.json`; o plano
  não adiciona chave nova.
- `errors="replace"` troca bytes inválidos por `U+FFFD` no texto enviado à IA (e
  muda a chave de cache) — é o contrato vigente do projeto.
- A seção 1.4.2 sem hash não serve de âncora para a próxima release; o
  `--force` no corte resolve. Sem ele, o commit do fix pode reaparecer na seção
  seguinte.
- Windows: escrever o arquivo Latin-1 em modo binário (sem tradução de newline);
  o fixture já fixa `core.autocrlf=false`, `commit.gpgsign=false`.
- `get_git_full_diff` não captura `FileNotFoundError` (git ausente), diferente de
  `get_git_diff`; fora do escopo desta correção cirúrgica.
