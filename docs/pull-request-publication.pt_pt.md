# Documentação Técnica: Publicação de PR no GitHub

Esta documentação descreve o fluxo de publicação de Pull Requests via interface interativa de terminal (TUI), permitindo rever, editar e publicar Pull Requests diretamente no GitHub sem sair do terminal.

---

## 1. O que é o Publicador de PR?

Quando executa o comando `gitpr` (comportamento predefinido), o GitPR gera a descrição do PR com IA, guarda o ficheiro `.md` localmente e abre um painel interativo diretamente no terminal. Isto permite rever, editar e publicar o Pull Request gerado pela Inteligência Artificial antes de o enviar para o repositório remoto via API REST.

---

## 2. Modos de Execução

O Publicador de PR possui **3 modos de execução**, acionados por opções (ou pela ausência delas).

### 2.1 Modo Interativo (Predefinido) — `gitpr`

Executar `gitpr` sem qualquer opção gera a descrição do PR e abre a TUI para revisão e edição antes de publicar.

```bash
gitpr
```

| Característica | Descrição |
|---|---|
| **Fluxo** | `git fetch` → IA gera o PR → `.md` guardado → a TUI abre → o utilizador edita → POST para o GitHub |
| **Quando usar** | Fluxo de trabalho padrão — controlo total sobre o que é publicado |
| **Resultado** | Pull Request criado no GitHub com o conteúdo editado |
| **Ideal para** | Desenvolvimento do dia a dia — rever e ajustar o conteúdo do PR antes de publicar |

> **Dica:** O ficheiro `.md` local é guardado antes de a TUI abrir e é guardado novamente com quaisquer edições antes de publicar. Tem sempre uma cópia de segurança.

---

### 2.2 Saltar o Publicador — `gitpr --no-publish`

Gera o PR e guarda-o localmente sem abrir o editor interativo.

```bash
gitpr --no-publish
```

| Característica | Descrição |
|---|---|
| **Fluxo** | `git fetch` → IA gera o PR → `.md` guardado → sair |
| **Quando usar** | Quando apenas precisa do ficheiro de descrição do PR para documentação ou revisão posterior |
| **Resultado** | Ficheiro Markdown guardado localmente; nenhuma TUI abre |
| **Ideal para** | Documentação, revisão offline, guardar rascunhos de PR para mais tarde |

---

### 2.3 Publicação Direta — `gitpr --no-edit`

Salta o editor interativo, faz commit automático das alterações pendentes com validação de lint e publica diretamente no GitHub.

```bash
gitpr --no-edit
```

| Característica | Descrição |
|---|---|
| **Fluxo** | `git fetch` → IA gera o PR → `.md` guardado → commit automático (lint + mensagem de commit com IA) → POST direto para o GitHub |
| **Quando usar** | Quando confia no resultado da IA e pretende publicar imediatamente |
| **Resultado** | Pull Request criado no GitHub sem abrir a TUI |
| **Ideal para** | Pipelines de CI/CD, correções rápidas, fluxos de trabalho automatizados |

> **Atenção:** Use com cuidado — não terá oportunidade de rever ou editar o conteúdo antes de publicar.

---

## 3. Fluxo de Commit Automático (--no-edit e F3 da TUI)

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
   └─ Display message, request confirmation
   
4. Execute: git commit -m "<message>" [--no-verify]
   └─ Proceed with PR publication
```

### Diagrama de Decisão do Linter

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

---

## 4. Configuração do Ramo de Base

O ramo de destino do Pull Request é determinado pela seguinte ordem de prioridade:

| Prioridade | Origem | Como configurar |
|---|---|---|
| **1 (mais alta)** | Opção `--base` | `gitpr --base develop` |
| **2** | Variável `PR_DEFAULT_BASE` | `PR_DEFAULT_BASE=develop` em `~/.gitpr/.env` |
| **3 (predefinido)** | Deteção automática | `git symbolic-ref refs/remotes/origin/HEAD` (geralmente `main` ou `master`) |

---

## 5. Atalhos e Navegação na TUI

A interface foi concebida para ser rápida e não exigir utilização constante do rato. Pode navegar pelos campos com a tecla `Tab` e utilizar os seguintes atalhos:

| Tecla | Ação | Descrição |
|---|---|---|
| **`F1`** | Ajuda | Abre um modal flutuante com instruções rápidas de utilização da interface |
| **`F2`** | Guardar `.md` local | Guarda o conteúdo atualizado no ficheiro de descrição do PR no projeto atual. Ideal quando pretender aperfeiçoar o conteúdo mais tarde |
| **`F3`** | Publicar PR | Executa commit automático (lint + mensagem de IA) se houver alterações pendentes e, em seguida, cria o Pull Request no GitHub via API. O link direto para o PR recém-criado será apresentado no terminal |
| **`Esc`** | Sair | Aborta a operação e fecha a interface sem publicar |
| **`Tab`** | Navegar | Alterna o foco entre os campos da interface |

---

## 6. Integração com o GitHub (Token PAT)

Para criar Pull Requests diretamente no repositório remoto (`F3`), o GitPR precisa de um **Personal Access Token (PAT)** do GitHub com o âmbito `repo`.

### 6.1 Configuração do Token

Na primeira vez que utilizar `F3` ou `--no-edit`, o GitPR irá:

1. Detetar que nenhum token está configurado
2. Apresentar o URL de geração do token com parâmetros pré-preenchidos (âmbito `repo`)
3. Pedir-lhe que cole o token gerado
4. Guardá-lo encriptado (Fernet) no ficheiro `~/.gitpr/.env`

> **Nota:** A TUI de Issues (`gitpr -is`) partilha o mesmo token. Se já configurou um token para Issues, este será reutilizado automaticamente.

### 6.2 Segurança

- O token é guardado como um hash encriptado — nunca em texto simples
- A chave mestra de desencriptação está localizada em `~/.gitpr/secret.key`
- O token é validado via `GET /user` antes de a TUI abrir
- Consulte o guia completo em [github-pat-integration.md](github-pat-integration.md)

---

## 7. API do GitHub — Criação de PR

O PR é criado via `POST https://api.github.com/repos/{owner}/{repo}/pulls` com o seguinte payload:

```json
{
  "title": "PR title (editable in TUI)",
  "body": "Full markdown PR description with commit message",
  "head": "Current branch (source)",
  "base": "Target branch (main, develop, etc.)"
}
```

---

## 8. Tratamento de Erros

| Erro | Comportamento |
|---|---|
| Token inválido/expirado (401) | Solicita um novo token (até 3 tentativas) |
| Ramo não encontrado (422) | Apresenta a mensagem de erro do GitHub com detalhes |
| Sem commits para fundir (422) | Apresenta um erro de validação sugerindo fazer alterações primeiro |
| O PR já existe (422) | Apresenta o conflito específico |
| Erros de lint | Pergunta ao utilizador: fazer commit com `--no-verify` ou abortar |
| Falha no commit | Apresenta o erro e permite tentar novamente ou cancelar |
| Falha de rede | Apresenta a mensagem de erro de ligação |
| Remote em falta | Erro antes de a TUI abrir — nenhuma chamada à API é tentada |

---

## 9. Variáveis de Ambiente

| Variável | Predefinição | Descrição |
|---|---|---|
| `GITHUB_TOKEN_ENCRYPTED` | *(nenhum)* | Personal Access Token do GitHub encriptado |
| `PR_DEFAULT_BASE` | *(vazio)* | Ramo de destino predefinido (utiliza deteção automática quando vazio) |
| `GITPR_AUTO_COMMIT` | `false` | Defina como `true` para executar commits sem pedir confirmação |
| `GITPR_SKIP_LINT` | `false` | Defina como `true` para saltar a validação de lint durante o commit automático |
| `GITPR_AUTO_STAGE` | `false` | Defina como `true` para fazer stage automático de todos os ficheiros unstaged sem mostrar o modal de seleção |
| `GITPR_SKIP_UNSTAGED_CHECK` | `false` | Defina como `true` para saltar completamente a verificação de ficheiros unstaged ao iniciar |

---

## 10. Exemplos Práticos

### Exemplo 1: Fluxo de trabalho padrão — rever e publicar

```bash
# You finished developing on the feature/login branch
gitpr
# → AI generates the PR description and opens the TUI
# → Review the title, body, and base branch
# → Press F3 to auto-commit and create the PR on GitHub
```

### Exemplo 2: Publicação rápida sem edição

```bash
gitpr --no-edit
# → AI generates PR, auto-commits changes, and publishes immediately
# → The PR URL is displayed in the terminal
```

### Exemplo 3: Apenas guardar o ficheiro do PR localmente

```bash
gitpr --no-publish
# → AI generates PR description, saves .md file, exits
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
# → Auto-commit skips lint, generates message, commits, and publishes
```

### Exemplo 6: Commit automático sem confirmação

```bash
GITPR_AUTO_COMMIT=true gitpr --no-edit
# → Commit message is generated and executed without asking for confirmation
```

---

## 11. Ficheiros Relacionados

| Ficheiro | Função |
|---|---|
| `.gitpr.pr.md` | Template local com regras personalizadas para geração da descrição do PR (descarregue com `gitpr -s`) |
| `~/.gitpr/.env` | Configuração global: chaves de API, predefinições de PR e token do GitHub encriptado |
| `~/.gitpr/secret.key` | Chave mestra Fernet para desencriptação de credenciais |

> **Nota:** Consulte também a [documentação principal (README.md)](../README.md) para uma visão geral de todas as funcionalidades do GitPR e o [guia de Descrição de PR](pr-descricao-padrao.md) para o fluxo predefinido de geração de PR.
