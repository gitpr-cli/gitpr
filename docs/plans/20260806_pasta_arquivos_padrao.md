**Prompt Melhorado para Agente de Vibe Coding - Reorganização de Diretórios de Saída**

---

### **Contexto**
Atualmente, os arquivos gerados pelos comandos `gitpr` (pull request title/description, reviews, blame, issues) são salvos na raiz do projeto quando nenhum caminho específico é definido nas variáveis de ambiente. Esta abordagem polui o diretório raiz e dificulta a organização.

---

### **Objetivo**
Reorganizar o local padrão de salvamento dos arquivos gerados, centralizando-os no diretório `.gitpr/reports/` com subpastas correspondentes ao tipo de arquivo, mantendo a compatibilidade com caminhos personalizados definidos nas variáveis de ambiente.

---

### **Regras de Desenvolvimento**

#### **1. Variáveis Afetadas**
As seguintes variáveis de ambiente devem ter seu comportamento alterado:
- `OUTPUT_FILE_NAME` (pull request title/description)
- `OUTPUT_FILE_NAME_REVIEW` (review)
- `OUTPUT_FILE_NAME_FULLREVIEW` (full review)
- `OUTPUT_FILE_NAME_FILEREVIEW` (file review)
- `OUTPUT_FILE_NAME_BLAME` (blame)
- `OUTPUT_FILE_NAME_ISSUE` (issue)

#### **2. Comportamento de Salvamento**
- **Se a variável contiver um caminho completo com diretório** → usar o caminho especificado (comportamento atual)
- **Se a variável contiver apenas um nome de arquivo (sem barras)** → salvar em `.gitpr/reports/{pasta_correspondente}/` com o nome do arquivo
- **Se a variável estiver vazia ou não definida** → usar o nome padrão do arquivo e salvar em `.gitpr/reports/{pasta_correspondente}/`

#### **3. Mapeamento de Pastas Correspondentes**
Cada tipo de arquivo deve ser salvo na mesma estrutura de diretórios utilizada para cache/prompts:

| Variável                      | Pasta Correspondente |
| ----------------------------- | -------------------- |
| `OUTPUT_FILE_NAME`            | `pr_desc`            |
| `OUTPUT_FILE_NAME_REVIEW`     | `review`             |
| `OUTPUT_FILE_NAME_FULLREVIEW` | `full_review`        |
| `OUTPUT_FILE_NAME_FILEREVIEW` | `file_review`        |
| `OUTPUT_FILE_NAME_BLAME`      | `blame`              |
| `OUTPUT_FILE_NAME_ISSUE`      | `issue`              |

**Caminho completo**: `.gitpr/reports/{pasta_correspondente}/`

#### **4. Compatibilidade com Diretórios Personalizados**
- Manter suporte a caminhos relativos e absolutos nas variáveis
- Se o usuário especificar um caminho com diretório (ex: `./docs/reports/pr.md`), usar esse caminho
- Apenas aplicar a nova regra quando o valor da variável for um nome de arquivo sem barras

#### **5. Criação Automática de Diretórios**
- Criar automaticamente os diretórios `.gitpr/reports/` e subpastas quando necessário
- Garantir permissões de escrita

#### **6. Atualização da Documentação**
- Atualizar a documentação (README e arquivos de exemplo do `.env`) para refletir o novo comportamento
- Incluir exemplos de configuração com e sem caminhos personalizados
- Atualizar mensagens de log para mostrar o caminho completo onde o arquivo foi salvo
