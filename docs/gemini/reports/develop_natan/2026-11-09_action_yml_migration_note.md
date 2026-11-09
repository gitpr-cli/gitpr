## Completion Report — Governança e Nota de Migração do `action.yml`

### What was done
- Formalized the breaking change contract of the composite GitHub Action (`action.yml`) migrating from sequential `--linter` + `--fullreview` to unified `gitpr check` with SARIF 2.1.0 output.
- Authored canonical Architectural Decision Record [`docs/adr/0011-action-unified-check-migration.md`](../../../adr/0011-action-unified-check-migration.md) documenting context, decisions, rejected options, and migration strategy referencing Section 7 of `docs/check-ci.md`.
- Added migration warning header and direct documentation link to [action.yml](../../../../action.yml).
- Added explicit `⚠️ Breaking Changes` notice in [CHANGELOG.md](../../../../CHANGELOG.md) directing CI pipeline maintainers to the migration guide.
- Extended automated regression tests in [tests/unit/test_check_ci_docs_parity.py](../../../../tests/unit/test_check_ci_docs_parity.py) to assert existence and cross-references between `action.yml`, `docs/adr/0011-action-unified-check-migration.md`, and `docs/check-ci.md`.
- Generated survey facts ([`docs/survey/20261109_action_yml_migration_note_surveyfacts.md`](../../../survey/20261109_action_yml_migration_note_surveyfacts.md)) and plans facts ([`docs/plans/develop_natan/20261109_action_yml_migration_note_plansfacts.md`](../../../plans/develop_natan/20261109_action_yml_migration_note_plansfacts.md)).

### Changed files
| File | Change type | Description |
|------|-------------|-------------|
| `docs/adr/0011-action-unified-check-migration.md` | feat | Canonical ADR formalizing the composite action breaking change |
| `action.yml` | feat | Added explanatory header comments and migration guide URL |
| `CHANGELOG.md` | feat | Added `⚠️ Breaking Changes` notice for composite action migration |
| `tests/unit/test_check_ci_docs_parity.py` | test | Added automated test verifying `action.yml` and ADR-0011 migration references |
| `docs/survey/20261109_action_yml_migration_note_surveyfacts.md` | docs | Survey facts from the grilling session |
| `docs/plans/develop_natan/20261109_action_yml_migration_note_plansfacts.md` | docs | Execution plan facts for the session |
| `docs/gemini/plans/develop_natan/2026-11-09_develop_natan_action_yml_migration_note.md` | docs | Implementation plan artifact |

### Impact
- **Functionality:** CI maintainers upgrading workflows now have canonical architecture records (ADR-0011), in-code guidance directly in `action.yml`, and clear release notes in `CHANGELOG.md` complementing the existing 5-language migration guide in `docs/check-ci.*.md`.
- **Performance:** Zero runtime overhead; changes are purely documentation, configuration metadata, and tests.
- **Compatibility:** Eliminates ambiguity for workflows upgrading from `v0.0.36` to modern GitPR versions.

### Next steps (if applicable)
- The inherited debt regarding the `action.yml` migration note is completely closed, tested, and governed across all documentation surfaces.
