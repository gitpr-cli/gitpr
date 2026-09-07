# Documentação Técnica: Revisores Sugeridos para Pull Requests

Ao publicar um Pull Request através do publicador interativo do GitPR (modo predefinido `gitpr`), o GitPR sugere quem o deve rever: identifica as pessoas que trabalharam no código que está a alterar e propõe até `GITPR_REVIEWER_SUGGESTION_TOP_N` candidatos (3 por omissão). As sugestões são apresentadas num campo editável do Publicador de PR (TUI) e, no GitHub, são submetidas à nova pull request logo depois de esta ser criada.

O cálculo está ativado por omissão e só corre no fluxo do publicador interativo — nunca com `--no-edit` nem `--no-publish`. É puramente consultivo e totalmente não bloqueante: qualquer falha ou situação não suportada degrada para um aviso e o fluxo de publicação continua inalterado.

---

## 1. Como Funciona

O GitPR não adivinha: atribui autoria real com `git blame`, executado sobre as linhas exatas que o seu diff adicionou, comparando a branch base com a sua working tree.

### 1.1 Autoria sobre as Linhas Adicionadas

- A entrada é o mesmo diff que o GitPR já calculou para o PR: branch base vs. working tree (alterações staged incluídas), com os smart-excludes aplicados. O parser consome esse texto do diff e nunca volta a executar `git diff`.
- Apenas as **linhas adicionadas** (`+`) contam para a autoria. Linhas removidas e de contexto são ignoradas.
- Linhas ainda não commitadas — "Not Committed Yet", hash de blame `0000…` — são saltadas: são o seu próprio trabalho em curso.
- O blame corre sobre a working tree (sem revisão), por isso coincide exatamente com o diff, incluindo ficheiros staged e novos.
- Ficheiros sem histórico utilizável (novos, binários, clones shallow) não geram candidatos: é mostrado um aviso e a análise prossegue.

### 1.2 Classificação e Exclusões

Cada autor encontrado é agregado por ficheiro e por linha e recebe uma pontuação:

| Fator | Peso | Significado |
| --- | --- | --- |
| Linhas tocadas | 50% | Percentagem das linhas adicionadas do diff escritas pela pessoa |
| Ficheiros tocados | 30% | Percentagem dos ficheiros alterados em que a pessoa tem autoria |
| Recência | 20% | `1 / (1 + days / 90)` — meia-vida de 90 dias desde o último toque |

O autor do PR é sempre excluído, mesmo quando domina o diff. **Bots** também são excluídos: qualquer identidade cujo nome ou a parte local do e-mail termine em `[bot]`, ou cujo e-mail esteja na lista de bots conhecidos (Dependabot, GitHub Actions, etc.). O domínio `users.noreply.github.com` nunca é tratado como bot — é o e-mail predefinido de utilizadores reais do GitHub. Pessoas adicionais podem ser excluídas através de `GITPR_REVIEWER_SUGGESTION_EXCLUDED`. Empates são desfeitos por linhas tocadas e o resultado é truncado no `top_n` configurado (predefinição: 3).

---

## 2. Configuração

A funcionalidade está ativada por omissão. Desative-a por execução com a flag ou globalmente através do ambiente:

```bash
gitpr --no-suggest-reviewers        # Desativa o cálculo nesta execução
```

```bash
# ~/.gitpr/.env — desativa globalmente e ajusta a classificação
GITPR_SUGGEST_REVIEWERS=false
GITPR_REVIEWER_SUGGESTION_TOP_N=5
GITPR_REVIEWER_SUGGESTION_EXCLUDED=renovate[bot],qa@example.com
```

| Variável | Predefinição | Descrição |
| --- | --- | --- |
| `GITPR_SUGGEST_REVIEWERS` | `true` | Interruptor geral. Valores falsy: `false`, `0`, `no`, `off`, `n` |
| `GITPR_REVIEWER_SUGGESTION_TOP_N` | `3` | Quantos candidatos sugerir; inválido ou ≤ 0 reverte para 3 |
| `GITPR_REVIEWER_SUGGESTION_EXCLUDED` | *(vazio)* | CSV opcional de e-mails ou nomes a excluir, além do autor do PR e dos bots |

As chaves são lidas de `~/.gitpr/.env` e nunca são gravadas automaticamente. `--no-edit` e `--no-publish` nunca calculam sugestões, independentemente da configuração.

---

## 3. Revisores Sugeridos no Publicador de PR (TUI)

### 3.1 A Secção de Revisores Sugeridos

No fluxo interativo predefinido, o GitPR mostra a linha `🔍 À procura de revisores sugeridos...` enquanto a análise corre, antes de o Publicador de PR abrir. Quando abre, é mostrada uma secção editável **👥 Revisores Sugeridos**:

- Um campo de introdução pré-preenchido com os nomes de utilizador sugeridos do GitHub, separados por vírgulas. Remova um revisor ao limpar o campo; adicione um ao escrever.
- Uma indicação apenas de leitura sob o campo, explicando cada sugestão (linhas e ficheiros tocados, última atividade).
- Deixar o campo vazio não submete revisores nenhuns.

### 3.2 Publicação

Depois de confirmar com F3, o GitPR cria a pull request e depois solicita os revisores aceites no GitHub através do endpoint `requested_reviewers` (`POST .../pulls/{number}/requested_reviewers`). O attach acontece no caminho de criação e no de atualização e **nunca é fatal**: se o GitHub rejeitar o pedido — por exemplo, um handle inválido escrito à mão, respondido com HTTP 422 — a PR permanece publicada e a TUI mostra um aviso (`⚠️ PR publicada, mas não foi possível solicitar os revisores: {error}`).

### 3.3 Ajuda Contextual

A flag participa no sistema de ajuda contextual:

```bash
gitpr -h --no-suggest-reviewers
```

---

## 4. Suporte e Limitações por Forge

| Forge | Sugestão | Submissão |
| --- | --- | --- |
| GitHub | Mostrada e editável | Sim — solicitada via `requested_reviewers` depois de a PR ser criada ou atualizada |
| GitLab | Mostrada apenas localmente | Não — sem endpoint equivalente |
| Bitbucket Cloud | Mostrada apenas localmente | Não — sem endpoint equivalente |
| Azure DevOps | Mostrada apenas localmente | Não — sem endpoint equivalente |

Nos forges que não são GitHub, o campo de introdução não é mostrado; a secção apresenta os candidatos com uma nota de que a sugestão é apenas local. Para transformar e-mails do GitHub em nomes de utilizador, o GitPR resolve cada candidato com best-effort e nunca bloqueia nisso: e-mails do domínio `users.noreply.github.com` são convertidos diretamente num handle e qualquer outro e-mail recorre ao fallback `/search/users in:email` do GitHub. Candidatos cujo e-mail o GitHub não reconhece aparecem com nome e e-mail e simplesmente não são pré-preenchidos — pode sempre escrever o handle deles.

Menos sugestões do que `top_n` é normal: ficheiros sem histórico, ficheiros binários, um diff sem linhas adicionadas ou um repositório recém-criado geram resultados vazios ou parciais com um aviso — nunca um erro. A análise nunca corre nos fluxos `--no-edit`/`--no-publish`, por isso os pipelines automatizados não são afetados.

---

## 5. Para Programadores e Plugins

O use case vive em quatro módulos planos em `src/`: `reviewer_suggestion.py` guarda o domínio puro (dataclasses, pesos, lista de bots, `rank_reviewers()` — sem git, sem rede), `diff_parser.py` implementa `parse_added_lines()` sobre o texto do diff, `blame_engine.py` ganhou a fina `get_blame_for_range()` (o fluxo da arqueologia não foi refatorado) e `suggest_reviewers.py` orquestra tudo com `compute_reviewer_suggestions()`, que **nunca levanta exceção**. As três chaves `GITPR_*` acima estão declaradas no `DEFAULT_CONFIG` em `src/config.py`, com `suggest_reviewers_enabled()` e `get_reviewer_suggestion_settings()`.

No lado do SCM, o contrato base `ScmProvider` ganhou um método **não abstrato** `request_pull_request_reviewers(repo, pr_id, reviewers)` cuja predefinição levanta `ScmNotSupportedError`; apenas o `github_provider.py` o implementa, juntamente com o `email_to_handle()`, exclusivo do GitHub. O `main.py` restringe o cálculo ao fluxo TUI predefinido e entrega à app um dict de view `{"handles", "lines", "submittable", "note"}`. Todo o texto visível passa por chaves i18n `__()`, por isso os 5 pacotes de idioma têm de permanecer sincronizados quando as mensagens mudam.

Registo de decisão de arquitetura e vocabulário canónico: [ADR-002 Sugestão de Revisores](plans/ADR-002-reviewer-suggestion.md) e [Glossário de Sugestão de Revisores](plans/glossary-reviewer-suggestion.md).

> **Nota:** Consulte também a [documentação de publicação de pull requests](pull-request-publication.md) para o fluxo completo de publicação, os seus modos e as suas flags.
