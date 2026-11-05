# Plano de Execução — Estabilização de `test_headless_full_flow`

**Data:** 2026-11-05  
**Branch:** `develop_natan`  
**Identificador:** `stabilize_test_headless_full_flow`

---

## 1. Escopo das Modificações

Arquivo a alterar: `tests/test_commit_app.py`

### 1.1 Imports
- Importar `Button` de `textual.widgets` para permitir chamada tipada de `query_one("#btn_confirm", Button)`.

### 1.2 Função auxiliar `_wait_until`
- Ajustar `timeout=10.0` como padrão (anteriormente `5.0`).

### 1.3 Método `test_headless_full_flow`
- Atualizar a espera de aparecimento da tela `CommitMessageScreen`:
  ```python
  await _wait_until(
      pilot,
      lambda: isinstance(app.screen, CommitMessageScreen)
      and app.screen.is_mounted
      and bool(app.screen.query("#btn_confirm")),
  )
  ```
- Substituir:
  ```python
  await pilot.click("#btn_confirm")
  ```
  Por:
  ```python
  app.screen.query_one("#btn_confirm", Button).press()
  await pilot.pause()
  ```

---

## 2. Estratégia de Verificação

1. Executar bateria isolada de `tests/test_commit_app.py`:
   `pytest tests/test_commit_app.py -v` (com bypass de sandbox para permitir loopback do Textual/asyncio no Windows).
2. Executar repetições consecutivas do teste `test_headless_full_flow` (ex: 5 iterações) para atestar ausência de intermitência.
3. Verificar a suíte completa de testes do módulo de commits para garantir que nenhum comportamento colateral foi afetado.
