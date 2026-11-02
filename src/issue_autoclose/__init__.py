"""The issue-autoclose feature: remember the issue `gitpr -is` created.

Modules, in dependency order:
  - issue_registry.py — the local record at ``.gitpr/conf/github.yml``
  - register_created_issue.py — writes the record after ``gitpr -is`` creates one
  - resolve_close_issue.py — decides whether the next pull request closes it
  - insert_close_line.py — adds the closing line to the assembled PR body

Import the submodule you need (``from src.issue_autoclose.issue_registry
import IssueRegistry``). This package deliberately re-exports nothing: the
registry has no network dependency and must stay importable by itself.
"""
