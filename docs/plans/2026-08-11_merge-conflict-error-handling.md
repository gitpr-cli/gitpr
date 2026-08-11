# Plano: Tratamento de erro de merge conflict no PR Publisher

## Contexto

Ao publicar um PR via `--publish`, o fluxo pergunta se o usuário quer fazer merge. Quando o merge falha com **405 "Pull Request has merge conflicts"**, a UI não mostra nenhum erro — simplesmente pergunta "Open in browser?" como se tudo tivesse funcionado. O erro só é visível no log (`C:\Users\nataniel\.gitpr\logs\pr_desc\pr_desc_*.log`).

### Causa raiz (múltiplos defeitos em `_do_merge`)

1. **`final_action` nunca é atualizado** no `_do_merge` — permanece `"created"`, fazendo o `main.py:956` imprimir a mensagem de erro em **verde** (cor de sucesso)
2. **Após falha, chama `_prompt_open_browser`** — o usuário vê "Open in browser?" como se o merge tivesse funcionado, sem nunca ver o erro na TUI
3. **Concatena erro ao invés de substituir**: `"❌ Merge failed: ..." + "\n" + self.final_message` — a mensagem de sucesso anterior fica junto com o erro
4. **Sem diferenciação para 405 (merge conflict)**: o status HTTP é ignorado, nenhuma orientação específica sobre como resolver

## Arquivos a modificar

### 1. `src/ui/pr_publish_app.py` — método `_do_merge` (linhas 1107–1126)

**Mudanças:**

- **No caminho de falha do merge**, em vez de chamar `_prompt_open_browser`, mostrar uma tela de erro com `_show_error` (ou similar) informando claramente o que aconteceu
- **Para merge conflict (status 405)**: mensagem específica — "PR has merge conflicts. Resolve them manually on GitHub and merge there."
- **Para outros erros**: mensagem genérica com o erro retornado pela API
- **Setar `final_action = "merge_failed"`** no caminho de falha para que `main.py` use cor vermelha
- **No caminho de sucesso**: setar `final_action = "merged"` para correta distinção
- **Não concatenar** a mensagem de erro com a de sucesso anterior — substituir `final_message` completamente no erro, ou manter a mensagem de PR criado + erro de merge como linhas separadas mas com indicador claro
- **Thread safety**: usar `call_from_thread` para atualizar `final_message` e `final_action`, ou mover toda a lógica de resultado para um callback na main thread

### 2. `src/main.py` — exibição pós-TUI (linha 956)

- Adicionar `"merged"` à lista de ações "verdes": `if app.final_action in ["saved", "created", "merged"]`
- `"merge_failed"` automaticamente cairá no else (vermelho) — comportamento correto

## Verificação

1. Simular ou forçar um merge que retorna 405 e verificar se o modal de erro aparece na TUI
2. Verificar se `final_message` é exibido em vermelho após saída da TUI
3. Confirmar que o fluxo de merge bem-sucedido continua funcionando (mensagem verde)
4. Rodar `pipenv run pytest -v` para garantir que nada quebrou
