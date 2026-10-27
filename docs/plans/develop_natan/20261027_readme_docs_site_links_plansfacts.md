# Plano — Trocar os links de documentação do README para o site

## Contexto

Os 5 READMEs da raiz apontavam a documentação para arquivos crus no GitHub
(`https://github.com/gitpr-cli/gitpr.git/blob/main/docs/*.md`). O projeto já
publica a mesma documentação em `https://gitpr.natanfiuza.dev.br/docs/{nome}`,
com o idioma por `?lang=` — formato canonizado no próprio código, em
`src/doc_links.py` (`DOCS_BASE_URL` + `doc_url()`), que documenta exatamente:
inglês sem parâmetro, demais idiomas com `?lang=`.

Objetivo: reescrever os links de documentação dos 5 READMEs para o site, levando
o idioma de cada arquivo no `?lang=`. Nenhuma mudança de código.

## Decisões (grilling)

| # | Decisão |
|---|---|
| Q1 | Só links de documentação. Repositório, `git clone`, `templates/*.json` e o logo continuam no GitHub — o site devolve 404 para `/templates/*.json` e `/logo.png`. |
| Q2 | Todo link de doc de um README de idioma recebe aquele `?lang=`, e o sufixo `.pt_br`/`.pt_pt`/`.es_es`/`.fr_fr` sai do caminho. |
| Q3 | `?lang=es_es` e `?lang=fr_fr` são aplicados mesmo com o fallback em inglês hoje: ficam corretos e prontos para quando as traduções forem publicadas. |
| Q4 | Escopo: apenas os 5 READMEs da raiz. `CHANGELOG.md`, `docs/**` e `templates/**` ficam fora. |
| Q5/Q6 | Rótulo visível trocado apenas nos 45 links cujo texto é um caminho (`[docs/xxx.md]`). Os 288 rótulos descritivos (`Full docs`, `**AI Code Review**`, `MCP Prompts guide`) permanecem. |
| Q7 | Rótulo sem protocolo: `gitpr.natanfiuza.dev.br/docs/{nome}` — mesmo estilo já usado na linha 14 do README. |
| Q8 | O `?lang=` não aparece no rótulo visível, só no destino do link. |
| Q9 | Links **relativos** de doc (`[x](docs/...)`), descobertos depois: converter os 9 cujo destino existe no site (auto-update ×5 + 4 do pt_br); os 5 do `docs/tutorial/install-from-source.*` ficam relativos porque a página dá 404 no site. Os rótulos `[auto-update.md]` acompanham o destino. |
| Q10 | Cada README já tinha **5 links apontando para o site** antes da tarefa. Preservados. Em `README.md`, os 4 que traziam `?lang=en_us` (`demo` ×2, `install-wizard` ×2) tiveram o parâmetro removido — a regra é "inglês sem `lang`" —, em 2 linhas, sem tocar no destino de idioma dos demais arquivos. |

## Regras de transformação

**Regra A — destino do link**

```
https://github.com/gitpr-cli/gitpr.git/blob/main/docs/{nome}.md
→ https://gitpr.natanfiuza.dev.br/docs/{nome}[?lang={idioma}]
```

- `{nome}` perde o sufixo de idioma (`.pt_br|.pt_pt|.es_es|.fr_fr`).
- `README.md` → inglês → sem `?lang=`; os demais usam o próprio idioma do arquivo.
- Regex: `https://github\.com/gitpr-cli/gitpr\.git/blob/main/docs/([A-Za-z0-9_.\-]+?)\.md`

**Regra B — rótulo do link**

```
[docs/{nome}.md] → [gitpr.natanfiuza.dev.br/docs/{nome}]
```

- Regex: `\[docs/([A-Za-z0-9_.\-]+?)\.md\]`
- Sem backticks nos rótulos, sem `.md` no resultado, sem `?lang=`.

**Não tocar (por arquivo):** 1 comando `git clone`, 2 links `templates/*.json`,
o link `📂 Repository:` da linha 14 (2 ocorrências na linha), 1 logo em
`raw.githubusercontent.com`, e o rótulo `[extensions/vscode/]`.

## Arquivos e volumes

| Arquivo | URLs reescritas | Rótulos reescritos |
|---|---|---|
| README.md | 69 | 9 |
| README.pt_br.md | 64 | 9 |
| README.pt_pt.md | 67 | 9 |
| README.es_es.md | 67 | 9 |
| README.fr_fr.md | 66 | 9 |
| **Total** | **333** | **45** |

Depois da Q9, mais **9 destinos relativos** foram convertidos (auto-update ×5 +
4 do `pt_br`) e **5 rótulos** `[auto-update.md]` passaram a exibir o endereço do
site: total de **342 destinos** e **50 rótulos** convertidos.

Somados aos **25** links de site que os READMEs já traziam (5 por arquivo), o
estado final tem **367** destinos para o site — 75/74/73/73/72 por arquivo.

## Procedimento

1. Aplicar as Regras A e B nos 5 arquivos com um script Python pontual, em
   `encoding='utf-8'`/`errors='replace'` e `newline=''` (os arquivos são CRLF).
   O script não é salvo no repositório.
2. Conferir as contagens por arquivo: `leftover_urls=0`, `leftover_labels=0`,
   `templates=2`, `clone=1`, `logo=1`.
3. Revisar o diff (`git diff --stat` e amostras por arquivo).

## Verificação

- [x] `blob/main/docs/` ausente nos 5 READMEs
- [x] Nenhum rótulo `[docs/*.md]` remanescente
- [x] As 217 URLs únicas geradas retornam 200 — `checked=217, failures=0`
      (a lista precisa ser gravada com `newline='\n'`: uma lista em CRLF faz o
      `curl` devolver `000` com URL inválida, o que foi confundido com rate limit)
- [x] Nenhum `?lang=en_us` remanescente; cada arquivo só usa o próprio idioma
- [x] Line endings CRLF preservados (612/610/607/607/608), sem BOM
- [x] Templates, clone, repositório e logo intactos
- [x] Nenhum teste automatizado a rodar — mudança exclusivamente em Markdown

## Entregáveis

- 5 READMEs da raiz alterados (sem commit — regra do `CLAUDE.md`)
- `docs/plans/develop_natan/20261027_readme_docs_site_links_plansfacts.md` — este plano
- `docs/survey/20261027_readme_docs_site_links_surveyfacts.md` — levantamento e decisões
- `docs/claude-code/reports/develop_natan/2026-10-27_readme_docs_site_links.md` — relatório de conclusão
