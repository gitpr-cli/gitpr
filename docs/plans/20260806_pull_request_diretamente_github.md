**Prompt Melhorado para Agente de Vibe Coding - Interface de Publicação de Pull Requests**

---

### **Contexto**
O comando `gitpr` gera um arquivo contendo a sugestão de pull request (título, descrição, resumo técnico e impacto). Atualmente, este arquivo é salvo localmente. É necessário implementar uma interface textual interativa que permita ao usuário publicar diretamente o pull request no GitHub a partir do conteúdo gerado.

---

### **Objetivo**
Criar uma interface no terminal que:
1. Exiba o conteúdo gerado do pull request de forma estruturada
2. Permita ao usuário editar campos antes da publicação
3. Publique o pull request no GitHub via API
4. Retorne a URL do pull request criado

---

### **Regras de Desenvolvimento**

#### **1. Interface Textual**
- Utilizar a biblioteca textual (ex: `textual`) para construir a interface interativa
- A interface deve ser executada após a geração do arquivo, seja automaticamente ou via comando específico (ex: `gitpr --publish`)
- Exibir as seções do pull request em painéis ou abas:
  - Título
  - Mensagem de commit
  - Resumo (summary)
  - Alterações técnicas (technical changes)
  - Impacto/avisos (impact/warnings)

#### **2. Funcionalidades da Interface**
- **Visualização**: Exibir todo o conteúdo do pull request formatado
- **Edição**: Permitir edição inline de cada seção antes da publicação
- **Validação**: Verificar campos obrigatórios (título, descrição)
- **Confirmação**: Solicitar confirmação final antes de publicar
- **Progresso**: Exibir progresso durante a criação do pull request
- **Resultado**: Mostrar a URL do pull request criado e oferecer opção de abrir no navegador

#### **3. Integração com GitHub**
- Utilizar token de acesso pessoal do GitHub configurado no `.env` (ex: `GITHUB_TOKEN`)
- Obter informações do repositório a partir do `git remote` ou variáveis de ambiente
- Utilizar a API REST do GitHub para criar o pull request
- Campos a serem enviados:
  - `title`: Título do pull request
  - `body`: Corpo completo do pull request (todas as seções)
  - `head`: Branch atual (branch de origem)
  - `base`: Branch base (configurável ou `main`/`develop` padrão)

#### **4. Configurações**
- Adicionar variáveis no `.env`:
  - `GITHUB_TOKEN`: Token de acesso pessoal
  - `PR_DEFAULT_BASE`: Branch base padrão (ex: `main`)
  - `PR_AUTO_PUBLISH`: Booleano para publicar automaticamente sem interface (opcional)
- Permitir sobrescrever configurações via argumentos de linha de comando:
  - `--publish`: Abrir interface para publicar após gerar
  - `--base <branch>`: Especificar branch base
  - `--no-edit`: Pular edição e publicar diretamente

#### **5. Fluxo de Execução**
1. Gerar o conteúdo do pull request (comportamento atual)
2. Salvar o arquivo (comportamento atual)
3. Se `--publish` ou `PR_AUTO_PUBLISH=true`:
   - Abrir interface textual
   - Exibir conteúdo gerado
   - Aguardar interação do usuário (edição, confirmação)
   - Enviar para API do GitHub
   - Exibir resultado

#### **6. Tratamento de Erros**
- Verificar token do GitHub antes de abrir a interface
- Validar branch base e head existentes no repositório
- Capturar e exibir erros da API (ex: branch não encontrada, conflitos)
- Oferecer opção de retry em caso de falha
- Salvar o conteúdo editado localmente como backup

#### **7. Mensagens de Log**
- Exibir passo a passo durante a publicação:
  - "Conectando ao GitHub..."
  - "Validando branches..."
  - "Criando pull request..."
  - "✅ Pull request criado: https://github.com/.../pull/123"

#### **8. Persistência**
- Manter o arquivo local salvo mesmo após publicação
- Adicionar metadados no arquivo (ex: data de publicação, URL)
- Se o arquivo for editado na interface, salvar versão atualizada localmente

#### **9. Segurança**
- Garantir que o token não seja exposto em logs ou interfaces
- Utilizar variáveis de ambiente para token
- Evitar armazenar token em arquivos de cache
