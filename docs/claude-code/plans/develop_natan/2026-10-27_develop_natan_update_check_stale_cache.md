# Fix: update check não detecta novo release a tempo

Branch: `develop_natan` · Data: 2026-10-27 · Versão alvo: 1.4.3

## Contexto

Usuários na 1.4.1 não são avisados de que a 1.4.2 existe. Causa confirmada na
máquina do mantenedor:

- `~/.gitpr/update_cache.json` = `{"date": "2026-10-27", "version": "1.4.1"}`,
  gravado às 07:54 -03; a 1.4.2 foi publicada às 10:45 -03.
- `src/updater.py` aceitava o cache enquanto `date == hoje` (até a meia-noite
  local), então toda execução depois do release comparou `1.4.1 <= 1.4.1`.
- `check_and_update()` (`gitpr -u`) lia o mesmo cache, contrariando
  `docs/auto-update.md`.

Buracos adicionais: subcomandos retornavam antes do gate; o skip switch aceitava
qualquer valor não vazio; `parse_version` devolvia `(0, 0, 0)` para PEP 440 com
sufixo; o fetch usava `urllib` cru, sem limite de DNS.

## Decisões

1. TTL corrido de 1 h no cache; `-u/--update` sempre consulta o PyPI.
2. Gate de subcomandos apenas em execução interativa (TTY nos dois lados,
   `--quiet/--hook/--mcp` isentos). Raiz inalterada.
3. `GITPR_SKIP_UPDATE_CHECK` estrito (`1/true/yes/on/y`).
4. Comparação PEP 440, pré-release remoto ignorado para instalação estável,
   versão inválida = desconhecida, fetch via `bounded_urlopen`, cache atômico.
5. Docs nas 5 variantes de `auto-update.*` e `tutorial/install-from-source.*`.
6. Bump 1.4.3 + CHANGELOG.

## Mudanças

### `src/updater.py`

- Constantes `UPDATE_CACHE_TTL_SECONDS = 3600`, `UPDATE_FETCH_HARD_TIMEOUT = 3.0`
  e `_SKIP_TRUTHY_VALUES`.
- Cache `{"checked_at": ISO local, "version": str}` com `_cache_is_fresh()`,
  `_read_cached_version()` e `_write_cached_version()` (temp no mesmo diretório +
  `os.replace`; falha de escrita não esconde a versão buscada).
- `_coerce_version()` (PEP 440, remove um único `v` inicial) e `parse_version()`
  como shim compatível sobre o release tuple.
- `_fetch_pypi_version()` via `bounded_urlopen(PYPI_API_URL, timeout=3,
  hard_timeout=3, headers={"User-Agent": "GitPR-Updater"})`; versão inválida não
  é cacheada.
- `get_latest_remote_version(force=False)`.
- `_is_newer(remote, local=None)` usado por `enforce_update_required()` e
  `check_and_update()` (este com `force=True`).
- `is_update_check_disabled()` estrito.
- `__version__ = "1.4.3"`. Sem strings i18n novas; `__lang_version__` intocado.

### `src/main.py`

- `_subcommand_help_in_argv()` lê `sys.argv` (o Click limpa `ctx.args` antes do
  callback do grupo).
- Antes de `if ctx.invoked_subcommand is not None: return`, aplica
  `enforce_update_required()` quando `may_ask and not update and not help_flag
  and not _subcommand_help_in_argv()`.
- Raiz (linha ~752) intocada.

### `tests/test_updater.py`

- Novos helpers de cache (`write_cache` com `checked_at`, `write_raw_cache`,
  `_pypi_payload`) e mocks em `src.updater.bounded_urlopen`.
- Cobertura: TTL (fresco, borda, expirado, timestamp futuro), cache legado
  `date`, JSON corrompido, tipos inválidos, versão vazia, `force`, falha de
  escrita, ausência de `.tmp`, headers/timeouts, comparador PEP 440,
  pré-release, post-release, versão inválida, flag estrita, `-u` forçado/offline
  e gate de subcomando via `badge --readme` (bloqueio, isenção sem TTY, isenção
  com `-h`).

### Documentação

- `docs/auto-update.{md,pt_br,pt_pt,es_es,fr_fr}.md`: janela de 1 h, `-u` sem
  cache, subcomandos interativos, novas isenções, PEP 440 e offline.
- `docs/tutorial/install-from-source.{md,pt_br,pt_pt,es_es,fr_fr}.md`: cache de
  1 h, parser estrito, religar com `=0`, tabela de isenções atualizada e nota de
  que flags continuam bloqueadas sem TTY.

### Versão e CHANGELOG

- `__version__ = "1.4.3"`; seção `## [1.4.3] - 2026-10-27` no topo do
  `CHANGELOG.md`.

## Verificação

1. `python -m pytest tests/test_updater.py -v`.
2. `python -m pytest tests/test_core.py tests/test_diff_failure_cli.py
   tests/test_net_timeouts.py tests/badge tests/test_release_cli.py
   tests/test_metrics.py tests/test_baseline_cli.py tests/test_check_cli.py
   tests/test_policy_cli.py tests/fix/test_fix_cli.py -q`.
3. `python -c "from src.updater import get_latest_remote_version;
   print(get_latest_remote_version(force=True))"` e inspeção do cache novo.
4. `python run.py -u`; `python run.py --quiet --status`; `python run.py
   metrics summary` (sem TTY).

## Riscos

- Bootstrap: instalações 1.4.1 precisam de um upgrade manual para receber a
  correção.
- CDN do PyPI pode atrasar alguns minutos a publicação.
- Relógio para trás invalida o cache (comportamento seguro).
- `-u` offline perde o cache fresco e reporta falha (contrato do comando).
- `gitpr-mcp` continua fora do gate.

## Fora de escopo

Auto-instalação, a instalação 1.2.0 / resíduo `~itpr-cli`, a linha de versão do
`CLAUDE.md` e o README.
