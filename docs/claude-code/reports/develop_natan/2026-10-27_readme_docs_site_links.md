## Completion Report — README documentation links moved to the official docs site

### What was done

- Rewrote **342** documentation destinations across the five root READMEs from
  `https://github.com/gitpr-cli/gitpr.git/blob/main/docs/*.md` to
  `https://gitpr.natanfiuza.dev.br/docs/*`, appending `?lang=<language>` on the
  four translated variants and nothing on `README.md`.
- Dropped the language suffix (`.pt_br`, `.pt_pt`, `.es_es`, `.fr_fr`) from the
  page name, since the language now travels in `?lang=` — the exact format the
  CLI already builds in `src/doc_links.py` (`doc_url()`).
- Rewrote the **50** visible labels whose text was a path
  (`[docs/xxx.md]` → `[gitpr.natanfiuza.dev.br/docs/xxx]`). The **288**
  descriptive labels (`Full docs`, `**AI Code Review**`, `MCP Prompts guide`)
  were left untouched, as decided in Q5/Q6.
- Converted **9 relative links** (`](docs/xxx.md)`) whose page exists on the
  site. The **5** `docs/tutorial/install-from-source.*` links stay relative
  because the site returns 404 for that page.
- Removed the redundant `?lang=en_us` from **4** pre-existing site links in
  `README.md` (`demo` ×2, `install-wizard` ×2) so English links carry no
  language parameter, as the rule requires.
- Left on GitHub, per Q1: the `📂 Repository:` link, the `git clone` command,
  the two `templates/*.json` links and the logo — the site serves 404 for
  `/logo.png` and `/templates/*.json`.
- Verification performed:
  - `blob/main/docs/` occurrences remaining: **0** in all five files.
  - `?lang=` values present per file: none in `README.md`; exactly the file's own
    language in each translated variant.
  - Only one relative doc link remains per file, the `tutorial/install-from-source`
    one, by design.
  - All **44** distinct documentation pages referenced return **200** on the
    site; `?lang=pt_br` and `?lang=pt_pt` serve the translations, while `es_es`
    and `fr_fr` currently fall back to English (also 200).
  - Full sweep of the **217** unique generated URLs: see *Verification* below.
  - CRLF endings and UTF-8 encoding preserved (612/610/607/607/608 CRLF pairs,
    no BOM); `git diff --stat` reports 345 insertions / 345 deletions, all of
    them documentation URLs.
- No source code was changed. No commit was made (`CLAUDE.md` rule).

### Changed files

| File | Change type | Description |
|------|-------------|-------------|
| `README.md` | docs | 70 destinations → site (English, no `?lang=`), 10 labels, plus 4 `?lang=en_us` removed |
| `README.pt_br.md` | docs | 69 destinations → site with `?lang=pt_br`, 10 labels |
| `README.pt_pt.md` | docs | 68 destinations → site with `?lang=pt_pt`, 10 labels |
| `README.es_es.md` | docs | 68 destinations → site with `?lang=es_es`, 10 labels |
| `README.fr_fr.md` | docs | 67 destinations → site with `?lang=fr_fr`, 10 labels |
| `docs/plans/develop_natan/20261027_readme_docs_site_links_plansfacts.md` | docs | Execution plan and Q1–Q10 decision record |
| `docs/survey/20261027_readme_docs_site_links_surveyfacts.md` | docs | Survey: inventory, site behaviour, CRLF incident, final rule |
| `docs/claude-code/reports/develop_natan/2026-10-27_readme_docs_site_links.md` | docs | This report |

### Verification

- Structural checks: **0** `blob/main/docs/` occurrences, **0** `?lang=en_us`,
  **1** intentional relative tutorial link and **2** `templates/*.json` links per
  file, `git clone` ×1 and logo ×1 per file.
- Site destinations in the final state: **367** = 342 converted + 25 that the
  READMEs already pointed at the site (75/74/73/73/72 per file).
- Full HTTP sweep of the **217** unique generated URLs: **checked=217,
  failures=0** — every one returns `200`.
- An earlier mass sweep returned `curl` code `000` for every URL and was
  initially read as host rate limiting. It was a harness defect: the URL list
  was written by Python's Windows stdout, which translates `\n` to `\r\n`, and
  `curl` treated each URL with a trailing `\r` as invalid. The site never
  rate-limited; with the list written using `newline='\n'` the same URLs answer
  `200`.

### Impact

- **Functionality:** Every documentation link in the five READMEs now opens the
  official docs site instead of a raw `.md` file on GitHub. The site renders the
  page and selects the language from `?lang=`, matching what the CLI prints via
  `src/doc_links.py`.
- **Performance:** None — Markdown only, no code path touched.
- **Compatibility:** The `docs/tutorial/install-from-source.*` links stay
  relative so they keep working inside the repository. Repository, `git clone`,
  `templates/*.json` and the logo remain on GitHub because the site does not
  serve them. `?lang=es_es` and `?lang=fr_fr` currently fall back to English;
  the links become correct automatically once those translations are published,
  with no further edit.

### Next steps

- Publish the `es_es` and `fr_fr` translations on the docs site — the links
  already carry the right parameter.
- Publish `/docs/tutorial/install-from-source` on the site; then the five
  remaining relative links can receive the same treatment.
- Review the working-tree diff and commit with:
  `docs: point README documentation links to the official docs site`
