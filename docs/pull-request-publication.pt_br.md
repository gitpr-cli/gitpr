# Documentação Técnica: Publicação de PR no GitHub

Esta documentação descreve o fluxo de publicação de Pull Requests via interface interativa de terminal (TUI), permitindo revisar, editar e publicar Pull Requests diretamente no GitHub sem sair do terminal.

---

## 1. O que é o Publicador de PR?

Quando você executa o comando `gitpr` (comportamento padrão), o GitPR gera a descrição do PR com IA, salva o arquivo `.md` localmente e abre um painel interativo diretamente no terminal. Isso permite revisar, editar e publicar o Pull Request gerado pela Inteligência Artificial antes de enviá-lo ao repositório remoto via API REST.

---

## 2. Fluxo Completo de Execução

```
gitpr
  ├─ Banner
  ├─ Verificação de arquivos unstaged (antes da geração do PR)
  │   ├─ GITPR_SKIP_UNSTAGED_CHECK=true → pular
  │   ├─ Sem arquivos unstaged → prosseguir
  │   ├─ GITPR_AUTO_STAGE=true → git add automático → prosseguir
  │   └─ Há arquivos unstaged → TUI StageFilesApp
  │       ├─ [Stage Selected] → git add → prosseguir
  │       ├─ [Skip] → prosseguir (sem stage)
  │       └─ [Cancel] → abortar
  ├─ Geração do PR (IA) → arquivo .md salvo em .gitpr/reports/pr_desc/
  └─ TUI (padrão) ou --no-publish / --no-edit
      └─ F3 Publicar PR → auto-commit (sem verificação duplicada de unstaged)
          ├─ Commit → git push → verificação de PR
          │   ├─ Sem PR existente → POST criar PR
          │   └─ PR existente encontrado → PATCH atualizar PR
          └─ Prompt de merge (se GITPR_AUTO_MERGE não estiver definido)
```

---

## 3. Modos de Execução

O Publicador de PR possui **3 modos de execução**, acionados por flags (ou pela ausência delas).

### 3.1 Modo Interativo (Padrão) — `gitpr`

Executar `gitpr` sem nenhuma flag gera a descrição do PR e abre a TUI para revisão e edição antes de publicar.

```bash
gitpr
```

| Característica | Descrição |
|---|---|
| **Fluxo** | Verificação de unstaged → `git fetch` → IA gera o PR → `.md` salvo → TUI abre → usuário edita → POST no GitHub |
| **Quando usar** | Fluxo de trabalho padrão — controle total sobre o que será publicado |
| **Resultado** | Pull Request criado no GitHub com o conteúdo editado |
| **Ideal para** | Desenvolvimento do dia a dia — revisar e ajustar o conteúdo do PR antes de publicar |

> **Dica:** O arquivo `.md` local é salvo antes de a TUI abrir e re-salvo com quaisquer edições antes de publicar. Você sempre tem um backup.

---

### 3.2 Pular Publicador — `gitpr --no-publish`

Gera o PR e salva localmente sem abrir o editor interativo.

```bash
gitpr --no-publish
```

| Característica | Descrição |
|---|---|
| **Fluxo** | Verificação de unstaged → `git fetch` → IA gera o PR → `.md` salvo → sair |
| **Quando usar** | Quando você só precisa do arquivo de descrição do PR para documentação ou revisão posterior |
| **Resultado** | Arquivo Markdown salvo localmente; nenhuma TUI abre |
| **Ideal para** | Documentação, revisão offline, salvar rascunhos de PR para depois |

---

### 3.3 Publicação Direta — `gitpr --no-edit`

Pula o editor interativo, faz auto-commit das alterações pendentes com validação do linter, faz push para o remoto e publica diretamente no GitHub.

```bash
gitpr --no-edit
```

| Característica | Descrição |
|---|---|
| **Fluxo** | Verificação de unstaged → `git fetch` → IA gera o PR → `.md` salvo → auto-commit (linter + mensagem de commit com IA) → git push → POST direto no GitHub |
| **Quando usar** | Quando você confia na saída da IA e quer publicar imediatamente |
| **Resultado** | Pull Request criado no GitHub sem abrir a TUI |
| **Ideal para** | Pipelines de CI/CD, correções rápidas, fluxos de trabalho automatizados |

> **Atenção:** Use com cuidado — você não terá a chance de revisar ou editar o conteúdo antes de publicar.

---

## 4. Gerenciamento de Arquivos Unstaged

Antes do início da geração do PR, o GitPR verifica se há arquivos unstaged e oferece uma interface modal para gerenciá-los. Essa verificação ocorre bem no início da execução do `gitpr`, antes de qualquer chamada de IA.

### 4.1 Fluxo da Verificação de Inicialização

```
gitpr inicia
  ├─ GITPR_SKIP_UNSTAGED_CHECK=true → pular a verificação inteira, prosseguir
  ├─ Nenhum arquivo unstaged detectado → prosseguir
  ├─ GITPR_AUTO_STAGE=true → git add automático de tudo → prosseguir
  └─ Arquivos unstaged encontrados → TUI StageFilesApp abre
      ├─ [Stage Selected] → git add <selecionados> → prosseguir
      ├─ [Skip] → prosseguir sem fazer stage
      └─ [Cancel] → abortar (sair sem gerar o PR)
```

### 4.2 Detecção de Arquivos

Os arquivos unstaged são detectados via `git status --porcelain`, procurando por:
- `??` — arquivos não rastreados (untracked)
- ` M` — modificados, mas não em stage (alterações na working tree)
- ` D` — deletados, mas não em stage

### 4.3 Variáveis de Ambiente

| Variável | Padrão | Descrição |
|---|---|---|
| `GITPR_SKIP_UNSTAGED_CHECK` | `false` | Defina como `true` para pular completamente a verificação de arquivos unstaged ao iniciar |
| `GITPR_AUTO_STAGE` | `false` | Defina como `true` para fazer stage automático de todos os arquivos unstaged sem mostrar o modal de seleção |

---

## 5. Fluxo de Auto-Commit (--no-edit e F3 na TUI)

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
   └─ Exibir a mensagem em um campo editável, solicitar confirmação
   └─ Opção de regenerar a mensagem

4. Executar: git commit -m "<mensagem>" [--no-verify]
   ├─ Sucesso → prosseguir com git push + publicação do PR
   └─ "Nothing to commit" → tratado como sucesso, prosseguir para a publicação
```

### 5.1 Tratamento de "Nothing to Commit"

Quando `git commit` retorna código diferente de zero, mas a saída indica que não há alterações reais, o fluxo trata isso como sucesso e continua. Os seguintes padrões são reconhecidos:

- `nothing to commit`
- `nothing added to commit`
- `no changes added to commit`
- `changes not staged`
- `working tree clean`
- `no changes`

### 5.2 Fluxograma de Decisão do Linter

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

### 5.3 Diálogos de Commit na TUI

O fluxo de auto-commit na TUI usa uma série de telas modais:

| Tela | Finalidade |
|---|---|
| `CommitConfirmScreen` | Confirmação antes de iniciar o fluxo de commit. Rótulos de botão personalizáveis para diferentes contextos |
| `FileStageScreen` | Lista de arquivos com alternância para `git add` seletivo antes do commit |
| `CommitProgressScreen` | Modal `RichLog` estilo terminal que isola os logs de commit da TUI principal |
| `CommitMessageScreen` | Mensagem de commit editável com botão "Regenerate" para regeneração da mensagem com IA |
| `LinterErrorScreen` | Exibe os erros do linter com opções para fazer commit com `--no-verify` ou abortar |
| `ErrorScreen` | Exibição genérica de erros com `max-height: 80%` e rolagem para saídas de erro grandes |

---

## 6. Git Push e Tratamento de PR Existente

Após um commit bem-sucedido, o GitPR faz push da branch e verifica se já existem PRs.

### 6.1 Fluxo de Push

```
git push origin <branch>
  ├─ Sucesso → verificar PRs existentes
  └─ Falha com "upstream" / "no upstream" no erro
      └─ Nova tentativa automática: git push --set-upstream origin <branch>
```

### 6.2 Detecção de PR Existente

Antes de criar um novo PR, o GitPR verifica se já existe um PR para a branch atual:

```
Verificar PRs existentes (GET /repos/{owner}/{repo}/pulls?head={branch})
  ├─ Sem PR existente → POST criar novo PR
  └─ PR existente encontrado
      ├─ Usuário escolhe "Push to existing PR" → PATCH atualizar corpo do PR
      └─ Usuário escolhe "Create new PR" → POST criar novo PR
```

### 6.3 Atualização do PR

Ao fazer push para um PR existente, o GitPR atualiza apenas o corpo (descrição) do PR via `PATCH /repos/{owner}/{repo}/pulls/{number}`. O título do PR permanece inalterado. O conteúdo enviado é apenas o campo Body do PR da TUI — nenhum wrapper ou prefixo de mensagem de commit é adicionado.

---

## 7. Fluxo de Merge

Após um PR ser criado ou atualizado, o GitPR pode mesclá-lo opcionalmente.

```
PR criado/atualizado com sucesso
  ├─ GITPR_AUTO_MERGE=true → merge automático via PUT /repos/{owner}/{repo}/pulls/{number}/merge
  ├─ GITPR_AUTO_MERGE=false → perguntar ao usuário se deseja mesclar
  └─ Usuário recusa → sair com a URL do PR exibida
```

| Variável | Padrão | Descrição |
|---|---|---|
| `GITPR_AUTO_MERGE` | `false` | Defina como `true` para mesclar PRs automaticamente após a criação/atualização sem perguntar |

---

## 8. Estrutura do Diretório de Saída

Por padrão, o GitPR salva todos os arquivos de saída no diretório `.gitpr/reports/`, organizado por tipo de artefato:

| Env var | Subpasta em `.gitpr/reports/` |
|---------|-------------------------------|
| `OUTPUT_FILE_NAME` | `pr_desc` |
| `OUTPUT_FILE_NAME_REVIEW` | `review` |
| `OUTPUT_FILE_NAME_FULLREVIEW` | `full_review` |
| `OUTPUT_FILE_NAME_FILEREVIEW` | `file_review` |
| `OUTPUT_FILE_NAME_BLAME` | `blame` |
| `OUTPUT_FILE_NAME_ISSUE` | `issue` |

### 8.1 Regras de Resolução de Caminho

A função `resolve_output_path()` em `src/core.py` lida com três cenários:

1. **Env var contém um separador de diretório** (`/` ou `\`) → usada como está (caminho customizado)
2. **Env var contém apenas um nome de arquivo** → salvo em `.gitpr/reports/{pasta}/`
3. **Env var está vazia/padrão** → usa o padrão de nome em `.gitpr/reports/{pasta}/`

Os diretórios são criados automaticamente via `os.makedirs(exist_ok=True)`. Isso garante total compatibilidade retroativa — usuários com caminhos de diretório customizados no `.env` mantêm o comportamento existente.

---

## 9. Configuração da Branch Base

A branch de destino do Pull Request é resolvida na seguinte ordem de prioridade:

| Prioridade | Origem | Como configurar |
|---|---|---|
| **1 (maior)** | flag `--base` | `gitpr --base develop` |
| **2** | env `PR_DEFAULT_BASE` | `PR_DEFAULT_BASE=develop` em `~/.gitpr/.env` |
| **3 (padrão)** | Detecção automática | `git symbolic-ref refs/remotes/origin/HEAD` (geralmente `main` ou `master`) |

---

## 10. Atalhos e Navegação na TUI

A interface foi projetada para ser rápida e dispensar o uso constante do mouse. Você pode navegar pelos campos usando a tecla `Tab` e utilizar os seguintes atalhos:

| Tecla | Ação | Descrição |
|---|---|---|
| **`F1`** | Ajuda | Abre um modal flutuante com instruções rápidas de uso da interface |
| **`F2`** | Salvar `.md` Local | Salva o conteúdo atualizado no arquivo de descrição do PR no projeto atual. Ideal para quando você quiser refinar o conteúdo posteriormente |
| **`F3`** | Publicar PR | Executa auto-commit (linter + mensagem com IA + stage de arquivos, se necessário) se houver alterações pendentes e, em seguida, cria ou atualiza o Pull Request no GitHub via API. O link direto para o PR será exibido no terminal |
| **`Esc`** | Sair | Aborta a operação e fecha a interface sem publicar |
| **`Tab`** | Navegar | Alterna o foco entre os campos da interface |

---

## 11. Integração com o GitHub (Token PAT)

Para criar Pull Requests diretamente no repositório remoto (`F3`), o GitPR precisa de um **Personal Access Token (PAT)** do GitHub com escopo `repo`.

### 11.1 Configuração do Token

Na primeira vez que você usar `F3` ou `--no-edit`, o GitPR irá:

1. Detectar que nenhum token está configurado
2. Exibir a URL de geração do token com os parâmetros pré-preenchidos (escopo `repo`)
3. Solicitar que você cole o token gerado
4. Armazená-lo criptografado (Fernet) no arquivo `~/.gitpr/.env`

> **Nota:** A TUI de Issues (`gitpr -is`) compartilha o mesmo token. Se você já configurou um token para Issues, ele será reutilizado automaticamente.

### 11.2 Segurança

- O token é armazenado como hash criptografado — nunca em texto plano
- A chave mestra de descriptografia está localizada em `~/.gitpr/secret.key`
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

> **Nota:** Apenas o conteúdo do campo Body do PR é enviado como `body` — nenhum wrapper ou prefixo de mensagem de commit é incluído.

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
| Branch não encontrada (422) | Exibe a mensagem de erro do GitHub com detalhes |
| Sem commits para mesclar (422) | Exibe erro de validação sugerindo fazer alterações primeiro |
| PR já existente (422) | Exibe o conflito específico; na TUI, oferece a opção de fazer push para o PR existente |
| Erros do linter | Pergunta ao usuário: fazer commit com `--no-verify` ou abortar |
| Falha no commit ("nothing to commit") | Tratada como sucesso — o fluxo continua para a publicação |
| Falha no commit (outros) | Exibe o erro e permite tentar novamente ou cancelar |
| Falha no push (sem upstream) | Nova tentativa automática com `--set-upstream origin <branch>` |
| Falha no push (outros) | Exibe a mensagem de erro com detalhes |
| Falha de rede | Exibe a mensagem de erro de conexão |
| Remote ausente | Erro antes de a TUI abrir — nenhuma chamada de API é tentada |

---

## 14. Variáveis de Ambiente

| Variável | Padrão | Descrição |
|---|---|---|
| `GITHUB_TOKEN_ENCRYPTED` | *(nenhum)* | Token de Acesso Pessoal do GitHub criptografado |
| `PR_DEFAULT_BASE` | *(vazio)* | Branch de destino padrão (usa detecção automática quando vazio) |
| `GITPR_AUTO_COMMIT` | `false` | Defina como `true` para executar commits sem pedir confirmação |
| `GITPR_SKIP_LINT` | `false` | Defina como `true` para pular a validação do linter durante o auto-commit |
| `GITPR_AUTO_STAGE` | `false` | Defina como `true` para fazer stage automático de todos os arquivos unstaged sem mostrar o modal de seleção |
| `GITPR_SKIP_UNSTAGED_CHECK` | `false` | Defina como `true` para pular completamente a verificação de arquivos unstaged ao iniciar |
| `GITPR_SHOW_LOGS` | `true` | Defina como `false` para ocultar os logs de progresso de commit/push na TUI |
| `GITPR_AUTO_MERGE` | `false` | Defina como `true` para mesclar PRs automaticamente após a criação/atualização sem perguntar |
| `OUTPUT_FILE_NAME` | `{branch}_{datetime}_PR_DESC.md` | Padrão de nome de arquivo para descrições de PR |
| `OUTPUT_FILE_NAME_REVIEW` | `{branch}_{datetime}_PR_REVIEW.txt` | Padrão de nome de arquivo para code reviews |
| `OUTPUT_FILE_NAME_FULLREVIEW` | `{branch}_{datetime}_PR_FULLREVIEW.txt` | Padrão de nome de arquivo para revisões completas |
| `OUTPUT_FILE_NAME_FILEREVIEW` | `{branch}_{datetime}_FILE_REVIEW.txt` | Padrão de nome de arquivo para revisões de arquivo |
| `OUTPUT_FILE_NAME_BLAME` | `{branch}_{datetime}_BLAME_REPORT.md` | Padrão de nome de arquivo para relatórios de blame |
| `OUTPUT_FILE_NAME_ISSUE` | `{branch}_{datetime}_ISSUE.md` | Padrão de nome de arquivo para issues |

---

## 15. Exemplos Práticos

### Exemplo 1: Fluxo de trabalho padrão — revisar e publicar

```bash
# Você terminou o desenvolvimento na branch feature/login
gitpr
# → Verificação de arquivos unstaged (se houver)
# → A IA gera a descrição do PR e abre a TUI
# → Revise o título, o corpo e a branch base
# → Pressione F3 para fazer auto-commit e criar o PR no GitHub
```

### Exemplo 2: Publicação rápida sem edição

```bash
gitpr --no-edit
# → Verificação de arquivos unstaged (se houver)
# → A IA gera o PR, faz auto-commit das alterações, faz push e publica imediatamente
# → A URL do PR é exibida no terminal
```

### Exemplo 3: Salvar apenas o arquivo do PR localmente

```bash
gitpr --no-publish
# → A IA gera a descrição do PR, salva o arquivo .md em .gitpr/reports/pr_desc/ e sai
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
# → O auto-commit pula o lint, gera a mensagem, faz o commit, faz push e publica
```

### Exemplo 6: Auto-commit sem confirmação

```bash
GITPR_AUTO_COMMIT=true gitpr --no-edit
# → A mensagem de commit é gerada e executada sem pedir confirmação
```

### Exemplo 7: Pular a verificação de arquivos unstaged

```bash
GITPR_SKIP_UNSTAGED_CHECK=true gitpr --no-edit
# → Pula o modal de arquivos unstaged da inicialização por completo
```

### Exemplo 8: Auto-stage e auto-merge

```bash
GITPR_AUTO_STAGE=true GITPR_AUTO_MERGE=true gitpr --no-edit
# → Todos os arquivos unstaged são colocados em stage automaticamente
# → O PR é mesclado automaticamente após a criação
```

### Exemplo 9: Diretório de saída customizado

```bash
# Em ~/.gitpr/.env:
OUTPUT_FILE_NAME=/home/user/prs/my_custom_pr.md
# → Descrição do PR salva em /home/user/prs/my_custom_pr.md
# → Caminhos de diretório nas env vars são usados como estão, nunca redirecionados para .gitpr/reports/
```

---

## 16. Arquivos Relacionados

| Arquivo | Função |
|---|---|
| `.gitpr.pr.md` | Template local com regras customizadas para geração da descrição do PR (baixe com `gitpr -s`) |
| `~/.gitpr/.env` | Configuração global: chaves de API, padrões de PR e token do GitHub criptografado |
| `~/.gitpr/secret.key` | Chave mestra Fernet para descriptografia das credenciais |
| `.gitpr/reports/pr_desc/` | Diretório de saída padrão para arquivos de descrição de PR |
| `.gitpr/reports/review/` | Diretório de saída padrão para arquivos de code review |
| `.gitpr/reports/full_review/` | Diretório de saída padrão para arquivos de revisão completa |

> **Nota:** Consulte também a [documentação principal (README.md)](../README.md) para uma visão geral de todos os recursos do GitPR e o [guia de Descrição de PR](pr-descricao-padrao.md) para o fluxo padrão de geração de PR.
