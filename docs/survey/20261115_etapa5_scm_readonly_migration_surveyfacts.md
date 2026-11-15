# Survey Facts — Etapa 5: Documentação da Migração SCM em `.env` Somente Leitura / Efêmero (`persisted=False`)

- **Data:** 2026-11-15
- **Branch:** `develop_natan`
- **Referência:** `docs/prompts/relatorio_pendencias_proximos_passos_i18n.md` (Etapa 5, L149–L167)

---

## 1. Contexto da Tarefa

Documentar o comportamento resiliente da rotina de migração automática `migrate_legacy_scm_config()` (`src/scm_settings.py`) quando o arquivo `~/.gitpr/.env` está montado como somente leitura (`:ro`), protegido por permissões ou em um container/runner CI/CD efêmero, garantindo que os 5 idiomas de `docs/scm-multiforge.*`, a `ADR-0020` e os testes de paridade reflitam o contrato real do código.

---

## 2. Decisões da Entrevista (`/grill-with-docs`)

| Questão | Decisão Confirmada | Justificativa |
| --- | --- | --- |
| **Q1** — Estrutura em `docs/scm-multiforge.*` (`### 3.1`) | Adicionar um bloco `> [!NOTE]` separado logo abaixo do `> [!WARNING]` existente em `### 3.1`. | Mantém o alerta de provisionamento enxuto, destaca visualmente o comportamento de runtime (`persisted=False`) e preserva paridade estrutural nos 5 idiomas. |
| **Q2** — Nível de detalhe técnico (`docs/scm-multiforge.*` vs. `ADR-0020`) | Explicitar `persisted=False` e o fallback em `os.environ` tanto em `### 3.1` de `docs/scm-multiforge.*` quanto na `ADR-0020` (com `(OSError, PermissionError)` e `MigrationResult` detalhados na ADR). | Alinha a documentação diretamente aos critérios de aceite da Etapa 5 e permite validação automatizada independente de idioma. |
| **Q3** — Expansão de `tests/unit/test_scm_multiforge_docs_parity.py` | Expandir `test_scm_multiforge_files_exist_and_have_migration_note_section()` e `test_adr_0020_exists_and_references_docs_and_adr_016()` para exigir `persisted=False` e `os.environ`. | Garante que nenhuma das 5 traduções nem a ADR-0020 percam a nota de fallback read-only em edições futuras. |
| **Q4** — Glossário (`CONTEXT.md`) | Não adicionar novo termo ao `CONTEXT.md`. | Trata-se de comportamento de resiliência/implementação de `migrate_legacy_scm_config()`, mantendo o glossário livre de detalhes de implementação. |

---

## 3. Fatos Levantados no Código e Documentação

1. **`src/scm_settings.py` (linhas 217–342):**
   - `migrate_legacy_scm_config()` executa `_migrate_legacy_scm_config()` sob `_MIGRATION_LOCK` (uma vez por processo, com cache em `_MIGRATION_STATE`).
   - Quando `config_module.save_config_values(to_persist)` ou `_remove_legacy_lines(file_values)` levanta `(OSError, PermissionError)`:
     - Captura a exceção sem abortar a execução;
     - Define `persisted = False` e preenche `warning` via `__("The legacy SCM configuration could not be migrated in {path}: {error}", ...)` (ou `"could not be removed from {path}: {error}"` quando restam apenas linhas vazias/legadas sem provider/token);
     - Materializa `writes` em `os.environ[key] = value` e remove `GITPR_SCM_PROVIDER`, `GITPR_SCM_TOKEN_ENCRYPTED` e `GITPR_SCM_BASE_URL` de `os.environ` via `os.environ.pop(key, None)`.
     - Retorna `MigrationResult(ran=True, migrated=bool(writes), provider=legacy_provider, persisted=False, warning=warning)`.
   - Como o `.env` permanece inalterado no disco, a migração tenta novamente na próxima execução e reemite o aviso a cada comando.
2. **`docs/scm-multiforge.*` (linhas 111–125 nos 5 arquivos):**
   - Todos os 5 idiomas (`.md`, `.pt_br.md`, `.pt_pt.md`, `.es_es.md`, `.fr_fr.md`) possuem `### 3.1` idêntico em estrutura: um bloco `> [!WARNING]` seguido de `---` antes de `## 4`.
   - `tests/unit/test_docs_translation_parity.py` exige contagem idêntica de headings (`^(#{1,6})\s`), linhas `|`, bullets (`^\s*[-*]\s`) e fences (` ``` `) entre os 5 arquivos.
3. **`docs/adr/0020-per-repo-scm-provisioning-migration.md` (linhas 64–72):**
   - A seção `## 3. Consequências` lista consequências positivas e negativas, mas ainda não registra o comportamento resiliente em `.env` somente leitura (`(OSError, PermissionError)`, `persisted=False`, materialização em `os.environ` e aviso recorrente).
4. **`tests/unit/test_scm_multiforge_docs_parity.py`:**
   - Valida a presença de `### 3.1 `, chaves legadas, slots por forge e link para `ADR-0020` nos 5 arquivos, além das referências em `ADR-0020` e termos em `CONTEXT.md`.
