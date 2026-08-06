# Verificação e Validação de Internacionalização (i18n)  

`20250805_verificacao_validacao_internacionalizacao_i18n.md` 

---

## **Contexto**
O sistema `gitpr` utiliza internacionalização (i18n) para suportar múltiplos idiomas através da função `__()` que gerencia traduções. 
Os arquivos de tradução estão localizados em `langs/` e contêm as chaves e valores para cada idioma suportado. 
É necessário garantir que **todas as strings marcadas com `__()`** no código-fonte estejam **presentes e devidamente traduzidas** em todos os arquivos de idioma.

O inglês não tem arquivo pois ele e o padrão nos arquivos, ou seja o fallback se não tiver arquivo do idioma.

---

## **Objetivo Geral**
Realizar uma **auditoria completa de internacionalização** nos arquivos `src/core.py` e `src/updater.py`, verificando:
1. Todas as ocorrências da função `__()` estão corretamente implementadas
2. Todas as chaves de tradução estão definidas em todos os arquivos de idioma
3. Todas as traduções estão completas e precisas para os 5 idiomas suportados
4. Nenhuma chave esta duplicada.

---

## **Tarefas Detalhadas**

### **1. Análise dos Arquivos-Fonte**

**Arquivos a serem verificados:**
- `src/core.py`
- `src/updater.py`

**O que verificar em cada arquivo:**

#### **1.1. Identificação de Strings**
- Localizar **todas as ocorrências** da função `__()`
- Extrair os **valores padrão** (em inglês) eles são as chaves. 
- Verificar se há **strings "hardcoded"** (sem i18n) que deveriam ser traduzidas


#### **1.2. Verificação de Formatação**
- Verificar se strings com **placeholders** (ex: `{version}`, `{lang}`) estão corretas
- Validar se todos os placeholders são mantidos nas traduções

---

### **2. Auditoria dos Arquivos de Idioma**

**Arquivos a serem verificados:**
```
langs/
├── pt_br.json       # Português Brasil
├── pt_pt.json       # Português Portugal
├── fr.json          # Francês
└── es.json          # Espanhol
```

**Estrutura esperada:**
```json
{
  "\\n✅ Setup wizard complete!": "\\n✅ Assistente de configuração concluído!",
  "\\n❌ Error saving review: {error}\", error=str(e)), fg=\"red": "\\n❌ Erro ao salvar a avaliação: {error}\", error=str(e)), fg=\"red",
  "\\n❌ Error: No internet connection.": "\\n❌ Erro: Sem conexão com a internet."  
}
```

**O que verificar:**
- [ ] Todas as chaves do código estão presentes em **todos** os arquivos JSON
- [ ] Traduções estão **completas** (nenhuma chave vazia ou faltando)
- [ ] Traduções estão **corretas** (qualidade linguística)
- [ ] Validar se todas as chaves estão traduzidas em todos os idiomas.
- [ ] Placeholders são **preservados** nas traduções (ex: `{version}`)
- [ ] **Semântica** é mantida (o significado original é preservado)
- [ ] **Formatação especial** (ex: `\n`, `\t`) é mantida

**Atenção**: nuca remova nenhuma chave de nenhum arquivo, todos os arquivos devem ter a mesma quantidade de chaves
---

### **3. Verificação de Consistência**

#### **3.1. Mapeamento de Chaves**
Criar um mapeamento entre:
- Chaves encontradas no código (em `core.py` e `updater.py`)
- Chaves definidas em cada arquivo de idioma

**Exemplo de mapeamento:**
```python
# Chaves encontradas em src/core.py
CODE_KEYS = [
  "\\n✅ Setup wizard complete!",
  "\\n❌ Error saving review: {error}\", error=str(e)), fg=\"red",
  "\\n❌ Error: No internet connection."
]

# Comparar com cada arquivo de idioma
for lang in ['en', 'pt_br', 'pt_pt', 'fr', 'es']:
    lang_keys = load_lang_file(f'langs/{lang}.json').keys()
    missing = set(CODE_KEYS) - set(lang_keys)
    if missing:
        print(f"❌ {lang} missing keys: {missing}")
```

#### **3.2. Validação de Placeholders**

Verificar se os placeholders nas traduções correspondem aos do código:
```python
# Código
click.secho(__("❌ Error calculating diff: {error}", error=e.stderr), fg="red")

# Tradução correta (pt_br)
"❌ Error calculating diff: {error}": "Erro ao calcular a diferença: {error}"

# Tradução incorreta (es) - FALTANDO PLACEHOLDER
"❌ Error calculating diff: {error}": "Erro ao calcular a diferença."
```

---

### **4. Ações Corretivas**

#### **4.1. Para Chaves Faltantes**
- Adicionar a chave em todos os arquivos de idioma
- Fornecer tradução correta baseada no contexto

#### **4.2. Para Traduções Incorretas**
- Corrigir a tradução mantendo o significado original
- Verificar consistência de terminologia entre arquivos

#### **4.3. Para Hardcoded Strings**
- Substituir strings hardcoded por chamadas `__()`
- Adicionar as novas chaves nos arquivos de idioma

**Exemplo de correção:**
```python
# ANTES (hardcoded)
print("⚠️ Warning: Script version mismatch detected")

# DEPOIS (com i18n)
print(__("version_mismatch_warning", "⚠️ Warning: Script version mismatch detected"))
```

---

### **5. Documentação do Processo**

Criar um relatório da auditoria contendo:
1. **Sumário executivo** - Status geral da i18n
2. **Chaves encontradas** - Lista completa de todas as chaves
3. **Chaves faltantes** - Por idioma e por arquivo
4. **Traduções incorretas** - Lista de correções necessárias
5. **Hardcoded strings** - Strings que precisam ser migradas
6. **Recomendações** - Melhorias e boas práticas

**Estrutura do relatório:**
```markdown
# Relatório de Auditoria i18n
Data: 2026-08-05
Arquivos auditados: src/core.py, src/updater.py

## Resumo
- Total de chaves únicas: 42
- Arquivos de idioma: 5
- Status: ⚠️ 3 chaves faltando em pt_pt

## Detalhes por Idioma

## Inglês (en) - ✅ 100% completo
## Português Brasil (pt_br) - ✅ 100% completo
## Português Portugal (pt_pt) - ❌ 3 chaves faltando
  - "scripts_version_header"
  - "install_scripts_confirm"
  - "docs_url_label"

## Francês (fr) - ✅ 100% completo
## Espanhol (es) - ⚠️ 1 tradução incorreta
  - "hooks_updated": Corrigir para "Ganchos actualizados correctamente"

## Hardcoded Strings Encontradas
- Line 245: "Error: Failed to update hooks"
- Line 378: "Success: All scripts synchronized"
```

---

### **6. Ferramentas de Verificação**

**Script de validação sugerido:**
```python
# scripts/validate_i18n.py

import json
import os
import re
from pathlib import Path

def extract_i18n_keys(filepath):
    """Extrai todas as chaves de __() do arquivo"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Padrão para encontrar __("key", "default")
    pattern = r'__\(["\']([^"\']+)["\']\s*,\s*["\']([^"\']+)["\']\)'
    matches = re.findall(pattern, content)
    
    keys = {}
    for key, default in matches:
        keys[key] = default
    
    return keys

def validate_lang_files(keys_from_code, lang_dir='langs'):
    """Valida todos os arquivos de idioma"""
    lang_files = Path(lang_dir).glob('*.json')
    results = {}
    
    for lang_file in lang_files:
        lang = lang_file.stem
        with open(lang_file, 'r', encoding='utf-8') as f:
            translations = json.load(f)
        
        missing = set(keys_from_code.keys()) - set(translations.keys())
        extra = set(translations.keys()) - set(keys_from_code.keys())
        placeholder_errors = []
        
        # Validar placeholders
        for key, value in translations.items():
            if key in keys_from_code:
                code_placeholders = re.findall(r'\{(\w+)\}', keys_from_code[key])
                trans_placeholders = re.findall(r'\{(\w+)\}', value)
                if set(code_placeholders) != set(trans_placeholders):
                    placeholder_errors.append(key)
        
        results[lang] = {
            'missing': missing,
            'extra': extra,
            'placeholder_errors': placeholder_errors,
            'complete': len(missing) == 0 and len(placeholder_errors) == 0
        }
    
    return results

if __name__ == '__main__':
    code_keys = extract_i18n_keys('src/core.py')
    code_keys.update(extract_i18n_keys('src/updater.py'))
    
    results = validate_lang_files(code_keys)
    
    for lang, result in results.items():
        status = '✅' if result['complete'] else '❌'
        print(f"{status} {lang}:")
        if result['missing']:
            print(f"  Missing: {result['missing']}")
        if result['placeholder_errors']:
            print(f"  Placeholder errors: {result['placeholder_errors']}")
```

---

### **7. Critérios de Aceite**

- [ ] **Todas as strings** em `src/core.py` e `src/updater.py` usam `__()` (sem hardcoded)
- [ ] **Todas as chaves** estão definidas em todos os 5 arquivos de idioma
- [ ] **Todas as traduções** estão completas e corretas
- [ ] **Placeholders** são preservados em todas as traduções
- [ ] **Arquivos JSON** estão formatados corretamente e válidos
- [ ] **Relatório de auditoria** gerado com todas as informações
- [ ] **Script de validação** criado e documentado
- [ ] **Nenhuma chave extra** em arquivos de idioma (limpeza)

---

### **8. Exemplo de Saída Esperada**

**Ao executar o script de validação:**
```bash
$ python scripts/validate_i18n.py

🔍 Analisando src/core.py... 28 chaves encontradas
🔍 Analisando src/updater.py... 14 chaves encontradas
📊 Total de chaves únicas: 42

✅ Validando arquivos de idioma...
   ✅ en.json: 42/42 chaves - COMPLETO
   ✅ pt_br.json: 42/42 chaves - COMPLETO
   ❌ pt_pt.json: 39/42 chaves - 3 FALTANDO
   ✅ fr.json: 42/42 chaves - COMPLETO  
   ⚠️ es.json: 42/42 chaves - 1 ERRO DE PLACEHOLDER

📋 Relatório de auditoria gerado: docs/i18n-audit-report.md

❌ Ações necessárias:
   1. Adicionar 3 chaves em langs/pt_pt.json
   2. Corrigir placeholder em langs/es.json (key: "hooks_updated")
```

---

## **Notas Técnicas**
- Os arquivos JSON devem ser **UTF-8** e com **codificação correta**
- Use `json.dumps(translations, indent=2, ensure_ascii=False)` para manter caracteres especiais
- Considere adicionar validação automática no pipeline de CI/CD
- Documente o processo de adição de novas chaves no `CONTRIBUTING.md`
- Mantenha o arquivo `en.json` como base/referência para todas as traduções

---

## **Arquivos a Serem Modificados/Criados**
```
src/core.py                   # Verificar e corrigir strings
src/updater.py                # Verificar e corrigir strings
langs/en.json                 # Base/Referência
langs/pt_br.json              # Verificar traduções
langs/pt_pt.json              # Verificar traduções
langs/fr.json                 # Verificar traduções
langs/es.json                 # Verificar traduções
scripts/validate_i18n.py      # Script de validação (novo)
docs/i18n-audit-report.md     # Relatório da auditoria (novo)
CONTRIBUTING.md               # Atualizar com processo i18n
```

---

## **Links Úteis**
- [Documentação i18n](@docs/i18n_explanation.md)
- [Relatório de Implementação](@docs/claude-code/reports/develop_natan/2026-08-05_hooks-versioning-i18n-sync.md)
- [Guia de Tradução](@docs/translation-guide.md)