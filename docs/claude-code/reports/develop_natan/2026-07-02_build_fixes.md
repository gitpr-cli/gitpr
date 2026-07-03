## Relatório de Conclusão — Correções de Build e Distribuição

### O que foi feito
- Corrigido circular import entre `core.py` e `cache.py` (lazy import de `get_current_branch`)
- Corrigido `SyntaxWarning` no banner ASCII art (raw string `r"""..."""`)
- Corrigido empacotamento: `src/ui/` não era incluído no `.whl` (criado `__init__.py` e alterado `pyproject.toml` para `find:`)
- Adicionadas dependências faltantes: `textual` e `requests`

### Arquivos alterados

| Arquivo | Tipo de mudança | Descrição |
|---|---|---|
| `src/cache.py` | fix | Substituído `from src.core import get_current_branch` (top-level) por lazy import dentro de `save_cached_response()` |
| `src/main.py` | fix | Banner `print_banner()` usa raw string `r"""..."""` para evitar `SyntaxWarning` no `\` |
| `src/ui/__init__.py` | fix (novo) | Arquivo vazio para tornar `src/ui/` um sub-package Python reconhecido pelo setuptools |
| `pyproject.toml` | fix | `packages = ["src"]` → `[tool.setuptools.packages.find]` com `include = ["src", "src.*"]`; adicionadas dependências `textual` e `requests` |

### Impacto
- **Funcionalidade:** `gitpr -is` agora funciona quando instalado via `pip install gitpr-cli` (antes falhava com `ModuleNotFoundError: No module named 'src.ui'` e `No module named 'textual'`)
- **Performance:** Sem impacto
- **Compatibilidade:** Nenhuma quebra. `src/ui/__init__.py` é arquivo vazio, não afeta imports existentes

### Próximos passos (se aplicável)
- Publicar versão `0.0.19` no PyPI com todas as correções
