# Add Junior Mentor Mode with pedagogical AI guidance for code review findings

## Add Junior Mentor Mode with pedagogical AI guidance for code review findings

### What
- [x] **Feature:** Introduces a new **Junior Mentor Mode** that enriches code review findings with pedagogical explanations (what is happening, why it matters, analogies, and concepts to learn) tailored for junior engineers.
- [x] **Feature:** Adds the `--mentor` CLI flag to automatically append a didactic Mentor section to `-r/--review` and `-f/--fullreview` outputs.
- [x] **Feature:** Adds a standalone `gitpr mentor` command (with `--finding <id>` and `--provider <name>` options) to explain all or a single finding from the last review.
- [x] **Feature:** Adds two new configuration toggles (`GITPR_REVIEW_MENTOR_MODE`, `GITPR_MENTOR_INCLUDE_ANALOGY`) exposed through the config schema.
- [x] **Feature:** Adds a new `mentor` skill template (`.gitpr.mentor.md`) wired into skill generation and the MCP server.
- [x] **Fix:** Corrects a typo in the Spanish locale (`quando` → `cuando`) for the Semgrep description string.
- [x] **Docs/Chore:** Bumps the language dictionary version to `v0.0.33`.

### Why
The tool already produces technical code review findings, but those findings often lack the pedagogical context that junior developers need to actually learn from a review. The Mentor Mode closes this gap by transforming cold review output into didactic, empathetic, and actionable feedback (with optional everyday analogies), while enforcing **epistemic honesty** — when the AI cannot infer why something matters from the diff alone, it explicitly says so instead of fabricating an explanation. This improves onboarding, learning outcomes, and review usefulness without changing the existing review pipeline.

### Where
**File:** `src/application/use_cases/generate_mentor_explanation.py` (new), `src/domain/mentor/mentor_explanation_builder.py` (new), `src/domain/mentor/__init__.py` (new), `src/config.py`, `src/config_schema.py`, `src/core.py`, `src/main.py`, `src/mcp_server.py`, `src/updater.py`, `langs/{es,es_es,fr,fr_fr,pt_br,pt_pt}.json`, `tests/application/use_cases/test_generate_mentor_explanation.py` (new), `tests/domain/mentor/test_mentor_explanation_builder.py` (new), `tests/test_mentor_cli.py` (new)
**Module, option, implementation, feature:** `mentor` skill / `--mentor` flag / `gitpr mentor` command / `GITPR_REVIEW_MENTOR_MODE` / `GITPR_MENTOR_INCLUDE_ANALOGY`

### How
1. **Backend / Engine:**
   - **New orchestration use case (`generate_mentor_explanation.py`):** Connects findings collected via `src.fix.apply_fix.collect_candidates` to the AI mentor skill prompt. It sorts candidates by severity (`_SEVERITY_ORDER`), caps runs at `MAX_FINDINGS_PER_RUN = 10`, truncates per-finding context at `MAX_CONTEXT_CHARS_PER_FINDING = 4000`, uses MD5-based local caching (`get_cached_response` / `save_cached_response`), and structures the AI response into a `MentorRun` (explanation tuple, `skipped_ids`, and rendered markdown). Exposes `generate_mentor_explanations_for_review`, `generate_mentor_explanation`, and `explain_review`.
   - **New pure domain package (`src/domain/mentor/`):** `mentor_explanation_builder.py` contains no I/O or network calls. It defines the frozen `MentorExplanation` dataclass, `parse_mentor_payload` (validates IDs against expected findings, discards duplicates/hallucinated IDs, forces `has_sufficient_evidence=false` when the diff is insufficient or placeholder markers are detected, and strips any URLs from `learn_more_pointer` via `_URL_RE`), and markdown builders `build_mentor_markdown` / `build_mentor_section`.
   - **CLI wiring (`src/main.py`):** Adds `--mentor` flag to the review command, a `_append_mentor_section` helper that synthesizes a review record and appends the generated markdown section, and a full `mentor` command with `--finding` and `--provider` options plus a `JUNIOR MENTOR GUIDANCE` banner. A warning is emitted if `--mentor` is used with unsupported actions.
   - **Skill wiring:** Registers `.gitpr.mentor.md` in `SKILL_FILES_BY_TYPE` (`src/config.py`), the template mapping in `generate_skill_template` (`src/core.py`), and `SKILL_FILES` (`src/mcp_server.py`).

2. **Database / Data:**
   - No database changes. Configuration environment variables added: `GITPR_REVIEW_MENTOR_MODE` (default `false`, enables the mentor section automatically) and `GITPR_MENTOR_INCLUDE_ANALOGY` (default `true`, controls analogy generation).
   - New `ConfigField` entries added to `src/config_schema.py` under the `review` category, plus new skill labels (`tests`, `explain`, `mentor`).
   - New helper functions `mentor_mode_enabled()` and `mentor_include_analogy()` in `src/config.py`.
   - Language dictionary bumped to `v0.0.33` in `src/updater.py`.

3. **Frontend / CLI / Interface:**
   - New localized strings added across all supported locales (en source keys in the docs, plus `es`, `es_es`, `fr`, `fr_fr`, `pt_br`, `pt_pt`) covering the flag help, command help, progress/status messages, section headers (`What is happening:`, `Why it matters:`, `Analogy:`, `To learn more:`), error messages, and the base system instruction for the mentor persona.
   - Users can now invoke `gitpr -r --mentor`, `gitpr -f --mentor`, or `gitpr mentor [--finding FIX-002] [--provider gemini]`.
   - New test coverage: unit tests for the use case (success, missing API key, caching, severity sorting/cap, single-candidate convenience), unit tests for the pure builder (parsing, null analogy, analogy flag disable, strict ID linking/ordering, URL stripping, epistemic-honesty fallback, malformed payloads, section formatting), and CLI integration tests (mentor opt-in, flag invocation, standalone command with and without `--finding`).

---
## Impact Warnings
- **Critical item (API key required):** Mentor Mode depends on a configured AI provider API key. Runs without a key raise a `MentorError` (`❌ No API key configured for {provider}`), so the review pipeline must degrade gracefully — the current implementation catches the error and returns the original content unchanged.
- **Critical item (provider trust):** AI-generated mentor explanations are untrusted input. The parser enforces strict safeguards (ID whitelisting, URL stripping, placeholder detection, epistemic-honesty fallback), and any change to `parse_mentor_payload` risks reintroducing hallucinated findings or fabricated links.
- **Behavioral change:** The `GITPR_REVIEW_MENTOR_MODE` toggle, when enabled, silently adds a mentor section to every `-r`/`-f` review. Teams enabling it should account for extra AI latency/token cost per review run.
- **Dependency:** Requires the `.gitpr.mentor.md` skill template to be installed (via `--install`) for the mentor persona prompt to resolve; otherwise a hardcoded fallback system instruction in the default locale is used.
- **Dependency:** There is a latent duplicate i18n key (`ℹ️ {count} additional finding(s) not expanded here...`) present twice in the locale files; downstream tooling that validates key uniqueness may flag it.
- **Dependency:** No newline at end of the modified JSON locale files (pre-existing condition) — any lint/format check enforcing trailing newlines will fail.