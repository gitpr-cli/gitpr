# Documentação Técnica: Integração de Git Hooks Locais (GitPR)

Esta documentação detalha a arquitetura e o uso da funcionalidade de Git Hooks automáticos do GitPR CLI. A implementação adota a prática de ****Shift Left****, trazendo a validação de código e a geração de mensagens (IA) para o momento exato do commit, antes de qualquer integração com o servidor remoto.

---

## 1. Instalação Automatizada

Para instalar os hooks no seu repositório local, navegue até a raiz do projeto (onde a pasta oculta `.git` reside) e execute:

```bash  
gitpr --installhooks  
# ou  
gitpr -ih  
```

**O que este comando faz sob o capô:**

1. Verifica a integridade do diretório .git/hooks.  
2. Faz o download da versão mais recente dos scripts pre-commit e prepare-commit-msg diretamente do repositório oficial do GitPR.  
3. Aplica automaticamente as permissões de execução POSIX (chmod +x) aos arquivos, garantindo compatibilidade entre Linux, macOS e ambientes Git Bash no Windows.

---

## **2. Hook: pre-commit (Linter Estático)**

O hook de pre-commit atua como um "guarda-costas" local. Ele é disparado instantaneamente ao executar git commit, antes da mensagem de commit ser solicitada.

### **Como funciona:**

* O script invoca o comando gitpr --linter.  
* O GitPR analisa o diff atual (arquivos em *stage*) contra as regras definidas no arquivo .gitpr.linter.yml.  
* **Exit Code 0:** Se não houver violações, o fluxo do Git continua normalmente.  
* **Exit Code 1:** Se strings proibidas (ex: console.log, senhas, localhost) forem detectadas, o script intercepta a ação, exibe os alertas no terminal e **aborta o commit**.

### **Rota de Fuga (Bypass)**

Se houver uma necessidade estrita de contornar a validação do Linter local (por exemplo, ao subir um código temporário de debug numa branch isolada), utilize a flag nativa do Git:

Bash

git commit --no-verify -m "Sua mensagem aqui"

---

## **3. Hook: prepare-commit-msg (IA Auto-Commit)**

Este hook elimina a necessidade de escrever mensagens de commit manualmente. Ele integra a inteligência artificial do Gemini diretamente no ciclo de vida do Git, gerando mensagens no padrão *Conventional Commits* baseadas no seu código.

### **Como funciona:**

1. Adicione os seus arquivos ao stage (git add .).  
2. Execute apenas o comando base de commit, sem passar a mensagem:  
   ```bash  
   git commit
   ```

3. O hook entra em ação exibindo a mensagem: 🤖 GitPR: A pedir sugestão de commit à IA...  
4. O GitPR roda a flag oculta --hook, enviando o seu *diff* para o Gemini.  
5. A IA gera a mensagem e o script injeta o resultado de forma limpa na primeira linha do arquivo temporário do Git.  
6. O seu editor de texto padrão (Vim, Nano, VS Code) abrirá com a mensagem já preenchida. Basta salvar e fechar para confirmar o commit.

### **Preservação do Fluxo Manual**

O script é inteligente o suficiente para não sobrescrever a sua intenção. Se você executar o commit passando a flag de mensagem explícita (-m), o hook reconhece a origem como "message" e **desativa o processamento da IA silenciosamente**:

```bash

# A IA NÃO será acionada neste caso, respeitando a sua mensagem.  
git commit -m "fix: corrige problema de concorrência na API"
```

---

## **4. Resolução de Problemas (Troubleshooting)**

* **O Hook não executa (Linux/macOS):** Certifique-se de que os arquivos em .git/hooks têm permissão de execução. Você pode forçar com chmod \+x .git/hooks/pre-commit.  
* **Comando não encontrado:** Os scripts dos hooks estão configurados para procurar tanto a instalação global (gitpr) quanto a execução local via ambiente virtual (pipenv run python run.py). Se você estiver usando um gerenciador de dependências diferente (como Poetry), poderá ser necessário editar os scripts dentro da pasta .git/hooks para refletir o seu ambiente.

