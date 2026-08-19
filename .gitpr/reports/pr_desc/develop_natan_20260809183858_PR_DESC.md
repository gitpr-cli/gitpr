# 🚀 Pull Request Suggestion

**Recommended Commit Message:**
```text
chore: add DeepSeek V3 tokenizer docs and bump versions
```

---

## 🎯 Summary

Added the DeepSeek V3 tokenizer script and configuration file to the documentation for reference. Updated version numbers in `updater.py` to align with recent GitPR (0.0.33) and language dictionary (v0.0.11) releases.

## 🛠️ Technical Changes

- Added `deepseek_tokenizer.py` and `tokenizer_config.json` to the documentation directory.
- Bumped GitPR version to `0.0.33` and language dictionary version to `v0.0.11` in `updater.py`.

## ⚠️ Impact/Warnings

- No functional impact; documentation and version metadata only.
- Downstream consumers relying on the version strings in `updater.py` will now reflect the updated values.