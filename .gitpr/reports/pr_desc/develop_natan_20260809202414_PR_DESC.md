# 🚀 Pull Request Suggestion

**Recommended Commit Message:**
```text
feat: export commit metrics and map-reduce large diffs
```

---

🎯 Summary

This PR enhances monitoring and scalability by exporting detailed commit execution metrics and introducing a map-reduce approach for processing large diffs during issue generation. It enables better visibility into token usage and duration, while ensuring the system can handle larger code changes without hitting context limits.

🛠️ Technical Changes

- Added export of commit metrics (`.csv` and `.json`) capturing token usage, execution duration, and repository details after successful commit commands.
- Implemented map-reduce processing for large diffs: splits the diff into chunks, generates partial summaries per chunk, and consolidates them into a final AI call.
- Aggregated token metadata across chunks and added map-reduce usage logging for improved monitoring and caching.

⚠️ Impact/Warnings

- New metric files will be created in the working directory; ensure sufficient disk space.
- Map-reduce may increase the total number of API calls but reduces individual payload size, preventing context length errors.
- No breaking changes to existing functionality.

close #95