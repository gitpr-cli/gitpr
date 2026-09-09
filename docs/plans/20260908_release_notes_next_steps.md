# Plano — Next Steps da família `release-notes`: ajuda contextual, i18n (48 chaves) e índice do README

> Estado: **implementado em 2026-09-08** (aprovado via ExitPlanMode). Este documento registra o plano aprovado e os refinamentos aplicados na implementação.

## Contexto

A tarefa de documentação da feature **GitPR Automated Changelog / Release Notes** (família `docs/release-notes.md` ×5) deixou next steps no relatório `docs/claude-code/reports/develop_natan/2026-09-08_documentacao_release_notes.md` — aplicados aqui (exceto "revisão/commit do usuário", que é ação do próprio usuário pela regra de nunca commitar):

1. **Roteamento da ajuda contextual** `gitpr release -h` → `get_doc_url("release-notes.md")`.
2. **Tradução das chaves i18n pendentes** do fluxo de release nos 6 arquivos `langs/*.json`.
3. **Registro da família no índice** do README (master + 4 cópias traduzidas).

Estado inicial verificado por sondagem: cada `langs/*.json` tinha 694 chaves com conjuntos idênticos e 0 órfãs; o subcomando de release e o classificador de changelog expunham ao extrator AST (test_i18n.py) **40 chaves ausentes** (`src/main.py` 17 help strings + mensagens de UI; `src/release_engine.py` 21, incl. 2 prompts de IA terminando em `\n` real com placeholders `{json_format}`/`{language}` e a persona "You are a Release Manager..."; `src/changelog_builder.py` 2 — `'Summary'` e `'Contributors'`). Com a Decisão 4 abaixo, os **8 headings** de seção também entraram no escopo → **48 chaves × 6 idiomas**.

Fatos mecânicos: `core.autocrlf=true`, sem `.gitattributes`; os 6 JSONs são 100% CRLF no worktree — escrita deve preservar CRLF; `es.json`×`es_es.json` e `fr.json`×`fr_fr.json` são pares quase idênticos (5 e 2 valores divergentes) → 1 tradução por par; os testes de release prendem `en_us` no `setUpClass` **após** o import dos módulos → traduções de heading resolvidas em runtime (helper), nunca no import.

## Decisões (aprovadas pelo usuário)

1. **Escopo do README: só release-notes** — suggested-reviewers e scm-multiforge continuam fora do índice; anotado como dívida no relatório final.
2. **Grupo do índice: Core Features, no fim do grupo** — nova bullet imediatamente após a de skill-template (linha 435), na 436, antes do `### Configuration & Infrastructure` (437).
3. **Mecanismo de ajuda contextual:** `HELP_MAP` não dispara para subcomandos (casamento por locals da raiz) → **`epilog=` no decorator Click** do subcomando `release`, reutilizando a chave existente `__(">> Full documentation:")` + `get_doc_url("release-notes.md")`.
4. **Os 8 headings do changelog viram traduzíveis:** `_SECTION_META`/`_BREAKING_HEADING` removidos; novo helper de runtime `_category_heading(category)` com 7 chamadas literais `__("✨ Features")` … `__("📦 Other Changes")` + literal direto de `__("⚠️ Breaking Changes")` na renderização. Chamadas literais → AST-visíveis; resolução em runtime → segue `set_lang`/`--lang`. `_SECTION_ORDER` fica.
5. **Traduções genuínas (nunca identidade)** nos 6 arquivos, preservando `{placeholders}` verbatim e o `\n` final das 2 chaves de prompt de IA; `Conventional Commits`, `OTHER`, `Map-Reduce`, `forge`, `release` e a persona `Release Manager` mantidos como empréstimos (a persona como título, seguindo o precedente de "Tech Lead"; a frase ao redor é traduzida). A persona **não** entra no allowlist `AI_PROMPT_PREFIXES`.
6. **Escrita dos JSONs:** driver Python único em diretório temporário **fora do repo** (nunca commitado): `json.load` → `dict.update` com as 48 chaves em lista única ordenada (append ao final, mesma ordem nos 6 arquivos) → `json.dumps(indent=2, ensure_ascii=False)` → conversão `\n`→`\r\n`, escrita com `newline=""`. Leituras também com `newline=""` (a tradução universal de novas linhas do modo texto mascararia o CRLF). Resultado: 742 chaves por arquivo, diff de +48 linhas na cauda, idempotência byte-exata.
7. **Bump do cache de idiomas:** `__lang_version__` em `src/updater.py` de "v0.0.22" → "v0.0.23" (renova as cópias OTA de `~/.gitpr/langs` quando chegar ao `main`).
8. **Teste novo** em `tests/test_release_cli.py`: `TestReleaseHelp(ReleaseCliTestCase)` — `runner.invoke(cli, ["release", "-h"])` → `exit_code == 0` e `"release-notes" in result.output` (fragmento de URL é locale-independent; o epilog congela no import sob o locale da máquina).

## Refinamento da Decisão 3 na implementação (sobre o plano original)

O plano previa `epilog=__(">> Full documentation:") + " " + get_doc_url(...)` numa única linha. Na validação com Click 8.3.3, o `HelpFormatter` **reembrulha** o epilog (largura ≤ 78 sob o CliRunner): com o rótulo pt_br + sufixo `?lang=pt_br`, a URL longa era quebrada no meio da palavra (`release-\nnotes`) e o teste falhava. A forma final usa o parágrafo `\b` do Click (marcador de bloco verbatim, sem rewrap):

```python
epilog="\b\n"
+ __(">> Full documentation:")
+ "\n"
+ get_doc_url("release-notes.md"),
```

Espelha a ajuda raiz (linha de rótulo verde + linha de URL) e é determinística entre locales — a URL renderiza íntegra em qualquer idioma.

## Entregáveis

| Arquivo | Tipo | Descrição |
|---------|------|-----------|
| `src/main.py` | feat | `epilog=` no decorator de `release` (parágrafo `\b`) apontando `get_doc_url("release-notes.md")` |
| `src/changelog_builder.py` | refactor | Helper `_category_heading(category)` com 7 chamadas `__("literal")` + literal de Breaking; remove `_SECTION_META`/`_BREAKING_HEADING` |
| `langs/{pt_br,pt_pt,es_es,fr_fr,es,fr}.json` ×6 | feat | +48 chaves traduzidas cada (694 → 742), CRLF preservado, append no fim |
| `src/updater.py` | chore | `__lang_version__` v0.0.22 → v0.0.23 |
| `README.md` + 4 cópias | docs | 1 bullet na linha 436 (fim do grupo Core Features); título/descrição traduzidos; link `.../docs/release-notes.md` nas 5 |
| `tests/test_release_cli.py` | test | `TestReleaseHelp` (exit 0 + fragmento `release-notes` no output) |
| `docs/plans/20260908_release_notes_next_steps.md` | docs | Este plano (PT-BR) |
| `docs/claude-code/reports/develop_natan/2026-09-08_release_notes_next_steps.md` | docs | Relatório final (template CLAUDE.md) |

## Etapas executadas

1. `src/changelog_builder.py`: helper de headings em runtime (8 literais AST-visíveis; AST 734 → 742).
2. `src/main.py`: `epilog` com parágrafo `\b` no `@cli.command(...)` do subcomando `release`.
3. `src/updater.py`: `__lang_version__` → "v0.0.23" (acima do import de i18n).
4. `tests/test_release_cli.py`: `TestReleaseHelp` — 4 passed.
5. Driver dos JSONs (fora do repo): reextração por AST conferida contra as 48 chaves; append nas 6 com CRLF; verificação por arquivo: 694 → 742, round-trip byte-exato, idempotência na releitura pós-escrita, fim `}\r\n`, sem escapes `\u`.
6. README × 5: bullet na linha 436 em todas as cópias (`grep -n "release-notes.md" README*.md` → 5 hits).
7. Suíte: `tests/test_i18n.py` 20 passed (gate 742×6, no-missing, no-orphan, identidade); subsets de release 64 passed; suíte completa 783 passed / 6 failed / 2 skipped — as 6 falhas são ambientais pré-existentes (4 de locale pt_br da máquina nas chaves OTA; 2 de `GITPR_AI_TIMEOUT=180` no `~/.gitpr/.env` do usuário), em caminhos intocados por esta tarefa (verificadas: 4 passam com `GITPR_LANG=en_us`).
8. Docs: este plano + relatório final.

## Verificação

- Gates i18n verdes — os dois testes de missing/orphan só passam juntos após código + JSONs (aritmética 734+8 = 742 = 694+48).
- `git diff langs/pt_br.json` = somente adições na cauda (+48 sobre as +7 pendentes pré-existentes da mesma família), sem ruído de EOL nem reordenação; idempotência byte-exata conferida dentro do driver.
- Smoke do epilog via CliRunner (novo teste): `gitpr release -h` termina com a linha do epilog contendo `release-notes`.
- `git status`: somente os arquivos previstos; nada staged/commitado.

## Observações (fora de escopo, documentadas no relatório)

- `tests/sync_i18n.py` **nunca** é executado: reordenaria os 6 arquivos (diff cosmético gigante), reescreveria LF e auto-inseriria valores identidade.
- OTA: o fetch de `langs/*.json` vem da branch `main` → o bump `v0.0.23` só renova as cópias locais quando publicado; comportamento normal (não é falha das gates).
- Quirk pré-existente (não corrigido): `src/release_engine.py` importa `CURRENT_LANG` por valor; `set_lang()` só religa o global do módulo i18n → `_language_for_prompt()` pode usar o locale do import nos testes. Afeta só o valor `{language}` dentro do prompt de IA (nunca assertado).
- Linhas do README para suggested-reviewers e scm-multiforge: dívida anotada no relatório final.
- Revisão/commit do usuário (ação do usuário); documentos `docs/release-notes.*` e artefatos da feature (ADRs, glossário, spec, surveys) intocados; sem ADR novo.
