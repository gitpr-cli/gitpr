# Glossário — `gitpr risk` (Local Risk Scoring)

> Vocabulário canônico da feature `gitpr risk` (cálculo de risco determinístico e explicável por arquivo e por diff/PR).
> Mantido junto da [spec](20261007_skill_gitpr_risk_scoring_spec.md) e do plano de implementação; a decisão arquitetural vive no [ADR-010](ADR-010-risk-scoring-domain-structure.md).

## Termos de domínio

| Termo | Definição |
|---|---|
| **risk score** | Pontuação numérica determinística normalizada de `0.0` a `100.0` atribuída a um arquivo alterado (`FileRisk`) ou agregada para o conjunto do diff/PR (`PullRequestRisk`). Não representa probabilidade estocástica de incidente, mas intensidade relativa de atenção técnica requerida. |
| **risk level** | Classificação categórica derivada do score numérico: `LOW` (0–24), `MEDIUM` (25–49), `HIGH` (50–79), `CRITICAL` (80–100) e `UNKNOWN` (sinais insuficientes). |
| **risk signal** | Enumeração canônica (`RiskSignal`) de causas detectáveis no código, arquitetura ou histórico (ex.: `CRITICAL_PATH`, `DATABASE_MIGRATION`, `NO_TEST_CHANGE`, `HISTORICAL_REVERTS`, `FINDING_BLOCKER`, `SIGNAL_UNAVAILABLE`). |
| **risk evidence** | Entidade explicável (`RiskEvidence`) que documenta cada contribuição pontuada para o score: `signal`, `points` (positivo ou mitigador negativo), `summary` legível, `details` estruturados e nível de confiança (`high`, `medium`, `low`). |
| **file risk** | Avaliação isolada de um arquivo alterado (`FileRisk`), contendo caminho, pontuação, nível, linhas e hunks alterados, lista de evidências, testes associados detectados e eventuais warnings. |
| **pull request risk** | Avaliação combinada do conjunto do diff (`PullRequestRisk`), composta por pontuação agregada (50% max file score + 30% média ponderada por linhas + 20% evidências críticas), arquivos críticos, total de linhas/arquivos, testes alterados e versão do schema. |
| **test matcher** | Mecanismo de correspondência simétrica que identifica se um arquivo de produção possui teste novo ou alterado correspondente no diff, emitindo `TEST_PRESENT` (-10) ou `NO_TEST_CHANGE` (+15). |
| **risk history reader** | Leitor Git local que extrai histórico recente de commits do arquivo (janela padrão de 90 dias / 50 commits), identificando reversões (`revert`) e correções de bugs (`fix:`). |
| **diff source** | Contrato de dados (`DiffSource`) compartilhado em `src/review/diff_source.py`, que encapsula a origem do diff (`LOCAL` ou `REMOTE_PR`), texto unificado pré-filtrado por smart-excludes e identificadores de escopo de cache. |

## Convenções de pontuação e faixas

- **Mitigações (pontos negativos):** Apenas permitidos para sinais mitigadores explícitos (ex.: `TEST_PRESENT` com -10). O score mínimo é delimitado em `0.0`.
- **Teto (saturação):** Somatórios superiores a 100 são estritamente delimitados em `100.0`.
- **Regra de elevação mandatória:** Se qualquer arquivo tiver score >= 80, o PR não pode ser classificado abaixo de `HIGH`. Se houver `FINDING_BLOCKER` ou arquivo >= 90, o PR é classificado como `CRITICAL`.
- **Mapeamento de Severidades de Findings:**
  - `error` com categoria de segurança/secret ou regra contendo "blocker"/"cve" → `FINDING_BLOCKER` (+25 pts);
  - outros `error` → `FINDING_CRITICAL` (+15 pts);
  - `warning` → `FINDING_WARNING` (+3 pts);
  - `info` → 0 pts (informativo).
- **Filtro `--file <path>`:** Decompõe e exibe exclusivamente o `FileRisk` para o arquivo indicado. Se ausente no diff, reporta amigavelmente com exit code 0.
- **Honestidade epistêmica e tolerância a falhas:** Em shallow clones ou falhas de leitura do histórico Git, emite `SIGNAL_UNAVAILABLE` com confiança `low` e registra aviso não-bloqueante em `warnings`, preservando o cálculo com os sinais remanescentes.
- **Integração com Review de IA:** Quando ativada (`GITPR_RISK_INCLUDE_IN_REVIEW=true`), anexa a seção `## ⚡ Risk Assessment` no arquivo gerado e injeta contexto estruturado no prompt da IA para guiar o foco analítico sem permitir que a IA altere o score numérico determinístico.

