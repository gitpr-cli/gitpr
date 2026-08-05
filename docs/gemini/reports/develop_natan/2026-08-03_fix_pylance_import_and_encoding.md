## Completion Report — Fix Pylance Import and Encoding

### What was done
- Added `[tool.pyright]` configuration to `pyproject.toml` to explicitly define the project root as `.` for Pylance/Pyright, fixing the incorrect `Cannot find module src.i18n` IDE inference.
- Added a safeguard in `src/main.py` to reconfigure `sys.stdout` to UTF-8 with `errors='replace'`, preventing `UnicodeEncodeError` when printing emojis (like 🚀) on Windows consoles (cp1252 default encoding).

### Changed files
| File | Change type | Description |
|------|-------------|-------------|
| pyproject.toml | fix | Added pyright configuration block with `executionEnvironments` mapping to `.` |
| src/main.py | fix | Reconfigured `sys.stdout` encoding to UTF-8 to fix crash on startup in Windows terminals |

### Impact
- **Functionality:** `gitpr` executable no longer crashes at startup on Windows terminals with legacy encodings.
- **Performance:** Negligible impact on startup.
- **Compatibility:** Pylance now correctly resolves imports out of the box without flagging false positive errors, improving developer experience.

### Next steps (if applicable)
- Verify if any other outputs explicitly write emojis directly to streams not protected by the `sys.stdout.reconfigure` rule.
