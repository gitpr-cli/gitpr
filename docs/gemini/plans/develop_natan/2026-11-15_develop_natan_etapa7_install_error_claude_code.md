# Implementation Plan — Stage 7: Include `claude-code` in `--install` error message and sync i18n

- **Date:** 2026-11-15
- **Branch:** `develop_natan`
- **Reference:** `docs/prompts/relatorio_pendencias_proximos_passos_i18n.md` (L192–L211)

## Goal Description

Align the unknown-editor error message returned by `_install_for_editor` in `src/mcp_server.py` with the `--install` CLI `choices` (`vscode`, `cursor`, `claude-code`, `claude`, `zed`, `auto`), keep all six `langs/*.json` translation dictionaries in parity, and cover the behavior with a unit test in `tests/test_mcp_server.py`.

## Proposed Changes

### 1. MCP Server (`src/mcp_server.py`)
- In `_install_for_editor` (around line 2901), update the `__(...)` string:
  - From: `"Unknown editor: '{editor}'. Valid options: vscode, cursor, claude, zed, auto"`
  - To: `"Unknown editor: '{editor}'. Valid options: vscode, cursor, claude-code, claude, zed, auto"`

### 2. CLI i18n Dictionaries (`langs/*.json`)
- Update key and translated value in all 6 files (`pt_br.json`, `pt_pt.json`, `es.json`, `es_es.json`, `fr.json`, `fr_fr.json`) around line 1179:
  - New key: `"Unknown editor: '{editor}'. Valid options: vscode, cursor, claude-code, claude, zed, auto"`
  - `pt_br.json` / `pt_pt.json`: `"Editor desconhecido: '{editor}'. Opções válidas: vscode, cursor, claude-code, claude, zed, auto"`
  - `es.json` / `es_es.json`: `"Editor desconocido: '{editor}'. Opciones válidas: vscode, cursor, claude-code, claude, zed, auto"`
  - `fr.json` / `fr_fr.json`: `"Éditeur inconnu : '{editor}'. Options valides : vscode, cursor, claude-code, claude, zed, auto"`

### 3. Unit Tests (`tests/test_mcp_server.py`)
- Add a unit test verifying that calling `_install_for_editor("invalid-editor", tmp_path)` returns `(False, msg)` where `msg` contains all valid options (`vscode`, `cursor`, `claude-code`, `claude`, `zed`, `auto`).

## Verification Plan

```bash
python -m pytest tests/test_i18n.py tests/test_mcp_server.py -v
```
