# Reorganização do Fluxo de Verificação de Arquivos (Unstaged files)



## **Contexto**
Atualmente, a verificação de arquivos unstaged ocorre apenas quando o usuário inicia o processo de commit durante a publicação do pull request. Isso precisa ser antecipado para melhorar o fluxo e a experiência do usuário.

---

## **Objetivos**
1. Antecipar a verificação de arquivos unstaged para o início da execução do `gitpr`
2. Isolar a interface de seleção de arquivos em um modal dedicado
3. Separar claramente as etapas de preparação (stage) e publicação
4. Remover verificação duplicada durante a publicação

---

## **Regras de Desenvolvimento**

### **1. Momento da Verificação**
- Executar verificação de arquivos unstaged assim que o comando `gitpr` for iniciado
- Antes de qualquer outra operação (geração de descrição, interface, etc.)
- Verificar usando `git status --porcelain` para arquivos com status `??` e ` M`

### **2. Interface de Seleção de Arquivos**
- Abrir interface textual exibindo **apenas** o modal "Unstaged Files"
- Modal deve conter:
  - Lista de arquivos com checkboxes (todos marcados por padrão)
  - Botão "Confirmar e adicionar" para stage dos arquivos selecionados
  - Botão "Pular" para ignorar arquivos e prosseguir
  - Botão "Cancelar" para abortar toda a operação
- Interface deve ser minimalista, sem outros elementos da aplicação

### **3. Fluxo Após Confirmação**
- Ao confirmar ou pular:
  - Fechar a interface textual completamente
  - Retornar ao terminal normal
  - Prosseguir com o fluxo normal de criação da descrição do pull request
  - Logs e saídas devem aparecer no terminal padrão (não na interface)

### **4. Remoção de Verificação Duplicada**
- Durante a publicação do pull request (fluxo do "F3 Publish PR"):
  - Não verificar novamente arquivos unstaged
  - Apenas verificar se o commit já foi realizado
  - Se não houver commit, iniciar fluxo de commit (gerar mensagem, executar commit)
  - Se houver commit, prosseguir diretamente com a publicação

### **5. Comportamento em Casos Especiais**
- **Nenhum arquivo unstaged**: Pular modal, prosseguir diretamente
- **Apenas arquivos ignorados pelo .gitignore**: Não exibir no modal
- **Usuário cancela**: Abortar toda a execução do `gitpr`
- **Usuário pula**: Prosseguir sem stage, arquivos permanecem unstaged

### **6. Mensagens de Feedback**
- Exibir no terminal antes de abrir a interface:
  - "🔍 Verificando arquivos não versionados..."
  - Se houver arquivos: "📋 Abrindo seleção de arquivos..."
  - Se não houver: "✅ Nenhum arquivo unstaged encontrado. Prosseguindo..."
- Após fechar a interface:
  - "✅ Arquivos selecionados adicionados ao stage" ou "⏭️ Arquivos ignorados"
  - "🚀 Iniciando geração do pull request..."

### **7. Logs Durante o Processo**
- Manter logs claros e concisos no terminal
- Evitar sobreposição de informações entre interface e terminal
- Separar visualmente as etapas com separadores ou emojis

### **8. Variáveis de Ambiente**
- `GITPR_AUTO_STAGE`: Boolean para pular seleção automática (fazer stage de tudo)
- `GITPR_SKIP_UNSTAGED_CHECK`: Boolean para pular completamente a verificação

### **9. Fluxo Completo Atualizado**
1. Usuário executa `gitpr`
2. Verificar arquivos unstaged
3. Se existirem, abrir interface com modal de seleção
4. Usuário confirma ou pula
5. Fechar interface, retornar ao terminal
6. Gerar descrição do pull request (fluxo normal)
7. Exibir resultado
8. Se usuário escolher publicar (F3 Publish PR):
   - Verificar se há commit pendente
   - Se não houver commit, iniciar fluxo de commit (sem verificação de unstaged)
   - Publicar pull request

#### 10. Documentação

- Implemente as variaveis de ambiente  `GITPR_AUTO_STAGE` e `GITPR_SKIP_UNSTAGED_CHECK` no arquivo @docs\pull-request-publication.md e nos outros 4 arquivos de idiomas 