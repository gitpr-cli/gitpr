## Completion Report — Reconcile Project Version

### What was done
- Reconciliada a versão do projeto em `CLAUDE.md` e `GEMINI.md` de `0.0.37` para `1.4.4`, referenciando explicitamente `src/updater.py::__version__` como SSOT canônica.
- Documentado no glossário (`CONTEXT.md`) os termos de domínio `Package version`, `Language asset version` e `Hook script version`.
- Registrada a decisão arquitetural em `docs/adr/0014-canonical-package-version-ssot.md`.
- Enriquecidos os comentários de `src/updater.py` explicitando o papel de `__version__` como SSOT para empacotamento, CLI, CI e regras de agentes.
- Implementada nova suíte de testes de consistência `tests/unit/test_version_consistency.py` cobrindo 5 cenários para prevenir drift em CI.
- Executados e aprovados os testes de consistência (`5 passed`).

### Changed files
| File | Change type | Description |
|------|-------------|-------------|
| `CLAUDE.md` | docs | Atualizada a versão atual para 1.4.4 e adicionada menção à SSOT |
| `GEMINI.md` | docs | Atualizada a versão atual para 1.4.4 e adicionada menção à SSOT |
| `CONTEXT.md` | docs | Adicionados os termos Package version, Language asset version e Hook script version |
| `docs/adr/0014-canonical-package-version-ssot.md` | docs | Novo ADR formalizando a convenção única de versionamento |
| `src/updater.py` | refactor | Comentários enriquecidos formalizando `__version__` como SSOT canônica |
| `tests/unit/test_version_consistency.py` | test | Nova suíte de testes automatizados garantindo consistência |
| `docs/gemini/plans/develop_natan/2026-10-31_develop_natan_reconcile_project_version.md` | docs | Plano de implementação arquivado |
| `docs/gemini/walkthrough/develop_natan/2026-10-31_reconcile_project_version.md` | docs | Walkthrough técnico arquivado |

### Impact
- **Functionality:** Não há alteração de funcionalidade de runtime na CLI. O `__version__` permanece em 1.4.4.
- **Performance:** Nenhum impacto em performance de produção.
- **Compatibility:** Total compatibilidade mantida. A sincronização de versão evita confusões em LLMs e desenvolvedores consultando guias do repositório.

### Next steps (if applicable)
- Durante futuros processos de release (`gitpr release`), o bump em `src/updater.py` continuará sendo verificado pelo novo teste `test_version_consistency.py`.
