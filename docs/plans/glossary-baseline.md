# Glossário — Baseline & Supressões Auditáveis

> Vocabulário canônico da feature `baseline` (adoção do GitPR em repositórios legados).
> Mantido junto do [plano de execução](develop_natan/20261010_baseline_suppressions_plansfacts.md);
> as decisões de arquitetura vivem no [ADR-012](ADR-012-baseline-suppressions.md);
> o levantamento que as originou, no [survey](../../survey/20261010_baseline_suppressions_surveyfacts.md).

## Termos de domínio

| Termo | Definição |
|---|---|
| **baseline** | O arquivo versionado `.gitpr/baseline.json`: o registro das decisões sobre achados **pré-existentes** de um repositório. Existe para que a adoção do GitPR num repositório legado comece do zero — só o que é novo no diff bloqueia. Não é um ignore list: cada entrada carrega status, primeira e última vez vista, e a decisão tomada sobre ela. |
| **achado (finding)** | `NormalizedFinding` — a forma canônica e estruturada de um problema reportado por linter, bridge externa, SAST ou IA: regra, categoria, arquivo, linhas, severidade, `source` e o digest da linha. É a única coisa que o baseline sabe identificar; prosa não é endereçável. |
| **fingerprint** | O id estável de um achado: `"sha256:" + sha256(payload)`, com o payload de oito linhas — versão, identidade da regra, categoria, caminho normalizado, `source`, `line_start`, `line_end` e o hash da linha. Duas execuções sobre a mesma revisão produzem o mesmo fingerprint em qualquer máquina. Ver *payload*. |
| **payload** | O texto exato que o digest cobre, uma linha por campo. **Nunca** entram nele: mensagem, timestamp, provedor/modelo, branch, caminho absoluto. Mensagem é prosa que uma regra reescrita muda; provedor e modelo pertencem a quem rodou a análise; a branch pertence ao checkout. |
| **hash de conteúdo** | O digest da linha ofensora, com os espaços colapsados. Só o **digest** entra no payload — o texto da linha nunca é persistido, porque o baseline é commitado no Git e uma chave hardcoded não pode virar conteúdo de `.gitpr/baseline.json`. Colapsar espaços faz reformatar sozinho não ressuscitar um achado. |
| **identidade da regra** | `rule_identity` — o `rule_id` declarado, ou `category:<categoria>` quando o achado não tem regra. O id é preservado como declarado, caixa inclusive: dois ids que diferem só por caixa são duas regras. |
| **low confidence** | A marca de um achado cuja identidade caiu para a categoria — ou seja, **todo** achado da IA, que não tem `rule_id`. Viaja na entrada para que o `show` não apresente a mesma confiança para um achado de regra e um achado de modelo. |
| **`FINGERPRINT_VERSION`** | A primeira linha do payload. Um bump muda **todos** os fingerprints de uma vez, e a migração vira uma decisão registrada — por isso o manifesto carrega a versão com que foi escrito. |
| **supressão** | A decisão explícita de não tratar um achado como pendência: motivo obrigatório, autor, data e escopo. Vive na entrada do baseline (escopo `finding`) ou num arquivo de overrides (qualquer escopo). |
| **dívida aceita (accepted debt)** | A supressão que **assume o problema em vez de escondê-lo**: exige `owner` e `reason`, aceita `due_date`, e um prazo vencido gera warning — nunca falha silenciosa. É o status que mantém a pendência conhecida, que é o que o nome promete. |
| **prazo vencido (overdue)** | Dívida aceita cujo `due_date` já passou. Vira warning no `show`, no `validate` e no `gate`; a dívida continua valendo e continua visível. |
| **overrides locais** | `.gitpr/baseline.overrides.yml` — o ajuste auditável por repositório, com a mesma forma e os mesmos validadores do bloco de pack. É **aditivo**: acrescenta decisões, nunca reescreve o arquivo do baseline. |
| **camada (layer)** | Uma origem de decisão aplicada por cima da entrada. A ordem é entrada do baseline → overrides locais → supressões do pack ativo, e **a decisão da própria entrada sempre vence a de uma camada**. |
| **origem (origin)** | De onde a decisão veio: `local` (arquivo do repositório ou overrides) ou `policy:<nome>@<versão>` (bloco `baseline:` de um Policy Pack ativo). A origem é o que torna a decisão atribuível — uma supressão sem autor é indistinguível de um esquecimento. |
| **provenance** | O mapa gravado em cada entrada dizendo **qual comando** a escreveu (`baseline create`, `baseline update`, `baseline suppress`, `baseline unsuppress`) e sob qual política. É o rastro de auditoria dentro do arquivo. |
| **checksum (lockfile)** | O SHA-256 do JSON canônico de tudo **menos a própria chave** `checksum`. Divergência significa edição manual não rastreada: o baseline é **ignorado** com aviso destacado e exit != 0 nos fluxos que bloqueiam, e voltar atrás exige `baseline update --recompute`. Não há recálculo automático — ele apagaria a evidência. |
| **gate** | `BaselineGate` — o único lugar onde o pipeline pergunta pelo baseline. Carrega o manifesto, classifica os achados, e é a partir dele que saem a linha de status, a anotação dos alertas e a evidência informativa de risco. Fora dele, nada no GitPR consulta o baseline. |
| **primeiro visto / último visto** | `first_seen_commit`/`first_seen_date` e `last_seen_commit`/`last_seen_date`. O `update` preserva os primeiros e recarimba os últimos; é o que permite responder "há quanto tempo este achado existe" sem varrer histórico. |
| **`new`** | Não é um status persistido — é o resultado de uma comparação. Ver *os cinco status*. |

## Os cinco status

| Status | Persistido? | Definição |
|---|---|---|
| `new` | **não** | O achado está no diff e não tem fingerprint no baseline. É o único status que bloqueia, e só com `level: error`. Nunca é gravado: um `new` no arquivo descreveria uma comparação contra uma árvore que já não existe, e nasceria obsoleto. |
| `existing` | sim | O fingerprint está no baseline e o achado segue lá. É o status da adoção de legado: conhecido, tolerado, contado. |
| `resolved` | sim | A entrada sumiu do diff **e** o arquivo dela aparece no diff atual. A segunda condição existe para que um diff que encolhe não marque o repositório inteiro como resolvido. |
| `ignored` | sim | Existe uma supressão em vigor para o achado, com motivo e autor. O achado continua sendo contado; deixa de ser pendência. |
| `accepted_debt` | sim | Existe uma dívida aceita em vigor, com dono e motivo. Como `ignored` no efeito, diferente na responsabilidade: alguém se comprometeu com ela, e o prazo, se houver, é cobrável. |

## Os quatro escopos de supressão

Do mais específico ao mais amplo. O mais específico vence e fornece o motivo exibido.

| Escopo | Alcance | Exige |
|---|---|---|
| `finding` | Um fingerprint exato. É o **único** escopo que pode ser gravado na própria entrada do baseline. | `reason` |
| `line` | Mesma regra, mesmo arquivo, e o intervalo da supressão **contendo** o intervalo do achado. Ignora o hash de conteúdo — e é exatamente por isso que exige motivo e aparece sempre no `show`. | `reason` |
| `file` | Mesma regra no arquivo (ou num path glob). É o conceito que o linter já tem em `ignore_paths`. | `reason` |
| `rule` | A regra em todo o repositório. O escopo mais fácil de abusar, e por isso o mais visível. | `reason` |

Achado de escopo `line`, `file` ou `rule` **não** vira decisão na entrada: a entrada guarda
apenas decisões de escopo `finding`, e as demais vivem no arquivo de overrides (ou no pack), onde
a amplitude da decisão fica à vista.

## Precedência

Do menor para o maior — cada camada sobrescreve a anterior, **exceto** quando a decisão está na
própria entrada, que sempre vence:

1. status gravado na entrada do baseline;
2. `.gitpr/baseline.overrides.yml` (origem `local`), quando `GITPR_BASELINE_ALLOW_LOCAL_OVERRIDES` permite;
3. bloco `baseline:` do Policy Pack ativo (origem `policy:<nome>@<versão>`), **só em memória**,
   nunca gravado.

Dentro de uma mesma camada, vale a especificidade do escopo. Sem baseline, o gate não existe e o
GitPR se comporta exatamente como antes — bytes, exit codes e métricas idênticos.

## Chaves de configuração (dotenv plano, `~/.gitpr/.env`)

| Chave | Significado |
|---|---|
| `GITPR_BASELINE_ENABLED` | `false` → o baseline nunca é resolvido, mesmo que o arquivo exista. É o interruptor de emergência da feature. |
| `GITPR_BASELINE_PATH` | O caminho do arquivo, relativo à raiz do repositório (default `.gitpr/baseline.json`). |
| `GITPR_BASELINE_REQUIRE_LOCKFILE_CHECKSUM_MATCH` | `true` → checksum divergente faz o baseline ser ignorado, com aviso e exit != 0 nos fluxos que bloqueiam. |
| `GITPR_BASELINE_ALLOW_LOCAL_OVERRIDES` | `false` → o `.gitpr/baseline.overrides.yml` é rejeitado com aviso. Existe para quem quer as decisões todas dentro do arquivo revisável. |

## Notas de fidelidade

- **Três chaves da spec não existem, e a ausência é a decisão.** `suppress_blocker_requires_reason`
  e `accepted_debt_requires_owner` são invariantes no código — uma configuração capaz de desligar a
  exigência de motivo é uma forma de comprar silêncio. `default_status_for_new` não existe em
  nenhuma forma: um `new` configurável para outro status esvaziaria o vocabulário dos cinco status.
- **A fase de achados estruturados do linter foi pré-requisito, não item de escopo.** O linter
  devolvia strings formatadas e o nome da regra não aparecia nelas, então não havia o que
  fingerprintar. O retorno atual permanece **byte-idêntico** quando ninguém pede os achados — é
  essa propriedade que mantém todos os call sites antigos intactos.
- **Achados da IA entram por um array opcional no envelope do review.** `{"review": "..."}` sozinho
  continua válido; a mudança de prompt invalida o cache de review **uma vez**, custo aceito e
  documentado. O caminho map-reduce permanece prosa-only e portanto não contribui achados.
- **Um `new` falso é preferível a um `existing` falso.** Deslocamento de linha gera `new` — visível
  e remediável com `baseline update`. O inverso deixaria um segredo real passar. O viés é
  deliberado e está no ADR.
- **`create --base` e `risk --base` andam em par.** Um baseline colhido de `HEAD` classifica quase
  tudo como `new` sob `--base`; a CLI imprime a dica em vez de deixar a surpresa.
- **`gitpr check` e SARIF não existem**, e por isso o §8.2/§11.9 da spec ficam adiados por
  inexistência — não por esquecimento. O schema é JSON puro e consumível por qualquer ferramenta.
- **O vocabulário muda de nome na superfície do usuário, não de sentido.** A documentação em
  pt_br/pt_pt chama o achado de **apontamento** ("hallazgo" em es_es, "constat" em fr_fr); nos
  documentos internos ele continua **achado**. `fingerprint`, `baseline`, `policy pack` e
  `checksum` não são traduzidos em idioma nenhum, porque são os nomes que aparecem na CLI, no
  arquivo e nos comandos.
