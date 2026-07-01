### **📋 Plano de Desenvolvimento: Motor Triplo de Issues (Híbrido)**

#### **Fase 1: Evolução Autônoma do Sistema de Cache (src/cache.py)**

*Meta: O cache descobre sozinho a branch atual e cria o resgatador de histórico.*

* \[ \] **1\. Atualizar save\_cached\_response():** Importar a função get\_current\_branch (ou implementar a leitura via subprocess localmente) dentro do src/cache.py para capturar a branch atual e gravá-la automaticamente em **todos** os arquivos .json gerados.  
* \[ \] **2\. Criar get\_cached\_pr\_descriptions(branch\_name):** Uma nova função no src/cache.py que vai varrer a pasta \~/.gitpr/cache/prompts/pr\_desc/, ler os JSONs que pertencem à branch solicitada e extrair os textos gerados pela IA no passado.

#### **Fase 2: Motor de Histórico Híbrido (src/core.py)**

*Meta: Juntar as informações do Git com as informações da IA.*

* \[ \] **1\. Criar get\_branch\_history\_text():** Função que executa git log origin/main..HEAD para pegar os commits reais e exclusivos da branch.  
* \[ \] **2\. Mesclar Contextos:** Esta mesma função chamará get\_cached\_pr\_descriptions(branch\_name), juntando o Log do Git com o Histórico de PRs Gerados em uma única string formatada para alimentar a Issue.

#### **Fase 3: Refatoração do Motor Arqueológico (src/blame\_engine.py)**

*Meta: Permitir que o Arqueólogo converse de forma invisível com o Gerador de Issues.*

* \[ \] **1\. Alterar run\_blame\_analysis():** Adicionar o parâmetro opcional return\_data=False. Quando for True (acionado via \--issue), a função pula os prints no terminal e a geração do arquivo .md, retornando diretamente a lista de dicionários da master\_timeline.

#### **Fase 4: Cérebro Adaptativo da IA (src/issue\_engine.py)**

*Meta: Ensinar a IA a ler 3 tipos diferentes de "idiomas" (Diff atual, Timeline de Blame, Histórico Híbrido da Branch).*

* \[ \] **1\. Alterar generate\_issue\_content(context\_text, context\_type="diff"):**  
  * Se context\_type \== "diff": O prompt instrui a IA a analisar o código novo.  
  * Se context\_type \== "blame": O prompt instrui a IA a analisar a evolução, idade e refatorações da regra.  
  * Se context\_type \== "history": O prompt instrui a IA a analisar o pacotão (Git Log \+ PRs Anteriores) para documentar a Release/Épico completa.

#### **Fase 5: Orquestração na CLI (src/main.py)**

*Meta: Criar as chaves no terminal para o usuário orquestrar esses fluxos.*

* \[ \] **1\. Adicionar Flag:** Incluir @click.option('-ht', '--history', is\_flag=True) no Click.  
* \[ \] **2\. Lógica de Roteamento (Switch):**  
  * Usuário rodou gitpr \-is \-ht: Executa Fase 1 e 2\.  
  * Usuário rodou gitpr \-is \-b arquivo.py: Executa Fase 3\.  
  * Usuário rodou gitpr \-is: Usa o diff padrão.

