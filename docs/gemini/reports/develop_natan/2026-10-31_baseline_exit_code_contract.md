## Completion Report — Baseline Exit Code Blast Radius Contract

### What was done
- Mapeado o blast radius completo de um baseline inutilizável (unusable baseline) em todos os pontos de entrada da CLI (`src/main.py`, `src/review/remote_pr.py`, `src/application/use_cases/baseline_gate.py`, `src/application/use_cases/run_check.py`).
- Documentado o contrato canônico de exit codes em `docs/baseline-suppressions.md` (e nas traduções `.pt_br`, `.pt_pt`, `.es_es`, `.fr_fr`), incluindo a diferenciação entre exit 1 (fluxos humanos/locais) e exit 2 (`gitpr check` para CI).
- Corrigida a afirmação incorreta anterior de que `-r`, `-f` e `-i` não alteravam exit code (esclarecido que não alteram por achados, mas saem com 1 diante de baseline inutilizável).
- Adicionadas referências cruzadas em `docs/check-ci.md` (e nas 4 traduções).
- Formalizado o termo canônico `Unusable baseline` em `CONTEXT.md`.
- Implementada suíte de testes de integração `tests/integration/test_baseline_exit_code_contract.py` cobrindo os 8 fluxos.
- Corrigido bug em `src/application/use_cases/run_check.py` onde atributos de `FileRisk` eram acessados como `.path` em vez de `.file_path`.

### Changed files
| File | Change type | Description |
|------|-------------|-------------|
| `docs/baseline-suppressions.md` | docs | Tabela canônica de exit codes por fluxo, correção sobre `-r`/`-f`/`-i`, decisão adiada |
| `docs/baseline-suppressions.pt_br.md` | docs | Tradução pt-BR do contrato de exit codes e correção |
| `docs/baseline-suppressions.pt_pt.md` | docs | Tradução pt-PT do contrato de exit codes e correção |
| `docs/baseline-suppressions.es_es.md` | docs | Tradução es-ES do contrato de exit codes e correção |
| `docs/baseline-suppressions.fr_fr.md` | docs | Tradução fr-FR do contrato de exit codes e correção |
| `docs/check-ci.md` | docs | Remissão cruzada na seção de códigos de saída |
| `docs/check-ci.pt_br.md` | docs | Tradução pt-BR da remissão cruzada |
| `docs/check-ci.pt_pt.md` | docs | Tradução pt-PT da remissão cruzada |
| `docs/check-ci.es_es.md` | docs | Tradução es-ES da remissão cruzada |
| `docs/check-ci.fr_fr.md` | docs | Tradução fr-FR da remissão cruzada |
| `CONTEXT.md` | docs | Adição do termo de glossário "Unusable baseline" |
| `src/application/use_cases/run_check.py` | fix | Acesso a `f.file_path` em vez de `f.path` para objetos `FileRisk` |
| `tests/integration/test_baseline_exit_code_contract.py` | test | Nova suíte de testes de integração travando o contrato de exit code |
| `docs/gemini/plans/develop_natan/2026-10-31_develop_natan_baseline_exit_code_contract.md` | docs | Plano de implementação arquivado |
| `docs/gemini/walkthrough/develop_natan/2026-10-31_baseline_exit_code_contract.md` | docs | Walkthrough do desenvolvimento arquivado |

### Impact
- **Functionality:** O comportamento da CLI e os exit codes foram preservados integralmente. O `check` continua emitindo 2 em erros de baseline e os seis comandos locais continuam emitindo 1.
- **Performance:** Nenhuma alteração de performance em produção.
- **Compatibility:** Total compatibilidade retroativa mantida. A decisão de unificar os fluxos para exit 2 foi documentada como explicitamente adiada para evitar quebras em scripts existentes.

### Next steps (if applicable)
- Avaliar em release maior (breaking) se os fluxos locais devem adotar exit 2 para alinhar com o `check`.
