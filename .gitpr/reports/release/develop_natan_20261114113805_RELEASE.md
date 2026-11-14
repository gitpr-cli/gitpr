## [1.8.0] - 2026-11-14

### Summary
Version 1.7.0 improves usability, documentation, and setup workflows. It adds a warning when a repository remote does not match a known forge, introduces per-provider token thresholds for map-reduce workflows, and adjusts the Windows headless flow to avoid the internet check. Documentation updates cover the dashboard charts tab, localized metrics charts for token trends and latency, marketplace publishing and credentials setup, update-check migration, and per-repository source-control provisioning guidance, with added translation and parity checks. The release also removes an outdated provider reference from an earlier report and refreshes the changelog and version information.

### ✨ Features
- warn when origin remote names no known forge ([c3da6ba](https://github.com/gitpr-cli/gitpr/commit/c3da6ba5e9a576c25e7838f17ea0651233f29b77)) · 2026-11-14
- add per-provider map-reduce token thresholds ([c7d95d7](https://github.com/gitpr-cli/gitpr/commit/c7d95d79a3f6822df47706cfabf676a7efdfb8ff)) · 2026-11-12
- add marketplace credentials setup wizard script ([a9544f3](https://github.com/gitpr-cli/gitpr/commit/a9544f3c19a2e971db251ca83790445f47cc5682)) · 2026-11-11

### 📚 Docs
- document dashboard charts tab and add translation parity guard ([0f2f0d4](https://github.com/gitpr-cli/gitpr/commit/0f2f0d40de0c9d8c4ae90b4c0e903740e54b06c0)) · 2026-11-14
- remove Anthropic Claude provider reference from v0.0.24 report ([faeecb8](https://github.com/gitpr-cli/gitpr/commit/faeecb82202615a57781bdcb2503a75717deaeb3)) · 2026-11-12
- sync token trend and latency charts in localized metrics docs ([0b3b899](https://github.com/gitpr-cli/gitpr/commit/0b3b89901dc7077a33a00636420dd941a66e4e9c)) · 2026-11-12
- translate marketplace publishing guide and add parity tests ([6b47f04](https://github.com/gitpr-cli/gitpr/commit/6b47f042fe72bcd494133bbcfced19e352e99f11)) · 2026-11-10
- document per-repo SCM provisioning migration note and ADR-0020 ([05df908](https://github.com/gitpr-cli/gitpr/commit/05df908970021113ed9179a5bfbaa2f1ff4939ae)) · 2026-11-10
- update changelog ([6d1f1dc](https://github.com/gitpr-cli/gitpr/commit/6d1f1dc89bbe7a17d84595beabdbb745531c3ae9)) · [#309](https://github.com/gitpr-cli/gitpr/pull/309) · 2026-11-10

### 🔧 Chores
- bump version to 1.7.0 and lang to v0.0.42 ([2354a30](https://github.com/gitpr-cli/gitpr/commit/2354a3085fa76e9195b469fda68816d557a639f5)) · 2026-11-10

### 📦 Other Changes
- skip headless flow on win32 and mock internet check ([3d80bb1](https://github.com/gitpr-cli/gitpr/commit/3d80bb1fc6656994705c05c7dc27854e3665fd3c)) · 2026-11-12
- add docs parity checks for update check migration ([77230b0](https://github.com/gitpr-cli/gitpr/commit/77230b04877b9c35c775a3aa69f7ac8cc7f42a39)) · 2026-11-11

**Contributors:** [@natanfiuza](https://github.com/natanfiuza)
