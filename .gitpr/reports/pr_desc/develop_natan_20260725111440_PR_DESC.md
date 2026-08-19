# 🚀 Sugestão de Pull Request

**Commit Message Recomendada:**
```text
feat: add adaptive spinner speed and expand thinking words
```

---

## 🎯 Summary
This change enhances the spinner's user experience by dynamically adjusting reveal speed based on phrase length, and massively expands the collection of thinking words/phrases in multiple languages with humorous and varied messages.

## 🛠️ Technical Changes
- Added `_adaptive_speed()` and `_next_word()` methods to `Spinner` class in `src/spinner.py`.
- Adapted the spin loop to use dynamic `sleep_time` and recalibrate on word change.
- Expanded English, Spanish, French, Portuguese (BR and PT) word lists with 84+ entries each, including creative phrases.
- Added a planning document `docs/plans/words_happy.md` with new English phrases.

## ⚠️ Impact/Warnings
- No breaking changes; spinner behavior remains consistent, just smoother for longer phrases.
- Slightly larger language files may increase memory usage negligibly.
- All existing functionality preserved.

close #62