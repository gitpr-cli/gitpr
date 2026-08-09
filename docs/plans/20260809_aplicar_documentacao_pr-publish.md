# Sincronização e Documentação das Funcionalidades de publicação de Pull Request

---

### **Contexto**
Foram implementadas diversas funcionalidades relacionadas à publicação de pull requests, reorganização de diretórios e gerenciamento de commits. É necessário consolidar toda a documentação técnica e atualizar o README principal com estas novas capacidades.

---

### **Objetivos**
1. Consolidar toda a documentação técnica no arquivo `docs/pull-request-publication.md`
2. Sincronizar a documentação com todos os idiomas suportados
3. Integrar as mudanças de reorganização de diretórios
4. Atualizar o README principal com as novas funcionalidades

---

### **Regras de Desenvolvimento**

#### **1. Consolidação da Documentação Técnica**
- **Arquivo alvo**: `docs/pull-request-publication.md`
- **Fontes a serem consolidadas**:
  - `2026-08-06_pr_publish_github.md` - Publicação de PR no GitHub
  - `2026-08-07_pr_publish_auto_commit.md` - Commit automático e linter
  - `2026-08-08_unstaged_files_reorganization.md` - Reorganização de arquivos unstaged
  - `2026-08-09_correcoes_confirmacao_commit.md` - Correções do fluxo de commit
  - `2026-08-06_reorganize_default_output_paths.md` - Reorganização de diretórios de saída

- **Estrutura do documento**:
  - Visão geral da funcionalidade de publicação
  - Configuração inicial (token, variáveis de ambiente)
  - Fluxo completo de publicação
  - Gerenciamento de arquivos unstaged
  - Commit automático com validação de linter
  - Verificação de PR existente
  - Tratamento de erros
  - Referência de comandos e tags
  - Variáveis de ambiente

#### **2. Sincronização com Outros Idiomas**
- Criar/atualizar os seguintes arquivos:
  - `docs/pull-request-publication.pt_br.md`
  - `docs/pull-request-publication.pt_pt.md`
  - `docs/pull-request-publication.fr.md`
  - `docs/pull-request-publication.es.md`
- Manter a mesma estrutura e conteúdo, apenas traduzido
- Utilizar o sistema i18n existente para consistência de terminologia

#### **3. Atualização do README**
- **Arquivo alvo**: `README.md`
- **Seções a serem atualizadas**:
  - Adicionar/atualizar seção sobre publicação de pull requests
  - Adicionar seção sobre reorganização de diretórios de saída
  - Atualizar exemplos de uso com as novas tags
  - Adicionar referência à documentação completa

- **Sincronizar com outros idiomas**:
  - `README.pt_br.md`
  - `README.pt_pt.md`
  - `README.fr.md`
  - `README.es.md`

#### **4. Conteúdo a ser Documentado**

**Publicação de Pull Requests**:
- Comportamento padrão com interface interativa
- Tags `--no-publish` e `--no-edit`
- Fluxo de commit automático com validação de linter
- Verificação de PR existente antes da criação
- Tratamento de erros e retry

**Reorganização de Diretórios de Saída**:
- Novo local padrão: `.gitpr/reports/{pasta_correspondente}/`
- Mapeamento de variáveis para pastas
- Compatibilidade com caminhos personalizados
- Criação automática de diretórios

**Gerenciamento de Arquivos Unstaged**:
- Verificação antecipada ao executar `gitpr`
- Modal de seleção de arquivos com checkboxes
- Opções de adicionar ao stage ou pular

#### **5. Verificações Obrigatórias**
- Garantir que todas as funcionalidades dos relatórios estejam documentadas
- Verificar consistência entre documentação técnica e README
- Validar que os exemplos de uso estão atualizados
- Confirmar que as variáveis de ambiente estão listadas
- Verificar links internos e externos

#### **6. Estrutura de Referência**
- **Comandos**:
  - `gitpr` - Comportamento padrão com interface
  - `gitpr --no-publish` - Apenas gera arquivo
  - `gitpr --no-edit` - Publica sem edição
- **Variáveis de Ambiente**:
  - `GITHUB_TOKEN` - Token de acesso ao GitHub
  - `PR_DEFAULT_BASE` - Branch base padrão
  - `GITPR_AUTO_COMMIT` - Commit automático
  - `GITPR_SKIP_LINT` - Pular validação de linter
  - `GITPR_AUTO_STAGE` - Stage automático de arquivos
  - `OUTPUT_FILE_NAME*` - Variáveis de saída

#### **7. Mensagens e Logs**
- Documentar mensagens exibidas ao usuário
- Incluir exemplos de saída esperada
- Descrever fluxos de erro e recuperação

#### **8. Atualização do CHANGELOG**
- Adicionar entrada com todas as novas funcionalidades
- Listar mudanças significativas (ex: novo local de arquivos)
- Indicar versão atualizada