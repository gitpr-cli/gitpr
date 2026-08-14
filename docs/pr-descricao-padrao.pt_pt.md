# Documentação Técnica: Geração de Pull Request (Modo Padrão)

Quando executado **sem flags**, o GitPR gera uma descrição completa de Pull Request em Markdown com IA — pronta para ser colada no GitHub, GitLab ou Bitbucket — e abre um painel interativo (TUI) para rever, editar e publicar o PR diretamente no GitHub sem sair do terminal.

---

## 1. Uso

```bash
gitpr
```

| Modo | Comando | Comportamento |
|---|---|---|
| Interativo (padrão) | `gitpr` | Gera o PR e abre a TUI para rever e publicar |
| Apenas guardar | `gitpr --no-publish` | Gera o PR e guarda o ficheiro `.md` localmente |
| Publicação direta | `gitpr --no-edit` | Gera o PR, faz auto-commit, push e publica sem abrir a TUI |

---

## 2. Fluxo de Execução

```
verificação de ficheiros unstaged → git fetch → diff contra origin/main → IA → .md → TUI → publicar
```

1. **Verificação de ficheiros unstaged** — Deteta ficheiros não commitados e oferece stage (stage, saltar ou cancelar)
2. **`git fetch`** — Sincroniza com o repositório remoto
3. **Diff** — Compara todas as alterações da branch atual contra `origin/main`
4. **IA** — Gera a mensagem de commit (Conventional Commits) e a descrição do PR
5. **Output** — Guarda um ficheiro `.md` em `.gitpr/reports/pr_desc/`
6. **Publicar** — Abre a TUI (`F3` = publicar) ou publica diretamente com `--no-edit`

---

## 3. Output

O ficheiro gerado (`{branch}_{datetime}_PR_DESC.md`) é guardado em `.gitpr/reports/pr_desc/` e contém:

```markdown
# 🚀 Pull Request Suggestion

**Recommended Commit Message:**
feat: short description of the change

---

## Description
...
## Changes
...
## Impact
...
```

---

## 4. Publicação do Pull Request

O publicador está disponível em 3 modos:

### 4.1 Modo Interativo (Padrão)

Executar `gitpr` abre a TUI após gerar a descrição. Atalhos:

| Tecla | Ação |
|---|---|
| **`F1`** | Ajuda |
| **`F2`** | Guarda o ficheiro `.md` localmente |
| **`F3`** | Publica o PR (auto-commit → push → cria/atualiza o PR no GitHub) |
| **`Esc`** | Sai sem publicar |

### 4.2 Apenas Guardar

```bash
gitpr --no-publish
```

Gera a descrição e guarda o ficheiro `.md` sem abrir a TUI.

### 4.3 Publicação Direta

```bash
gitpr --no-edit
```

Ignora a TUI: faz auto-commit das alterações pendentes (linter + mensagem de commit via IA), envia push e publica diretamente. Use com cuidado — o conteúdo não é revisto antes da publicação.

Para publicar, o GitPR necessita de um **Personal Access Token (PAT)** do GitHub com âmbito `repo`, armazenado encriptado em `~/.gitpr/.env`. A branch de destino é resolvida através da flag `--base` → env `PR_DEFAULT_BASE` → deteção automática.

> **Nota:** Consulte o [guia completo de publicação](pull-request-publication.md) para o fluxo detalhado (verificação de unstaged, auto-commit, merge, tratamento de erros).

---

## 5. Customização

### 5.1 Template de PR

O comportamento da IA pode ser customizado através do ficheiro `.gitpr.pr.md`:

```bash
gitpr -s          # Downloads the template
# Edit .gitpr.pr.md with your team's required sections
gitpr             # The AI will follow your template
```

### 5.2 Nome do Ficheiro de Saída

Configure a variável de ambiente `OUTPUT_FILE_NAME` no ficheiro `~/.gitpr/.env`:

```ini
OUTPUT_FILE_NAME=PR_{branch}_{datetime}.md
```

Variáveis disponíveis: `{branch}` (nome da branch atual) e `{datetime}` (timestamp `YYYYMMDDHHMMSS`).

---

## 6. Seleção de Provedor de IA

```bash
gitpr -p gemini       # Forces Google Gemini
gitpr -p deepseek     # Forces DeepSeek
```

Se nenhum provider for especificado, o GitPR usa o padrão definido na variável `DEFAULT_AI_PROVIDER` do `~/.gitpr/.env`.

---

## 7. Cache de Respostas

O GitPR gera um hash MD5 do diff + instruções da IA. Se executar `gitpr` novamente **sem alterar o código**, a resposta é devolvida do cache local em milissegundos, sem consumir quotas da API.

> **Nota:** Consulte também a [documentação principal (README.md)](../README.md) para visão geral de todas as funcionalidades.
