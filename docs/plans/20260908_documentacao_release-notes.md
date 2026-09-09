# Plano — Next Steps da família `release-notes`: ajuda contextual, i18n (48 chaves) e índice do README

## Contexto

A tarefa de documentação da feature **GitPR Automated Changelog / Release Notes** (família `docs/release-notes.md` ×5, concluída em 2026-09-08) deixou 3 next steps opcionais no relatório `docs/claude-code/reports/develop_natan/2026-09-08_documentacao_release_notes.md` — o usuário pediu para aplicá-los (exceto "revisão/commit do usuário", que é ação do próprio usuário pela regra de nunca commitar):

1. **Roteamento da ajuda contextual** `gitpr release -h` → `get_doc_url("release-notes.md")`.
2. **Tradução das chaves i18n pendentes** do fluxo de release nos 6 arquivos `langs/*.json`.
3. **Registro da família no índice** do README (master + 4 cópias traduzidas).

Estado verificado por sondagem direta: cada `langs/*.json` tem 694 chaves, conjuntos idênticos, **0 órfãs** hoje; **exatamente 40 chaves visíveis ao extrator AST** (`__("literal")` em `src/` + `run.py`) estão ausentes dos 6 arquivos → `test_no_missing_keys` está vermelho na árvore. As 40: 17 da região do subcomando em `src/main.py` (help strings das opções + mensagens de UI), 21 de `src/release_engine.py` (incl. 2 prompts de IA terminando em `\n` literal com placeholders `{json_format}`/`{language}` e a persona "You are a Release Manager..."), 2 de `src/changelog_builder.py` (`'Summary'` L167, `'Contributors'` L182 — chamadas literais).

Fatos mecânicos: `core.autocrlf=true`, sem `.gitattributes`; os 6 JSONs são 100% CRLF no worktree (`i/lf w/crlf`) — a escrita deve preservar CRLF; `es.json`×`es_es.json` e `fr.json`×`fr_fr.json` são pares quase idênticos (5 e 2 valores divergentes) → 1 tradução por par; os testes de release prendem `en_us` no `setUpClass` **após** o import dos módulos (máquina dev pode ser pt_br) → qualquer tradução em tempo de import quebraria as asserções EN em máquinas não-EN.

## Decisões

1. **Escopo do README: só release-notes** (decisão do usuário) — suggested-reviewers e scm-multiforge continuam fora do índice; anotar como dívida no relatório final.
2. **Grupo do índice: Core Features, no fim do grupo** (decisão do usuário) — nova bullet imediatamente após a de skill-template (linha 435 nas 5 cópias), antes do `### Configuration & Infrastructure` (437).
3. **Mecanismo de ajuda contextual:** `HELP_MAP` não dispara para subcomandos (casamento por locals da raiz, main.py:541-542, early-return) → **`epilog=` no decorator Click** do subcomando (main.py:1607-1609), reutilizando a chave existente `__(">> Full documentation:")` (usada em main.py:575; presente e traduzida nas 6) + `get_doc_url("release-notes.md")` (src/core.py:455-469; já importado em main.py:33). Forma exata validada (click 8.3.3, sem outro epilog no repo):
   ```python
   @cli.command(
       context_settings={"help_option_names": ["-h", "--help"]},
       epilog=__(">> Full documentation:") + " " + get_doc_url("release-notes.md"),
   )
   ```
   Freeze no import é o padrão de todas as help strings do arquivo → consistente. Nenhum teste atual asserta o help de `release`; o único teste de root-help existente (test_main_suggest_reviewers.py:103) não quebra.
4. **Os 8 headings do changelog viram traduzíveis** (decisão do usuário): hoje `_SECTION_META` (changelog_builder.py:81-89, 7 entradas) e `_BREAKING_HEADING` (:91) são consumidos dinamicamente em `__(...)` nas linhas 142 e 170 — invisíveis ao extrator AST do `test_i18n.py` (exige `ast.Constant` como 1º argumento); adicioná-los aos JSONs sem mudança de código criaria 8 órfãs → `test_no_orphan_keys` vermelho. Grep validou: **nenhuma referência externa** a `_SECTION_META`/`_BREAKING_HEADING` (só em changelog_builder.py); `_SECTION_ORDER` (71-79) é usado na L175 e **fica**. Correção: remover as 2 constantes e adicionar **helper de tempo de execução** `_category_heading(category)` com dict literal de 7 chamadas `__("✨ Features")` … `__("📦 Other Changes")` no corpo (chamado na L142) + literal direto `__("⚠️ Breaking Changes")` na L170 (BREAKING **não** entra no helper — não pertence a `_SECTION_META`/`_SECTION_ORDER`; `ChangeCategory.BREAKING` existe e é usado só em version_bump.py). Chamadas literais → AST-visíveis (ast.walk cobre aninhadas); resolução em runtime → segue `set_lang` dos testes (EN pinado no `setUpClass`; `set_lang("en*")` → `{}` → fallback na chave EN) e o `--lang` em execução. Aritmética pós-mudança: AST 734 → 742; langs 694 → 742 — os dois gates só passam quando código e JSONs chegam juntos (árvore hoje intencionalmente vermelha em `test_no_missing_keys`).
5. **Traduções genuínas (nunca identidade)** nas 6 cópias, preservando `{placeholders}` verbatim e o `\n` final das 2 chaves de prompt de IA (o `\n` é caractere real no código — release_engine.py:183/257; a entrada JSON termina com o escape `\n`; remover o `\n` mudaria o prompt e a chave de cache). **Não** mesclar com as chaves-irmãs existentes que compartilham o prefixo "Generate ONLY a JSON object in the format {json_format}" (issue_engine.py:216, core.py:787) — as 2 novas são strings completas distintas. A persona de release é traduzida nas 6 e **não** entra no allowlist `AI_PROMPT_PREFIXES` (identidade com `{` só é permitida sob esse allowlist; sem `{`, nenhum teste exige identidade — QA manual de cada valor). Nota: não há teste de count fixo (floor é >500), e `CLEAN_KEYS` (50, de scripts/fix_mangled_i18n_keys.py) não intersecta as novas chaves.
6. **Escrita dos JSONs:** driver Python único via heredoc (ou arquivo temporário **fora do repo**, nunca commitado): `json.load` → `dict.update` com as 48 chaves numa **lista fixa única** (append ao final, mesma ordem nos 6 arquivos — paridade de cauda hoje exata; ordem de inserção preservada pelo `json.load`) → `json.dumps(indent=2, ensure_ascii=False)` → conversão `\n`→`\r\n` (escrita com `newline=""`). Round-trip byte-exato validado: `raw == (json.dumps(json.loads(raw), indent=2, ensure_ascii=False) + "\n").replace("\n","\r\n")` é True para os 6 hoje → diff de exatamente +48 linhas por arquivo, nada mais. Resultado: 742 chaves por arquivo; verificar idempotência (2ª passada byte-idêntica) e ausência de escapes `\u`.
7. **Bump do cache de idiomas:** `__lang_version__` em src/updater.py:13 de "v0.0.22" → "v0.0.23" (já é mudança não commitada; necessário para as cópias OTA em `~/.gitpr/langs` re-baixarem com as 48 chaves).
8. **Teste novo** em tests/test_release_cli.py: `class TestReleaseHelp(ReleaseCliTestCase)` (subclasse herda o pin/restore de en_us da base na linha 46) com `runner.invoke(cli, ["release", "-h"])` → `exit_code == 0` e `"release-notes" in result.output` (fragmento de URL é locale-independent — em máquina pt_br o epilog congela no import a partir da cópia OTA de `~/.gitpr/langs`, possivelmente com 694 chaves; **não** assertar label EN). Import do módulo pode fazer um fetch OTA limitado (~3 s) quando `LANG_VERSION` difere — inofensivo.
9. **Nada staged/commitado** (regra do projeto); plano datado em `docs/plans/` + relatório final obrigatório (template CLAUDE.md) em `docs/claude-code/reports/develop_natan/`.

## Entregáveis

| Arquivo                                         | Tipo     | Descrição                                                                                                                         |
| ----------------------------------------------- | -------- | --------------------------------------------------------------------------------------------------------------------------------- |
| `src/main.py`                                   | feat     | `epilog=` no decorator de `release` (~1607-1609) apontando `get_doc_url("release-notes.md")`                                      |
| `src/changelog_builder.py`                      | refactor | Helper de headings com 7 chamadas `__("literal")` + literal de Breaking; remove `_SECTION_META`/`_BREAKING_HEADING`               |
| `langs/{pt_br,pt_pt,es_es,fr_fr,es,fr}.json` ×6 | feat     | +48 chaves traduzidas cada (→ 742), CRLF preservado, append no fim                                                                |
| `src/updater.py`                                | chore    | `__lang_version__` v0.0.22 → v0.0.23                                                                                              |
| `README.md` + 4 cópias                          | docs     | 1 bullet no fim do grupo Core Features (título/descrição traduzidos, link `.../docs/release-notes.md` no padrão das linhas irmãs) |

Bullet sugerido (EN, inserido entre as linhas 435 e 436; título sem prefixo "Technical Documentation", descrição com `gitpr release` em backticks como nas linhas irmãs):

```markdown
* [**Release Notes & Changelog (gitpr release)**](https://github.com/gitpr-cli/gitpr.git/blob/main/docs/release-notes.md) — How the `gitpr release` subcommand generates the changelog / release notes of a repository, suggests the next semantic version and publishes releases on the forge.
```

Traduções espelhando o vocabulário dos H1 de `docs/release-notes.*.md`: pt_br/pt_pt "Notas de Versão e Changelog (gitpr release)", es_es "Notas de la Versión y Changelog (gitpr release)", fr_fr "Notes de version et changelog (gitpr release)" + descrição correspondente em cada idioma.
| `tests/test_release_cli.py` | test | 1 teste de help com epilog |
| `docs/plans/20260908_release_notes_next_steps.md` | docs | Este plano (PT-BR) |
| `docs/claude-code/reports/develop_natan/2026-09-08_release_notes_next_steps.md` | docs | Relatório final (template CLAUDE.md) |

## Vocabulário de tradução (âncoras)

Reutilizar traduções existentes nos próprios `langs/*.json` para conceitos já mapeados (ex.: "summary" → formas de "Resumo/Resumen/Résumé" já usadas; "Contributors" → termo já usado em chaves irmãs se houver) e seguir o glossário das docs `release-notes.*.md` ("notas de versão"/"notes de la versión"/"notes de version", "borrador"/"brouillon", "forge", etc.). Cada par regional (es×es_es, fr×fr_fr) recebe o mesmo valor onde não houver variação natural; variar só onde o par já diverge ("nuevamente"×"de nuevo", "Timeout de la API"×"Timeout API").

## Etapas

Ambiente: `python -m pytest` (Python global 3.13, pytest 9.1.1 — **não** usar `pipenv run`). Nada de `git add/commit/push`. Ordem validada:

1. **`src/changelog_builder.py`**: remover `_SECTION_META` (81-89) e `_BREAKING_HEADING` (91); adicionar `_category_heading(category)` (dict literal de 7 chamadas `__("...")` no corpo, retorno `headings[category]`); L142 → `heading = _category_heading(category)`; L170 → `f"### {__('⚠️ Breaking Changes')}"`. Manter `_SECTION_ORDER` (71-79) e o import de `__` (L18). Verificar AST: snippet `ast.walk` sobre o arquivo deve listar exatamente 10 chaves (`Summary`, `Contributors`, 8 headings).
2. **`src/main.py`**: `epilog=__(">> Full documentation:") + " " + get_doc_url("release-notes.md"),` no `@cli.command(...)` (1607-1609). Smoke: `CliRunner().invoke(cli, ["release", "-h"])` → exit 0 e `"release-notes"` no output.
3. **`src/updater.py`**: `__lang_version__` "v0.0.22" → "v0.0.23" (L13; manter acima do import de i18n).
4. **`tests/test_release_cli.py`**: classe `TestReleaseHelp(ReleaseCliTestCase)` com o teste descrito na Decisão 8.
5. **Driver dos JSONs** (heredoc do repo root, script nunca salvo no repo): reextrair as 40 chaves ausentes por AST (`src/` + `run.py` vs. langs) + 8 headings em lista fixa; append nas 6; CRLF. Verificações por arquivo: 694 → 742; round-trip byte-exato (`raw == (json.dumps(json.loads(raw), indent=2, ensure_ascii=False) + "\n").replace("\n","\r\n")`); 2ª passada byte-idêntica (idempotência); `git diff --stat langs/` = +48 por arquivo, só adições na cauda; fim de arquivo `}\r\n` (743 × `\r\n`); sem escapes `\u`.
6. **README × 5**: inserir a bullet após a linha 435 (antes da 437) em README.md/pt_br/pt_pt/es_es/fr_fr. Verificar: `grep -n "release-notes.md" README*.md` → 5 hits na linha 436.
7. **Suíte** (nessa ordem): `python -m pytest tests/test_i18n.py -q` (gate: paridade 742×6, no-missing, no-orphan, identidade) → `python -m pytest tests/test_release_cli.py tests/test_changelog_builder.py tests/test_release_engine.py tests/test_skill_command.py tests/scm/test_release_publish.py -q` → suíte completa `python -m pytest tests/ -q`. Falhas em máquina pt_br seriam exatamente a classe de bug que o desenho evita — sinalizar qualquer uma inesperada.
8. **Docs**: `docs/plans/20260908_release_notes_next_steps.md` (PT-BR) + relatório final em `docs/claude-code/reports/develop_natan/2026-09-08_release_notes_next_steps.md` (template CLAUDE.md), com a nota de que `sync_i18n.py` foi deliberadamente **não** executado e de que as cópias OTA em `~/.gitpr/langs/` só renovam depois que o bump chegar ao `main` (as gates validam os JSONs do repo — esperado). Conferir `git status --short` final: 6 JSONs + 5 READMEs + src/main.py + src/changelog_builder.py + src/updater.py + tests/test_release_cli.py + 2 docs; nada staged.

## Verificação

- Gates i18n verdes (item 7 acima) — os dois testes de missing/orphan só passam juntos após código + JSONs (aritmética 734+8 = 742 = 694+48).
- `git diff langs/pt_br.json` = somente adições na cauda (sem ruído de EOL, sem reordenação); idempotência byte-exata do driver na 2ª passada.
- Smoke do epilog via CliRunner (novo teste): `gitpr release -h` termina com a linha do epilog contendo `release-notes`.
- Suíte completa verde com `python -m pytest` global (sem pipenv).
- `git status`: somente os arquivos previstos; nada staged/commitado.

## Observações (fora de escopo, mas documentadas no relatório)

- `tests/sync_i18n.py` **nunca** é executado: reordenaria os 6 arquivos (diff cosmético gigante), reescreveria LF e, se rodado antes das traduções, auto-inseriria valores identidade — várias das 40 chaves têm `{braces}` e falhariam `test_identity_keys_with_braces_allowlist` por nome. Ferramenta de scaffold apenas.
- OTA: o fetch de `langs/*.json` é da branch `main` de `natanfiuza/gitpr` → o bump `v0.0.23` só renova cópias locais quando publicado; comportamento normal (não é falha das gates).
- Quirk pré-existente (não corrigir nesta tarefa): `src/release_engine.py:40` importa `CURRENT_LANG` por valor; `set_lang()` só religa o global do módulo i18n → `_language_for_prompt()` pode usar o locale do import após os testes prenderem en_us. Afeta só o valor `{language}` dentro do texto de prompt de IA (nunca assertado).
- Linhas do README para suggested-reviewers e scm-multiforge: dívida anotada no relatório final.
- Revisão/commit do usuário (ação do usuário); documentos `docs/release-notes.*` e artefatos da feature (ADRs, glossário, spec, surveys) intocados; sem ADR novo.
