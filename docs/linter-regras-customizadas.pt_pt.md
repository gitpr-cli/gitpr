# **Documentação Técnica: Linter Estático Personalizável (--linter)**


O GitPR CLI possui um motor de análise estática ultrarrápido que corre localmente, sem consumir quotas de IA ou necessitar de ligação à internet. Ele analisa apenas as **linhas modificadas ou adicionadas** no seu git diff, garantindo feedback instantâneo.

## **1. Como Executar o Linter**

Pode acionar o linter de três formas:

1. **Manualmente:** Executando gitpr --linter no terminal.  
2. **Via Pre-commit Hook:** Automaticamente antes de cada commit (instalado via gitpr -ih).  
3. **Via CI/CD:** No GitHub Actions, bloqueando o merge caso o código devolva exit code 1.

---

## **2. Estrutura do Ficheiro .gitpr.linter.yml**

As regras do Linter vivem no ficheiro .gitpr.linter.yml na raiz do seu projeto. O ficheiro é lido a cada execução e possui a seguinte estrutura YAML:

```YAML

rules:  
  - name: "identificador-da-regra"  
    extensions: ["js", "php", "py"] \# Extensões onde a regra se aplica  
    regex: 'sua-expressao-regular-aqui'  
    message: "🚨 Mensagem de erro que aparecerá no terminal ({file\_name}, Linha {line\_number})"  
    ignore\_comments: true \# Ignora se a regex fizer match dentro de um comentário (//, \#, /\*)  
    ignore\_paths: \# Opcional: Pastas onde esta regra NÃO deve correr  
      \- "vendor/\*"  
    require\_paths: \# Opcional: Pastas exclusivas onde esta regra DEVE correr  
      \- "routes/\*"

## ---

## **3. Tutorial: Criar Regras com Expressões Regulares (Regex)**

O motor do GitPR usa a biblioteca nativa de Regex do Python (re). O segredo de uma boa regra de Linter é ser restritiva o suficiente para apanhar o erro, mas flexível o suficiente para ignorar espaços em branco extra.

### **Exemplo Prático 1: Proibir Verbos em Rotas (Padrão RESTful)**

**O Problema:** No padrão REST, as URLs não devem conter verbos (ex: /api/buscar-usuarios), mas sim substantivos e métodos HTTP adequados (GET /api/usuarios).

Veja como configurar uma regra no Laravel (PHP) para impedir isto:

```YAML

  \- name: "check-route-verbs"  
    extensions: \["php"\]  
    require\_paths:  
      \- "routes/\*"  
    regex: 'Route::\[a-zA-Z\]+\\s\*\\(\\s\*\[''"\](get|get-|busca|buscar|procura|procurar|pesquisa|pesquisar|lista|listar)'  
    message: "🚨 URI inadequada em {file\_name} (Linha {line\_number}). Evite verbos como 'buscar' ou 'listar' na URL. Use o padrão RESTful."  
    ignore\_comments: true

#### **Dissecar a Regex acima:**

Para perceber como criar as suas, veja como esta foi construída peça por peça:

* Route:: → Procura exatamente pela chamada da Facade do Laravel.  
* [a-zA-Z]+ → Captura qualquer método HTTP que venha depois (ex: get, post, put).  
* \s\*(\s\* → O \s\* significa "zero ou mais espaços". Isto garante que o Linter apanhe tanto Route::get(' quanto Route::get ( '.  
* [''"] → Aceita tanto aspas simples quanto duplas para abrir a string da URL.  
* (get|get-|busca|buscar...) → O grupo de captura principal. O pipe | funciona como um "OU". Se qualquer uma dessas palavras logo no início da URL for detetada, a regra falha.

### **Exemplo Prático 2: Bloquear Logs de Debug Esquecidos**

**O Problema:** Os programadores esquecem-se frequentemente de comandos de debug no código antes de fazer o commit.

**Regra para PHP (dd ou dump):**

```YAML

  \- name: "check-php-debug"  
    extensions: \["php"\]  
    regex: '\\b(dd|dump|var\_dump|print\_r)\\s\*\\('  
    message: "🚨 Código de debug esquecido ({file\_name}, Linha {line\_number})."  
    ignore\_comments: true

*Dica Regex:* O \b (Word Boundary) garante que a palavra seja exata. Ele apanha o comando dd(), mas ignora a palavra add(), evitando falsos positivos.

**Regra para JavaScript (console.log):**

```YAML

  - name: "check-js-console"  
    extensions: \["js", "ts", "vue"\]  
    regex: 'console\\.(log|debug|info)\\s\*\\('  
    message: "🚨 Uso de console.log não permitido em produção ({file\_name}, Linha {line\_number})."  
    ignore\_comments: true

*Dica Regex:* O ponto \. precisa de uma barra invertida (escape), pois na linguagem Regex, um ponto sozinho significa "qualquer caractere".

---

## **4. Dicas de Ouro para Regex no Linter**

1. **Faça escape dos caracteres especiais:** Símbolos como ( ) [ ] { } . \* \+ ? ^ $ têm funções matemáticas na Regex. Se quiser procurá-los no código, coloque uma barra antes (ex: \( para encontrar um parêntese aberto).  
2. **Cuidado com aspas no YAML:** No ficheiro .yml, envolva sempre a sua regex: com aspas simples '...'. Se a sua regex precisar de uma aspa simples dentro dela, duplique-a '' ou use aspas duplas por fora "...".  
3. **Use o \s\* sem moderação:** Nunca presuma que a formatação do código está perfeita. Use \s\* para cobrir espaços em branco, tabs e quebras de linha entre comandos.

---

