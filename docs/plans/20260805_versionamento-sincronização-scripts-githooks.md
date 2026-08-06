# Versionamento e Sincronização de Scripts Git Hooks

`20260805_versionamento-sincronização-scripts-githooks.md`

## **Contexto**
O sistema `gitpr` gerencia hooks do Git através de scripts localizados em `scripts/`. Atualmente, não há um controle de versão ou sincronização automatizada desses scripts, o que pode levar a inconsistências entre diferentes ambientes e execuções.

### **Objetivo Geral**
Implementar um sistema robusto de **versionamento e sincronização automática** dos scripts de hooks do Git, garantindo que todos os projetos utilizem a versão mais recente e no idioma correto, com suporte a múltiplos idiomas.

---

## **Tarefas Detalhadas**

### **1. Versionamento Centralizado**
**Arquivo:** `src/updater.py`
- Criar a variável:
  ```python
  __scripts_version__ = 'v0.0.1'
  ```
- Esta variável será a **fonte única de verdade** para a versão atual dos scripts.
- Sempre que os scripts forem atualizados, esta versão deve ser incrementada seguindo [Semantic Versioning](https://semver.org/).

---

### **2. Controle de Versão por Ambiente**
**Arquivo:** `~/.gitpr/.env`
- Criar/adicionar a variável:
  ```bash
  SCRIPTS_VERSION='v0.0.1'
  ```
- Esta variável armazena a versão dos scripts **instalados localmente**.
- Será usada para comparar com `__scripts_version__` e determinar se há necessidade de atualização.

---

### **3. Verificação de Hooks Instalados**
**Local:** Diretório `.git/hooks/` do projeto onde o `gitpr` foi executado

- Verificar a existência dos seguintes arquivos:
  - `pre-push`
  - `prepare-commit-msg`
  - `pre-commit`
  - `post-merge`
  - `post-checkout`

- **Para cada hook encontrado:**
  - Comparar a versão atual com `SCRIPTS_VERSION` do `.env`
  - Se `SCRIPTS_VERSION` for **diferente** ou **não existir** → atualizar o script com a nova versão.

---

### **4. Internacionalização (i18n) dos Scripts**
**Diretório:** `scripts/`

- **Idioma padrão:** Inglês (en) - arquivo base
- **Idiomas suportados:**
  - Português do Brasil (`pt_br`)
  - Português de Portugal (`pt_pt`)
  - Francês (`fr`)
  - Espanhol (`es`)

**Estrutura de nomenclatura:**
```
scripts/
├── pre-commit-template.sh          # Inglês (padrão)
├── pre-commit-template.pt_br.sh    # Português Brasil
├── pre-commit-template.pt_pt.sh    # Português Portugal
├── pre-commit-template.fr.sh       # Francês
├── pre-commit-template.es.sh       # Espanhol
├── pre-push-template.sh
├── pre-push-template.pt_br.sh
├── prepare-commit-msg-template.sh
├── prepare-commit-msg-template.pt_br.sh
└── ...
```

**Requisitos de tradução:**
- Traduzir **todas as mensagens** exibidas ao usuário
- Traduzir **todos os comentários** dentro dos scripts
- Manter a **lógica do script idêntica** em todas as versões
- Usar a **variável de ambiente `LANG`** ou `GITPR_LANG` para determinar o idioma a ser instalado

---

### **5. Atualização Automática na Execução do gitpr**

**Fluxo a ser implementado:**

```
1. gitpr é executado
2. Verificar ~/.gitpr/.env → obter SCRIPTS_VERSION
3. Comparar com __scripts_version__ em src/updater.py
4. Se versões diferentes:
   a. Determinar idioma atual (LANG ou GITPR_LANG)
   b. Baixar/copiar os scripts correspondentes ao idioma
   c. Atualizar os hooks em .git/hooks/
   d. Atualizar SCRIPTS_VERSION no .env
5. Prosseguir com a execução normal do gitpr
```

---

#### **6. Integração com install_git_hooks()**
**Arquivo:** `src/core.py`

- Modificar a função `install_git_hooks()` para:
  1. **Suportar i18n** na instalação inicial
  2. **Baixar a versão correta** do script baseado no idioma
  3. **Registrar a versão** no `.env` do usuário


---

## **Critérios de Aceite**
- [ ] `__scripts_version__` criado em `src/updater.py` com valor `v0.0.1`
- [ ] `SCRIPTS_VERSION` criado em `~/.gitpr/.env`
- [ ] Verificação automática de versão em todas as execuções do `gitpr`
- [ ] Atualização automática dos hooks quando versão difere
- [ ] Todos os scripts traduzidos para os 5 idiomas suportados
- [ ] Estrutura de diretórios organizada com sufixos de idioma
- [ ] `install_git_hooks()` com suporte a i18n
- [ ] Fallback para inglês quando idioma não disponível
- [ ] Mensagens de log informando sobre atualizações

---

## **Exemplo de Saída Esperada**
```
🔍 Verificando versão dos scripts...
   Atual: v0.0.0 (do .env)
   Última: v0.0.1 (do código)
📦 Atualizando scripts para v0.0.1...
   Idioma detectado: pt_br
   ✅ pre-push atualizado
   ✅ prepare-commit-msg atualizado
   ✅ pre-commit atualizado
   ✅ post-merge atualizado
   ✅ post-checkout atualizado
💾 SCRIPTS_VERSION atualizado no ~/.gitpr/.env
✅ Scripts sincronizados com sucesso!
```

---

## **Notas Técnicas**

- Mantenha compatibilidade com sistemas que não têm o `.env` (criar automaticamente)
- Adicione testes unitários para verificar a lógica de versão
- Documente o processo de tradução para novos idiomas no `README.md`