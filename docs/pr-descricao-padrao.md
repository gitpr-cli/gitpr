# Documentação Técnica: Geração de Pull Request (Modo Padrão)

Quando executado **sem flags**, o GitPR gera automaticamente uma descrição completa de Pull Request em Markdown, pronta para ser colada no GitHub, GitLab ou Bitbucket.

---

## 1. Uso

```bash
gitpr
```

---

## 2. Fluxo de Execução

```
git fetch → diff contra origin/main → IA → .md
```

1. **`git fetch`** — Sincroniza com o repositório remoto
2. **Diff** — Compara todas as alterações da branch atual contra `origin/main`
3. **IA** — Gera a mensagem de commit (Conventional Commits) e a descrição do PR
4. **Output** — Salva um arquivo `.md` na raiz do projeto

---

## 3. Output

O arquivo gerado (`{branch}_{datetime}_PR_DESC.md`) contém:

```markdown
# 🚀 Sugestão de Pull Request

**Commit Message Recomendada:**
feat: descricao curta da alteracao

---

## Descrição
...
## Alterações
...
## Impacto
...
```

---

## 4. Customização

### 4.1 Template de PR

O comportamento da IA pode ser customizado através do arquivo `.gitpr.pr.md`:

```bash
gitpr -s          # Baixa o template
# Edite .gitpr.pr.md com as secções obrigatórias da sua equipa
gitpr             # A IA seguirá o seu template
```

### 4.2 Nome do Arquivo de Saída

Configure a variável de ambiente `OUTPUT_FILE_NAME` no ficheiro `~/.gitpr/.env`:

```ini
OUTPUT_FILE_NAME=PR_{branch}_{datetime}.md
```

Variáveis disponíveis: `{branch}` (nome da branch atual) e `{datetime}` (timestamp `YYYYMMDDHHMMSS`).

---

## 5. Seleção de Provedor de IA

```bash
gitpr -p gemini       # Força Google Gemini
gitpr -p deepseek     # Força DeepSeek
```

Se nenhum provider for especificado, o GitPR usa o padrão definido na variável `DEFAULT_AI_PROVIDER` do `~/.gitpr/.env`.

---

## 6. Cache de Respostas

O GitPR gera um hash MD5 do diff + instruções da IA. Se executar `gitpr` novamente **sem alterar o código**, a resposta é devolvida do cache local em milissegundos, sem consumir cotas da API.

> **Nota:** Consulte também a [documentação principal (README.md)](../README.md) para visão geral de todas as funcionalidades.
