# **🚀 Relatório de Status do Projeto: GitPR CLI**

## **📌 Visão Geral**

O **GitPR** é uma ferramenta de CLI (Command Line Interface) avançada para automação de processos Git utilizando Inteligência Artificial (Google Gemini / DeepSeek). O objetivo principal é atuar como um assistente inteligente local que faz Code Reviews, gera Pull Requests, mensagens de commit semânticas, audita dívida técnica e injeta boas práticas no fluxo de trabalho do desenvolvedor (Shift Left).

## **🏗️ Arquitetura e Bibliotecas Base**

* **Linguagem:** Python 3.x  
* **CLI Framework:** Click (para comandos, flags e formatação de terminal).  
* **UI/Terminal:** Interface interativa e TUI (Text User Interface) para chat e revisão de issues.  
* **Criptografia:** cryptography.fernet para proteção local de chaves de API.  
* **Configuração:** dotenv, pyyaml (para o linter estático).  
* **IA Providers:** Integração via SDK oficial do Google GenAI (gemini-2.5-flash) e DeepSeek.

## **🧩 Módulos Implementados e Arquitetura de Ficheiros**

### **1\. Núcleo e Operações Git (src/core.py)**

* **Geração Estruturada:** Comunica com a LLM pedindo retorno estritamente em JSON (commit\_message e pr\_description).

### **2\. Interface CLI e Setup (src/main.py e src/config.py)**

* **Setup Inicial:** Detecta primeira execução, cria a pasta \~/.gitpr/, e solicita interativamente as chaves de API e preferências, salvando num .env.  
* **Routing de Comandos:** Gerencia as flags (--commit, \--review, \--fullreview, \--linter, \--skill, \--issue, \--blame).

### **3\. Motor de Análise Estática / Linter (src/linter\_engine.py)**

* **Linter Offline:** Analisa estaticamente as linhas adicionadas (+) no git diff sem gastar cotas de IA.  
* **Regras YAML:** Lê o ficheiro local .gitpr.linter.yml (criado via \--skill). Suporta regex de validação (ex: detectar console.log, localhost), ignorar comentários e ignorar diretórios específicos (usando fnmatch).

### **4\. Segurança e Cofre (src/security.py)**

* **Criptografia:** Gera uma chave mestra secret.key na pasta \~/.gitpr/.  
* **Funções:** encrypt\_data e decrypt\_data para garantir que tokens e chaves não fiquem em texto claro.

### **5\. Auto-Updater (src/updater.py)**

* **Hot-Swap:** Verifica na API do GitHub Releases a versão mais recente (.sha256). Se houver divergência, baixa o binário compilado (gitpr.exe) em background, renomeia o executável atual e substitui sem quebrar a execução em andamento (com capacidade de rollback).

### **6\. Interface de Chat e Auto-Patch (src/ui/chat\_app.py)**

* **Interatividade:** Possui um histórico de mensagens (self.memory).  
* **Atalho de Extração (F5):** Função action\_apply\_code usa Regex não-destrutivo para extrair blocos de código sugeridos pela IA e exportá-los para um ficheiro GITPR\_PATCH\_SUGGESTION.txt para fácil aplicação pelo dev.

### **7\. Internacionalização (i18n)**

* **Traduções:** Sistema de dicionários JSON (ex: langs/pt\_br.json) contendo traduções completas para todos os menus de ajuda do Click, alertas do linter, mensagens do sistema e retornos do Git Hooks.

### **8. Otimização Nativa e Map-reduce

Foi implementada uma arquitetura em duas camadas para contornar o limite de tokens (`429 RESOURCE_EXHAUSTED` e `400 Invalid Request Error`) nas APIs do Gemini e DeepSeek, garantindo a leitura completa de Pull Requests gigantes (como migrações massivas de Blade para Vue/Inertia).

#### 🛠️ Mudanças Técnicas (`src/core.py`)

1. **Otimização Nativa do Git (Nível 1 de Defesa):**
   - Injeção das flags cirúrgicas `-U1`, `-w`, `-M` e `-B` nos comandos das funções `get_git_diff` e `get_git_full_diff`.
   - *Impacto:* Redução imediata de contexto inútil, ignorando reindentações e forçando a leitura de reescritas complexas como deleção/criação.

2. **Estimativa e Split Seguro (Nível 2 de Defesa):**
   - Implementação da função `estimate_token_count` usando a heurística leve de `len() // 4`.
   - Implementação da função `split_diff_into_chunks` com um limite de 90.000 tokens, quebrando o texto estritamente no delimitador regex `(^diff --git a/)` para não corromper a sintaxe de leitura da IA.

3. **Arquitetura Map-Reduce:**
   - Refatoração do fluxo da `generate_pr_content` para iterar assincronamente sobre os chunks.
   - Aplicação de chamadas parciais exigindo um JSON com a chave `{"resumo": "..."}`.
   - Injeção de um `time.sleep(1)` entre os lotes ("Map") para respeitar o Rate Limit.
   - Concatenação dos resumos parciais ("Reduce") enviada no prompt principal para manter o padrão de saída e o tom de voz da arquitetura (Code Review ou PR Description).