# ADR-002 — Sugestão de Revisores para Pull Requests (`suggest_reviewers`)

- **Status:** Aceito
- **Data:** 2026-09-06
- **Contexto:** spec [20260904_skill_gitpr_reviewer_suggestion_spec.md](20260904_skill_gitpr_reviewer_suggestion_spec.md), entrevista (grilling) + domain-modeling e plano [20260906_skill_gitpr_reviewer_suggestion_plan.md](20260906_skill_gitpr_reviewer_suggestion_plan.md)
- **Glossário:** [glossary-reviewer-suggestion.md](glossary-reviewer-suggestion.md)

## Contexto

Ao publicar um PR, o GitPR agora sugere 1..N revisores calculando quem mais
tocou (git blame sobre a working tree) as **linhas adicionadas** do diff, com
score `0.5·linhas + 0.3·arquivos + 0.2·recência`, exibição **editável** no PR
Publisher (TUI) e submissão real na criação do PR.

A exploração do código mostrou que a spec foi escrita contra suposições
defasadas: a CLI não tem subcomando `pr` (o fluxo vive em `main.py` com flags),
não existe parser de hunks de diff, `PullRequestRequest.reviewers` é um campo
morto que nenhum provider envia, a configuração é dotenv plano (sem YAML — ver
[ADR-001](ADR-001-scm-abstraction.md)), a TUI de PRs não tem seção de metadados
e a suíte de testes não usa repositórios git reais (mocks de subprocess). Essas
divergências foram entrevistadas com o usuário (Rodadas 1–2 do grilling) e as
respostas viraram decisões vinculantes abaixo.

## Decisão

Criar a sugestão de revisores como um use case **flat** de `src/`:

1. **`src/reviewer_suggestion.py` (puro)** — dataclasses `BlameHit`,
   `ReviewerCandidate`, `ReviewerSuggestionResult`; pesos/half-life e bots
   padrão como constantes de código; `rank_reviewers()` com exclusão do autor
   do PR, de bots e de `excluded_authors`, score ponderado e truncamento em
   `top_n`. Sem git, sem rede.
2. **`src/blame_engine.py` (+1 função)** — `get_blame_for_range()` roda
   `git blame --line-porcelain -L` com o mesmo contrato tolerante da
   arqueologia (erros → `[]`); **nenhuma refatoração** de
   `execute_git_blame`/`run_blame_analysis` (regressão zero da arqueologia).
3. **`src/diff_parser.py` (novo)** — `parse_added_lines()`: parser por
   estados dos hunks já produzidos por `get_git_full_diff()` (flags
   `-U1 -w -M -B`, renames, `+++ /dev/null`, binários, `\ No newline`).
4. **`src/suggest_reviewers.py` (novo)** — `compute_reviewer_suggestions()`
   orquestra parse → agrupamento de intervalos → blame por intervalo →
   ranking, **nunca levantando** (arquivos sem histórico/blame incompleto
   viram warnings i18n); helpers de apresentação via `__()`.
5. **Config dotenv plana** — `GITPR_SUGGEST_REVIEWERS` (default `true`),
   `GITPR_REVIEWER_SUGGESTION_TOP_N` (default `3`),
   `GITPR_REVIEWER_SUGGESTION_EXCLUDED` (CSV opcional) em `DEFAULT_CONFIG`
   (mesmo padrão das chaves ADR-001).
6. **`src/main.py` orquestra** — flag `--no-suggest-reviewers` (opt-out);
   cálculo **só** no fluxo TUI default (nunca em `--no-edit`/`--no-publish`);
   view dict `{"handles", "lines", "submittable", "note"}` repassada ao
   `PrPublishApp`. Falha em qualquer etapa → secho amarelo e fluxo segue.
7. **SCM GitHub** — método **não-abstrato**
   `request_pull_request_reviewers(repo, pr_id, reviewers)` no ABC
   (default `raise ScmNotSupportedError`) + implementação GitHub
   (`POST …/pulls/{n}/requested_reviewers`, expected `{201}`) e
   `email_to_handle()` best-effort (parse de `users.noreply.github.com`,
   fallback `/search/users in:email`; nunca levanta).
8. **TUI `PrPublishApp`** — seção `👥 Suggested Reviewers` editável
   (`Input` CSV pré-preenchido + hint com justificativas); attach pós-criação
   e pós-update do PR, GitHub-only, não-fatal (aviso no `final_message`).

### Alternativas consideradas

| Alternativa | Veredito |
|---|---|
| Camadas `src/domain|application` e mover `blame_engine.py` para `infrastructure/git/` (spec) | Rejeitada — `blame_engine.py` importa `core.py`; qualquer orquestração em `core.py` criaria ciclo. Arquitetura flat + integração em `main.py` (orquestrador real do fluxo). |
| Subcomando `gitpr pr` (spec) | Rejeitada — a CLI é flag-based; adicionar subcomando quebraria `gitpr`, hooks e docs. Flag opt-out no fluxo existente. |
| Submissão multi-forge desde já (spec) | Rejeitada — só o GitHub tem endpoint `requested_reviewers` pós-criação; GitLab/Bitbucket/Azure exibem a sugestão localmente (nota i18n). |
| Campo `reviewers` no payload de criação (spec) | Rejeitada — `PullRequestRequest.reviewers` é morto e o GitHub não aceita reviewers no create; attach pós-criação via endpoint próprio. |
| Config em YAML (`suggest_reviewers.yml`, spec) | Rejeitada — o projeto usa dotenv plano + Fernet (ADR-001); 3 chaves novas em `DEFAULT_CONFIG`. Pesos fixos em código (constantes). |
| Atribuição sobre o diff inteiro (linhas removidas/contexto) | Rejeitada — blame vale sobre linhas adicionadas (new-side) contra a working tree; "Not Committed Yet" (`0000…`) é pulado. |
| Excluir todo domínio `users.noreply.github.com` como bot (spec) | Rejeitada — é o e-mail padrão de usuários reais do GitHub; filtro fino: sufixo `[bot]` no nome/local-part + lista de bots conhecidos. |

## Desvios aprovados (vs. a spec)

1. **Arquitetura plana, não em camadas** — spec §4 pedia `src/domain`/
   `application` e mover o blame para `infrastructure/git/`. O código atual é
   flat; `blame_engine.py → core.py` torna a movimentação cara e cíclica.
   Novos módulos na raiz de `src/`; `core.py` intocado; `main.py` orquestra.
2. **Integração no fluxo TUI default com flag opt-out, não subcomando `pr`**
   — a spec §4.3 descreve subcomando; a CLI real é de flags. Default ON +
   `--no-suggest-reviewers` (e `GITPR_SUGGEST_REVIEWERS=false`); cálculo
   **nunca** roda em `--no-edit`/`--no-publish`.
3. **Submissão GitHub-only** — a spec §5 pedia submissão nos forges; só o
   GitHub expõe `requested_reviewers` (pós-criação). As outras forges exibem
   localmente com nota. A base do ABC ganha método **não-abstrato** que levanta
   `ScmNotSupportedError` (contrato de testes intacto).
4. **Mapeamento e-mail→handle por `users.noreply` + search, nunca por domínio
   como bot** — a spec §5.3 excluía o domínio noreply inteiro como bot; isso
   excluiria usuários reais. Filtro fino (`[bot]` e bots conhecidos) + parse do
   noreply + fallback `/search/users in:email` (nunca bloqueia).
5. **Config dotenv (3 chaves) + pesos em código** — a spec §6.1 pedia YAML com
   pesos configuráveis; o projeto não tem YAML de config. Pesos/half-life são
   constantes de código (testáveis); só enable/top_n/excluídos são chaves.
6. **Blame granular sobre linhas adicionadas da working tree** — a spec §3.3
   descrevia atribuição por heurística sobre o diff; a implementação blameia
   cada intervalo de linhas `+` (new-side) da working tree, pulando NCY —
   atribuição real de autoria em vez de heurística.
7. **TUI: seção editável com Input CSV + hint, attach não-fatal** — a spec
   pedia lista fixa de metadados; a TUI não tem seção de metadados e o fluxo
   exige edição (remover/adicionar). Input pré-preenchido + hint read-only;
   falha de attach degrada a aviso, o PR permanece criado.

## Consequências

**Positivas:**
- Zero mudança de comportamento para quem não quer a feature (default ON só
  computa no fluxo TUI; falhas são não-bloqueantes) e opt-out por flag ou env.
- A arqueologia (blame) não foi tocada — `test_blame_metrics.py` verde.
- Use case testado em dois níveis: scoring puro (sem git) + integração com
  repositório git real em `tmp_path` (offline, identidades por `-c user.*`).
- Reaproveita `ScmProvider`/`ScmProviderError` do ADR-001; nada novo por forge
  além do método GitHub.

**Negativas / custos:**
- Sugestões em GitLab/Bitbucket/Azure são apenas informativas (limitação de
  API documentada na TUI e no glossário).
- O mapeamento e-mail→handle depende de o git ter e-mails que o GitHub
  reconhece (noreply ou públicos); candidatos sem handle aparecem pelo nome.
- `sync_i18n.py` (regex) não dobra concatenação implícita de literais
  adjacentes — `test_i18n` exige chaves AST-cheias; rodar o sync exige
  reconstruir com o conjunto AST (ver report 2026-09-06).

**Observado fora do escopo:** sugestão por faixas de revisão do próprio PR
(contra o diff do PR aberto), times/CODEOWNERS, e submissão em forges sem
endpoint (quando existir) ficam para trabalho futuro; `chat_app.py` mantém uma
chave i18n com texto pré-existente corrompido (`Ctrlhift` — herdado, fora do
escopo desta feature).
