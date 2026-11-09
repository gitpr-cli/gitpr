# Walkthrough — Nota de Migração e Governança do `action.yml`

Fechamento do item herdado de documentação e governança arquitetural referente à quebra de contrato da composite action (`action.yml`) com a adoção do comando unificado `gitpr check`.

## Alterações Realizadas

### 1. ADR Canônico: [`docs/adr/0011-action-unified-check-migration.md`](../../../adr/0011-action-unified-check-migration.md)
Criado o Architectural Decision Record 0011 formalizando:
- Contexto da substituição de `--linter` + `--fullreview` por `gitpr check`.
- Motivação para a descontinuação do arquivo de texto puro `*_PR_FULLREVIEW.txt` em disco e a migração para SARIF 2.1.0 (Code Scanning) e JSON/JUnit.
- Justificativas das opções rejeitadas e detalhamento das consequências para pipelines legados.

### 2. Cabeçalho de Orientação no [`action.yml`](../../../../action.yml)
Inserido bloco de cabeçalho orientando qualquer usuário que leia o arquivo:
```yaml
# ==============================================================================
# GitPR Unified CI Check Composite Action
#
# NOTE (Migration Guide):
# Since modern versions of GitPR, this action runs the unified 'gitpr check'
# pipeline, generating SARIF 2.1.0, JSON, or JUnit XML artifacts instead of
# legacy text files (*_PR_FULLREVIEW.txt).
# For migration steps and before/after workflow comparisons, see:
# https://gitpr.natanfiuza.dev.br/docs/check-ci#7-migration-guide
# ==============================================================================
```

### 3. Alerta de Breaking Change no [`CHANGELOG.md`](../../../../CHANGELOG.md)
Registrado sob a versão `[1.6.0]` a seção destacada:
```markdown
### ⚠️ Breaking Changes
- **Composite Action (`action.yml`)**: Modern versions run the unified `gitpr check` pipeline producing SARIF 2.1.0/JSON/JUnit artifacts instead of legacy `*_PR_FULLREVIEW.txt` text files. See the migration guide in [`docs/check-ci.md`](docs/check-ci.md#7-migration-guide) and [ADR-0011](docs/adr/0011-action-unified-check-migration.md).
```

### 4. Testes de Paridade e Guarda Contratual: [`tests/unit/test_check_ci_docs_parity.py`](../../../../tests/unit/test_check_ci_docs_parity.py)
Adicionado o teste `test_action_yml_and_adr_0011_reference_migration_guide` garantindo que:
- O ADR-0011 exista e contenha as referências a `action.yml`, `gitpr check`, `--linter`, `--fullreview`, `SARIF` e `docs/check-ci.md`.
- O `action.yml` referencie `gitpr check` e `docs/check-ci`.

---

## Verificação e Resultados

### Execução dos Testes Automatizados
```bash
python -m pytest tests/unit/test_check_ci_docs_parity.py -v
```
Resultado:
- `test_check_ci_files_exist_and_have_all_sections PASSED`
- `test_context_md_defines_legacy_ci_action_contract PASSED`
- `test_action_yml_and_adr_0011_reference_migration_guide PASSED`

```bash
python -m pytest tests/unit/test_version_consistency.py -v
```
Resultado:
- Todos os 5 testes de consistência de versão e SSOT passaram com sucesso.
