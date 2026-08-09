# Documentação Técnica: Publicação de PR no GitHub

Esta documentação descreve o fluxo de publicação de Pull Requests via interface interativa de terminal (TUI), permitindo revisar, editar e publicar Pull Requests diretamente no GitHub sem sair do terminal.

---

## 1. O que é o Publicador de PR?

Quando você executa o comando `gitpr` (comportamento padrão), o GitPR gera a descrição do PR com IA, salva o arquivo `.md` localmente e abre um painel interativo diretamente no terminal. Isso permite revisar, editar e publicar o Pull Request gerado pela Inteligência Artificial antes de enviá-lo ao repositório remoto via API REST.

---

## 2. Modos de Execução

O Publicador de PR possui **3 modos de execução**, acionados por flags (ou pela ausência delas).

### 2.1 Modo Interativo (Padrão) — `gitpr`

Executar `gitpr` sem nenhuma flag gera a descrição do PR e abre a TUI para revisão e edição antes de publicar.

```bash
gitpr
```

| Característica | Descrição |
|---|---|
| **Fluxo** | `git fetch` → IA gera o PR → `.md` salvo → TUI abre → usuário edita → POST no GitHub |
| **Quando usar** | Fluxo de trabalho padrão — controle total sobre o que será publicado |
| **Resultado** | Pull Request criado no GitHub com o conteúdo editado |
| **Ideal para** | Desenvolvimento do dia a dia — revisar e ajustar o conteúdo do PR antes de publicar |

> **Dica:** O arquivo `.md` local é salvo antes de a TUI abrir e re-salvo com quaisquer edições antes de publicar. Você sempre tem um backup.

---

### 2.2 Pular Publicador — `gitpr --no-publish`

Gera o PR e salva localmente sem abrir o editor interativo.

```bash
gitpr --no-publish
```

| Característica | Descrição |
|---|---|
| **Fluxo** | `git fetch` → IA gera o PR → `.md` salvo → sair |
| **Quando usar** | Quando você só precisa do arquivo de descrição do PR para documentação ou revisão posterior |
| **Resultado** | Arquivo Markdown salvo localmente; nenhuma TUI abre |
| **Ideal para** | Documentação, revisão offline, salvar rascunhos de PR para depois |

---

### 2.3 Publicação Direta — `gitpr --no-edit`

Pula o editor interativo, faz auto-commit das alterações pendentes com validação do linter e publica diretamente no GitHub.

```bash
gitpr --no-edit
```

| Característica | Descrição |
|---|---|
| **Fluxo** | `git fetch` → IA gera o PR → `.md` salvo → auto-commit (linter + mensagem de commit com IA) → POST direto no GitHub |
| **Quando usar** | Quando você confia na saída da IA e quer publicar imediatamente |
| **Resultado** | Pull Request criado no GitHub sem abrir a TUI |
| **Ideal para** | Pipelines de CI/CD, correções rápidas, fluxos de trabalho automatizados |

> **Atenção:** Use com cuidado — você não terá a chance de revisar ou editar o conteúdo antes de publicar.

---

## 3. Fluxo de Auto-Commit (--no-edit e F3 na TUI)

Ao usar `--no-edit` ou pressionar `F3` na TUI com alterações não commitadas, o GitPR executa um fluxo de commit automático:

```
1. Verificar alterações não commitadas (git diff HEAD --stat)
   └─ Se limpo → pular commit, prosseguir para a publicação
   
2. Executar linter estático (regras do .gitpr.linter.yml)
   ├─ ✅ Aprovado → prosseguir
   ├─ ⚠️ Avisos → exibidos, prosseguir
   └─ 🚨 Erros:
        ├─ [Fazer commit com --no-verify] → prosseguir
        └─ [Abortar] → operação cancelada
   
3. Gerar mensagem de commit via IA (formato Conventional Commits)
   └─ Exibir a mensagem, solicitar confirmação
   
4. Executar: git commit -m "<mensagem>" [--no-verify]
   └─ Prosseguir com a publicação do PR
```

### Fluxograma de Decisão do Linter

```
Há alterações não commitadas?
├─ Não → Pular commit, publicar PR
└─ Sim
   └─ GITPR_SKIP_LINT=true?
      ├─ Sim → Ir para a mensagem de commit com IA
      └─ Não
         └─ Executar linter
            ├─ Sem erros → Ir para a mensagem de commit com IA
            └─ Com erros
               └─ Usuário confirma --no-verify?
                  ├─ Sim → Ir para a mensagem de commit com IA (com --no-verify)
                  └─ Não → Abortar
```

---

## 4. Configuração da Branch Base

A branch de destino do Pull Request é resolvida na seguinte ordem de prioridade:

| Prioridade | Origem | Como configurar |
|---|---|---|
| **1 (maior)** | flag `--base` | `gitpr --base develop` |
| **2** | env `PR_DEFAULT_BASE` | `PR_DEFAULT_BASE=develop` em `~/.gitpr/.env` |
| **3 (padrão)** | Detecção automática | `git symbolic-ref refs/remotes/origin/HEAD` (geralmente `main` ou `master`) |

---

## 5. Atalhos e Navegação na TUI

A interface foi projetada para ser rápida e dispensar o uso constante do mouse. Você pode navegar pelos campos usando a tecla `Tab` e utilizar os seguintes atalhos:

| Tecla | Ação | Descrição |
|---|---|---|
| **`F1`** | Ajuda | Abre um modal flutuante com instruções rápidas de uso da interface |
| **`F2`** | Salvar `.md` Local | Salva o conteúdo atualizado no arquivo de descrição do PR no projeto atual. Ideal para quando você quiser refinar o conteúdo posteriormente |
| **`F3`** | Publicar PR | Executa auto-commit (linter + mensagem com IA) se houver alterações pendentes e cria o Pull Request no GitHub via API. O link direto para o PR recém-criado será exibido no terminal |
| **`Esc`** | Sair | Aborta a operação e fecha a interface sem publicar |
| **`Tab`** | Navegar | Alterna o foco entre os campos da interface |

---

## 6. Integração com o GitHub (Token PAT)

Para criar Pull Requests diretamente no repositório remoto (`F3`), o GitPR precisa de um **Personal Access Token (PAT)** do GitHub com escopo `repo`.

### 6.1 Configuração do Token

Na primeira vez que você usar `F3` ou `--no-edit`, o GitPR irá:

1. Detectar que nenhum token está configurado
2. Exibir a URL de geração do token com os parâmetros pré-preenchidos (escopo `repo`)
3. Solicitar que você cole o token gerado
4. Armazená-lo criptografado (Fernet) no arquivo `~/.gitpr/.env`

> **Nota:** A TUI de Issues (`gitpr -is`) compartilha o mesmo token. Se você já configurou um token para Issues, ele será reutilizado automaticamente.

### 6.2 Segurança

- O token é armazenado como hash criptografado — nunca em texto plano
- A chave mestra de descriptografia está localizada em `~/.gitpr/secret.key`
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
| Branch não encontrada (422) | Exibe a mensagem de erro do GitHub com detalhes |
| Sem commits para mesclar (422) | Exibe erro de validação sugerindo fazer alterações primeiro |
| PR já existente (422) | Exibe o conflito específico |
| Erros do linter | Pergunta ao usuário: fazer commit com `--no-verify` ou abortar |
| Falha no commit | Exibe o erro e permite tentar novamente ou cancelar |
| Falha de rede | Exibe a mensagem de erro de conexão |
| Remote ausente | Erro antes de a TUI abrir — nenhuma chamada de API é tentada |

---

## 9. Variáveis de Ambiente

| Variável | Padrão | Descrição |
|---|---|---|
| `GITHUB_TOKEN_ENCRYPTED` | *(nenhum)* | Token de Acesso Pessoal do GitHub criptografado |
| `PR_DEFAULT_BASE` | *(vazio)* | Branch de destino padrão (usa detecção automática quando vazio) |
| `GITPR_AUTO_COMMIT` | `false` | Defina como `true` para executar commits sem pedir confirmação |
| `GITPR_SKIP_LINT` | `false` | Defina como `true` para pular a validação do linter durante o auto-commit |
| `GITPR_AUTO_STAGE` | `false` | Defina como `true` para fazer stage automático de todos os arquivos unstaged sem mostrar o modal de seleção |
| `GITPR_SKIP_UNSTAGED_CHECK` | `false` | Defina como `true` para pular completamente a verificação de arquivos unstaged ao iniciar |

---

## 10. Exemplos Práticos

### Exemplo 1: Fluxo de trabalho padrão — revisar e publicar

```bash
# Você terminou o desenvolvimento na branch feature/login
gitpr
# → A IA gera a descrição do PR e abre a TUI
# → Revise o título, o corpo e a branch base
# → Pressione F3 para fazer auto-commit e criar o PR no GitHub
```

### Exemplo 2: Publicação rápida sem edição

```bash
gitpr --no-edit
# → A IA gera o PR, faz auto-commit das alterações e publica imediatamente
# → A URL do PR é exibida no terminal
```

### Exemplo 3: Salvar apenas o arquivo do PR localmente

```bash
gitpr --no-publish
# → A IA gera a descrição do PR, salva o arquivo .md e sai
# → Sem TUI, sem publicação
```

### Exemplo 4: Publicar contra uma branch base customizada

```bash
gitpr --base staging
# → A branch de destino é definida como "staging" em vez de "main"
```

### Exemplo 5: Pular o linter no auto-commit

```bash
GITPR_SKIP_LINT=true gitpr --no-edit
# → O auto-commit pula o lint, gera a mensagem, faz o commit e publica
```

### Exemplo 6: Auto-commit sem confirmação

```bash
GITPR_AUTO_COMMIT=true gitpr --no-edit
# → A mensagem de commit é gerada e executada sem pedir confirmação
```

---

## 11. Arquivos Relacionados

| Arquivo | Função |
|---|---|
| `.gitpr.pr.md` | Template local com regras customizadas para geração da descrição do PR (baixe com `gitpr -s`) |
| `~/.gitpr/.env` | Configuração global: chaves de API, padrões de PR e token do GitHub criptografado |
| `~/.gitpr/secret.key` | Chave mestra Fernet para descriptografia das credenciais |

> **Nota:** Consulte também a [documentação principal (README.md)](../README.md) para uma visão geral de todos os recursos do GitPR e o [guia de Descrição de PR](pr-descricao-padrao.md) para o fluxo padrão de geração de PR.
