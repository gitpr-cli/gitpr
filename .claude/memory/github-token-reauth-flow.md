---
name: github-token-reauth-flow
description: Validação de PAT via GET /user antes da TUI com loop de re-autenticação em 401
metadata:
  type: project
  source: docs/claude-code/reports/develop_natan/2026-07-28_github_token_401_reauth.md
  date: 2026-07-28
  branch: develop_natan
---

O fluxo de autenticação GitHub para `gitpr -is` foi reforçado com validação
proativa e re-autenticação em 401:

1. **Validação antes da TUI**: `validate_github_token()` (`src/config.py`) faz
   uma chamada leve `GET /api.github.com/user` para verificar o PAT.
   Se expirado, re-prompt ao usuário (máx 3 tentativas).

2. **Re-autenticação durante a TUI**: `IssueApp.action_create_issue()` em
   `src/ui/issue_app.py` detecta 401 e sinaliza `final_action = "reauth"`.
   O handler em `main.py` faz loop back para validação e relança a TUI
   **sem perder o rascunho da issue**.

3. **Separação de responsabilidades**:
   - `_remove_expired_token()`: limpa token inválido
   - `_show_auth_instructions()`: exibe instruções de geração de PAT
   - `_prompt_and_save_token()`: captura e persiste novo token

**Why:** Antes, um token expirado só era detectado ao tentar criar a issue
no GitHub (F3), resultando em erro silencioso. Agora a validação é proativa
e o usuário pode re-autenticar sem perder o trabalho.

**How to apply:**
1. `validate_github_token()` deve ser usada antes de qualquer operação GitHub
2. O loop `while True` com `reauth` action em `main.py` preserva o estado da TUI
3. Max 3 tentativas de token antes de desistir
4. O PAT necessário tem scope `repo` (URL de geração com parâmetros preenchidos)
5. Novas features que usam GitHub API devem integrar o mesmo fluxo de validação
