# Survey — Update check não detecta um release publicado no mesmo dia

## Contexto da tarefa

Relato do mantenedor: "O gitpr não está verificando uma nova versão ao executar,
ele ainda está na 1.4.1 nos usuários". A 1.4.2 já estava publicada no PyPI, mas
usuários na 1.4.1 continuavam executando o GitPR sem aviso e sem bloqueio.

## Fatos levantados

### Causa raiz (comprovada na máquina do mantenedor)

- `~/.gitpr/update_cache.json` continha
  `{"date": "2026-10-27", "version": "1.4.1"}`, gravado às **07:54 -03**.
- A 1.4.2 foi publicada no PyPI às **10:45 -03** do mesmo dia.
- `src/updater.py:52-60` (antes da correção) aceitava o cache enquanto
  `cache_data.get("date") == today` — ou seja, o valor ficava válido até a
  meia-noite local. Toda execução depois do release comparava
  `parse_version("1.4.1") <= parse_version("1.4.1")` e liberava o comando.
- `src/updater.py:124` (antes) fazia `check_and_update()` (`gitpr -u`) chamar
  `get_latest_remote_version()` **sem** qualquer bypass: o comando manual
  respondia do mesmo cache, contrariando `docs/auto-update.md`, que promete uma
  verificação imediata.

### Buracos adicionais no mesmo caminho

- `src/main.py:679-680`: subcomandos (`gitpr release`, `gitpr fix`,
  `gitpr review-pr`, …) retornavam antes do gate raiz, que ficava em
  `src/main.py:752`.
- `src/updater.py:44-46`: `bool(os.environ.get(SKIP_ENV, "").strip())` lia a
  chave de escape como flag simples — `GITPR_SKIP_UPDATE_CHECK=false` desligava a
  verificação.
- `parse_version()` customizada devolvia `(0, 0, 0)` para sufixos PEP 440
  (`1.4.3rc1`, `1.4.3.post1`), podendo tanto esconder quanto forjar um release.
- `urllib.request.urlopen(..., timeout=3)` não limita a resolução de DNS, que no
  Windows pode travar por minutos; o repositório já tem `src/net.py` com
  `bounded_urlopen()` justamente para isso.

### Restrições e fatos técnicos verificados

- `packaging>=23.0` já é dependência declarada em `pyproject.toml` e já usada em
  `src/domain/policy/policy_compatibility.py` — nenhuma dependência nova.
- `src/net.py` é livre de dependências internas (i18n importa net), então
  `src.updater -> src.net` não cria ciclo.
- Click 8.3.3 limpa `ctx.args` e `ctx._protected_args` **antes** de chamar o
  callback do grupo: `gitpr release -h` chega ao gate indistinguível de
  `gitpr release`. A única fonte confiável é `sys.argv`.
- O helper `_may_ask_the_user(quiet, hook, mcp)` (`src/main.py:63-75`) já
  responde "há terminal dos dois lados e nenhum modo mudo ativo" e é calculado
  uma única vez em `may_ask` (`src/main.py:667`).
- `gitpr badge --readme` é puro: imprime um snippet e não escreve nada — serve de
  sonda para os testes do gate de subcomando.
- `_previous_block()` (`src/release_engine.py:178`) pula a versão-alvo, então
  uma seção `## [1.4.3]` escrita à mão não quebra o âncora do `gitpr release`.
- `tests/conftest.py` define `GITPR_SKIP_UPDATE_CHECK=true`; com o parser
  estrito, `true` continua desligando a verificação — nenhum teste existente
  quebra por causa da mudança.
- `~itpr-cli`/instalação 1.2.0 na máquina do mantenedor: fora do escopo; para
  testar o checkout, usar `python run.py`.

## Rodadas de decisão (grill)

### Rodada 1 — cache, gate, escape e profundidade da correção

- Cache: **TTL corrido de 1 hora**; `-u/--update` **ignora o cache**.
- Gate: **estender aos subcomandos**, com exceções.
- Escape: `GITPR_SKIP_UPDATE_CHECK` com **booleano estrito**.
- Profundidade: **correção completa** (PEP 440, `bounded_urlopen`, escrita
  atômica, guardas de tipo) em vez de patch mínimo.

### Rodada 2 — como detectar interatividade, versão e alcance da documentação

- Subcomandos só com **TTY** (`_may_ask_the_user`); help de subcomando isento.
- **Bump 1.4.3 + seção no CHANGELOG** nesta entrega.
- Documentação nas **5 variantes** (`auto-update.*` e
  `tutorial/install-from-source.*`).

### Rodada 3 — comportamento do caminho antigo por flags

- **Manter a raiz como está**: `gitpr --status`, `gitpr -c` etc. continuam
  bloqueados mesmo sem TTY; só os subcomandos ganharam a isenção não interativa.

## Resultado

Escopo fechado: TTL de 1 h, `-u` sempre online, gate em subcomandos
interativos, parser estrito, PEP 440, fetch limitado por `bounded_urlopen`,
cache atômico, docs nas 5 línguas, bump 1.4.3. O README ("on every run") ficou
fora de escopo por já ser impreciso antes da mudança.
