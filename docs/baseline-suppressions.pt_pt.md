# Documentação Técnica: Baseline e Supressões Auditáveis (`gitpr baseline`)

Adotar o GitPR num repositório legado é o momento em que a ferramenta é menos útil: o linter reporta quatrocentos problemas pré-existentes, o ruleset de segredos assinala uma chave sintética num fixture de teste, e o primeiro pull request da migração falha num portão que não tem nada a ver com a alteração que está nele. A equipa tem duas opções, e as duas são más — desligar o portão, ou gastar um sprint a corrigir código que ninguém está a mexer.

Um **baseline** é a terceira opção. É um ficheiro, commitado no Git, que regista os apontamentos que o repositório já tem. A partir daí uma execução classifica cada apontamento que encontra: os que estão no ficheiro são **existing**, os que estavam lá e desapareceram são **resolved**, e só o que *esta alteração* introduziu é **new** — e só `new` bloqueia. O portão passa a ser uma afirmação sobre o diff em vez de uma afirmação sobre a história do repositório.

Junto com o registo vem a trilha de auditoria: uma supressão não é um filtro silencioso, é uma decisão com **motivo**, autor e data; a dívida aceite tem **responsável** e, opcionalmente, **prazo**; e um checksum sobre o ficheiro inteiro apanha uma edição feita fora do GitPR. Tudo o que a ferramenta decide sobre um apontamento pode ser lido de volta e questionado.

Sem um ficheiro de baseline, todo comando comporta-se exatamente como antes desta funcionalidade existir — mesma saída, mesmos exit codes, mesmas chaves de cache.

---

## 1. Visão Geral

```bash
gitpr baseline create                    # Regista o diff atual como baseline
gitpr baseline show                      # Os apontamentos, as decisões e as contagens
gitpr baseline validate                  # Todo defeito do ficheiro, exit 1 em qualquer um
gitpr baseline update                    # Regista o que o diff mostra hoje, mantendo decisões
gitpr baseline suppress <id> --reason "…"    # Uma decisão sobre um apontamento
gitpr baseline unsuppress <id>           # Desfaz uma decisão
```

| Comando | Escreve | Descrição |
|---|---|---|
| **`create`** | `.gitpr/baseline.json` | Regista os apontamentos do diff atual como ponto de partida. `--base <ref>` regista o diff contra uma ref em vez da árvore de trabalho; `--refresh` corre a revisão de IA de novo em vez de reutilizar a em cache; `--format json` para CI |
| **`show`** | — | Contagens por status e a lista de todo apontamento que carrega uma decisão, com motivo, escopo e origem. `--status`, `--rule`, `--file` filtram; `--format json` emite as entradas |
| **`validate`** | — | Todo problema que o ficheiro e os overrides podem ter: schema, versão de fingerprint, compatibilidade, checksum, fingerprints duplicados, campos desconhecidos, dívida vencida. Exit 1 em qualquer um deles |
| **`update`** | `.gitpr/baseline.json` | Regista de novo o que o diff mostra hoje, marcando o que desapareceu como `resolved` e mantendo cada decisão. Recusa um ficheiro cujo checksum divergiu, a menos que `--recompute` seja dado |
| **`suppress`** | a entrada, ou `.gitpr/baseline.overrides.yml` | Regista uma decisão sobre um apontamento. `--reason` é obrigatório; `--scope finding\|line\|file\|rule`; `--debt --owner <quem> [--due-date YYYY-MM-DD]` regista dívida em vez de supressão |
| **`unsuppress`** | a entrada, ou o ficheiro de overrides | Desfaz uma decisão. Uma decisão mais ampla do que aquele apontamento é *reportada*, nunca apagada — é editada onde vive |

Todo comando de escrita aceita `--yes`, que responde ao prompt de confirmação sem saltar as verificações que estão atrás dele. Sem terminal e sem `--yes` o comando falha com a instrução, em vez de ficar preso num prompt que ninguém vai ler.

### 1.1 Ids de apontamento

Um apontamento é nomeado na linha de comando por um **prefixo único do seu fingerprint**, que o `show` imprime e o `suppress` aceita:

```
sha256:ab12cd34ef56…
```

Um id que não corresponde a nenhum apontamento, ou a dois, é recusado — e a recusa diz qual dos dois casos foi, porque o id é a única pega que o utilizador tem sobre o apontamento.

---

## 2. Os cinco status

| Status | Significado | Persistido |
|---|---|---|
| **`new`** | O apontamento não está no baseline. É o ponto inteiro da funcionalidade, e o único status que bloqueia | **nunca** |
| **`existing`** | O apontamento está registado e continua lá. Nada é dito sobre ele ser bom ou mau — é conhecido | sim |
| **`resolved`** | O apontamento estava registado e não aparece mais, num ficheiro que o diff atual toca | sim |
| **`ignored`** | Um humano olhou e decidiu que ele fica, com um motivo | sim |
| **`accepted_debt`** | Um humano decidiu que ele será corrigido, com um responsável e um motivo declarado — e opcionalmente um prazo | sim |

`new` nunca é gravado no ficheiro: uma entrada guardada como "new" estaria obsoleta na execução seguinte, e um ficheiro que regista a própria comparação é um ficheiro que mente.

`resolved` só é aplicado a entradas cujo **ficheiro aparece no diff atual**. Um ficheiro fora do diff pode estar intocado por razões que não têm nada a ver com o apontamento — o diff simplesmente não chega até ele — e chamar a isso "resolved" seria uma afirmação falsa no único sítio que a equipa lê como registo. A regra mais estreita faz com que um diff que encolhe nunca invente uma resolução.

---

## 3. O que bloqueia, e quanto custa

| Superfície | Efeito do baseline |
|---|---|
| `gitpr -l` / `--linter` | Sai com 1 só quando um apontamento de nível **error** é `new`. Apontamentos existing, ignored e accepted aparecem com o seu status e o seu motivo, e a execução continua |
| `gitpr -r`, `-f`, `-i` | A revisão anota cada apontamento com o seu status. A revisão nunca foi um portão, por isso nenhum exit code muda |
| `gitpr risk` | Só apontamentos `new` pontuam. Todo o resto é anexado como evidência informativa que vale **zero pontos**, com o status em `details`, para que o número de risco descreva a alteração em vez do repositório |
| `gitpr review-pr` | Resolve a política e o baseline por conta própria, anotando os apontamentos do linter, a secção de risco e o comentário do PR |
| Todo o resto (`-c`, descrição de PR, blame, issue, chat, release, split, fix) | O baseline não é consultado de forma alguma |

Um aviso destrutivo, um alerta ignorado ou um prazo vencido nunca falham uma execução sozinhos: um prazo vencido é um aviso, impresso ao lado do relatório.

---

## 4. Configuração

Quatro variáveis em `~/.gitpr/.env`, também editáveis pelo `gitpr config` na secção **Baseline**:

| Chave | Predefinição | Efeito |
|---|---|---|
| `GITPR_BASELINE_ENABLED` | `true` | `false` → nenhuma execução lê o baseline; o comportamento de antes da funcionalidade, byte a byte |
| `GITPR_BASELINE_PATH` | *(vazio)* | `.gitpr/baseline.json` por predefinição. Um caminho relativo é resolvido a partir da raiz do repositório — é assim que se aponta para um monorepo ou para um baseline partilhado noutro sítio |
| `GITPR_BASELINE_REQUIRE_LOCKFILE_CHECKSUM_MATCH` | `true` | Um checksum divergente torna o baseline inutilizável: a execução recusa, imprime a instrução e sai com código diferente de zero nos fluxos que bloqueiam. Com ele desligado o ficheiro é aplicado e a divergência ainda é reportada como aviso |
| `GITPR_BASELINE_ALLOW_LOCAL_OVERRIDES` | `true` | `false` → `.gitpr/baseline.overrides.yml` não é lido, com um aviso. As decisões gravadas no ficheiro de baseline ficam sozinhas |

A chave mestra falha aberta — só `false`, `0`, `no`, `off` ou `n` a desligam.

---

## 5. O ficheiro

`.gitpr/baseline.json`, commitado junto com o código:

```json
{
  "schema_version": 1,
  "fingerprint_version": "1",
  "policy_name": "acme/team-policy",
  "policy_version": "1.0.0",
  "gitpr_version": "0.0.37",
  "created_at": "2026-10-10T09:12:44+00:00",
  "updated_at": "2026-10-10T09:12:44+00:00",
  "checksum": "sha256:…",
  "entries": [
    {
      "fingerprint": "sha256:…",
      "rule_id": "sec-aws-key",
      "category": "security",
      "file_path": "tests/fixtures/keys.py",
      "line_start": 18,
      "line_end": 18,
      "severity": "error",
      "source": "linter",
      "status": "ignored",
      "low_confidence": false,
      "first_seen_commit": "a1b2c3d",
      "last_seen_commit": "a1b2c3d",
      "first_seen_date": "2026-10-10",
      "last_seen_date": "2026-10-10",
      "resolved_at": null,
      "suppressed": true,
      "suppression_reason": "Synthetic key in a fixture; never used to reach a service.",
      "suppression_scope": "finding",
      "suppressed_by": "alice",
      "suppressed_at": "2026-10-10",
      "accepted_debt_owner": null,
      "accepted_debt_due_date": null,
      "accepted_debt_reason": null,
      "provenance": {"origin": "local", "command": "baseline suppress", "policy": null}
    }
  ]
}
```

Três propriedades do formato importam:

1. **Nenhuma entrada guarda mensagem, e nenhuma guarda código.** A prosa que uma regra emite pertence à regra — reescrevê-la pareceria uma alteração de baseline — e o baseline é commitado no Git, por isso persistir a linha ofensora colocaria no repositório justamente o segredo que o ruleset assinalou. Só um *digest* dessa linha é guardado.
2. **As entradas são gravadas em ordem de fingerprint.** O ficheiro é commitado, e duas execuções sobre os mesmos apontamentos em duas máquinas têm de produzir o mesmo diff.
3. **O checksum não se cobre a si mesmo.** É o SHA-256 do JSON canónico (chaves ordenadas, sem espaços, entradas ordenadas) de todos os outros campos. Editar uma entrada à mão num editor — mudar um número de linha, trocar um status — quebra-o, e o `gitpr baseline validate` nomeia a divergência em vez de aplicar o ficheiro.

`gitpr baseline update --recompute` é a forma sancionada de aceitar um ficheiro editado à mão: reescreve o checksum sobre o conteúdo que encontra, para que a edição se torne uma alteração na história do Git com um commit atrás, em vez de uma divergência silenciosa.

---

## 6. O fingerprint

Um apontamento é identificado por um SHA-256 sobre oito linhas, nesta ordem:

```
1  FINGERPRINT_VERSION      ("1")
2  rule_identity            o rule id, ou "category:<categoria>" quando não há
3  category                 em minúsculas
4  normalize_path           relativo ao repo, barras normais, minúsculas
5  source                   linter | ai | external | …
6  line_start
7  line_end
8  snippet_hash             digest da linha ofensora, com espaços colapsados
```

Deliberadamente **fora** do payload: a mensagem, o timestamp, o provider e o modelo, a branch, o caminho absoluto do checkout. Duas execuções sobre a mesma revisão produzem o mesmo fingerprint em qualquer máquina, e um build num caminho diferente não muda nada.

O que isto significa na prática:

| Alteração | Efeito |
|---|---|
| A mensagem da regra é reescrita | Mesmo fingerprint — uma mensagem não é uma identidade |
| A linha é reindentada ou espaçada de outra maneira | Mesmo fingerprint — os espaços são colapsados antes do hash |
| O conteúdo da linha muda | **Fingerprint novo** — uma linha diferente é um apontamento diferente |
| Uma linha é inserida acima do apontamento, deslocando-o | **Fingerprint novo** — os números de linha fazem parte da identidade |
| O ficheiro é renomeado | **Fingerprint novo** — o caminho faz parte da identidade |
| A análise corre noutra máquina, outra branch, outro provider | Mesmo fingerprint |
| O apontamento vem da IA e não carrega rule id | A identidade cai para a categoria, e `low_confidence` é marcado como `true` na entrada |

O viés em direção a `new` é deliberado. Um `new` falso é visível no relatório e curado num comando (`gitpr baseline update`); um `existing` falso silenciaria um apontamento que não é o mesmo apontamento — e o que ele silenciaria poderia ser um segredo real. Os números de linha estão no payload pelo mesmo motivo.

`FINGERPRINT_VERSION` é a **primeira** linha do payload, por isso mudar o algoritmo muda todo fingerprint de uma vez, invalidando todo baseline de propósito — uma migração, não uma reinterpretação silenciosa. O manifesto regista a versão com que foi escrito, e um ficheiro escrito sob outra versão é recusado com a instrução.

---

## 7. Decisões: supressões e dívida aceite

Uma decisão é registada num de dois sítios, do mais estreito ao mais amplo:

1. **Na entrada** — uma supressão de escopo `finding`, ou dívida aceite. Um fingerprint, um apontamento.
2. **Em `.gitpr/baseline.overrides.yml`** — tudo o que é mais amplo: uma regra, um ficheiro, um intervalo de linhas. Este ficheiro é aditivo e editável à mão, e é onde uma equipa declara uma política sobre uma *classe* de apontamentos.

```yaml
overrides:
  suppressions:
    - fingerprint: "sha256:…"
      scope: finding
      reason: "Chave sintética num fixture; nunca é usada para alcançar um serviço."
      by: "alice"
      date: "2026-10-10"
    - scope: rule
      rule_id: "warning-todo-fixme"
      reason: "A regra é um apoio à decisão, não um portão, nesta árvore legada."
    - scope: file
      rule_id: "php-tabs"
      file_path: "app/Legacy/*"
      reason: "Ficheiros gerados, reescritos a cada migração."
    - scope: line
      rule_id: "php-tabs"
      file_path: "app/Old.php"
      line_start: 100
      line_end: 120
      reason: "Bloco legado em migração neste trimestre."
  accepted_debt:
    - fingerprint: "sha256:…"
      owner: "time-backend"
      reason: "Migração planeada para o próximo trimestre."
      due_date: "2026-12-31"
```

| Escopo | Alcança | Notas |
|---|---|---|
| `finding` | Um fingerprint exato | O mais estreito, e o único registado na própria entrada |
| `line` | Uma regra, num ficheiro, dentro de um intervalo de linhas que **contém** o intervalo do apontamento | Ignora o digest de conteúdo, por isso sobrevive a edições dentro do bloco — é por isso que exige sempre um motivo |
| `file` | Uma regra, num ficheiro ou glob de caminho | A mesma ideia que o linter já tem em `ignore_paths` |
| `rule` | Uma regra, em todo o repositório | O mais amplo |

A correspondência mais específica vence e fornece o motivo mostrado ao leitor. Duas invariantes são garantidas no código, e não por configuração:

- Uma supressão tem **motivo** não vazio. Uma decisão que ninguém explicou não é uma decisão; é um filtro.
- Dívida aceite tem **responsável**. Uma dívida que ninguém assume não está aceite, está esquecida.

Um prazo é opcional. Um prazo **vencido** é um aviso impresso ao lado do relatório e um problema para o `gitpr baseline validate` — nunca uma falha da execução em si.

Existe uma terceira camada que o repositório não grava: um **Policy Pack** ativo pode carregar um bloco `baseline:` próprio (veja `docs/policy-packs.md`). Essas decisões são aplicadas em memória durante a classificação, exibidas com a origem `policy:<nome>@<versão>`, e nunca gravadas em `.gitpr/baseline.json` — o pack é uma opinião partilhada, o ficheiro é o registo do próprio repositório. O `gitpr baseline unsuppress` não apaga uma delas: diz qual pack a carrega.

---

## 8. O fluxo num repositório legado

```bash
# 1. Na branch de migração, registe o que já está lá.
gitpr baseline create --yes

# 2. Commite o registo junto com o código que ele descreve.
git add .gitpr/baseline.json && git commit -m "chore: record the baseline"

# 3. Trabalhe. Só o que a alteração introduz é novo.
gitpr -l
gitpr -r
gitpr risk
```

O registo é revisto como qualquer outro ficheiro. O que um revisor procura:

| No diff | Leitura |
|---|---|
| Uma entrada nova com `status: "existing"` e nenhuma decisão | O autor reconheceu um apontamento pré-existente. Normal, mas se a contagem crescer em centenas num só commit, o baseline foi provavelmente registado contra a ref errada |
| Uma entrada nova com `suppressed: true` e um `suppression_reason` | Uma decisão. O motivo é a coisa sob revisão — um motivo que repete a regra ("é barulhenta") não explica nada; um motivo que declara a situação ("ficheiro gerado, reescrito pela migração") é auditável |
| Uma entrada nova com `accepted_debt_owner` | Dívida que alguém assume, com um prazo que o `gitpr baseline validate` vai cobrar |
| `.gitpr/baseline.overrides.yml` a acrescentar um escopo `rule` ou `file` | O tipo mais amplo de alteração na postura do repositório. Silencia uma classe de apontamentos, não um |
| Entradas a passar a `status: "resolved"` | Boa notícia, e barata de verificar: o apontamento desapareceu de um ficheiro que o diff toca |
| O `checksum` a mudar sem mais nada | Nada mais foi tocado — mas uma edição ao lado dele teria sido apanhada |

Os caminhos `.gitpr/baseline.json` e `.gitpr/baseline.overrides.yml` estão em `templates/gitpr.smart-excludes.json`: são registos, não código, e nunca são enviados à IA como parte de um diff.

O `create` não tem dry run: grava o registo e o `gitpr baseline show` lê-o de volta, que é a pré-visualização. Para registar um diff contra outra ref, `create --base <ref>` e `risk --base <ref>` são o par que tem de concordar — um baseline registado a partir do `HEAD` classifica quase tudo como `new` quando a execução de risco pergunta sobre uma branch.

---

## 9. Ler de um agente de IDE (MCP)

O servidor MCP expõe o registo apenas para leitura, para que um agente possa perguntar o que o repositório já sabe antes de ler um relatório:

| Superfície | O que responde |
|---|---|
| Tool `get_baseline_status` | O resumo em JSON: entradas por status, as regras mais ruidosas, as decisões por origem e escopo, a dívida aceite com responsável e prazo, a dívida vencida, e o estado do checksum |
| Resource `baseline://summary` | O mesmo resumo, como resource |

Os dois devolvem `baseline_summary()`, que abre o ficheiro, conta o que está nele e para: nenhum linter, nenhuma chamada à IA, nenhuma resolução de política, nenhuma escrita. Um ficheiro que não pode ser aplicado é *reportado* — `usable: false` com os `problems` que o explicam — nunca lançado como exceção, porque "o registo está lá e o portão recusá-lo-ia" é uma das respostas que quem chamou veio buscar. O resumo lê as mesmas camadas que o portão lê, por isso `.gitpr/baseline.overrides.yml` e o bloco `baseline:` do pack ativo aparecem nas suas contagens.

`counts.new` é sempre `0`, e a resposta diz porquê em `counts_note`: `new` é o resultado da comparação de uma execução contra o registo, não algo que um ficheiro possa guardar.

---

## 10. Limites, ditos sem rodeios

- **Uma linha deslocada é um apontamento novo.** Deliberado, e explicado acima. O `gitpr baseline update` regista-o de novo; o registo mantém o `first_seen_date` do que reconhece.
- **Um apontamento reportado pela IA é de baixa confiança.** Não tem rule id, por isso a sua identidade é a categoria e a localização — dois problemas diferentes na mesma linha, reportados por duas execuções de revisão diferentes, são uma identidade só para o baseline. A entrada diz `low_confidence: true` para que o leitor possa ponderar.
- **O caminho map-reduce não tem apontamentos.** Para um diff grande demais para uma única chamada, a IA responde em prosa, e prosa não tem apontamento para registar; o `create` diz quantos vieram da revisão de IA, para que a diferença seja visível.
- **O `create` só lê a revisão em cache quando o diff bate.** O cache chaveia uma revisão pelo seu prompt, por isso o `create` confere o `diff` a partir do qual a revisão foi feita contra o atual; uma divergência é reportada e a revisão não é consultada.
- **Não existe `gitpr check`, nem exportação SARIF.** O baseline é JSON e é consumível por qualquer coisa que leia JSON; um portão de CI de primeira classe e uma superfície SARIF não fazem parte desta funcionalidade.
- **O baseline nunca é enviado à IA.** A classificação acontece depois de o modelo ter respondido, sobre a saída estruturada dele. Nada a respeito do registo chega a um prompt.

---

## 11. Leitura relacionada

- `docs/policy-packs.md` — o bloco `baseline:` que um pack pode carregar, e como as decisões de um pack de dependência lhe são atribuídas
- `docs/mcp-integration.md` — o servidor MCP, a tool `get_baseline_status` e o resource `baseline://summary`
- `docs/linter-regras-customizadas.md` — as regras de linter a partir das quais um apontamento é fingerprintado
- `docs/config-tui.md` — o ecrã de configuração onde as quatro variáveis vivem
- `docs/plans/ADR-012-baseline-suppressions.md` — porque é que o fingerprint faz hash do conteúdo da linha, porque é que `new` nunca é persistido, e porque é que a camada de um pack fica em memória
