## Completion Report — Update check não detecta release publicado depois da primeira execução do dia

### What was done

- Reescrito o controle de versão em [src/updater.py](src/updater.py): o cache diário chaveado por data local (`{"date": "YYYY-MM-DD", "version": ...}`) — que mantinha a resposta da PyPI válida até a meia-noite, mesmo que um release fosse publicado depois — foi substituído por um cache com **TTL corrido de 1 hora** (`{"checked_at": <ISO local>, "version": ...}`).
- Causa raiz comprovada na máquina do mantenedor: `~/.gitpr/update_cache.json` continha `{"date": "2026-10-27", "version": "1.4.1"}`, gravado às 07:54 -03; a 1.4.2 foi publicada às 10:45 -03 e continuou invisível durante todo o dia.
- `gitpr -u/--update` passou a **ignorar o cache** (`force=True`) e consultar a PyPI em toda invocação, como a documentação já prometia.
- Gate de atualização estendido aos **subcomandos em execução interativa** (TTY nos dois lados; `--quiet`, `--hook`, `--mcp` e `-h/--help` isentos). `gitpr release`, `fix`, `review-pr` etc. agora param quando há release novo; CI, pipes e hooks nunca são bloqueados. A raiz permaneceu inalterada.
- Comparação de versões migrada para **PEP 440** (`packaging.version.Version`): `1.4.10 > 1.4.9`, pré-release remoto ignorado para instalação estável e versão inválida tratada como desconhecida (nunca bloqueia).
- Fetch da PyPI migrado do `urllib` cru para `bounded_urlopen` (limite de 3 s de wall clock, incluindo DNS); cache gravado de forma atômica (temp no mesmo diretório + `os.replace`) e versão inválida não é cacheada.
- `GITPR_SKIP_UPDATE_CHECK` passou a aceitar apenas valores verdadeiros (`1/true/yes/on/y`); `false/0/no/off/n` mantêm a checagem ligada.
- Bump para **1.4.3** e seção `## [1.4.3] - 2026-10-27` no `CHANGELOG.md`.
- Documentação atualizada nas 5 variantes (`auto-update.*` e `tutorial/install-from-source.*`): janela de 1 hora, `-u` sem cache, tabela de isenções ampliada, regra PEP 440 e comportamento offline.
- Nenhuma string i18n nova ou alterada; `__lang_version__` e `langs/*.json` intocados.
- Nenhum commit, push ou add foi executado — as mudanças estão na working tree para revisão.

### Changed files

| File | Change type | Description |
|------|-------------|-------------|
| `src/updater.py` | fix | Cache com TTL de 1 h (`checked_at`, escrita atômica), fetch via `bounded_urlopen`, comparação PEP 440, skip switch estrito, `-u` sempre consulta a PyPI, `__version__ = "1.4.3"` |
| `src/main.py` | fix | Gate de atualização aplicado a subcomandos em execução interativa; `_subcommand_help_in_argv()` lê `sys.argv` porque o Click limpa `ctx.args` antes do callback do grupo |
| `tests/test_updater.py` | test | 55 testes: TTL (fresco, borda, expirado, timestamp futuro/aware), cache legado `date`, JSON corrompido, `force`, falha de escrita, ausência de `.tmp`, timeouts/UA, comparador PEP 440, pré-release, skip switch estrito e gate de subcomando (bloqueio, isenção sem TTY, isenção com `-h`) |
| `CHANGELOG.md` | docs | Seção 1.4.3 (Summary, Bug Fixes, Chores) |
| `docs/auto-update.md` + `.pt_br/.pt_pt/.es_es/.fr_fr` | docs | Janela de 1 h, `-u` ignora o cache, subcomandos interativos, novas isenções, PEP 440 e offline |
| `docs/tutorial/install-from-source.md` + `.pt_br/.pt_pt/.es_es/.fr_fr` | docs | Cache de 1 h, parser estrito do switch, tabela de isenções e nota de que flags continuam bloqueadas sem TTY |
| `CONTEXT.md` | docs | Glossário do domínio: update gate, update check, release cache, freshness window, interactive run |
| `docs/survey/20261027_update_check_stale_cache_surveyfacts.md` | docs | Levantamento da sessão de grill: contexto, causa raiz, fatos verificados e 3 rodadas de decisão |
| `docs/plans/develop_natan/20261027_update_check_stale_cache_plansfacts.md` | docs | Plano de execução da sessão |
| `docs/claude-code/plans/develop_natan/2026-10-27_develop_natan_update_check_stale_cache.md` | docs | Plano de implementação no formato do CLAUDE.md |
| `docs/claude-code/reports/develop_natan/2026-10-27_update_check_stale_cache.md` | docs | Este relatório |

### Impact

- **Functionality:** um release publicado depois da primeira execução do dia passa a ser detectado em até 1 hora (antes: só no dia seguinte). `gitpr -u` sempre consulta a PyPI. Subcomandos interativos são bloqueados por um release novo; execuções não interativas (CI, pipes, hooks, MCP) nunca. Pré-releases remotos não bloqueiam instalações estáveis; versões ilegíveis contam como desconhecidas. `GITPR_SKIP_UPDATE_CHECK=false` deixou de desligar a checagem.
- **Performance:** no máximo uma consulta à PyPI por hora por instalação (antes uma por dia); cada consulta tem teto de 3 s de wall clock, DNS incluído. Nenhuma chamada de rede fora do gate.
- **Compatibility:** o cache legado com `date` é ignorado e reescrito no primeiro fetch — sem migração manual. Nenhuma chave i18n nova (`__lang_version__` intocado). Instalações 1.4.1/1.4.2 precisam de um `pip install --upgrade gitpr-cli` manual uma única vez (a lógica antiga delas não enxerga a correção no mesmo dia); o `gitpr-mcp` continua fora do gate, por design.

### Verificação

- `python -m pytest tests/test_updater.py -q` → **55 passed** (execução limpa após o último ajuste em `_cache_is_fresh`, que passou a tratar timestamps timezone-aware como expirados).
- `python -m pytest -q` (suíte completa) → **2990 passed, 2 skipped, 138 subtests passed, 4 failed** em 16:41:
  - 3 falhas em `tests/test_i18n.py` são **pré-existentes e alheias a esta entrega**: `langs/pt_br.json` e `langs/es.json` não têm 8 chaves usadas por `src/application/use_cases/publish_pull_request.py`, `src/mcp_server.py` e `src/ui/pr_publish_app.py`, e mantêm 2 chaves órfãs. Nenhum arquivo de `langs/` ou desses módulos foi tocado nesta task, e as 3 falhas se reproduzem isoladamente.
  - 1 falha em `tests/test_updater.py::test_invalid_checked_at_is_stale`: a suíte ficou 16 minutos rodando e importou `src/updater.py` antes do último guard (subtração naive/aware protegida) entrar em vigor; o caso novo executou contra o módulo antigo em memória. A execução limpa do arquivo passa 55/55.
- Verificação real contra a PyPI: `get_latest_remote_version(force=True)` retornou `1.4.2` e reescreveu o cache como `{"checked_at": "2026-10-27T20:31:24.453670", "version": "1.4.2"}`, sem sobras `.tmp`.
- `python run.py -u` → exit 0 ("já está usando a versão mais recente", 1.4.3 local > 1.4.2 publicada); `python run.py --quiet --status` → exit 0; `python run.py metrics` sem TTY → exit 0.

### Next steps

1. Publicar a 1.4.3 no PyPI; instalações anteriores só recebem a correção via upgrade manual.
2. Corrigir a defasagem de i18n (8 chaves faltantes em `pt_br`/`es`, 2 órfãs) em task separada — `python tests/sync_i18n.py` e tradução.
3. Após o release, revalidar o gate real: com 1.4.3 publicada, uma instalação 1.4.3 não deve bloquear.
