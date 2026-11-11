# Survey de Fatos — Publicação da Extensão nos Marketplaces (Setup Wizard & Release)

**Data:** 2026-11-10  
**Branch:** `develop_natan`  
**Task:** `publish_extension_marketplaces`  
**Responsáveis:** Natan Fiuza, Antigravity

---

## 1. Contexto e Motivação da Tarefa

A extensão GitPR para VS Code e Cursor (`extensions/vscode`) possui código compilado em TypeScript, suíte de testes mocha, ícone oficial (256x256), licença LGPL-2.1 e integração via stdio com o servidor `gitpr-mcp`.

O workflow de CI/CD `.github/workflows/extension.yml` já está desacoplado e endurecido com:
- Criação de GitHub Releases com anexação permanente do pacote `.vsix` em tags `ext-v*`.
- **Granular marketplace gate**: avaliação não-bloqueante independente de `VSCE_PAT` e `OVSX_PAT`, que emite aviso e relatório no `$GITHUB_STEP_SUMMARY` sem falhar o build caso os segredos não estejam configurados.
- Guias de instalação manual e de 1 clique (`code --install-extension` / `cursor --install-extension`) em 5 idiomas (`docs/editor-extension.*.md`).
- Guia detalhado de publicação passo a passo traduzido nos 5 idiomas (`docs/marketplace-publishing-guide.*.md`).

A pendência restante identificada no relatório de estado do projeto é puramente operacional/externa: a criação dos tokens de acesso pessoal (PATs) no Azure DevOps (para o Visual Studio Marketplace) e no Open VSX Registry, e seu cadastramento como secrets no repositório GitHub.

---

## 2. Levantamento de Fatos Técnicos

| Componente | Fato Levantado | Situação Atual |
|---|---|---|
| **Publisher ID** | Declarado como `"publisher": "natanfiuza"` em `extensions/vscode/package.json`. | Requer publisher `natanfiuza` no Azure DevOps e namespace `natanfiuza` no Open VSX. |
| **Pipeline de Publicação** | `.github/workflows/extension.yml` avalia `secrets.VSCE_PAT` e `secrets.OVSX_PAT`. | Pronto para publicar assim que os secrets existirem. |
| **Validação Local de PAT** | `npx @vscode/vsce verify-pat natanfiuza -p <PAT>` e `npx ovsx verify-pat -p <PAT>`. | CLIs oficiais validam credenciais sem publicar. |
| **Padrão de Wizards do Projeto** | `.agents/skills/wizard/template.sh` define biblioteca bash consistente com abertura de URLs, prompts mascarados, validação e gravação via `gh secret set`. | Disponível para reuso como base do assistente. |
| **Expiração de Credenciais** | PATs do Azure DevOps possuem validade máxima de 1 ano. | Exige ferramenta reprodutível para facilitar renovações periódicas. |
| **Segurança de Tokens** | PATs de publicação de extensões não devem ser salvos em arquivos `.env` locais em texto puro. | Devem ser gravados diretamente nos secrets de CI/CD do GitHub. |

---

## 3. Decisões Consolidadas da Sessão de Grill (Rodadas 1 e 2)

### Rodada 1
1. **Objetivo e formato de execução (Q1):** Criar um assistente interativo em Bash (`scripts/marketplace-setup-wizard.sh`) que guia o operador na criação, teste e configuração dos PATs.
2. **Publisher e Namespace (Q2):** Confirmar e manter `natanfiuza` como publisher e namespace em ambos os portais externos.
3. **Estratégia de corte da primeira versão (Q3):** Conectar a configuração dos segredos ao release oficial `ext-v0.1.0`.
4. **Persistência do assistente (Q4):** Versionar permanentemente em `scripts/marketplace-setup-wizard.sh`.

### Rodada 2
1. **Armazenamento de Credenciais (Q1):** Gravação exclusiva nos secrets do GitHub Actions via `gh secret set` (com link direto de fallback para o navegador). Nenhum token gravado em arquivo local.
2. **Validação Local Prévia (Q2):** Execução automática de `vsce verify-pat` e `ovsx verify-pat` via `npx` antes da gravação do secret, com fallback resiliente para continuidade manual se `npx` ou rede falharem.
3. **Ação de Fechamento (Q3):** Oferecer a criação e envio da tag oficial `ext-v0.1.0` via confirmação `[y/N]`, executando `git tag ext-v0.1.0 && git push origin ext-v0.1.0` quando aceito.
4. **Sincronização de Documentação e Glossário (Q4):** Documentar o novo wizard em 5 idiomas (`docs/marketplace-publishing-guide.*.md`), adicionar o termo canônico `Marketplace setup wizard` ao `CONTEXT.md` e estender os testes em `tests/unit/test_marketplace_publishing_guide_docs_parity.py`.
