# 🚀 Pull Request Suggestion

**Recommended Commit Message:**
```text
chore: bump version to 0.0.33 and add DeepSeek V3 tokenizer docs
```

---

## 🎯 Summary

Increment project version to 0.0.33, update language dictionary version to v0.0.11, and provide documentation/example for using the DeepSeek V3 tokenizer.

## 🛠️ Technical Changes

- Updated version numbers in `src/updater.py`.
- Added `docs/extra/deepseek_v3_tokenizer/deepseek_tokenizer.py` – a self-contained example script to load the tokenizer and encode a sample string.
- Added `docs/extra/deepseek_v3_tokenizer/tokenizer_config.json` – the tokenizer configuration file including special tokens, chat template, and `LlamaTokenizerFast` class reference.

## ⚠️ Impact/Warnings

- No breaking changes; purely a version bump and documentation addition.
- Ensure dependent systems are aware of the new release version for compatibility.