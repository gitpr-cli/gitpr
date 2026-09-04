# 🎯 Smart Excludes — Otimização de Tokens

Se você já viu o GitPR reduzir automaticamente o seu diff antes de enviá-lo para a IA, é o **Smart Excludes** em ação. Esta página explica o que é, como funciona e como você pode personalizá-lo para o seu projeto.

## 🔍 O que é o Smart Excludes?

O Smart Excludes é um sistema de otimização de tokens que **remove automaticamente arquivos não relacionados a código** do seu `git diff` antes de enviá-lo para a análise da IA. Ao eliminar lockfiles, assets minificados, arquivos binários e textos de documentação, a IA recebe um diff mais limpo e mais relevante — o que significa:

- **Menor consumo de tokens** (e menores custos de API)
- **Respostas de IA mais rápidas** (menos texto para processar)
- **Análise de maior qualidade** (a IA foca no código, não no ruído)

## ⚙️ Como Funciona

O GitPR usa a sintaxe nativa de **exclusão por pathspec** do Git (`:(exclude)*.md`) para filtrar arquivos do diff. Isso acontece no nível do comando `git diff`, antes que qualquer texto chegue à IA — portanto, os arquivos excluídos nunca consomem um único token.

O sistema possui **duas camadas** de exclusões:

### 1. Exclusões Centrais (Ruído)
Controladas por [`templates/gitpr.smart-excludes.json`](https://github.com/gitpr-cli/gitpr.git/blob/main/templates/gitpr.smart-excludes.json):

- **Lockfiles:** `package-lock.json`, `yarn.lock`, `Cargo.lock`, `Pipfile.lock`, `uv.lock`, etc.
- **Assets minificados:** `*.min.js`, `*.min.css`, `*.bundle.js`
- **Arquivos gerados:** `*.map`, `*.pyc`, `*.log`
- **Arquivos de sistema operacional:** `.DS_Store`, `Thumbs.db`

### 2. Exclusões de Documentação (Texto)
Controladas por [`templates/gitpr.docs-smart-excludes.json`](https://github.com/gitpr-cli/gitpr.git/blob/main/templates/gitpr.docs-smart-excludes.json):

- **Markup/texto:** `.md`, `.txt`, `.rst`, `.adoc`, `.asciidoc`, `.org`, `.textile`, `.wiki`
- **Escrita acadêmica/técnica:** `.tex`, `.rtf`, `.pod`, `.rdoc`
- **Markdown estendido:** `.mdx`, `.markdown`, `.rest`
- **Páginas man:** `.man`, `.1`–`.8`

As duas listas são **mescladas em tempo de execução** em uma única variável `SMART_EXCLUDES`, que é anexada a todo comando `git diff` executado pelo GitPR.

## 📋 Metadados de Documentação (Documentos Alterados Sem Conteúdo)

Excluir a documentação do diff economiza tokens, mas você ainda quer saber _quais_ documentos foram modificados. O GitPR resolve isso executando um comando leve separado:

```bash
git diff --name-only <ref> -- <doc-paths>
```

Ele filtra a saída pelas extensões de documentação acima e **injeta a lista de arquivos como metadados** nas instruções de sistema da IA:

```
Changed documentation (content excluded from diff):
- docs/README.md
- CHANGELOG.md
- guides/setup.rst
```

Dessa forma, a IA sabe quais documentos foram alterados — um contexto útil para mensagens de commit e descrições de PR — sem consumir tokens com o conteúdo completo dos textos.

## 📁 Arquivos de Configuração

| Arquivo | Finalidade | Gerenciado por |
|------|---------|---------|
| `templates/gitpr.smart-excludes.json` | Exclusões centrais (lockfiles, binários, minificados) | Remoto (GitHub) |
| `templates/gitpr.docs-smart-excludes.json` | Extensões de documentação | Remoto (GitHub) |
| `~/.gitpr/conf/gitpr.smart-excludes.json` | Cache local das exclusões centrais | Download automático |
| `~/.gitpr/conf/gitpr.docs-smart-excludes.json` | Cache local das exclusões de documentação | Download automático |
| `./.gitpr/conf/gitpr.smart-excludes.json` | Exclusões **específicas do projeto** (opcional) | Criado pelo usuário (versionável) |

Ambos os templates remotos são **versionados** — o GitPR os baixa novamente automaticamente quando uma nova versão é publicada (disparada pelo marcador `__lang_version__`). Você nunca precisa atualizar esses arquivos manualmente.

### Cadeia de Resolução

Ao iniciar, o GitPR carrega cada lista de exclusões por uma cadeia de fallback:

1. **Cache global** — `~/.gitpr/conf/` (mais rápido, zero rede)
2. **Download remoto** — do repositório oficial do GitHub (timeout: 3 segundos)
3. **Cópia global obsoleta** — usada quando a rede está indisponível
4. **Fallback embutido** — padrões hardcoded (garante funcionalidade offline)
5. **Mesclagem local do projeto** — `.gitpr/conf/gitpr.smart-excludes.json` na raiz do projeto é carregado e **mesclado** (união) com a lista global. Os itens no arquivo local são aditivos — adicionam exclusões extras específicas do seu projeto

## 📊 Exemplo de Uso

Considere uma branch em que você alterou `src/auth.py`, `docs/README.md` e `package-lock.json`:

**Sem Smart Excludes** (todos os arquivos no diff):
```diff
diff --git a/src/auth.py b/src/auth.py
+ def validate_token(token): ...
diff --git a/docs/README.md b/docs/README.md
+ ## New Section
+ This is a long documentation update with many paragraphs...
diff --git a/package-lock.json b/package-lock.json
+ 500 lines of dependency tree changes
```
→ ~600+ linhas enviadas à IA (~15.000 tokens)

**Com Smart Excludes** (apenas o código no diff):
```diff
diff --git a/src/auth.py b/src/auth.py
+ def validate_token(token): ...
```
→ ~10 linhas enviadas à IA (~250 tokens)

**Além dos metadados** injetados na instrução de sistema:
```
Changed documentation (content excluded from diff):
- docs/README.md
```

> **Resultado:** ~98% de redução de tokens neste cenário, com a IA ainda ciente de que a documentação foi atualizada.

## 🎨 Personalização

### Adicionando Novas Extensões

Para adicionar novos padrões permanentemente, edite os arquivos de template no [repositório do GitPR](https://github.com/gitpr-cli/gitpr.git):

1. Edite `templates/gitpr.smart-excludes.json` para ruídos não relacionados a código
2. Edite `templates/gitpr.docs-smart-excludes.json` para extensões de documentação
3. Aumente `__lang_version__` em `src/updater.py`
4. Os novos padrões são propagados para todos os usuários na próxima execução

### Configuração Local do Projeto (Recomendado)

Cada projeto pode ter seu próprio arquivo Smart Excludes em `.gitpr/conf/gitpr.smart-excludes.json`. Este arquivo é **mesclado** com a lista global em tempo de execução — adiciona exclusões extras que se aplicam apenas ao seu projeto (ex: `dist/`, `node_modules/`, artefatos de build de frameworks específicos).

**Criando o arquivo:**

O arquivo é criado automaticamente na primeira vez que o GitPR baixa a lista global do Smart Excludes. Você também pode criá-lo manualmente:

```json
{
  "_comment": "Exclusões específicas do projeto. Mesclado com a lista global em tempo de execução.",
  "excludes": [
    "dist/",
    "*.pyc",
    "build/"
  ]
}
```

**Por que usar o arquivo local em vez de editar o cache global?**

- O cache global (`~/.gitpr/conf/`) é sobrescrito a cada atualização de versão
- O arquivo local persiste independentemente e pode ser **versionado** no seu repositório
- Os membros da equipe recebem as mesmas exclusões específicas do projeto quando clonam o repositório

### Substituição Temporária

Você pode editar diretamente os arquivos em cache em `~/.gitpr/conf/`. Essas alterações persistem até o próximo aumento de `__lang_version__`, quando a versão remota os sobrescreve. Prefira o arquivo local do projeto para exclusões permanentes.

### Desabilitando o Smart Excludes

Defina a variável de ambiente `GITPR_SKIP_SMART_EXCLUDES=1` para desabilitar toda a filtragem do Smart Excludes na sessão atual. Use com moderação — remove tanto as exclusões globais quanto as locais do projeto.

## ❓ FAQ

### Por que os arquivos de documentação são excluídos do diff?

O texto de documentação (READMEs, guias, CHANGELOGs) pode ter milhares de palavras. Incluí-los no prompt da IA consome tokens que seriam melhor utilizados na análise das alterações de código. A IA ainda recebe os _nomes_ dos arquivos como metadados, então ela sabe quais documentos foram alterados.

### Como sei quais arquivos de documentação foram alterados?

O GitPR injeta automaticamente a lista de arquivos de documentação alterados no contexto da IA. Você também pode executar `git diff --name-only` por conta própria e filtrar pelas extensões listadas acima.

### Posso desabilitar o Smart Excludes completamente?

O Smart Excludes é uma otimização central, mas pode ser desabilitado definindo `GITPR_SKIP_SMART_EXCLUDES=1` no seu ambiente. Para um controle mais refinado, use o arquivo de configuração local do projeto (`.gitpr/conf/gitpr.smart-excludes.json`) para adicionar ou ajustar exclusões para o seu projeto sem desabilitar o sistema globalmente.

### Isso afeta o repositório git real?

Não. O Smart Excludes afeta apenas o que o GitPR _lê_ do seu repositório. O seu `git diff` real, os commits e a working tree permanecem completamente inalterados.

### O que acontece com o Linter?

O linter estático (`.gitpr.linter.yml`) é executado no diff **depois** da filtragem do Smart Excludes. Arquivos de documentação não são lintados.

---

📂 **Repositório:** [https://github.com/gitpr-cli/gitpr.git](https://github.com/gitpr-cli/gitpr.git)
🌐 **Site:** [gitpr.natanfiuza.dev.br](https://gitpr.natanfiuza.dev.br/)
