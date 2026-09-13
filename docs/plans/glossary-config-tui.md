# Glossary — Configuration Screen

The vocabulary introduced by `gitpr config`. Each term here is one the screen's behaviour actually depends on; the ambiguity they resolve is noted, because in every case the wrong reading produces a bug rather than a wording preference.

---

## File value

The value of a variable **as written in `~/.gitpr/.env`**. Read with a file-only parser (`dotenv_values`), never with `os.getenv()`.

*Ambiguity resolved:* "the current value" is not a single thing in GitPR, because `load_dotenv()` runs with `override=False` everywhere. When a variable is exported in the shell, the process value and the file value differ, and only the file value is what the screen can meaningfully edit.

*Not to be confused with:* **effective value**.

---

## Effective value

The value the running process actually resolves at runtime: the environment variable when one is set, otherwise the file value, otherwise the built-in default.

*Ambiguity resolved:* the screen displays the **file value** while the process may be using the **effective value**. Everywhere else in the docs "the value" means the effective one; inside the configuration screen it does not. A field where the two differ is marked **⚠ in environment**.

---

## Shadowed

State of a variable whose name is also present in the process environment, so its file value is ignored at runtime. Shown as **⚠ in environment**.

*Ambiguity resolved:* "shadowed" and "overridden" are used interchangeably in the codebase; this document uses **shadowed** for the environment-beats-file relationship specifically, and reserves *overridden* for a GitPR download replacing a cached file.

---

## Restore (a field)

`Ctrl+R`. Removes the variable's line from the file so the built-in default applies again.

*Ambiguity resolved:* "restore the default" sounds like *write the default value into the file*. It does not — writing it would freeze today's default into the file and silently opt the user out of every future default change. Restore **removes**; the default stays in the code where it can keep moving.

*Not to be confused with:* **reset**, which is not a thing this screen does. There is no per-category restore.

---

## Pending change

An edit held in memory and not yet written to disk. The screen keeps these in a dictionary keyed by variable name, not in the widgets, so they survive navigating to another category.

*Ambiguity resolved:* "dirty" and "pending" describe the same state from two sides — *dirty* is the field's property, *pending* is the change's. The screen's own text says **unsaved**; all three refer to the same thing. Only a pending change on a **secret** field triggers credential validation.

---

## Advanced field

A setting GitPR maintains itself — downloaded-artifact version markers, the hook language, the spinner word list. Revealed by the **Show advanced** toggle, off on every launch.

*Ambiguity resolved:* "advanced" here means *not meant to be edited by hand*, not *difficult* and not *powerful*. Most are inert markers whose only effect is triggering a re-download when `__lang_version__` changes.

---

## Unknown key

A variable present in the file that the schema does not declare. Shown read-only in a category that appears only when such keys exist.

*Ambiguity resolved:* an unknown key is not an error and not necessarily dead — it may belong to a newer GitPR, a plugin, or a shell script of the user's. The screen therefore preserves it untouched instead of offering to remove it.

---

## Credential validation

The single network round trip performed before saving a changed secret, which separates *refused* from *unreachable*.

*Ambiguity resolved:* the two failures must not be treated alike. **Refused** (HTTP 401/403, or a provider answering "invalid API key") blocks the save, because storing a credential known to be wrong is indefensible. **Unreachable** (network failure, timeout) does not, because refusing to save a correct key typed behind a proxy would make the screen unusable offline. Anything ambiguous is treated as unreachable — a false *refused* would block a valid credential, which is the worse error.

*Not to be confused with:* **offline validation**, which checks a value's *shape* (`true`/`false`, a positive integer, a known placeholder) and needs no network.
