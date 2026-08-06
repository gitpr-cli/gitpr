# Plan: Versionamento e Sincronização de Scripts Git Hooks

## Context

GitPR manages Git hooks via shell scripts in `scripts/`. Currently there is no version control or automatic sync — hooks are installed once via `--installhooks` and never updated. The scripts themselves are hardcoded in Portuguese with no i18n support. This plan implements versioning with auto-sync and multi-language hook scripts (en, pt_br, pt_pt, fr, es).

## Design Decisions

### 1. Independent `__scripts_version__` (NOT piggybacking on `__lang_version__`)

The existing pattern uses `__lang_version__` to refresh translations, smart-excludes, and thinking words together. However, hook scripts change on a different cadence than language resources — a script logic fix shouldn't force re-download of all translation files, and a translation update shouldn't force re-download of scripts. **Use a dedicated `__scripts_version__` with its own `SCRIPTS_VERSION` marker.**

### 2. Auto-check placement in main.py

Called inside `cli()` at line ~244, right after `--lang` handling and before any command-specific logic. The check is a single env-var comparison — no I/O until versions actually differ. When versions differ, downloads happen and the user sees the sync output block.

### 3. URL naming pattern

Following the existing `generate_skill_template()` convention:
- **English (default)**: `{template}.sh` (no suffix) — e.g., `pre-commit-template.sh`
- **Other languages**: `{template}.{lang}.sh` — e.g., `pre-commit-template.pt_br.sh`
- At download time: try `{template}.{lang}.sh` first, fall back to `{template}.sh` if 404.

### 4. Migration of existing scripts

Current scripts are in Portuguese → they become the `.pt_br.sh` variants. New English versions become the default (no-suffix) files.

---

## Implementation Steps

### Step 1: Add `__scripts_version__` to `src/updater.py`

**File:** [src/updater.py](src/updater.py), after line 13

```python
__scripts_version__ = "v0.0.1"  # Hook scripts version control
```

### Step 2: Create `sync_hooks()` in `src/core.py`

New function that runs on every gitpr execution:

```python
def sync_hooks():
    """
    Checks if installed Git hooks need updating based on __scripts_version__.
    Called on every gitpr execution. Only downloads when versions differ.
    """
```

Logic:
1. Get `hooks_dir = os.path.join(os.getcwd(), ".git", "hooks")` — return silently if no `.git`
2. Read `SCRIPTS_VERSION` from `.env` via `os.getenv("SCRIPTS_VERSION")`
3. Import `__scripts_version__` from `src.updater`
4. If `SCRIPTS_VERSION == __scripts_version__`: return (no update needed)
5. If different or missing:
   - Detect language from `CURRENT_LANG` (from `src.i18n`)
   - For each of the 5 hooks, download the language-appropriate script
   - Write to `.git/hooks/`, chmod +x
   - Show progress output (cyan "syncing" messages)
   - Stamp `SCRIPTS_VERSION` in `.env` via `set_key()`
   - Print success summary

Language resolution:
- Extract base lang: `CURRENT_LANG` → `pt_br` (already normalized by i18n)
- EN (starts with "en"): `lang_suffix = ""`
- Other: `lang_suffix = f".{CURRENT_LANG}"`
- URL: `https://raw.githubusercontent.com/natanfiuza/gitpr/main/scripts/{template}{lang_suffix}.sh`
- If download fails with 404 for language-specific URL, retry without suffix (English fallback)

### Step 3: Modify `install_git_hooks()` in `src/core.py`

**File:** [src/core.py](src/core.py), function at line 522

Changes:
1. Add `lang_suffix` logic (same as Step 2)
2. Build URL with `{template}{lang_suffix}.sh`
3. After all hooks installed successfully, stamp `SCRIPTS_VERSION` in `.env`:
   ```python
   from dotenv import set_key
   from src.config import ENV_FILE
   from src.updater import __scripts_version__
   set_key(ENV_FILE, "SCRIPTS_VERSION", __scripts_version__)
   ```
4. Keep existing behavior: overwrite, chmod +x, error handling per-hook

### Step 4: Create translated hook scripts

**Directory:** `scripts/`

#### 4a. `pre-commit-template.sh` (and variants)

Current content (PT-BR) → move to `pre-commit-template.pt_br.sh`.
Create new English base `pre-commit-template.sh`:

| Message               | EN                                                                                                | PT-BR (existing)                                                                                                    |
| --------------------- | ------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| Header comment        | `# GitPR Linter Hook - Pre-commit validation`                                                     | `# GitPR Linter Hook - Pre-commit validation`                                                                       |
| Color vars comment    | `# Terminal colors`                                                                               | `# Cores para o terminal`                                                                                           |
| Lint start            | `🔍 GitPR: Validating static analysis rules...`                                                    | `🔍 GitPR: A validar regras de análise estática...`                                                                  |
| Command check comment | `# Try to run the command.`                                                                       | `# Tenta executar o comando.`                                                                                       |
| Not found error       | `❌ Error: 'gitpr' command not found.`                                                             | `❌ Erro: Comando 'gitpr' não encontrado.`                                                                           |
| Install hint          | `Make sure GitPR is installed via pip (pip install gitpr-cli) or the executable is in your PATH.` | `Certifique-se de que o GitPR está instalado via pip (pip install gitpr-cli) ou que o executável está no seu PATH.` |
| Exit code comment     | `# Capture the exit code`                                                                         | `# Captura o código de saída`                                                                                       |
| Blocked               | `🚨 COMMIT BLOCKED!`                                                                               | `🚨 COMMIT BLOQUEADO!`                                                                                               |
| Violations found      | `The Linter found code violations that need fixing.`                                              | `O Linter encontrou violações de código que precisam de correção.`                                                  |
| Force hint            | `Tip: To force the commit (not recommended), use: git commit --no-verify`                         | `Dica: Para forçar o commit (não recomendado), use: git commit --no-verify`                                         |
| Approved              | `✅ Code approved! Finishing commit...`                                                            | `✅ Código aprovado! A finalizar commit...`                                                                          |

Then create `pt_pt`, `fr`, `es` variants with same structure, translating only the messages/comments.

#### 4b. `prepare-commit-msg-template.sh` (and variants)

Current content (PT-BR) → move to `prepare-commit-msg-template.pt_br.sh`.
Create new English base version:

| Message          | EN                                                                        | PT-BR (existing)                                                                     |
| ---------------- | ------------------------------------------------------------------------- | ------------------------------------------------------------------------------------ |
| Header           | `# GitPR Hook - Auto-fill commit message with AI`                         | `# GitPR Hook - Preenche a mensagem de commit automaticamente com IA`                |
| Color vars       | `# Terminal colors`                                                       | `# Cores para o terminal`                                                            |
| Manual msg check | `# If user already passed a manual message with 'git commit -m', skip AI` | `# Se o usuário já passou uma mensagem manual com 'git commit -m', aborta a IA`      |
| AI request       | `🤖 GitPR: Requesting AI commit suggestion...`                             | `🤖 GitPR: A pedir sugestão de commit à IA...`                                        |
| Call comment     | `# Call GitPR passing the commit file path ($1) to our --hook flag`       | `# Chama o GitPR repassando o caminho do arquivo ($1) para a nossa nova flag --hook` |
| Not found        | `❌ Warning: 'gitpr' command not found. Proceeding without AI.`            | `❌ Aviso: Comando 'gitpr' não encontrado. Prosseguindo sem IA.`                      |

Then create `pt_pt`, `fr`, `es` variants.

#### 4c. Telemetry hooks (pre-push, post-merge, post-checkout)

These have no user-facing output — only comments. Strategy:
- Current versions → rename to `.pt_br.sh` (comments already in PT-BR)
- Create English base versions (translate comments only)
- Create `pt_pt`, `fr`, `es` variants (translate comments only)

**Files to create (20 new + rename 5 existing):**
```
scripts/
├── pre-commit-template.sh          (NEW - EN base)
├── pre-commit-template.pt_br.sh    (renamed from current)
├── pre-commit-template.pt_pt.sh    (NEW)
├── pre-commit-template.fr.sh       (NEW)
├── pre-commit-template.es.sh       (NEW)
├── prepare-commit-msg-template.sh  (NEW - EN base)
├── prepare-commit-msg-template.pt_br.sh (renamed from current)
├── prepare-commit-msg-template.pt_pt.sh (NEW)
├── prepare-commit-msg-template.fr.sh    (NEW)
├── prepare-commit-msg-template.es.sh    (NEW)
├── pre-push-template.sh            (NEW - EN base)
├── pre-push-template.pt_br.sh      (renamed from current)
├── pre-push-template.pt_pt.sh      (NEW)
├── pre-push-template.fr.sh         (NEW)
├── pre-push-template.es.sh         (NEW)
├── post-merge-template.sh          (NEW - EN base)
├── post-merge-template.pt_br.sh    (renamed from current)
├── post-merge-template.pt_pt.sh    (NEW)
├── post-merge-template.fr.sh       (NEW)
├── post-merge-template.es.sh       (NEW)
├── post-checkout-template.sh       (NEW - EN base)
├── post-checkout-template.pt_br.sh (renamed from current)
├── post-checkout-template.pt_pt.sh (NEW)
├── post-checkout-template.fr.sh    (NEW)
└── post-checkout-template.es.sh    (NEW)
```

### Step 5: Integrate auto-sync into `src/main.py`

**File:** [src/main.py](src/main.py)

Add call to `sync_hooks()` inside `cli()` function:
- After `--lang` handling block (~line 249)
- Before any command-specific logic (skill, installhooks, blame, etc.)
- The function is silent when versions match, so it won't clutter normal output
- Import `sync_hooks` from `src.core`

```python
# After --lang handling:
from src.core import sync_hooks
sync_hooks()
```

### Step 6: Test

1. **Existing tests**: `python -m pytest tests/ -v` — ensure no regressions
2. **Manual verification**: Run `gitpr` (any command) — verify no output when hooks are current
3. **Simulate version mismatch**: Set `SCRIPTS_VERSION=v0.0.0` in `.env`, run `gitpr` — verify sync output and version stamp
4. **Test `--installhooks`**: Run on a test repo — verify language-specific scripts downloaded and `SCRIPTS_VERSION` stamped
5. **Test fallback**: Set `GITPR_LANG=fr`, delete `pre-commit-template.fr.sh` from `scripts/`, run `--installhooks` — verify fallback to English

---

## Files Modified

| File                                           | Change            | Description                                                                        |
| ---------------------------------------------- | ----------------- | ---------------------------------------------------------------------------------- |
| `src/updater.py`                               | Add constant      | `__scripts_version__ = "v0.0.1"`                                                   |
| `src/core.py`                                  | Add + modify      | New `sync_hooks()` function; modify `install_git_hooks()` for i18n + version stamp |
| `src/main.py`                                  | Add import + call | Call `sync_hooks()` after lang handling                                            |
| `scripts/pre-commit-template.sh`               | Rewrite           | English base version                                                               |
| `scripts/pre-commit-template.pt_br.sh`         | Rename            | Current PT-BR content                                                              |
| `scripts/pre-commit-template.pt_pt.sh`         | New               | European Portuguese                                                                |
| `scripts/pre-commit-template.fr.sh`            | New               | French                                                                             |
| `scripts/pre-commit-template.es.sh`            | New               | Spanish                                                                            |
| `scripts/prepare-commit-msg-template.sh`       | Rewrite           | English base version                                                               |
| `scripts/prepare-commit-msg-template.pt_br.sh` | Rename            | Current PT-BR content                                                              |
| `scripts/prepare-commit-msg-template.pt_pt.sh` | New               | European Portuguese                                                                |
| `scripts/prepare-commit-msg-template.fr.sh`    | New               | French                                                                             |
| `scripts/prepare-commit-msg-template.es.sh`    | New               | Spanish                                                                            |
| `scripts/pre-push-template.sh`                 | Rewrite           | English base version                                                               |
| `scripts/pre-push-template.pt_br.sh`           | Rename            | Current PT-BR content                                                              |
| `scripts/pre-push-template.pt_pt.sh`           | New               | European Portuguese                                                                |
| `scripts/pre-push-template.fr.sh`              | New               | French                                                                             |
| `scripts/pre-push-template.es.sh`              | New               | Spanish                                                                            |
| `scripts/post-merge-template.sh`               | Rewrite           | English base version                                                               |
| `scripts/post-merge-template.pt_br.sh`         | Rename            | Current PT-BR content                                                              |
| `scripts/post-merge-template.pt_pt.sh`         | New               | European Portuguese                                                                |
| `scripts/post-merge-template.fr.sh`            | New               | French                                                                             |
| `scripts/post-merge-template.es.sh`            | New               | Spanish                                                                            |
| `scripts/post-checkout-template.sh`            | Rewrite           | English base version                                                               |
| `scripts/post-checkout-template.pt_br.sh`      | Rename            | Current PT-BR content                                                              |
| `scripts/post-checkout-template.pt_pt.sh`      | New               | European Portuguese                                                                |
| `scripts/post-checkout-template.fr.sh`         | New               | French                                                                             |
| `scripts/post-checkout-template.es.sh`         | New               | Spanish                                                                            |

## Verification

1. `python -m pytest tests/ -v` — all existing tests pass
2. `pipenv run python run.py -ih` — installs hooks with i18n, stamps SCRIPTS_VERSION
3. `pipenv run python run.py -c` — sync check runs silently (version matches)
4. Manually set `SCRIPTS_VERSION=v0.0.0` in `~/.gitpr/.env`, run any gitpr command — verify sync output
5. Test fallback: delete a language-specific script from GitHub test, verify English fallback works
