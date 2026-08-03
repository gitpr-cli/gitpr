## Completion Report — Update Version to 0.0.31 & Lang Version to v0.0.9

### What was done
- Updated project version from `0.0.30` to `0.0.31` in `pyproject.toml`.
- Updated `__version__` from `0.0.30` to `0.0.31` and `__lang_version__` from `v0.0.8` to `v0.0.9` in `src/updater.py`.

### Changed files
| File | Change type | Description |
|------|-------------|-------------|
| [pyproject.toml](file:///c:/Users/nataniel/projetos/python/gitpr/pyproject.toml) | refactor | Updated version to 0.0.31 |
| [src/updater.py](file:///c:/Users/nataniel/projetos/python/gitpr/src/updater.py#L9-L12) | refactor | Updated `__version__` to 0.0.31 and `__lang_version__` to v0.0.9 |

### Impact
- **Functionality:** Version identifiers updated for PyPI metadata, CLI version check, and language dictionary auto-updater.
- **Performance:** No impact.
- **Compatibility:** Fully compatible; triggers language updates for clients using `__lang_version__` v0.0.9.
