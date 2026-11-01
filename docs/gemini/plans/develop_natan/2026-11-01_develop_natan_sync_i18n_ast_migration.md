# Implementation Plan - Migração do Extrator do `sync_i18n.py` para AST

## Goal Description
Migrar o extrator de chaves de internacionalização em `tests/sync_i18n.py` de expressões regulares (`re`) para Abstract Syntax Tree (`ast`). O regex atual trunca literais com concatenação implícita (ex: `__("a " "b")` e literais multilinha), capturando apenas o primeiro fragmento e corrompendo os arquivos de tradução (`langs/*.json`) ao sincronizar. `tests/test_i18n.py` já utilizava AST localmente para validação; este plano unifica o extrator em `tests/sync_i18n.py`, elimina duplicação de código e atualiza a suíte de testes unitários do extrator.

## User Review Required
> [!NOTE]
> Todas as 4 decisões da rodada de alinhamento foram confirmadas pelo usuário:
> 1. Unificar o extrator AST em `tests/sync_i18n.py` como Single Source of Truth e importá-lo em `tests/test_i18n.py`.
> 2. Substituir o `PATTERN` legado e atualizar `TestPatternExtraction` para `TestAstExtraction` em `tests/test_i18n.py`, validando a concatenação completa de literais adjacentes.
> 3. Padronizar caminhos e raízes de busca com `pathlib.Path` relativo à raiz do repositório (`REPO`), removendo a entrada redundante `main.py` de `SRC_DIRS`.
> 4. Sem alterações no `CONTEXT.md` ou criação de ADRs, documentando no relatório técnico mandatório.

## Proposed Changes

### Tests & Sincronização i18n

#### [MODIFY] [tests/sync_i18n.py](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/tests/sync_i18n.py)
- Importar `Path` de `pathlib`.
- Substituir o regex `PATTERN` e a função `_extract_keys` baseada em regex por um extrator AST robusto:
  - Analisa o código Python com `ast.parse(source)`.
  - Percorre a árvore com `ast.walk(tree)`.
  - Identifica nós `ast.Call` onde `node.func` é um `ast.Name` com identificador `"__"`.
  - Extrai o primeiro argumento (`node.args[0]`) quando for um `ast.Constant` com valor string. O parser AST do Python dobra automaticamente concatenações implícitas (`"a " "b"` -> `"a b"`).
- Atualizar `SRC_DIRS` para `[REPO / "src", REPO / "run.py"]`, eliminando a referência inexistente `main.py` na raiz.
- Padronizar leitura/gravação de arquivos em `LANGS_DIR = REPO / "langs"` com `pathlib.Path`.

```python
from pathlib import Path
import ast
import json
import os

REPO = Path(__file__).resolve().parent.parent
SRC_DIRS = [REPO / "src", REPO / "run.py"]
LANGS_DIR = REPO / "langs"
LANG_FILES = ["pt_br.json", "pt_pt.json", "es_es.json", "fr_fr.json", "es.json", "fr.json"]

def _extract_keys(source, keys):
    """Extracts every __("literal") translation key from Python source using AST.

    Folds implicit concatenation (__("a " "b") and multi-line literals) into a
    single string, matching runtime lookup behaviour.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)):
            continue
        if node.func.id != "__" or not node.args:
            continue
        first = node.args[0]
        if isinstance(first, ast.Constant) and isinstance(first.value, str):
            keys.add(first.value)
```

---

#### [MODIFY] [tests/test_i18n.py](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/tests/test_i18n.py)
- Atualizar import: `from tests.sync_i18n import _extract_keys`.
- Refatorar `_extract_keys_ast(path, keys)` para delegar a leitura do arquivo para `_extract_keys(content, keys)`.
- Atualizar `TestPatternExtraction` para `TestAstExtraction`:
  - Testar amostras com kwargs e chamadas aninhadas (`click.secho(__("..."))`).
  - Testar aspas simples com aspas duplas internas e caracteres de escape.
  - Atualizar o teste de literais adjacentes (`test_adjacent_literals_yield_joined_string`): agora valida que `__("a " "b")` resulta em `{"a b"}` completo.
  - Adicionar teste para concatenação multilinha.
- Atualizar docstrings que referenciam o regex legado como limitação.

---

## Verification Plan

### Automated Tests
1. Executar a suíte de testes de internacionalização:
   ```bash
   python -m unittest tests/test_i18n.py
   ```
2. Executar a suíte completa de testes do repositório:
   ```bash
   python -m pytest tests/ -v
   ```

### Manual Verification
1. Executar `tests/sync_i18n.py` a partir da raiz e de subdiretórios para garantir que o script roda sem erros e encontra todas as chaves ativas:
   ```bash
   python tests/sync_i18n.py
   ```
2. Verificar com `git status` e `git diff langs/` que nenhum arquivo de tradução foi corrompido ou truncado.
