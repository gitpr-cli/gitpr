### **📋 Plano de Desenvolvimento: \--issue (TUI \+ GitHub API)**

#### **Fase 1: Configuração e Setup**

*Meta: Preparar o ambiente base com o mínimo de alterações para suportar o novo fluxo.*

* \[ \] **1\. Atualizar src/config.py:**  
  * Adicionar a chave OUTPUT\_FILE\_NAME\_ISSUE no dicionário DEFAULT\_CONFIG.  
  * Criar a função get\_github\_token() reutilizando a lógica de descriptografia existente.  
  * *Verificação:* A variável de ambiente é carregada e a função retorna None quando o token não existe.  
* \[ \] **2\. Atualizar src/core.py:**  
  * Modificar a função generate\_skill\_template() para incluir o template .gitpr.issue.md (Padrão: O Que / Por Que / Onde / Como).  
  * *Verificação:* Executar gitpr \--skill e confirmar a criação física do arquivo com o conteúdo correto.

#### **Fase 2: Motor de Inteligência (src/issue\_engine.py)**

*Meta: Isolar a complexidade da extração de dados do Git e a comunicação com a IA.*

* \[ \] **1\. Novo Arquivo:** Criar src/issue\_engine.py.  
* \[ \] **2\. Extração de Repositório:**  
  * Criar a função get\_github\_repo\_info().  
  * *Verificação:* Roda git remote \-v, aplica *regex* e retorna no padrão owner/repo (ou levanta exceção clara se não for um repo GitHub).  
* \[ \] **3\. Geração de Conteúdo:**  
  * Criar a função generate\_issue\_content(diff\_text).  
  * *Verificação:* Envia o *diff* para a IA e retorna um dicionário estrito: {"titulo": "...", "corpo": "..."}.

#### **Fase 3: Autenticação Segura e TUI (src/tui\_issue.py)**

*Meta: Capturar o token de forma segura e prover uma interface visual para edição antes do envio.*

* \[ \] **1\. Captura de Token (PAT):**  
  * Criar a função validate\_or\_request\_github\_token(repo\_info).  
  * Lógica: Se não houver token, monta a URL (\[https://github.com/settings/tokens/new\](https://github.com/settings/tokens/new)?...), exibe instrução clara, solicita o *input* oculto, criptografa e salva via set\_key.  
  * *Verificação:* O token é criptografado corretamente no arquivo .env e pode ser lido posteriormente.  
* \[ \] **2\. Interface Gráfica (Textual):**  
  * Criar a classe IssueApp(App) renderizando um Input (Título) e um TextArea (Corpo).  
  * *Verificação:* A TUI abre sem quebrar o terminal, pré-preenchida com os dados da IA.  
* \[ \] **3\. Integração de Ações (F2 e F3):**  
  * Mapear F2 para salvar o arquivo .md local e F3 para disparar o POST na API do GitHub usando requests.  
  * *Verificação:* O arquivo é salvo no disco (F2) E a issue aparece no repositório remoto do GitHub (F3).

#### **Fase 4: Ligação Cirúrgica na CLI (src/main.py)**

*Meta: Conectar os módulos no ponto de entrada do usuário.*

* \[ \] **1\. Adicionar Opção:** Injetar a flag \-is / \--issue no decorator do Click.  
* \[ \] **2\. Orquestração:**  
  * Capturar o *diff* ➔ Chamar generate\_issue\_content ➔ Validar token ➔ Abrir TUI.  
  * *Verificação:* O comando gitpr \--issue executa o fluxo completo do início ao fim sem afetar os comandos de *commit* ou *review*.

