# SPEC — GitPR Local Risk Scoring

> Documento de especificação técnica para implementação via Claude Code skill.
> Escopo: calcular uma pontuação de risco local, determinística e explicável para cada arquivo alterado e para o PR/diff completo, usando sinais do Git e do repositório: áreas críticas, ausência de testes, migrations, histórico de bugs/reversões, tamanho da mudança, findings e acoplamento. O resultado deve priorizar a atenção humana e orientar o review de IA, sem substituir a classificação de severidade nem bloquear o fluxo por si só.

## 0. Contexto obrigatório antes de codificar

Antes de gerar qualquer código, a skill DEVE:

1. Ler o pipeline atual de diff/review em `core.py` e identificar o ponto comum usado por review local, `--review-pr` e demais entradas de diff. O risk scoring deve consumir uma representação normalizada do diff, não chamar `git diff` de forma paralela para cada feature.
2. Verificar se já existe um modelo canônico de finding, risk score, métricas de histórico ou classificação de arquivos. Reaproveitar os contratos existentes; não criar um segundo modelo de finding nem conflitar com a severidade do linter/review.
3. Ler `blame_engine.py` e confirmar como o projeto já acessa `git blame`, autores, datas, commits e classificação histórica. Reaproveitar a infraestrutura para os sinais de histórico, sem duplicar parsing de blame.
4. Verificar se já existem utilitários para:
   - obter arquivos alterados e estatísticas do diff;
   - localizar commits de correção/reversão;
   - detectar testes correspondentes;
   - reconhecer migrations, autenticação, pagamentos, infraestrutura e outros caminhos críticos;
   - contar histórico de alterações por arquivo.
5. Confirmar o mecanismo de cache e telemetria local. O score deve ser reproduzível, não enviar código/histórico para serviços externos e não incluir conteúdo sensível em logs.
6. Confirmar como o map-reduce/smart excludes trata arquivos grandes, gerados, binários e lockfiles. O score deve usar exclusões consistentes, mas nunca esconder silenciosamente uma alteração crítica.
7. Confirmar a interface real do provider de IA. O cálculo do score deve ser local e concluído antes da IA; a integração com o review deve enviar apenas o score e os motivos estruturados, conforme configuração, não uma chamada adicional obrigatória.

Não prosseguir sem completar os passos 1–4. Se algum sinal não puder ser obtido com confiabilidade, ele deve ser marcado como indisponível e não receber valor implícito que distorça a pontuação.

## 1. Escopo da feature

- **Objetivo:** calcular risco por arquivo e risco agregado do PR/diff, explicar os fatores que contribuíram para o resultado e disponibilizar os dados para terminal, TUI, review de IA, CI e formatos estruturados futuros.
- **Comandos/flags:**
  - `gitpr risk` — calcula o risco do diff local atual.
  - `gitpr risk --file <path>` — calcula o risco de um arquivo específico.
  - `gitpr risk --format {text|json}` — seleciona saída humana ou estruturada.
  - `gitpr risk --base <ref>` — calcula contra uma base Git explícita.
  - integração opcional com `gitpr -r`, `gitpr --review-pr <n>` e `gitpr pr`, reutilizando o mesmo resultado já calculado.
- **Comportamento padrão:** somente leitura, local e sem alteração no working tree. O score não bloqueia commit, PR ou merge automaticamente nesta fase.
- **Unidades de análise:**
  - arquivo alterado;
  - PR/diff agregado;
  - opcionalmente hunk, se a representação normalizada existente já suportar essa granularidade.
- **Fora de escopo nesta fase:** treinamento de modelo estatístico, envio de telemetria para dashboard remoto, scoring baseado em comportamento individual de desenvolvedores, estimativa de probabilidade numérica de incidente em produção, enforcement organizacional de thresholds e configuração remota via Policy Packs.
- **Compatibilidade:** o risk score é informativo. Não altera `severity` dos findings, regras de linter, resultado de `gitpr fix` ou códigos de saída existentes. Enforcement por threshold será especificado posteriormente no `gitpr check`/CI.

## 2. Árvore de arquivos a criar/alterar

```
src/domain/risk/
├── risk_types.py                 # NOVO — contratos e enums
├── risk_rules.py                 # NOVO — pesos e regras determinísticas
├── risk_calculator.py            # NOVO — cálculo puro por arquivo/PR
└── risk_explanation.py           # NOVO — motivos legíveis e ordenados

src/application/use_cases/
└── calculate_risk.py             # NOVO — orquestra diff, Git history, testes e findings

src/infrastructure/git/
├── risk_history_reader.py        # NOVO ou extensão de utilitários existentes
└── test_matcher.py               # NOVO ou extensão de detecção existente

core.py                            # ALTERAR — registrar `gitpr risk` e integrar review/PR
main.py                            # ALTERAR — CLI e formatos de saída
config.schema.yml                  # ALTERAR — configuração de pesos/padrões

src/ui/                            # ALTERAR somente se houver dashboard/TUI de review compatível

tests/domain/risk/
├── test_risk_calculator.py
├── test_risk_rules.py
└── test_risk_explanation.py
tests/application/use_cases/
└── test_calculate_risk.py
tests/infrastructure/git/
├── test_risk_history_reader.py
└── test_test_matcher.py
```

A skill DEVE adaptar a árvore aos caminhos reais do repositório. Não criar diretórios paralelos se já houver uma camada equivalente.

## 3. Contrato de dados obrigatório

```python
# src/domain/risk/risk_types.py
from dataclasses import dataclass, field
from enum import Enum


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class RiskSignal(str, Enum):
    CRITICAL_PATH = "critical_path"
    SECURITY_SENSITIVE = "security_sensitive"
    DATABASE_MIGRATION = "database_migration"
    INFRASTRUCTURE = "infrastructure"
    LARGE_DIFF = "large_diff"
    NO_TEST_CHANGE = "no_test_change"
    TEST_PRESENT = "test_present"
    HISTORICAL_BUGS = "historical_bugs"
    HISTORICAL_REVERTS = "historical_reverts"
    HIGH_CHURN = "high_churn"
    HIGH_COUPLING = "high_coupling"
    FINDING_BLOCKER = "finding_blocker"
    FINDING_CRITICAL = "finding_critical"
    FINDING_WARNING = "finding_warning"
    NEW_FILE = "new_file"
    SIGNAL_UNAVAILABLE = "signal_unavailable"


@dataclass
class RiskEvidence:
    signal: RiskSignal
    points: float
    summary: str
    details: dict = field(default_factory=dict)
    confidence: str = "medium"  # high | medium | low


@dataclass
class FileRisk:
    file_path: str
    score: float                  # 0.0–100.0
    level: RiskLevel
    changed_lines: int
    changed_hunks: int
    evidence: list[RiskEvidence]
    related_test_files: list[str]
    signals_available: list[RiskSignal]
    warnings: list[str]


@dataclass
class PullRequestRisk:
    score: float                  # 0.0–100.0
    level: RiskLevel
    files: list[FileRisk]
    evidence: list[RiskEvidence]  # evidências agregadas, ordenadas por impacto
    total_changed_files: int
    total_changed_lines: int
    tests_changed: bool
    critical_files: list[str]
    analysis_version: str
    warnings: list[str]
```

## 4. Modelo de pontuação

O cálculo deve ser determinístico e normalizado em `0.0–100.0`. Os pesos abaixo são defaults iniciais e devem ficar configuráveis:

| Sinal | Pontos padrão | Condição inicial |
|---|---:|---|
| Caminho crítico | +25 | autenticação, autorização, permissões, pagamentos, dados pessoais, secrets, CI/CD, infraestrutura |
| Security-sensitive | +25 | arquivo/configuração de segurança, criptografia, sessão, middleware de acesso |
| Migration/schema | +20 | migration, alteração de schema, seed estrutural ou contrato de banco |
| Infraestrutura/deploy | +20 | Docker, Terraform, Kubernetes, pipelines, configuração de produção |
| Sem teste correspondente | +15 | mudança de código executável sem teste novo/alterado detectável |
| Diff grande | +5 a +15 | escala configurável por linhas e arquivos |
| Histórico de bugs | +5 a +20 | arquivo associado a commits de correção/reversão recentes |
| Histórico de reversões | +10 | arquivo alterado em commits revertidos |
| Churn elevado | +5 a +15 | frequência de alteração acima do baseline local |
| Acoplamento elevado | +5 a +15 | muitos módulos dependentes ou alteração de API pública |
| Finding blocker | +25 | finding já produzido por linter/review |
| Finding critical | +15 | finding crítico existente |
| Finding warning | +3 | warning existente |
| Teste correspondente presente | -10 | evidência de teste novo/alterado relacionado |
| Arquivo novo | 0 | não elevar sozinho; histórico inexistente deve ser explicitado |

Regras:

1. Somar evidências e limitar o resultado a `100.0`.
2. Não transformar ausência de histórico em risco alto automaticamente; usar `SIGNAL_UNAVAILABLE` com confiança baixa.
3. Não adicionar simultaneamente sinais duplicados para a mesma evidência sem justificativa.
4. O score agregado do PR deve ser calculado por combinação explicável, não somente pela média:
   - maior risco entre arquivos: 50%;
   - média ponderada pelos `changed_lines`: 30%;
   - evidências críticas agregadas: 20%.
5. Se houver arquivo crítico com score `>= 80`, o PR não pode ser classificado abaixo de `high`.
6. Se houver finding `blocker` ou arquivo com score `>= 90`, classificar o PR como `critical`.
7. Faixas default:
   - `0–24`: low;
   - `25–49`: medium;
   - `50–79`: high;
   - `80–100`: critical.
8. Toda pontuação deve exibir os fatores que a produziram. Um score sem evidência legível é inválido.

## 5. Detecção dos sinais

### 5.1 Caminhos críticos

Implementar padrões configuráveis, com defaults para:

- autenticação/autorização: `auth`, `login`, `permission`, `policy`, `gate`, `middleware`;
- pagamentos: `payment`, `billing`, `checkout`, `transaction`;
- dados pessoais: `user`, `customer`, `cpf`, `personal`, `privacy`;
- banco: `migration`, `migrations`, `schema`, `database`;
- segurança: `security`, `crypto`, `secret`, `token`, `session`;
- infraestrutura: `.github/workflows`, `.gitlab-ci`, `Dockerfile`, `docker`, `terraform`, `k8s`, `helm`.

A correspondência deve ser case-insensitive e baseada em glob/segmentos de caminho, não em substring indiscriminada que gere falsos positivos em nomes não relacionados.

### 5.2 Ausência de testes

A skill DEVE reutilizar o detector de framework/testes existente, se houver. O algoritmo mínimo é:

1. Identificar arquivos de produção alterados.
2. Identificar arquivos de teste alterados.
3. Procurar correspondência por convenção de nome, diretório, classe/módulo importado ou configuração do framework.
4. Emitir `NO_TEST_CHANGE` apenas quando houver evidência suficiente de que o arquivo é código executável e não existe teste relacionado no diff.
5. Não penalizar arquivos exclusivamente de documentação, configuração não executável, lockfile ou testes.
6. Registrar `signals_available` e warnings quando a correspondência não puder ser determinada.

### 5.3 Histórico de bugs e reversões

Reutilizar `blame_engine.py`/leitura Git existente para obter:

- quantidade de commits de correção associados ao arquivo nos últimos `N` dias;
- quantidade de reversões (`revert`, `rollback`, `hotfix`) que tocaram o arquivo;
- frequência de alterações e autores, sem exibir dados pessoais além do necessário;
- idade da última alteração relevante.

Não inferir que um autor ou equipe é de risco. O sinal pertence ao arquivo/histórico técnico, não à pessoa.

### 5.4 Acoplamento

Implementar somente se já houver parser/índice local confiável. Caso contrário, registrar o sinal como indisponível nesta versão, em vez de usar uma heurística frágil. Possíveis sinais aceitáveis:

- quantidade de arquivos importando o módulo alterado;
- alteração de interface pública/exportada;
- número de módulos afetados no grafo já existente.

## 6. Integração com review e IA

1. `gitpr risk` calcula o score local sem IA.
2. No review padrão, o score pode ser incluído no contexto enviado ao provider, se `review.include_risk_context=true`.
3. A IA deve receber:
   - score e nível;
   - principais evidências;
   - arquivos críticos;
   - indicação de sinais indisponíveis.
4. A IA não deve recalcular nem substituir o score local.
5. O review deve usar o score para priorizar ordem/atenção, mas não alterar a severidade de findings.
6. Quando o score estiver alto, o prompt pode solicitar análise mais detalhada dos arquivos críticos, respeitando limites de tokens e map-reduce existentes.
7. Nenhum conteúdo de código/histórico deve ser enviado para IA adicional apenas para calcular o score.

## 7. Configuração

```yaml
risk:
  enabled: true
  include_in_review: true
  analysis_version: "1.0"
  thresholds:
    low_max: 24
    medium_max: 49
    high_max: 79
  weights:
    critical_path: 25
    security_sensitive: 25
    database_migration: 20
    infrastructure: 20
    no_test_change: 15
    historical_bugs: 20
    historical_reverts: 10
    high_churn: 15
    high_coupling: 15
    finding_blocker: 25
    finding_critical: 15
    finding_warning: 3
    test_present: -10
  critical_paths:
    - "app/Http/Middleware/**"
    - "app/Policies/**"
    - "database/migrations/**"
    - ".github/workflows/**"
  test_patterns:
    - "tests/**"
    - "**/*Test.php"
    - "**/*.test.js"
    - "**/*.spec.ts"
```

Configuração inválida deve gerar erro claro ou fallback seguro documentado. Pesos negativos só devem ser permitidos para sinais explicitamente definidos como mitigadores.

## 8. Saídas

### Texto

Exibir:

- score e nível agregado;
- resumo em uma linha;
- top 3 evidências;
- arquivos críticos;
- indicação de teste ausente;
- warnings de sinais indisponíveis.

### JSON

A saída JSON deve serializar `PullRequestRisk` com `analysis_version`, evidências, scores por arquivo e warnings. O schema deve ser versionado para futura integração com SARIF, `gitpr check` e dashboard.

### Integração TUI

Se houver componente de review/metrics compatível:

- mostrar score agregado no cabeçalho;
- ordenar arquivos por risco decrescente;
- permitir expandir evidências;
- manter a mensagem técnica original dos findings;
- não bloquear a navegação nem ocultar arquivos de baixo risco.

## 9. Testes obrigatórios — critérios de aceite

1. **Teste de cálculo puro:** mesma entrada produz exatamente o mesmo score, nível e evidências em execuções repetidas.
2. **Teste de caminhos críticos:** arquivos de autenticação, migration, pagamento e CI recebem os sinais corretos; arquivos semelhantes fora dos padrões não recebem penalidade indevida.
3. **Teste de ausência de testes:** código executável sem teste correspondente recebe `NO_TEST_CHANGE`; código com teste correspondente recebe mitigação; documentação/lockfile não é penalizado.
4. **Teste de histórico:** fixture Git com arquivo corrigido/revertido várias vezes gera evidências compatíveis com o histórico; arquivo sem histórico suficiente gera warning, não score artificialmente alto.
5. **Teste de agregação do PR:** maior risco, média ponderada e evidência crítica produzem o score agregado esperado.
6. **Teste de saturação:** valores acima de 100 são limitados a 100; valores abaixo de zero são limitados a 0.
7. **Teste de configuração:** pesos e padrões customizados alteram o resultado de forma previsível; configuração inválida é rejeitada com mensagem clara.
8. **Teste de não-regressão:** review sem `include_risk_context` mantém a saída, findings, severidades e chamadas de IA anteriores.
9. **Teste de integração com IA:** quando habilitado, a IA recebe o score e evidências; ela não é chamada para calcular o score.
10. **Teste de privacidade/offline:** cálculo completo não abre rede, não envia código e não grava segredos em logs/telemetria.
11. **Teste de JSON:** saída `--format json` valida contra schema versionado e preserva todos os campos necessários.
12. **Teste de diff remoto:** se `--review-pr` já existir, o scoring aceita a mesma representação normalizada de diff remoto sem chamar Git local indevidamente.

Critério de feature completa: `gitpr risk` funciona em repositório de fixture com score por arquivo e agregado; motivos são legíveis; a execução é determinística e local; review e fluxo existente não regridem quando a integração está desativada.

## 10. Ordem de execução recomendada

1. Inventariar utilitários existentes de diff, blame, testes, histórico e findings; registrar lacunas antes de codificar.
2. Implementar contratos de `risk_types.py` e schema JSON versionado.
3. Implementar regras e cálculo puro com fixtures determinísticas.
4. Implementar leitores de histórico e matcher de testes somente reutilizando utilitários existentes.
5. Implementar `calculate_risk.py` com `gitpr risk --format text|json` em modo somente leitura.
6. Integrar ao review como contexto opcional, sem alterar findings/severidades.
7. Integrar à TUI, se a arquitetura existente permitir sem criar componente paralelo.
8. Adicionar configuração e documentação de pesos/padrões.
9. Validar com repositórios de teste contendo migrations, autenticação, ausência/presença de testes e histórico de reversões.
10. Rodar a suíte completa antes de considerar a feature concluída.

Cada etapa deve ser um commit/PR isolado e revisável. Não implementar enforcement de threshold nesta tarefa; ele pertence à futura especificação de `gitpr check`/CI.

## 11. Riscos e dependências

- **Dependência:** modelo de finding normalizado; sem ele, a integração com findings deve ser adiada ou adaptada ao contrato real.
- **Dependência:** `blame_engine.py` e utilitários Git; não duplicar parsing de histórico.
- **Dependência futura:** Policy Packs devem poder fornecer caminhos críticos, pesos e thresholds; portanto, manter regras configuráveis e separar código de configuração.
- **Dependência futura:** baseline/supressões deve poder marcar evidências aceitas, sem apagar o score bruto; preservar score e evidência separadamente.
- **Risco:** ausência de teste pode ser inferida incorretamente em projetos com convenções não padrão. O sistema deve emitir warning de confiança baixa, não penalização máxima.
- **Risco:** histórico de bugs baseado apenas em palavras de commit gera ruído. Usar sinais combinados e tornar a janela/padrão configurável.
- **Risco:** score numérico pode criar falsa precisão. Exibir sempre nível, evidências, confiança e versão da análise.
- **Risco:** caminhos críticos diferentes por stack. Manter defaults conservadores, configuração por projeto e futura extensão via Policy Packs.

## 12. Fora de escopo

- Dashboard web ou agregação entre repositórios.
- Telemetria remota de scores.
- Machine learning treinado em incidentes reais.
- Ranking de desenvolvedores ou equipes.
- Bloqueio automático de commit/PR/merge.
- Alteração automática de severidade de findings.
- SAST completo, secret scanning ou análise semântica substituindo os bridges existentes.
- Configuração remota/assinada de pesos — será tratada em Policy Packs.

## 13. Encaixe estratégico

Risk scoring permanece no tier Free/Community como capacidade local de priorização e transparência. Ele é uma fundação técnica para `gitpr check`, SARIF, Policy Packs e dashboards Team, mas não deve ser artificialmente limitado no modo local. A camada comercial futura pode vender políticas organizacionais, thresholds compartilhados, tendências agregadas e auditoria — não o cálculo local básico.
