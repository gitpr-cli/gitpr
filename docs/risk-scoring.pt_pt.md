# Documentação Técnica: Pontuação de Risco Local (gitpr risk)

O `gitpr risk` calcula uma pontuação de risco local, determinística e explicável para cada ficheiro modificado e para o pull request / diff globalmente. Utiliza sinais do repositório e do Git — caminhos críticos, ausência de testes, migrações de base de dados, histórico de bugs e reversões, dimensão do diff e findings estáticos — para priorizar a atenção humana na revisão de código e orientar o foco da IA, sem depender de rede, sem consumir quotas de IA e sem bloquear o fluxo de trabalho.

---

## 1. Visão Geral

A Pontuação de Risco Local atua em três interfaces complementares:

1. **Linha de Comandos Autónoma (`gitpr risk`)**: Avalia o diff da árvore de trabalho ou da branch contra uma referência base e apresenta um detalhe colorido dos níveis de risco, pontuações e fatores contribuintes.
2. **Inspeção por Ficheiro Específico (`gitpr risk --file <path>`)**: Isola o cálculo de risco para um único ficheiro indicado, detalhando os seus sinais pontuados e a correlação de testes.
3. **Contexto Aditivo na Revisão de Código (`gitpr -r` / `gitpr -f` / `gitpr --review-pr`)**: Quando ativado (`GITPR_RISK_INCLUDE_IN_REVIEW=true`), anexa automaticamente a secção `## ⚡ Risk Assessment` ao relatório gerado e introduz um resumo estruturado no prompt da IA para direcionar a análise a ficheiros críticos.

### 1.1 Referência de Comandos

```bash
gitpr risk                        # Calcula o risco do diff local não comitado (ou da branch)
gitpr risk --file src/auth.py     # Decompõe fatores de risco de um ficheiro específico
gitpr risk --format json          # Retorna JSON estruturado para CI/CD e automações
gitpr risk --base main            # Avalia o risco contra uma referência base explícita
gitpr risk --no-history           # Desativa a leitura do histórico Git para execução ultrarrápida
```

| Opção | Descrição |
|---|---|
| **`--file <path>`** | Calcula os fatores de risco detalhados para um ficheiro específico |
| **`--format {text\|json}`** | Seleciona saída legível no terminal (predefinição) ou JSON estruturado |
| **`--base <ref>`** | Calcula o diff contra uma branch ou commit base explícito |
| **`--no-history`** | Ignora a extração do histórico de commits para otimizar o tempo de execução |

---

## 2. Modelo de Pontuação e Fórmula de Agregação

Todas as pontuações são rigorosamente normalizadas no intervalo **`0.0 – 100.0`**.

### 2.1 Níveis de Risco e Limiares (Thresholds)

| Nível | Intervalo de Pontos | Badge | Significado |
|---|---|---|---|
| **LOW** | 0.0 – 24.0 | `LOW 🟢` | Alterações rotineiras com baixa probabilidade de regressão |
| **MEDIUM** | 25.0 – 49.0 | `MEDIUM 🟡` | Modificações moderadas exigindo vigilância normal de revisão |
| **HIGH** | 50.0 – 79.0 | `HIGH 🟠` | Mudanças significativas em áreas críticas ou sem testes |
| **CRITICAL** | 80.0 – 100.0 | `CRITICAL 🔴` | Elevada exposição a incidentes, blockers ou impacto estrutural grave |

### 2.2 Tabela de Pesos e Sinais

| Sinal | Pontos Padrão | Condição / Padrão |
|---|---:|---|
| **`CRITICAL_PATH`** | +25 | Autenticação, autorização, permissões, pagamentos, políticas, faturação |
| **`SECURITY_SENSITIVE`** | +25 | Configurações de segurança, criptografia, sessões, gestão de tokens |
| **`DATABASE_MIGRATION`** | +20 | Alterações de esquema, migrations de base de dados, SQL estrutural |
| **`INFRASTRUCTURE`** | +20 | Pipelines de CI/CD, Dockerfiles, Terraform, configurações Kubernetes |
| **`NO_TEST_CHANGE`** | +15 | Código executável de produção alterado sem testes correspondentes no diff |
| **`LARGE_DIFF`** | +5 a +15 | Volume do diff: >= 50 linhas (+5), >= 100 linhas (+10), >= 300 linhas (+15) |
| **`HISTORICAL_BUGS`** | +10 a +20 | Ficheiro associado a commits de correção de bugs no histórico recente (90 dias / 50 commits) |
| **`HISTORICAL_REVERTS`** | +10 | Ficheiro alterado por commits de reversão (`revert` ou `rollback`) |
| **`HIGH_CHURN`** | +15 | Frequência de alteração elevada (>= 20 commits na janela recente) |
| **`FINDING_BLOCKER`** | +25 | Finding bloqueador detetado por linter ou verificador de segredos |
| **`FINDING_CRITICAL`** | +15 | Finding de erro crítico reportado pelo linter estático |
| **`FINDING_WARNING`** | +3 | Aviso não bloqueante reportado pelo linter estático |
| **`TEST_PRESENT`** | -10 | Sinal mitigador: teste correspondente adicionado ou alterado juntamente com o código |
| **`NEW_FILE`** | 0 | Informativo: ficheiro recém-criado sem histórico prévio de commits |

### 2.3 Fórmula de Agregação (50 / 30 / 20)

A pontuação agregada do pull request/diff combina as pontuações individuais:
- **50%**: Maior pontuação entre os ficheiros individuais (`max_file_score`)
- **30%**: Média ponderada pela quantidade de linhas alteradas (`weighted_avg_lines`)
- **20%**: Pontuação agregada de evidências críticas (`critical_evidence_score`)

### 2.4 Regras Obrigatórias de Elevação

1. **Piso High**: Se qualquer ficheiro individual pontuar **>= 80.0**, o nível agregado do PR não pode ser inferior a `HIGH`.
2. **Piso Critical**: Se existir qualquer finding bloqueador (`FINDING_BLOCKER`) ou ficheiro com pontuação **>= 90.0**, o nível do PR é automaticamente classificado como `CRITICAL`.
3. **Saturação e Delimitação**: As pontuações são limitadas estritamente entre `0.0` e `100.0`. Pontos negativos são permitidos apenas para mitigações explícitas (`TEST_PRESENT`).

---

## 3. Configuração e Personalização

### 3.1 Configuração Global (`~/.gitpr/.env` ou `gitpr config`)

| Chave | Tipo | Predefinição | Descrição |
|---|---|---|---|
| `GITPR_RISK_INCLUDE_IN_REVIEW` | booleano | `true` | Anexa automaticamente a secção de Avaliação de Risco às revisões de código (`-r`, `-f`, `--review-pr`). |

### 3.2 Regras Personalizadas via YAML (`.gitpr/skill/gitpr.risk.yml`)

Pode configurar caminhos, pesos e limiares específicos do projeto no ficheiro `.gitpr/skill/gitpr.risk.yml` ou `.gitpr.risk.yml`:

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
    test_present: -10
  critical_paths:
    - "app/Http/Middleware/**"
    - "app/Policies/**"
    - "database/migrations/**"
    - ".github/workflows/**"
```

---

## 4. Garantias de Desempenho e Privacidade

- **100% Offline e Determinístico**: Executa totalmente sobre os diffs locais e metadados do Git. Não realiza chamadas de rede nem envia código para servidores externos.
- **Execução em Milissegundos**: Concluído quase instantaneamente, ideal para git hooks locais e esteiras de CI/CD.
- **Honestidade Epistémica**: Caso o histórico Git esteja inacessível (ex.: shallow clone em CI), o sinal é marcado como `SIGNAL_UNAVAILABLE` com aviso não bloqueante, em vez de gerar pontuações artificiais.

