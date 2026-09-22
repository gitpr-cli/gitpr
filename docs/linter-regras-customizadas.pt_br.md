# **Documentação Técnica: Linter Estático Customizável (--linter)**


O GitPR CLI possui um motor de análise estática ultrarrápido que roda localmente, sem consumir cotas de IA ou necessitar de conexão com a internet. Ele analisa apenas as **linhas modificadas ou adicionadas** no seu git diff, garantindo feedback instantâneo.

## **1. Como Executar o Linter**

Você pode acionar o linter de três formas:

1. **Manualmente:** Executando gitpr --linter no terminal.  
2. **Via Pre-commit Hook:** Automaticamente antes de cada commit (instalado via gitpr -ih).  
3. **Via CI/CD:** No GitHub Actions, bloqueando o merge caso o código retorne exit code 1.

---

## **2. Estrutura do Arquivo .gitpr.linter.yml**

As regras do Linter vivem no arquivo .gitpr.linter.yml em `.gitpr/skill/`. O arquivo é lido a cada execução e possui a seguinte estrutura YAML:

```YAML

rules:  
  - name: "identificador-da-regra"  
    level: "error"
    extensions: ["js", "php", "py"] \# Extensões onde a regra se aplica  
    regex: 'sua-expressao-regular-aqui'  
    message: "🚨 Mensagem de erro que aparecerá no terminal ({file\_name}, Linha {line\_number})"  
    ignore\_comments: true \# Ignora se a regex der match dentro de um comentário (//, \#, /\*)  
    ignore\_paths: \# Opcional: Pastas onde esta regra NÃO deve rodar  
      \- "vendor/\*"  
    require\_paths: \# Opcional: Pastas exclusivas onde esta regra DEVE rodar  
      \- "routes/\*"

external_linters:
  - name: "ESLint (JavaScript/TypeScript)"
    extensions: ["js", "ts", "vue", "jsx", "tsx"]
    command: "npx eslint --format checkstyle"

**`level`** decide o que um alerta faz. `"error"` (o padrão quando o campo está
ausente) é bloqueante: o `gitpr --linter` sai com código 1, que é o que aborta o
commit no pre-commit hook e reprova o job de CI. `"warning"` é informativo — o
alerta aparece no terminal e no relatório Markdown, e o código de saída continua
0. Qualquer valor diferente de `"warning"` é tratado como `"error"`, então um erro
de digitação nunca rebaixa uma regra bloqueante em silêncio.

**`extensions: ["*"]`** significa todos os arquivos, incluindo os que não têm
sufixo algum (`id_rsa`, `Dockerfile`, `Makefile`) e os dotfiles (`.env`). Sem o
curinga, uma regra só se aplica às extensões que você listar — uma regra com
`extensions: ["py"]` é pulada em todos os outros arquivos, e uma regra sem a
chave `extensions` nunca se aplica a nada.

## ---

## **3. Tutorial: Criando Regras com Expressões Regulares (Regex)**

O motor do GitPR usa a biblioteca nativa de Regex do Python (re). O segredo de uma boa regra de Linter é ser restritiva o suficiente para pegar o erro, mas flexível o suficiente para ignorar espaços em branco extras.

### **Exemplo Prático 1: Proibindo Verbos em Rotas (Padrão RESTful)**

**O Problema:** No padrão REST, as URLs não devem conter verbos (ex: /api/buscar-usuarios), mas sim substantivos e métodos HTTP adequados (GET /api/usuarios).

Veja como configurar uma regra no Laravel (PHP) para impedir isso:

```YAML

  \- name: "check-route-verbs"  
    extensions: \["php"\]  
    require\_paths:  
      \- "routes/\*"  
    regex: 'Route::\[a-zA-Z\]+\\s\*\\(\\s\*\[''"\](get|get-|busca|buscar|procura|procurar|pesquisa|pesquisar|lista|listar)'  
    message: "🚨 URI inadequada em {file\_name} (Linha {line\_number}). Evite verbos como 'buscar' ou 'listar' na URL. Use o padrão RESTful."  
    ignore\_comments: true

#### **Dissecando a Regex acima:**

Para entender como criar as suas, veja como essa foi construída peça por peça:

* Route:: → Procura exatamente pela chamada da Facade do Laravel.  
* [a-zA-Z]+ → Captura qualquer método HTTP que venha depois (ex: get, post, put).  
* \s\*(\s\* → O \s\* significa "zero ou mais espaços". Isso garante que o Linter pegue tanto Route::get(' quanto Route::get ( '.  
* [''"] → Aceita tanto aspas simples quanto duplas para abrir a string da URL.  
* (get|get-|busca|buscar...) → O grupo de captura principal. O pipe | funciona como um "OU". Se qualquer uma dessas palavras logo no início da URL for detectada, a regra falha.

### **Exemplo Prático 2: Bloqueando Logs de Debug Esquecidos**

**O Problema:** Desenvolvedores frequentemente esquecem comandos de debug no código antes de fazer o commit.

**Regra para PHP (dd ou dump):**

```YAML

  \- name: "check-php-debug"  
    extensions: \["php"\]  
    regex: '\\b(dd|dump|var\_dump|print\_r)\\s\*\\('  
    message: "🚨 Código de debug esquecido ({file\_name}, Linha {line\_number})."  
    ignore\_comments: true

*Dica Regex:* O \b (Word Boundary) garante que a palavra seja exata. Ele pega o comando dd(), mas ignora a palavra add(), evitando falsos positivos.

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

1. **Escape os caracteres especiais:** Símbolos como ( ) [ ] { } . \* \+ ? ^ $ têm funções matemáticas na Regex. Se quiser procurar por eles no código, coloque uma barra antes (ex: \( para achar um parêntese aberto).  
2. **Cuidado com aspas no YAML:** No arquivo .yml, envolva a sua regex: sempre com aspas simples '...'. Se a sua regex precisar de uma aspa simples dentro dela, duplique-a '' ou use aspas duplas por fora "...".  
3. **Use o \s\* sem moderação:** Nunca presuma que a formatação do código está perfeita. Use \s\* para cobrir espaços em branco, tabs e quebras de linha entre comandos.

---

## **5. Integração com Linters Externos (Bridge via Checkstyle)**

O GitPR CLI não precisa reinventar a roda. Se o seu projeto já usa ferramentas como PHP_CodeSniffer, ESLint ou Stylelint, o GitPR pode atuar como uma ponte, executando essas ferramentas em background e filtrando os erros **apenas para as linhas que você alterou no seu Pull Request atual**.

Para isso, o linter externo precisa suportar a saída de relatórios no formato `checkstyle` (padrão universal em CI/CD).

### **Timeout do Linter Externo**

Cada subprocesso de linter externo é limitado por um **timeout de 120 segundos**
(configurável via `GITPR_LINTER_TIMEOUT` em `~/.gitpr/.env`). Se um linter
exceder o limite, ele é pulado — suas violações não entram no relatório — em
vez de bloquear toda a revisão. Valores inválidos ou não positivos voltam ao
padrão de 120s.

### **Como Configurar Rapidamente (--linter-setup)**

Em vez de configurar o YAML manualmente, você pode usar nosso assistente interativo:
Execute no terminal:
`gitpr --linter-setup`

O assistente exibirá opções pré-configuradas, orientará você sobre o comando de instalação no seu projeto (ex: `npm install --save-dev eslint`) e injetará a configuração correta automaticamente no seu `.gitpr.linter.yml`.

Os presets do assistente são controlados remotamente pelo arquivo `templates/gitpr.linter-presets.json` (cache local em `~/.gitpr/conf/`), permitindo adicionar novos linters sem esperar por uma nova versão do GitPR.

---

## **6. Relatórios de Análise (Markdown)**

Toda vez que o linter rodar (seja manualmente via `--linter` ou automaticamente antes do commit), ele irá consolidar os erros gerados pelas Regras de Regex e pelos Linters Externos em um relatório único.

Este relatório formatado em Markdown será salvo automaticamente, mantendo um histórico das suas auditorias locais. 

**Localização Padrão:** `.gitpr/reports/linter/`

**Customização:** Você pode alterar o nome e a pasta deste arquivo definindo a variável `OUTPUT_FILE_NAME_LINTER` no seu arquivo `~/.gitpr/.env`.

---

## **7. Varredura de Segredos Embutida**

O GitPR traz um conjunto de regras de segurança que roda em **toda** execução do
linter, seja acionada por você (`gitpr --linter`), pelo pre-commit hook
(`gitpr -ih`) ou pela CI. Elas não precisam de nenhum `.gitpr.linter.yml` seu —
um projeto sem nenhuma regra customizada continua sendo varrido.

Elas vivem no pacote (`src/security_ruleset.py`), e não num template baixado, para
serem idênticas em toda máquina e não poderem ser substituídas por um download do
`--skill` nem reescritas pelo assistente de configuração.

### **O que bloqueia e o que apenas reporta**

| Regra | Procura | Nível |
|-------|---------|-------|
| `sec-aws-access-key` | AWS access key ID (`AKIA…`) | **error** |
| `sec-github-token` | Token do GitHub (`ghp_…`) | **error** |
| `sec-slack-token` | Token do Slack (`xoxb-…`) | **error** |
| `sec-google-api-key` | Chave de API do Google (`AIza…`) | **error** |
| `sec-private-key-block` | `-----BEGIN … PRIVATE KEY-----` | **error** |
| `sec-db-connection-string` | URL de banco de dados com senha | warning |
| `sec-generic-credential-assignment` | `password = "…"`, `token = "…"`, `api_key = "…"` | warning |

As cinco regras de `error` bloqueiam: o commit é abortado e o `--linter` sai com
código 1. São padrões que provam a si mesmos — uma string que casa com o formato
de uma chave da AWS é uma chave da AWS. As duas de `warning` reportam sem
bloquear, porque uma connection string ou uma linha `password = "…"` aparecem
legitimamente em exemplos, fixtures e documentação. A regra genérica ignora os
placeholders de sempre (`changeme`, `xxxxxx`, `example`, `dummy`, `sample`,
`your_password_here`, `sua_senha`), para que um template não trave um commit.

As regras casam em **todos os arquivos** (`extensions: ["*"]`), que é como
`id_rsa`, `.env`, `Dockerfile` e lockfiles ficam cobertos — os arquivos de onde
segredo de fato vaza. No modo `--input` isso significa que `.md` e `.txt` também
são varridos; eles são reportados, nunca bloqueados.

**Um alerta nunca imprime o valor que casou** — apenas o arquivo e a linha. A
mensagem chega ao terminal, ao relatório Markdown e, no fluxo de PR, ao corpo do
pull request; ecoar o segredo o copiaria para os três.

### **Como desligar**

Duas chaves no `~/.gitpr/.env`, ambas editáveis na tela de configuração na
categoria `linter`:

```bash
# Desligar o conjunto inteiro
GITPR_LINTER_SECURITY=false

# Ou remover regras específicas pelo nome, separadas por ponto e vírgula
GITPR_LINTER_SECURITY_DISABLED_RULES=sec-db-connection-string;sec-slack-token
```

O conjunto vem **ligado por padrão**, e só um valor negativo reconhecido
(`false`, `0`, `no`, `off`, `n`) o desliga — um valor vazio ou desconhecido o
mantém rodando, então um erro de digitação não desativa a varredura em silêncio.
A primeira execução do produto semeia as duas chaves no `~/.gitpr/.env`, então o
opt-out é uma edição de uma linha em vez de uma chave que você precisa conhecer.

### **Lacunas conhecidas nesta versão**

* Uma atribuição sem aspas **não** é pega: `API_KEY=abc123` — o formato do `.env`,
  que é justamente onde segredo vaza. A regra genérica exige aspas.
* Faltam alguns prefixos: `ASIA…` (credenciais temporárias da AWS), `github_pat_…`
  e `xoxc-`/`xoxd-` (tokens de usuário do Slack).
* A regra genérica não tem fronteira à esquerda no nome da chave: `mytoken` casa
  exatamente como `token`, então uma variável que apenas termina com uma
  palavra-chave é reportada.

São lacunas deliberadas, e não descuidos, mantidas estreitas para que o conjunto
continue confiável; um linter que grita demais é um linter que as pessoas desligam.
