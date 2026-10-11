# ADR-012 — Baseline de achados: identidade por fingerprint sem conteúdo, decisões auditáveis e camadas

- **Status:** Aceito
- **Data:** 2026-10-10
- **Contexto:** spec [20261010_skill_gitpr_baseline_spec.md](20261010_skill_gitpr_baseline_spec.md), grill de 4 rodadas
- **Glossário:** [glossary-baseline.md](glossary-baseline.md)
- **Plano:** [20261010_baseline_suppressions_plansfacts.md](develop_natan/20261010_baseline_suppressions_plansfacts.md)
- **Survey:** [20261010_baseline_suppressions_surveyfacts.md](../../survey/20261010_baseline_suppressions_surveyfacts.md)

## Contexto

Quem adota o GitPR num repositório legado vê o passado como falha de pipeline no primeiro
contato: o linter, o ruleset de segredos, as bridges SAST e a própria IA reportam de uma vez
tudo o que já estava lá antes do GitPR existir, e não há como dizer "isto eu já sei, trate só o
que é novo". A feature responde a isso com um **baseline versionado em Git**: um arquivo de
decisões sobre achados pré-existentes, com supressão auditável, dívida técnica com dono e prazo,
e um checksum que denuncia edição manual não rastreada.

Cinco fatos do código moldaram a decisão, e nenhum deles está na spec original:

1. **Não existe modelo de achado para a IA.** O review devolve prosa — `{"review": "..."}`
   (`src/core.py`) — e nada nele é endereçável.
2. **Não existe fingerprint algum.** O MD5 do prompt (`src/cache.py`) é chave de cache, não
   identidade de achado.
3. **O linter devolve strings formatadas e o nome da regra não aparece nelas**
   (`src/linter_engine.py` interpola só `rule["message"]`), então fingerprintar um achado do
   linter era impossível. Isso tornou obrigatória uma fase que a spec não listou: **achados
   estruturados do linter**, sem a qual a feature não tem o que identificar.
4. **Não existem `.gitpr/config.yml`, `gitpr check` nem SARIF.** A configuração do projeto é
   `~/.gitpr/.env` + `src/config_schema.py`, e é essa a convenção que o baseline segue.
5. **Subcomandos não executam o callback raiz** (`src/main.py`), então `review-pr` e `risk`
   resolvem política e baseline por conta própria — o baseline não pode depender de um estado
   que só o fluxo principal monta.

## Decisão

### 1. Fingerprint é identidade sem conteúdo

O payload tem oito linhas — `FINGERPRINT_VERSION`, identidade da regra, categoria, caminho
normalizado, `source`, `line_start`, `line_end`, hash da linha — unidas por `"\n"` e digeridas
em SHA-256.

**Só o digest da linha entra, nunca a linha.** O baseline é commitado no Git e o GitPR não
persiste código nem segredo: um achado sobre uma chave hardcoded não pode colocar a chave dentro
de `.gitpr/baseline.json`. O digest cobre a linha com espaços colapsados, então reformatar
sozinho não ressuscita um achado antigo.

Nunca no payload: mensagem, timestamp, provedor/modelo, branch, caminho absoluto. Mensagem é
prosa que uma regra reescrita muda; provedor e modelo pertencem a quem rodou a análise; a branch
pertence ao checkout. Duas execuções sobre a mesma revisão produzem o mesmo fingerprint em
qualquer máquina.

**Os números de linha entram de propósito.** Uma edição acima do achado o desloca e ele lê como
novo. O viés é deliberado: um falso `new` é visível e remediável com `gitpr baseline update`,
enquanto um falso `existing` deixaria um segredo real passar. `FINGERPRINT_VERSION` é a primeira
linha do payload justamente para que um bump mude todos os fingerprints de uma vez, e o manifesto
carrega a versão com que foi escrito.

Achado sem `rule_id` cai para `category:<categoria>` e é marcado `low_confidence` — é o caso de
todo achado da IA, e a marca viaja na entrada para que o `show` não apresente a mesma confiança
para as duas origens.

### 2. `new` é resultado de comparação, nunca estado gravado

Os status persistidos são quatro: `existing`, `ignored`, `accepted_debt`, `resolved`. O enum
mantém `NEW` porque o comparator precisa dele, e o validador do manifesto **recusa** um `new`
gravado: ele descreveria uma comparação contra uma árvore que já não existe, e o próximo `show`
mostraria um status que nenhum diff sustenta.

### 3. `resolved` só em arquivo que o diff atual toca

Uma entrada cujo **arquivo aparece no diff** e não foi vista é `resolved`; uma entrada de arquivo
**fora** do diff permanece `existing`. Sem essa restrição, um diff que encolhe — ou uma execução
com `--base` diferente — marcaria o repositório inteiro como resolvido em silêncio. É o ponto de
correção mais afiado do desenho e tem teste próprio.

### 4. Quatro escopos de supressão, o mais específico vence

Do mais específico ao mais amplo: `finding` (fingerprint exato), `line`, `file`, `rule`.
O escopo mais específico fornece o motivo exibido, e **a decisão da própria entrada sempre vence
a de uma camada** — o que está escrito na entrada do arquivo é a palavra final sobre ela.

O escopo `line` é **contenção**: mesmo `rule_id`, mesmo arquivo, e o intervalo da supressão
contendo o intervalo do achado. É exatamente por ignorar o hash de conteúdo que ele exige
`reason` e aparece sempre no `show` — suprimir um bloco inteiro é a decisão mais fácil de abusar,
então é a que mais presta contas.

Todo escopo exige `reason` não vazio. `accepted_debt` exige `owner` **e** `reason`, com
`due_date` opcional; prazo vencido gera **warning**, nunca falha silenciosa — a dívida continua
conhecida e visível, que é o que ela promete.

### 5. Três chaves de configuração do §9 da spec não existem como configuração

`suppress_blocker_requires_reason` e `accepted_debt_requires_owner` são **invariantes no código**,
não chaves: uma configuração capaz de desligar a exigência de motivo é uma forma de comprar
silêncio, e a feature existe para o oposto. `default_status_for_new` não existe em nenhuma forma —
um `new` que pudesse ser configurado para outro status esvaziaria o vocabulário dos cinco status.
Sobram quatro chaves: `GITPR_BASELINE_ENABLED`, `GITPR_BASELINE_PATH`,
`GITPR_BASELINE_REQUIRE_LOCKFILE_CHECKSUM_MATCH` e `GITPR_BASELINE_ALLOW_LOCAL_OVERRIDES`.

### 6. Camadas: entrada → overrides locais → pack, esta última só em memória

A supressão de um Policy Pack (bloco `baseline:` do manifesto) é aplicada **na classificação e
nunca gravada** em `.gitpr/baseline.json`. O arquivo do repositório não passa a conter decisões
que o revisor não escreveu; a decisão do pack vive enquanto o pack estiver ativo, e o `show` a
exibe com a origem `policy:<nome>@<versão>`. `gitpr baseline unsuppress` não a remove — diz qual
pack a mantém, porque remover exigiria editar o pack, não o baseline.

O bloco passa pelos **mesmos validadores** do `baseline.overrides.yml` editado à mão, incluindo a
recusa de fingerprint duplicado: um pack não compra uma regra mais fraca declarando-a em outro
arquivo. Se dois packs ativos trouxerem o mesmo fingerprint, a ativação falha nomeando o conflito
— o GitPR nunca escolhe um vencedor em silêncio.

### 7. Checksum que não cobre a si mesmo

O `checksum` é o SHA-256 do JSON canônico (`sort_keys`, separadores `(",", ":")`,
`ensure_ascii=False`) de tudo **menos** a própria chave, com as entradas ordenadas por fingerprint
antes de escrever — o que dá diff Git mínimo e reprodutível entre máquinas.

Divergência de checksum faz o baseline ser **ignorado** com aviso destacado e exit != 0 nos fluxos
que bloqueiam. Não há recálculo automático: ele apagaria a evidência da edição manual, que é o
único motivo de o checksum existir. Quem quer voltar atrás roda `baseline update --recompute`,
que é um ato explícito e registrado.

### 8. Integração em `main.py` e resolução própria dos subcomandos

Todo o efeito do baseline vive dentro de `if gate.manifest is not None:`. Sem o arquivo, o
caminho, os bytes de saída, os exit codes e as métricas são exatamente os de hoje — a
não-regressão é verificada byte a byte, porque a feature não pode mudar a vida de quem não a
adotou. O bloqueio continua preso a `new` **com `level: error`**: o `sys.exit(1)` do `--linter`
não passa a disparar por `warning`.

`review-pr` e `risk` resolvem o baseline por conta própria pelo fato 5 acima; `-c`, PR, blame,
issue, chat, release, split e fix pedem `required=False` e não consultam nada.

### 9. Uma invalidação única do cache de review

O envelope do review ganha um array **opcional** `findings`, com o mesmo formato que o `gitpr fix`
já consome; `{"review": "..."}` sozinho continua válido. Mudar o prompt invalida o cache de review
**uma vez** — custo aceito e documentado, não contornado: um envelope com achados e um sem são
respostas diferentes à mesma pergunta, e servir a antiga em silêncio produziria um baseline
incompleto sem que ninguém soubesse. O caminho map-reduce permanece prosa-only, e portanto não
contribui achados.

### 10. `gitpr check` e SARIF não existem

O §8.2/§11.9 da spec ficam **adiados por inexistência**: o GitPR não tem um comando `check` nem
exporta SARIF, e criar um seria uma segunda feature. O schema continua JSON puro e consumível por
qualquer ferramenta, e este ADR registra a lacuna para que ela não seja lida depois como
esquecimento.

## Consequências

- **Sem baseline, nada muda.** Nem bytes, nem exit codes, nem cache, nem métricas. É o que permite
  entregar a feature sem migração.
- **Fingerprint sensível a deslocamento de linha.** Falso `new` é visível e remediável
  (`baseline update`); o viés inverso esconderia segredo real. A escolha é registrada, não
  escondida.
- **`create --base` e `risk --base` andam em par.** Um baseline colhido de `HEAD` classifica quase
  tudo como `new` sob `--base`; a CLI imprime a dica de uma linha em vez de deixar a surpresa.
- **Review em cache obsoleto não vira baseline.** O `create` recusa um registro cujo diff gravado
  diverge do atual, avisa e chama a IA de novo.
- **A fase de achados estruturados do linter é permanente.** O linter passa a acumular
  `NormalizedFinding` além das strings formatadas; o retorno atual permanece **byte-idêntico**
  quando ninguém pede os achados, e é essa propriedade que mantém todos os call sites antigos
  intactos.
- **Privacidade por abstenção.** O baseline nunca entra em prompt, a classificação é pós-hoc sobre
  o que a IA devolveu, e o arquivo guarda digests e decisões — nunca código, nunca segredo. A
  verificação roda sem rede.
- **O baseline é revisável num PR.** Como são JSON e YAML ordenados e canônicos, revisar um
  baseline é ler um diff — que é a única forma de uma supressão ser realmente auditável.

## Alternativas consideradas

| Alternativa | Por que não |
|---|---|
| **Fingerprint sem o hash do conteúdo da linha** | Uma edição na linha manteria o achado antigo vivo, transformando uma linha corrigida num `existing` eterno — e o viés viraria o perigoso: falso `existing` esconde segredo real |
| **Fingerprint sem os números de linha** (matching de realocação) | Exigiria um algoritmo de similaridade já na v1, e o payload deixaria de ser auditável à mão. A própria spec deixa o matching de realocação fora do escopo |
| **Gravar `new` no arquivo** | Nasce obsoleto: descreve uma comparação contra uma árvore que já não existe, e o próximo `show` mostraria um status que nenhum diff sustenta |
| **`.gitpr/config.yml` para as chaves do baseline** | O projeto tem uma convenção (dotenv global + `config_schema.py` + TUI de configuração). Um segundo sistema de configuração criaria duas verdades sobre o mesmo parâmetro |
| **Supressão vinda de pack gravada no baseline** | O arquivo versionado passaria a conter decisões que ninguém escreveu, e desativar o pack deixaria a supressão órfã no repositório — indevida e invisível |
| **Checksum divergente → recálculo automático** | Apagaria a evidência da edição manual, que é a única razão de o checksum existir |
| **Bloquear por `new` em qualquer severidade** | Um `warning` novo derrubaria o pipeline, mudando o significado do gate para quem não pediu. O bloqueio continua preso a `error`, como sempre foi |
| **Criar `gitpr check` + SARIF agora** | Seria uma segunda feature pendurada numa primeira ainda não validada em uso real; o schema JSON já é consumível por quem quiser construir a ponte |
