# Documentação Técnica: Revisores Sugeridos para Pull Requests

Ao publicar um Pull Request pelo publicador interativo do GitPR (modo padrão `gitpr`), o GitPR sugere quem deve revisá-lo: ele identifica as pessoas que trabalharam no código que você está alterando e propõe até `GITPR_REVIEWER_SUGGESTION_TOP_N` candidatos (3 por padrão). As sugestões aparecem em um campo editável do Publicador de PR (TUI) e, no GitHub, são enviadas ao novo pull request logo após a sua criação.

O cálculo vem habilitado por padrão e roda somente no fluxo do publicador interativo — nunca com `--no-edit` nem `--no-publish`. Ele é puramente consultivo e totalmente não bloqueante: qualquer falha ou situação não suportada vira um aviso e o fluxo de publicação continua inalterado.

---

## 1. Como Funciona

O GitPR não adivinha: ele atribui autoria real com `git blame`, executado sobre as linhas exatas que o seu diff adicionou, comparando a branch base com a sua working tree.

### 1.1 Autoria sobre as Linhas Adicionadas

- A entrada é o mesmo diff que o GitPR já calculou para o PR: branch base vs. working tree (mudanças staged incluídas), com os smart-excludes aplicados. O parser consome esse texto e nunca re-executa `git diff`.
- Somente **linhas adicionadas** (`+`) contam para a autoria. Linhas removidas e de contexto são ignoradas.
- Linhas ainda não commitadas — "Not Committed Yet", hash de blame `0000…` — são puladas: é o seu próprio trabalho em andamento.
- O blame roda sobre a working tree (sem revisão), então casa exatamente com o diff, incluindo arquivos staged e novos.
- Arquivos sem histórico utilizável (novos, binários, clones shallow) não geram candidatos: um aviso é exibido e a análise segue adiante.

### 1.2 Classificação e Exclusões

Cada autor encontrado é agregado por arquivo e por linha e recebe uma pontuação:

| Fator | Peso | Significado |
| --- | --- | --- |
| Linhas tocadas | 50% | Participação nas linhas adicionadas do diff escritas pela pessoa |
| Arquivos tocados | 30% | Participação nos arquivos alterados em que a pessoa tem autoria |
| Recência | 20% | `1 / (1 + days / 90)` — meia-vida de 90 dias desde o último toque |

O autor do PR é sempre excluído, mesmo quando domina o diff. **Bots** também são excluídos: qualquer identidade cujo nome ou a parte local do e-mail termine em `[bot]`, ou cujo e-mail esteja na lista de bots conhecidos (Dependabot, GitHub Actions etc.). O domínio `users.noreply.github.com` nunca é tratado como bot — é o e-mail padrão de usuários reais do GitHub. Pessoas adicionais podem ser excluídas via `GITPR_REVIEWER_SUGGESTION_EXCLUDED`. Empates são desfeitos por linhas tocadas e o resultado é truncado no `top_n` configurado (padrão 3).

---

## 2. Configuração

O recurso vem habilitado por padrão. Desative-o por execução com a flag ou globalmente pelo ambiente:

```bash
gitpr --no-suggest-reviewers        # Desativa o cálculo nesta execução
```

```bash
# ~/.gitpr/.env — desativa globalmente e ajusta a classificação
GITPR_SUGGEST_REVIEWERS=false
GITPR_REVIEWER_SUGGESTION_TOP_N=5
GITPR_REVIEWER_SUGGESTION_EXCLUDED=renovate[bot],qa@example.com
```

| Variável | Padrão | Descrição |
| --- | --- | --- |
| `GITPR_SUGGEST_REVIEWERS` | `true` | Interruptor geral. Valores falsy: `false`, `0`, `no`, `off`, `n` |
| `GITPR_REVIEWER_SUGGESTION_TOP_N` | `3` | Quantos candidatos sugerir; inválido ou ≤ 0 volta para 3 |
| `GITPR_REVIEWER_SUGGESTION_EXCLUDED` | *(vazio)* | CSV opcional de e-mails ou nomes a excluir, além do autor do PR e dos bots |

As chaves são lidas de `~/.gitpr/.env` e nunca são gravadas automaticamente. `--no-edit` e `--no-publish` nunca calculam sugestões, independentemente da configuração.

---

## 3. Revisores Sugeridos no Publicador de PR (TUI)

### 3.1 A Seção de Revisores Sugeridos

No fluxo interativo padrão, o GitPR exibe a linha `🔍 Procurando revisores sugeridos...` enquanto a análise roda, antes de o Publicador de PR abrir. Quando ele abre, uma seção editável **👥 Revisores Sugeridos** é exibida:

- Um campo de entrada pré-preenchido com os nomes de usuário sugeridos do GitHub, separados por vírgula. Remova um revisor limpando o campo; adicione um digitando.
- Uma dica somente leitura abaixo do campo explicando cada sugestão (linhas e arquivos tocados, última atividade).
- Deixar o campo vazio não submete revisor nenhum.

### 3.2 Publicação

Depois de confirmar com F3, o GitPR cria o pull request e então solicita os revisores aceitos no GitHub pelo endpoint `requested_reviewers` (`POST .../pulls/{number}/requested_reviewers`). O attach acontece no caminho de criação e no de atualização e **nunca é fatal**: se o GitHub rejeitar a solicitação — por exemplo, um handle inválido digitado à mão, respondido com HTTP 422 — o PR permanece publicado e a TUI mostra um aviso (`⚠️ PR publicado, mas não foi possível solicitar os revisores: {error}`).

### 3.3 Ajuda Contextual

A flag participa do sistema de ajuda contextual:

```bash
gitpr -h --no-suggest-reviewers
```

---

## 4. Suporte e Limitações por Forge

| Forge | Sugestão | Envio |
| --- | --- | --- |
| GitHub | Exibida e editável | Sim — solicitada via `requested_reviewers` depois de o PR ser criado ou atualizado |
| GitLab | Exibida apenas localmente | Não — sem endpoint equivalente |
| Bitbucket Cloud | Exibida apenas localmente | Não — sem endpoint equivalente |
| Azure DevOps | Exibida apenas localmente | Não — sem endpoint equivalente |

Nos forges que não são GitHub, o campo de entrada não é exibido; a seção mostra os candidatos com uma nota de que a sugestão é apenas local. Para transformar e-mails do GitHub em nomes de usuário, o GitPR resolve cada candidato com best-effort e nunca bloqueia nisso: e-mails do domínio `users.noreply.github.com` são convertidos diretamente em handle e qualquer outro e-mail cai no fallback `/search/users in:email` do GitHub. Candidatos cujo e-mail o GitHub não reconhece aparecem com nome e e-mail e simplesmente não são pré-preenchidos — você ainda pode digitar o handle deles.

Menos sugestões que `top_n` é normal: arquivos sem histórico, arquivos binários, um diff sem linhas adicionadas ou um repositório recém-criado geram resultados vazios ou parciais com um aviso — nunca um erro. A análise nunca roda nos fluxos `--no-edit`/`--no-publish`, então pipelines automatizados não são afetados.

---

## 5. Para Desenvolvedores e Plugins

O use case vive em quatro módulos planos em `src/`: `reviewer_suggestion.py` guarda o domínio puro (dataclasses, pesos, lista de bots, `rank_reviewers()` — sem git, sem rede), `diff_parser.py` implementa `parse_added_lines()` sobre o texto do diff, `blame_engine.py` ganhou a fina `get_blame_for_range()` (o fluxo da arqueologia não foi refatorado) e `suggest_reviewers.py` orquestra tudo com `compute_reviewer_suggestions()`, que **nunca levanta exceção**. As três chaves `GITPR_*` acima são declaradas no `DEFAULT_CONFIG` em `src/config.py`, com `suggest_reviewers_enabled()` e `get_reviewer_suggestion_settings()`.

No lado do SCM, o contrato base `ScmProvider` ganhou um método **não abstrato** `request_pull_request_reviewers(repo, pr_id, reviewers)` cujo padrão levanta `ScmNotSupportedError`; apenas o `github_provider.py` o implementa, junto com o `email_to_handle()`, exclusivo do GitHub. O `main.py` restringe o cálculo ao fluxo TUI padrão e entrega ao app um dict de view `{"handles", "lines", "submittable", "note"}`. Todo texto visível passa por chaves i18n `__()`, então os 5 pacotes de idioma precisam ficar sincronizados quando mensagens mudam.

Registro de decisão de arquitetura e vocabulário canônico: [ADR-002 Sugestão de Revisores](plans/ADR-002-reviewer-suggestion.md) e [Glossário de Sugestão de Revisores](plans/glossary-reviewer-suggestion.md).

> **Nota:** Consulte também a [documentação de publicação de pull requests](pull-request-publication.md) para o fluxo completo de publicação, seus modos e suas flags.
