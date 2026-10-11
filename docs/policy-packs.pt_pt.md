# Documentação Técnica: Policy Packs (`gitpr policy`)

Um **Policy Pack** é um manifesto YAML versionável que transporta a política de qualidade inteira de uma equipa — skills de revisão, regras de linter, overrides de severidade, caminhos críticos, pesos de risco e as convenções de PR/commit — num único ficheiro que um repositório pode adotar, rever e versionar a par do próprio código. O `gitpr policy` regista *qual* pack o repositório segue e é a única coisa que decide *o que* esse pack altera.

Até agora cada uma dessas superfícies era configurada noutro sítio: `.gitpr/skill/.gitpr.review.md`, `.gitpr/skill/.gitpr.linter.yml`, `.gitpr/skill/gitpr.risk.yml`, `~/.gitpr/.env`. Nada ligava o conjunto, por isso "seguimos a política da Acme" era uma convenção, não algo que a ferramenta pudesse verificar. Com um pack, é uma linha num ficheiro sob controlo de versões.

---

## 1. Visão Geral

Os Policy Packs atuam em três superfícies:

1. **O grupo `gitpr policy`**: sete comandos para listar, validar, mostrar, adotar, instalar, criar e abandonar uma política. `list`, `validate` e `show` apenas leem; `use`, `install`, `init` e `off` escrevem e perguntam antes de escrever.
2. **Todos os comandos posteriores no repositório**: com um pack ativo, `gitpr -r`, `gitpr -f`, `gitpr -c`, `gitpr` (descrição de PR), `gitpr -l` e `gitpr risk` correm sob ele, sem que nenhum deles ganhe um argumento novo.
3. **`.gitpr/policy.lock.yml`**: o ficheiro que regista a decisão. Nomeia o pack, a versão, a origem e um checksum por pack, para que um colega obtenha a mesma política a partir do mesmo commit.

### 1.1 Referência de Comandos

```bash
gitpr policy list                        # Os packs desta máquina e o que está em vigor
gitpr policy validate gitpr/laravel-quality   # Schema, compatibilidade, skills, regras, dependências
gitpr policy show                        # A política efetiva, com a origem de cada valor
gitpr policy use acme/team-policy@1.0.0  # Fixa um pack, escrevendo .gitpr/policy.lock.yml
gitpr policy init --stack laravel        # Sugere e ativa o pack oficial da stack
gitpr policy install ./our-policy        # Copia um diretório local para ~/.gitpr/policies
gitpr policy off                         # Deixa de seguir o pack
```

| Comando | Escreve | Descrição |
|---|---|---|
| **`list`** | — | O pack ativo (com o seu grafo de dependências) e todos os packs encontrados nesta máquina |
| **`validate <caminho\|nome[@intervalo]>`** | — | Valida um pack e reporta o que ele faz. Saída diferente de zero quando o pack é inválido, para o CI poder bloquear |
| **`show`** | — | A política efetiva em vigor, com a proveniência de cada campo e a ordem de precedência que a produziu |
| **`use <nome>[@<versão>]`** | `.gitpr/policy.lock.yml` | Fixa um pack para este repositório. Substitui o pack que estivesse ativo |
| **`init [--stack laravel\|vue\|php\|node]`** | `.gitpr/policy.lock.yml` | Deteta a stack a partir do projeto e ativa o pack oficial correspondente |
| **`install <caminho> [--force]`** | `~/.gitpr/policies/` | Valida um pack num diretório local e copia-o para o repositório de packs do utilizador. Não há registry nem download |
| **`off`** | remove `.gitpr/policy.lock.yml` | Deixa de seguir o pack. O pack e o ficheiro de overrides são mantidos |

Todos os comandos de escrita aceitam `--yes`, que ignora a confirmação mas **não** as verificações por trás dela. Sem terminal e sem `--yes`, um comando de escrita falha com a instrução em vez de ficar preso num prompt que ninguém vai ler — é isso que torna o grupo seguro para ser chamado de um hook ou de um job de CI que se esqueceu da flag.

### 1.2 De onde um pack pode vir

Três origens, procuradas nesta ordem:

| Ordem | Origem | Local | `source` no lockfile |
|---:|---|---|---|
| 1 | O próprio repositório | `<repo>/.gitpr/policies/<nome>/` | `local_path` |
| 2 | O repositório do utilizador | `~/.gitpr/policies/<nome-achatado>/` | `installed` |
| 3 | O que o GitPR entrega | `src/policy_packs/<nome>/` | `bundled` |

Um pack instalado vive num diretório **achatado** — `acme/team-policy` é guardado como `acme__team-policy` — porque o namespace faz parte da identidade do pack, não do layout do sistema de ficheiros. Um pack versionado dentro do repositório é encontrado por caminho, e é isso que permite a uma equipa adotar uma política que ninguém instalou.

Nada é descarregado. Um pack é texto em disco; a resolução lê-o, calcula o seu hash e compõe-no.

---

## 2. O Manifesto

Um pack é um diretório com `policy.yml` e os assets que o manifesto declarar:

```
acme__team-policy/
├── policy.yml          # o manifesto — o único ficheiro obrigatório
├── linter.yml          # declarado por linter.rules_file
├── README.md           # viaja junto; faz parte do pack, não é lido por ninguém
└── CHANGELOG.md
```

### 2.1 Schema

O schema é **fechado**: uma chave desconhecida é erro, não aviso. Um erro de escrita como `test:` em vez de `tests:` tem de falhar alto, porque a alternativa é uma política que silenciosamente não faz nada enquanto o seu nome continua a aparecer na saída.

| Chave | Obrigatória | Tipo | Significado |
|---|---|---|---|
| `schema_version` | ✅ | int | Versão do schema do manifesto. Atualmente `1` |
| `name` | ✅ | str | `namespace/nome`. Path traversal é recusado |
| `version` | ✅ | str | A versão do próprio pack |
| `min_gitpr_version` | ✅ | str | Intervalo `SpecifierSet`, ex.: `">=1.3.0"`. Validado contra o GitPR em execução |
| `description` | — | str | Texto livre, mostrado por `policy list` |
| `license` | — | str | Texto livre |
| `authors` | — | list[str] | Texto livre |
| `extends` | — | list | Dependências: `[{name, version}]`. `version` é um intervalo |
| `baseline` | — | map | `suppressions`, `accepted_debt` — as decisões que o pack traz para o baseline, só em memória |
| `skills` | — | map | `skills.<tipo>.additional_context` — texto anexado ao prompt dessa skill |
| `linter` | — | map | `rules_file`, `severity_overrides` |
| `risk` | — | map | `critical_paths`, `test_patterns`, `weights`, `thresholds` |
| `pr` | — | map | `required_sections` |
| `commit` | — | map | `allowed_types` |
| `protected_paths` | — | list[str] | Declarado para o prompt, não imposto por nenhum motor |

### 2.2 Um exemplo completo

```yaml
schema_version: 1
name: acme/team-policy
version: 1.0.0
description: The Acme house rules for PHP services.
min_gitpr_version: ">=1.3.0"
license: MIT
authors:
  - Acme Platform

extends:
  - name: acme/base-policy
    version: ">=1.0.0 <2.0.0"

skills:
  review:
    additional_context: |
      Money is an integer in minor units. A float in a monetary field is a bug
      regardless of how it got there.

linter:
  rules_file: linter.yml
  severity_overrides:
    - rule_name: acme-no-float-money
      level: warning
      reason: the float check is advisory while the migration is in flight

risk:
  critical_paths:
    - app/Services/**
  test_patterns:
    - spec/**
  weights:
    database_migration: 25

pr:
  required_sections:
    - Business impact
    - Rollback plan

commit:
  allowed_types:
    - feat
    - fix
    - chore

baseline:
  suppressions:
    - scope: rule
      rule_id: acme-no-float-money
      reason: The float check is advisory while the migration is in flight.
  accepted_debt:
    - fingerprint: "sha256:9f2c…"
      owner: acme-platform
      reason: Scheduled for the payments rewrite.
      due_date: 2026-12-31

protected_paths:
  - config/**
```

### 2.3 As secções

**`skills`** — um bloco por tipo de skill. Os tipos válidos são os que o GitPR conhece: `commit`, `pr`, `review`, `filereview`, `blame`, `issue`, `release`, `fix`, `tests`, `explain`, `mentor`. Um tipo desconhecido é recusado no parsing; um pack não pode inventar uma skill, porque nada a iria ler. O texto é concatenado com as contribuições dos outros packs e anexado ao prompt como instruções de sistema, e é por isso que também entra na chave de cache — veja a §4.3.

**`linter.rules_file`** — o nome de um ficheiro YAML de regras **dentro do diretório do pack**. Um caminho que escape do diretório é recusado, por isso um pack não pode apontar para `/etc/passwd` nem para um ficheiro acima de si mesmo. As regras entram no catálogo por `name`, com as regras do próprio projeto a vencer as do pack.

**`linter.severity_overrides`** — altera o nível de uma regra que já existe, depois de todo o catálogo ter sido fundido. `level` é `error` ou `warning`. **Rebaixar uma regra de `error` para `warning` exige um `reason`** — um override que enfraquece o portão é uma decisão que alguém tomou de propósito, e o motivo viaja com ele para o `policy validate`, o `policy show` e o relatório de revisão. Endurecer uma regra não precisa de justificação. Um override que nomeia uma regra inexistente em qualquer ponto do catálogo final é **erro**: não fazer nada em silêncio deixaria a equipa a acreditar que uma regra foi relaxada quando não foi.

**`risk.critical_paths` / `risk.test_patterns`** — unidos entre packs, por ordem de precedência. `test_patterns` ensina ao motor de risco quais os ficheiros que contam como teste no layout *deste* projeto (`spec/**`, `**/*Cest.php`), que é o que faz o `TEST_PRESENT` disparar num repositório cujo diretório de testes não se chama `test/` nem `tests/`.

**`risk.weights` / `risk.thresholds`** — um valor único, não uma lista. Dois packs não relacionados por `extends` a discordar do mesmo peso é **erro de validação**, nomeando os dois; uma dependência e o seu dependente a discordar é refinamento, e o dependente vence.

**`pr.required_sections`, `commit.allowed_types`, `protected_paths`** — nada no código lê estes três. Existem para serem *ditos* ao modelo, e é por isso que são renderizados nos contextos das skills `pr` e `commit` como texto de prompt, em vez de ficarem como dado.

### 2.4 `extends`

Um pack pode depender de outros packs. O grafo é resolvido em **ordem topológica** — dependências primeiro, pack raiz por último — por isso os valores de uma dependência são aplicados antes dos do pack que se baseia neles. Um ciclo é recusado com a cadeia na mensagem, porque "há um ciclo" sem o caminho não é acionável.

Um pack raiz por repositório. O `gitpr policy use` **substitui** a escolha anterior em vez de lhe somar; o grafo abaixo da raiz é alcançado por `extends`, o que mantém a escada de precedência uma linha em vez de uma rede.

### 2.5 `baseline`

Um pack pode carregar as supressões e a dívida aceite que a sua stack já conhece, para que adotar o pack e adotar o baseline sejam uma decisão só em vez de duas:

```yaml
baseline:
  suppressions:
    - scope: rule
      rule_id: acme-no-float-money
      reason: The float check is advisory while the migration is in flight.
  accepted_debt:
    - fingerprint: "sha256:9f2c…"
      owner: acme-platform
      reason: Scheduled for the payments rewrite.
      due_date: 2026-12-31
```

As duas metades têm a **mesma forma e os mesmos quatro escopos** de `.gitpr/baseline.overrides.yml` — `finding`, `line`, `file`, `rule` — e passam pelos **mesmos validadores**: um pack que declarasse uma supressão sem motivo, ou dívida aceite que ninguém assume, seria uma forma de contornar a auditabilidade pela qual o baseline existe. Um pack não compra uma regra mais fraca declarando-a noutro ficheiro. O bloco é fechado como o resto do manifesto: uma chave desconhecida é erro, e uma falha nomeia o pack, a metade e o índice da entrada, porque é isso que o `gitpr policy validate` imprime.

Três propriedades separam esta camada dos ficheiros do próprio repositório:

| | Bloco do pack | `.gitpr/baseline.json` / `.overrides.yml` |
|---|---|---|
| **Onde vive** | Em memória, durante a classificação | Em disco, commitado |
| **Origem exibida** | `policy:<nome>@<versão>`, por entrada — a decisão de uma dependência nomeia a dependência, não a raiz | `local` |
| **Gravado por uma execução** | Nunca. Nada de um pack chega ao ficheiro de baseline | `baseline create`, `update`, `suppress` |

O `gitpr baseline unsuppress`, portanto, não remove uma delas: diz qual pack a carrega, e a resposta é uma edição ao pack, não ao repositório. Nada é descarregado para ler o bloco — o pack já é texto em disco, coberto pelo checksum do lockfile como todo outro campo que ele declara, por isso o baseline de um pack não pode ser editado sem que o checksum dê por isso.

Um pack que use este bloco deve declarar um `min_gitpr_version` que inclua a versão contra a qual foi escrito: um GitPR mais antigo faz o parse do manifesto, não conhece a chave e recusa o pack inteiro, em vez de aplicar uma política com uma metade em falta em silêncio.

---

## 3. Precedência

Do mais baixo para o mais alto. Um valor com número maior sobrepõe-se a um com número menor.

| # | Camada | Escrito por |
|---:|---|---|
| 1 | Defaults internos do GitPR | o código |
| 2 | Packs de dependência | `extends`, em ordem topológica |
| 3 | O pack raiz | `.gitpr/policy.lock.yml` |
| 4 | `.gitpr/policy.overrides.yml` | o repositório |
| 5 | Configuração local do projeto | `.gitpr/skill/*`, `.gitpr.linter.yml` |
| 6 | Flags de CLI | `--base`, `--provider`, … |
| 7 | Variáveis de ambiente | `GITPR_*` |

O catálogo do linter é fundido na sua própria ordem, porque as suas camadas não são as mesmas:

**ruleset de segurança embutido → regras dos packs → regras do projeto → plugins globais → overrides de severidade**

Os overrides de severidade são aplicados **em último lugar**, contra o catálogo final, porque só aí o conjunto de nomes de regra conhecidos está completo — e é isso que permite que um override com erro de escrita falhe em vez de silenciosamente não fazer nada.

### 3.1 O lockfile

`gitpr policy use acme/team-policy@1.0.0` escreve:

```yaml
schema_version: 1
root:
  name: acme/team-policy
  version: 1.0.0
  source: installed
  checksum: 4f449708ac83901bffb4275e8d6d7c880154022bca0382962519c2270cb1842f
packs:
  - name: acme/base-policy
    version: 1.0.0
    source: installed
    checksum: 9c1f…
  - name: acme/team-policy
    version: 1.0.0
    source: installed
    checksum: 4f44…
```

O ficheiro deve ser **commitado**. Um pack dentro do repositório é também registado por um `path` relativo ao repositório, em POSIX, para que um colega o leia do mesmo sítio em vez de uma cópia própria; um pack do repositório do utilizador é registado apenas pelo nome, porque onde ele mora é um detalhe de máquina.

### 3.2 Overrides

`.gitpr/policy.overrides.yml` é o repositório a falar de si mesmo, um nível abaixo das flags de CLI. Usa a forma `{add, remove}` para listas, por isso remover um caminho protegido ou uma secção obrigatória é uma linha num diff em vez de uma ausência:

```yaml
protected_paths:
  add:
    - legacy/**
  remove:
    - .env.example

risk:
  weights:
    large_diff: 10
```

---

## 4. Integridade e Comportamento em Falha

### 4.1 O checksum

O checksum de cada pack é SHA-256 sobre `policy.yml` mais todos os assets declarados pelo manifesto, calculado quando o pack é ativado e reverificado a cada execução. Um asset editado é uma política diferente, e uma política diferente não foi a que a equipa acordou.

Note que o checksum é byte a byte: um pack versionado dentro do repositório e reescrito pelo `core.autocrlf` no checkout vai abortar com mismatch. Um `gitpr policy use` sobre um pack com a cópia de trabalho normalizada em LF — ou um `.gitattributes` a fixar o diretório do pack — resolve.

### 4.2 As três abortagens

A resolução **aborta** em vez de degradar em exatamente três casos:

| Falha | Por que aborta |
|---|---|
| Um pack já não está em disco | As suas regras desapareceram; a saída continuaria a transportar o rótulo da política |
| Uma versão fixada desapareceu (após um upgrade, ou um `use` noutro sítio) | A versão que a equipa acordou não é a que correria |
| Um checksum já não confere | O conteúdo mudou desde a ativação |

Cumprir metade da promessa é pior do que não a cumprir, porque a revisão, a saída do linter e a pontuação de risco continuariam a alegar correr sob a política. Cada abortagem nomeia o pack, o que aconteceu e o comando que repara.

`strict=False` é a única escotilha de escape, e só os próprios comandos `gitpr policy` a usam — são a ferramenta que repara um lockfile quebrado, por isso têm de poder correr enquanto um está quebrado.

### 4.3 Âmbito de cache

O GitPR faz cache das respostas de IA por MD5 sobre o prompt. O contexto da skill é um **argumento separado** (`instrucao_sistema`) e não faz parte desse hash — por isso, sem uma correção, ativar um pack sobre um diff já em cache não mudaria absolutamente nada, e o rótulo seria mentira.

A correção é o âmbito de cache. Com um pack ativo, `::policy::<nome>@<versão>::<checksum>` é anexado à chave de cache, o que significa que um pack ativado invalida as entradas afetadas e dois packs diferentes nunca partilham uma resposta. Sem pack, o âmbito é a string vazia, por isso nada muda.

### 4.4 Garantias

- **Sem rede, nunca**: um pack é local por design. A resolução lê um lockfile, calcula hashes de ficheiros e compõe texto.
- **Sem execução arbitrária**: o `policy validate` não corre subprocesso nenhum, e a validação é offline e sem efeitos colaterais. Um pack é texto que outra pessoa escreveu, e o comando que o inspeciona não executa nada do que ele contém.
- **Sem segredos num manifesto**: um manifesto que corresponda a uma das regras embutidas de deteção de segredos é recusado no parsing, usando o mesmo ruleset que o linter corre em vez de um segundo scanner que poderia divergir dele.

---

## 5. Configuração

| Chave | Tipo | Predefinição | Descrição |
|---|---|---|---|
| `GITPR_POLICY_ENABLED` | bool | `true` | Lê e aplica o lockfile. Desligar faz todo comando comportar-se como se o repositório não tivesse pack, sem tocar no lockfile |
| `GITPR_POLICY_CONTEXT_MAX_CHARACTERS` | int | `12000` | Teto de quanto contexto um pack pode adicionar a um prompt. Além dele, as contribuições são descartadas primeiro do pack de menor precedência e o descarte é reportado como aviso |

Qual pack está ativo deliberadamente **não** é uma chave de configuração: pertence ao repositório, não à máquina, por isso vive no lockfile onde pode ser revisto e versionado a par do código ao qual se aplica.

---

## 6. Packs Oficiais

| Pack | Regras em cadeia | Para que serve |
|---|---:|---|
| `gitpr/php-security` | 8 | Baseline de segurança PHP: interpolação em SQL, `eval`, hashes de password fracos, `unserialize` estrangeiro, includes dinâmicos, `extract()` a partir de input, CORS com wildcard, cookies de sessão inseguros |
| `gitpr/laravel-quality` | 7 (+8) | Portão de qualidade Laravel: autorização, mass assignment, transações, N+1, migrations reversíveis, filas, dados pessoais. **Estende `gitpr/php-security`** |
| `gitpr/node-quality` | 7 | Serviços Node: promises flutuantes, validação de entrada, estados não tratados, higiene de dependências, configuração e segredos |
| `gitpr/vue-quality` | 6 | Componentes Vue 3: props e emits, reatividade, limpeza de efeitos colaterais, estados assíncronos, acessibilidade, dimensão do componente |

Cada um transporta contexto de revisão que um revisor genérico não tem (o que custa um `down()` que não reverte o seu `up()`, porque é que um job disparado dentro de uma transação pode correr antes de a linha ser commitada), caminhos críticos e padrões de teste para o seu layout, e convenções de PR/commit. São deliberadamente pequenos e opinativos: acrescentam o que os defaults ainda não cobrem, em vez de os repetir.

O `gitpr policy init` escolhe um a partir dos marcadores do próprio projeto — `composer.json` + `artisan` para Laravel, `package.json` + Vue para Vue, e assim por diante — do mais específico para o mais genérico.

---

## 7. Adotar uma Política numa Equipa

```bash
# Uma pessoa, uma vez: valida e instala o pack
gitpr policy install ./our-policy --yes

# No repositório: fixa e commita a decisão
gitpr policy use acme/team-policy@1.0.0
git add .gitpr/policy.lock.yml && git commit -m "chore: adopt the Acme quality policy"

# Toda a gente: nada a instalar se o pack está commitado com o repo
gitpr policy show
```

Três formas de partilhar uma política, conforme o quanto a equipa quer depender de uma máquina:

- **Um pack dentro do repositório** (`.gitpr/policies/<nome>/`) — versionado com o código, sem passo de instalação, e o lockfile regista o caminho relativo. A melhor opção para uma política que é do próprio repositório.
- **Um pack instalado** (`~/.gitpr/policies/`) — uma cópia para todos os repositórios da máquina. Cada colega instala-o da mesma origem; o lockfile regista nome e versão.
- **Um pack oficial** — lido diretamente do que o GitPR entrega. Nada a distribuir, e uma nova versão do GitPR pode trazer uma nova versão dele.

O ciclo de vida do pack é separado do do GitPR: suba o `version` no manifesto e o checksum muda, o que é um diff no lockfile, o que é uma revisão. É esse o ponto de fixar a versão.
