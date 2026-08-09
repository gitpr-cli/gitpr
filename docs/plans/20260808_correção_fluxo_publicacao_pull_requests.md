# Correção do Fluxo de Publicação de Pull Requests

---

### **Contexto**
O fluxo de publicação de pull requests apresenta problemas na interface e na execução dos comandos, especialmente na geração de commit, exibição de animações e tratamento de erros.

---

### **Objetivos**
1. Corrigir a animação do modal "Processing commit"
2. Garantir execução correta do commit com a mensagem gerada
3. Implementar criação do pull request no GitHub após o commit
4. Adicionar tratamento de erros com opções de retry e cancelamento

---

### **Regras de Desenvolvimento**

#### **1. Modal "Processing commit"**
- **Animação**: Deve ser contínua e cíclica durante todo o processamento

#### **2. Modal "Commit Message"**
- **Exibição**: Mostrar a mensagem gerada em campo editável
- **Edição**: Permitir alteração do texto antes da confirmação
- **Ação "Confirm"**: 
  - Fechar modal de mensagem
  - Abrir modal "Processing commit"
  - Executar `git commit -m "<mensagem>"`
  - Após sucesso, prosseguir para criação do pull request

#### **3. Criação do Pull Request no GitHub**
- Executar após commit bem-sucedido
- Utilizar API do GitHub com token configurado
- Campos: título, corpo, branch base e head
- Exibir progresso dentro do modal "Processing Publish Pull Request"
- Atualizar mensagem para: "Criando pull request no GitHub..."

#### **4. Tratamento de Erros - Commit**
- **Falha no commit**: 
  - Fechar modal "Processing commit"
  - Abrir modal de erro com detalhes específicos
  - Opções: "Tentar novamente" (reabre modal de mensagem) ou "Cancelar" (fecha tudo)
- **Manter mensagem original**: Preservar a mensagem editada para tentativas futuras

#### **5. Tratamento de Erros - Publicação no GitHub**
- **Falha na criação do PR**:
  - Fechar modal "Processing Publish Pull Request"
  - Abrir modal de erro com detalhes da resposta da API
  - Opções: "Tentar novamente" (republicar com mesmos dados) ou "Cancelar" (fecha tudo)
- **Manter commit já realizado**: Não desfazer o commit em caso de falha na publicação

#### **6. Fechamento da Interface**
- **Sucesso**: 
  - Exibir mensagem de sucesso com URL do PR
  - Fechar automaticamente após 3 segundos ou com clique
- **Cancelamento**: Fechar todos os modais e retornar ao terminal
- **Erro**: Manter interface aberta até usuário escolher ação

#### **7. Variáveis de Estado**
- Manter estado da mensagem de commit editada
- Manter estado do commit (já realizado ou não)
- Manter estado da publicação (tentativas)

#### **8. Logs e Feedback**
- Exibir logs detalhados dentro do terminal
- Atualizar em tempo real cada etapa
- Em caso de erro, incluir comando executado e saída do mesmo

#### **9. Comportamento em Casos Especiais**
- **Commit vazio**: Validar mensagem não vazia antes de confirmar
- **Sem alterações**: Detectar e informar que não há o que commit
- **Conflitos**: Capturar erro de merge e exibir orientações
- **Token inválido**: Exibir erro específico de autenticação
- **Branch inexistente**: Validar branch base antes de publicar