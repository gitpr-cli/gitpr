# Plano — Documentação GitPR Suggested Reviewers (família `suggested-reviewers.md`, 5 idiomas)

## Contexto

A funcionalidade **Suggested Reviewers (sugestão de revisores para pull requests)** foi implementada em 2026-09-06 (commit `c7148ed`) e documentada nos artefatos de governança de `docs/plans/` (plano `20260906_skill_gitpr_reviewer_suggestion_plan.md`, `ADR-002-reviewer-suggestion.md` — Aceito —, `glossary-reviewer-suggestion.md`) e no relatório `docs/claude-code/reports/develop_natan/2026-09-06_reviewer_suggestion.md`.

Faltava a **documentação técnica de usuário em `docs/`**: o projeto mantém 30 famílias de documentos, cada uma em 5 cópias (master inglês sem sufixo + `.pt_br.md`, `.pt_pt.md`, `.es_es.md`, `.fr_fr.md`, com paridade linha a linha — ex.: `scm-multiforge.md` tem 145 linhas em todas as cópias). A funcionalidade de sugestão de revisores não possuía família própria, embora a ajuda contextual da flag já a referencie: `HELP_MAP["no-suggest-reviewers"]` aponta para `get_doc_url("suggested-reviewers.md")` (`src/main.py:222`) — um link morto até esta tarefa.

## Decisões (aprovadas no grilling — rodada 1)

1. **Nome do arquivo:** família `suggested-reviewers.md` — fixada pelo `get_doc_url` do `HELP_MAP` (`src/main.py:222`); não `reviewer-suggestion.md` (nome usado só nos artefatos de `docs/plans/`).
2. **Escopo confirmado:** a menção "Multi-Forge SCM" no pedido era texto de modelo desatualizado — essa família já existe e foi commitada hoje (`scm-multiforge.*`, commit `ddc8fff`).
3. **Escopo/audiência:** documento de referência orientado ao usuário (como funciona, configuração `.env`, uso na TUI, suporte por forge) + seção curta "For Developers and Plugins" (módulos, contrato SCM, apontadores para ADR-002/glossário).
4. **Índices:** somente os 5 arquivos do documento em `docs/` — sem alterar README.md, CLAUDE.md ou docs/ARCHITECTURE.md.
5. **Artefatos:** plano datado em `docs/plans/` + relatório final obrigatório (CLAUDE.md). ADR-002/glossário existentes permanecem inalterados; nenhum ADR novo (sem decisão difícil de reverter).

## Entregáveis (7 arquivos novos)

| Arquivo | Idioma | Finalidade |
|---------|--------|------------|
| `docs/suggested-reviewers.md` | Inglês | Master (107 linhas) |
| `docs/suggested-reviewers.pt_br.md` | PT-BR | Tradução (107 linhas) |
| `docs/suggested-reviewers.pt_pt.md` | PT-PT | Tradução (europeu autêntico) |
| `docs/suggested-reviewers.es_es.md` | Espanhol | Tradução |
| `docs/suggested-reviewers.fr_fr.md` | Francês | Tradução |
| `docs/plans/20260907_documentacao_suggested_reviewers.md` | PT-BR | Este plano |
| `docs/claude-code/reports/develop_natan/2026-09-07_documentacao_suggested_reviewers.md` | Inglês | Relatório final (template CLAUDE.md) |

## Estrutura do documento (master EN)

Convenções de `docs/scm-multiforge.md`/`docs/code-review-ia.md`: H1 `# Technical Documentation: Suggested Reviewers for Pull Requests`, seções numeradas `## N.`/`### N.N`, separadores `---`, tabelas Markdown, blocos ```bash, nota final em blockquote com cross-link.

1. **How It Works** — ### 1.1 Autoria sobre as linhas adicionadas (diff base vs. working tree com staged e smart-excludes, só linhas `+`, NCY `0000…` pulado, blame sem revisão, arquivos sem histórico → aviso); ### 1.2 Ranking (tabela de fatores 50% linhas / 30% arquivos / 20% recência com `1/(1+days/90)`, exclusões de autor do PR/bots — `[bot]` e lista conhecida, domínio noreply nunca é bot — e `GITPR_REVIEWER_SUGGESTION_EXCLUDED`, desempate por linhas, truncamento em `top_n`).
2. **Configuration** — default ON; flag `--no-suggest-reviewers`; tabela das 3 chaves `GITPR_*` em `~/.gitpr/.env` (valores falsy, `top_n` inválido → 3); nunca auto-gravadas; `--no-edit`/`--no-publish` nunca calculam.
3. **Suggested Reviewers in the PR Publisher (TUI)** — ### 3.1 seção `👥` editável (Input CSV pré-preenchido + hint read-only; vazio = sem submissão) com as mensagens de UI reais; ### 3.2 Publicação (F3 → PR criado → attach GitHub `requested_reviewers` no create e no update; falha não-fatal, ex. 422); ### 3.3 ajuda contextual (`gitpr -h --no-suggest-reviewers`).
4. **Forge Support and Limitations** — tabela GitHub (envia) vs. GitLab/Bitbucket/Azure (apenas local, sem campo de entrada); mapeamento e-mail→handle best-effort (parse do noreply, fallback `/search/users in:email`, candidato sem handle não é pré-preenchido); menos sugestões que `top_n` é normal, nunca erro.
5. **For Developers and Plugins** (curta) — módulos flat em `src/` (`reviewer_suggestion.py` puro, `diff_parser.py`, `blame_engine.py::get_blame_for_range` sem tocar a arqueologia, `suggest_reviewers.py` que nunca levanta), 3 chaves em `DEFAULT_CONFIG` (`src/config.py`), contrato SCM (método **não-abstrato** com default `ScmNotSupportedError`; implementação só no GitHub + `email_to_handle()`), view dict `{handles, lines, submittable, note}`, texto visível via `__()`; links para ADR-002 e glossário. Nota final cruza `pull-request-publication.md`.

## Etapas

1. Levantar convenções de tradução/link das cópias existentes (`scm-multiforge.*`): H1/seções traduzidos, tokens técnicos intactos, comentários de code block traduzidos, cross-links sem sufixo.
2. Escrever `docs/suggested-reviewers.md` (master EN, 107 linhas).
3. Escrever as 4 traduções com paridade linha a linha (107 linhas cada), citando apenas strings de UI verificadas nos 6 `langs/*.json` (nunca traduções inventadas).
4. Escrever este plano (PT-BR).
5. Escrever o relatório final conforme template obrigatório do CLAUDE.md.
6. Nenhum commit: árvore de trabalho intacta para revisão do usuário.

## Verificação

- Paridade: `wc -l` idêntico (107) nas 5 cópias; títulos `^#` (headings reais) nas mesmas linhas em todas as cópias.
- `git status`: apenas os 7 arquivos novos como untracked; nada staged/commitado.
- Leitura pontual de H1 + trechos para conferir idioma e tokens (`GITPR_*`, flags) intactos.

## Fora de escopo

- Nenhuma alteração de código (CLI, `get_doc_url`, i18n) — somente documentação.
- Nenhum registro em README.md (raiz e traduções), CLAUDE.md ou docs/ARCHITECTURE.md.
- Sem ADR novo e sem alteração do ADR-002/glossário/plano da funcionalidade (já commitados).
