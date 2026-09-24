## Goal Description
Update the project's `README.md` to include any new features that are present in the codebase but not yet documented. Then propagate those updates to the localized README files (`README.es_es.md`, `README.fr_fr.md`, `README.pt_br.md`, `README.pt_pt.md`) to keep all language versions consistent.

## User Review Required
> [!IMPORTANT] The plan modifies multiple large markdown files. Ensure that the added feature descriptions are accurate and do not duplicate existing content. Verify that the localized files are updated in the same order.

## Open Questions
> [!WARNING] Do you want the new feature list to be placed under a specific section (e.g., a new "New Features" heading) or appended to the existing "Features" list? 
> [!CAUTION] Should we keep the language of the localized READMEs exactly as they are, only inserting the same English text, or attempt a native translation? (Current approach will insert the English text unchanged into each localized file.)

## Proposed Changes
---
### README.md (English)
#### [MODIFY] README.md
- Add a "New Features" subsection after the existing feature list.
- List each new feature with a brief description and a link to the relevant documentation.

### Localized READMEs
#### [MODIFY] README.es_es.md
#### [MODIFY] README.fr_fr.md
#### [MODIFY] README.pt_br.md
#### [MODIFY] README.pt_pt.md
- Insert the same "New Features" subsection (in English) at the same location in each file to keep them synchronized.

---
## Verification Plan
- Run `git diff` to ensure only the intended README files are changed.
- Build the project (`pipenv run python -m pytest -q`) to confirm no side effects.
- Manually open each README in a markdown viewer to confirm the new section renders correctly.

### Automated Tests
```
pipenv run pytest -q
```

### Manual Verification
1. Open each README file and verify the new "New Features" section appears.
2. Ensure links point to existing documentation files.
3. Confirm no other files were modified.

## Walkthrough
(To be completed after implementation.)
