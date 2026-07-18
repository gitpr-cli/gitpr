### **📋 Plano de Desenvolvimento: Otimização de Contexto e Map-Reduce**

* \[ \] **Passo 1: Otimização Nativa do Git (src/core.py)**  
  * Adicionar as flags \-U1, \-w, \-M e \-B nas listas de execução das funções get\_git\_diff e get\_git\_full\_diff.  
  * Garantir que todo diff extraído já venha limpo de ruídos visuais de espaçamento e reindentações.  
* \[ \] **Passo 2: Estimativa de Tokens e Limites (src/core.py)**  
  * Implementar a função estimate\_tokens utilizando a heurística rápida de len(text) / 4\.  
  * Definir o teto de segurança da janela de contexto para ativar o Map-Reduce apenas quando necessário.  
* \[ \] **Passo 3: Algoritmo "Map" / Splitter (src/core.py e src/ai\_providers.py)**  
  * Criar um parser inteligente que divida o diff gigante pelo delimitador padrão diff \--git a/, garantindo que nenhum arquivo seja cortado no meio.  
  * Agrupar os arquivos em lotes (chunks) respeitando o limite da estimativa de tokens.  
  * Disparar chamadas sequenciais para gerar o resumo de cada lote usando call\_ai\_model, aplicando o time.sleep(1) entre as iterações para blindar a aplicação contra os Rate Limits (429) do Gemini e DeepSeek.  
* \[ \] **Passo 4: Algoritmo "Reduce" / Unificação (src/core.py)**  
  * Compilar e concatenar todos os resumos parciais retornados pelo Passo 3\.  
  * Injetar o resumo unificado na requisição final para gerar a descrição do PR ou do Code Review com consistência arquitetural.

