# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
feat: show progress modal while merging pull request
```

---

## 🎯 Summary

Merging a pull request previously ran silently in a background worker: the user had no visual feedback while the forge call was in flight, and an unexpected provider exception killed the daemon thread without ever reporting back, leaving the UI stuck. This change surfaces the merge as a first-class, observable operation by reusing the existing progress modal with a merge-specific title and status line, and by guaranteeing that every merge outcome — success, conflict, or unexpected error — reaches the user.

## 🛠️ Technical Changes

- Extend `CommitProgressScreen` with an optional `title` parameter so the same modal serves both commit and merge flows, defaulting to the existing "📦 Processing commit..." text.
- Add `mark_finished(show_close=False)` to allow auto-dismissed flows (merge success) to complete the bar without offering a Close button.
- Track `_merge_progress_screen` on `PrPublishApp` and push the modal before the worker starts, so fast callbacks always find mounted widgets.
- Start the merge worker from the screen's mount timer, removing the race between modal mounting and a fast success/failure callback.
- Add a generic `except Exception` in the merge worker that logs the error and routes it to `_on_merge_failure`, preventing silent thread death.
- On success, append the merged PR confirmation to the modal log, auto-dismiss after 1.2s, then show the existing open-in-browser prompt; on failure, pop the progress modal before showing the failure dialog.
- Handle the case where the user dismisses the progress modal mid-merge: the merge still completes and the browser prompt is shown without touching stale widgets.
- Add translations for the new merge strings in `es`, `es_es`, `fr`, `fr_fr`, `pt_br`, and `pt_pt`.
- Add tests covering title rendering, close-button behavior, the animated modal during merge, the auto-merge path, conflict handling, unexpected exceptions, and dismissal-while-merging.

## ⚠️ Impact/Warnings

- No database, dependency, or environment variable changes.
- Signature changes are backward compatible: `title` defaults to `None` and `mark_finished()` defaults to `show_close=True`, so existing commit flows are unaffected.
- Six locale files require the new keys; any additional language added later must include them to avoid untranslated merge strings.
- Merge failures caused by bugs (previously swallowed) now surface to users as a "❌ Merge Failed" dialog with the raw error message.

close #215

---

[![GitPR](https://img.shields.io/badge/GitPR-no_issues-brightgreen)](https://gitpr.natanfiuza.dev.br/)