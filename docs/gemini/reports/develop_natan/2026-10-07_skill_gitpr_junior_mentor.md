## Completion Report — GitPR Junior Mentor Mode

### What was done
- Implemented GitPR "Junior Mentor" mode, a pedagogical coaching feedback layer for code reviews designed to nurture developer growth instead of merely highlighting defects.
- Created domain entity and pure markdown builder in `src/domain/mentor/mentor_explanation_builder.py` (`MentorExplanation`, `build_mentor_markdown`, `build_mentor_section`, `parse_mentor_payload`) supporting epistemic honesty (`has_sufficient_evidence`), structured educational sections (why it matters, conceptual analogy, guided questions, and key takeaways), and clean learn-more topics without external links.
- Created application use case in `src/application/use_cases/generate_mentor_explanation.py` (`generate_mentor_explanations_for_review`, `generate_mentor_explanation`, `explain_review`, `MentorRun`, `MentorError`) supporting review cache integration, candidate finding extraction via `collect_candidates`, batch AI querying (max 10 findings per run), and fallback handling.
- Added configuration keys `GITPR_REVIEW_MENTOR_MODE` and `GITPR_MENTOR_INCLUDE_ANALOGY` to `src/config.py` and `src/config_schema.py` in the `review` category.
- Integrated CLI options into `src/main.py`:
  - Added `--mentor` flag to append pedagogical explanations to code reviews (`gitpr -r --mentor` and `gitpr -f --mentor`).
  - Added standalone `gitpr mentor` command (`gitpr mentor [--finding <id>] [--provider <name>]`).
- Created localized skill templates in 5 languages (`templates/gitpr.mentor.md`, `templates/gitpr.mentor.pt_br.md`, `templates/gitpr.mentor.pt_pt.md`, `templates/gitpr.mentor.es_es.md`, `templates/gitpr.mentor.fr_fr.md`).
- Resolved skill registry synchronization across `src/mcp_server.py`, `src/core.py`, `src/config.py`, and `src/config_schema.py` for `tests`, `explain`, and `mentor`.
- Added complete documentation in 5 languages (`docs/mentor-mode.md`, `docs/mentor-mode.pt_br.md`, `docs/mentor-mode.pt_pt.md`, `docs/mentor-mode.es_es.md`, `docs/mentor-mode.fr_fr.md`), architectural documentation (`docs/plans/ADR-009-mentor-domain-package.md`, `docs/plans/glossary-gitpr-mentor.md`), and updated `README.md`.
- Updated all internationalization files (`langs/pt_br.json`, `langs/pt_pt.json`, `langs/es_es.json`, `langs/es.json`, `langs/fr_fr.json`, `langs/fr.json`), bumped `__lang_version__` to `v0.0.33` in `src/updater.py`, and verified 100% i18n parity and zero orphan keys.
- Implemented comprehensive automated test suite across domain, application, CLI, schema, and i18n layers (103 passing tests).

### Changed files
| File | Change type | Description |
|------|-------------|-------------|
| `docs/plans/glossary-gitpr-mentor.md` | docs | Ubiquitous language glossary for Junior Mentor Mode |
| `docs/plans/ADR-009-mentor-domain-package.md` | docs | Architecture Decision Record for domain-driven mentor module |
| `src/domain/mentor/__init__.py` | feat | Package marker exporting mentor domain entities and builders |
| `src/domain/mentor/mentor_explanation_builder.py` | feat | Pure domain builder and parser for pedagogical mentor explanations |
| `src/application/use_cases/generate_mentor_explanation.py` | feat | Application use case orchestrating review cache, candidate collection, and AI execution |
| `src/config.py` | feat | Added mentor settings, getters, and registered skill template mapping |
| `src/config_schema.py` | feat | Registered mentor configuration fields in review category and updated skill labels |
| `src/core.py` | feat | Registered mentor, tests, and explain skills in template generation and downloads |
| `src/mcp_server.py` | fix/feat | Synchronized SKILL_FILES list including tests, explain, and mentor |
| `src/main.py` | feat | Added `--mentor` flag to reviews, integrated `mentor` command, and registered CLI help |
| `src/updater.py` | feat | Bumped `__lang_version__` to `v0.0.33` for OTA language updates |
| `templates/gitpr.mentor.md` | feat | English AI system instructions template for Junior Mentor Mode |
| `templates/gitpr.mentor.pt_br.md` | feat | Brazilian Portuguese AI system instructions template |
| `templates/gitpr.mentor.pt_pt.md` | feat | European Portuguese AI system instructions template |
| `templates/gitpr.mentor.es_es.md` | feat | Spanish AI system instructions template |
| `templates/gitpr.mentor.fr_fr.md` | feat | French AI system instructions template |
| `langs/pt_br.json` | feat | Brazilian Portuguese translation strings for mentor mode |
| `langs/pt_pt.json` | feat | European Portuguese translation strings for mentor mode |
| `langs/es_es.json` | feat | Spanish (Spain) translation strings for mentor mode |
| `langs/es.json` | feat | Spanish translation strings for mentor mode |
| `langs/fr_fr.json` | feat | French (France) translation strings for mentor mode |
| `langs/fr.json` | feat | French translation strings for mentor mode |
| `docs/mentor-mode.md` | docs | English guide for Junior Mentor Mode |
| `docs/mentor-mode.pt_br.md` | docs | Brazilian Portuguese guide for Junior Mentor Mode |
| `docs/mentor-mode.pt_pt.md` | docs | European Portuguese guide for Junior Mentor Mode |
| `docs/mentor-mode.es_es.md` | docs | Spanish guide for Junior Mentor Mode |
| `docs/mentor-mode.fr_fr.md` | docs | French guide for Junior Mentor Mode |
| `README.md` | docs | Added CLI commands, review flags, and skill templates description |
| `tests/domain/mentor/test_mentor_explanation_builder.py` | test | Unit tests for domain entity, builders, and payload parser |
| `tests/application/use_cases/test_generate_mentor_explanation.py` | test | Unit tests for use case orchestration and candidate handling |
| `tests/test_mentor_cli.py` | test | CLI invocation tests for standalone command and review flags |

### Impact
- **Functionality:** Users can now run `gitpr -r --mentor` or `gitpr -f --mentor` to receive educational mentoring explanations alongside their code review, or run `gitpr mentor` (with optional `--finding <id>`) to explain specific findings on demand.
- **Performance:** Findings are batched in a single AI call capped at 10 items per run, sorted by severity, with prompt token minimization. MD5 caching prevents redundant API calls.
- **Compatibility:** Strictly additive and opt-in (`GITPR_REVIEW_MENTOR_MODE=false` by default). Does not break any existing review, PR, fix, test generation, or MCP workflows.

### Next steps (if applicable)
- Optional future enhancement: Expose a dedicated MCP tool `explain_review_finding` in `src/mcp_server.py` for IDE agents to query mentor explanations directly.

