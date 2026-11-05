# Marcadores de Versão (Recursos OTA)

O GitPR distribui vários recursos **fora** do pacote publicado — traduções, palavras do
spinner, listas de smart-excludes, presets de linter e scripts de Git hooks. Eles residem no
GitHub e são descarregados over the air (OTA) para que possam ser corrigidos sem necessidade
de lançar uma nova release.

Um **Marcador de Versão** (*Version Marker*) é o mecanismo que decide *quando* uma cópia
em cache está desatualizada.

---

## 1. Como funciona o padrão

Cada marcador é uma chave simples no `~/.gitpr/.env` global do utilizador. Regista **qual
a versão do código que descarregou esse recurso pela última vez**:

```dotenv
LANG_VERSION=v0.0.39
SMART_EXCLUDES_VERSION=v0.0.39
THINKING_WORDS_VERSION=v0.0.39
LINTER_PRESETS_VERSION=v0.0.39
SCRIPTS_VERSION=v0.0.4
```

Em tempo de execução, o carregador do recurso compara o marcador com a constante
autoritativa em [`src/updater.py`](../src/updater.py):

```python
needs_update = os.getenv("LINTER_PRESETS_VERSION") != __lang_version__
```

* **Igual** → a cópia local está atualizada; utiliza-a sem chamada de rede.
* **Diferente ou ausente** → descarrega o template remoto, sobrescreve a cópia local e
  grava o marcador novamente com `set_key(...)`.

Como o marcador só é gravado **após** um descarregamento bem-sucedido, uma falha na
obtenção deixa-o desatualizado e a execução seguinte volta a tentar. Cada carregador
mantém também uma cadeia de fallback offline, pelo que uma falha de descarregamento
degrada para a cópia anterior em vez de interromper o comando.

> Os marcadores **não** são inicializados em `DEFAULT_CONFIG` no `src/config.py`. São
> gravados a pedido pelo carregador responsável por eles. Um marcador ausente significa
> simplesmente "nunca descarregado", o que aciona corretamente a primeira obtenção.

---

## 2. Os marcadores

| Marcador | Recurso | Cache local | Comparado com | Responsável |
| --- | --- | --- | --- | --- |
| `LANG_VERSION` | Dicionários de tradução | `~/.gitpr/langs/{lang}.json` | `__lang_version__` | [`src/i18n.py`](../src/i18n.py) |
| `SMART_EXCLUDES_VERSION` | Exclusões de pathspec do diff | `~/.gitpr/conf/gitpr.smart-excludes.json` | `__lang_version__` | [`src/core.py`](../src/core.py) |
| `THINKING_WORDS_VERSION` | Palavras de pensamento do spinner | `~/.gitpr/.env` (`SPINNER_THINKING_WORDS`) | `__lang_version__` | [`src/spinner.py`](../src/spinner.py) |
| `LINTER_PRESETS_VERSION` | Presets de linters externos | `~/.gitpr/conf/gitpr.linter-presets.json` | `__lang_version__` | [`src/linter_wizard.py`](../src/linter_wizard.py) |
| `SCRIPTS_VERSION` | Scripts de Git hooks | `.git/hooks/` | `__scripts_version__` | [`src/core.py`](../src/core.py) |

Quatro dos cinco são comparados com `__lang_version__`, pelo que um único incremento
atualiza-os em bloco. Os scripts de hooks são versionados de forma independente por
`__scripts_version__` porque mudam numa cadência diferente.

---

## 3. `LINTER_PRESETS_VERSION`

Rastreia [`templates/gitpr.linter-presets.json`](../templates/gitpr.linter-presets.json),
o catálogo de definições prontas de linters externos oferecido pelo `gitpr --linter-setup`
(pontes compatíveis com Checkstyle: ESLint, PHPCS, Checkstyle, entre outros).

O seu objetivo é permitir que **novos linters cheguem às instalações existentes sem uma nova release**.
Adicionar um preset ao template é suficiente — o próximo `--linter-setup` num cliente cujo
marcador esteja desatualizado volta a descarregar o catálogo.

Cadeia de resolução em `_load_linter_presets()`:

1. Cópia local em `~/.gitpr/conf/gitpr.linter-presets.json`, quando
   `LINTER_PRESETS_VERSION == __lang_version__`.
2. Novo descarregamento a partir do template remoto — cópia local gravada, marcador atualizado.
3. Cópia local desatualizada, quando o descarregamento falha (offline).
4. Constante integrada `_LINTER_PRESETS`, como último recurso.

> **Não confundir com a versão de release do GitPR.** `__version__` (`1.5.0`)
> identifica o próprio CLI; `LINTER_PRESETS_VERSION` regista apenas qual o snapshot do
> catálogo de presets que está em cache localmente. Os dois evoluem de forma independente.

---

## 4. Incrementar um marcador

Os marcadores no `.env` são gravados pelo GitPR — **nunca os edite manualmente**. O que se
altera é a constante em [`src/updater.py`](../src/updater.py) com a qual são comparados:

```python
__lang_version__ = "v0.0.39"     # traduções, smart excludes, thinking words, linter presets
__scripts_version__ = "v0.0.4"   # scripts de Git hooks
```

Para publicar uma alteração em qualquer recurso controlado por `__lang_version__`:

1. **Faça primeiro o merge da alteração do template na `main`.** Os clientes obtêm de
   `raw.githubusercontent.com/natanfiuza/gitpr/main/...`, pelo que o novo conteúdo já
   tem de lá estar.
2. **Depois** incremente `__lang_version__` e lance a release.

Fazê-lo pela ordem inversa fixa os clientes ao ficheiro *antigo* sob o marcador *novo*:
descarregam o que a `main` estiver a servir no momento, carimbam a nova versão e nunca
voltam a tentar — a correção silenciosamente nunca chega.

### Checklist

- [ ] Template atualizado e integrado na `main`
- [ ] `__lang_version__` (ou `__scripts_version__`) incrementado em `src/updater.py`
- [ ] Alteração verificada num cliente com marcador desatualizado
- [ ] Paridade de `langs/*.json` continua verde (`pytest tests/test_i18n.py`)

---

## 5. Relacionados

* [ARCHITECTURE.pt_pt.md](ARCHITECTURE.pt_pt.md) — §16 Marcadores de Versão
* [hooks-versioning.pt_pt.md](hooks-versioning.pt_pt.md) — especificidades de `SCRIPTS_VERSION`
* [linter-regras-customizadas.pt_pt.md](linter-regras-customizadas.pt_pt.md) — presets de linter e `--linter-setup`
