**Prompt Melhorado para Agente de Vibe Coding - Implementação de Smart Excludes Local por Projeto**

---

### **Contexto**
O sistema Smart Excludes do gitpr utiliza um arquivo global `~/.gitpr/conf/gitpr.smart-excludes.json` para definir extensões e pastas que devem ser removidas do `git diff`. É necessário implementar um arquivo local por projeto que permita configurações específicas, mesclando ambas as listas.

---

### **Regras de Desenvolvimento**

#### **1. Estrutura de Arquivos**
- **Arquivo global**: `~/.gitpr/conf/gitpr.smart-excludes.json`
  - Configurações que se aplicam a todos os projetos
  - Criado durante a instalação/configuração inicial do gitpr
- **Arquivo local**: `./.gitpr/conf/gitpr.smart-excludes.json`
  - Configurações específicas do projeto
  - Deve ser versionado no repositório do projeto
  - Sobrescreve ou mescla com as configurações globais

#### **2. Modificação da Função `core._load_smart_excludes()`**
- Carregar o arquivo global `~/.gitpr/conf/gitpr.smart-excludes.json`
- Carregar o arquivo local `./.gitpr/conf/gitpr.smart-excludes.json` se existir
- Mesclar ambas as listas antes de retornar
- Prioridade: arquivo local sobrescreve o global em caso de conflito
- Garantir que a lista final não contenha duplicatas

#### **3. Criação Automática de Arquivos**
- Durante a criação do arquivo global `~/.gitpr/conf/gitpr.smart-excludes.json`:
  - Criar também o arquivo local `./.gitpr/conf/gitpr.smart-excludes.json`
  - Iniciar com uma lista vazia ou com exemplos comentados
  - Adicionar instrução no arquivo sobre seu propósito

#### **4. Comportamento de Mesclagem**
- **Regra de mesclagem**: União das listas de extensões e pastas
- **Conflitos**: Lista local prevalece sobre a global
- **Ordem**: Não importa, apenas a existência do item
- **Formato**: Manter estrutura JSON consistente com o arquivo global

#### **5. Tratamento de Erros**
- Se arquivo global não existir: Criar com valores padrão
- Se arquivo local tiver formato inválido: Ignorar e prosseguir com global
- Logar aviso sobre arquivo local ignorado
- Se ambos os arquivos não existirem: Usar lista padrão vazia

#### **6. Mensagens de Log**
- "📂 Carregando smart-excludes global..."
- "📁 Carregando smart-excludes local do projeto..."
- "✅ Smart-excludes mesclados: X itens globais, Y itens locais"
- "⚠️ Arquivo local ignorado (formato inválido)"

#### **7. Casos de Uso**
- **Global**: Extensões comuns (ex: `*.log`, `*.tmp`, `*.lock`)
- **Local**: Pastas específicas do projeto (ex: `dist/`, `build/`, `node_modules/`)
- **Local**: Extensões específicas do framework (ex: `*.pyc`, `*.class`)

#### **8. Variáveis de Ambiente**
- `GITPR_SMART_EXCLUDES_GLOBAL`: Caminho alternativo para arquivo global
- `GITPR_SMART_EXCLUDES_LOCAL`: Caminho alternativo para arquivo local
- `GITPR_SKIP_SMART_EXCLUDES`: Boolean para desabilitar completamente

#### **9. Compatibilidade**
- Manter compatibilidade com sistemas que não têm a pasta `./.gitpr/conf/`
- Criar a estrutura de diretórios automaticamente se não existir
- Não quebrar funcionalidade existente para usuários sem arquivo local

#### **10. Documentação**
- Atualizar documentação técnica sobre Smart Excludes em @docs\smart-excludes.md e os outros idiomas
- Incluir exemplo de arquivo local no README.md e em seu outros idiomas.
- Adicionar seção explicando como configurar exclusões por projeto