---
name: docs-multilingue-convencao
description: Convenção de documentação multilíngue com inglês como base canônica e localizações por sufixo de idioma
metadata:
  type: reference
  source: docs/gemini/reports/develop_natan/2026-08-03_translate_github_ci_linter_docs.md
  date: 2026-08-03
  branch: develop_natan
---

A documentação do GitPR segue uma convenção de nomenclatura consistente para
múltiplos idiomas. O inglês é a base canônica e cada localização usa o sufixo
de código de idioma no nome do arquivo:

```
docs/<nome-base>.md              # Inglês (canônico)
docs/<nome-base>.<lang>.md       # Localização
```

Onde `<lang>` segue os códigos usados pelo projeto: `pt_br` (Português Brasil),
`pt_pt` (Português Portugal), `es_es` (Espanhol), `fr_fr` (Francês). A função
`get_doc_url()` em `src/core.py` resolve a URL correta baseada no idioma ativo
do usuário (detectado via OS ou `GITPR_LANG`).

Regras de conteúdo nas traduções:
- Blocos de código, nomes de variáveis de ambiente, endpoints e comandos
  permanecem em inglês (não são traduzidos)
- Texto explicativo, descrições e instruções são totalmente localizados
- O arquivo canônico em inglês é a referência primária para atualizações
- Toda nova documentação deve nascer com pelo menos o arquivo `.md` (EN) e
  `.pt_br.md`; demais idiomas podem seguir depois

Documentos que seguem esta convenção: `github-ci-linter`, `guia-regex-gitpr`,
`gitpr-issue-option`, `smart-excludes`, `mcp-integration`, `mcp-annotations`,
`mcp-prompts`, entre outros.

**Why:** A padronização do formato `<base>.<lang>.md` permite que `get_doc_url()`
resolva documentação dinamicamente sem um registro centralizado de arquivos.
O inglês como base canônica garante que sempre existe uma versão de referência
completa, mesmo que uma localização esteja desatualizada.

**How to apply:**
1. Nova documentação: criar `<nome>.md` em inglês + `<nome>.pt_br.md` no mínimo
2. Blocos de código e comandos NUNCA são traduzidos
3. Usar `get_doc_url()` para gerar links de documentação — nunca hardcodar URLs
4. Ao adicionar uma nova localização, seguir o padrão de nomenclatura existente
5. Documentação referenciada no help contextual usa URLs resolvidas por idioma
