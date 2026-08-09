**Prompt Melhorado para Agente de Vibe Coding - Aprimoramentos da Interface de Commit**

---

### **Contexto**
A interface interativa para publicação de pull requests inclui um fluxo de commit automático que precisa ser refinado para melhor experiência do usuário, especialmente no gerenciamento de arquivos e exibição de informações.

---

### **Objetivos**
1. Ajustar tamanho e posicionamento do modal de confirmação de alterações não commitadas
2. Implementar seleção de arquivos unstaged antes do commit
3. Isolar logs de criação de commit em modal dedicado
4. Permitir edição da mensagem de commit antes da confirmação

---

### **Regras de Desenvolvimento**

#### **1. Modal de Confirmação de Alterações**
- Reduzir altura para 70% da altura total da tela
- Centralizar vertical e horizontalmente na interface
- Manter largura proporcional (ex: 60-80% da largura)
- Garantir que o conteúdo seja rolável se necessário

#### **2. Gerenciamento de Arquivos Unstaged**
- **Detecção**: Ao identificar a necessidade de commit, verificar arquivos fora do stage (`git status --porcelain` com `??` e ` M`)
- **Modal de seleção**:
  - Exibir lista de arquivos unstaged com checkbox
  - Checkbox marcado por padrão para todos os arquivos
  - Permitir desmarcar arquivos individualmente
  - Opção "Selecionar todos" / "Desmarcar todos"
  - Botão "Confirmar" para adicionar ao stage
  - Botão "Continuar sem adicionar" para prosseguir sem stage
  - Botão "Cancelar" para abortar a operação
- **Ação**: Ao confirmar, executar `git add <arquivos_selecionados>`

#### **3. Exibição de Logs de Commit**
- **Isolamento**: Logs do processo de criação da mensagem de commit não devem sobrepor a interface textual
- **Modal de terminal**:
  - Exibir logs dentro de um modal com aparência de terminal
  - Mostrar progresso em tempo real (geração, linter, commit)
  - Rolagem automática para novas mensagens
  - Título do modal: "📦 Processando commit..."
  - Fechar automaticamente ao finalizar ou permitir fechamento manual
- **Manter interface principal** visível em segundo plano (desfocada ou escurecida)

#### **4. Edição da Mensagem de Commit**
- **Exibição**: Após gerar a mensagem, exibir em um modal/editor
- **Edição**: Campo editável com a mensagem pré-preenchida
- **Ações**:
  - "Confirmar" (usa mensagem atual)
  - "Editar" (permite alterar antes de confirmar)
  - "Regenerar" (solicita nova geração)
  - "Cancelar" (aborta operação)
- **Validação**: Verificar se a mensagem não está vazia antes de confirmar

#### **5. Fluxo Completo Atualizado**
1. Verificar alterações não commitadas
2. Abrir modal de confirmação (70% altura, centralizado)
3. Se houver arquivos unstaged, abrir modal de seleção
4. Processar stage dos arquivos selecionados
5. Abrir modal de terminal para logs de geração de mensagem
6. Exibir mensagem gerada em modal editável
7. Aguardar confirmação do usuário
8. Executar commit
9. Fechar modais e prosseguir com publicação

#### **6. Comportamento em Casos Especiais**
- **Nenhum arquivo unstaged**: Pular modal de seleção
- **Usuário não seleciona arquivos**: Continuar com `--no-verify` ou abortar conforme escolha
- **Falha na geração da mensagem**: Exibir erro e permitir tentar novamente
- **Timeout no linter**: Exibir aviso e oferecer opções

#### **7. Mensagens e Feedback**
- Indicar claramente cada etapa do processo
- Mostrar quantos arquivos foram adicionados ao stage
- Exibir a mensagem de commit gerada antes da confirmação
- Confirmar com o usuário antes de cada ação destrutiva

#### **8. Teclas de Atalho**
- `<Enter>`: Confirmar ação atual
- `<Esc>`: Cancelar/fechar modal atual
- `<Tab>`: Navegar entre elementos (checkboxes, botões)
- `<Espaço>`: Alternar checkbox

#### **9. Variáveis de Ambiente**
- `GITPR_AUTO_STAGE`: Boolean para pular seleção de arquivos (stage automático)
- `GITPR_SHOW_LOGS`: Boolean para exibir logs detalhados no modal