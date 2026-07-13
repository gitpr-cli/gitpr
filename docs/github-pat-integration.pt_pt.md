# Documentação Técnica: Integração e Segurança do Token GitHub (PAT)

Para que a funcionalidade de criação direta de Issues (`gitpr --issue`) funcione de forma automatizada, o GitPR precisa de comunicar com a **API REST do GitHub**. Esta documentação explica como essa autenticação ocorre e como as suas credenciais são protegidas localmente.

📖 **Documentação relacionada:** [Guia da opção `--issue` (gitpr-issue-option.md)](gitpr-issue-option.md)

## 1. Porque precisamos de um Token (PAT)?
A criação de issues em repositórios remotos de forma programática exige autenticação. O GitHub recomenda a utilização de um **Personal Access Token (PAT)** para que ferramentas de linha de comandos (CLI) possam interagir com a sua conta de programador de forma segura.

## 2. Âmbito Necessário (`repo`)
O GitPR precisa apenas do âmbito **`repo`** ativado no momento da criação do seu PAT. Isto garante permissão para ler os metadados e criar a Issue no projeto correto (seja ele privado ou público). 
Para agilizar este processo, o próprio CLI gera uma URL de configuração dinâmica. Ele extrai o nome do seu repositório local e monta uma ligação que abre no seu navegador com as opções corretas já pré-selecionadas.

## 3. Segurança e Encriptação Local (Design Patterns)
A segurança das suas credenciais é tratada com extrema seriedade. O GitPR **nunca** envia a sua chave para servidores de terceiros que não sejam a própria API do GitHub.

* **Encriptação Simétrica (Fernet):** Assim que cola o seu Token no terminal, o GitPR utiliza a biblioteca nativa `cryptography` para encriptar a string em tempo real.
* **Armazenamento Seguro:** O token encriptado é guardado de forma permanente no ficheiro global `~/.gitpr/.env` (na pasta raiz do seu utilizador, inacessível a outros utilizadores do sistema operativo).
* **Chave Mestra de Desencriptação:** A chave mestra necessária para reverter essa encriptação fica isolada na sua máquina local (`~/.gitpr/secret.key`). 
    
Graças a esta arquitetura, caso ocorra uma fuga local e um script malicioso leia o seu ficheiro `.env`, o seu Token do GitHub continuará absolutamente ilegível e protegido.