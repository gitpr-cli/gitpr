## Completion Report — Assistente de Publicação nos Marketplaces e Preparação de Release

### What was done
- Conduzida sessão de alinhamento e refinamento (**Grill with Docs**) com esgotamento completo da fronteira de decisões.
- Criado o assistente interativo em Bash [`scripts/marketplace-setup-wizard.sh`](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/scripts/marketplace-setup-wizard.sh) baseado na biblioteca padronizada de wizards do projeto (`.agents/skills/wizard/template.sh`), composto por 5 etapas:
  1. Verificação de pré-requisitos (`git`, `gh auth`, `node`/`npx`).
  2. Guia de criação do PAT no Azure DevOps (`Marketplace: Acquire, Manage`, `All accessible organizations`) e publisher `natanfiuza`.
  3. Validação local prévia via `npx @vscode/vsce verify-pat natanfiuza -p "$VSCE_PAT"` e gravação do segredo `VSCE_PAT` no GitHub Actions via `gh secret set`.
  4. Guia de criação de conta e namespace `natanfiuza` no Open VSX Registry e geração do Access Token.
  5. Validação local prévia via `npx ovsx verify-pat -p "$OVSX_PAT"`, gravação do segredo `OVSX_PAT` no GitHub Actions via `gh secret set` e prompt de confirmação para disparo do release oficial `ext-v0.1.0` (`git tag ext-v0.1.0 && git push origin ext-v0.1.0`).
- Atualizado o modelo de domínio em [`CONTEXT.md`](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/CONTEXT.md) com o novo termo canônico `Marketplace setup wizard`.
- Atualizado o guia de publicação nos 5 idiomas suportados ([`docs/marketplace-publishing-guide.md`](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/docs/marketplace-publishing-guide.md), `.pt_br.md`, `.pt_pt.md`, `.es_es.md`, `.fr_fr.md`) adicionando a seção "Quick Setup with the Marketplace Setup Wizard" como método recomendado.
- Atualizado o [`README.md`](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/README.md) na seção de Extensões com referência ao wizard.
- Criada a suíte de testes unitários [`tests/unit/test_marketplace_wizard_syntax.py`](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/tests/unit/test_marketplace_wizard_syntax.py) validando shebang, marcadores, 5 etapas e sintaxe estática via `bash -n`.
- Atualizado [`tests/unit/test_marketplace_publishing_guide_docs_parity.py`](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/tests/unit/test_marketplace_publishing_guide_docs_parity.py) para exigir a preservação do token `scripts/marketplace-setup-wizard.sh` em todos os 5 idiomas.
- Validação executada e aprovada: 7 testes unitários Python passando (100%) e 7 testes mocha da extensão passando (incluindo teste live stdio com `gitpr-mcp`).

### Changed files
| File | Change type | Description |
|------|-------------|-------------|
| `scripts/marketplace-setup-wizard.sh` | feat (new) | Interactive bash setup wizard for VS Code Marketplace & Open VSX |
| `CONTEXT.md` | docs | Added canonical domain term `Marketplace setup wizard` |
| `docs/marketplace-publishing-guide.md` | docs | Added quick setup wizard section (EN) |
| `docs/marketplace-publishing-guide.pt_br.md` | docs | Added quick setup wizard section (PT-BR) |
| `docs/marketplace-publishing-guide.pt_pt.md` | docs | Added quick setup wizard section (PT-PT) |
| `docs/marketplace-publishing-guide.es_es.md` | docs | Added quick setup wizard section (ES-ES) |
| `docs/marketplace-publishing-guide.fr_fr.md` | docs | Added quick setup wizard section (FR-FR) |
| `README.md` | docs | Referenced marketplace setup wizard in Extension section |
| `tests/unit/test_marketplace_wizard_syntax.py` | test (new) | Unit tests for wizard markers and bash -n syntax validation |
| `tests/unit/test_marketplace_publishing_guide_docs_parity.py` | test | Added wizard token assertion across 5 languages |
| `docs/survey/20261110_publish_extension_marketplaces_surveyfacts.md` | docs (new) | Survey facts from grilling session |
| `docs/plans/develop_natan/20261110_publish_extension_marketplaces_plansfacts.md` | docs (new) | Execution plan facts from grilling session |
| `docs/gemini/plans/develop_natan/2026-11-10_develop_natan_publish_extension_marketplaces.md` | docs (new) | Task implementation plan |

### Impact
- **Functionality:** O mantenedor agora dispõe de um assistente interativo de ponta a ponta (`scripts/marketplace-setup-wizard.sh`) que remove a fricção de navegação nos portais do Azure DevOps e Open VSX, valida localmente os PATs gerados antes de salvá-los e provisiona automaticamente os secrets `VSCE_PAT` e `OVSX_PAT` no GitHub Actions.
- **Performance:** Zero overhead de runtime no core CLI ou na extensão.
- **Compatibility:** Total compatibilidade entre plataformas (Windows Git Bash, Linux e macOS).

### Next steps (if applicable)
- Executar `./scripts/marketplace-setup-wizard.sh` quando desejar cadastrar os PATs e publicar a extensão no Visual Studio Marketplace e Open VSX.
- Disparar a tag `ext-v0.1.0` (`git tag -a ext-v0.1.0 -m "release: GitPR Editor Extension v0.1.0" && git push origin ext-v0.1.0`).
