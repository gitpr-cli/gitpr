## [1.7.0] - 2026-11-10

### Summary
This release improves the dashboard with ASCII charts and tabbed navigation, making status information easier to scan. It adds support for binary extensions and more resilient handling of change groups, while separating extension release publishing from broader release steps and introducing a more granular marketplace gate. Project configuration gains a new floating-point option and token pricing fields, along with documentation for configuration seed segregation, language fallback, audit closures, and migration guidance. Documentation and release guidance were also updated to clarify unified checks, interactive breaking changes, and language declarations.

### ✨ Features
- add ASCII charts and tabbed navigation to dashboard ([07822f7](https://github.com/gitpr-cli/gitpr/commit/07822f7c2bc88dce9d069ae6cc997f1f44f3d5a4)) · 2026-11-10
- add binary extensions and defensive hunk collapse ([c1cddbb](https://github.com/gitpr-cli/gitpr/commit/c1cddbb15fbe60ad63053b21021ce4b899b4149c)) · 2026-11-09
- decouple extension VSIX GitHub release and implement granular marketplace gate ([3bcc6c9](https://github.com/gitpr-cli/gitpr/commit/3bcc6c97736900f67cd3882f8660d76ebbc7839f)) · 2026-11-09
- add float config kind and token pricing fields ([c5485dd](https://github.com/gitpr-cli/gitpr/commit/c5485dd07ee0ce387b596727a534b1ab1d60e4dc)) · 2026-11-08
- add language declaration to release skill front matter ([b277632](https://github.com/gitpr-cli/gitpr/commit/b277632c4dde7eed0bb184d729d927f56894a750)) · [#292](https://github.com/gitpr-cli/gitpr/pull/292) · 2026-11-07

### 📚 Docs
- formalize project configuration seed segregation in ADR 0019 ([98b23cc](https://github.com/gitpr-cli/gitpr/commit/98b23cc3ed97b2e6283bdf7be1f64806527754ee)) · 2026-11-10
- formalize documentation site language fallback contract in ADR 0017 ([80378b0](https://github.com/gitpr-cli/gitpr/commit/80378b05835ad62caeb16ac0cf7d5ec8352a6819)) · 2026-11-10
- document unified check migration in action.yml ([7bd6678](https://github.com/gitpr-cli/gitpr/commit/7bd6678cd7b8de1d99480277f36b6d7fcf8ebe5e)) · 2026-11-09
- document audit and formal closure of config tui debts ([8886976](https://github.com/gitpr-cli/gitpr/commit/8886976cef6799a6c466b9c0ec90d2a6b274c31c)) · 2026-11-09
- document audit and formal closure of smart excludes config tui item ([a7c316a](https://github.com/gitpr-cli/gitpr/commit/a7c316a4b7912f91727f49df35bf38f89ed54511)) · 2026-11-09
- document interactive commit breaking change migration note ([1995213](https://github.com/gitpr-cli/gitpr/commit/1995213d1e0fc27752c09d49d7c9806ec8a7bc4d)) · 2026-11-09
- document project config seed migration and CI/monorepo opt-out ([7cf4ac8](https://github.com/gitpr-cli/gitpr/commit/7cf4ac830cc9860b343412fd2a90e277cac0ea01)) · 2026-11-09
- add project status report v0.0.23 ([00d5644](https://github.com/gitpr-cli/gitpr/commit/00d564416f40d4635e5bd9622a06e4845f5310a8)) · [#293](https://github.com/gitpr-cli/gitpr/pull/293) · 2026-11-08

**Contributors:** [@natanfiuza](https://github.com/natanfiuza)
