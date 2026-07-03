# **Como Reverter um Commit no Git Localmente: Guia Completo**

No Git, a ação de "reverter" pode ser interpretada de duas maneiras distintas: desfazer uma alteração criando um novo histórico seguro (git revert) ou apagar/reescrever o histórico recente (git reset).  
Este guia detalha como utilizar cada uma dessas abordagens, seus impactos no código e em quais cenários elas devem ser aplicadas.

## **1. Encontrando o Hash do Commit**

Antes de executar qualquer comando de reversão, é necessário identificar o código (Hash) do commit que será alterado.  
Utilize o comando de log simplificado para visualizar o histórico:

Bash  
git log --oneline

A saída exibirá uma lista estruturada da seguinte forma:

Plaintext  
a1b2c3d (HEAD -> feature_ai_integration) feat: add gemini api support  
e4f5g6h fix: resolve parser error  
i7j8k9l docs: update readme instructions

**Nota:** O código de 7 caracteres no início de cada linha (ex: e4f5g6h) é o Hash do commit que você utilizará nos comandos abaixo.

## **2. A Rota Segura: git revert**

O comando git revert é a forma mais segura e recomendada de desfazer uma alteração. Ele **não apaga** o commit original. Em vez disso, gera um **novo commit** contendo as alterações inversas.

* **Quando utilizar:** Quando o commit já foi enviado (push) para um repositório remoto compartilhado (como o GitHub) ou integrado à branch principal (main).

**Como executar:**  
Para reverter um commit específico através do seu Hash:

Bash  
git revert e4f5g6h

Para reverter imediatamente o último commit da branch atual:

Bash  
git revert HEAD

Após a execução, o Git abrirá o editor de texto padrão do terminal solicitando a confirmação da mensagem do novo commit gerado (ex: Revert "fix: resolve parser error"). Salve e feche o editor para concluir a operação.

## **3. A Rota de Reescrita: git reset**

O comando git reset altera o ponteiro da branch atual, retornando-o para um estado anterior e removendo do histórico os commits subsequentes.

* **Quando utilizar:** Quando os commits existem **apenas no ambiente local** e ainda não foram enviados para o repositório remoto, ou quando há total certeza sobre a reescrita do histórico em uma branch isolada.

O comportamento do reset é definido por suas *flags*. Compreender a diferença entre elas é fundamental para evitar a perda de código.

### **3.1. Retendo código no Stage (--soft)**

Retorna o histórico, mas mantém todas as alterações dos arquivos **preparadas para um novo commit (Staged)**.

* **Cenário de uso:** Agrupar os últimos commits em um único commit (squash manual).  
* **Comando:**  
  Bash  
  git reset --soft HEAD~3

* **Resultado:** Os últimos 3 commits são removidos do log, mas as modificações de código permanecem intactas e prontas para um novo git commit.

### **3.2. Retendo código fora do Stage (--mixed ou padrão)**

Esta é a ação padrão. Retorna o histórico e mantém as modificações físicas nos arquivos, mas os remove da área de preparação **(Unstaged)**.

* **Cenário de uso:** Um commit foi feito com arquivos incorretos e é necessário selecionar novamente, um por um, o que deve ser adicionado.  
* **Comando:**  
  Bash  
  git reset HEAD~1

* **Resultado:** O último commit é desfeito. O código permanece inalterado no disco, mas precisará ser adicionado novamente via git add.

### **3.3. Descarte Total (--hard)**

**Atenção: Ação destrutiva.** Retorna o histórico e **destrói fisicamente** todas as alterações de código que ocorreram após o commit especificado.

* **Cenário de uso:** Uma implementação falhou completamente, o sistema local quebrou, e é necessário descartar todo o trabalho recente para retornar a um estado limpo e funcional.  
* **Comando:**  
  Bash  
  git reset --hard HEAD~1

* **Resultado:** O código e o histórico voltam exatamente ao estado do commit especificado. Todo o trabalho não salvo será perdido permanentemente.

## **4. Resumo de Boas Práticas**

| Situação | Comando Recomendado | Risco de Perda de Código |
| :---- | :---- | :---- |
| Código já está no servidor/compartilhado | git revert | Nenhum (Cria novo commit) |
| Refazer commits locais sem perder alterações | git reset --mixed ou --soft | Baixo (Código mantido localmente) |
| Descartar todo o trabalho recente e recomeçar | git reset --hard | **Alto** (Código apagado fisicamente) |

