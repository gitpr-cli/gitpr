## Relatório de Conclusão — i18n do blame_engine.py

### O que foi feito
- Aplicadas 28 substituições i18n no `src/blame_engine.py` conforme mapa `docs/plans/mapa_substituicao_blame_engine.md`
- Todas as strings de UI convertidas de português para inglês com wrapper `__()`
- Status internos alterados: `ORIGEM` → `ORIGIN`, `REFATORACAO` → `REFACTORING`
- Prompts da IA traduzidos para inglês (system instruction, análise de diff, resumo executivo)
- Comparações de status (`== "ORIGEM"`) atualizadas para `== "ORIGIN"`

### Arquivos alterados

| Arquivo | Tipo de mudança | Descrição |
|---|---|---|
| `src/blame_engine.py` | feat (i18n) | 28 chamadas `__()`: execute_git_blame, analyze_commit_with_ai, run_blame_analysis; 6+ ORIGEM→ORIGIN; prompts IA em inglês |

### Impacto
- **Funcionalidade:** Toda a UI do arqueólogo de código agora suporta i18n (EN/PT). Status `ORIGIN`/`REFACTORING` padronizados
- **Performance:** Sem impacto
- **Compatibilidade:** Código que verificava `"ORIGEM"` em cache ou JSON da IA precisa ser atualizado para `"ORIGIN"`

### Próximos passos (se aplicável)
- Aplicar i18n nos arquivos restantes: `issue_engine.py`, `tui_issue.py`, `config.py`, `updater.py`, `ui/*.py`
- Publicar versão 0.0.20 no PyPI
