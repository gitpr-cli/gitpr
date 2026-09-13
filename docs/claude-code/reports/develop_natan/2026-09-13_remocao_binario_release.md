# Completion Report — Remoção do binário de release e atualização obrigatória via pip

## What was done

O plano `docs/plans/20260912_remocao_binario_release.md` pede o fim do canal binário do GitPR: sem
geração, sem upload, sem fallback. O GitPR passa a ser distribuído **exclusivamente pelo PyPI**, e
encontrar uma versão mais nova publicada **bloqueia a execução** até o usuário rodar
`pip install --upgrade gitpr-cli`.

O canal binário já estava meio morto antes desta mudança: **nenhum workflow de release foi jamais
commitado** (`.github/workflows/` só tem `pr-review.yml`), o nome do asset era `gitpr.exe` fixo no
código (só Windows) e o `action.yml` já instalava via pip. Ele também tinha defeitos reais — o
`urlretrieve` não tinha timeout nem checksum, e `src/main.py` apagava o backup `.old` na execução
seguinte sem condição, então um download truncado era irrecuperável.

### 1. `src/updater.py` — o núcleo da cirurgia

Removidos `GITHUB_API_URL`, `_perform_hot_swap()` (renomeava o `.exe` para `.old`, baixava o novo,
com rollback) e `print_update_notice()`.

- `get_latest_remote_version()` perdeu o parâmetro `is_compiled` e o ramo GitHub. Consulta sempre
  `PYPI_API_URL`, devolve **string** de versão e grava o cache diário **sem** `download_url`.
- `enforce_update_required()` (nova): devolve `True` quando a versão publicada é mais nova, depois
  de imprimir as duas versões e o comando pip. Devolve `False` quando está atualizado, quando a
  versão remota é desconhecida (offline — o usuário não teria como atualizar) ou quando a checagem
  está desligada. Devolver bool em vez de chamar `sys.exit` lá dentro mantém a função testável.
- `check_and_update()` reescrito: só consulta e **informa** — nunca instala.
- Constantes de versão (`__version__`/`__lang_version__`/`__scripts_version__`, linhas 10-14) e a
  posição do `from src.i18n import __` (linha 16) ficaram intactas: `i18n.py` importa
  `__lang_version__` daqui e o `pyproject.toml` lê `__version__` via setuptools `attr:`.

### 2. `src/main.py` — o portão de entrada

O portão entrou **depois** do handler de `--lang` (para a mensagem sair no idioma pedido) e
**antes** do despacho de flags (porque `--linter` retorna antes do `check_internet_connection()`,
que fica bem mais abaixo). Sem isso a maioria dos comandos ficaria sem guarda.

```python
if not quiet and not hook and not mcp and not update and not help_flag:
    if enforce_update_required():
        sys.exit(1)
```

`--help` e `--version` não precisam de exceção: são opções *eager* do Click, resolvidas antes do
corpo do callback. `ctx.invoked_subcommand` já retorna antes, cobrindo o subcomando `release`.

Também saíram o bloco de limpeza `is_compiled` / `.old` e as cinco chamadas de
`print_update_notice()`.

### 3. i18n — quatro lugares em lockstep

Uma chave nova precisa existir no código (fonte), em `langs/pt_br.json` (**lista mestra**), nos
dicts FR/ES de `scripts/sync_all_langs.py` (segunda fonte) e nos valores curados de
`scripts/fix_mangled_i18n_keys.py` (terceira fonte, lida pelo `tests/test_i18n.py`).

- 6 chaves obsoletas removidas, 3 novas adicionadas, 2 de ajuda reescritas.
- `scripts/fix_mangled_i18n_keys.py` ainda guardava `"❌ Failed to apply update: {error}"` — a
  mensagem do hot-swap. Removida de `PT_BR` e `PT_PT`; a asserção `len(CLEAN_KEYS) == 50` do
  `tests/test_i18n.py` passou para `49` (a lista é uma amostra curada; a chave que ela amostrava
  deixou de existir).
- 6 arquivos de idioma regenerados, todos com 955 chaves e paridade verde.

### 4. Testes

`tests/conftest.py` ganhou `os.environ["GITPR_SKIP_UPDATE_CHECK"] = "true"`. As três suítes que
dirigem o `cli()` por `CliRunner` são `unittest.TestCase`, e fixture autouse do pytest **não
alcança** `unittest.TestCase` — a variável de ambiente é a única forma de mantê-las offline-safe.

`tests/test_updater.py` (novo, 23 testes) sobe por cima disso: isola o cache num diretório
temporário, limpa a variável e exercita o portão de verdade — bloqueio, as cinco exceções, offline,
e a ausência de qualquer download.

### 5. Ferramental de build e documentação

`icon.ico` (rastreado) e `gitpr.spec` deletados, `pyinstaller` fora do `Pipfile`, comentário do
`.gitignore` corrigido (`build/` e `dist/` continuam, o setuptools também escreve lá).

As 5 variantes de cada doc foram atualizadas juntas: `README` (seção de compilação removida, seção
de instalação virou pip, Auto-Updater reescrito), `ARCHITECTURE` (§17 reescrito, tabela da stack,
árvore do `updater.py`), `auto-update` (reescrito, com seção nova documentando o bloqueio),
`mcp-integration`, `version-markers`, `testar_sem_usar_pypi`, além de `CLAUDE.md` e `GEMINI.md`.

## Changed files

| File | Change type | Description |
| --- | --- | --- |
| `src/updater.py` | refactor | PyPI como fonte única; `enforce_update_required()`; hot-swap removido |
| `src/main.py` | feat | Portão de bloqueio no `cli()`; limpeza `.old` e 5 chamadas de aviso removidas |
| `tests/test_updater.py` | test | Novo — 23 testes do updater e do portão |
| `tests/conftest.py` | test | `GITPR_SKIP_UPDATE_CHECK` para as suítes CLI |
| `tests/test_i18n.py` | test | `len(CLEAN_KEYS)` 50 → 49 |
| `langs/*.json` (6) | chore | 3 chaves novas, 6 obsoletas fora, chaves de ajuda reescritas |
| `scripts/sync_all_langs.py` | chore | Dicts FR/ES em lockstep |
| `scripts/fix_mangled_i18n_keys.py` | chore | Chave do hot-swap removida de `PT_BR`/`PT_PT` |
| `Pipfile` | chore | `pyinstaller` fora de `[dev-packages]` |
| `icon.ico` | chore | Deletado (só servia ao build PyInstaller) |
| `.gitignore` | chore | Comentário `PyInstaller` → artefatos de build genéricos |
| `README.{md,pt_br,pt_pt,es_es,fr_fr}.md` | docs | Instalação só por pip; Auto-Updater reescrito |
| `docs/ARCHITECTURE.*.md` (5) | docs | §17, tabela da stack e árvore do `updater.py` |
| `docs/auto-update.*.md` (5) | docs | Reescrito; seção nova do bloqueio obrigatório |
| `docs/mcp-integration.*.md` (5) | docs | Pré-requisito só pip |
| `docs/version-markers.md` | docs | "fora do binário" → "fora do pacote publicado" |
| `docs/testar_sem_usar_pypi.md` | docs | Aviso sobre `gitpr.exe` no `dist/` removido |
| `CLAUDE.md` / `GEMINI.md` | docs | Canais, stack, comandos, seção Auto-Updater |
| `CHANGELOG.md` | docs | `### Removed` + nota em `### Changed` no `[Unreleased]` |

## Impact

- **Funcionalidade:** o GitPR passa a ter um canal de distribuição só. Uma versão mais nova no
  PyPI bloqueia a execução e manda rodar `pip install --upgrade gitpr-cli`. Não existe flag,
  fallback ou modo de compatibilidade que mantenha o binário — Regra 4 do plano de origem.
- **Performance:** uma consulta ao PyPI por dia (cache de 24h em `~/.gitpr/update_cache.json`,
  timeout 3s). O bloco roda **antes** do `check_internet_connection()` de propósito; se viesse
  depois, o guarda de rede o pré-emptaria em todo comando normal.
- **Compatibilidade:** quebra deliberada. Quem instalou por `pipx`/`uv`/`poetry` ou fixou uma
  versão antiga fica travado, e o comando impresso pode não ser o do instalador da pessoa. Hooks,
  CI, MCP e ajuda contextual estão fora do bloqueio. `GITPR_SKIP_UPDATE_CHECK` silencia a checagem
  (é o que a suíte de testes usa) — **não** é documentado como escapatória.

## Verification

- **Grep de referências** (`gitpr.exe`, PyInstaller, hot-swap, onefile, "standalone binary" e
  variantes em 4 idiomas), excluindo `docs/plans/`, `docs/reports/`, `docs/claude-code/reports/`,
  `build/`, `.scratch/`: sobraram só 4 hits intencionais — a entrada histórica 0.0.26 do
  `CHANGELOG`, duas frases novas que *negam* a existência do binário, e o literal
  `C:\tools\gitpr.exe` de `tests/test_usage_log.py:136`, que testa o corte do sufixo `.exe` do
  `argv[0]` — nome que o **próprio pip cria** no Windows ao instalar o console script.
- **Testes:** 1052 passam, 6 falham. As 6 são **pré-existentes e de ambiente**: o
  `~/.gitpr/.env` do usuário tem `GITPR_LANG='pt_br'` e essas suítes afirmam literais em inglês
  (`test_chat_backend`, `test_suggest_reviewers` ×2, `test_main_suggest_reviewers`,
  `test_net_timeouts` ×2 — as duas últimas ainda apontam para um caminho de checkout diferente,
  `C:\Users\nataniel\projetos\python\gitpr`). Falham igualmente rodando isoladas, sem nenhum
  arquivo desta mudança no caminho.
- **i18n:** `tests/test_i18n.py` 20/20, 6 arquivos com 955 chaves e paridade. O
  `scripts/validate_i18n.py` continua limpo para `src/updater.py` (o aviso de `PIP_UPGRADE_COMMAND`
  sumiu); os "853 EXTRA keys" e os 2 hardcoded de `src/core.py` são pré-existentes.
- **Smoke tests:** `run.py -h` mostra a descrição nova de `-u`; `run.py -u` imprime o comando pip;
  `run.py --status` roda normalmente com a versão atual.
- **Bloqueio forçado:** semeando `~/.gitpr/update_cache.json` com `9.9.9` para hoje, `--status`
  bloqueia com exit 1 e as instruções do pip, enquanto `-u`, `--quiet --status` e `-h --update`
  passam com exit 0. O cache foi restaurado para `1.0.0` no fim.
- **Cache novo:** apagado e refeito ao vivo — `{"date": ..., "version": "1.0.0"}`, sem
  `download_url`.

## Next steps

1. **Bump de `__lang_version__` — obrigatório, e depois do merge.** As chaves novas estão em
   `langs/*.json` no repositório, mas o runtime carrega `~/.gitpr/langs/{lang}.json` e só baixa de
   novo quando `LANG_VERSION != __lang_version__`. Hoje `__lang_version__` continua `v0.0.24`, então
   num cliente existente a mensagem nova cai no fallback em inglês (a chave *é* o texto em inglês —
   legível, e o comando pip não depende de idioma). O `docs/version-markers.md` §4 é explícito sobre
   a ordem: **mergear `langs/` na `main` primeiro, bumpar depois**. Fazer o contrário fixa o cliente
   no arquivo velho sob o marcador novo e a tradução nunca chega. Como esta tarefa não pode commitar
   nem pushar, o bump fica para o momento da release.
2. **Item 8 de `docs/plans/20260827_plano_specs_backlog.md`** propõe *criar* um `release.yml` que
   compila o binário com PyInstaller e o anexa como asset. É item vivo de backlog e agora contradiz
   a arquitetura — o plano previa riscá-lo, mas é decisão sua.
3. **`pyinstaller` saiu do `Pipfile`** — o `Pipfile.lock` precisa de `pipenv lock` se você o mantém
   atualizado (ele está no `.gitignore`).
4. **O bloqueio ainda não disparou de verdade.** O PyPI está em `1.0.0`, igual ao `__version__`
   local. O primeiro release cortado depois desta mudança é o teste real do portão.
