# SPEC — GitPR Baseline & Auditável Suppressions

> Documento de especificação técnica para implementação via Claude Code skill.
> Escopo: permitir adoção progressiva do GitPR em repositórios legados, classificando achados como novos, existentes, resolvidos, ignorados ou dívida aceita; com supressões auditáveis, justificadas e versionáveis em Git.

## 0. Contexto obrigatório antes de codificar

Antes de gerar qualquer código, a skill DEVE:

1. Ler `core.py` e o pipeline atual de review/linter para confirmar o modelo real de finding: campos obrigatórios, severidades, categorias, arquivo, linha, fonte (`ai`/`linter`/`external`), mensagem, sugestão e mecanismo de bloqueio.
2. Confirmar se já existe um identificador estável de finding (`fingerprint`), hash de regra ou mecanismo equivalente. Se não existir, esta feature deve implementá-lo como pré-requisito, pois baseline sem fingerprint estável não permite classificar corretamente achados entre execuções.
3. Confirmar como o GitPR hoje obtém o diff e a base de comparação (`git diff`, `--base`, `--review-pr`). O baseline deve operar sobre a mesma representação normalizada de findings, sem chamar `git diff` de forma paralela.
4. Verificar se o projeto já tem mecanismo de supressão por regra/linha/arquivo (comentário inline, config, etc.). Se não existir, esta feature deve implementar supressão declarativa versionada no baseline, sem depender de comentários que podem conflitar com convenções do usuário.
5. Confirmar como o GitPR hoje persiste resultados de review (cache, arquivo local, saída JSON) para decidir onde o baseline lê os findings e como evita reprocessamento desnecessário.
6. Verificar a estrutura de `gitpr check`, SARIF e Policy Packs, se já implementados ou especificados. O baseline deve ser consumível por esses fluxos futuros, mas não deve depender deles nesta entrega.
7. Confirmar o formato de configuração local (`.gitpr/config.yml`, YAML, variáveis de ambiente) e a precedência de overrides já estabelecida, para que baseline/overrides não conflitem com Policy Packs ou configuração local.

Não prosseguir sem completar os passos 1–4. Se o modelo de finding não tiver fingerprint estável, implementar primeiro essa fundação, pois sem ela a classificação entre novo/existente/resolvido é não determinística.

## 1. Escopo da feature

- **Objetivo:** permitir que uma equipe adote o GitPR em código legado sem transformar milhares de problemas pré-existentes em falha de pipeline, mantendo visibilidade e rastreabilidade de dívida técnica.
- **Comandos novos:**
  - `gitpr baseline create` — cria/atualiza baseline a partir do resultado do review/linter atual.
  - `gitpr baseline show` — lista resumo do baseline: contagem por status, regra, severidade e arquivo.
  - `gitpr baseline validate` — valida schema, checksums e compatibilidade.
  - `gitpr baseline update` — atualiza baseline após correção/aceite, preservando histórico de mudanças.
  - `gitpr baseline suppress <finding-id> --reason <texto>` — cria supressão auditável.
  - `gitpr baseline unsuppress <finding-id>` — remove supressão.
  - integração automática com `gitpr -r`, `gitpr --review-pr <n>` e `gitpr check` quando baseline existir.
- **Comportamento padrão:** se não houver baseline, o comportamento atual do review/linter não muda. A criação de baseline é sempre explícita.
- **Classificação obrigatória de achados:**
  - `new` — introduzido ou modificado no diff atual;
  - `existing` — já presente no baseline;
  - `resolved` — estava no baseline e não aparece mais;
  - `ignored` — suprimido por regra com justificativa;
  - `accepted_debt` — dívida técnica reconhecida, com dono e prazo opcional.
- **Fora de escopo nesta fase:** dashboard web, sincronização cloud de baseline, aprovação administrativa, assinatura criptográfica obrigatória, varredura retroativa de todo histórico Git, integração com Jira/Linear para dívida técnica, marketplace de supressões.
- **Compatibilidade:** a existência de baseline não deve alterar o comportamento do review sem baseline. Regras de severidade e bloqueio continuam sendo definidas pelo linter/review/Policy Pack, não pelo baseline.

## 2. Árvore de arquivos a criar/alterar

```text
src/domain/baseline/
├── baseline_types.py             # NOVO — dataclasses/enums
├── baseline_manifest.py          # NOVO — parsing e validação de schema
├── baseline_comparator.py        # NOVO — compara findings atuais vs. baseline
├── baseline_fingerprint.py       # NOVO ou reaproveitamento — fingerprint estável
└── suppression_policy.py         # NOVO — regras de supressão/aceitação

src/application/use_cases/
├── create_baseline.py            # NOVO
├── compare_against_baseline.py   # NOVO
├── suppress_finding.py           # NOVO
└── update_baseline.py            # NOVO

src/infrastructure/baseline/
└── local_baseline_repository.py  # NOVO — leitura/escrita de baseline versionável

.gitpr/
└── baseline.json                 # NOVO — baseline versionável no Git

core.py                            # ALTERAR — integrar baseline no review/check
main.py                            # ALTERAR — grupo de comandos `gitpr baseline`
config.schema.yml                  # ALTERAR — schema de baseline/suppressões

tests/domain/baseline/
├── test_baseline_manifest.py
├── test_baseline_comparator.py
├── test_baseline_fingerprint.py
└── test_suppression_policy.py
tests/application/use_cases/
├── test_create_baseline.py
├── test_compare_against_baseline.py
└── test_suppress_finding.py
tests/integration/
└── test_baseline_effect_on_review_check.py
```

A skill DEVE adaptar caminhos à estrutura real. Não duplicar parser de findings ou mecanismo de cache se já existirem.

## 3. Contrato de dados obrigatório

```python
# src/domain/baseline/baseline_types.py
from dataclasses import dataclass, field
from enum import Enum


class BaselineStatus(str, Enum):
    NEW = "new"
    EXISTING = "existing"
    RESOLVED = "resolved"
    IGNORED = "ignored"
    ACCEPTED_DEBT = "accepted_debt"


class SuppressionScope(str, Enum):
    FINDING = "finding"
    RULE = "rule"
    FILE = "file"
    LINE = "line"


@dataclass
class FindingFingerprint:
    fingerprint: str               # SHA-256 estável
    rule_id: str
    category: str
    file_path: str
    line_start: int
    line_end: int
    source: str                    # ai | linter | external
    severity: str


@dataclass
class BaselineEntry:
    fingerprint: str
    rule_id: str
    category: str
    file_path: str
    line_start: int
    line_end: int
    severity: str
    source: str
    status: BaselineStatus
    first_seen_commit: str | None
    last_seen_commit: str | None
    first_seen_date: str | None    # ISO 8601
    last_seen_date: str | None
    suppressed: bool = False
    suppression_reason: str | None = None
    suppression_scope: SuppressionScope = SuppressionScope.FINDING
    accepted_debt_owner: str | None = None
    accepted_debt_due_date: str | None = None
    provenance: dict = field(default_factory=dict)


@dataclass
class BaselineManifest:
    schema_version: int
    policy_name: str | None
    policy_version: str | None
    gitpr_version: str
    created_at: str
    updated_at: str
    entries: list[BaselineEntry]
    checksum: str
```

```python
# src/domain/baseline/baseline_comparator.py
@dataclass
class ComparedFinding:
    fingerprint: str
    current_severity: str
    baseline_status: BaselineStatus
    is_blocking: bool              # False para existing/resolved/ignored/accepted_debt
    reason: str
```

```python
# src/application/use_cases/compare_against_baseline.py
def compare_against_baseline(
    findings: list,                 # modelo de finding já existente
    baseline: BaselineManifest,
) -> list[ComparedFinding]:
    ...
```

## 4. Fingerprint estável — pré-requisito crítico

O fingerprint deve ser determinístico e estável entre execuções para o mesmo problema técnico, mesmo que a IA reformule a mensagem.

Regras obrigatórias:

1. Fingerprint deve ser calculado por hash SHA-256 de campos estáveis:
   - `rule_id`;
   - `category`;
   - `file_path` normalizado;
   - `line_start` e `line_end` normalizados;
   - `source`;
   - versão da regra/política, quando disponível;
   - hash do trecho de código relevante, se disponível na representação normalizada do diff.
2. Fingerprint não deve incluir:
   - texto livre da IA reformulado;
   - timestamp;
   - provider/modelo de IA;
   - nome de branch;
   - caminho absoluto da máquina;
   - conteúdo de segredo.
3. Se o motor de review de IA não fornecer regra estável, usar categoria + arquivo + intervalo de linhas normalizado como fallback, marcando confiança baixa.
4. Fingerprint deve ser documentado e versionado (`fingerprint_version`), pois mudanças no algoritmo exigem migração do baseline.
5. Dois findings distintos na mesma linha podem compartilhar fingerprint somente se representarem a mesma regra/categoria; caso contrário, diferenciar por `rule_id`/categoria.

## 5. Algoritmo — comparação e classificação

1. Executar review/linter normalmente e obter findings atuais.
2. Carregar baseline existente, se houver.
3. Calcular fingerprint de cada finding atual.
4. Comparar contra entradas do baseline:
   - fingerprint presente e não suprimido → `existing`;
   - fingerprint presente e suprimido → `ignored`;
   - fingerprint presente com status `accepted_debt` → `accepted_debt`;
   - fingerprint ausente → `new`;
   - fingerprint presente no baseline mas ausente no diff atual → `resolved`.
5. Para findings `new`, aplicar severidade e bloqueio normalmente.
6. Para `existing`, não bloquear por padrão, mas exibir contagem e permitir promoção explícita para blocker via override/política.
7. Para `resolved`, registrar a resolução no baseline atualizado, preservando histórico (`first_seen`, `last_seen`, data de resolução).
8. Para `ignored`/`accepted_debt`, exibir motivo, autor da supressão e data — nunca esconder silenciosamente.
9. Atualizar baseline somente por comando explícito (`baseline create`/`update`), nunca automaticamente em cada review.

## 6. Supressões auditáveis

### 6.1 Regras de supressão

- Toda supressão exige `reason` não vazio.
- Supressão pode ser por finding, regra, arquivo ou linha.
- Supressão por arquivo/regra deve registrar escopo e justificativa.
- Redução de severidade de finding `blocker` exige justificativa explícita e deve ficar registrada no baseline/override.
- Supressão não remove o finding do histórico; apenas altera seu status.
- Supressão deve ser versionável no Git e auditável.

### 6.2 Dívida aceita

- `accepted_debt` exige:
  - dono (pessoa/time responsável);
  - justificativa;
  - prazo opcional;
  - data de aceitação;
  - provenance (quem aceitou, qual política).
- Dívida aceita não deve bloquear fluxo por padrão, mas deve aparecer em relatórios de dívida técnica.
- Expiração de prazo deve gerar warning informativo, não falha silenciosa.

## 7. Lockfile e provenance

`.gitpr/baseline.json` deve conter:

- schema version;
- versão do GitPR;
- política ativa (se houver Policy Pack);
- checksum SHA-256 do baseline;
- data de criação/atualização;
- entradas com fingerprint, status, severidade, datas e provenance.

Requisitos:

1. Baseline deve ser versionável no Git.
2. Alteração manual não rastreada deve gerar mismatch de checksum e exigir validação/reativação.
3. Toda mudança de status deve preservar histórico (`first_seen`, `last_seen`, datas).
4. Nenhum conteúdo de segredo deve ser persistido no baseline — segredos são inválidos no finding de qualquer forma.

## 8. Integração com review, check e Policy Packs

1. Resolver baseline uma vez por execução, após carregar configuração local e antes de review/linter/risk.
2. Passar baseline por injeção de dependência para:
   - motor de review: classificar findings como new/existing/resolved;
   - linter: aplicar supressões por regra/linha;
   - risk scoring: preservar score bruto, mas marcar evidências aceitas;
   - `gitpr check`: aplicar thresholds apenas sobre `new` findings;
   - SARIF: exportar status de baseline quando suportado.
3. Se não houver baseline, retornar comportamento atual sem alteração.
4. Exibir em logs/TUI uma linha curta quando baseline estiver ativo, por exemplo: `Baseline: 120 existing, 3 new, 2 resolved`.
5. Não incluir automaticamente baseline em prompts sem validar limite de tamanho. Definir limite configurável e retornar erro/aviso claro se o contexto exceder o orçamento aceito pelo provider/pipeline existente.

## 9. Configuração

```yaml
baseline:
  enabled: true
  path: ".gitpr/baseline.json"
  require_lockfile_checksum_match: true
  allow_local_overrides: true
  default_status_for_new: "new"
  suppress_blocker_requires_reason: true
  accepted_debt_requires_owner: true
```

Configuração local de overrides:

```yaml
# .gitpr/baseline.overrides.yml
overrides:
  suppressions:
    - fingerprint: "sha256:..."
      scope: finding
      reason: "Segredo sintético em fixture de teste."
  accepted_debt:
    - fingerprint: "sha256:..."
      owner: "time-backend"
      due_date: "2026-12-31"
      reason: "Dívida técnica conhecida, migração planejada."
```

A syntax de `add`, `remove` ou substituição deve ser alinhada ao formato de configuração já existente. Se não houver suporte consistente, limitar a primeira versão a operações aditivas e overrides explícitos de valor simples.

## 10. CLI e UX

### `gitpr baseline create`

Deve:

1. executar review/linter atual;
2. calcular fingerprints;
3. criar/atualizar baseline;
4. exibir resumo (new/existing/resolved/ignored/accepted_debt);
5. pedir confirmação antes de sobrescrever baseline existente sem justificativa.

### `gitpr baseline show`

Deve mostrar:

- resumo por status;
- top regras/severidades;
- findings suprimidos e justificativas;
- dívida aceita com dono/prazo;
- provenance de mudanças recentes.

### `gitpr baseline suppress`

Deve:

1. localizar finding por fingerprint/id;
2. exigir reason;
3. aplicar scope correto;
4. atualizar baseline com provenance;
5. pedir confirmação antes de escrever.

### `gitpr baseline validate`

Deve informar:

- schema válido/inválido;
- compatibilidade da versão do GitPR;
- checksum match/mismatch;
- fingerprints duplicados/inválidos;
- warnings de campos desconhecidos ou contexto excessivo.

## 11. Testes obrigatórios — critérios de aceite

1. **Fingerprint determinístico:** mesma entrada produz exatamente o mesmo fingerprint em execuções repetidas; mudança de provider/modelo não deve alterar fingerprint se campos estáveis forem iguais.
2. **Classificação new/existing/resolved:** fixture contendo baseline e findings atuais deve classificar corretamente cada caso.
3. **Supressão auditável:** supressão exige reason; finding suprimido aparece como `ignored`, nunca desaparece silenciosamente.
4. **Dívida aceita:** accepted_debt exige owner/reason; expiração gera warning, não falha silenciosa.
5. **Bloqueio de fluxo:** apenas findings `new` com severidade bloqueante devem bloquear commit/PR; existing/resolved/ignored/accepted_debt não bloqueiam por padrão.
6. **Não-regressão sem baseline:** review, linter, risk scoring e fluxo existente mantêm comportamento anterior.
7. **Lockfile/checksum:** criação/atualização gera checksum; alteração manual não rastreada gera mismatch detectável; revalidação atualiza checksum de forma explícita.
8. **Privacidade/offline:** comparação e baseline não abrem rede, não enviam código e não gravam segredos em logs/telemetria.
9. **Integração SARIF/check:** baseline deve poder ser consumido por `gitpr check`/SARIF quando essas features existirem, sem conflito de schema.
10. **Integração com Policy Packs:** policy pack pode fornecer regras de baseline/supressão, mas não pode contornar validação de schema/fingerprint.
11. **CLI:** `create`, `show`, `validate`, `suppress`, `unsuppress` e `update` seguem a convenção de parsing/saída do projeto; comandos de escrita pedem confirmação explícita antes de alterar arquivos.

Critério de feature completa: um repositório legado de fixture pode criar baseline, rodar review/linter/risk com classificação correta de new/existing/resolved/ignored/accepted_debt, e continuar reproduzível em outra máquina a partir de arquivos versionados, sem depender de download remoto ou skills dinâmicas.

## 12. Ordem de execução recomendada

1. Inventariar modelo de finding, severidades, review/linter/risk e precedência atual de config.
2. Implementar contratos de domínio e validação estrita de `BaselineManifest`, sem integração.
3. Implementar fingerprint estável e testes de determinismo; sem fingerprint estável, não prosseguir.
4. Implementar `baseline_comparator` com fixtures pequenas cobrindo todos os status.
5. Implementar regras de supressão/dívida aceita com validação de reason/owner.
6. Implementar `baseline_manifest` e lockfile/checksum.
7. Implementar `create_baseline` e `compare_against_baseline` em modo somente leitura.
8. Integrar ao review/linter/risk apenas pelos pontos de entrada centralizados.
9. Implementar comandos somente leitura: `show`, `validate`.
10. Implementar comandos com escrita: `create`, `update`, `suppress`, `unsuppress`, com confirmação explícita.
11. Adicionar integração com `gitpr check`/SARIF quando essas features existirem.
12. Atualizar schema, README, CLI help e documentação de autoria/versionamento de baseline.
13. Rodar a suíte completa antes de considerar a feature concluída.

Cada etapa deve ser um commit/PR isolado e revisável. Não começar por dashboard/remoto; validar primeiro que baseline local versionado resolve o problema de adoção em legado.

## 13. Riscos e dependências

- **Dependência:** modelo de finding normalizado; sem ele, baseline não pode classificar de forma confiável.
- **Dependência:** fingerprint estável; sem ele, classificação entre execuções é não determinística.
- **Dependência:** motor de linter/review precisa estar estável para receber baseline/supressões.
- **Dependência futura:** Policy Packs devem poder fornecer regras de baseline/supressão; manter regras configuráveis e separar código de configuração.
- **Risco:** fingerprint baseado apenas em linha pode gerar falsos positivos/negativos em diffs grandes. Usar hash combinado de campos estáveis e documentar limitações.
- **Risco:** supressões podem enfraquecer segurança. Exigir reason e provenance para redução de severidade.
- **Risco:** baseline muito grande pode virar arquivo difícil de manter. Iniciar com baseline pequeno e bem testado, com filtros configuráveis.
- **Risco:** dívida aceita sem dono/prazo vira dívida invisível. Exigir owner e reason.

## 14. Fora de escopo

- Dashboard web ou agregação entre repositórios.
- Telemetria remota de baseline/supressões.
- Sincronização cloud de organização.
- Aprovação administrativa de supressões.
- SSO/RBAC.
- Varredura retroativa de todo histórico Git.
- Integração com Jira/Linear para dívida técnica.
- Marketplace de supressões.
- Enforcement bloqueante no CI; será tratado em `gitpr check` e Policy Gates.

## 15. Encaixe estratégico

Baseline e supressões auditáveis são a fundação da adoção em legado e do futuro plano Team: traduzem findings individuais em uma política de dívida técnica versionável, auditável e compartilhável. Nesta primeira versão devem permanecer locais/bundled e no tier Free/Community, porque o valor imediato é adoção progressiva em repositórios legados. A monetização futura deve estar na colaboração: baseline compartilhado, aprovação de supressões, auditoria, dashboard de dívida técnica e suporte — não no bloqueio do uso local de baseline.


## 16. Documentação

1. Crie a sua documentação própria em docs/
2. Adicione em README.md e em suas versões em outros idiomas
3. Se alguma variável ambiente foi criada e utilizada nesta feature adicionar na interface de Configuração na seção correspondente ou crie nova