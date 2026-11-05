# Marcadores de Versão (Recursos OTA)

O GitPR distribui vários recursos **fora** do pacote publicado — traduções, palavras do
spinner, listas de smart-excludes, presets de linter e scripts de Git hooks. Eles vivem no
GitHub e são baixados over the air (OTA) para que possam ser corrigidos sem precisar
publicar uma nova release.

Um **Marcador de Versão** (*Version Marker*) é o mecanismo que decide *quando* uma cópia
em cache está desatualizada.

---

## 1. Como o padrão funciona

Cada marcador é uma chave simples no `~/.gitpr/.env` global do usuário. Ele registra **qual
versão do código baixou aquele recurso pela última vez**:

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

* **Igual** → a cópia local está atualizada; usa-a sem chamada de rede.
* **Diferente ou ausente** → baixa o template remoto, sobrescreve a cópia local e grava
  o marcador de volta com `set_key(...)`.

Como o marcador só é gravado **após** um download bem-sucedido, uma falha na busca deixa
o marcador desatualizado e a próxima execução tenta novamente. Todo carregador também
mantém uma cadeia de fallback offline, de modo que uma falha de download degrada para a
cópia anterior em vez de quebrar o comando.

> Os marcadores **não** são semeados em `DEFAULT_CONFIG` no `src/config.py`. Eles são
> gravados sob demanda pelo carregador responsável por eles. Um marcador ausente significa
> simplesmente "nunca baixado", o que aciona corretamente a primeira busca.

---

## 2. Os marcadores

| Marcador | Recurso | Cache local | Comparado com | Responsável |
| --- | --- | --- | --- | --- |
| `LANG_VERSION` | Dicionários de tradução | `~/.gitpr/langs/{lang}.json` | `__lang_version__` | [`src/i18n.py`](../src/i18n.py) |
| `SMART_EXCLUDES_VERSION` | Exclusões de pathspec do diff | `~/.gitpr/conf/gitpr.smart-excludes.json` | `__lang_version__` | [`src/core.py`](../src/core.py) |
| `THINKING_WORDS_VERSION` | Palavras de pensamento do spinner | `~/.gitpr/.env` (`SPINNER_THINKING_WORDS`) | `__lang_version__` | [`src/spinner.py`](../src/spinner.py) |
| `LINTER_PRESETS_VERSION` | Presets de linters externos | `~/.gitpr/conf/gitpr.linter-presets.json` | `__lang_version__` | [`src/linter_wizard.py`](../src/linter_wizard.py) |
| `SCRIPTS_VERSION` | Scripts de Git hooks | `.git/hooks/` | `__scripts_version__` | [`src/core.py`](../src/core.py) |

Quatro dos cinco são comparados com `__lang_version__`, de modo que um único incremento
atualiza todos em bloco. Os scripts de hooks são versionados de forma independente por
`__scripts_version__` porque mudam em uma cadência diferente.

---

## 3. `LINTER_PRESETS_VERSION`

Rastreia [`templates/gitpr.linter-presets.json`](../templates/gitpr.linter-presets.json),
o catálogo de definições prontas de linters externos oferecido pelo `gitpr --linter-setup`
(pontes compatíveis com Checkstyle: ESLint, PHPCS, Checkstyle e assim por diante).

Seu objetivo é permitir que **novos linters cheguem às instalações existentes sem uma nova release**.
Adicionar um preset ao template é suficiente — o próximo `--linter-setup` em um cliente cujo
marcador esteja desatualizado baixa o catálogo novamente.

Cadeia de resolução em `_load_linter_presets()`:

1. Cópia local em `~/.gitpr/conf/gitpr.linter-presets.json`, quando
   `LINTER_PRESETS_VERSION == __lang_version__`.
2. Novo download a partir do template remoto — cópia local gravada, marcador atualizado.
3. Cópia local desatualizada, quando o download falha (offline).
4. Constante embutida `_LINTER_PRESETS`, como último recurso.

> **Não confunda com a versão de release do GitPR.** `__version__` (`1.5.0`)
> identifica o próprio CLI; `LINTER_PRESETS_VERSION` registra apenas qual snapshot do
> catálogo de presets está em cache localmente. Os dois evoluem de forma independente.

---

## 4. Incrementando um marcador

Os marcadores no `.env` são gravados pelo GitPR — **nunca os edite manualmente**. O que você
altera é a constante em [`src/updater.py`](../src/updater.py) com a qual eles são comparados:

```python
__lang_version__ = "v0.0.39"     # traduções, smart excludes, thinking words, linter presets
__scripts_version__ = "v0.0.4"   # scripts de Git hooks
```

Para publicar uma alteração em qualquer recurso controlado por `__lang_version__`:

1. **Faça o merge da alteração do template na `main` primeiro.** Os clientes buscam de
   `raw.githubusercontent.com/natanfiuza/gitpr/main/...`, portanto o novo conteúdo já
   precisa estar lá.
2. **Depois** incremente `__lang_version__` e publique a release.

Fazer na ordem inversa prende os clientes ao arquivo *antigo* sob o marcador *novo*:
eles baixam o que a `main` estiver servindo no momento, gravam a nova versão e nunca
tentam novamente — a correção silenciosamente nunca chega.

### Checklist

- [ ] Template atualizado e mergeado na `main`
- [ ] `__lang_version__` (ou `__scripts_version__`) incrementado em `src/updater.py`
- [ ] Alteração verificada em um cliente com marcador desatualizado
- [ ] Paridade de `langs/*.json` continua verde (`pytest tests/test_i18n.py`)

---

## 5. Relacionados

* [ARCHITECTURE.pt_br.md](ARCHITECTURE.pt_br.md) — §16 Marcadores de Versão
* [hooks-versioning.pt_br.md](hooks-versioning.pt_br.md) — detalhes de `SCRIPTS_VERSION`
* [linter-regras-customizadas.pt_br.md](linter-regras-customizadas.pt_br.md) — presets de linter e `--linter-setup`
