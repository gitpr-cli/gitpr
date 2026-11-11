# Plano de Execução — Assistente de Publicação nos Marketplaces (`marketplace-setup-wizard.sh`)

**Data:** 2026-11-10  
**Branch:** `develop_natan`  
**Task:** `publish_extension_marketplaces`  

---

## 1. Escopo e Objetivos

Desenvolver, testar e documentar o assistente interativo `scripts/marketplace-setup-wizard.sh` para guiar a configuração de credenciais (`VSCE_PAT` e `OVSX_PAT`), validar os tokens localmente, provisionar os segredos no GitHub Actions e viabilizar o disparo do primeiro release oficial (`ext-v0.1.0`).

---

## 2. Etapas de Implementação

### Etapa 1: Criação do Wizard Interativo (`scripts/marketplace-setup-wizard.sh`)
- Basear-se na biblioteca padrão de UX do projeto (`.agents/skills/wizard/template.sh`).
- Definir 5 etapas focadas (`TOTAL_STAGES=5`):
  1. **Stage 1 (Prerequisites)**: Verificação de pré-requisitos (`git`, `gh` autenticado, `node`/`npx`).
  2. **Stage 2 (Visual Studio Marketplace)**: Abrir Azure DevOps PAT settings, guiar criação de PAT com `Marketplace (Acquire, Manage)` e `All accessible organizations`, publisher `natanfiuza`, captura mascarada de `VSCE_PAT`.
  3. **Stage 3 (VSCE PAT Validation & Secret Provisioning)**: Testar via `npx @vscode/vsce verify-pat natanfiuza -p "$VSCE_PAT"`, gravar secret no GitHub via `set_secret VSCE_PAT "$VSCE_PAT"`.
  4. **Stage 4 (Open VSX Registry)**: Abrir `open-vsx.org`, guiar registro de namespace `natanfiuza` e criação de Access Token, captura mascarada de `OVSX_PAT`.
  5. **Stage 5 (OVSX PAT Validation, Secret Provisioning & Release Prompt)**: Testar via `npx ovsx verify-pat -p "$OVSX_PAT"`, gravar secret no GitHub via `set_secret OVSX_PAT "$OVSX_PAT"`, oferecer criação e push da tag `ext-v0.1.0`.

### Etapa 2: Atualização do Modelo de Domínio (`CONTEXT.md`)
- Incluir o termo canônico:
  - **Marketplace setup wizard**: The interactive guided script (`scripts/marketplace-setup-wizard.sh`) that assists the maintainer in generating, locally validating (`vsce verify-pat`, `ovsx verify-pat`), and provisioning `VSCE_PAT` and `OVSX_PAT` credentials into GitHub repository secrets.

### Etapa 3: Atualização da Documentação nos 5 Idiomas
- Atualizar `docs/marketplace-publishing-guide.md`, `pt_br.md`, `pt_pt.md`, `es_es.md` e `fr_fr.md` adicionando a seção "Quick Setup with the Marketplace Wizard" como o caminho recomendado antes dos passos manuais.
- Adicionar menção no `README.md`.

### Etapa 4: Testes Automatizados e Verificação
- Estender `tests/unit/test_marketplace_publishing_guide_docs_parity.py` para verificar que todos os 5 guias referenciam `marketplace-setup-wizard.sh`.
- Criar teste de validação de sintaxe e executabilidade do script bash (`test_marketplace_wizard_syntax.py`).
- Executar suíte completa de testes (`pytest`).
