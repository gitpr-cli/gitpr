# Extensão de Editor do GitPR (VS Code & Cursor)

A **Extensão de Editor do GitPR** traz geração de mensagens Conventional Commits com IA, Code Reviews, criação/publicação de Pull Requests e diagnósticos unificados do `gitpr check` diretamente para o **VS Code** e o **Cursor** como um **thin client MCP** leve.

---

## Arquitetura: Thin Client Real via MCP

Em vez de duplicar templates de prompt, parsers de diff ou gerenciamento de credenciais em TypeScript, a extensão se comunica via `stdio` com o servidor local `gitpr-mcp` (`@modelcontextprotocol/sdk`):

- **Uma Sessão por Pasta do Workspace**: A extensão inicia o `gitpr-mcp` sob demanda (lazy) no primeiro comando (com `cwd` apontando para a raiz da pasta do workspace) e mantém a sessão persistente, reconectando automaticamente se o processo encerrar.
- **Verificação de Contrato (Handshake)**: Ao conectar, a extensão chama `listTools` e confere se todas as tools obrigatórias (`get_git_context`, `generate_commit_message`, `review_code`, `full_review`, `generate_pr_description`, `run_check`, `publish_pull_request`) existem. Se o seu `gitpr-cli` estiver desatualizado, exibe um aviso de atualização (`pip install --upgrade gitpr-cli`).
- **Zero Configuração Paralela**: Chaves de API, tokens SCM e preferências permanecem no `~/.gitpr/.env` criptografados com Fernet. A extensão nunca solicita nem armazena segredos.
- **Mascaramento de Segredos em Profundidade**: Tanto o servidor MCP em Python (`mask_sensitive_text`) quanto a extensão em TypeScript (`maskSensitiveText`) mascaram tokens (`ghp_*`, `glpat-*`, `sk-*`, `AIza*`, `Bearer *`, chaves privadas) antes de exibir notificações ou gravar no OutputChannel `GitPR`.

---

## Instalação

### 1. Pré-requisito: `gitpr-cli`

Certifique-se de que o `gitpr-cli` está instalado e configurado na sua máquina:

```bash
pip install --upgrade gitpr-cli
gitpr --install
```

### 2. Instale a Extensão (VS Code & Cursor)

Tanto o VS Code quanto o Cursor compartilham o mesmo pacote VSIX (`natanfiuza.gitpr`):

- **VS Code Marketplace**: Procure por `GitPR` (`natanfiuza.gitpr`).
- **Cursor / Open VSX**: Procure por `GitPR` ou instale a partir do arquivo `.vsix`.
- **A partir do Código-Fonte (VSIX Local)**:
  ```bash
  cd extensions/vscode
  npm install
  npm run compile
  npm run package
  code --install-extension gitpr-0.1.0.vsix
  ```

---

## Comandos e Fluxos de Uso

Todos os comandos estão disponíveis na **Command Palette** (`Ctrl+Shift+P` / `Cmd+Shift+P`), e os 4 atalhos principais (**Commit**, **Review**, **PR**, **Check**) ficam fixados na **Status Bar**.

| Comando | Tool MCP Chamada | Comportamento |
|---|---|---|
| `GitPR: Commit (Gerar Mensagem)` | `generate_commit_message` | Gera um rascunho Conventional Commits e preenche a caixa de mensagem do painel **Source Control** (com fallback para copiar para a área de transferência). Nunca faz commit sozinho. |
| `GitPR: Review (Alterações Locais)` | `review_code(mentor=false)` | Revisa alterações locais (`git diff HEAD`) e abre um preview Markdown lado a lado. |
| `GitPR: Full Review (Contra Branch Base)` | `full_review(mentor=false)` | Executa `git fetch` e revisa a branch inteira contra `origin/main`, abrindo preview Markdown. |
| `GitPR: Review (Modo Mentor Júnior)` | `review_code(mentor=true)` | Anexa explicações didáticas do Modo Mentor Júnior ao preview do code review. |
| `GitPR: Gerar Rascunho de PR` | `generate_pr_description(explain=false)` | Abre um documento Markdown editável de rascunho de PR (`linha 1` = título, restante = corpo). |
| `GitPR: Gerar Rascunho de PR (com Guia do Revisor)` | `generate_pr_description(explain=true)` | Gera o rascunho editável de PR incluindo a seção **Explain my PR** (Guia do Revisor). |
| `GitPR: Publicar PR a partir do Rascunho Ativo` | `publish_pull_request` | Lê o rascunho Markdown editado ativo, pede confirmação em modal (`Publicar` ou `Publicar como Rascunho`) e cria o PR no forge configurado (GitHub, GitLab, Bitbucket, Azure DevOps). |
| `GitPR: Check (Diagnósticos Unificados de Linter e Segurança)` | `run_check` | Executa o pipeline unificado de verificação e popula o painel **Problems** com diagnósticos clicáveis por arquivo, linha e severidade. |

### Publicação de Pull Request em Dois Passos

A publicação nunca ocorre às cegas:
1. Execute **`GitPR: Gerar Rascunho de PR`** (ou **`Gerar Rascunho de PR (com Guia do Revisor)`**).
2. Revise e edite o documento Markdown aberto. A primeira linha não vazia é usada como título do Pull Request e o restante como corpo.
3. Clique no botão **`Publicar PR`** na barra superior do editor (ou execute **`GitPR: Publicar PR a partir do Rascunho Ativo`**).
4. Confirme no modal. O servidor retorna status estruturados:
   - `needs_push` → oferece o botão **Push e Publicar** via `vscode.git`.
   - `already_exists` → oferece abrir o PR existente no navegador.
   - `auth_required` → oferece abrir um terminal executando `gitpr` para autenticar.
   - `success` → oferece abrir o PR recém-criado no navegador.

---

## Configurações da Extensão

Configure no `settings.json` do VS Code / Cursor:

```json
{
  "gitpr.mcpCommand": "gitpr-mcp",
  "gitpr.mcpArgs": [],
  "gitpr.provider": "",
  "gitpr.check.useAI": false
}
```

| Configuração | Tipo | Padrão | Descrição |
|---|---|---|---|
| `gitpr.mcpCommand` | `string` | `"gitpr-mcp"` | Executável usado para iniciar o servidor MCP do GitPR. |
| `gitpr.mcpArgs` | `string[]` | `[]` | Argumentos adicionais passados ao executável do servidor MCP. |
| `gitpr.provider` | `string` | `""` | Sobrescrita opcional do provedor de IA (`gemini`, `deepseek`, `ollama`). Vazio herda do `~/.gitpr/.env`. |
| `gitpr.check.useAI` | `boolean` | `false` | Ativa revisão por IA dentro do `GitPR: Check`. Desativado por padrão para manter verificações no editor rápidas e sem consumo de tokens. |

---

## Internacionalização (i18n) e Telemetria

- **Idiomas da Interface**: Empacotada com traduções `en`, `pt-br`, `es` e `fr` (`package.nls.*.json` e `l10n/bundle.l10n.*.json`). Nota: o VS Code não possui pacote de idioma `pt-pt` separado; usuários de Português (Portugal) recebem a interface `pt-br` no editor, enquanto todo conteúdo gerado pelo servidor respeita `GITPR_LANG=pt_pt`.
- **Apenas Telemetria Local**: A extensão não envia telemetria externa nem abre conexões de rede. O servidor MCP local registra os eventos `mcp:check` e `mcp:publish_pr` no ledger SQLite local (`~/.gitpr/metrics/telemetry.db`).
