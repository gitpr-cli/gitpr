## Completion Report — Correção de arquivos de contexto defasados e refs quebradas do HELP_MAP

Correções derivadas da varredura `/reports-to-memory` executada na mesma sessão, que
identificou divergências entre os arquivos auto-carregados de contexto e o código real.

### What was done

- **`HELP_MAP` (2 links quebrados):** `get_doc_url()` apontava para dois arquivos
  inexistentes, gerando URLs de documentação mortas no help contextual:
  - `chat-interativo.md` → `understanding_chat_functionality.md` (o nome correto já era
    usado nas linhas 1117 e 1176 do mesmo arquivo — a entrada do `HELP_MAP` ficou para trás)
  - `metricas_analytics_dashboard.md` → `metricas-telemetria.md`
  - As 15 referências do `HELP_MAP` foram verificadas uma a uma contra `docs/`.
- **`CLAUDE.md` — versão:** `0.0.30` → `0.0.37` (conferido em `src/updater.py`).
- **`CLAUDE.md` — tabela de comandos:** removida a flag `--publish`, que não existe em
  `src/main.py`. O publisher passou a ser o **fluxo padrão**; os modificadores reais são
  `--no-publish` (salva o `.md` sem abrir a TUI), `--no-edit` (auto-commit + POST direto) e
  `--base`. Comportamento confirmado no dispatch em `src/main.py:1435`.
  A tabela foi reconstruída a partir da lista real de `@click.option`, incorporando as
  flags que faltavam: `--chat`, `--install`, `--metrics`/`--dashboard`, `--status`,
  `--plugins`, `--mcp`, `--lang`, `--linter-setup`. A linha do `--provider` passou a citar
  `ollama`.
- **`GEMINI.md` — versão:** `0.0.35` → `0.0.37`.
- **`GEMINI.md` — fluxo padrão:** a linha `*(default)*` descrevia apenas "PR description";
  agora reflete o publisher TUI e ganhou as linhas `--no-publish` / `--no-edit`. O restante
  da tabela do GEMINI.md já estava correto.
- **Memória:** `.claude/memory/claude-md-desatualizado-vs-architecture.md` reescrita — ela
  descrevia exatamente o defeito corrigido aqui e teria virado informação falsa. Mantém a
  lição durável (arquivos auto-carregados derivam em silêncio) e registra a correção.

### Changed files

| File | Change type | Description |
|------|-------------|-------------|
| src/main.py | fix | 2 refs de doc do `HELP_MAP` corrigidas para arquivos existentes |
| CLAUDE.md | docs/fix | Versão 0.0.30 → 0.0.37; tabela de comandos reconstruída (remoção de `--publish`, +9 flags reais) |
| GEMINI.md | docs/fix | Versão 0.0.35 → 0.0.37; linha do fluxo padrão + `--no-publish`/`--no-edit` |
| .claude/memory/claude-md-desatualizado-vs-architecture.md | docs | Memória atualizada pós-correção |
| .claude/memory/MEMORY.md | docs | Linha de índice da memória acima |

### Impact

- **Functionality:** `gitpr -h --chat` e `gitpr -h --metrics` passam a exibir links de
  documentação válidos (antes: 404). Nenhuma outra mudança de comportamento — as demais
  alterações são de arquivos de contexto, não de runtime.
- **Performance:** Nenhum impacto.
- **Compatibility:** Sem quebras de API. Nenhuma flag, chave i18n ou assinatura alterada;
  as duas strings trocadas são nomes de arquivo passados a `get_doc_url()`.

### Verification

- `python -c "from src.main import cli"` → import OK.
- Todas as 15 refs de `get_doc_url()` em `src/main.py` resolvem para arquivos reais em
  `docs/` (verificado por script).
- `python run.py -h --chat` → `.../docs/understanding_chat_functionality?lang=pt_br`.
- `python run.py -h --metrics` → `.../docs/metricas-telemetria?lang=pt_br`.
- `python -m pytest tests/ -q` → **269 passed, 2 failed**.

**Sobre as 2 falhas:** `tests/test_i18n.py::test_key_parity_and_count` e
`::test_identity_keys_with_braces_allowlist` falham com `638 != 547`. São **pré-existentes**
e não relacionadas a esta tarefa — confirmado via `git stash push src/main.py CLAUDE.md
GEMINI.md` seguido de re-execução, que reproduz as mesmas 2 falhas sem as minhas mudanças.
A causa é o trabalho de i18n ainda não commitado na árvore (`langs/*.json` modificados,
638 chaves) contra a contagem de 547 que o teste ainda espera.

### Next steps (if applicable)

- Atualizar a contagem esperada em `tests/test_i18n.py` (547 → 638) e a allowlist de
  identity keys como parte do trabalho de i18n em andamento — é o que destrava a suíte.
- O bump de `__lang_version__` correspondente às novas chaves deve seguir a regra de
  [[langs-ota-stale-race]]: subir os `langs/*.json` ao `main` **antes** do bump do marcador.
