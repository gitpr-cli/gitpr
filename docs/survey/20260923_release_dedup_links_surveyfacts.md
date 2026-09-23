# Survey — `gitpr release`: corte por versão anterior, links e datas

> Levantamento completo da sessão de grill da skill `grill-with-docs`.
> Task: corrigir a repetição de commits/PRs entre versões e enriquecer os bullets com link, data e perfil do contribuidor.
> Data: 2026-09-23 · Branch: `develop_natan`

---

## 1. Contexto da tarefa

O relato do usuário: `gitpr release` está gerando, em **toda** versão nova, todos os commits e PR da versão anterior. O pedido é que cada uma das sete categorias (Funcionalidades, Correções, Performance, Documentação, Refatoração, Tarefas, Outras Alterações) liste **apenas o que for diferente da versão anterior**. Além disso: quando aparecer a hash curta (ex.: `b55df27`), acrescentar o link para o repositório e a data do evento; e, em Contribuidores, linkar cada pessoa ao seu perfil.

O sintoma estava visível no próprio `CHANGELOG.md` do projeto: a seção 1.3.0 saiu com **124 bullets**, sendo que a 1.2.0 tinha 115 — ou seja, 115 dos 124 eram repetição. O `### Resumo` também arrastava conteúdo velho, citando a preparação da 1.1.0.

O escopo desta sessão não é reescrever o gerador: é fixar o desenho correto (grade de decisões Q1–Q8) e só então implementar, sem nova rodada de perguntas de produto.

## 2. Relatório de fatos levantados

Todos os fatos abaixo foram apurados por leitura direta do código e por execução de comandos no repositório real, antes de qualquer decisão ser tomada.

### 2.1 A causa raiz não é a IA — é o range do `git log`

As sete categorias são **100% determinísticas**: quem decide a categoria de cada commit é [src/commit_classifier.py](src/commit_classifier.py) a partir do Conventional Commit, e quem monta o Markdown é [src/changelog_builder.py](src/changelog_builder.py). A IA escreve **apenas** o parágrafo do `### Resumo`. Portanto, nenhuma alteração de prompt resolveria a repetição: o problema está inteiramente em *quais commits entram na lista*.

O range era resolvido por `git describe --tags --abbrev=0`, em [src/release_engine.py:102](src/release_engine.py#L102). Neste repositório esse comando resolve para **`v0.0.8`**: apenas as tags `v0.0.1`…`v0.0.8` são ancestrais de `develop_natan`. As tags `v1.0.0`, `v1.1.0` e `v1.2.0` existem somente em `origin/main` e não são alcançáveis a partir do branch de desenvolvimento.

| Range | Commits |
|---|---|
| `v0.0.8..HEAD` (o que era usado) | **124** |
| `v1.2.0..HEAD` | 9 |
| `6138cf1..HEAD` (hash mais recente do bloco 1.3.0) | 0 |

A aritmética fecha exatamente: 115 (corretos na 1.2.0) + 9 (genuinamente novos) = 124. O gerador estava certo sobre o conteúdo; errado sobre a fronteira.

### 2.2 O `CHANGELOG.md` é a única fonte confiável da fronteira

As tags de versão vivem no branch onde a release foi cortada, que não é necessariamente o branch atual. O `CHANGELOG.md`, ao contrário, viaja com o código: cada seção registra os commits que aquela versão publicou. Por isso a fronteira do range deve vir dele, e não do `git describe`.

Os bullets antigos carregam a hash curta entre parênteses — formato `(a799664)` na era 0.0.x e `([a799664](url))` a partir da mudança de hoje. Um único regex `[\(\[]([0-9a-f]{7,40})[\)\]]` cobre as duas formas.

### 2.3 Já existe no projeto a escada correta para resolver identidade → login

[src/reviewer_resolution.py:48-71](src/reviewer_resolution.py#L48-L71) já resolve nomes/e-mails em logins de forge, e o comentário do próprio código diz qual é o caminho confiável: **`get_commit_author_login(repo, sha)` primeiro** — "funciona para endereços corporativos que a busca de usuários não enxerga" — e `email_to_handle(email)` como fallback.

Esse detalhe foi confirmado na prática: o rodapé da 1.3.0 só ganhou `[@natanfiuza]` depois que a escada completa foi usada. Apenas com `email_to_handle`, a resolução devolvia `None`, porque `natan.fiuza@gmail.com` não aparece na busca pública `in:email` do GitHub — o endereço é privado no perfil. A API de commits, por outro lado, conhece o autor de um commit já publicado.

### 2.4 A URL web não tinha dono

Não existia módulo algum que traduzisse `provider + repo + sha` em URL navegável. O conhecimento de forge estava espalhado e incompleto (o `parse_repo_ref` dá o nome, não a URL). Daí a decisão de criar um módulo puro, sem I/O, e **não** alterar nenhum provider existente.

### 2.5 `upsert_changelog(force=True)` tinha um defeito latente

[src/release_engine.py](src/release_engine.py) delimitava a seção a substituir com `_SECTION_HEADER_RE = re.compile(r"(?m)^#{1,6}\s")` — qualquer nível de heading. Como toda seção começa com `## [x.y.z]` e logo abaixo vem `### Summary`, o "próximo header" era o próprio `### Summary`: o `--force` apagava **apenas a linha do título** e mantinha todo o corpo antigo, que então ficava duplicado sob o título novo. O defeito era pré-existente (idêntico em `HEAD`) e nunca havia aparecido porque o teste que o cobria era fraco demais: ele afirmava `"RENEWED" in content` e `content.count("## [1.2.0]") == 1`, ambas verdadeiras mesmo com o corpo velho preservado.

A fronteira correta é o próximo heading **de nível 2** (`^##\s`), porque `###` é subseção da mesma seção.

### 2.6 O `--format json` estava poluído pelo spinner

O contrato documentado é "stdout puro". Na prática, o `call_ai_model()` era chamado sem `quiet`, e o `Spinner` escreve em **stdout** — o JSON saía precedido de quadros em braille e da palavra "Serializing". Também pré-existente (idêntico em `HEAD`), descoberto por rodar o comando de verdade no repositório em vez de confiar no teste com mock.

### 2.7 Duas duplicações de conteúdo que **não** foram tratadas

- O número do PR aparece duas vezes no bullet quando o assunto já termina em `(#190)`: o classificador extrai o `pr_number` mas **não** remove o sufixo do sujeito. O formato final fica `- add bridges (#190) ([aaaaaaa](url)) — linter · [#190](url) · 2026-09-01`. Decidiu-se não mexer: limpar o sujeito alteraria o texto que o autor escreveu e mudaria a chave do cache MD5.
- O `### Resumo` ainda pode citar versões antigas quando servido do cache MD5. O cache é do prompt; como o conjunto de commits mudou, o cache se renova sozinho na próxima execução sem cache.

### 2.8 Estado pré-existente da suíte (não é regressão desta task)

- **40 chaves `__()` ausentes** nos arquivos de idioma, vindas dos commits `7d84daf` ("test suite generation") e `6138cf1` ("reviewer guide explain").
- **3 falhas** em `TestSkillsSection` / `TestSkillRegistryAgreement` por causa das skills `tests` e `explain`.
- **1 flake sensível a ordem/carga**: `test_pr_publish_linter_modal` passa isolado.
- `python tests/sync_i18n.py` é **destrutivo** neste repositório (trunca 63 chaves por arquivo e descarta traduções). Não deve ser executado.

## 3. Decisões (grade Q1–Q8)

| # | Decisão | Justificativa |
|---|---|---|
| **Q1** | A fronteira do range é **o bloco da versão anterior no `CHANGELOG.md`** | As tags de versão vivem no branch onde a release foi cortada; o changelog viaja com o código (fato 2.2) |
| **Q2** | A âncora é **a hash mais recente dos bullets do bloco anterior**, com a **tag daquela versão como fallback** | Hashes independem de alcançabilidade de tag: o range fica exato mesmo quando a tag não é ancestral do `HEAD` |
| **Q3** | Filtro anti-duplicata contra **todos** os blocos anteriores do changelog, não só o imediatamente anterior | Um changelog editado à mão pode ter sobreposição entre quaisquer seções, não apenas entre vizinhas |
| **Q4** | Login do contribuidor por **`get_commit_author_login` → `email_to_handle`**, com cache em disco | É a escada que o próprio projeto já usa para revisores, e a única que resolve endereços privados (fato 2.3) |
| **Q5** | URLs web em **módulo isolado novo** (`web_links.py`); **nenhum provider existente é alterado** | Mantém a abstração `ScmProvider` intacta e testável sem rede; o módulo é puro |
| **Q6** | Bullet no **formato A**: `- {subject} ([{hash}](url)) — {scope} · [#{n}](url) · {YYYY-MM-DD}` | Data no fim, preservando a posição atual do scope; o PR entra com link, como o usuário pediu |
| **Q7** | Sem âncora derivável → degrada para `git describe` **com aviso visível** | Falhar em silêncio reproduziria exatamente o bug relatado, sem o usuário saber por quê |
| **Q8** | **Regenerar a seção 1.3.0** já poluída no `CHANGELOG.md` | A seção publicada era a evidência do bug; deixá-la como estava manteria 115 bullets falsos em um arquivo versionado |

### Decisões de detalhe

- **Contribuidor não resolvido mantém o nome puro.** Não se inventa link. Azure DevOps não tem URL de perfil simples, então lá todos ficam com o nome.
- **Só acertos entram no cache.** Um erro transitório ou rate limit não pode envenenar `~/.gitpr/cache/contributors.json` para sempre.
- **A resolução nunca levanta.** Sem token, offline ou forge sem lookup, a release sai com nomes puros — nunca falha por causa de um rodapé.
- **Sem contexto de link, a seção degrada para texto puro**: a hash fica sem link, mas a data e o número do PR permanecem. Uma seção nunca é perdida por falha de link.
- **`previous_tag` mantém o nome e passa a carregar a âncora resolvida** (tag **ou** sha), preservando a compatibilidade do `--format json`. O campo novo `previous_version` traz a versão lida do changelog.
- **O baseline do bump semver** passa a ser a versão do bloco anterior, não `_latest_semver_tag()`. De quebra, isso corrige a sugestão de versão, que hoje parte de `v0.0.8` e sugeriria `v0.0.9` em vez de `1.4.0`.

## 4. Fora de escopo (registrado para não virar surpresa)

- A regra não commitada em [.gitpr/skill/.gitpr.release.md](.gitpr/skill/.gitpr.release.md) ("Create the summary and all items in English") é **inerte**: a IA não gera os itens.
- O idioma misto dos cabeçalhos no `CHANGELOG.md` (seguem `GITPR_LANG` em tempo de render) é o comportamento atual e não faz parte do pedido.
- Usar `author.login` da API de commits como alternativa ao `email_to_handle` — a escada já cobre esse caminho.
- Remover o sufixo `(#123)` do sujeito (fato 2.7).

## 5. Verificação no repositório real (fim da implementação)

| Verificação | Resultado |
|---|---|
| `gitpr release --version 1.3.0 --force` | Seção 1.3.0 caiu de **124 → 9 bullets** |
| Commits da 1.2.0 presentes na 1.3.0 | **Nenhum** |
| Bullets com `([hash](url))` | 9 de 9, com `· YYYY-MM-DD` |
| Rodapé | `**Contribuidores:** [@natanfiuza](https://github.com/natanfiuza)` |
| Rodar de novo **sem** `--force` | Aborta com exit 1, arquivo intacto (idempotência preservada) |
| `--format json` | stdout puro (após correção do `quiet`, fato 2.6) |
| Artefato `.gitpr/reports/release/` | 9 bullets, 9 links de commit, rodapé linkado |
