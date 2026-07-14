### **🗺️ Plano de Ação Mestre: Chat Interativo Híbrido**

#### **Fase 1: O Motor de Persistência e Estado (src/chat\_memory.py ou cache.py)**

Vamos criar o cérebro que garante que a IA nunca se esquece da conversa, mesmo que feches o terminal.

* **A Estrutura de Pastas:** Gestão automática de \~/.gitpr/cache/chat/\<uuid-base-15\>/.  
* **Os Ficheiros:**  
  * conversation\_\<uuid\>.json: Guarda o histórico exato do formato exigido pelas APIs (ex: \[{"role": "user", "content": "..."}\]).  
  * chat-config\_\<uuid\>.json: Guarda os metadados da sessão (nome do repo, branch, utilizador) e o **diff\_history** (um array com os hashes MD5 dos diffs para sabermos se o código mudou durante a sessão).  
* **Lógica de Sessão Contínua:** Se rodares gitpr \--chat e o diff atual ainda não tiver sido commitado na branch, o GitPR reaproveita o UUID anterior e retoma a conversa de onde parou.

#### **Fase 2: O Motor Cognitivo e Sistema de Comandos (src/ai\_providers.py)**

Vamos adaptar a IA para o formato de Chat e criar o intercetor de comandos.

* **A Função call\_ai\_chat:** Nova função que aceita histórico de mensagens, instrução de sistema (com o diff injetado) e retorna **Markdown** livre em vez de JSON restrito.  
* **O Intercetor de Comandos Rápidos (/comandos):**  
  * Antes de enviar a mensagem do utilizador para a API, validamos se começa com /.  
  * Se for /explicar: Substitui a mensagem por um prompt arquitetural que pede para explicar o diff linha a linha.  
  * Se for /testes: Pede à IA para gerar casos de teste (ex: PyTest/Jest) estritamente para as funções alteradas no diff.  
  * Se for /otimizar: Pede uma análise focada em complexidade ciclomática e performance.

#### **Fase 3: A Interface Gráfica Base (src/ui/chat\_app.py)**

Vamos construir o ecrã com a biblioteca textual.

* **Layout do Chat:**  
  * **Header:** Exibe o ID da sessão (UUID Base 15\) e o ambiente (Repo/Branch).  
  * **Corpo (RichLog/Markdown):** Uma área de leitura que interpreta blocos de código com sintaxe colorida (*syntax highlighting*).  
  * **Input e Footer:** Caixa de texto persistente no fundo para o utilizador escrever, com a listagem dos atalhos no rodapé.  
* **Motor Assíncrono:** Uso do decorador @work do Textual para garantir que o terminal continua fluido com a animação "A pensar..." enquanto a API responde em background.

#### **Fase 4: As Funcionalidades *Enterprise* (A Magia da TUI)**

Ainda dentro do ChatApp, vamos implementar as teclas de atalho matadoras:

* **F2 (Refresh Silencioso do Diff):**  
  * Se fores ao VSCode e mudares uma linha, voltas ao terminal e carregas em F2.  
  * O GitPR roda o git diff silenciosamente, compara o MD5 com o do chat-config.json e envia uma mensagem de sistema invisível à IA: *"O utilizador atualizou o código agora mesmo. O novo diff é \[NOVO\_DIFF\]"*. O chat continua sem reiniciar\!  
* **F5 (Aplicar Código / Auto-Patch):**  
  * Lê a última mensagem da IA, extrai o conteúdo do bloco de código Markdown (python ... ) e tenta aplicar a substituição no teu ficheiro local usando lógica de *diff/patch*. É o *Pair Programming* a funcionar.  
* **F6 (Exportar Sessão):**  
  * Pega em todo o ficheiro conversation.json, envia um comando oculto à IA para "Resumir as decisões tomadas nesta conversa" e encaminha esse resumo diretamente para a nossa aplicação IssueApp (a que criaste anteriormente) para publicar no GitHub.

#### **Fase 5: A Ponte de Comando CLI e Idiomas (src/main.py)**

O último passo para ligar tudo ao utilizador.

* Adicionar a flag @click.option('-ch', '--chat', is\_flag=True) ao comando principal.  
* Atualizar o Dicionário HELP\_MAP para documentar não só a flag, mas também as teclas de atalho e os comandos /.  
* Lógica no cli(): Se o \--chat for ativado, inicializamos a classe do Motor de Memória (Fase 1), descobrimos o UUID, capturamos o Diff atual e lançamos o ChatApp(uuid, diff).

