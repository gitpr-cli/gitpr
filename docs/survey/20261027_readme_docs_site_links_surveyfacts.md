# Survey — Links de documentação do README para o site oficial

**Data:** 2026-10-27 · **Branch:** `develop_natan`
**Pedido:** no `README.md`, trocar os endereços do GitHub pelos do site
(`https://gitpr.natanfiuza.dev.br`), com o idioma no `?lang=` (inglês sem
parâmetro), aplicando o mesmo critério nos demais READMEs de idioma.

## Contexto da tarefa

Os 5 READMEs da raiz apontavam a documentação para arquivos crus no GitHub:

```
https://github.com/gitpr-cli/gitpr.git/blob/main/docs/{nome}.md
```

O projeto já publica a mesma documentação no site, e o formato de URL **já está
canonizado no código**, em `src/doc_links.py`:

```python
DOCS_BASE_URL = "https://gitpr.natanfiuza.dev.br/docs/"

def doc_url(filename):
    base, _ = filename.rsplit(".", 1)
    url = f"{DOCS_BASE_URL}{base}"
    if not CURRENT_LANG.startswith("en"):
        url += f"?lang={CURRENT_LANG}"
    return url
```

Ou seja: o pedido alinha os READMEs ao formato que a CLI já usa ao imprimir
links de documentação — inglês sem parâmetro, demais idiomas com `?lang=`.

## Decisões (grilling, por rodada)

### Rodada 1

| # | Pergunta | Resposta |
|---|---|---|
| Q1 | Reescrever só links de doc, ou também repositório/clone/templates? | **Só links de doc.** Repositório, `git clone`, `templates/*.json` e logo ficam no GitHub. |
| Q2 | Links para `.md` sem tradução em README de idioma: recebem `?lang=`? | **Sim, uniforme.** Todo link de doc de um README de idioma recebe aquele `?lang=`; o sufixo de idioma sai do caminho. |
| Q3 | ES/FR ainda não publicados no site: aplicar mesmo assim? | **Aplicar.** O fallback é o mesmo conteúdo que o link do GitHub entrega hoje. |
| Q4 | Escopo de arquivos. | **Só os 5 READMEs da raiz.** `CHANGELOG.md`, `docs/**` e `templates/**` ficam fora. |

### Rodada 2

| # | Pergunta | Resposta |
|---|---|---|
| Q5/Q6 | Trocar o rótulo visível de todos os 333 links ou só dos que são caminho? | **Só os 45 rótulos de caminho** (`[docs/xxx.md]`). Os 288 rótulos descritivos permanecem. |
| Q7 | Rótulo com ou sem protocolo? | **Sem protocolo:** `gitpr.natanfiuza.dev.br/docs/{nome}` (estilo da linha 14). |
| Q8 | `?lang=` no rótulo visível? | **Não** — só no destino. |

### Rodada 3 (achados posteriores)

| # | Pergunta | Resposta |
|---|---|---|
| Q9 | Links **relativos** de doc (`[x](docs/...)`), que o inventário inicial só de URLs do GitHub não pegou: converter? | **Converter os 9 cujo destino existe no site** (auto-update ×5 + 4 do `pt_br`). Os 5 de `docs/tutorial/install-from-source.*` ficam relativos — a página não existe no site. |
| Q10 | Links de site **pré-existentes** com `?lang=en_us` no `README.md`: normalizar? | **Sim** — a regra é inglês sem `lang`. Removido o parâmetro das 4 ocorrências (`demo` ×2, `install-wizard` ×2), em 2 linhas. |

## Fatos levantados

### Inventário dos READMEs

| Arquivo | Links de doc | Rótulos de caminho | `templates/*.json` | `git clone` | Logo | Link "Repository" |
|---|---|---|---|---|---|---|
| README.md | 69 | 9 | 2 | 1 | 1 | 2 ocorrências (linha 14) |
| README.pt_br.md | 64 | 9 | 2 | 1 | 1 | 2 ocorrências (linha 14) |
| README.pt_pt.md | 67 | 9 | 2 | 1 | 1 | 2 ocorrências (linha 14) |
| README.es_es.md | 67 | 9 | 2 | 1 | 1 | 2 ocorrências (linha 14) |
| README.fr_fr.md | 66 | 9 | 2 | 1 | 1 | 2 ocorrências (linha 14) |
| **Total** | **333** | **45** | 10 | 5 | 5 | 10 |

Outras verificações de forma:

- Nenhum link de doc tem `#âncora` ou query string.
- Nenhum link de doc vem em `<a href="...">` HTML — todos são Markdown.
- Nenhum rótulo `[docs/...]` está entre backticks.
- Únicos links GitHub fora de `docs/`: os 2 de `templates/*.json`, o `git clone`,
  o link "Repository" e o logo em `raw.githubusercontent.com`.

### Site (`gitpr.natanfiuza.dev.br`), verificado em 2026-10-27

| Verificação | Resultado |
|---|---|
| As **44** páginas de doc distintas referenciadas | **200** em todas |
| `/docs/{nome}?lang=pt_br` | conteúdo **PT-BR** |
| `/docs/{nome}?lang=pt_pt` | conteúdo **PT-PT** (redação distinta do PT-BR) |
| `/docs/{nome}?lang=es_es` | **fallback em inglês** (tradução ainda não publicada) |
| `/docs/{nome}?lang=fr_fr` | **fallback em inglês** |
| `/docs/{nome}?lang=xx_yy` (idioma inexistente) | fallback em inglês, **200** (não 404) |
| `/docs` (índice) | 404 |
| `/logo.png` | **404** |
| `/templates/gitpr.smart-excludes.json` | **404** |
| `/templates/gitpr.docs-smart-excludes.json` | **404** |

Consequência direta para Q1: templates e logo **não** podem migrar para o site.

### Links que já apontavam para o site

Cada README já trazia **5** links de documentação no domínio do site antes da
tarefa — **25 no total**, todos preservados (1 `hooks-versioning` + 4 de `demo`
e `install-wizard`). Eles explicam a diferença entre os **342** destinos
convertidos e os **367** destinos de site no estado final:

| Arquivo | Destinos de site no estado final |
|---|---|
| README.md | 75 |
| README.pt_br.md | 74 |
| README.pt_pt.md | 73 |
| README.es_es.md | 73 |
| README.fr_fr.md | 72 |
| **Total** | **367** = 342 convertidos + 25 pré-existentes |

Em `README.md`, os 4 links pré-existentes que traziam `?lang=en_us` perderam o
parâmetro (Q10) — as URLs são equivalentes, o site serve inglês com ou sem
`lang`.

### Encoding e fim de linha

Todos os 5 READMEs são **CRLF**, sem BOM. A reescrita preservou `newline=''` na
leitura e na escrita, mantendo as contagens de CRLF idênticas (612/610/607/607/608).

### Falso alarme de rate limit (CRLF na lista de URLs)

As primeiras varreduras retornavam `curl` código `000` em **todas** as URLs,
enquanto uma requisição isolada respondia 200 — o que sugeria bloqueio de taxa do
host. A causa real era outra: a lista de URLs foi gerada por `print()` do Python
no Windows, cujo stdout em modo texto traduz `\n` para `\r\n`. Cada linha lida
com `read -r` carregava um `\r` final, e o `curl` trata a URL resultante como
inválida, devolvendo `000`.

Correção: gravar a lista com `newline='\n'` (ou `tr -d '\r'`). Com a lista limpa,
as mesmas URLs respondem 200. **Não houve bloqueio do site em momento algum** — o
defeito estava no harness de verificação, não nos links.

Lição para próximas varreduras: no Windows, qualquer lista consumida por `curl`
em loop precisa ser escrita com `newline='\n'`.

## Regra final aplicada

**Destino**

```
https://github.com/gitpr-cli/gitpr.git/blob/main/docs/{nome}.md
→ https://gitpr.natanfiuza.dev.br/docs/{nome}[?lang={idioma}]
```

**Rótulo (só quando o texto é `docs/{nome}.md`)**

```
[docs/{nome}.md] → [gitpr.natanfiuza.dev.br/docs/{nome}]
```

**Não alterado:** `📂 Repository:`, `git clone`, `templates/*.json`, logo em
`raw.githubusercontent.com`, rótulo `[extensions/vscode/]` e todos os rótulos
descritivos.
