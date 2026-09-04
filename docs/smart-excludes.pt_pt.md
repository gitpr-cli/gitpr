# 🎯 Smart Excludes — Otimização de Tokens

Se já alguma vez viu o GitPR reduzir automaticamente o seu diff antes de o enviar para a IA, é o **Smart Excludes** a trabalhar. Esta página explica o que é, como funciona e como pode personalizá-lo para o seu projeto.

## 🔍 O que é o Smart Excludes?

O Smart Excludes é um sistema de otimização de tokens que **remove automaticamente ficheiros que não são código** do seu `git diff` antes de o enviar para a análise da IA. Ao eliminar lockfiles, assets minificados, ficheiros binários e textos de documentação, a IA recebe um diff mais limpo e mais relevante — o que significa:

- **Menor consumo de tokens** (e custos de API mais baixos)
- **Respostas da IA mais rápidas** (menos texto para processar)
- **Análise de maior qualidade** (a IA concentra-se no código, não no ruído)

## ⚙️ Como Funciona

O GitPR utiliza a sintaxe nativa de **exclusão por pathspec** do Git (`:(exclude)*.md`) para filtrar ficheiros do diff. Isto acontece ao nível do comando `git diff`, antes de qualquer texto chegar à IA — por isso, os ficheiros excluídos nunca consomem um único token.

O sistema tem **duas camadas** de exclusões:

### 1. Exclusões Centrais (Ruído)
Controladas por [`templates/gitpr.smart-excludes.json`](https://github.com/gitpr-cli/gitpr.git/blob/main/templates/gitpr.smart-excludes.json):

- **Lockfiles:** `package-lock.json`, `yarn.lock`, `Cargo.lock`, `Pipfile.lock`, `uv.lock`, etc.
- **Assets minificados:** `*.min.js`, `*.min.css`, `*.bundle.js`
- **Ficheiros gerados:** `*.map`, `*.pyc`, `*.log`
- **Ficheiros do sistema operativo:** `.DS_Store`, `Thumbs.db`

### 2. Exclusões de Documentação (Texto)
Controladas por [`templates/gitpr.docs-smart-excludes.json`](https://github.com/gitpr-cli/gitpr.git/blob/main/templates/gitpr.docs-smart-excludes.json):

- **Markup/texto:** `.md`, `.txt`, `.rst`, `.adoc`, `.asciidoc`, `.org`, `.textile`, `.wiki`
- **Escrita académica/técnica:** `.tex`, `.rtf`, `.pod`, `.rdoc`
- **Markdown alargado:** `.mdx`, `.markdown`, `.rest`
- **Páginas de manual:** `.man`, `.1`–`.8`

As duas listas são **fundidas em tempo de execução** numa única variável `SMART_EXCLUDES`, que é anexada a todos os comandos `git diff` executados pelo GitPR.

## 📋 Metadados de Documentação (Documentos Alterados Sem Conteúdo)

Excluir a documentação do diff poupa tokens, mas continua a querer saber _quais_ documentos foram modificados. O GitPR resolve isto executando um comando leve em separado:

```bash
git diff --name-only <ref> -- <doc-paths>
```

Este filtra a saída pelas extensões de documentação acima e **injeta a lista de ficheiros como metadados** nas instruções de sistema da IA:

```
Changed documentation (content excluded from diff):
- docs/README.md
- CHANGELOG.md
- guides/setup.rst
```

Desta forma, a IA sabe quais documentos foram alterados — um contexto útil para mensagens de commit e descrições de PR — sem consumir tokens com o conteúdo integral dos textos.

## 📁 Ficheiros de Configuração

| Ficheiro | Finalidade | Gerido por |
|------|---------|---------|
| `templates/gitpr.smart-excludes.json` | Exclusões centrais (lockfiles, binários, minificados) | Remoto (GitHub) |
| `templates/gitpr.docs-smart-excludes.json` | Extensões de documentação | Remoto (GitHub) |
| `~/.gitpr/conf/gitpr.smart-excludes.json` | Cache local das exclusões centrais | Descarregamento automático |
| `~/.gitpr/conf/gitpr.docs-smart-excludes.json` | Cache local das exclusões de documentação | Descarregamento automático |
| `./.gitpr/conf/gitpr.smart-excludes.json` | Exclusões **específicas do projeto** (opcional) | Criado pelo utilizador (versionável) |

Ambos os templates remotos são **versionados** — o GitPR volta a descarregá-los automaticamente quando é publicada uma nova versão (acionado pelo marcador `__lang_version__`). Nunca precisa de atualizar estes ficheiros manualmente.

### Cadeia de Resolução

Ao iniciar, o GitPR carrega cada lista de exclusões através de uma cadeia de fallback:

1. **Cache global** — `~/.gitpr/conf/` (mais rápida, zero rede)
2. **Descarregamento remoto** — a partir do repositório oficial do GitHub (timeout: 3 segundos)
3. **Cópia global desatualizada** — utilizada quando a rede está indisponível
4. **Fallback integrado** — valores predefinidos embutidos no código (garante o funcionamento offline)
5. **Fusão local do projeto** — `.gitpr/conf/gitpr.smart-excludes.json` na raiz do projeto é carregado e **fundido** (união) com a lista global. Os itens no ficheiro local são aditivos — adicionam exclusões extra específicas do seu projeto

## 📊 Exemplo de Utilização

Considere uma branch em que alterou `src/auth.py`, `docs/README.md` e `package-lock.json`:

**Sem Smart Excludes** (todos os ficheiros no diff):
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

### Adicionar Novas Extensões

Para adicionar novos padrões de forma permanente, edite os ficheiros de template no [repositório do GitPR](https://github.com/gitpr-cli/gitpr.git):

1. Edite `templates/gitpr.smart-excludes.json` para ruído que não seja código
2. Edite `templates/gitpr.docs-smart-excludes.json` para extensões de documentação
3. Aumente `__lang_version__` em `src/updater.py`
4. Os novos padrões são propagados para todos os utilizadores na próxima execução

### Configuração Local do Projeto (Recomendado)

Cada projeto pode ter o seu próprio ficheiro Smart Excludes em `.gitpr/conf/gitpr.smart-excludes.json`. Este ficheiro é **fundido** com a lista global em tempo de execução — adiciona exclusões extras que se aplicam apenas ao seu projeto (ex: `dist/`, `node_modules/`, artefactos de build de frameworks específicos).

**Criando o ficheiro:**

O ficheiro é criado automaticamente na primeira vez que o GitPR descarrega a lista global do Smart Excludes. Também pode criá-lo manualmente:

```json
{
  "_comment": "Exclusões específicas do projeto. Fundido com a lista global em tempo de execução.",
  "excludes": [
    "dist/",
    "*.pyc",
    "build/"
  ]
}
```

**Porquê usar o ficheiro local em vez de editar a cache global?**

- A cache global (`~/.gitpr/conf/`) é substituída a cada atualização de versão
- O ficheiro local persiste independentemente e pode ser **versionado** no seu repositório
- Os membros da equipa recebem as mesmas exclusões específicas do projeto quando clonam o repositório

### Substituição Temporária

Pode editar diretamente os ficheiros em cache em `~/.gitpr/conf/`. Estas alterações persistem até ao próximo aumento de `__lang_version__`, altura em que a versão remota os substitui. Prefira o ficheiro local do projeto para exclusões permanentes.

### Desativar o Smart Excludes

Defina a variável de ambiente `GITPR_SKIP_SMART_EXCLUDES=1` para desativar toda a filtragem do Smart Excludes na sessão atual. Utilize com moderação — remove tanto as exclusões globais como as locais do projeto.

## ❓ FAQ

### Porque é que os ficheiros de documentação são excluídos do diff?

Os textos de documentação (READMEs, guias, CHANGELOGs) podem ter milhares de palavras. Incluí-los no prompt da IA consome tokens que seriam melhor utilizados na análise das alterações de código. A IA continua a receber os _nomes_ dos ficheiros como metadados, pelo que sabe quais documentos foram alterados.

### Como sei quais ficheiros de documentação foram alterados?

O GitPR injeta automaticamente a lista dos ficheiros de documentação alterados no contexto da IA. Também pode executar `git diff --name-only` por sua conta e filtrar pelas extensões listadas acima.

### Posso desativar o Smart Excludes por completo?

O Smart Excludes é uma otimização central, mas pode ser desativado definindo `GITPR_SKIP_SMART_EXCLUDES=1` no seu ambiente. Para um controlo mais refinado, utilize o ficheiro de configuração local do projeto (`.gitpr/conf/gitpr.smart-excludes.json`) para adicionar ou ajustar exclusões para o seu projeto sem desativar o sistema globalmente.

### Isto afeta o repositório git real?

Não. O Smart Excludes afeta apenas aquilo que o GitPR _lê_ do seu repositório. O seu `git diff` real, os commits e a working tree permanecem completamente inalterados.

### O que acontece ao Linter?

O linter estático (`.gitpr.linter.yml`) é executado no diff **depois** da filtragem do Smart Excludes. Os ficheiros de documentação não são analisados pelo linter.

---

📂 **Repositório:** [https://github.com/gitpr-cli/gitpr.git](https://github.com/gitpr-cli/gitpr.git)
🌐 **Website:** [gitpr.natanfiuza.dev.br](https://gitpr.natanfiuza.dev.br/)
