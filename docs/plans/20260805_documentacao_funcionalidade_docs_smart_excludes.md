# Documentação da Funcionalidade Docs Smart Excludes

`20260805_documentacao_funcionalidade_docs_smart_excludes.md`

---

## **Contexto**
Foi implementado um novo sistema de **Smart Excludes** para otimização de `git diff`, que exclui arquivos de documentação e outros arquivos não-código do diff para reduzir o uso de tokens. Esta funcionalidade está documentada no relatório `@docs/claude-code/reports/develop_natan/2026-08-05_docs_smart_excludes.md`. Agora é necessário **documentar essa funcionalidade** para os usuários e **integrar com o sistema de URLs** existente.

---

## **Objetivo Geral**
1. **Documentar a funcionalidade Smart Excludes** no README em todos os idiomas suportados
2. **Criar documentação técnica dedicada** no diretório `docs/` em todos os idiomas
3. **Integrar com `get_docs_url()`** para fornecer links diretos durante a execução do CLI

---

## **Tarefas Detalhadas**

### **1. Atualização dos READMEs**

**Arquivos a serem modificados/criados:**
- `README.md` (Inglês - padrão)
- `README.pt_br.md` (Português Brasil)
- `README.pt_pt.md` (Português Portugal)
- `README.fr.md` (Francês)
- `README.es.md` (Espanhol)

**Conteúdo a ser adicionado:**

- **Nova seção** sobre Smart Excludes, destacando:
  - O que é a funcionalidade e seu propósito
  - Como os arquivos de documentação são identificados e excluídos do diff
  - Benefícios: redução de tokens, desempenho otimizado, foco em código relevante
  - Como o sistema gerencia a lista de extensões excluídas
  - Como os usuários podem verificar quais arquivos de documentação foram alterados
  - Onde encontrar mais informações (link para documentação completa)

- **Exemplo prático** do comportamento esperado:
  - Comando executado
  - O que é excluído do diff
  - Como a lista de documentação alterada é exibida

- **Link para documentação completa** usando a URL gerada por `get_docs_url()`

---

### **2. Documentação Técnica em `docs/`**

**Arquivos a serem criados:**
- `docs/smart-excludes.md` (Inglês - padrão)
- `docs/smart-excludes.pt_br.md` (Português Brasil)
- `docs/smart-excludes.pt_pt.md` (Português Portugal)
- `docs/smart-excludes.fr.md` (Francês)
- `docs/smart-excludes.es.md` (Espanhol)

**Estrutura do documento:**

1. **Visão Geral** - Descrição da funcionalidade e seus objetivos

2. **Como Funciona** - Explicação técnica do mecanismo:
   - Uso de `SMART_EXCLUDES` nos comandos `git diff`
   - Criação e uso de `gitpr.docs-smart-excludes.json`
   - Extensões de documentação suportadas (`.md`, `.txt`, `.rst`, etc.)
   - Processo de geração da lista de documentação alterada

3. **Arquivos de Configuração** - Descrição dos arquivos envolvidos:
   - `templates/gitpr.smart-excludes.json` (modelo base)
   - `gitpr.docs-smart-excludes.json` (extensões de documentação)
   - Como os arquivos são mesclados no `SMART_EXCLUDES` principal

4. **Exemplo de Uso** - Cenário prático:
   - Execução do `git diff` com e sem Smart Excludes
   - Comparação de saída e redução de tokens

5. **Benefícios** - Vantagens da funcionalidade:
   - Redução de tokens em até X%
   - Melhor performance
   - Foco em mudanças relevantes para revisão de código

6. **Personalização** - Como os usuários podem adaptar:
   - Adicionar novas extensões
   - Modificar o comportamento padrão

7. **Perguntas Frequentes** - Dúvidas comuns:
   - Por que os arquivos de documentação são excluídos?
   - Como saber quais documentos foram alterados?
   - Posso desabilitar esta funcionalidade?

---

### **3. Integração com `get_docs_url()`**

**Arquivo de referência:** `@docs\i18n_explanation.md`

**Implementação no CLI:**

Quando o sistema Smart Excludes for ativado ou mencionado na saída, utilizar a função `get_docs_url()` para exibir o link apropriado.

**Pontos de integração:**
- Durante a primeira execução que utiliza Smart Excludes
- Quando um usuário pergunta sobre exclusão de arquivos
- Em mensagens de log que mencionam a funcionalidade
- Como parte da saída de ajuda ou informações do sistema

**Comportamento esperado:**
- Detectar o idioma atual do usuário
- Gerar URL correta para a documentação
- Exibir o link de forma clara e acessível
- Incluir contexto sobre onde encontrar mais informações

---

### **4. Mapeamento de URLs por Idioma**

**Estrutura de URLs esperada:**
- Inglês → URL base com caminho `smart-excludes`
- Português Brasil → URL base com caminho `pt_br/smart-excludes`
- Português Portugal → URL base com caminho `pt_pt/smart-excludes`
- Francês → URL base com caminho `fr/smart-excludes`
- Espanhol → URL base com caminho `es/smart-excludes`

---

### **5. Critérios de Aceite**

- [ ] README atualizado em todos os 5 idiomas com a nova seção
- [ ] 5 arquivos de documentação criados em `docs/` (um por idioma)
- [ ] Todos os documentos traduzidos corretamente seguindo a regra i18n
- [ ] `get_docs_url()` integrado no fluxo do CLI para exibir links
- [ ] URL correta exibida no momento apropriado
- [ ] Fallback para inglês quando o idioma não está disponível
- [ ] Documentação inclui exemplos práticos e casos de uso
- [ ] Links são verificados e funcionais
- [ ] Terminologia consistente entre README, docs e código

---

### **6. Exemplo de Comportamento Esperado no CLI**

**Ao executar gitpr com Smart Excludes ativo:**
- Sistema exibe mensagem indicando que Smart Excludes está sendo utilizado
- Mostra quais extensões estão sendo excluídas
- Exibe a lista de documentação alterada (sem conteúdo)
- Fornece link para documentação completa

**Ao detectar a primeira execução com a funcionalidade:**
- Mensagem informativa sobre a nova funcionalidade
- Explicação breve sobre redução de tokens
- Link para documentação detalhada

---

### **7. Notas Técnicas**

- Use o mesmo sistema de i18n já implementado para os scripts
- Mantenha consistência de terminologia entre README, docs e código
- Verifique se a URL base está configurada corretamente no `get_docs_url()`
- Considere adicionar um comando específico para exibir informações sobre Smart Excludes
- Atualize o changelog para refletir essa nova funcionalidade
- Certifique-se de que a documentação seja acessível e clara para usuários de todos os níveis

---

### **8. Arquivos a Serem Modificados/Criados**

```
README.md
README.pt_br.md
README.pt_pt.md
README.fr.md
README.es.md
docs/smart-excludes.md
docs/smart-excludes.pt_br.md
docs/smart-excludes.pt_pt.md
docs/smart-excludes.fr.md
docs/smart-excludes.es.md

```

---

## **Links Úteis**

- [Relatório de Implementação](@docs/claude-code/reports/develop_natan/2026-08-05_docs_smart_excludes.md)
- [Documentação i18n](@docs/i18n_explanation.md)
- [Arquivos de Configuração](@templates/gitpr.smart-excludes.json)