# Survey and Facts — Documentação da Quebra de Comportamento do `-c` Interativo como Nota de Migração

**Data:** 2026-11-09  
**Branch:** develop_natan  
**Task:** document_interactive_commit_migration_note  

---

## 1. Contexto e Problema

O comando `gitpr -c` (`--commit`) do GitPR foi originalmente projetado como um comando puramente de console que gerava uma mensagem de commit no padrão Conventional Commits via IA e a imprimia na saída padrão (`stdout`), sem modificar o stage ou executar o comando `git commit`.

### Histórico da Mudança (v1.4.4 e v1.6.0)
- **Antes da v1.4.4:** `gitpr -c` era um comando estritamente de console / silencioso. Ele analisava o diff dos arquivos em stage (`git diff --cached` ou `HEAD`), solicitava a mensagem à IA e exibia o texto no terminal. Ele nunca abria telas interativas e nunca realizava `git commit`.
- **A partir da v1.4.4 (commit `9bd2038`):** O comando foi reformulado para fornecer um fluxo TUI interativo completo de 4 etapas (`CommitApp`):
  1. Seletor de arquivos fora do stage (`StageFilesScreen`).
  2. Geração da mensagem com progresso animado (`CommitProgressScreen`).
  3. Revisão e edição do texto da mensagem (`CommitMessageScreen`).
  4. Execução do commit (`git commit -m "..."`) com barra animada e exibição do hash gerado.
- **Ajuste na v1.6.0 (commit `869e2a1`):** A implementação inicial de `CommitApp` travava ambientes headless / CI sem TTY porque `app.run()` esperava interatividade de terminal. Foi adicionada a guarda `if may_ask:`. Ambientes sem TTY (`sys.stdin.isatty()` falso) não abrem a TUI, caindo de volta no modo console que exibe a mensagem no stdout sem comitar.
- **A Lacuna na Documentação:**
  O arquivo `docs/commit-message-ia.md` (e suas 4 traduções: `.pt_br.md`, `.pt_pt.md`, `.es_es.md`, `.fr_fr.md`) foi atualizado para descrever o fluxo TUI novo, mas não incluía uma **Nota de Migração** explícita alertando sobre a quebra de comportamento para quem utilizava `gitpr -c` como comando silencioso ou em automações de CI, nem destacava explicitamente a diretriz: "antes era silencioso; em CI / hooks use `--hook`".

---

## 2. Decisões do Grill (Rodada 1)

1. **Localização e Formato Visual da Nota de Migração (`docs/commit-message-ia.*.md`)**:
   - Callout de aviso GitHub (`> [!WARNING]`) de **Nota de Migração / Migration Note** posicionado logo na Seção 1 (após a descrição do fluxo interativo de 4 etapas) com destaque visual imediato sobre a quebra em relação ao comportamento pré-v1.4.4.
   - Nota complementar na Seção 3 ("Git Hooks Integration (Non-Interactive)").
2. **Escopo da Orientação Técnica para CI e Automações**:
   - *Injeção em arquivo / Git Hooks:* Orientar explicitamente o uso de `gitpr --commit --hook <caminho-do-arquivo>`, que garante execução 100% não interativa (sem modais) e grava a mensagem diretamente no arquivo temporário do Git.
   - *Scripts e Pipelines CI:* Explicar que em ambientes não interativos (sem TTY, com `--quiet`, ou em pipes), o GitPR não executa o commit e apenas imprime a sugestão no console. Se a intenção for comitar automaticamente em pipelines de PR, o comando correto é `gitpr --no-edit`.
3. **Paridade de Internacionalização (i18n)**:
   - Aplicar a atualização simultaneamente nos 5 idiomas suportados:
     - `docs/commit-message-ia.md` (Inglês - Canônico)
     - `docs/commit-message-ia.pt_br.md` (Português - Brasil)
     - `docs/commit-message-ia.pt_pt.md` (Português - Portugal)
     - `docs/commit-message-ia.es_es.md` (Espanhol)
     - `docs/commit-message-ia.fr_fr.md` (Francês)
4. **Alinhamento com o Modelo de Domínio (`CONTEXT.md`)**:
   - Refinar a definição do termo `Commit flow` em `CONTEXT.md` para especificar que a execução do commit ocorre exclusivamente durante um **Interactive run**, enquanto invocações não interativas recorrem à injeção via hook ou saída no console.

---

## 3. Matriz de Arquivos Afetados

| Arquivo | Mudança | Escopo / Idioma |
|---|---|---|
| `CONTEXT.md` | Refinamento do termo `Commit flow` | Modelo de Domínio |
| `docs/commit-message-ia.md` | Callout de Nota de Migração na Seção 1 e nota na Seção 3 | Inglês (Canônico) |
| `docs/commit-message-ia.pt_br.md` | Callout de Nota de Migração na Seção 1 e nota na Seção 3 | Português (Brasil) |
| `docs/commit-message-ia.pt_pt.md` | Callout de Nota de Migração na Seção 1 e nota na Seção 3 | Português (Portugal) |
| `docs/commit-message-ia.es_es.md` | Callout de Nota de Migração na Seção 1 e nota na Seção 3 | Espanhol |
| `docs/commit-message-ia.fr_fr.md` | Callout de Nota de Migração na Seção 1 e nota na Seção 3 | Francês |
