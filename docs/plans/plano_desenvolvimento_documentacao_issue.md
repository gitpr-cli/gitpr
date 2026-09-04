### **📋 Plano de Desenvolvimento Detalhado: Documentação \--issue**

#### **Fase 1: Criação dos Arquivos de Documentação (docs/)**

Nesta fase, criaremos os textos base que ficarão hospedados no repositório.

* \[ \] **1\. Criar docs/issue-tui-help.md:**  
  * **Objetivo:** Explicar o funcionamento da Interface Gráfica de Terminal (TUI) baseada na biblioteca Textual.  
  * **Conteúdo:** Detalhar a edição nativa no terminal, como os atalhos funcionam (F1 Ajuda, F2 Salvar Local, F3 Criar no GitHub), e como a IA estrutura o O Que / Por Que / Onde / Como.  
* \[ \] **2\. Criar docs/github-pat-integration.md:**  
  * **Objetivo:** Explicar a segurança e o motivo da integração via API REST.  
  * **Conteúdo:** Detalhar o porquê da exigência do *Personal Access Token* (PAT), explicar o escopo repo, como a URL de geração é montada dinamicamente pelo CLI, e como a chave é criptografada com segurança no arquivo \~/.gitpr/.env usando a biblioteca cryptography.

#### **Fase 2: Injeção dos Links Contextuais no Código (UX)**

Nesta fase, alteraremos o código Python para exibir os links de ajuda exatamente nos momentos de dúvida do usuário, seguindo o padrão de design que você já estabeleceu.

* \[ \] **1\. Atualizar a Solicitação do PAT:**  
  * **Arquivo:** src/tui\_issue.py (ou onde estiver a função validate\_or\_request\_github\_token).  
  * **Ação:** Adicionar um click.secho com o link para github-pat-integration.md logo abaixo da instrução que pede o token.  
  * **Trecho previsto:**  
    Python  
    click.secho("📚 Entenda por que precisamos do Token e como ele é protegido:", fg="cyan")  
    click.secho("👉 https://github.com/gitpr-cli/gitpr.git/blob/main/docs/github-pat-integration.md\\n", fg="blue", underline=True)

* \[ \] **2\. Atualizar o Modal de Ajuda da TUI:**  
  * **Arquivo:** src/ui/help\_screen.py (O modal de ajuda da interface Textual).  
  * **Ação:** Adicionar o link direto para issue-tui-help.md dentro do componente de texto (Static) do modal, para que o usuário possa ler o guia completo se os atalhos rápidos não forem suficientes.

#### **Fase 3: Atualização do README.md**

Nesta fase, integraremos a nova *feature* na vitrine do seu projeto.

* \[ \] **1\. Seção "Opções e Comandos Avançados":**  
  * **Ação:** Inserir a flag \-is na lista de comandos.  
  * **Trecho previsto:**  
    Markdown  
    \* \`-is\` ou \`--issue\`: Gera automaticamente o rascunho de uma **\*\*Issue padronizada\*\*** a partir das suas alterações e abre uma interface interativa (TUI) para edição, salvamento local ou envio direto para o repositório no GitHub via API.

* \[ \] **2\. Seção "Documentação Técnica e Guias Avançados":**  
  * **Ação:** Adicionar os links para os dois novos arquivos Markdown que criamos na Fase 1, mantendo o padrão da lista.  
  * **Trecho previsto:**  
    Markdown  
    \* \[\*\*Geração de Issues e Interface TUI\*\*\](docs/issue-tui-help.md): Como utilizar a interface gráfica de terminal para revisar e gerenciar Issues estruturadas.  
    \* \[\*\*Integração e Segurança do Token GitHub (PAT)\*\*\](docs/github-pat-integration.md): Entenda como o GitPR gera issues diretamente no seu repositório de forma segura utilizando criptografia local.  
