# Plano — Documentação GitPR Multi-Forge SCM (família `scm-multiforge.md`, 5 idiomas)

## Contexto

A funcionalidade **Multi-Forge SCM (abstração `ScmProvider`)** foi implementada em 2026-09-05 e documentada nos artefatos de governança de `docs/plans/` (plano `20260905_multi-forge_abstracao_scmprovider.md`, `ADR-001-scm-abstraction.md` — Aceito —, `glossary-scm-multiforge.md`) e no relatório `docs/claude-code/reports/develop_natan/2026-09-05_scm_multiforge_providers.md`.

Faltava a **documentação técnica de usuário em `docs/`**: o projeto mantém 29 famílias de documentos, cada uma em 5 cópias (master inglês sem sufixo + `.pt_br.md`, `.pt_pt.md`, `.es_es.md`, `.fr_fr.md`, com paridade linha a linha — ex.: `code-review-ia.md` tem 105 linhas em todas as cópias). A funcionalidade Multi-Forge não possuía família própria.

## Decisões (aprovadas no grilling)

1. **Nome do arquivo:** família `scm-multiforge.md` (alinha com `glossary-scm-multiforge.md` / `ADR-001-scm-abstraction.md` / spec `2026-09-02_multi_skill_gitpr_multiforge_spec.md`).
2. **Escopo/audiência:** documento de referência orientado ao usuário (wizard `--init`, config `.env`, uso por forge, limitações) + seção curta "For Developers and Plugins" (contrato, erros, shim deprecado, apontadores para ADR/glossário).
3. **Índices:** somente os 5 arquivos do documento em `docs/` — sem alterar README.md, CLAUDE.md ou docs/ARCHITECTURE.md.
4. **Artefatos:** plano datado em `docs/plans/` + relatório final obrigatório (CLAUDE.md). ADR-001/glossário existentes permanecem inalterados; nenhum ADR novo (sem decisão difícil de reverter).

## Entregáveis (7 arquivos novos)

| Arquivo | Idioma | Finalidade |
|---------|--------|------------|
| `docs/scm-multiforge.md` | Inglês | Master |
| `docs/scm-multiforge.pt_br.md` | PT-BR | Tradução |
| `docs/scm-multiforge.pt_pt.md` | PT-PT | Tradução (europeu autêntico) |
| `docs/scm-multiforge.es_es.md` | Espanhol | Tradução |
| `docs/scm-multiforge.fr_fr.md` | Francês | Tradução |
| `docs/plans/20260907_documentacao_scm_multiforge.md` | PT-BR | Este plano |
| `docs/claude-code/reports/develop_natan/2026-09-07_documentacao_scm_multiforge.md` | Inglês | Relatório final (template CLAUDE.md) |

## Estrutura do documento (master EN)

Convenções de `docs/code-review-ia.md`: H1 `# Technical Documentation: Multi-Forge SCM (ScmProvider)`, seções numeradas `## N.`/`### N.N`, separadores `---`, tabelas Markdown, blocos ```bash, nota final em blockquote com cross-link.

1. **Supported Forges** — tabela Forge/Provider key/API base/Auth; ### 1.1 Auto-detection do remote `origin` (substring: gitlab, bitbucket, dev.azure.com/visualstudio.com, default github) + endereçamento `RepoRef`/workspace por forge.
2. **First-Time Setup — `gitpr --init`** — passos do wizard: detecção → confirmação → extras por forge (Azure org/project; Bitbucket username) → base URL customizada (exceto GitHub) → token → `test_connection()` (3 tentativas; 401 re-prompt amarelo; demais erros abortam) → persistência só no sucesso (`GITPR_SCM_PROVIDER` + token Fernet + extras em `~/.gitpr/.env`).
3. **Manual Configuration (.env)** — tabela das 7 chaves `GITPR_SCM_*` + fallback legado `GITHUB_TOKEN_ENCRYPTED` (zero migração).
4. **Using GitPR with the Configured Forge** — ### 4.1 Publicação de PR (TUI / `--no-edit` / `--no-publish`); ### 4.2 Issues (`-is`, F3; Azure → salvar local F2; Bitbucket exige Issue Tracker); ### 4.3 Expiração/reauth 401.
5. **Per-Forge Notes and Limitations** — GitHub (byte-parity, reviewers nativos), GitLab (`iid`, draft `"Draft: "`, URL-quote, strategy ignorada), Bitbucket (Basic + username, Issue Tracker, estratégias de merge), Azure (org/project, `api-version=7.1`, `refs/heads/`, diff = resumo textual por arquivo, sem issues, remotes `*.visualstudio.com`).
6. **For Developers and Plugins** (curta) — contrato em `src/infrastructure/scm/`, `resolve_scm_provider()`, `ScmProviderError`/`ScmNotSupportedError` (raise, nunca tuplas), shim `github_api.py` deprecado; links para ADR-001 e glossário.

## Etapas

1. Levantar convenções de tradução/link das cópias existentes (`code-review-ia.*`): H1/seções traduzidos, tokens técnicos intactos, comentários de code block traduzidos, cross-links sem sufixo.
2. Escrever `docs/scm-multiforge.md` (master EN, 145 linhas).
3. Escrever as 4 traduções com paridade linha a linha (145 linhas cada).
4. Escrever este plano (PT-BR).
5. Escrever o relatório final conforme template obrigatório do CLAUDE.md.
6. Nenhum commit: árvore de trabalho intacta para revisão do usuário.

## Verificação

- Paridade: `wc -l` idêntico (145) nas 5 cópias; títulos `^#` nas mesmas linhas em todas as cópias.
- `git status`: apenas os 7 arquivos novos como untracked; nada staged/commitado.
- Leitura pontual de H1 + trechos para conferir idioma e tokens (`GITPR_SCM_*`, provider keys) intactos.

## Fora de escopo

- Nenhuma alteração de código (CLI, `get_doc_url`, i18n) — somente documentação.
- Nenhum registro em README.md (raiz e traduções), CLAUDE.md ou docs/ARCHITECTURE.md.
- Sem ADR novo e sem alteração do ADR-001/glossário existentes.
