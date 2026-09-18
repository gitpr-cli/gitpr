## Completion Report — Tutorial: instalar do código-fonte e desbloquear o portão de versão

### What was done

Diagnosed why the mandatory update gate (`enforce_update_required()`) blocks an
editable install, and documented it in a new five-language tutorial under
`docs/tutorial/` — a directory that did not exist before.

**Root cause documented:** in an editable install, `src/updater.py` is read from
the **working tree**, not from a copy frozen at install time. The gate compares
that value against PyPI's latest, so any checkout reporting a version lower than
the published release is blocked on every command. The install is not broken —
it is the gate behaving as designed on a tree behind the release.

Three factual details were verified against the source before being written,
because the naive reading is wrong in each case:

1. `GITPR_SKIP_UPDATE_CHECK` is read as a plain flag
   (`bool(os.environ.get(..., "").strip())`, `src/updater.py:46`) — so `0`,
   `false` and `no` **also** disable the check. Only an empty or whitespace-only
   value leaves it enabled.
2. It is **not** a `DEFAULT_CONFIG` key (`src/config.py`) and **not** in
   `src/config_schema.py` — it does not appear in the configuration TUI and must
   be added to `~/.gitpr/.env` by hand. It still works there because
   `src/i18n.py:21` runs `load_dotenv` at import time, before the gate.
3. All four subcommands bypass the gate entirely via `ctx.invoked_subcommand`
   (`src/main.py:548`), as do `--help`/`--version` — neither was listed in the
   existing exemptions table.

**Secondary edits required for coherence:** `docs/auto-update.md` (×5) asserted
*"There is no flag, fallback or compatibility mode that keeps an outdated version
running"* — which the tutorial would have directly contradicted. The claim was
narrowed to an **installed release** and the escape switch named. The READMEs
(×5) offered only the pipenv route and had a malformed clone URL
(`gitpr.git.git`), now corrected to `https://github.com/gitpr-cli/gitpr.git`
(confirmed against `git remote -v`).

### Changed files

| File | Change type | Description |
|------|-------------|-------------|
| `docs/tutorial/install-from-source.md` | docs (new) | EN canonical tutorial — 9 sections |
| `docs/tutorial/install-from-source.pt_br.md` | docs (new) | PT-BR translation |
| `docs/tutorial/install-from-source.pt_pt.md` | docs (new) | PT-PT translation |
| `docs/tutorial/install-from-source.es_es.md` | docs (new) | ES-ES translation |
| `docs/tutorial/install-from-source.fr_fr.md` | docs (new) | FR-FR translation |
| `docs/auto-update.md` + `.pt_br`/`.pt_pt`/`.es_es`/`.fr_fr` | docs | Line 25: removed the false absolute claim, linked the tutorial |
| `README.md` + `.pt_br`/`.pt_pt`/`.es_es`/`.fr_fr` | docs | "From Source Code": added `pip install -e .` route, fixed clone URL, link to the tutorial |
| `docs/ARCHITECTURE.md` | docs | Added the tutorial to the 5-language doc index |

No file under `src/` or `tests/` was touched — the change is purely documentary.

### Impact

- **Functionality:** none. No code, no i18n keys, no CLI surface changed.
- **Performance:** none.
- **Compatibility:** none. `GITPR_SKIP_UPDATE_CHECK` is documented as a
  **local/offline development** resource, explicitly not a substitute for
  updating a released installation. The gate policy itself is unchanged.

### Verification performed

1. Structural parity across the 5 variants — identical in all five: 9 `##`
   sections, 10 fenced code blocks, 3 tables (differing only in translated prose,
   237–247 lines).
2. `grep -c "gitpr.git.git" README*.md` → 0 in all five.
3. `grep -c "tutorial/install-from-source"` → 1 in all five READMEs, all five
   `auto-update` files, and `docs/ARCHITECTURE.md`.
4. Live rehearsal of both operational assertions in the tutorial:
   - `pip list --editable` → `gitpr-cli 1.2.0  C:\Users\nataniel\projetos\pessoal\gitpr_projeto\gitpr`
   - `gitpr -u` → ran to completion unblocked, printed `✅ Você já está usando a
     versão mais recente do GitPR.` (exit 0)
5. `git status --short` → 11 modified files, `docs/tutorial/` untracked. Nothing
   committed, staged or amended, per the project rule.

### Incidental finding

`pip list --editable` emits `WARNING: Ignoring invalid distribution ~itpr-cli`.
Investigation showed two stale directories in `site-packages` —
`~itpr_cli-0.0.28.dist-info` and `~itpr_cli-0.0.30.dist-info` — the rename
artifacts pip leaves behind when an uninstall/upgrade is interrupted. They are
inert and ignored by pip. Because a reader following the tutorial will hit this
warning on the exact command the tutorial prescribes, a short note explaining it
was added to §7 in all five languages. Removing them requires no action unless
the warning is unwanted.

### Next steps (if applicable)

- **`docs/auto-update.md:44` remains inaccurate.** It states the connection
  guardian runs "before any network operation", but the update gate runs before
  it (`src/main.py:621` vs `:852`). Pre-existing, left untouched as out of scope.
- **Consider exposing `GITPR_SKIP_UPDATE_CHECK` in the configuration TUI.** It is
  currently documentable but not editable through the interface. This is a
  product decision, deliberately not taken here.
- **`docs/ARCHITECTURE.md` still labels the tutorial block "Portuguese only"**, a
  statement that now sits next to a five-language tutorial in its own
  subdirectory. The new entry was placed in the main 5-language list rather than
  that block, so the heading remains true of its own contents — but the split is
  worth revisiting if more tutorials gain translations.
- **The version bump `1.2.0` was committed during this task** (in `4218b5a docs:
  update docs files`, alongside docs changes). The editable install is therefore
  no longer at risk of re-blocking on the current tree. Note that the bump is a
  source change riding in a `docs:` commit; a separate `chore:` commit would
  match the project's atomic-commit rule.
