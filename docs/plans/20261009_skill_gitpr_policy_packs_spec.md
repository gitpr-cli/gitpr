# SPEC — GitPR Policy Packs / Skills Compartilháveis

> Documento de especificação técnica para implementação via Claude Code skill.
> Escopo: unificar skills suportadas pelo GitPR, presets de linter YAML, regras de severidade, caminhos críticos, configuração de risk score e convenções de PR/commit em um **Policy Pack** versionável e compartilhável. Um pack é um manifesto declarativo, aplicável por repositório, que padroniza o quality gate sem criar um segundo sistema de skills dinâmicas.

## 0. Contexto obrigatório antes de codificar

Antes de gerar qualquer código, a skill DEVE:

1. Ler `core.py`, especialmente `get_skill_context`, e confirmar a regra arquitetural já definida no projeto: as skills suportadas são **fixas**, registradas em código, e não descobertas por varredura dinâmica de diretórios. Policy Packs NÃO podem criar, carregar ou executar skills com nomes arbitrários.
2. Mapear a lista real de skills suportadas, seus nomes internos, arquivos físicos e pontos de uso (PR, review, issue, explain, mentor e outras que existirem). O manifesto de pack deve referenciar apenas nomes presentes nessa lista.
3. Ler o formato real de `.gitpr.linter.yml` e dos presets de linter existentes, incluindo regras, severidades, exclusões, combinações de presets, configuração de bridges externos e mecanismo de override por projeto.
4. Ler a configuração real de risk scoring, se a spec/implementação anterior já existir, para identificar chaves configuráveis: pesos, caminhos críticos, padrões de teste, thresholds e versão de análise.
5. Verificar o sistema de plugins já existente: onde os plugins são instalados, como são versionados, se há atualização OTA, como a integridade é tratada e qual é o formato de configuração. Policy Packs devem reaproveitar essa infraestrutura quando ela for adequada; não criar registry, updater ou cache paralelos sem justificativa.
6. Verificar como o GitPR encontra configuração local do projeto (`.gitpr/`, YAML, variáveis de ambiente) e estabelecer ordem de precedência compatível com a configuração existente.
7. Ler o fluxo `gitpr --init` e a TUI de configuração, se existirem, para saber onde oferecer instalação, ativação e inspeção de packs sem introduzir uma UX paralela.
8. Verificar como o projeto hoje trata arquivos de configuração vindos de terceiros. Como packs podem ser compartilhados dentro de equipes, a implementação deve validar schema, versão e referências locais antes de alterar comportamento do linter/review.

Não prosseguir sem completar os passos 1–4. Se o sistema de plugins existente não for adequado para distribuição de packs, implementar primeiro somente packs locais versionados no repositório; registry remoto, instalação OTA e marketplace ficam fora do escopo inicial.

## 1. Decisão arquitetural obrigatória

### 1.1 Packs não são skills dinâmicas

A regra central desta feature é:

- `get_skill_context` continua sendo a fonte de verdade para as skills que o GitPR sabe executar.
- Um pack pode **ativar**, **parametrizar**, **adicionar contexto complementar** ou **selecionar formato** de uma skill fixa suportada.
- Um pack não pode declarar uma skill inexistente em `get_skill_context`.
- Um pack não pode executar código arbitrário, comandos shell, hooks externos ou prompts remotos nesta primeira versão.
- Qualquer referência a skill inválida deve falhar durante a validação/instalação do pack, antes de o pack ser ativado.

Isso preserva a arquitetura atual e permite compartilhamento de políticas sem transformar o projeto em um carregador inseguro de prompts/código de terceiros.

### 1.2 O que um Policy Pack contém

Um pack pode declarar:

- metadados: nome, versão SemVer, autor, descrição, compatibilidade mínima do GitPR, licença e changelog;
- skills fixas habilitadas e contexto complementar por operação (`review`, `pr`, `commit`, `issue`, `explain`, `mentor`), limitado a skills suportadas;
- presets/regras de linter YAML e overrides de severidade;
- configuração de risk score: caminhos críticos, padrões de teste, pesos e thresholds informativos;
- convenções de commit e PR: formatos aceitos, seções obrigatórias, labels sugeridas, caminhos protegidos;
- dependências de outros packs, com versão compatível;
- regras de merge/precedência declarativas.

Um pack não contém nesta versão:

- executáveis, scripts, binários ou código Python;
- tokens, segredos, credenciais, URLs privadas com token embutido;
- instalação automática de dependências externas (Semgrep, Gitleaks, Bandit etc.);
- políticas obrigatórias remotas impostas sem confirmação local.

## 2. Escopo da feature

- **Objetivo:** permitir que uma equipe mantenha políticas de qualidade como artefatos versionados em Git e aplique um conjunto consistente de skills, linter, severidade e risco em vários repositórios.
- **Comandos novos:**
  - `gitpr policy list` — lista packs locais/disponíveis, versão, origem e status de ativação.
  - `gitpr policy validate <pack-or-path>` — valida manifesto, schema, compatibilidade e referências a skills/prests.
  - `gitpr policy install <path-ou-ref>` — instala/copia um pack local ou adiciona referência declarativa, conforme a infraestrutura existente.
  - `gitpr policy use <name>@<version>` — ativa um pack para o repositório atual.
  - `gitpr policy show <name>` — mostra configuração efetiva e origem de cada regra.
  - `gitpr policy init --stack <laravel|vue|php|node>` — instala/ativa um pack oficial de stack, se disponível.
- **Packs oficiais iniciais:**
  - `gitpr/laravel-quality`;
  - `gitpr/vue-quality`;
  - `gitpr/php-security`;
  - `gitpr/node-quality`.
- **Comportamento padrão:** nenhum pack é obrigatório. A ausência de pack mantém o comportamento atual do GitPR.
- **Fora de escopo nesta fase:** marketplace remoto, pagamento por pack, sincronização cloud de organização, SSO/RBAC, assinatura criptográfica obrigatória, atualização automática silenciosa, execução de código arbitrário, gestão centralizada de políticas Team/Enterprise.
- **Compatibilidade:** configurações locais já existentes devem continuar funcionando. O pack adiciona uma camada de configuração com precedência documentada, não substitui silenciosamente configurações do usuário.

## 3. Estrutura de arquivos

A skill DEVE adaptar os caminhos ao repositório real, mas o modelo esperado é:

```text
src/domain/policy/
├── policy_types.py               # NOVO — dataclasses/enums do manifesto e configuração efetiva
├── policy_manifest.py            # NOVO — parsing e validação de schema
├── policy_resolver.py            # NOVO — resolve dependências, precedência e configuração efetiva
├── policy_compatibility.py       # NOVO — valida versão mínima do GitPR e referências permitidas
└── policy_checksum.py            # NOVO — checksum local para detectar alteração inesperada

src/application/use_cases/
├── install_policy_pack.py        # NOVO
├── validate_policy_pack.py       # NOVO
├── activate_policy_pack.py       # NOVO
└── resolve_effective_policy.py   # NOVO

src/infrastructure/policy/
├── local_policy_repository.py    # NOVO — leitura/escrita de packs instalados
└── policy_pack_loader.py         # NOVO — carrega YAML e assets declarativos

policy-packs/
├── laravel-quality/
│   ├── policy.yml
│   ├── linter.yml
│   ├── README.md
│   └── CHANGELOG.md
├── vue-quality/
│   ├── policy.yml
│   ├── linter.yml
│   └── README.md
├── php-security/
│   ├── policy.yml
│   ├── linter.yml
│   └── README.md
└── node-quality/
    ├── policy.yml
    ├── linter.yml
    └── README.md

.gitpr/
├── policy.lock.yml               # NOVO — pack(s) ativos, versão resolvida e checksum
└── policy.overrides.yml          # NOVO — overrides explícitos e auditáveis por repositório

core.py                            # ALTERAR — resolve policy efetiva antes de skills/linter/risk
main.py                            # ALTERAR — grupo de comandos `gitpr policy`
config.schema.yml                  # ALTERAR — schema de política ativa e overrides

tests/domain/policy/
├── test_policy_manifest.py
├── test_policy_resolver.py
├── test_policy_compatibility.py
└── test_policy_checksum.py
tests/application/use_cases/
├── test_install_policy_pack.py
├── test_validate_policy_pack.py
└── test_activate_policy_pack.py
tests/integration/
└── test_policy_effect_on_review_linter_risk.py
```

Não duplicar o sistema de plugins caso ele já possua armazenamento, leitura de manifestos e lifecycle compatíveis. Nesse caso, os arquivos podem viver na estrutura de plugins existente, mas o conceito de `policy.yml`, lockfile e resolução de precedência deve ser preservado.

## 4. Contratos de dados obrigatórios

```python
# src/domain/policy/policy_types.py
from dataclasses import dataclass, field
from enum import Enum


class PolicySource(str, Enum):
    BUNDLED = "bundled"
    LOCAL_PATH = "local_path"
    INSTALLED = "installed"


@dataclass
class PackReference:
    name: str                     # ex.: gitpr/laravel-quality
    version: str                  # SemVer exato ou range aceito durante resolução
    source: PolicySource
    path: str | None = None
    checksum: str | None = None


@dataclass
class SkillPolicy:
    skill_name: str               # DEVE estar na lista fixa de get_skill_context
    enabled: bool = True
    additional_context: str | None = None
    required_sections: list[str] = field(default_factory=list)


@dataclass
class SeverityOverride:
    rule_id: str
    severity: str                 # usar enum/severidades reais já existentes no projeto
    reason: str | None = None


@dataclass
class EffectivePolicy:
    packs: list[PackReference]
    enabled_skills: dict[str, SkillPolicy]
    linter_config: dict
    severity_overrides: dict[str, SeverityOverride]
    risk_config: dict
    pr_config: dict
    commit_config: dict
    protected_paths: list[str]
    provenance: dict[str, str]    # chave de config -> pack/override que a definiu
    warnings: list[str]
```

```python
# src/domain/policy/policy_manifest.py
@dataclass
class PolicyManifest:
    name: str
    version: str
    description: str
    min_gitpr_version: str
    license: str | None
    authors: list[str]
    dependencies: list[PackReference]
    skills: list[SkillPolicy]
    linter_file: str | None
    severity_overrides: list[SeverityOverride]
    risk: dict
    pr: dict
    commit: dict
    protected_paths: list[str]
```

## 5. Formato do manifesto

O manifesto deve ser YAML e validado antes de ser ativado. Exemplo estrutural; ajustar chaves ao schema real do projeto:

```yaml
schema_version: 1
name: gitpr/laravel-quality
version: 1.0.0
description: Quality gate para aplicações Laravel.
min_gitpr_version: ">=1.0.0"
license: MIT
authors:
  - GitPR

extends:
  - name: gitpr/php-security
    version: ">=1.0.0 <2.0.0"

skills:
  review:
    enabled: true
    additional_context: |
      Priorize validação, autorização, transações, N+1, migrations,
      filas, idempotência, logs e exposição de dados pessoais.
  pr:
    enabled: true
    required_sections:
      - Impacto de negócio
      - Implementação técnica
      - Riscos
      - Evidência de testes
      - Plano de rollback
  mentor:
    enabled: false

linter:
  preset_file: linter.yml
  severity_overrides:
    - rule_id: SEC-GENERIC-CREDENTIAL-ASSIGNMENT
      severity: critical
      reason: Política Laravel enterprise.

risk:
  critical_paths:
    - app/Http/Middleware/**
    - app/Policies/**
    - app/Providers/**
    - database/migrations/**
    - routes/api.php
  weights:
    database_migration: 25
    no_test_change: 20
  test_patterns:
    - tests/**
    - "**/*Test.php"

pr:
  required_sections:
    - Impacto de negócio
    - Implementação técnica
    - Riscos
    - Evidência de testes
    - Plano de rollback

commit:
  conventional_commits: true
  allowed_types:
    - feat
    - fix
    - refactor
    - test
    - docs

protected_paths:
  - database/migrations/**
  - routes/api.php
```

Regras do formato:

1. `schema_version`, `name`, `version` e `min_gitpr_version` são obrigatórios.
2. `name` deve seguir formato namespace/nome e não conter path traversal.
3. `version` deve obedecer SemVer.
4. `min_gitpr_version` deve ser validado antes da ativação.
5. `skills.<nome>` só pode usar nomes de skills retornados por `get_skill_context`/registro fixo.
6. `additional_context` é texto declarativo; não pode conter instruções de execução de shell, download ou carregamento de arquivo arbitrário.
7. `linter.preset_file` deve ser relativo ao diretório do pack e não pode escapar dele.
8. Nenhum campo pode aceitar segredo, token, chave privada ou URL com credencial.

## 6. Resolução, precedência e composição

### 6.1 Ordem de precedência

A implementação deve produzir configuração efetiva de forma previsível. Ordem da menor para a maior precedência:

1. defaults internos do GitPR;
2. packs dependentes, na ordem topológica de `extends`;
3. pack principal ativo;
4. `.gitpr/policy.overrides.yml` do repositório;
5. configuração local já existente do projeto, quando a chave for explicitamente permitida para override;
6. flags explícitas de CLI;
7. variáveis de ambiente existentes, conforme a convenção atual do projeto.

Se a convenção atual de ambiente/configuração tiver outra precedência, seguir a convenção do projeto e documentá-la. Não criar uma segunda hierarquia isolada.

### 6.2 Regras de merge

- mapas/dicionários: merge profundo somente para chaves declaradas como mescláveis;
- listas de padrões (ex.: `critical_paths`, `test_patterns`, `protected_paths`): união ordenada sem duplicidade;
- `severity_overrides`: a regra mais específica de maior precedência vence, preservando provenance;
- `required_sections`: união ordenada; remoção só pode ocorrer em override explícito com justificativa;
- `additional_context`: concatenar em ordem de precedência, com delimitadores de origem, nunca sobrescrever silenciosamente;
- skills: uma skill não pode ser ativada se não for suportada pelo registro fixo; a tentativa gera erro de validação, não warning.

### 6.3 Dependências e ciclos

- resolver dependências por grafo;
- detectar ciclos em `extends` antes de ativar;
- falhar com mensagem clara contendo a cadeia do ciclo;
- conflito de versões incompatíveis deve impedir ativação;
- nenhum download remoto deve ocorrer automaticamente para resolver dependência nesta primeira versão.

## 7. Lockfile, proveniência e auditabilidade

Ao ativar um pack, criar/atualizar `.gitpr/policy.lock.yml` com:

- nome e versão exata de cada pack resolvido;
- origem local/bundled/instalada;
- checksum SHA-256 de `policy.yml` e assets declarativos carregados;
- versão do GitPR usada para validar;
- data/hora de ativação;
- dependências resolvidas;
- schema version.

Requisitos:

1. O lockfile deve ser versionável no Git.
2. Se o conteúdo de um pack ativo mudar sem atualização correspondente do checksum, o GitPR deve avisar e exigir `gitpr policy validate`/reativação explícita antes de aplicar a nova versão.
3. A saída de review/linter/risk deve poder incluir `policy name@version` quando uma política estiver ativa, mas nunca deve expor conteúdo de segredo — secrets são inválidos no manifesto de qualquer forma.
4. `.gitpr/policy.overrides.yml` deve registrar overrides com justificativa para campos sensíveis, como redução de severidade de regra ou remoção de caminho protegido.

## 8. Integração com core.py e fluxos existentes

1. Resolver a `EffectivePolicy` uma vez por execução, logo após carregar configuração local e antes de montar skills/linter/risk.
2. Passar a política efetiva por injeção de dependência para:
   - `get_skill_context`: habilitar skill fixa e anexar `additional_context` validado;
   - motor de linter: carregar `preset_file` e aplicar `severity_overrides`;
   - risk scoring: combinar caminhos críticos, pesos e padrões de teste;
   - geração de PR: incluir `required_sections` e caminhos protegidos, quando suportado;
   - geração de commit: aplicar convenções permitidas, quando suportado.
3. Não espalhar leitura de `policy.yml` em `core.py`, TUI, linter e AI providers. Somente `policy_resolver` pode fazer parsing e composição de manifestos.
4. Se não houver pack ativo, retornar `EffectivePolicy` vazio/default e preservar comportamento atual.
5. Exibir em logs/TUI uma linha curta quando pack estiver ativo, por exemplo: `Policy: gitpr/laravel-quality@1.0.0`.
6. Não incluir automaticamente `additional_context` de pack em prompts sem validar limite de tamanho. Definir limite configurável e retornar erro/aviso claro se o contexto exceder o orçamento aceito pelo provider/pipeline existente.

## 9. Packs oficiais iniciais

### 9.1 `gitpr/laravel-quality`

Foco: Form Requests, `Policy`/`Gate`, autorização, transações, N+1, migrations reversíveis, jobs/queues, idempotência, logs e dados pessoais.

Ativa/referencia somente skills fixas existentes e configura caminhos Laravel conhecidos. Não pressupor que todos os projetos Laravel usem a mesma estrutura; padrões devem ser customizáveis no override local.

### 9.2 `gitpr/vue-quality`

Foco: props/emits, estado reativo, side effects, cleanup de listeners, acessibilidade, tratamento de loading/error, componentes grandes e testes de componente.

### 9.3 `gitpr/php-security`

Foco: validação, query parametrizada, escaping de saída, serialização insegura, credenciais hardcoded, arquivos sensíveis e configuração de produção. Pode depender do preset de secret scanning/bridge SAST quando estes estiverem disponíveis, mas nunca deve forçar a instalação de binários externos.

### 9.4 `gitpr/node-quality`

Foco: validação de input, tratamento de promises, erros assíncronos, dependências, secrets, configuração de ambiente e testes.

Os packs iniciais devem ser pequenos, opinativos e testáveis. Não tentar cobrir todas as práticas de cada ecossistema na primeira versão.

## 10. CLI e UX

### `gitpr policy validate`

Deve informar:

- schema válido/inválido;
- compatibilidade da versão do GitPR;
- skills suportadas/inválidas;
- dependências e conflitos;
- arquivos linter referenciados e paths inválidos;
- checksum calculado;
- warnings de campos desconhecidos ou contexto excessivo.

### `gitpr policy show`

Deve mostrar:

- packs ativos e dependências;
- ordem de precedência;
- skills efetivas e origem do contexto;
- regras de severidade alteradas;
- paths críticos/protegidos;
- warnings e overrides locais;
- provenance de campos relevantes.

### `gitpr policy init --stack`

Deve:

1. detectar a stack se possível, usando detector existente;
2. sugerir pack oficial compatível;
3. pedir confirmação antes de criar lockfile ou override no repositório;
4. validar o pack antes de ativar;
5. nunca sobrescrever `.gitpr/policy.lock.yml` ou `.gitpr/policy.overrides.yml` existente sem confirmação explícita.

## 11. Configuração

```yaml
policy:
  enabled: true
  active:
    - name: gitpr/laravel-quality
      version: "1.0.0"
      source: bundled
  context_max_characters: 12000
  require_lockfile_checksum_match: true
  allow_local_overrides: true
```

Configuração local de overrides:

```yaml
# .gitpr/policy.overrides.yml
overrides:
  severity_overrides:
    - rule_id: SEC-GENERIC-CREDENTIAL-ASSIGNMENT
      severity: warning
      reason: Valores de fixture sintéticos neste repositório.
  risk:
    critical_paths:
      add:
        - modules/finance/**
  pr:
    required_sections:
      add:
        - Impacto LGPD
```

A syntax de `add`, `remove` ou substituição deve ser alinhada ao formato de configuração já existente. Se não houver suporte consistente, limitar a primeira versão a operações aditivas e overrides explícitos de valor simples.

## 12. Testes obrigatórios — critérios de aceite

1. **Validação de schema:** manifesto válido passa; campos obrigatórios ausentes, versão SemVer inválida, nome inválido e campos desconhecidos em modo estrito falham com mensagem clara.
2. **Skills fixas:** pack que referencia skill inexistente em `get_skill_context` falha antes da ativação; pack com skills suportadas é resolvido corretamente.
3. **Compatibilidade:** `min_gitpr_version` incompatível impede ativação; versão compatível é aceita.
4. **Dependências:** resolução topológica correta; ciclo em `extends` falha exibindo a cadeia; conflito de versão falha de forma determinística.
5. **Precedência:** fixture contendo default, dependência, pack principal, override local, config e flag CLI produz `EffectivePolicy` com valores e provenance corretos.
6. **Merge de listas:** caminhos críticos/protegidos e seções obrigatórias são unidos sem duplicidade e em ordem previsível.
7. **Override de severidade:** override válido altera apenas a regra indicada; outras regras permanecem sem alteração; provenance identifica a origem.
8. **Lockfile/checksum:** ativação gera lockfile versionável; alteração posterior em asset do pack gera mismatch detectável; revalidação/reativação atualiza checksum de forma explícita.
9. **Sem execução arbitrária:** manifestos contendo campos de shell, path traversal, URL com credencial ou referência de arquivo fora do diretório do pack devem falhar; nenhum subprocess/rede deve ser chamado durante validação de pack local.
10. **Não-regressão sem pack:** sem política ativa, skills, linter, risk scoring, review e geração de PR mantêm o comportamento anterior.
11. **Integração Laravel:** ativar `gitpr/laravel-quality` em fixture Laravel altera apenas configurações declaradas (paths, contexto, regras) e o review/linter/risk recebe a política efetiva correta.
12. **Contexto limitado:** contexto adicional acima do limite configurado gera aviso/erro controlado, sem enviar prompt excessivo ao provider.
13. **CLI:** `list`, `validate`, `show`, `use` e `init --stack` seguem a convenção de parsing/saída do projeto; comandos de escrita pedem confirmação explícita antes de alterar arquivos.

Critério de feature completa: um repositório Laravel de fixture pode ativar `gitpr/laravel-quality@1.0.0`, gerar lockfile, executar review/linter/risk com configuração efetiva rastreável, e continuar reproduzível em outra máquina a partir de arquivos versionados, sem depender de download remoto ou skills dinâmicas.

## 13. Ordem de execução recomendada

1. Inventariar skills fixas, linter YAML, risk config, plugin system e precedência atual de config.
2. Implementar contratos de domínio e validação estrita de `PolicyManifest`, sem instalação nem integração.
3. Implementar `policy_resolver` com dependências, precedência, merge e provenance; testar exaustivamente com fixtures pequenas.
4. Implementar lockfile/checksum e validação de integridade local.
5. Implementar primeiro pack bundled mínimo: `gitpr/laravel-quality`, com `policy.yml`, `linter.yml` e testes de integração.
6. Integrar `EffectivePolicy` em skills, linter e risk scoring apenas pelos pontos de entrada centralizados.
7. Implementar comandos somente leitura: `list`, `validate`, `show`.
8. Implementar comandos com escrita: `use`, `install` e `init --stack`, com confirmação explícita.
9. Adicionar `vue-quality`, `php-security` e `node-quality` incrementalmente, cada um com fixture e testes próprios.
10. Atualizar schema, README, CLI help e documentação de autoria/versionamento de packs.
11. Rodar a suíte completa antes de considerar a feature concluída.

Cada etapa deve ser um commit/PR isolado e revisável. Não começar por registry remoto ou marketplace; validar primeiro que packs locais versionados resolvem o problema de padronização entre repositórios.

## 14. Riscos e dependências

- **Dependência:** `get_skill_context` é a fonte de verdade de skills. Packs não podem contornar esse mecanismo.
- **Dependência:** modelo de linter e de risk scoring precisa estar estável o suficiente para receber configuração declarativa.
- **Dependência:** plugin system pode ser reutilizado, mas somente após confirmar compatibilidade com lockfile, checksum e validação de manifestos.
- **Risco:** contexto adicional em prompt pode conflitar com skill base. Preservar ordem, delimitadores de origem e limite de tamanho.
- **Risco:** overrides de severidade podem enfraquecer segurança. Exigir justificativa e provenance para redução de severidade.
- **Risco:** múltiplos packs podem produzir regras contraditórias. Falhar em conflitos não resolvíveis; não escolher vencedor silenciosamente.
- **Risco:** packs muito amplos viram documentos de regras difíceis de manter. Iniciar com packs pequenos e bem testados por stack.
- **Risco:** distribuição remota sem integridade cria risco de supply chain. Permanecer local/bundled inicialmente e registrar checksum.

## 15. Fora de escopo

- Marketplace remoto ou catálogo público de packs.
- Atualização OTA, download automático ou registry hospedado.
- Cobrança/licenciamento de packs premium.
- SSO, RBAC ou aprovação administrativa de políticas.
- Assinatura criptográfica obrigatória e verificação de identidade do autor.
- Execução de scripts/hooks/código Python dentro de packs.
- Skills arbitrárias descobertas dinamicamente.
- Sincronização cloud de organização.
- Enforcement bloqueante no CI; será tratado em `gitpr check` e Policy Gates.

## 16. Encaixe estratégico

Policy Packs são a fundação do futuro plano Team: traduzem skills, linter, risco e convenções individuais em uma política de engenharia versionável, auditável e compartilhável. Nesta primeira versão devem permanecer locais/bundled e no tier Free/Community, porque o valor imediato é adoção e padronização dentro de repositórios. A monetização futura deve estar na colaboração: registry privado, sincronização organizacional, aprovação de mudanças, auditoria, dashboard e suporte — não no bloqueio do uso local de packs.
