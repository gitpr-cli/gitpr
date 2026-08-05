# 🚀 Criação e Gestão de Issues com o GitPR CLI

A funcionalidade `--issue` (ou `-is`) transforma o GitPR num assistente avançado de documentação. Em vez de escrever Issues do zero, a Inteligência Artificial lê o seu contexto de trabalho, estrutura a issue no padrão **O Que / Por Que / Onde / Como** e abre uma interface visual diretamente no seu terminal para revisar antes do envio.

---

## 1. O Motor Triplo de Contexto (Qual usar e porquê?)

A IA do GitPR pode ler três "idiomas" diferentes dependendo da combinação de flags que utilizar. Cada motor foi pensado para um cenário específico do dia a dia do desenvolvedor:

### 🆕 Issue de Código Novo (O Padrão)
**Comando:** `gitpr --issue` ou `gitpr -is`
* **Como funciona:** O GitPR lê o seu `git diff` atual (as alterações que acabou de fazer e ainda não enviou/acrescentou ao commit).
* **Porquê usar:** Ideal para documentar rapidamente uma pequena *feature* ou *bugfix* que acabou de programar, garantindo que o rastreio do problema fica registado no GitHub antes de enviar o código.

### 📦 Issue de Release / Épico
**Comando:** `gitpr -is -ht` (Issue + History)
* **Como funciona:** O GitPR compila todo o `git log` da branch atual e soma com o banco de memórias da própria IA (procurando descrições de PRs antigos dessa branch na cache local).
* **Porquê usar:** Se trabalhou durante vários dias numa branch, este comando gera uma super issue resumindo a *feature* inteira. Excelente para entregar documentação consolidada de uma Release para a equipa de QA ou Produto.

### 🕰️ Issue Arqueológica / Dívida Técnica
**Comando:** `gitpr -is -b src/arquivo.py:10-20` (Issue + Blame)
* **Como funciona:** O GitPR não olha para o código novo. Ele aciona o Motor Arqueológico para ler a linha do tempo e a evolução daquelas linhas específicas no passado.
* **Porquê usar:** Ideal para documentar dívidas técnicas. A IA estrutura uma issue explicando como uma regra de negócio legada evoluiu com o tempo, por que se tornou um problema e qual é o fundamento para uma futura refatoração.

---

## 2. Autenticação e o Token PAT

Para que o GitPR consiga criar a Issue diretamente no seu repositório remoto, precisa de se comunicar com a **API REST do GitHub**.

1. Na primeira vez que executar o comando, a ferramenta solicitará um **Personal Access Token (PAT)**.
2. O GitPR gera uma ligação inteligente e exibe no terminal. Basta clicar nela: o seu navegador abrirá diretamente na página de criação de tokens do GitHub com a permissão correta (`repo`) já pré-selecionada.
3. Cole o token no terminal. 

**Segurança:** O seu token nunca trafega em texto limpo. Assim que o cola, o GitPR utiliza a biblioteca `cryptography` para encriptar a chave simetricamente, guardando apenas o hash seguro no ficheiro oculto `~/.gitpr/.env` da sua máquina.

---

## 3. A Interface Gráfica de Terminal (TUI)

Após a IA processar o contexto e estruturar a Issue, o GitPR não envia os dados às cegas. Abrirá uma interface interativa baseada na biblioteca `textual`.

Nesta ecrã azul elegante, pode editar livremente o Título e o Corpo da issue. Quando estiver satisfeito, utilize os atalhos de teclado rápidos (sem precisar de rato):

* **`F4` (Ajuda):** Abre um modal com explicações rápidas sobre a interface.
* **`F2` (Guardar Local):** Exporta o conteúdo do ecrã para um ficheiro Markdown (`.md`) na sua pasta atual. Útil se pretender apenas o rascunho para refinar mais tarde.
* **`F3` (Criar no GitHub):** Dispara o pedido oficial. Em segundos, o GitPR fecha o ecrã e exibe no terminal a ligação verde da sua nova issue já criada e publicada no repositório.
* **`Esc` (Sair):** Aborta a operação com segurança sem guardar nada.
