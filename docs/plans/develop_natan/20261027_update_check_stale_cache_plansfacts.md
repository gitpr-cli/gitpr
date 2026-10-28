# Plano — Corrigir o update check que ignora um release do mesmo dia

## Contexto

Usuários na 1.4.1 não recebem aviso da 1.4.2 porque o cache da checagem é
chaveado pelo dia local: `~/.gitpr/update_cache.json` foi gravado às 07:54 -03
com `1.4.1`, a 1.4.2 saiu às 10:45 -03, e o cache continuou válido até a
meia-noite. `gitpr -u` lê o mesmo cache. Subcomandos retornam antes do gate,
`GITPR_SKIP_UPDATE_CHECK=false` desliga a checagem e `parse_version()` devolve
`(0, 0, 0)` para versões PEP 440 com sufixo.

## Decisões (grill)

1. Cache com **TTL corrido de 1 hora**; `-u/--update` **ignora o cache** e
   consulta o PyPI sempre.
2. Gate estendido a **subcomandos apenas com TTY** (`_may_ask_the_user`). A raiz
   continua bloqueando sem TTY; `--quiet/--hook/--mcp` isentos.
3. `GITPR_SKIP_UPDATE_CHECK` booleano estrito: só `1/true/yes/on/y` desligam.
4. Correção completa: `packaging.version.Version` (PEP 440), pré-release remoto
   ignorado quando o local é estável, `bounded_urlopen`, escrita atômica, guarda
   de tipo.
5. Documentação nas 5 variantes (`auto-update.*` e
   `tutorial/install-from-source.*`).
6. Bump para **1.4.3** + seção no CHANGELOG nesta entrega.

## Implementação

### 1. `src/updater.py`

- `UPDATE_CACHE_TTL_SECONDS = 3600` e `UPDATE_FETCH_HARD_TIMEOUT = 3.0`.
- Cache novo `{"checked_at": "<ISO local>", "version": "<str>"}`; helpers
  `_cache_is_fresh()`, `_read_cached_version()` e `_write_cached_version()`
  (temp na mesma pasta + `os.replace`).
- `_coerce_version()` sobre `Version` PEP 440; `parse_version()` vira um shim
  compatível que devolve o release tuple (ou `(0, 0, 0)`).
- `get_latest_remote_version(force=False)` usa `bounded_urlopen` e só grava
  versões válidas.
- `_is_newer()` centraliza a comparação (pré-release remoto não bloqueia
  instalação estável; versão inválida = desconhecida).
- `enforce_update_required()` e `check_and_update()` passam a usar `_is_newer`;
  o último força a rede.
- `is_update_check_disabled()` com a lista `("1", "true", "yes", "on", "y")`.
- Nenhuma string i18n nova → `__lang_version__` intacto.

### 2. `src/main.py`

- Helper `_subcommand_help_in_argv()` (varre `sys.argv`, porque o Click limpa
  `ctx.args` antes do callback do grupo).
- Antes de `if ctx.invoked_subcommand is not None: return`, reusa `may_ask`,
  `update` e `help_flag` para aplicar o gate aos subcomandos interativos.
- Raiz inalterada.

### 3. `tests/test_updater.py`

- Migração dos mocks de `urllib` para `src.updater.bounded_urlopen` e do cache
  para o novo schema.
- Cobertura de: TTL (fresco, na borda, expirado, futuro), cache legado/corrupto/
  tipos inválidos, `force=True`, falha de escrita, cache inválido não gravado,
  boilerplate PEP 440, pré-release, flag estrita, gate de subcomando com
  `badge --readme` (bloqueio, isenção sem TTY, isenção com `-h`).

### 4. Documentação (5 idiomas cada)

- `docs/auto-update.*`: "24 hours" → 1 hora (janela móvel), `-u` ignora o cache,
  subcomandos interativos, novas linhas de isenção, PEP 440 e offline.
- `docs/tutorial/install-from-source.*`: cache de 1 h, parser estrito, religar
  com `=0`, tabela de isenções (subcomandos não interativos e help) e o
  esclarecimento de que flags continuam bloqueadas sem TTY.

### 5. Versão e CHANGELOG

- `__version__ = "1.4.3"` e seção `## [1.4.3] - 2026-10-27` no topo do
  `CHANGELOG.md`.

## Verificação

1. `python -m pytest tests/test_updater.py -v`.
2. Regressão: `tests/test_core.py`, `tests/test_diff_failure_cli.py`,
   `tests/test_net_timeouts.py`, `tests/badge`, `tests/test_release_cli.py`,
   `tests/test_metrics.py`, `tests/test_baseline_cli.py`, `tests/test_check_cli.py`,
   `tests/test_policy_cli.py`, `tests/fix/test_fix_cli.py`.
3. Consulta real ao PyPI com `force=True` e inspeção do novo
   `~/.gitpr/update_cache.json`.
4. `python run.py -u` e `python run.py --quiet --status`.

## Riscos e notas

- **Bootstrap:** quem está na 1.4.1 só recebe a correção após um
  `pip install --upgrade gitpr-cli`; a lógica antiga não detecta a 1.4.3 no
  mesmo dia.
- PyPI/CDN pode servir a versão anterior por alguns minutos após o upload.
- Relógio para trás → `checked_at` no futuro conta como expirado.
- `-u` offline passa a dizer "Could not check" mesmo com cache fresco.
- `gitpr-mcp` continua fora do gate (entry point próprio, por design).
- Sem ADR: decisão reversível e registrada na documentação.

## Fora de escopo

- Auto-instalação (o projeto nunca instala nada).
- Corrigir a instalação 1.2.0 / resíduo `~itpr-cli` desta máquina.
- Atualizar a linha "Current version" do `CLAUDE.md` (já defasada antes).
- README (a frase "on every run" já era imprecisa antes da mudança).
