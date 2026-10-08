## Completion Report — GitPR Local Risk Scoring (`gitpr risk`)

### What was done
- Alinhamento de design via rodadas de entrevista estruturadas (**Grilling + Domain Modeling**), consolidando decisões de arquitetura e vocabulário sem premissas tácitas.
- Criação do glossário de domínio canônico em `docs/plans/glossary-gitpr-risk-scoring.md` e do documento de decisão arquitetural `docs/plans/ADR-010-risk-scoring-domain-structure.md`.
- Implementação dos contratos de domínio em `src/domain/risk/risk_types.py` (`RiskLevel`, `RiskSignal`, `RiskEvidence`, `FileRisk`, `PullRequestRisk`).
- Implementação de regras e configuração em `src/domain/risk/risk_rules.py` com carregamento opcional de `.gitpr.risk.yml` e fallback determinístico.
- Implementação do motor de cálculo puro em `src/domain/risk/risk_calculator.py` com a fórmula ponderada 50/30/20, clamping `[0.0, 100.0]` e regras mandatórias de elevação de severidade.
- Implementação de explicabilidade e formatadores em `src/domain/risk/risk_explanation.py` para terminal, saída de review e contexto da IA.
- Implementação da camada de infraestrutura Git:
  - `src/infrastructure/git/risk_history_reader.py`: extração resiliente de histórico local (`git log`) para contagem de bugs e reversões, com degradação graciosa para `SIGNAL_UNAVAILABLE`.
  - `src/infrastructure/git/test_matcher.py`: correspondência simétrica entre arquivos de código executável e testes correspondentes.
- Implementação do caso de uso orquestrador em `src/application/use_cases/calculate_risk.py`, consumindo `DiffSource` de forma unificada.
- Criação do comando CLI `gitpr risk` em `src/main.py` com suporte a `--file`, `--format {text|json}`, `--base` e `--no-history`.
- Integração aditiva ao fluxo de review padrão (`gitpr -r`, `gitpr -f` e `--review-pr`) em `src/review/render.py`, `src/core.py` e `src/main.py`.
- Adição da configuração `GITPR_RISK_INCLUDE_IN_REVIEW` em `src/config.py` e do template padrão em `templates/gitpr.risk.yml`.
- Criação de suíte completa de testes unitários e de integração (28 testes no total), cobrindo cálculo puro, regras, leitores de histórico, matcher de testes, use case e CLI.

### Changed files
| File | Change type | Description |
|------|-------------|-------------|
| `docs/plans/glossary-gitpr-risk-scoring.md` | feat | Glossário canônico de termos de domínio de risk scoring |
| `docs/plans/ADR-010-risk-scoring-domain-structure.md` | feat | Registro de decisão arquitetural do risk scoring |
| `src/domain/risk/risk_types.py` | feat | Contratos de dados e enums de risco |
| `src/domain/risk/risk_rules.py` | feat | Regras determinísticas, pesos e leitura de `.gitpr.risk.yml` |
| `src/domain/risk/risk_calculator.py` | feat | Cálculo puro de score por arquivo e agregação 50/30/20 do PR |
| `src/domain/risk/risk_explanation.py` | feat | Explicabilidade legível, badges e seções de Markdown |
| `src/domain/risk/__init__.py` | feat | Exportações do pacote de domínio de risco |
| `src/infrastructure/git/risk_history_reader.py` | feat | Leitor Git seguro para reversões e histórico de bugs |
| `src/infrastructure/git/test_matcher.py` | feat | Correlacionador simétrico de arquivos de teste no diff |
| `src/application/use_cases/calculate_risk.py` | feat | Caso de uso orquestrador de cálculo de risco |
| `src/review/render.py` | feat | Suporte opcional à seção de avaliação de risco no review gerado |
| `src/config.py` | feat | Adição de `GITPR_RISK_INCLUDE_IN_REVIEW` e helper de verificação |
| `src/core.py` | feat | Injeção de contexto de risco estruturado nas instruções do modelo de IA |
| `src/main.py` | feat | Registro do comando `gitpr risk`, integração de review e help map |
| `templates/gitpr.risk.yml` | feat | Template de configuração padrão de caminhos e pesos de risco |
| `tests/domain/risk/test_risk_calculator.py` | test | Testes unitários de cálculo puro, limites e agregação |
| `tests/domain/risk/test_risk_rules.py` | test | Testes unitários de padrões críticos e carregamento de YAML |
| `tests/infrastructure/git/test_test_matcher.py` | test | Testes de correspondência de testes unitários |
| `tests/infrastructure/git/test_risk_history_reader.py` | test | Testes com mocks para leitura de histórico Git |
| `tests/application/use_cases/test_calculate_risk.py` | test | Testes do caso de uso orquestrador com diffs e findings |
| `tests/test_risk_cli.py` | test | Testes de ponta a ponta do comando CLI `gitpr risk` |

### Impact
- **Functionality:** O comando `gitpr risk` calcula agora pontuações explicáveis e determinísticas locais sem chamada a modelos de IA. No review padrão, a seção de risco é anexada de forma aditiva.
- **Performance:** Avaliação estritamente local, concluída em poucos milissegundos sem chamadas de rede ou consumo de cotas de IA.
- **Compatibility:** Totalmente compatível com as saídas e flags pré-existentes. O cálculo de risco é informativo e não bloqueia fluxos nem altera a severidade dos findings do linter.

### Next steps (if applicable)
- Planejamento futuro de verificação e bloqueio por threshold via `gitpr check` para pipelines de CI/CD.

