# Walkthrough — Documentação da Mudança de Semântica de GITPR_SKIP_UPDATE_CHECK

**Data:** 2026-11-09  
**Branch:** develop_natan  
**Task:** document_gitpr_skip_update_check_migration_note  

---

## 1. O que foi feito

Documentamos formalmente a mudança semântica do `GITPR_SKIP_UPDATE_CHECK` (introduzida na versão 1.4.3 com o parser booleano estrito) como uma nota de migração nos documentos de referência técnica (`docs/auto-update.*.md`) e nos tutoriais de instalação a partir do código-fonte (`docs/tutorial/install-from-source.*.md`), em todas as 5 línguas suportadas pelo GitPR (EN, PT-BR, PT-PT, ES-ES, FR-FR). Além disso, o vocabulário ubíquo foi atualizado em `CONTEXT.md` com a definição canônica de **Update check switch**.

---

## 2. Arquivos Modificados

| Arquivo | Mudança | Escopo / Idioma |
|---|---|---|
| `CONTEXT.md` | Formalização do termo ubíquo `Update check switch` | Modelo de Domínio |
| `docs/auto-update.md` | Subseção e nota de migração `[!WARNING]` | Técnico / EN |
| `docs/auto-update.pt_br.md` | Subseção e nota de migração `[!WARNING]` | Técnico / PT-BR |
| `docs/auto-update.pt_pt.md` | Subseção e nota de migração `[!WARNING]` | Técnico / PT-PT |
| `docs/auto-update.es_es.md` | Subseção e nota de migração `[!WARNING]` | Técnico / ES-ES |
| `docs/auto-update.fr_fr.md` | Subseção e nota de migração `[!WARNING]` | Técnico / FR-FR |
| `docs/tutorial/install-from-source.md` | Callout de nota de migração `[!WARNING]` na Seção 5 | Tutorial / EN |
| `docs/tutorial/install-from-source.pt_br.md` | Callout de nota de migração `[!WARNING]` na Seção 5 | Tutorial / PT-BR |
| `docs/tutorial/install-from-source.pt_pt.md` | Callout de nota de migração `[!WARNING]` na Seção 5 | Tutorial / PT-PT |
| `docs/tutorial/install-from-source.es_es.md` | Callout de nota de migração `[!WARNING]` na Seção 5 | Tutorial / ES-ES |
| `docs/tutorial/install-from-source.fr_fr.md` | Callout de nota de migração `[!WARNING]` na Seção 5 | Tutorial / FR-FR |

---

## 3. Validação dos Resultados

- **Clareza da Armadilha de Migração**: A nota explica detalhadamente que antes da 1.4.3 qualquer string não-vazia (incluindo `=false`, `=0`, `=off`) silenciava a checagem por simples teste de presença de variável. A partir da 1.4.3, o parser booleano estrito só aceita valores truthy (`1`, `true`, `yes`, `on`, `y`), de modo que `=false` faz a checagem rodar e potencialmente bloquear comandos em ambientes com versão defasada.
- **Paridade Multilíngue**: Todos os 5 idiomas mantêm exata coerência semântica e estrutural.
- **Integridade do Glossário**: O termo `Update check switch` foi integrado a `CONTEXT.md` respeitando a estrutura do arquivo e as regras de termos a evitar.
