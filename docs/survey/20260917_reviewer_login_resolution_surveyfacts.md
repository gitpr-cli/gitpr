# Survey — resolução do login do revisor sugerido (levantamento de fatos e decisões)

> Sessão `/grill-with-docs` de **2026-09-17**, branch `develop_natan`.
> Tarefa pedida: *"Vamos fazer uma correção no sistema de sugestão de reviewers […] quando digito o nome do reviewer sugerido no campo não aparece no pull request a sugestão no forge (testei com o github), corrija"*.
> Plano gerado e aprovado: `C:\Users\nataniel\.claude\plans\vamos-fazer-uma-corre-o-misty-aho.md` (plan mode).
> Base de domínio: [ADR-002-reviewer-suggestion.md](../plans/ADR-002-reviewer-suggestion.md) e [glossary-reviewer-suggestion.md](../plans/glossary-reviewer-suggestion.md).

## 1. Contexto da tarefa

A feature "Suggested Reviewers" (ADR-002) mostra no PR Publisher (TUI) um campo editável com os revisores
sugeridos pelo `git blame`. O usuário relata que **digitar o nome do revisor sugerido no campo não faz o
revisor aparecer no PR do GitHub**.

O sintoma é real e a causa é uma **falha silenciosa**: o campo nasce pré-preenchido apenas com *handles*
resolvidos por `provider.email_to_handle()` — que só enxerga e-mails `users.noreply.github.com` ou com
e-mail **público** no GitHub. Com e-mail corporativo nada resolve, o `Input` nasce **vazio**, e o hint
mostra apenas o **nome**. O usuário digita exatamente o que a UI mostrou, e a CLI envia esse nome
**verbatim** como se fosse login.

### Evidência (log real do usuário)

`~/.gitpr/logs/pr_desc/pr_desc_w7YW-kabx4-8xAg.log`:

```
[2026-09-16 19:06:08] PR created successfully: .../SIG-Novo/pull/1068, number=1068
[2026-09-16 19:06:10] Reviewers requested on PR #1068: ['Eduarda Leal']
```

A linha só é escrita **depois** que `_request()` retorna sem levantar, e ele levanta para qualquer status
fora de `{201}`. Logo: **o GitHub respondeu 201 e não anexou ninguém**. Nenhum aviso chegou ao usuário —
o `final_message` só aparece depois de a TUI fechar e o fluxo segue direto para o prompt de merge.

O log da execução seguinte (`pr_desc_S1IN-sjW6H-jIk1.log`, 2026-09-17) confirma o mesmo caminho **sem** a
linha de reviewers: o campo foi submetido vazio, e nada foi reportado.

## 2. Fatos levantados

### 2.1 — Por que o prefill nasce vazio

| Fato | Onde |
|---|---|
| `_reviewer_suggestion_view()` monta `handles` só com `provider.email_to_handle(candidate.author_email)` | `src/main.py:2471-2515` |
| `email_to_handle()` = parse de `users.noreply.github.com` **ou** `GET /search/users?q={email} in:email` | `src/infrastructure/scm/github_provider.py:367-392` |
| `/search/users in:email` só encontra quem tem e-mail **público** no perfil | GitHub REST docs (pesquisa) |
| O hint exibe `candidate.author_name` — a **única** identidade oferecida pela UI quando o handle não resolve | `src/suggest_reviewers.py:107-123` |

Medido no repo real (SIG-Novo): `eduardaleal@grafjb.com.br` e `lealduda03@gmail.com` — nenhum resolve.

### 2.2 — O que a CLI envia

`_parsed_reviewers()` (`src/ui/pr_publish_app.py:746-766`) lê o `Input` e devolve os valores **crus**,
separados por vírgula. `_attach_reviewers()` (`:768-792`) repassa direto para
`provider.request_pull_request_reviewers(repo_ref, pr_number, reviewers)` — **nenhuma validação**.

### 2.3 — Fatos de API (pesquisa)

| Fato | Consequência no desenho |
|---|---|
| O corpo do `201` de `POST …/pulls/{n}/requested_reviewers` traz `requested_reviewers` | Dá para **ler de volta** quem foi realmente anexado, sem chamada extra |
| `GET /repos/{o}/{r}/commits/{sha}` devolve `author.login` (conta ligada ao e-mail do commit) | É a via de resolução pelo **commit do blame** — funciona sem e-mail público |
| O mesmo `author` vem `null` ou `{}` quando não há conta ligada ao e-mail | Resolução devolve `None` sem erro |
| Login **inexistente** → `201` **ignorado** (empírico: o log acima) | Explica a falha silenciosa — *não* é 422 |
| Usuário **existente mas inelegível** (autor do PR, não-colaborador) → `422` **tudo-ou-nada** | Um item ruim derruba o lote inteiro → reenvio um a um |

**Tensão registrada em aberto:** a documentação do GitHub descreve `422` para não-colaboradores e **não**
descreve o `201` ignorado para login inexistente. O comportamento do `201` é **empírico** (vem do log do
usuário, não da doc); o do `422` é documentado. O desenho cobre os dois caminhos.

### 2.4 — Bug secundário achado de passagem

`src/main.py` indexa o `who_map` pelo **e-mail cru** (`who_map[candidate.author_email] = f"@{handle}"`)
enquanto `format_suggestion_lines()` consulta por `normalize_email(candidate.author_email)`
(`src/suggest_reviewers.py:126-139`). Um e-mail com maiúscula esconde o `@handle` do hint — mesma família
do bug principal (identidade mal normalizada). Corrigido na mesma entrega.

### 2.5 — Estado do TUI e da i18n

- `CommitConfirmScreen` é semântica **Yes/No** e o modal de erro oferece "Try Again" — nenhum dos dois
  serve para "publicado, com ressalvas". Precisa de um `NoticeScreen` novo (um botão, "Close").
- `_publish_pr_from_progress` roda **na app thread** (`call_from_thread`, `:1119`); `_push_and_exit` roda
  em **worker** (`_do_push`) — o DOM não é consultável de worker e `call_from_thread` **levanta** se
  chamado da própria app thread (Textual 8.2.8).
- `tests/test_i18n.py` exige paridade **exata** de chaves nos 6 pacotes `langs/*.json` (AST), sem órfãs.
  `tests/sync_i18n.py` é regex e **mishandles** concatenação implícita de strings → uma literal por linha.

## 3. Decisões do grill (4 rodadas)

### Rodada 1 — o que o campo aceita e o que a UI promete

| # | Questão | Decisão |
|---|---|---|
| Q1 | O campo aceita só login, ou também nome/e-mail? | **Login, nome ou e-mail** — o valor é resolvido para login antes de submeter |
| Q2 | Como saber quem foi realmente anexado? | **Read-back** do corpo do `201` (`requested_reviewers`) |
| Q3 | Item que não resolve: some ou avisa? | **Avisa e mantém o campo** — o usuário pode corrigir e reenviar |
| Q4 | Onde entram os textos novos? | **Chaves novas nos 6 pacotes** `langs/*.json` |

### Rodada 2 — como resolver a identidade

| # | Questão | Decisão |
|---|---|---|
| Q5 | Qual a via primária de resolução? | **O commit do blame**: `GET /repos/{o}/{r}/commits/{sha}` → `author.login` |
| Q6 | Onde a resolução acontece? | **Antes da TUI** (prefill + hint) e **validação no attach** do que foi digitado |
| Q7 | O que fazer com o item que não resolve? | **Pular e reportar com o motivo** — nunca enviar como veio |
| Q8 | O que `request_pull_request_reviewers()` devolve? | **A lista de logins efetivamente anexados** |

### Rodada 3 — casamento, UX e documentação

| # | Questão | Decisão |
|---|---|---|
| Q9 | Casamento do que foi digitado com os candidatos | **Exato e normalizado** (strip + casefold) — **sem fuzzy** |
| Q10 | Quem é o autor do PR? *(reformulada na Q13)* | ~~Resolver com `GET /user`~~ → **sem** `GET /user` no caminho feliz |
| Q11 | Como o aviso de falha parcial chega ao usuário? | **Modal no TUI** que precisa ser fechado, **+** a linha no `final_message` |
| Q12 | Sem login resolvido, o que o hint mostra? | A pessoa + **aviso i18n**; o `Input` continua disponível |
| Q13 | Forges não-GitHub | **Inalterados** (`submittable=False`, sem Input, nota local-only) |

### Rodada 4 — borda do 422 e entregáveis

| # | Questão | Decisão |
|---|---|---|
| Q14 | Lote com `422` (tudo-ou-nada) | **Reenviar um a um**, anexando os bons e reportando os ruins com a mensagem do GitHub |
| Q15 | Cobertura de documentação | Família `docs/suggested-reviewers.*` (**5 cópias**), emenda no ADR-002, glossário, relatório |

**Decisão reaberta (transparência):** a Q10 original partia da premissa de que o read-back reportaria o
autor do PR. A pesquisa mostrou que o caso do autor/não-colaborador é um `422` que **derruba o lote
inteiro** — a premissa não sobreviveu. Em vez de mudar a decisão em silêncio, a questão foi **reaberta** e
reformulada na Q13/Q14, e a solução passou a ser o reenvio um a um.

### Não-objetivos

- Nenhuma chave de config nova (seguem as 3 do ADR-002).
- Nada muda em `--no-edit` / `--no-publish` — esses caminhos nunca calculam sugestão.
- Sem cache da resolução (inputs são por execução; o caminho não passa pelo cache MD5 de IA).
- `PullRequestRequest.reviewers` continua **morto** — o GitHub não aceita reviewers no payload de create.

## 4. Resultado

Plano aprovado em plan mode (13 decisões fechadas, 8 blocos de implementação na ordem de execução, testes
incluindo a **regressão do bug relatado**, e verificação com baseline `GITPR_LANG=en_us`: 1277 passed,
2 skipped, 4 failed — todos os 4 pré-existentes e fora do escopo).

A prova de ponta a ponta fica no repo real (SIG-Novo): publicar um PR e conferir o prefill com `@login`,
o hint marcando quem não tem login, o revisor aparecendo em *Reviewers* no PR, o `NoticeScreen` no caso
parcial, e a linha `Reviewers requested on PR #N: [...] -> attached [...]` no log.

Nada é commitado — as mudanças ficam na árvore de trabalho (regra do `CLAUDE.md`).
