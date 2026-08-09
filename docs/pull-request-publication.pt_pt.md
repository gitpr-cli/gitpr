# Documentação Técnica: Publicação de PR no GitHub

Esta documentação descreve o fluxo de publicação de Pull Requests via interface interativa de terminal (TUI), permitindo rever, editar e publicar Pull Requests diretamente no GitHub sem sair do terminal.

---

## 1. O que é o Publicador de PR?

Quando executa o comando `gitpr` (comportamento predefinido), o GitPR gera a descrição do PR com IA, guarda o ficheiro `.md` localmente e abre um painel interativo diretamente no terminal. Isto permite rever, editar e publicar o Pull Request gerado pela Inteligência Artificial antes de o enviar para o repositório remoto via API REST.

---

## 2. Fluxo de Execução Completo

```
gitpr
  ├─ Banner
  ├─ Unstaged files check (before PR generation)
  │   ├─ GITPR_SKIP_UNSTAGED_CHECK=true → skip
  │   ├─ No unstaged files → proceed
  │   ├─ GITPR_AUTO_STAGE=true → auto git add → proceed
  │   └─ Has unstaged files → StageFilesApp TUI
  │       ├─ Stage Selected → git add → proceed
  │       ├─ Skip → proceed (no staging)
  │       └─ Cancel → abort
  ├─ PR generation (AI) → .md file saved to .gitpr/reports/pr_desc/
  └─ TUI (default) or --no-publish / --no-edit
      └─ F3 Publish PR → auto-commit (no duplicate unstaged check)
          ├─ Commit → git push → PR check
          │   ├─ No existing PR → POST create PR
          │   └─ Existing PR found → PATCH update PR
          └─ Merge prompt (if GITPR_AUTO_MERGE is not set)
```

---

## 3. Modos de Execução

O Publicador de PR possui **3 modos de execução**, acionados por opções (ou pela ausência delas).

### 3.1 Modo Interativo (Predefinido) — `gitpr`

Executar `gitpr` sem qualquer opção gera a descrição do PR e abre a TUI para revisão e edição antes de publicar.

```bash
gitpr
```

| Característica | Descrição |
|---|---|
| **Fluxo** | Verificação de unstaged → `git fetch` → IA gera o PR → `.md` guardado → a TUI abre → o utilizador edita → POST para o GitHub |
| **Quando usar** | Fluxo de trabalho padrão — controlo total sobre o que é publicado |
| **Resultado** | Pull Request criado no GitHub com o conteúdo editado |
| **Ideal para** | Desenvolvimento do dia a dia — rever e ajustar o conteúdo do PR antes de publicar |

> **Dica:** O ficheiro `.md` local é guardado antes de a TUI abrir e é guardado novamente com quaisquer edições antes de publicar. Tem sempre uma cópia de segurança.

---

### 3.2 Saltar o Publicador — `gitpr --no-publish`

Gera o PR e guarda-o localmente sem abrir o editor interativo.

```bash
gitpr --no-publish
```

| Característica | Descrição |
|---|---|
| **Fluxo** | Verificação de unstaged → `git fetch` → IA gera o PR → `.md` guardado → sair |
| **Quando usar** | Quando apenas precisa do ficheiro de descrição do PR para documentação ou revisão posterior |
| **Resultado** | Ficheiro Markdown guardado localmente; nenhuma TUI abre |
| **Ideal para** | Documentação, revisão offline, guardar rascunhos de PR para mais tarde |

---

### 3.3 Publicação Direta — `gitpr --no-edit`

Salta o editor interativo, faz commit automático das alterações pendentes com validação de lint, faz push para o remoto e publica diretamente no GitHub.

```bash
gitpr --no-edit
```

| Característica | Descrição |
|---|---|
| **Fluxo** | Verificação de unstaged → `git fetch` → IA gera o PR → `.md` guardado → commit automático (lint + mensagem de commit com IA) → `git push` → POST direto para o GitHub |
| **Quando usar** | Quando confia no resultado da IA e pretende publicar imediatamente |
| **Resultado** | Pull Request criado no GitHub sem abrir a TUI |
| **Ideal para** | Pipelines de CI/CD, correções rápidas, fluxos de trabalho automatizados |

> **Atenção:** Use com cuidado — não terá oportunidade de rever ou editar o conteúdo antes de publicar.

---

## 4. Gestão de Ficheiros Unstaged

Antes de a geração do PR começar, o GitPR verifica a existência de ficheiros unstaged e oferece uma interface modal para os gerir. Esta verificação é executada logo no início da execução de `gitpr`, antes de qualquer chamada de IA.

### 4.1 Fluxo da Verificação no Arranque

```
gitpr starts
  ├─ GITPR_SKIP_UNSTAGED_CHECK=true → skip entire check, proceed
  ├─ No unstaged files detected → proceed
  ├─ GITPR_AUTO_STAGE=true → auto git add all → proceed
  └─ Unstaged files found → StageFilesApp TUI opens
      ├─ [Stage Selected] → git add <selected> → proceed
      ├─ [Skip] → proceed without staging
      └─ [Cancel] → abort (exit without generating PR)
```

### 4.2 Deteção de Ficheiros

Os ficheiros unstaged são detetados via `git status --porcelain`, procurando por:
- `??` — ficheiros não rastreados (untracked)
- ` M` — modificados mas não stageados (alterações na working tree)
- ` D` — eliminados mas não stageados

### 4.3 Variáveis de Ambiente

| Variável | Predefinição | Descrição |
|---|---|---|
| `GITPR_SKIP_UNSTAGED_CHECK` | `false` | Defina como `true` para saltar completamente a verificação de ficheiros unstaged ao iniciar |
| `GITPR_AUTO_STAGE` | `false` | Defina como `true` para fazer stage automático de todos os ficheiros unstaged sem mostrar o modal de seleção |

---

## 5. Fluxo de Commit Automático (--no-edit e F3 da TUI)

Ao utilizar `--no-edit` ou ao premir `F3` na TUI com alterações não commitadas, o GitPR executa um fluxo de commit automático:

```
1. Check for uncommitted changes (git diff HEAD --stat)
   └─ If clean → skip commit, proceed to publish

2. Run static linter (.gitpr.linter.yml rules)
   ├─ ✅ Pass → proceed
   ├─ ⚠️ Warnings → shown, proceed
   └─ 🚨 Errors:
        ├─ [Commit with --no-verify] → proceed
        └─ [Abort] → operation cancelled

3. Generate commit message via AI (Conventional Commits format)
   └─ Display message in editable field, request confirmation
   └─ Option to regenerate the message

4. Execute: git commit -m "<message>" [--no-verify]
   ├─ Success → proceed with git push + PR publication
   └─ "Nothing to commit" → treated as success, proceed to publish
```

### 5.1 Tratamento de «Nothing to Commit»

Quando `git commit` devolve um código diferente de zero, mas o resultado indica que não existem alterações reais, o fluxo trata isto como um sucesso e continua. São reconhecidos os seguintes padrões:

- `nothing to commit`
- `nothing added to commit`
- `no changes added to commit`
- `changes not staged`
- `working tree clean`
- `no changes`

### 5.2 Diagrama de Decisão do Linter

```
Has uncommitted changes?
├─ No → Skip commit, publish PR
└─ Yes
   └─ GITPR_SKIP_LINT=true?
      ├─ Yes → Skip to AI commit message
      └─ No
         └─ Run linter
            ├─ No errors → Skip to AI commit message
            └─ Has errors
               └─ User confirms --no-verify?
                  ├─ Yes → Skip to AI commit message (with --no-verify)
                  └─ No → Abort
```

### 5.3 Diálogos de Commit na TUI

O fluxo de commit automático na TUI utiliza uma série de ecrãs modais:

| Ecrã | Finalidade |
|---|---|
| `CommitConfirmScreen` | Confirmação antes de iniciar o fluxo de commit. Rótulos de botão personalizáveis para diferentes contextos |
| `FileStageScreen` | Lista de ficheiros alternável para `git add` seletivo antes do commit |
| `CommitProgressScreen` | Modal `RichLog` semelhante a um terminal que isola os logs de commit da TUI principal |
| `CommitMessageScreen` | Mensagem de commit editável com botão «Regenerate» para regenerar a mensagem gerada por IA |
| `LinterErrorScreen` | Mostra os erros de lint com opções para fazer commit com `--no-verify` ou abortar |
| `ErrorScreen` | Apresentação genérica de erros com `max-height: 80%` e scroll para resultados de erro extensos |

---

## 6. Git Push e Tratamento de PRs Existentes

Após um commit bem-sucedido, o GitPR faz push do ramo e verifica a existência de PRs.

### 6.1 Fluxo de Push

```
git push origin <branch>
  ├─ Success → check for existing PRs
  └─ Failure with "upstream" / "no upstream" in error
      └─ Auto-retry: git push --set-upstream origin <branch>
```

### 6.2 Deteção de PR Existente

Antes de criar um novo PR, o GitPR verifica se já existe um PR para o ramo atual:

```
Check existing PRs (GET /repos/{owner}/{repo}/pulls?head={branch})
  ├─ No existing PR → POST create new PR
  └─ Existing PR found
      ├─ User chooses "Push to existing PR" → PATCH update PR body
      └─ User chooses "Create new PR" → POST create new PR
```

### 6.3 Atualização do PR

Ao fazer push para um PR existente, o GitPR atualiza apenas o body (descrição) do PR via `PATCH /repos/{owner}/{repo}/pulls/{number}`. O título do PR permanece inalterado. O conteúdo enviado é apenas o campo PR Body da TUI — sem wrapper nem prefixo de mensagem de commit adicionados.

---

## 7. Fluxo de Merge

Depois de um PR ser criado ou atualizado, o GitPR pode, opcionalmente, fundi-lo.

```
PR created/updated successfully
  ├─ GITPR_AUTO_MERGE=true → auto-merge via PUT /repos/{owner}/{repo}/pulls/{number}/merge
  ├─ GITPR_AUTO_MERGE=false → prompt user to merge
  └─ User declines → exit with PR URL displayed
```

| Variável | Predefinição | Descrição |
|---|---|---|
| `GITPR_AUTO_MERGE` | `false` | Defina como `true` para fundir automaticamente os PRs após a criação/atualização sem pedir confirmação |

---

## 8. Estrutura do Diretório de Saída

Por predefinição, o GitPR guarda todos os ficheiros de saída no diretório `.gitpr/reports/`, organizados por tipo de artefacto:

| Variável de ambiente | Subpasta em `.gitpr/reports/` |
|---------|-------------------------------|
| `OUTPUT_FILE_NAME` | `pr_desc` |
| `OUTPUT_FILE_NAME_REVIEW` | `review` |
| `OUTPUT_FILE_NAME_FULLREVIEW` | `full_review` |
| `OUTPUT_FILE_NAME_FILEREVIEW` | `file_review` |
| `OUTPUT_FILE_NAME_BLAME` | `blame` |
| `OUTPUT_FILE_NAME_ISSUE` | `issue` |

### 8.1 Regras de Resolução do Caminho

A função `resolve_output_path()` em `src/core.py` trata três cenários:

1. **A variável de ambiente contém um separador de diretório** (`/` ou `\`) → utilizada como está (caminho personalizado)
2. **A variável de ambiente contém apenas um nome de ficheiro** → guardado em `.gitpr/reports/{folder}/`
3. **A variável de ambiente está vazia/predefinida** → utiliza o padrão predefinido em `.gitpr/reports/{folder}/`

Os diretórios são criados automaticamente via `os.makedirs(exist_ok=True)`. Isto garante total retrocompatibilidade — utilizadores com caminhos de diretório personalizados no `.env` mantêm o comportamento existente.

---

## 9. Configuração do Ramo de Base

O ramo de destino do Pull Request é determinado pela seguinte ordem de prioridade:

| Prioridade | Origem | Como configurar |
|---|---|---|
| **1 (mais alta)** | Opção `--base` | `gitpr --base develop` |
| **2** | Variável `PR_DEFAULT_BASE` | `PR_DEFAULT_BASE=develop` em `~/.gitpr/.env` |
| **3 (predefinido)** | Deteção automática | `git symbolic-ref refs/remotes/origin/HEAD` (geralmente `main` ou `master`) |

---

## 10. Atalhos e Navegação na TUI

A interface foi concebida para ser rápida e não exigir utilização constante do rato. Pode navegar pelos campos com a tecla `Tab` e utilizar os seguintes atalhos:

| Tecla | Ação | Descrição |
|---|---|---|
| **`F1`** | Ajuda | Abre um modal flutuante com instruções rápidas de utilização da interface |
| **`F2`** | Guardar `.md` local | Guarda o conteúdo atualizado no ficheiro de descrição do PR no projeto atual. Ideal quando pretender aperfeiçoar o conteúdo mais tarde |
| **`F3`** | Publicar PR | Executa o commit automático (lint + mensagem de IA + stage de ficheiros, se necessário) se houver alterações pendentes e, em seguida, cria ou atualiza o Pull Request no GitHub via API. O link direto para o PR será apresentado no terminal |
| **`Esc`** | Sair | Aborta a operação e fecha a interface sem publicar |
| **`Tab`** | Navegar | Alterna o foco entre os campos da interface |

---

## 11. Integração com o GitHub (Token PAT)

Para criar Pull Requests diretamente no repositório remoto (`F3`), o GitPR precisa de um **Personal Access Token (PAT)** do GitHub com o âmbito `repo`.

### 11.1 Configuração do Token

Na primeira vez que utilizar `F3` ou `--no-edit`, o GitPR irá:

1. Detetar que nenhum token está configurado
2. Apresentar o URL de geração do token com parâmetros pré-preenchidos (âmbito `repo`)
3. Pedir-lhe que cole o token gerado
4. Guardá-lo encriptado (Fernet) no ficheiro `~/.gitpr/.env`

> **Nota:** A TUI de Issues (`gitpr -is`) partilha o mesmo token. Se já configurou um token para Issues, este será reutilizado automaticamente.

### 11.2 Segurança

- O token é guardado como um hash encriptado — nunca em texto simples
- A chave mestra de desencriptação está localizada em `~/.gitpr/secret.key`
- O token é validado via `GET /user` antes de a TUI abrir
- Consulte o guia completo em [github-pat-integration.md](github-pat-integration.md)

---

## 12. Referência da API do GitHub

### 12.1 Criação de PR

`POST https://api.github.com/repos/{owner}/{repo}/pulls`

```json
{
  "title": "PR title (editable in TUI)",
  "body": "PR body content from the TUI text area",
  "head": "Current branch (source)",
  "base": "Target branch (main, develop, etc.)"
}
```

> **Nota:** Apenas o conteúdo do campo PR Body é enviado como `body` — sem wrapper nem prefixo de mensagem de commit.

### 12.2 Atualização de PR (PR Existente)

`PATCH https://api.github.com/repos/{owner}/{repo}/pulls/{number}`

```json
{
  "body": "Updated PR body content from the TUI text area"
}
```

### 12.3 Merge de PR

`PUT https://api.github.com/repos/{owner}/{repo}/pulls/{number}/merge`

```json
{
  "merge_method": "merge"
}
```

---

## 13. Tratamento de Erros

| Erro | Comportamento |
|---|---|
| Token inválido/expirado (401) | Solicita um novo token (até 3 tentativas) |
| Ramo não encontrado (422) | Apresenta a mensagem de erro do GitHub com detalhes |
| Sem commits para fundir (422) | Apresenta um erro de validação sugerindo fazer alterações primeiro |
| O PR já existe (422) | Apresenta o conflito específico; na TUI, oferece a opção de fazer push para o PR existente |
| Erros de lint | Pergunta ao utilizador: fazer commit com `--no-verify` ou abortar |
| Falha no commit («nothing to commit») | Tratada como sucesso — o fluxo continua para a publicação |
| Falha no commit (outros) | Apresenta o erro e permite tentar novamente ou cancelar |
| Falha no push (sem upstream) | Tentativa automática com `--set-upstream origin <branch>` |
| Falha no push (outros) | Apresenta a mensagem de erro com detalhes |
| Falha de rede | Apresenta a mensagem de erro de ligação |
| Remote em falta | Erro antes de a TUI abrir — nenhuma chamada à API é tentada |

---

## 14. Variáveis de Ambiente

| Variável | Predefinição | Descrição |
|---|---|---|
| `GITHUB_TOKEN_ENCRYPTED` | *(nenhum)* | Personal Access Token do GitHub encriptado |
| `PR_DEFAULT_BASE` | *(vazio)* | Ramo de destino predefinido (utiliza deteção automática quando vazio) |
| `GITPR_AUTO_COMMIT` | `false` | Defina como `true` para executar commits sem pedir confirmação |
| `GITPR_SKIP_LINT` | `false` | Defina como `true` para saltar a validação de lint durante o commit automático |
| `GITPR_AUTO_STAGE` | `false` | Defina como `true` para fazer stage automático de todos os ficheiros unstaged sem mostrar o modal de seleção |
| `GITPR_SKIP_UNSTAGED_CHECK` | `false` | Defina como `true` para saltar completamente a verificação de ficheiros unstaged ao iniciar |
| `GITPR_SHOW_LOGS` | `true` | Defina como `false` para ocultar os logs de progresso de commit/push na TUI |
| `GITPR_AUTO_MERGE` | `false` | Defina como `true` para fundir automaticamente os PRs após a criação/atualização sem pedir confirmação |
| `OUTPUT_FILE_NAME` | `{branch}_{datetime}_PR_DESC.md` | Padrão de nome de ficheiro predefinido para descrições de PR |
| `OUTPUT_FILE_NAME_REVIEW` | `{branch}_{datetime}_PR_REVIEW.txt` | Padrão de nome de ficheiro predefinido para code reviews |
| `OUTPUT_FILE_NAME_FULLREVIEW` | `{branch}_{datetime}_PR_FULLREVIEW.txt` | Padrão de nome de ficheiro predefinido para revisões completas |
| `OUTPUT_FILE_NAME_FILEREVIEW` | `{branch}_{datetime}_FILE_REVIEW.txt` | Padrão de nome de ficheiro predefinido para revisões de ficheiro |
| `OUTPUT_FILE_NAME_BLAME` | `{branch}_{datetime}_BLAME_REPORT.md` | Padrão de nome de ficheiro predefinido para relatórios de blame |
| `OUTPUT_FILE_NAME_ISSUE` | `{branch}_{datetime}_ISSUE.md` | Padrão de nome de ficheiro predefinido para issues |

---

## 15. Exemplos Práticos

### Exemplo 1: Fluxo de trabalho padrão — rever e publicar

```bash
# You finished developing on the feature/login branch
gitpr
# → Unstaged files check (if any)
# → AI generates the PR description and opens the TUI
# → Review the title, body, and base branch
# → Press F3 to auto-commit and create the PR on GitHub
```

### Exemplo 2: Publicação rápida sem edição

```bash
gitpr --no-edit
# → Unstaged files check (if any)
# → AI generates PR, auto-commits changes, pushes, and publishes immediately
# → The PR URL is displayed in the terminal
```

### Exemplo 3: Apenas guardar o ficheiro do PR localmente

```bash
gitpr --no-publish
# → AI generates PR description, saves .md file to .gitpr/reports/pr_desc/, exits
# → No TUI, no publication
```

### Exemplo 4: Publicar para um ramo de base personalizado

```bash
gitpr --base staging
# → Target branch is set to "staging" instead of "main"
```

### Exemplo 5: Saltar o linter no commit automático

```bash
GITPR_SKIP_LINT=true gitpr --no-edit
# → Auto-commit skips lint, generates message, commits, pushes, and publishes
```

### Exemplo 6: Commit automático sem confirmação

```bash
GITPR_AUTO_COMMIT=true gitpr --no-edit
# → Commit message is generated and executed without asking for confirmation
```

### Exemplo 7: Saltar a verificação de ficheiros unstaged

```bash
GITPR_SKIP_UNSTAGED_CHECK=true gitpr --no-edit
# → Skips the startup unstaged files modal entirely
```

### Exemplo 8: Stage automático e merge automático

```bash
GITPR_AUTO_STAGE=true GITPR_AUTO_MERGE=true gitpr --no-edit
# → All unstaged files are automatically staged
# → PR is automatically merged after creation
```

### Exemplo 9: Diretório de saída personalizado

```bash
# In ~/.gitpr/.env:
OUTPUT_FILE_NAME=/home/user/prs/my_custom_pr.md
# → PR description saved to /home/user/prs/my_custom_pr.md
# → Directory paths in env vars are used as-is, never redirected to .gitpr/reports/
```

---

## 16. Ficheiros Relacionados

| Ficheiro | Função |
|---|---|
| `.gitpr.pr.md` | Template local com regras personalizadas para geração da descrição do PR (descarregue com `gitpr -s`) |
| `~/.gitpr/.env` | Configuração global: chaves de API, predefinições de PR e token do GitHub encriptado |
| `~/.gitpr/secret.key` | Chave mestra Fernet para desencriptação de credenciais |
| `.gitpr/reports/pr_desc/` | Diretório de saída predefinido para ficheiros de descrição de PR |
| `.gitpr/reports/review/` | Diretório de saída predefinido para ficheiros de code review |
| `.gitpr/reports/full_review/` | Diretório de saída predefinido para ficheiros de revisão completa |

> **Nota:** Consulte também a [documentação principal (README.md)](../README.md) para uma visão geral de todas as funcionalidades do GitPR e o [guia de Descrição de PR](pr-descricao-padrao.md) para o fluxo predefinido de geração de PR.
