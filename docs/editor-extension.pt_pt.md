# Extensão de Editor do GitPR (VS Code & Cursor)

A **Extensão de Editor do GitPR** traz geração de mensagens Conventional Commits com IA, Code Reviews, criação/publicação de Pull Requests e diagnósticos unificados do `gitpr check` diretamente para o **VS Code** e o **Cursor** como um **thin client MCP** leve.

---

## Arquitetura: Thin Client Real via MCP

Em vez de duplicar modelos de prompt, analisadores de diff ou gestão de credenciais em TypeScript, a extensão comunica via `stdio` com o servidor local `gitpr-mcp` (`@modelcontextprotocol/sdk`):

- **Uma Sessão por Pasta do Workspace**: A extensão inicia o `gitpr-mcp` a pedido (lazy) no primeiro comando (com `cwd` a apontar para a raiz da pasta do workspace) e mantém a sessão persistente, reconectando automaticamente se o processo terminar.
- **Verificação de Contrato (Handshake)**: Ao ligar, a extensão invoca `listTools` e confirma que todas as tools obrigatórias (`get_git_context`, `generate_commit_message`, `review_code`, `full_review`, `generate_pr_description`, `run_check`, `publish_pull_request`) estão disponíveis. Se o seu `gitpr-cli` estiver desatualizado, apresenta um aviso de atualização (`pip install --upgrade gitpr-cli`).
- **Zero Configuração Paralela**: Chaves de API, tokens SCM e preferências permanecem em `~/.gitpr/.env` encriptados com Fernet. A extensão nunca pede nem guarda segredos.
- **Mascaramento de Segredos em Profundidade**: Tanto o servidor MCP em Python (`mask_sensitive_text`) como a extensão em TypeScript (`maskSensitiveText`) mascaram tokens (`ghp_*`, `glpat-*`, `sk-*`, `AIza*`, `Bearer *`, chaves privadas) antes de apresentar notificações ou escrever no OutputChannel `GitPR`.

---

## Instalação

### 1. Pré-requisito: `gitpr-cli`

Certifique-se de que o `gitpr-cli` está instalado e configurado na sua máquina:

```bash
pip install --upgrade gitpr-cli
gitpr --install
```

### 2. Instale a Extensão (VS Code & Cursor)

Tanto o VS Code como o Cursor partilham o mesmo pacote VSIX (`natanfiuza.gitpr`):

- **VS Code Marketplace**: Procure por `GitPR` (`natanfiuza.gitpr`).
- **Cursor / Open VSX**: Procure por `GitPR` ou instale a partir do ficheiro `.vsix`.
- **A partir do Código-Fonte (VSIX Local)**:
  ```bash
  cd extensions/vscode
  npm install
  npm run compile
  npm run package
  code --install-extension gitpr-0.1.0.vsix
  ```

---

## Comandos e Fluxos de Utilização

Todos os comandos estão disponíveis na **Command Palette** (`Ctrl+Shift+P` / `Cmd+Shift+P`), e os 4 atalhos principais (**Commit**, **Review**, **PR**, **Check**) ficam afixados na **Status Bar**.

| Comando | Tool MCP Invocada | Comportamento |
|---|---|---|
| `GitPR: Commit (Gerar Mensagem)` | `generate_commit_message` | Gera um rascunho Conventional Commits e preenche a caixa de mensagem do painel **Source Control** (com alternativa para copiar para a área de transferência). Nunca efetua commit automaticamente. |
| `GitPR: Review (Alterações Locais)` | `review_code(mentor=false)` | Revê alterações locais (`git diff HEAD`) e abre uma pré-visualização Markdown lado a lado. |
| `GitPR: Full Review (Contra Branch Base)` | `full_review(mentor=false)` | Executa `git fetch` e revê a branch inteira contra `origin/main`, abrindo pré-visualização Markdown. |
| `GitPR: Review (Modo Mentor Júnior)` | `review_code(mentor=true)` | Anexa explicações didáticas do Modo Mentor Júnior à pré-visualização da revisão de código. |
| `GitPR: Gerar Rascunho de PR` | `generate_pr_description(explain=false)` | Abre um documento Markdown editável de rascunho de PR (`linha 1` = título, restante = corpo). |
| `GitPR: Gerar Rascunho de PR (com Guia do Revisor)` | `generate_pr_description(explain=true)` | Gera o rascunho editável de PR incluindo a secção **Explain my PR** (Guia do Revisor). |
| `GitPR: Publicar PR a partir do Rascunho Ativo` | `publish_pull_request` | Lê o rascunho Markdown editado ativo, pede confirmação modal (`Publicar` ou `Publicar como Rascunho`) e cria o PR na forja configurada (GitHub, GitLab, Bitbucket, Azure DevOps). |
| `GitPR: Check (Diagnósticos Unificados de Linter e Segurança)` | `run_check` | Executa o pipeline unificado de verificação e preenche o painel **Problems** com diagnósticos clicáveis por ficheiro, linha e severidade. |

### Publicação de Pull Request em Dois Passos

A publicação nunca ocorre às cegas:
1. Execute **`GitPR: Gerar Rascunho de PR`** (ou **`Gerar Rascunho de PR (com Guia do Revisor)`**).
2. Reveja e edite o documento Markdown aberto. A primeira linha não vazia é usada como título do Pull Request e o restante como corpo.
3. Clique no botão **`Publicar PR`** na barra superior do editor (ou execute **`GitPR: Publicar PR a partir do Rascunho Ativo`**).
4. Confirme na janela modal. O servidor devolve estados estruturados:
   - `needs_push` → disponibiliza o botão **Push e Publicar** via `vscode.git`.
   - `already_exists` → disponibiliza abrir o PR existente no navegador.
   - `auth_required` → disponibiliza abrir um terminal a executar `gitpr` para autenticar.
   - `success` → disponibiliza abrir o PR recém-criado no navegador.

---

## Definições da Extensão

Configure no `settings.json` do VS Code / Cursor:

```json
{
  "gitpr.mcpCommand": "gitpr-mcp",
  "gitpr.mcpArgs": [],
  "gitpr.provider": "",
  "gitpr.check.useAI": false
}
```

| Definição | Tipo | Predefinição | Descrição |
|---|---|---|---|
| `gitpr.mcpCommand` | `string` | `"gitpr-mcp"` | Executável usado para iniciar o servidor MCP do GitPR. |
| `gitpr.mcpArgs` | `string[]` | `[]` | Argumentos adicionais passados ao executável do servidor MCP. |
| `gitpr.provider` | `string` | `""` | Substituição opcional do fornecedor de IA (`gemini`, `deepseek`, `ollama`). Vazio herda de `~/.gitpr/.env`. |
| `gitpr.check.useAI` | `boolean` | `false` | Ativa revisão por IA dentro do `GitPR: Check`. Desativado por predefinição para manter verificações no editor rápidas e sem consumo de tokens. |

---

## Internacionalização (i18n) e Telemetria

- **Idiomas da Interface**: Empacotada com traduções `en`, `pt-br`, `es` e `fr` (`package.nls.*.json` e `l10n/bundle.l10n.*.json`). Nota: o VS Code não disponibiliza um pacote de idioma `pt-pt` separado; utilizadores de Português (Portugal) recebem a interface `pt-br` no editor, enquanto todo o conteúdo gerado pelo servidor respeita `GITPR_LANG=pt_pt`.
- **Apenas Telemetria Local**: A extensão não emite telemetria externa nem abre ligações de rede. O servidor MCP local regista os eventos `mcp:check` e `mcp:publish_pr` no ledger SQLite local (`~/.gitpr/metrics/telemetry.db`).
