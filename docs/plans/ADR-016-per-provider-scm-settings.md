# ADR-016 — Forge por repositório e credencial por provider

- **Status:** Aceito
- **Data:** 2026-11-07
- **Contexto:** bug report de uso real (dois repositórios, GitLab e GitHub, na mesma máquina)
- **Glossário:** [glossary-scm-multiforge.md](glossary-scm-multiforge.md)
- **Supera em parte:** [ADR-001-scm-abstraction.md](ADR-001-scm-abstraction.md) (configuração global e fallback de token)

## Contexto

O ADR-001 guardou a configuração SCM num par **global** em `~/.gitpr/.env`:
`GITPR_SCM_PROVIDER` (o forge ativo) e `GITPR_SCM_TOKEN_ENCRYPTED` (o token).
Isso funciona para uma máquina com um único forge, que era o caso do GitHub
legado, mas quebra no uso real da ferramenta:

1. `gitpr --init` num repositório GitLab grava `GITPR_SCM_PROVIDER=gitlab`
   para a **máquina inteira**. De volta a um repositório GitHub, `main.py`
   injetava a chave do `.env` por cima da detecção do remote
   (`settings["provider"] = detect_provider_from_remote(...)` era sobrescrito),
   então o GitPR falava com a API errada e procurava um token que nunca foi
   configurado.
2. Existia **um único slot** de token. Dois forges na mesma máquina exigiam
   trocar o token à mão a cada repositório.
3. `base_url` vazava: `resolve_scm_provider(config)` repassava `base_url` para
   **qualquer** provider, então um `GITPR_SCM_BASE_URL` de GitLab self-hosted
   apontava o GitHub para a API errada.

A causa comum é tratar como propriedade **da máquina** algo que é propriedade
**do repositório**.

## Decisão

O forge passa a ser resolvido **por repositório**, e cada forge ganha o seu
próprio slot de credencial. Dez decisões vinculantes:

1. **Precedência** — `scm.provider` no `.gitpr/conf/gitpr.config.yml` →
   detecção do remote `origin` → `github`. Override explícito **sempre** vence
   (permite corrigir uma detecção errada, ex.: GitLab self-hosted sem
   "gitlab" no domínio).
2. **Detecção distingue reconhecido de desconhecido** —
   `detect_provider_from_remote(url, default=None)`: `None` significa "este
   remote não nomeia forge nenhum", e só aí o wizard pergunta. Chamadas de um
   argumento continuam devolvendo `github`, então nenhum outro call site muda.
3. **Token cifrado por provider** —
   `GITHUB_TOKEN_ENCRYPTED` (nome preservado), `GITLAB_TOKEN_ENCRYPTED`,
   `BITBUCKET_TOKEN_ENCRYPTED`, `AZURE_DEVOPS_TOKEN_ENCRYPTED`. O
   `GITPR_SCM_TOKEN` **cru** continua único e global e é consultado primeiro
   (é o override de CI/CD, não uma credencial de repositório).
4. **`base_url` por provider** — `GITHUB_BASE_URL`, `GITLAB_BASE_URL`,
   `BITBUCKET_BASE_URL`, `AZURE_DEVOPS_BASE_URL`. Um forge nunca herda o host
   de outro.
5. **Extras continuam globais** — `GITPR_SCM_ORGANIZATION`,
   `GITPR_SCM_PROJECT` e `GITPR_SCM_USERNAME`, porque cada um é lido por
   exatamente um provider.
6. **Migração one-shot** na primeira chamada do resolvedor: move o par legado
   para o slot do forge que ele nomeia, **nunca** sobrescreve um
   `<PROVIDER>_TOKEN_ENCRYPTED` já preenchido, remove as três linhas antigas e
   é idempotente. Falha de escrita não quebra o comando: o valor migrado vale
   para o processo atual e a próxima execução tenta de novo.
7. **As chaves legadas somem do vocabulário** — `GITPR_SCM_PROVIDER`,
   `GITPR_SCM_TOKEN_ENCRYPTED` e `GITPR_SCM_BASE_URL` saem do schema, do seed,
   da TUI e de todas as leituras. Não existe ramo "legado" em nenhum leitor;
   a migração do item 6 é a única transição.
8. **Token ausente** — em execução interativa o GitPR pede, valida e salva na
   hora; em hooks, MCP e CI falha com uma mensagem que aponta `gitpr --init`
   para aquele repositório.
9. **`gitpr --init` vira wizard do repositório** — grava o override no arquivo
   de projeto **somente** quando o forge escolhido difere do detectado, e
   grava o token no slot do forge escolhido.
10. **Todas as superfícies SCM** (publicação de PR/issues, `release --publish`,
    `metrics` ciclo, MCP) passam pelo mesmo resolvedor (`src/scm_settings.py`).

### Alternativas consideradas

| Alternativa | Veredito |
|---|---|
| Manter o slot global e pedir `--provider` em cada comando | Rejeitada — o usuário teria de declarar o forge a cada execução; o remote já sabe a resposta. |
| Tokens por repositório no keyring do sistema | Adiada — resolve "dois tokens do mesmo forge na mesma máquina", mas exige dependência nativa e não resolve o forge como propriedade do repositório. Fica para um ADR futuro. |
| Um arquivo por forge (`~/.gitpr/scm.d/gitlab.env`) | Rejeitada — duplica a camada dotenv, o Fernet e a TUI para ganhar o que um prefixo de chave já dá. |
| Inferir o token do forge a cada chamada, sem migração | Rejeitada — é exatamente o bug atual: um token global usado para o forge de outro repositório. |
| Gravar o override no arquivo de projeto **sempre** | Rejeitada — sujaria o arquivo versionado de todo repositório, e a detecção do remote já acerta o caso comum. |

## Consequências

**Positivas:**
- Uma máquina atende GitHub, GitLab, Bitbucket e Azure ao mesmo tempo, um
  token por forge, sem troca manual.
- O forge deixa de depender da ordem dos `gitpr --init` na máquina: cada
  repositório resolve o seu.
- O `base_url` de um forge não contamina os outros.

**Negativas / custos (quebra intencional):**
- Quem tinha um token não-GitHub no slot global passa a tê-lo num único slot
  de forge após a migração. Os outros repositórios do **mesmo** forge
  reutilizam o mesmo token; repositórios de **outro** forge pedem o token uma
  vez (interativo) ou falham com "run `gitpr --init`" (CI, hooks, MCP).
- Um remote que não contenha o nome do forge na URL (ex.: GitLab self-hosted
  em `git.empresa.com`) resolve para `github` depois da migração. A migração
  emite um aviso, e o `gitpr --init` grava o override no projeto.
- HOME somente leitura degrada com aviso; o token vale para o processo atual.

**Fora de escopo:** um token por **repositório** do mesmo forge (keyring),
duas organizações Azure na mesma máquina (`GITPR_SCM_ORGANIZATION`/`PROJECT`
seguem globais), GitHub Enterprise Server e Bitbucket Server/DC além do
`*_BASE_URL` manual, e o shim `src/github_api.py` com o `get_github_token()`.
