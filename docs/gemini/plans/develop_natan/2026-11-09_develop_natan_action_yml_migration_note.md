# Plano de Implementação — Nota de Migração e Governança do `action.yml`

- **Branch:** `develop_natan`
- **Data:** `2026-11-09`
- **Arquivo:** `docs/gemini/plans/develop_natan/2026-11-09_develop_natan_action_yml_migration_note.md`

## 1. Visão Geral e Contexto
O comando `gitpr check` unificou a esteira de CI do GitPR em um único executor com saída SARIF 2.1.0, JSON ou JUnit XML, substituindo a abordagem anterior de executar em sequência `gitpr --linter` e `gitpr --fullreview`.
Essa transição no `action.yml` representou uma quebra de contrato para workflows de CI que dependiam da existência de arquivos de texto `*_PR_FULLREVIEW.txt` e de sua concatenação manual no `$GITHUB_STEP_SUMMARY`.

A documentação principal com a tabela "Antes vs Depois" e instruções de migração foi inserida nos 5 idiomas em `docs/check-ci.*.md` (Seção 7), guardada pelo teste `tests/unit/test_check_ci_docs_parity.py`.
Este plano fecha a governança arquitetural pendente através da criação do ADR 0011 em `docs/adr/`, anotação direta no `action.yml` e registro destacado no `CHANGELOG.md`.

## 2. Mudanças Propostas

### 2.1. Criação do ADR 0011 (`docs/adr/0011-action-unified-check-migration.md`)
- Registro formal de decisão de arquitetura documentando:
  - Contexto da composite action legada (`v0.0.12` – `v0.0.36`) vs moderna (`v0.0.37+` / `v1.0+`).
  - Decisões tomadas: adoção de `gitpr check`, abandono do `.txt` em disco em prol de SARIF/JUnit/JSON, código de saída determinístico baseado em `--fail-on` e chave de IA opcional (`no-ia: "true"`).
  - Consequências e orientações para workflows migrarem para `github/codeql-action/upload-sarif@v3`.

### 2.2. Inserção de Comentários Orientativos em `action.yml`
- Adicionar cabeçalho explicativo informando aos desenvolvedores que a action executa `gitpr check` e apontando diretamente para o guia de migração `docs/check-ci.md#7-migration-guide`.

### 2.3. Atualização do `CHANGELOG.md`
- Adicionar menção explícita sobre a quebra de contrato da composite action no `CHANGELOG.md`.

## 3. Plano de Verificação

### 3.1. Testes Automatizados
```bash
python -m pytest tests/unit/test_check_ci_docs_parity.py -v
python -m pytest tests/unit/test_version_consistency.py -v
```

### 3.2. Validação Manual
- Inspecionar a renderização e links do ADR 0011.
- Inspecionar a sintaxe YAML do `action.yml`.
