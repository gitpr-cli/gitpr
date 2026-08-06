# Documentação e Internacionalização para scripts Git hooks

`20260805_documentação_internacionalizacao_scripts_githooks.md` 
---

## **Contexto**
Foi implementado um novo sistema de **versionamento e sincronização de hooks do Git** com suporte a i18n, conforme documentado no arquivo `@docs/claude-code/reports/develop_natan/2026-08-05_hooks-versioning-i18n-sync.md`. Agora é necessário **documentar essa funcionalidade** e **integrar com o sistema de URLs** existente para fornecer uma experiência completa ao usuário.

---

## **Objetivos Gerais**
1. **Documentar a funcionalidade** no README em todos os idiomas suportados
2. **Criar documentação técnica dedicada** no diretório `docs/` em todos os idiomas
3. **Integrar com `get_docs_url()`** para exibir links diretos durante atualizações dos scripts

---

## **Tarefas Detalhadas**

### **1. Atualização dos READMEs**

**Arquivos a serem modificados/criados:**
```
README.md                    # Inglês (padrão)
README.pt_br.md              # Português Brasil
README.pt_pt.md              # Português Portugal
README.fr.md                 # Francês
README.es.md                 # Espanhol
```

**Conteúdo a ser adicionado:**
- **Nova seção:** "🔄 Hook Scripts Versioning & Auto-Sync"
- **Descrição do sistema:**
  - Explicação do versionamento (`__scripts_version__` e `SCRIPTS_VERSION`)
  - Como funciona a sincronização automática
  - Suporte a múltiplos idiomas nos scripts
  - Como o sistema detecta e instala a versão correta
- **Exemplo de uso:**
  ```bash
  # Ao executar gitpr, os scripts são verificados e atualizados
  gitpr
  # Output: 🔄 Atualizando scripts para v0.0.1 (pt_br)...
  ```
- **Link para documentação completa** usando `get_docs_url()`

**Exemplo de texto (Inglês):**
```markdown
## 🔄 Hook Scripts Versioning & Auto-Sync

GitPR now includes an automatic versioning system for Git hook scripts. 
When you run `gitpr`, it:
1. Checks the current version of installed scripts
2. Compares with the latest version available
3. Automatically updates scripts if a new version is found
4. Respects your language preference (English, PT-BR, PT-PT, FR, ES)

📚 [Full Documentation](https://docs.gitpr.dev/hooks-versioning)
```

---

### **2. Documentação Técnica em `docs/`**

**Arquivos a serem criados:**
```
docs/
├── hooks-versioning.md          # Inglês (padrão)
├── hooks-versioning.pt_br.md    # Português Brasil
├── hooks-versioning.pt_pt.md    # Português Portugal
├── hooks-versioning.fr.md       # Francês
└── hooks-versioning.es.md       # Espanhol
```

**Estrutura do documento:**
```markdown
# Hook Scripts Versioning and Synchronization

## Overview
Breve descrição do sistema.

## Architecture
## Version Control
- `__scripts_version__` em `src/updater.py`
- `SCRIPTS_VERSION` em `~/.gitpr/.env`

## Supported Languages
- Inglês (padrão)
- Português do Brasil
- Português de Portugal
- Francês
- Espanhol

## How It Works
1. Verificação de versão
2. Detecção de idioma
3. Download/instalação dos scripts
4. Atualização dos hooks

## Configuration
Variáveis de ambiente e configurações.

## Troubleshooting
Problemas comuns e soluções.

## API Reference
Funções e métodos relacionados.
```

**Requisitos de tradução:**
- Manter a mesma estrutura em todos os idiomas
- Traduzir **todos os títulos, parágrafos e exemplos de código**
- Preservar nomes de arquivos, funções e variáveis em inglês
- Incluir exemplos de saída no idioma correspondente

---

### **3. Integração com `get_docs_url()`**

**Arquivo de referência:** `@docs\i18n_explanation.md`

**Função a ser utilizada:**
```python
def get_docs_url(path: str, lang: str = None) -> str:
    """
    Retorna a URL correta para a documentação baseada no idioma.
    
    Args:
        path: Caminho do documento (ex: 'hooks-versioning')
        lang: Código do idioma (ex: 'pt_br', 'en')
    
    Returns:
        URL completa da documentação no idioma apropriado
    """
```

**Implementação no CLI:**

Quando os scripts forem atualizados, exibir:
```python
# Em src/updater.py ou src/core.py
def display_update_notification(version, lang):
    docs_url = get_docs_url('hooks-versioning', lang)
    print(f"\n✅ Scripts atualizados para versão {version}")
    print(f"📚 Documentação disponível em: {docs_url}")
    print(f"   (Para mais detalhes sobre o sistema de versionamento)")
```

**Exemplo de saída no CLI:**
```
🔄 Atualizando scripts para v0.0.1...
   Idioma detectado: pt_br
   ✅ pre-push atualizado
   ✅ prepare-commit-msg atualizado
   ✅ pre-commit atualizado
   ✅ post-merge atualizado
   ✅ post-checkout atualizado
💾 SCRIPTS_VERSION atualizado no ~/.gitpr/.env
✅ Scripts sincronizados com sucesso!

📚 Documentação disponível em: https://docs.gitpr.dev/pt_br/hooks-versioning
   (Para mais detalhes sobre o sistema de versionamento)
```

---

### **4. Estrutura de URLs Esperada**

**Mapeamento de idiomas para URLs:**
- `en` → `https://docs.gitpr.dev/hooks-versioning`
- `pt_br` → `https://docs.gitpr.dev/pt_br/hooks-versioning`
- `pt_pt` → `https://docs.gitpr.dev/pt_pt/hooks-versioning`
- `fr` → `https://docs.gitpr.dev/fr/hooks-versioning`
- `es` → `https://docs.gitpr.dev/es/hooks-versioning`

---

## **Critérios de Aceite**
- [ ] README atualizado em todos os 5 idiomas com a nova seção
- [ ] 5 arquivos de documentação criados em `docs/` (um por idioma)
- [ ] Todos os documentos traduzidos corretamente
- [ ] `get_docs_url()` integrado no fluxo de atualização de scripts
- [ ] URL correta exibida no CLI quando scripts são atualizados
- [ ] Fallback para inglês quando o idioma não está disponível
- [ ] Links funcionando (verificar se as URLs estão corretas)
- [ ] Documentação inclui exemplos práticos e casos de uso

---

## **Exemplo de Comportamento Esperado**

**Quando um usuário executa `gitpr` pela primeira vez:**
```bash
$ gitpr
🔄 Verificando versão dos scripts...
   ⚠️ Nenhuma versão encontrada. Instalando scripts...
   Idioma: pt_br
   ✅ Scripts instalados com sucesso (v0.0.1)

📚 Documentação disponível em: https://docs.gitpr.dev/pt_br/hooks-versioning
   (Para mais detalhes sobre o sistema de versionamento)
```

**Quando há uma nova versão disponível:**
```bash
$ gitpr
🔍 Verificando versão dos scripts...
   Atual: v0.0.1 (do .env)
   Última: v0.0.2 (do código)
📦 Atualizando scripts para v0.0.2...
   Idioma: pt_br
   ✅ Todos os hooks atualizados

📚 Documentação disponível em: https://docs.gitpr.dev/pt_br/hooks-versioning
   (Veja o changelog e novidades da v0.0.2)
```

---

## **Notas Técnicas**
- Use o mesmo sistema de i18n já implementado para os scripts
- Mantenha a consistência de terminologia entre README, docs e código
- Considere adicionar um comando `gitpr docs` para abrir a documentação no navegador
- Atualize o changelog para refletir essa nova funcionalidade
- Verifique se a URL base (ex.: `https://docs.gitpr.dev/`) está configurada corretamente no `get_docs_url()`

---

## **Arquivos a Serem Modificados/Criados**
```
README.md
README.pt_br.md
README.pt_pt.md
README.fr.md
README.es.md
docs/hooks-versioning.md
docs/hooks-versioning.pt_br.md
docs/hooks-versioning.pt_pt.md
docs/hooks-versioning.fr.md
docs/hooks-versioning.es.md
src/updater.py (adicionar chamada get_docs_url)
src/core.py (adicionar chamada get_docs_url)
```

---

## **Links Úteis**
- [Documentação i18n](@docs/i18n_explanation.md)
- [Relatório de Implementação](@docs/claude-code/reports/develop_natan/2026-08-05_hooks-versioning-i18n-sync.md)
- [Semantic Versioning](https://semver.org/)