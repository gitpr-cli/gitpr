# ADR-010 — Arquitetura de Domínio e Ingestão do `gitpr risk` (Local Risk Scoring)

- **Status:** Aceito
- **Data:** 2026-10-07
- **Contexto:** spec [20261007_skill_gitpr_risk_scoring_spec.md](20261007_skill_gitpr_risk_scoring_spec.md), grill rodada 1
- **Glossário:** [glossary-gitpr-risk-scoring.md](glossary-gitpr-risk-scoring.md)

## Contexto

A especificação técnica de Risk Scoring visa calcular uma pontuação determinística e explicável de risco técnico por arquivo alterado e agregado para o pull request/diff. 

Três aspectos fundamentais de arquitetura foram decididos para integrar harmoniosamente a funcionalidade à base existente do GitPR:
1. **Ingestão de Diff:** O projeto já possui o contrato `DiffSource` (ADR-005) em `src/review/diff_source.py`, que encapsula a proveniência (local vs remote PR) e garante aplicação prévia de `smart-excludes`.
2. **Origem dos Findings:** O risco agrega penalidades por findings de severidade alta/blocker. O motor do GitPR possui linters estáticos regex locais e bridges SAST (`NormalizedFinding`), enquanto IA produz findings apenas sob demanda.
3. **Localização e Configuração de Regras:** O GitPR adota arquivos YAML locais/skill em `.gitpr/skill/` para regras dinâmicas (ex.: `.gitpr.linter.yml`), complementando as variáveis globais de `~/.gitpr/.env`.

## Decisão

1. **Adesão à Clean Architecture sob `src/domain/risk/` e `src/application/use_cases/`:**
   - Modelos puros e contratos: `src/domain/risk/risk_types.py`
   - Regras de pontuação, pesos e thresholds padrão: `src/domain/risk/risk_rules.py`
   - Mecanismo puro de cálculo e agregação: `src/domain/risk/risk_calculator.py`
   - Formatador e explicador de evidências: `src/domain/risk/risk_explanation.py`
   - Leitores de infraestrutura Git e testes: `src/infrastructure/git/risk_history_reader.py` e `src/infrastructure/git/test_matcher.py`
   - Caso de uso orquestrador: `src/application/use_cases/calculate_risk.py`

2. **Consumo Direto de `DiffSource`:**
   - O caso de uso `calculate_risk` consome exclusivamente `DiffSource`.
   - No comando CLI `gitpr risk`, o comando constrói `DiffSource(origin=DiffOrigin.LOCAL, content=get_git_full_diff(...), identifier="head")`.
   - Quando integrado a fluxos de review (`-r`, `--review-pr`), o `DiffSource` já computado é repassado sem redundância de comandos Git.

3. **Execução Estática Local para Findings:**
   - Em execuções isoladas (`gitpr risk`), findings são extraídos via linters estáticos locais (`parse_diff_and_lint`) e bridges SAST já disponíveis sem consultar rede ou consumir tokens de IA. Se desabilitados ou vazios, o sinal degrada graciosamente para `SIGNAL_UNAVAILABLE`.

4. **Detecção Simétrica de Testes (`test_matcher`):**
   - Combina detecção de frameworks (`framework_detector.py`) com mapeamento de convenções estruturadas de diretório/arquivo (`tests/**`, `test_*`, `*Test.*`).
   - Evita penalizar arquivos puramente de documentação, lockfiles ou arquivos de configuração não executáveis.

5. **Histórico Git com Janela Delimitada:**
   - Leitura Git local com janela padrão de 90 dias e limite de 50 commits por arquivo, identificando `revert` e Conventional Commits `fix:` sem penalizar arquivos recém-criados (`NEW_FILE`).

6. **Configuração via Template YAML e Defaults:**
   - Carregamento opcional a partir de `.gitpr.risk.yml` ou `.gitpr/skill/gitpr.risk.yml`, com fallbacks seguros para constantes em código.

7. **Classificação e Mapeamento de Severidades de Findings:**
   - Severidades de findings são mapeadas deterministicamente: `error` em segurança/secrets/cve vira `FINDING_BLOCKER` (+25); demais `error` viram `FINDING_CRITICAL` (+15); `warning` vira `FINDING_WARNING` (+3); `info` é neutro (0).

8. **Comportamento Cirúrgico do `--file <path>`:**
   - Ao inspecionar arquivo específico, avalia-o no contexto do diff e foca a exibição humana/JSON no `FileRisk` específico, reportando sem erro caso o arquivo não tenha sido alterado no diff.

9. **Enriquecimento Aditivo do Code Review de IA:**
   - Integração opcional (`GITPR_RISK_INCLUDE_IN_REVIEW=true`) anexando a seção `## ⚡ Risk Assessment` no arquivo de review e fornecendo sumário determinístico no prompt para priorizar atenção da IA, sem que a IA recalcule ou altere o score local.

## Consequências

- **Positivas:**
  - 100% determinístico, offline e sem custo de tokens de IA para cálculo do score.
  - Testes unitários de domínio totalmente desacoplados de subprocessos Git e de rede.
  - Reutilização dos contratos canônicos (`DiffSource`, `PatchSection`, `NormalizedFinding`).
  - Sem duplicação de parsing ou subprocessos redundantes no fluxo de review.
- **Limitações:**
  - Em ambientes sem histórico local completo (como shallow clones em CI), sinais históricos degradam para `SIGNAL_UNAVAILABLE` com confiança reduzida.

