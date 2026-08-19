# 🚀 Pull Request Suggestion

**Recommended Commit Message:**
```text
feat: add DeepSeek V3 tokenizer support
```

---

🎯 **Summary**
This PR adds initial support for the DeepSeek V3 tokenizer, enabling its use within the project. It includes an example script for loading the tokenizer and a configuration file with chat template.

🛠️ **Technical Changes**
- Added `example_deepseek_v3_tokenizer.py` script to demonstrate loading and using the DeepSeek V3 tokenizer with the `transformers` library.
- Added tokenizer configuration file (`tokenizer_config.json`) for LlamaTokenizerFast with chat template and special tokens for DeepSeek V3.
- Bumped project version to `0.0.33` and language dictionary to `v0.0.11` in `updater.py`.

⚠️ **Impact/Warnings**
- No breaking changes. Users can now utilize the DeepSeek V3 tokenizer via the provided example.