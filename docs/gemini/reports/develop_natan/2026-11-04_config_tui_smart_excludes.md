## Completion Report — Seção Smart Exclude na TUI (`gitpr config`)

### What was done
- Implementou-se a categoria dedicada `smart_excludes` em substituição à categoria provisória `diff` na TUI de configuração (`gitpr config`), encerrando o **Item 10** herdado e pendente desde a v0.0.14.
- Agruparam-se os campos `GITPR_SKIP_SMART_EXCLUDES`, `GITPR_SMART_EXCLUDES_GLOBAL`, `GITPR_SMART_EXCLUDES_LOCAL` e moveu-se `SMART_EXCLUDES_VERSION` (com botão de forçar download) para a nova categoria `smart_excludes`.
- Adicionaram-se no `src/core.py` funções utilitárias para carregamento e persistência das regras locais do repositório (`.gitpr/conf/gitpr.smart-excludes.json`) e das listas globais Core e Docs.
- Criou-se o painel dedicado `_EXCLUDES_PANE_ID` no `src/ui/config_app.py`, permitindo alternar entre as 3 fontes (Projeto, Global Core, Global Docs), editar as regras do projeto via `TextArea` (um padrão glob por linha), criar o arquivo local via botão dedicado caso não exista, e salvar tudo atomicamente via `F2` (com suporte a reversão `Ctrl+R` e confirmação de descarte no `Esc`).
- Adicionou-se o termo canônico "Smart Excludes" ao `CONTEXT.md`.
- Atualizaram-se os 6 arquivos de dicionário em `langs/` (`pt_br`, `pt_pt`, `es_es`, `es`, `fr_fr`, `fr`) com 100% de paridade e conformidade nos testes estritos de i18n (`test_i18n.py`).
- Atualizou-se a documentação técnica `docs/smart-excludes.md` e suas 4 versões traduzidas (`.pt_br.md`, `.pt_pt.md`, `.es_es.md`, `.fr_fr.md`) mantendo estrita paridade de linhas (185 linhas cada).
- Implementaram-se testes automatizados dedicados em `tests/test_config_schema.py` e `tests/test_config_app.py`.

### Changed files
| File | Change type | Description |
|------|-------------|-------------|
| `CONTEXT.md` | docs | Adição do termo canônico Smart Excludes e definição das suas 3 camadas |
| `src/config_schema.py` | feat | Substituição de `diff` por `smart_excludes`, realocação de campos e versão |
| `src/core.py` | feat | Helpers para leitura/gravação das listas de padrões de exclusão |
| `src/ui/config_app.py` | feat | Painel interativo com seletor de fontes, editor de regras e ações na TUI |
| `langs/*.json` (6 arquivos) | i18n | Remoção de chaves órfãs e adição das 12 novas strings traduzidas |
| `docs/smart-excludes*.md` (5 arquivos) | docs | Documentação da seção na TUI mantendo paridade de 185 linhas |
| `tests/test_config_schema.py` | test | Validação da nova categoria e campos |
| `tests/test_config_app.py` | test | Testes assíncronos da TUI cobrindo a seção, criação e persistência |
| `tests/test_i18n.py` | test | Adição de "Smart Excludes" em `ALLOWED_IDENTITY_TERMS` |
| `docs/survey/20261104_config_tui_smart_excludes_surveyfacts.md` | docs | Registro dos fatos e decisões da sessão de grill |
| `docs/gemini/plans/develop_natan/2026-11-04_develop_natan_config_tui_smart_excludes.md` | docs | Plano de implementação técnica |

### Impact
- **Functionality:** O usuário agora pode visualizar e gerenciar facilmente as regras de exclusão de diff do projeto diretamente pela TUI de configuração sem editar arquivos JSON manualmente, além de inspecionar as listas globais embutidas.
- **Performance:** Nenhuma degradação. O carregamento das listas é local e sob demanda ao navegar até a categoria.
- **Compatibility:** Total compatibilidade retroativa. As variáveis de ambiente `GITPR_SMART_EXCLUDES_*` e o formato do arquivo `.gitpr/conf/gitpr.smart-excludes.json` continuam idênticos.

### Next steps (if applicable)
- Revisão das alterações e execução manual de conferência visual via `python run.py config`.
