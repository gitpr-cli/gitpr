# Survey — Auditoria e Encerramento: Git Diff com Arquivos Binários Grandes e Smart Excludes

- **Data:** 2026-11-09
- **Branch:** `develop_natan`
- **Origem:** Grill `/plan /grill-with-docs` (1 rodada, 3 decisões)
- **Objeto:** Auditoria técnica, encerramento formal do item herdado e reforço de defesa em profundidade (Defense-in-Depth) contra fluxos de bytes binários `U+FFFD` no modelo de IA
- **Estado:** Confirmado e Validado

---

## 1. Contexto da Tarefa

Nas rodadas e levantamentos anteriores (notadamente a partir do survey de diffs não-UTF-8 `docs/survey/20261027_git_diff_non_utf8_surveyfacts.md`), constava como pendência:
> *Revisar o `git diff` em repositórios com arquivos binários grandes: bytes binários chegam ao modelo como sequência de `U+FFFD`; vale confirmar que os smart excludes cobrem os casos reais. **Item herdado, ainda aberto.***

Esta sessão realizou o levantamento completo da arquitetura de filtragem de diffs, analisou as defesas já existentes no motor, verificou a cobertura de extensões e estabeleceu a blindagem final na entrada do gerador de conteúdo da IA.

---

## 2. Decisões Confirmadas no Grill (Rodada 1)

| # | Tema | Decisão |
|---|------|---------|
| **Q1** | Objetivo e Escopo | **Auditoria Técnica + Reforço em Profundidade (Opção A):** Confirmar formalmente a cobertura dos casos reais e implementar defesa defensiva em profundidade adicionando `collapse_binary_hunks()` no ponto de entrada de `generate_pr_content()` em `src/core.py`. |
| **Q2** | Catálogo de Smart Excludes | **Adicionar extensões modernas de ML/Data e manter paridade (Opção A):** Incluir `*.arrow`, `*.gguf`, `*.tflite`, `*.keras` em `templates/gitpr.smart-excludes.json`, `_FALLBACK_SMART_EXCLUDES` (`src/core.py`) e na suíte de testes de cobertura. |
| **Q3** | Governança e Artefatos | **Aprovar roteiro documental (Opção A):** Registrar `surveyfacts.md`, `plansfacts.md`, plano de implementação e completion report, consolidando os termos canônicos de domínio (`Smart Excludes` e `Binary hunk guard`). |

---

## 3. Fatos do Código Levantados e Auditados

1. **Primeira Linha de Defesa — Smart Excludes na Filtragem do Git:**
   - O GitPR aplica pathspecs `:(exclude)<pattern>` diretamente no comando `git diff` (`get_git_diff`, `get_unstaged_diff`, `get_git_staged_diff`, `get_git_full_diff`) e em diffs remotos via `filter_excluded_sections`.
   - Cobre 8 famílias de arquivos binários:
     1. Imagens e assets de design (`.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`, `.ico`, `.bmp`, `.psd`, `.avif`, `.heic`, `.ai`, `.icns`, `.tiff`, `.tif`)
     2. Documentos binários e Office (`.pdf`, `.doc`, `.docx`, `.xls`, `.xlsx`, `.ppt`, `.pptx`, `.odt`, `.ods`, `.odp`)
     3. Arquivos compactados e instaladores (`.zip`, `.tar`, `.gz`, `.tgz`, `.bz2`, `.xz`, `.7z`, `.rar`, `.jar`, `.war`, `.ear`, `.whl`, `.egg`, `.deb`, `.rpm`, `.dmg`, `.iso`, `.apk`, `.aab`, `.ipa`)
     4. Fontes web e desktop (`.woff`, `.woff2`, `.ttf`, `.otf`, `.eot`)
     5. Mídia de áudio e vídeo (`.mp3`, `.mp4`, `.wav`, `.ogg`, `.webm`, `.mov`, `.avi`, `.flac`, `.m4a`, `.mkv`)
     6. Binários compilados, bibliotecas e bytecode (`.exe`, `.dll`, `.so`, `.dylib`, `.a`, `.lib`, `.o`, `.obj`, `.class`, `.pyd`, `.wasm`, `.pdb`)
     7. Bancos de dados, datasets e pesos de ML (`.sqlite`, `.sqlite3`, `.db`, `.mdb`, `.accdb`, `.parquet`, `.feather`, `.pkl`, `.pickle`, `.npy`, `.npz`, `.h5`, `.hdf5`, `.pt`, `.pth`, `.onnx`, `.safetensors`, `.bin`, `.dat` — e expandido agora com `.arrow`, `.gguf`, `.tflite`, `.keras`)
     8. Certificados e keystores (`.p12`, `.pfx`, `.der`, `.cer`, `.jks`, `.keystore`)
   - Testado em `tests/test_smart_excludes.py::TestSmartExcludesBinaryCoverage` com verificação de paridade 1:1 entre template e fallback estático.

2. **Segunda Linha de Defesa — Binary Hunk Guard (`src/diff_parser.py`):**
   - Para arquivos binários com extensões desconhecidas ou não catalogadas onde o Git não detecta o byte NUL nos primeiros 8000 bytes (ou arquivos forçados como texto via `.gitattributes`), o leitor do Python (`errors="replace"`) gera sequências de `U+FFFD`.
   - `collapse_binary_hunks()` em `src/diff_parser.py`:
     - Avalia se há runs contíguos de $\ge 8$ caracteres `U+FFFD` (`BINARY_FFFD_CONTIGUOUS_RUN`) ou densidade $\ge 10\%$ com pelo menos 32 caracteres `U+FFFD` (`BINARY_FFFD_MIN_DENSITY` e `BINARY_FFFD_MIN_COUNT`).
     - Preserva byte a byte códigos-fonte legítimos em Latin-1 / Windows-1252 que possuem caracteres acentuados isolados.
     - Substitui o hunk binário por `Binary files a/... and b/... differ`.
     - Possui atalho rápido $O(1)$ caso o texto do diff não contenha `\ufffd`.

3. **Gaps Identificados e Solucionados:**
   - Diffs fornecidos externamente (ex.: via parâmetro de MCP `diff_text` ou chamadas diretas a `generate_pr_content`) não passavam por `collapse_binary_hunks()` se o chamador não usasse as funções de git do `core.py`.
   - Adicionada a proteção diretamente no topo de `generate_pr_content()` em `src/core.py`.
