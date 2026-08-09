# Correção do Fluxo de Commit e Push

---

### **Contexto**
Ao confirmar a mensagem de commit, o sistema pode encontrar uma situação onde o commit já foi realizado anteriormente e não há novos arquivos para registrar. Além disso, o modal de erro está com tamanho inadequado.

---

### **Regras de Desenvolvimento**

#### **1. Tratamento do Cenário "Commit Já Realizado"**
- **Detecção**: Capturar saída do `git commit` indicando que não há alterações para commit
- **Interpretação**: Não tratar como erro, mas como estado válido onde o commit já foi feito
- **Ação**: 
  - Pular etapa de commit
  - Prosseguir diretamente para verificação e criação do pull request no GitHub
- **Mensagem**: Exibir "✅ Commit já realizado. Prosseguindo para publicação..."

#### **2. Verificação de Pull Request Existente**
- Antes de criar novo PR, verificar se já existe um PR aberto para a branch atual
- Utilizar API do GitHub para listar PRs com `head` igual à branch atual e `state=open`
- Se existir PR aberto:
  - Exibir URL do PR existente
  - Perguntar ao usuário se deseja atualizar o PR ou pular a publicação
- Se não existir PR: Prosseguir com criação

#### **3. Ajuste do Modal "Commit Failed"**
- Reduzir altura de 100% para 80%
- Manter centralizado vertical e horizontalmente
- Manter largura atual
- Garantir que o conteúdo seja rolável se necessário

#### **4. Fluxo Completo de Commit e Push**
1. Usuário confirma mensagem de commit
2. Tentar executar `git commit -m "<mensagem>"`
3. Se commit bem-sucedido: Prosseguir para push/PR
4. Se commit já realizado (sem alterações): Prosseguir para push/PR
5. Se erro real (ex: conflito): Exibir modal de erro com 80% de altura
7. Verificar PR existente
8. Se PR existe: Oferecer opções (atualizar/cancelar publicação)
atualizar - Se existe novos arquivos
cancelar publicação - 
9.  Se PR não existe: Criar novo PR

#### **5. Mensagens de Feedback**
- "📝 Verificando estado do commit..."
- "✅ Commit já realizado" (quando não há alterações)
- "✅ Commit realizado com sucesso" (quando novo commit é criado)
- "🔍 Verificando pull requests existentes..."
- "📋 PR existente encontrado: <url>"
- "🚀 Criando novo pull request..."

#### **6. Tratamento de Erros Específicos**
- **Conflitos de merge**: Exibir mensagem clara com instruções
- **Branch sem upstream**: Configurar upstream automaticamente
- **Token inválido**: Solicitar novo token
- **Rede indisponível**: Permitir retry com backoff

#### **7. Comportamento no Push**
- Se PR já existe: Atualizar a descrição do PR com novo conteúdo
- Se PR não existe: Criar novo PR com título e corpo gerados
- Exibir URL do PR criado ou atualizado