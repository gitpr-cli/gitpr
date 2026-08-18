# Internacionalização (i18n) no GitPR — Guia do Desenvolvedor

## Visão Geral

O GitPR utiliza um motor de internacionalização (i18n) personalizado inspirado no **helper `__()` do Laravel**. Todas as strings exibidas ao usuário são escritas em **inglês** como chaves, e as traduções são carregadas de arquivos JSON em tempo de execução. O sistema detecta automaticamente o idioma do sistema operativo e usa o inglês como fallback quando não há tradução disponível.

---

## Arquitetura

### Ficheiros principais

| Ficheiro | Finalidade |
|---|---|
| `src/i18n.py` | Motor de tradução: função `__()`, detecção de idioma, carregamento de JSON |
| `src/updater.py` | Define `__lang_version__` — controla a invalidação do cache de traduções |
| `langs/pt_br.json` | Traduções para português (Brasil) — pares chave-valor (EN → PT-BR) |
| `~/.gitpr/langs/{lang_code}.json` | Cache local de traduções do usuário (baixado na primeira execução) |
| `~/.gitpr/.env` | Armazena `GITPR_LANG` (forçar idioma) e `LANG_VERSION` (versão do cache) |

### Como funciona

```
1. i18n.py carrega no momento da importação do módulo
2. get_system_language() detecta o locale do SO (ex: pt_BR, es_ES) ou lê GITPR_LANG do .env
3. get_translations() carrega o arquivo JSON de ~/.gitpr/langs/{lang}.json
   - Se o arquivo não existe ou está desatualizado (LANG_VERSION != __lang_version__) → baixa do GitHub
   - Se o idioma for inglês → retorna dicionário vazio (não precisa de tradução)
   - Se o download falhar e existir arquivo local → usa a versão em cache
4. O dicionário TRANSLATIONS é mantido em memória durante a sessão
5. Função __(): procura a chave → retorna a tradução (ou a própria chave como fallback)
```

### A função `__()`

```python
def __(key, **kwargs):
    """
    Motor de Tradução inspirado no Laravel.
    Tenta encontrar a chave no dicionário. Se não achar, retorna a própria chave (inglês).
    """
    text = TRANSLATIONS.get(key, key)
    if kwargs:
        try:
            text = text.format(**kwargs)
        except KeyError:
            pass
    return text
```

**Características principais:**
- **Chave = fallback em inglês** — se não existir tradução, a string em inglês é exibida diretamente
- **Placeholders nomeados** — suporta `str.format()` do Python com argumentos nomeados
- **Formatação segura** — se um placeholder estiver faltando, silenciosamente usa a string original

---

## Como usar `__()` no código

### Uso básico (strings estáticas)

```python
from src.i18n import __

# Antes (inglês hardcoded):
click.secho("✅ File saved successfully!", fg="green")

# Depois (i18n-ready):
click.secho(__("✅ File saved successfully!"), fg="green")
```

### Com placeholders (valores dinâmicos)

```python
# Placeholder único
click.echo(__("Downloading {file_name}...", file_name="template.md"))

# Múltiplos placeholders
click.secho(__("🤖 GitPR is analyzing your code using {provider} ({model})...",
               provider="Gemini", model="gemini-pro-latest"), fg="cyan")
```

### Em decorators do Click

```python
@click.option('-c', '--commit', is_flag=True,
              help=__("Generates only the commit message and displays it in the console."))
```

### Em atributos de classe (cuidado com a ordem de importação)

```python
class IssueApp(App):
    TITLE = __("GitPR - Issue Generator")  # Funciona! __() executa no momento da definição da classe
```

### Em componentes Textual TUI

```python
BINDINGS = [
    Binding("f2", "save_local", __("Save Local")),
    Binding("f3", "create_issue", __("Create on GitHub")),
]
```

### Para comparações de strings (respostas da IA, chaves de cache)

**⚠️ Importante:** Nunca uses `__()` para comparações de strings! A função retorna o valor traduzido (ex: português), o que quebraria as comparações. Em vez disso, usa uma lista de variações possíveis em ambos os idiomas:

```python
# CORRETO — verifica múltiplas variações de idioma
_no_commits = [
    "No exclusive commits",
    "No exclusive commits found",
    "Nenhum commit exclusivo",
    "Nenhum commit exclusivo encontrado",
]
_no_commits_found = any(phrase in context_text for phrase in _no_commits)
```

---

## Como adicionar traduções

### 1. Adiciona a chave de tradução ao `langs/pt_br.json`

```json
{
    "✅ File saved successfully!": "✅ Arquivo salvo com sucesso!",
    "Downloading {file_name}...": "A baixar {file_name}..."
}
```

A chave é a **string exata em inglês** usada no código. O valor é a tradução em português.

### 2. Os placeholders devem corresponder

Se a chave em inglês tem `{file_name}`, a tradução em português também deve usar `{file_name}`:

```json
{
    "Downloading {file_name}...": "A baixar {file_name}..."
}
```

### 3. Sem chaves duplicadas

JSON não suporta chaves duplicadas. Usa o script de verificação:

```bash
python -c "
import json, re
from collections import Counter
with open('langs/pt_br.json', 'r') as f: content = f.read()
keys = []
for i, line in enumerate(content.splitlines(), 1):
    m = re.match(r'^\s*\"(.+?)\"\s*:', line)
    if m: keys.append((m.group(1), i))
dupes = {k: v for k, v in Counter(k for k, _ in keys).items() if v > 1}
print(f'Duplicates: {dupes}' if dupes else 'No duplicates!')
"
```

---

## Como adicionar um novo idioma

1. Cria o arquivo JSON: `langs/{lang_code}.json` (ex: `langs/es_ES.json`)
2. Adiciona todos os pares chave-valor com chaves em inglês e valores traduzidos
3. Faz commit do arquivo — será servido de `https://raw.githubusercontent.com/natanfiuza/gitpr/main/langs/`
4. O motor i18n baixa-o automaticamente na primeira utilização para esse locale

---

## Prioridade de detecção de idioma

1. **`.env` `GITPR_LANG`** — se definido, força um idioma específico (ex: `GITPR_LANG=pt_br`)
2. **Locale do SO** — detectado automaticamente via `locale.getdefaultlocale()` (ex: `pt_BR`, `es_ES`)
3. **Fallback** — `"en_us"` (inglês, não precisa de arquivo de tradução)

Para forçar inglês: define `GITPR_LANG=en` no `~/.gitpr/.env` ou remove a variável.

---

## Controle de versão das traduções

- `__lang_version__` no `src/updater.py` é incrementado quando as traduções mudam
- Em cada execução, se o `LANG_VERSION` local != `__lang_version__`, o arquivo de tradução é re-baixado
- Isto garante que os usuárioes têm sempre as traduções mais recentes sem atualizações manuais

---

## Precauções com importações circulares

O módulo i18n importa `__lang_version__` do `updater.py`. Portanto:

- **`updater.py`** NÃO deve importar `__` no topo — usa lazy imports dentro das funções
- **`cache.py`** NÃO deve importar `__` no topo — usa lazy imports dentro das funções que precisam
- Outros módulos podem importar `__` no topo com segurança

```python
# NÃO faça isto no updater.py ou cache.py:
from src.i18n import __

# FAZ isto em vez disso (dentro da função que precisa):
def some_function():
    from src.i18n import __  # lazy import
    click.secho(__("message"))
```

---

## i18n nas URLs de documentação

A função `get_doc_url()` no `core.py` constrói URLs de documentação com sufixo de idioma:

```python
from src.i18n import CURRENT_LANG

def get_doc_url(filename):
    if CURRENT_LANG.startswith("en"):
        return f"https://github.com/.../docs/{filename}"
    else:
        base, ext = filename.rsplit(".", 1)
        return f"https://github.com/.../docs/{base}.{CURRENT_LANG}.{ext}"

# Uso:
get_doc_url("issue-tui-help.md")
# EN → "https://github.com/.../docs/issue-tui-help.md"
# PT → "https://github.com/.../docs/issue-tui-help.pt_br.md"
```

---

## Checklist resumo para novas funcionalidades

Ao adicionar novo texto exibido ao usuário:

- [ ] Usar `__("English text here")` para TODAS as chamadas click.secho, click.echo, click.prompt
- [ ] Adicionar o par inglês→português ao `langs/pt_br.json`
- [ ] Usar formato `{placeholder}` com argumentos nomeados (nunca f-strings dentro de `__()`)
- [ ] Para comparações de strings, usar listas de variações em múltiplos idiomas (não `__()`)
- [ ] Garantir que `updater.py` e `cache.py` usam lazy imports de `__`
- [ ] Testar com `GITPR_LANG=pt_br` e `GITPR_LANG=en` para verificar ambos os idiomas
- [ ] Incrementar `__lang_version__` no `updater.py` se as traduções mudarem significativamente
