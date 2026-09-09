# Plano — Documentação GitPR Release Notes / Changelog (família `release-notes.md`, 5 idiomas)

## Context

A funcionalidade **GitPR Automated Changelog / Release Notes** (`gitpr release` — o primeiro subcomando da CLI) foi implementada e documentada apenas nos artefatos internos: spec `docs/plans/20260904_skill_gitpr_release_notes_spec.md`, `ADR-002-gitpr-release-subcommand.md`, `ADR-003-gitpr-release-flat-modules.md`, `glossary-release-notes.md`, relatórios de tarefa em `docs/claude-code/reports/develop_natan/2026-09-07_*.md` e `2026-09-08_skill_release_template.md`, e surveys em `docs/survey/` (todos já no lugar, árvore não commitada).

Falta a **documentação técnica de usuário em `docs/`**: o projeto mantém 31 famílias de documentos, cada uma em 5 cópias (master inglês sem sufixo + `.pt_br.md`, `.pt_pt.md`, `.es_es.md`, `.fr_fr.md`, paridade linha a linha). A feature não tem família própria. Precedente exato das tarefas-irmãs: `docs/plans/20260907_documentacao_scm_multiforge.md` + `2026-09-07_documentacao_scm_multiforge.md` e o par equivalente de suggested-reviewers.

**Escopo:** somente documentação — nenhuma alteração de código (CLI, `get_doc_url`, i18n, README, CLAUDE.md, ARCHITECTURE). Nenhum ADR novo (nada de decisão difícil de reverter; ADRs/glossário existentes permanecem intocados). Nenhum commit (regra do projeto).

## Entregáveis (7 arquivos novos)

| Arquivo                                                                           | Idioma   | Finalidade                                           |
| --------------------------------------------------------------------------------- | -------- | ---------------------------------------------------- |
| `docs/release-notes.md`                                                           | Inglês   | Master (EN, sem sufixo)                              |
| `docs/release-notes.pt_br.md`                                                     | PT-BR    | Tradução completa                                    |
| `docs/release-notes.pt_pt.md`                                                     | PT-PT    | Tradução (europeu autêntico)                         |
| `docs/release-notes.es_es.md`                                                     | Espanhol | Tradução completa                                    |
| `docs/release-notes.fr_fr.md`                                                     | Francês  | Tradução completa                                    |
| `docs/plans/20260908_documentacao_release_notes.md`                               | PT-BR    | Plano datado desta tarefa (estilo dos planos irmãos) |
| `docs/claude-code/reports/develop_natan/2026-09-08_documentacao_release_notes.md` | Inglês   | Relatório final obrigatório (template CLAUDE.md)     |

Fonte de conteúdo: relatórios/spec/ADR/glossário listados acima + leitura direta do código para fidelidade. Nome `release-notes.md` aprovado pelo usuário (vocabulário da própria feature).

## Estrutura do documento (master EN) — espelho de docs/code-review-ia.md

Convenções: H1 `# Technical Documentation: Release Notes & Changelog (gitpr release)`; parágrafo intro sem heading; seções numeradas `## N.` / `### N.N`; separadores `---` só entre H2; tabelas Markdown (2-3 colunas, primeira célula em **bold**); blocos fenced ```bash / ```markdown; sem TOC, sem seção de referências, sem rodapé data/autor/licença; nota final em blockquote com cross-link relativo sem sufixo (`skill-template.md`, `scm-multiforge.md`).

Esboço alvo (~7 H2, ~200 linhas):

1. **Overview** — subcomando `gitpr release` (raiz virou `click.group`; flags legadas inalteradas); fluxo padrão local (gera seção + salva `CHANGELOG.md` + preview de terminal de até 40 linhas, sem TUI interativo em v1); `### 1.1 Command Reference` com tabela de opções cujas descrições são os **help strings verbatim** do CLI (`--since`, `--version`, `--publish`, `--draft`, `--format {markdown|json}`, `--force` — de `src/main.py` região do subcomando, ~linhas 1594-1851) e tabela `| Characteristic | Description |` do fluxo default (fonte: range since..HEAD sem merges; AI automática; arquivos escritos; nada publicado; tags/arquivos de versão nunca tocados).
2. **Release Range and Version Suggestion** — `### 2.1 Commit Range (--since)`: origem default última tag (`git describe --tags --abbrev=0`), sem tag = primeira release (range desde o primeiro commit), merges excluídos, fim sempre `HEAD`; `### 2.2 Semantic Version Suggestion`: regras MAJOR/MINOR/PATCH (breaking→MAJOR; ≥1 feat→MINOR; só fixes/outros→PATCH; sem tag semver→nenhuma sugestão e `--version` obrigatório p/ publish), read-only (tags git apenas), prefixo `v` preservado, prompt `❓ Use the suggested version {version}?` (quando ocorre/é pulado); `### 2.3 Explicit Version (--version)`: única fonte da tag publicada, aceita sem `v`.
3. **Changelog Structure and Files** — `### 3.1 Commit Classification`: tabela das 8 categorias (FEATURE/FIX/BREAKING/PERFORMANCE/DOCS/REFACTOR/CHORE/OTHER → headings com emoji), não-conformes → OTHER + warning (nunca falha), dedupe PR `(#123)`, breaking só no bloco Breaking; `### 3.2 Version Section Anatomy`: exemplo markdown realista da anatomia da seção (`## [x.y.z] - date`, Summary, blocos por categoria, `**Contributors:**`) — **verificar no código** (`src/changelog_builder.py`: headings/ordem exatas, rótulos via `__()`); `### 3.3 Files Written`: tabela `CHANGELOG.md` (raiz, override por env) / artefato `.gitpr/reports/release/{branch}_{datetime}_RELEASE.md` (best-effort) / preview.
4. **AI Executive Summary** — `### 4.1 First-Run Skill Template (.gitpr.release.md)`: auto-download no primeiro run em modo markdown (só na camada CLI; respeita `CURRENT_LANG`; nunca sobrescreve; nunca falha em erro de rede; pulado em `--format json`), usado como `system_instruction` (persona Release Manager), editável; `### 4.2 Generation and Graceful Degradation`: JSON estrito `{"summary": ...}`, Map-Reduce em lotes de 200 commits, cache MD5 (action `release_summary` — edição da skill não invalida o cache, fato documentado), idioma da interface; degradação: sem chave/falha → warning `AI summary failed: changelog generated without a summary.` e segue com listas classificadas; `GITPR_RELEASE_AI_SUMMARY=false` desliga.
5. **Publishing to the Forge** — `### 5.1 Confirmation and Guardrails (--publish)`: confirmação explícita `❓ Publish release {version} on {provider}?` (default No), guarda sem remote `origin` (exit 1), `--publish`+json só avisa, corpo da release = seção sem o heading `## [x.y.z]`; `### 5.2 Supported Forges`: tabela GitHub (tag auto-criada via API na default branch; draft honrado) / GitLab (tag pré-existente; sem draft) / Bitbucket Cloud e Azure DevOps (sem API de release → warning, fluxo local completa); `### 5.3 Drafts (--draft)`: só com `--publish`; GitHub default draft (`GITPR_RELEASE_PUBLISH_DRAFT_BY_DEFAULT=true`).
6. **JSON Mode and Idempotency** — `### 6.1 Pure JSON Output (--format json)`: stdout-only (não escreve nada, não publica, nunca pergunta, sem auto-download), para scripts/CI; `### 6.2 Existing Section and --force`: seção existente → aborta exit 1 (nunca duplica/sobrescreve em silêncio); `--force` regenera.
7. **Environment Variables** — tabela 5 chaves com defaults verbatim de `src/config.py`: `GITPR_RELEASE_CHANGELOG_PATH` (`CHANGELOG.md`), `GITPR_RELEASE_AI_SUMMARY` (`true`), `GITPR_RELEASE_AUTO_BUMP` (`true`), `GITPR_RELEASE_PUBLISH_DRAFT_BY_DEFAULT` (`true`), `OUTPUT_FILE_NAME_RELEASE` (`{branch}_{datetime}_RELEASE.md`); convenção booleana ("false"/"0" desliga) e arquivo `~/.gitpr/.env`.

Footer: `> **Note:** See also the [Skills and Templates documentation](skill-template.md) ...`

**Não afirmar (anti-overclaim verificado):** TUI interativo de preview em v1 (só print de terminal ≤40 linhas); range entre duas tags (`--since A --until B` fora de escopo); config YAML / mapeamento custom `commit_types`; regra específica p/ `revert:`; traduções inventadas de strings de UI que não existam nos `langs/*.json`.

## Convenções de tradução (das cópias existentes)

- Prosa 100% traduzida (inclui intro, cabeçalhos de tabela, nota final); tokens técnicos intactos (flags, env vars, paths, `CHANGELOG.md`, exemplos em code block, cross-links **sem sufixo**).
- Voz: pt_br informal e com glossário do próprio repo (`bump`, `release`, `merge` mantidos, como no `glossary-release-notes.md`); pt_pt europeu autêntico ("por omissão", "secção", "ficheiro", "funcionalidade"); es neutro ("lanzamiento", "borrador"); fr com tipografia francesa (" : ") e "notes de version".
- Strings de UI citadas: só as verbatim em EN (entre backticks) — exceto onde existir tradução real verificada no `langs/*.json` correspondente (hoje só `pt_br.json` existe localmente; headings do changelog podem renderizar EN como fallback — o texto dirá "segue o idioma da interface", que permanece verdadeiro).
- Mapa de termos por idioma (changelog mantido; release notes → notas de versão / notas de la versión / notes de version; versão sugerida / versión sugerida / version suggérée; resumo executivo → resumen ejecutivo / résumé exécutif; contribuidores → colaboradores / contributeurs; breaking change → mudança quebra / cambio incompatible / changement cassant; draft → rascunho / borrador / brouillon...).
- Paridade: mesmo número de linhas nas 5 cópias (padrão das famílias existentes); equalizar prosa no fim.

## Etapas

1. **Verificações de fidelidade** (leitura direta): `src/main.py` (docstring do subcomando + help strings verbatim das 6 opções + mensagens de UI reais), `src/config.py` (defaults exatos das 5 env vars), `src/changelog_builder.py` (headings/categorias/ordem/anatomia exatas da seção — conferir `⚠️` vs `⚠`, ordem dos blocos, rótulo `Contributors`), `docs/code-review-ia.md` + `docs/code-review-ia.pt_br.md` (estilo/tradução).
2. Escrever `docs/release-notes.md` (master EN) conforme o esboço.
3. Escrever as 4 traduções com paridade linha a linha, a partir do master.
4. Escrever `docs/plans/20260908_documentacao_release_notes.md` (PT-BR, estilo do plano irmão: Contexto / Decisões / Entregáveis / Estrutura / Etapas / Verificação / Fora de escopo — citando os artefatos-fonte já salvos em `docs/plans/`, `docs/survey/` e `docs/claude-code/reports/`).
5. Escrever o relatório final conforme template obrigatório do CLAUDE.md (seções What was done / Changed files / Impact / Next steps + tabela de verificação).
6. Nenhum commit — árvore de trabalho intacta para revisão do usuário.

## Verificação

- Paridade: `wc -l` idêntico nas 5 cópias; headings reais (`grep '^#'`) nas mesmas linhas em todas as cópias; blocos de código fenced idênticos entre master e cópias.
- Fidelidade técnica: opções da tabela 1.1 == help strings do `gitpr release --help`; defaults da tabela 7 == `src/config.py`; seção exemplo == saída real do `changelog_builder`.
- `git status`: apenas os 7 arquivos novos como untracked; nada staged/commitado.
- Nenhuma suíte de testes executada — tarefa só de documentação (nenhum código tocado).

## Fora de escopo

- Nenhuma alteração de código; nenhum registro em README.md/CLAUDE.md/docs/ARCHITECTURE.md; nenhum link do `HELP_MAP`/`get_doc_url` (subcomando `gitpr release` ainda não tem entrada de ajuda contextual — anotar como next step no relatório); ADRs/glossário/spec existentes intocados; i18n das 40 chaves pendentes (dívida conhecida, fora desta tarefa).
