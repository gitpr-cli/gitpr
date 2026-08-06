# Remover conteúdo de arquivos de documentação em git diff

`20260805_remover_conteudo_arquivos_documentacao_gitdiff.md`

## **Contexto**

Atualmente, ao executar um `git diff` no projeto, utilizamos o seguinte comando:, com algumas variações, mas deveriam utilizar o SMART_EXCLUDES:
```python
cmd = ["git", "diff", "-U1", "-w", "-M", "-B", ancestor_hash, "--"] + SMART_EXCLUDES
```

## **Objetivos**
1. **Garantir consistência** – Verificar se o `SMART_EXCLUDES` está sendo aplicado em **todos** os prompts que utilizam `git diff`. Caso contrário, aplicar imediatamente.
2. **Criar novo arquivo de exclusão para documentação** – Baseado no modelo `templates\gitpr.smart-excludes.json`, criar um novo arquivo chamado `gitpr.docs-smart-excludes.json`, contendo uma lista de extensões de arquivos de texto comuns usados como documentação (ex.: `.md`, `.txt`, `.rst`, etc.).
3. **Incorporar ao SMART_EXCLUDES principal** – Adicionar as extensões definidas no novo arquivo ao `SMART_EXCLUDES` global, para que **arquivos de documentação não sejam incluídos no conteúdo do `git diff`**, reduzindo ruído e tokens.
4. **Gerar lista de documentação separada** – Executar o comando:
   ```bash
   git diff --name-only <ancestor_hash> -- <caminhos>
   ```
   Filtrar apenas os arquivos cujas extensões estejam em `docs-smart-excludes` e **incluir essa lista nos prompts como metadado**, sem expor o conteúdo completo, apenas indicando quais arquivos de documentação foram alterados.

---

## **Ações Práticas**

### **1. Verificação e Aplicação do SMART_EXCLUDES**
- Faça uma varredura em todos os prompts que invocam `git diff`.
- Verifique se a lista a seguir existe em `templates\gitpr.smart-excludes.json`:
  ```json
  ["*.lock", "*.log", "*.tmp", "*.min.js", "*.map", "*.png", "*.jpg", "*.ico", "*.svg"]
  ```
- Certifique-se de que a variável `SMART_EXCLUDES` esteja definida centralmente e seja reutilizada, e tem um fallback.

### **2. Criação do Arquivo `gitpr.docs-smart-excludes.json`**
- Localize o arquivo `templates\gitpr.smart-excludes.json` como base.
- Crie uma nova lista com extensões típicas de documentação em texto:
  ```json
  [".md", ".txt", ".rst", ".adoc", ".org", ".textile", ".wiki", ".pod", ".tex", ".rtf"]
  ```
- Faça um busca por mais extensões de texto utilizadas como documentação, e adicione a lista.  
- Salve como `gitpr.docs-smart-excludes.json`.

### **3. Atualização do SMART_EXCLUDES Principal**
- Leia o conteúdo de `gitpr.docs-smart-excludes.json`.
- Mescle com o `SMART_EXCLUDES` existente, garantindo que as extensões de documentação sejam **excluídas do diff**.
- Atualize a variável global `SMART_EXCLUDES` com a nova lista.

### **4. Geração da Lista de Documentação Alterada**
- Execute:
  ```bash
  git diff --name-only <ancestor_hash> -- <caminhos>
  ```
- Filtre os resultados pelas extensões contidas em `docs-smart-excludes`.
- Injete essa lista nos prompts (acho melhor injetar em system_instructions pois não precisaria alterar os arquivos de prompt que já foram salvos em /.gitpr/skill ) da seguinte forma:
  ```
  Documentação alterada (sem conteúdo):
  - docs/README.md
  - docs/guide.rst
  ```
- Isso permite que o gitpr saiba quais documentos foram modificados, sem consumir tokens com seu conteúdo completo.

---

## **Resultado Esperado**
- Redução significativa no uso de tokens em `git diff`.
- Manutenção da rastreabilidade sobre quais arquivos de documentação foram alterados.
- Padronização do uso de `SMART_EXCLUDES` em todos os prompts.
- Estrutura reutilizável e escalável para futuras exclusões.

---

## **Notas Adicionais**
- Caso o projeto use outros formatos de documentação (ex.: `.asciidoc`, `.rest`), adicione-os à lista.
- O arquivo `gitpr.docs-smart-excludes.json` pode ser versionado e compartilhado com a equipe.
- Considere criar um script auxiliar para validar se as extensões estão sendo corretamente ignoradas.
