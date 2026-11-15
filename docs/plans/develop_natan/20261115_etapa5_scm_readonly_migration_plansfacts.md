# Plano de Execução — Etapa 5: Migração SCM em `.env` Somente Leitura / Efêmero (`persisted=False`)

- **Data:** 2026-11-15
- **Branch:** `develop_natan`
- **Escopo:** `docs/scm-multiforge.*` (5 idiomas), `docs/adr/0020-per-repo-scm-provisioning-migration.md`, `tests/unit/test_scm_multiforge_docs_parity.py`

---

## 1. Alterações Planejadas

1. **`docs/scm-multiforge.md` + 4 traduções (`.pt_br.md`, `.pt_pt.md`, `.es_es.md`, `.fr_fr.md`)**:
   - Inserir um callout `> [!NOTE]` imediatamente após o `> [!WARNING]` em `### 3.1` (antes do separador `---`).
   - Explicar que, quando `~/.gitpr/.env` é somente leitura (ex.: volumes `:ro` ou containers efêmeros), a migração retorna `persisted=False`, emite um aviso a cada comando e degrada com segurança para `os.environ` em memória (materializando os slots por forge e removendo as chaves legadas do ambiente do processo).
   - Recomendar a remoção das chaves legadas da imagem/script ou o uso de `GITPR_SCM_TOKEN` em ambientes efêmeros.
   - Garantir que o bloco `> [!NOTE]` tenha exatamente a mesma assinatura estrutural (0 headings, 0 table rows, 0 bullets, 0 fences) nos 5 idiomas.

2. **`docs/adr/0020-per-repo-scm-provisioning-migration.md`**:
   - Atualizar `## 3. Consequências` (e/ou adicionar nota de resiliência em runtime) registrando o comportamento de `migrate_legacy_scm_config()` diante de `(OSError, PermissionError)`: retorno de `MigrationResult(..., persisted=False, warning=...)`, materialização em `os.environ`, remoção das chaves legadas em memória e emissão de aviso a cada execução até que o `.env` ou script de provisionamento seja atualizado.

3. **`tests/unit/test_scm_multiforge_docs_parity.py`**:
   - Expandir `test_scm_multiforge_files_exist_and_have_migration_note_section()` para verificar `"persisted=False"` e `"os.environ"` nos 5 idiomas.
   - Expandir `test_adr_0020_exists_and_references_docs_and_adr_016()` para verificar `"persisted=False"`, `"os.environ"` e `"PermissionError"` na `ADR-0020`.

---

## 2. Verificação

```bash
python -m pytest tests/unit/test_scm_multiforge_docs_parity.py tests/unit/test_docs_translation_parity.py tests/scm/test_scm_settings.py -v
```
