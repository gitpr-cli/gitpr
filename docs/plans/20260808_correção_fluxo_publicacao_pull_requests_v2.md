# Correção do Fluxo de Commit e Publicação

---

### **Contexto**
A funcionalidade de publicação de pull requests está com falhas críticas no fluxo de commit: animação não funciona, telas não são exibidas e o processo é interrompido sem feedback.

---

### **Regras de Desenvolvimento**

#### **1. Animação do Modal "Processing commit..."**
- A animação deve ser contínua e visível durante todo o processamento
- Iniciar imediatamente ao abrir o modal
- Manter em execução até que o processo seja concluído
- Utilizar o que já foi feito com movimento constante da esquerda para a direita

#### **2. Ajuste do Modal "Commit Message"**
- Reduzir altura para 50% da altura da tela
- Manter centralizado vertical e horizontalmente
- Garantir que o campo de edição seja visível e funcional

#### **3. Remoção do Botão "Regenerate"**
- Remover completamente o botão do modal "Commit Message"
- Manter apenas os botões "Confirm" e "Cancel"

#### **4. Fluxo do Modal "Confirming commit"**
- Após clicar em "Confirm" no modal "Commit Message":
  1. Fechar o modal "Commit Message"
  2. Abrir o modal "Processing commit..." com animação ativa
  3. Executar o comando de commit em background
  4. Manter o modal aberto exibindo progresso
  5. Ao concluir, fechar o modal e prosseguir com a publicação

#### **5. Tratamento de Interrupção sem Mensagem**
- Identificar por que o fluxo está interrompendo após o clique em "Confirm"
- Garantir que todas as exceções sejam capturadas
- Exibir mensagem de erro específica em caso de falha
- Não fechar modais sem feedback ao usuário

#### **6. Verificações Obrigatórias**
- Validar se o comando `git commit` está sendo executado corretamente
- Confirmar se a mensagem editada está sendo passada para o comando
- Verificar se há permissão para escrever no repositório
- Validar se o diretório `.git` existe e é acessível

#### **7. Feedback ao Usuário**
- Exibir mensagens de progresso dentro do modal "Processing commit..."
- Mostrar saída do comando `git commit` (stdout/stderr)
- Em caso de sucesso: exibir "✅ Commit realizado com sucesso"
- Em caso de falha: exibir "❌ Erro ao realizar commit: <mensagem>"

#### **8. Fluxo Completo Após Correção**
1. Usuário clica em "Confirm" no modal "Commit Message"
2. Modal "Commit Message" fecha
3. Modal "Processing commit..." abre com animação ativa
4. Mensagem: "📝 Criando commit..."
5. Comando `git commit -m "<mensagem>"` é executado
6. Se sucesso: "✅ Commit realizado" → Fechar modal → Publicar PR
7. Se falha: "❌ Erro: <detalhes>" → Exibir opções (Tentar novamente / Cancelar)

#### **9. Logs de Depuração**

- Criar um arquivo de log em cada linha com data e mensagem exemplo "[2026-08-08 17:00:08] | Erro ..."
- O log deve ser criado em um arquivo no local ~/.gitpr/logs/pr_desc/ 
- O Arquivo de log deve ter o formato "pr_desc_<uuid_base_15>.log" cada sessão gera um novo arquivo. Onde <uuid_base_15> e gerada na função chat_memory.gerar_uuid_base_15() 
- Adicionar logs para rastrear cada etapa do processo
- Registrar quando os modais são abertos e fechados
- Registrar quando ao botão e clicado
- Registrar saída do comando `git commit`
- Registrar saída do comando `git add` dos unstaged files
- Registrar exceções com stack trace completo
- Gerar os logs em uma unica linha sem quebra de linha na mensagem de log.
- Adicionar variavel `PR_PUBLISH_LOG` ao ~/.gitpr/.env, com o valor padrão true, para desabilitar o log. 
