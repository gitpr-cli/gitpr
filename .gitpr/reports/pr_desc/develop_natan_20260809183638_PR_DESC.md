# 🚀 Pull Request Suggestion

**Recommended Commit Message:**
```text
feat: integrate DeepSeek V3 tokenizer with config
```

---

## 🎯 Summary
This change integrates the DeepSeek V3 tokenizer into the project, providing tokenization support for the DeepSeek chat model. It includes a utility script for encoding text and the necessary configuration file with chat template and special tokens, enabling compatibility with the model's expected input format.

## 🛠️ Technical Changes
- Added `deepseek_tokenizer.py` script that loads the tokenizer from a local directory and demonstrates encoding of "Hello!".
- Added tokenizer configuration file containing the DeepSeek V3 chat template, special tokens (BOS, EOS, etc.), and other settings.
- Bumped GitPR version to 0.0.33.
- Bumped language dictionary version to v0.0.11.

## ⚠️ Impact/Warnings
- Requires the DeepSeek V3 tokenizer files to be placed in the specified local directory; users must download them beforehand.
- Version bumps may affect dependent modules; verify compatibility before merging.