**Prompt Melhorado para Agente de Vibe Coding - Atualização da Publicação de Pull Requests**

---

### **Contexto**
A funcionalidade de publicação de pull requests possui comportamentos que precisam ser revisados e documentados, especialmente em relação à interface interativa, commit automático e validação de código.

---

### **Objetivos**
1. Substituir a tag `--publish` por `--no-publish` como comportamento padrão
2. Atualizar a documentação refletindo as novas regras
3. Implementar fluxo automático de commit com validação de lint
4. Integrar interface interativa com opções de confirmação

---

### **Regras de Desenvolvimento**

#### **1. Comportamento de Publicação**
- **Comportamento padrão**: Ao executar `gitpr`, a interface interativa é aberta para publicação
- **Tag `--no-publish`**: Impede a abertura da interface, apenas salva o arquivo localmente
- **Tag `--no-edit`**: Pula a edição do conteúdo, publica com o texto gerado automaticamente
- **Remover a tag `--publish`**: Não é mais necessária, pois a publicação é o comportamento padrão

#### **2. Atualização da Documentação**
- Remover qualquer referência à tag `--publish` do arquivo `docs/pull-request-publication.md`
- Adicionar documentação para a tag `--no-publish`
- Adicionar documentação para a tag `--no-edit`
- Atualizar exemplos e fluxos de uso

#### **3. Fluxo de Commit Automático**
**Ativação**: Quando o usuário acionar "F3 Publish PR" ou utilizar a tag `--no-edit`

**Processo**:
1. **Verificar commits pendentes**: Detectar se há alterações não commitadas no repositório
2. **Executar linter**: Rodar o linter local para validar o código antes do commit
3. **Solicitar frase de commit**: Gera o prompt e executa a requisição ao provider interno (LLM) para gerar a frese de commit baseado no "git diff", deve exibir a frase gerada e solicitar confirmação ao usuário.
4. **Tratamento de falhas no lint**:
   - Se o linter encontrar problemas, exibir os erros na interface
   - Perguntar ao usuário: "Deseja executar o commit mesmo com problemas no linter? (--no-verify)"
   - Opções: "Sim" (executa com `--no-verify`), "Não" (aborta a operação)
5. **Executar commit**: `git commit -m "<mensagem>"` (com ou sem `--no-verify` conforme escolha do usuário)
6. **Prosseguir com publicação**: Continuar o fluxo normal de publicação após o commit

#### **4. Interface Interativa**
- Exibir status do commit durante o processo
- Mostrar progresso da execução do linter
- Exibir resultados do linter de forma clara
- Opções de navegação: confirmar, cancelar, visualizar detalhes
- Indicar claramente quando o commit foi executado com sucesso ou falhou
- Solicitar confirmação da frase do commit ao usuário
- Exibir resultados do processamento de criação do pull request
 
#### **5. Comportamento em Cenários Específicos**
- **Sem alterações para commit**: Exibir mensagem e pular etapa de commit
- **Linter não encontrado**: Prosseguir com aviso (sem bloqueio)
- **Falha no commit**: Exibir erro e permitir retry ou cancelamento
- **Conflitos de merge**: Detectar e informar antes do commit

#### **6. Variáveis de Ambiente**
- `GITPR_AUTO_COMMIT`: Boolean para executar commit automaticamente sem perguntar (padrão: false)
- `GITPR_SKIP_LINT`: Boolean para pular validação do linter (padrão: false)


#### **7. Mensagens e Logs**
- Exibir no terminal:
  - "📝 Gerando mensagem de commit..."
  - "🔍 Executando linter..."
  - "✅ Linter aprovado" ou "❌ Problemas encontrados no linter"
  - "📦 Commit executado: <hash>"
  - "🚀 Publicando pull request..."

#### **8. Atualização do Arquivo de Documentação**
Adicionar ao `docs/pull-request-publication.md`:
- Seção explicando o comportamento padrão vs tags
- Detalhamento do fluxo de commit automático
- Exemplos de uso da tag `--no-publish` e `--no-edit`
- Tabela comparativa de comportamentos
- Fluxograma simplificado da decisão de commit com linter
- Detalhe todas as variáveis de ambiente já utilizadas, e adicione `GITPR_SKIP_LINT` e `GITPR_AUTO_COMMIT` 