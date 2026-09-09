# Plano — Documentação GitPR Release Notes / Changelog (família `release-notes.md`, 5 idiomas)

## Contexto

A funcionalidade **GitPR Automated Changelog / Release Notes** (`gitpr release` — o primeiro subcomando da CLI) foi implementada em 2026-09-07 e registrada nos artefatos internos de `docs/plans/` (spec `20260904_skill_gitpr_release_notes_spec.md`, `ADR-002-gitpr-release-subcommand.md` — Aceito —, `ADR-003-gitpr-release-flat-modules.md` — Aceito —, `glossary-release-notes.md`), nos relatórios `docs/claude-code/reports/develop_natan/2026-09-07_gitpr_release_feature.md`, `2026-09-07_gitpr_release_notes_grill.md` e `2026-09-08_skill_release_template.md`, e nos surveys de `docs/survey/` (`20260907_gitpr_release_notes_surveyfacts.md`, `20260908_skill_release_template_surveyfacts.md`). O código da feature (`src/changelog_builder.py`, `src/commit_classifier.py`, `src/release_engine.py`, `src/version_bump.py` e o subcomando em `src/main.py`) também segue na árvore de trabalho — nada foi commitado ainda.

Faltava a **documentação técnica de usuário em `docs/`**: o projeto mantém 31 famílias de documentos, cada uma em 5 cópias (master inglês sem sufixo + `.pt_br.md`, `.pt_pt.md`, `.es_es.md`, `.fr_fr.md`, com paridade linha a linha — ex.: `suggested-reviewers.md` tem 107 linhas em todas as cópias). A feature de release não possuía família própria e, diferentemente do precedente suggested-reviewers, nenhum código fixa o nome: o subcomando `gitpr release` ainda não tem entrada no `HELP_MAP`/`get_doc_url` (`src/main.py`).

## Decisões (aprovadas no grilling)

1. **Nome do arquivo:** família `release-notes.md` — escolha do usuário em AskUserQuestion (não imposta por código); reflete o vocabulário da própria feature ("release notes").
2. **Escopo/audiência:** documento de referência orientado ao usuário (fluxo padrão, opções, sugestão de versão, estrutura do changelog, resumo de IA, publicação na forge, modo JSON/idempotência, env vars) — **sem** seção "For Developers and Plugins" (diferente de `suggested-reviewers.md`): os módulos flat da feature já estão descritos em ADR-003/glossário, e o documento cruza `skill-template.md`, `providers-ia.md` e `scm-multiforge.md` onde o usuário precisar deles.
3. **Anti-overclaim verificado por leitura do código** (`src/main.py` região do subcomando ~1594-1851, `src/config.py`, `src/changelog_builder.py`, `src/commit_classifier.py`): sem TUI interativo de preview em v1 (só print de terminal ≤ 40 linhas com `… and N more lines`), sem range entre duas tags (`--since A --until B` fora de escopo), sem config YAML / `commit_types` custom, sem regra específica para `revert:`, sem traduções inventadas — strings de UI citadas apenas verbatim em EN (os headings do changelog e as mensagens do fluxo passam pelo `__()` com fallback em inglês).
4. **Índices:** somente os 5 arquivos do documento em `docs/` — sem alterar README.md, CLAUDE.md ou docs/ARCHITECTURE.md (convenção das famílias irmãs).
5. **Artefatos:** plano datado em `docs/plans/` + relatório final obrigatório (CLAUDE.md). ADRs/glossário/spec/surveys/relatórios-fonte permanecem inalterados; nenhum ADR novo (sem decisão difícil de reverter).

## Entregáveis (7 arquivos novos)

| Arquivo | Idioma | Finalidade |
|---------|--------|------------|
| `docs/release-notes.md` | Inglês | Master (230 linhas) |
| `docs/release-notes.pt_br.md` | PT-BR | Tradução (230 linhas) |
| `docs/release-notes.pt_pt.md` | PT-PT | Tradução europeia autêntica (230 linhas) |
| `docs/release-notes.es_es.md` | Espanhol | Tradução (230 linhas) |
| `docs/release-notes.fr_fr.md` | Francês | Tradução (230 linhas) |
| `docs/plans/20260908_documentacao_release_notes.md` | PT-BR | Este plano |
| `docs/claude-code/reports/develop_natan/2026-09-08_documentacao_release_notes.md` | Inglês | Relatório final (template CLAUDE.md) |

## Estrutura do documento (master EN)

Convenções de `docs/code-review-ia.md`: H1 `# Technical Documentation: Release Notes & Changelog (gitpr release)`, parágrafo de intro sem heading, seções numeradas `## N.`/`### N.N` com separadores `---` só entre H2, tabelas Markdown (2-3 colunas, primeira célula em **bold**), blocos fenced ```bash / ```markdown, nota final em blockquote com cross-link. Sem TOC, sem seção de referências, sem rodapé de data/autor/licença.

1. **Overview** — primeiro subcomando da CLI (raiz virou `click.group`; flags legadas inalteradas); fluxo padrão local: coleta do range → classificação → sugestão de versão → seção (IA opcional) → `CHANGELOG.md` → artefato por execução → preview no terminal ≤ 40 linhas; seção existente aborta (exit 1). **1.1 Command Reference** — tabela das 6 opções com os help strings verbatim do CLI e tabela de características do fluxo padrão (fonte: `since..HEAD` sem merges; IA automática; arquivos escritos; nada publicado; tags/arquivos de versão nunca tocados).
2. **Release Range and Version Suggestion** — 2.1 Commit Range (`--since <tag>`): origem padrão = última tag alcançável (`git describe --tags --abbrev=0`), sem tag = primeira release (range desde o primeiro commit), merges excluídos, fim sempre `HEAD`; 2.2 Semantic Version Suggestion: regras MAJOR/MINOR/PATCH (breaking → MAJOR; ≥ 1 feat → MINOR; só fixes/outros → PATCH; sem tag semver anterior → nenhuma sugestão, `--version` obrigatório para publicar), read-only (tags git apenas, `pyproject.toml` nunca lido), prefixo `v` preservado, prompt `❓ Use the suggested version {version}?` (quando ocorre e quando é pulado); 2.3 Explicit Version (`--version <x.y.z>`): única fonte da tag publicada, `v` opcional.
3. **Changelog Structure and Files** — 3.1 Commit Classification: tabela das 8 categorias (BREAKING/FEATURE/FIX/PERFORMANCE/DOCS/REFACTOR/CHORE/OTHER → headings com emoji), não-conformes → OTHER + aviso (nunca falha), dedupe de PR `(#123)`, breaking só no bloco Breaking, ordem fixa dos blocos, títulos via `__()` (idioma da interface, EN como fallback); 3.2 Version Section Anatomy: anatomia `## [x.y.z] - date` + `### Summary` + blocos + `**Contributors:**`, bullets `subject (short hash)` com scope quando presente, exemplo markdown realista (byte-idêntico nas 5 cópias = saída real do builder), prefixo ao `CHANGELOG.md` (nunca reescrito de raiz); 3.3 Files Written: tabela `CHANGELOG.md` (raiz, exceção deliberada à convenção `.gitpr/reports/`, override por env) / artefato `.gitpr/reports/release/{branch}_{datetime}_RELEASE.md` (best-effort) / preview de terminal.
4. **AI Executive Summary** — 4.1 First-Run Skill Template (`.gitpr.release.md`): auto-download no primeiro run em modo markdown (só camada CLI), language-aware, nunca sobrescreve, nunca falha em erro de rede, pulado em `--format json`, usado como system instruction (persona **Release Manager**, contrato JSON estrito), editável; 4.2 Generation and Graceful Degradation: Map-Reduce em lotes de 200 commits (`📦 Large commit range detected!`), cache MD5 padrão (indexado pelo prompt — editar a skill não invalida o cache, fato documentado), degradação sem chave/falha → `AI summary failed: changelog generated without a summary.` e segue só com listas; `GITPR_RELEASE_AI_SUMMARY=false` desliga; cross-links `skill-template.md` e `providers-ia.md`.
5. **Publishing to the Forge** — 5.1 Confirmation and Guardrails (`--publish`): confirmação explícita `❓ Publish release {version} on {provider}?` (default No → `⏭️ Publication skipped — the changelog was generated locally.`), corpo da release = seção sem o heading `## [x.y.z] - date`, guardas sem remote `origin` (exit 1), `--publish` + `--format json` só avisa, hint pós-local `ℹ️ To publish this release on the forge, run again with --publish.`; 5.2 Supported Forges: tabela GitHub (tag auto-criada na branch padrão do repo, drafts honrados) / GitLab (tag pré-existente, sem drafts) / Bitbucket Cloud e Azure DevOps (sem API de release → `⚠️ Release publishing is not supported...` e fluxo local completa); cross-link `scm-multiforge.md`; 5.3 Drafts (`--draft`): só com `--publish`, GitHub default draft (`GITPR_RELEASE_PUBLISH_DRAFT_BY_DEFAULT=true`).
6. **JSON Mode and Idempotency** — 6.1 Pure JSON Output (`--format json`): stdout-only (nada escrito, nada publicado, nunca pergunta, sem auto-download), payload completo listado campo a campo; 6.2 Existing Section and `--force`: seção existente → aborta exit 1 sem tocar o arquivo (nunca duplica/sobrescreve em silêncio); `--force` regenera (`🔄 Existing section for version {version} regenerated.`).
7. **Environment Variables** — tabela das 5 chaves com defaults verbatim de `src/config.py`: `GITPR_RELEASE_CHANGELOG_PATH` (`CHANGELOG.md`), `GITPR_RELEASE_AI_SUMMARY` (`true`), `GITPR_RELEASE_AUTO_BUMP` (`true`), `GITPR_RELEASE_PUBLISH_DRAFT_BY_DEFAULT` (`true`), `OUTPUT_FILE_NAME_RELEASE` (`{branch}_{datetime}_RELEASE.md`); convenção booleana "false desliga" e arquivo `~/.gitpr/.env`.

Footer: `> **Note:** See also the [Skills and Templates documentation](skill-template.md) ...`

## Etapas

1. Verificações de fidelidade por leitura direta: `src/main.py` (docstring + help strings verbatim das 6 opções + mensagens de UI reais + `_preview_release` 40 linhas + `effective_draft`), `src/config.py` (defaults exatos das 5 env vars), `src/changelog_builder.py` (headings/ordem/emoji exatos, bullets com subject limpo, `**Contributors:**`), `src/commit_classifier.py`; exemplos de estilo `docs/code-review-ia.md` + `docs/code-review-ia.pt_br.md` e precedentes `docs/plans/20260907_documentacao_suggested_reviewers.md` + relatório irmão.
2. Escrever `docs/release-notes.md` (master EN, 230 linhas).
3. Escrever as 4 traduções com paridade linha a linha (230 linhas cada): pt_br e pt_pt ("release notes" → notas de versão; "default" → padrão / por omissão; "file" → arquivo / ficheiro; "section" → seção / secção), es ("archivo", "por defecto", "borrador", "rama por defecto"), fr ("fichier", "par défaut", "brouillon", tipografia " : "); comentários de code block bash traduzidos; tokens técnicos, cross-links sem sufixo e o sample markdown byte-idênticos ao master.
4. Escrever este plano (PT-BR, estilo do plano irmão).
5. Escrever o relatório final conforme template obrigatório do CLAUDE.md.
6. Nenhum commit: árvore de trabalho intacta para revisão do usuário.

## Verificação

- Paridade: `wc -l` idêntico (230) nas 5 cópias; headings reais (`grep '^#'`) nas mesmas linhas em todas as cópias (H1 na 1; H2 em 7, 40, 86, 140, 161, 197, 218); blocos fenced idênticos entre master e cópias exceto os comentários bash traduzidos; sample markdown byte-idêntico.
- Fidelidade técnica: opções da tabela 1.1 == help strings do `gitpr release --help`; defaults da tabela 7 == `src/config.py`; anatomia do sample == saída real do `changelog_builder` (headings `## [x.y.z] - date`, `### ⚠️ Breaking Changes` etc.).
- `git status`: apenas os 7 arquivos novos como untracked; nada staged/commitado.
- Nenhuma suíte de testes executada — tarefa só de documentação (nenhum código tocado).

## Fora de escopo

- Nenhuma alteração de código (CLI, `get_doc_url`, i18n) — somente documentação.
- Nenhum registro em README.md (raiz e traduções), CLAUDE.md ou docs/ARCHITECTURE.md.
- Sem ADR novo e sem alteração dos ADR-002/ADR-003/glossário/spec/surveys da feature (na árvore, ainda não commitados).
- Sem entrada de ajuda contextual para `gitpr release` no `HELP_MAP`/`get_doc_url` (o subcomando ainda não tem `-h` roteado a documentação — anotar como next step no relatório).
- Traduções das ~40 chaves i18n pendentes do fluxo de release (dívida conhecida) fora desta tarefa.
