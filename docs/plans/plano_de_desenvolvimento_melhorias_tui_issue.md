

### **📋 Plano de Desenvolvimento: Melhorias na TUI da Issue**

#### **Fase 1: Títulos e Rodapé Limpo (src/tui\_issue.py)**

* \[ \] Definir a constante TITLE \= "GitPR \- Gerador de Issues" na classe IssueApp para mudar o banner do topo.  
* \[ \] Definir a constante SUB\_TITLE para exibir a *Branch* e o *Repositório Remoto* dinamicamente.  
* \[ \] Inserir a flag ENABLE\_COMMAND\_PALETTE \= False para remover o ^p palette indesejado do rodapé.

#### **Fase 2: Labels e Layout**

* \[ \] Importar o componente Label do Textual.  
* \[ \] Injetar os Labels ("Título da Issue" e "Corpo da Issue") imediatamente acima dos campos Input e TextArea dentro do método compose.

#### **Fase 3: Modal de Ajuda (F1)**

* \[ \] Criar uma nova classe HelpScreen(ModalScreen) com um texto explicativo e um botão para fechar.  
* \[ \] Importar os componentes necessários (ModalScreen, Button).  
* \[ \] Adicionar o atalho Binding("f1", "show\_help", "Ajuda") no array BINDINGS.  
* \[ \] Criar o método action\_show\_help para renderizar o modal na tela quando F1 for pressionado.

