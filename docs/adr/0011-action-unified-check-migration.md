# 0011 — Quebra de contrato na composite action (`action.yml`) com `gitpr check`

- **Status:** Aceito
- **Data:** 2026-11-09
- **Decisores:** Natan Fiuza, Antigravity
- **Contexto:** Transição do pipeline de CI (`action.yml`) de etapas discretas (`--linter` + `--fullreview`) para o comando unificado `gitpr check`. Referência: ADR-013 (`docs/plans/ADR-013-check-ci-command.md`), PR #267 (`d1a06f3`), `docs/check-ci.md` §7.

## Contexto e Decisão

Nas versões legadas do GitPR (`v0.0.12` a `v0.0.36`), a GitHub Action composta oficial (`action.yml`) executava dois comandos em sequência:
1. `gitpr --linter` — interrompia o pipeline imediatamente em caso de erro estático;
2. `gitpr --fullreview` — invocava a revisão completa via IA, gravando no disco do runner o arquivo de texto não estruturado `*_PR_FULLREVIEW.txt`, que workflows costumavam concatenar manualmente no `$GITHUB_STEP_SUMMARY`. Adicionalmente, o input `api-key` era estritamente obrigatório (`required: true`).

A introdução do comando `gitpr check` consolidou linter estático, detecção de segredos, bridges SAST externos (Semgrep, Gitleaks, Bandit), revisão por IA opcional, pontuação de risco e baseline em uma única execução determinística. O `action.yml` foi refatorado para invocar exclusivamente `gitpr check "${ARGS[@]}"`.

Essa mudança introduziu uma **quebra de contrato para workflows existentes**:
1. **Ausência de `*_PR_FULLREVIEW.txt` em disco**: `gitpr check` não cria arquivo de texto plano; pipelines legados que executavam `cat *_PR_FULLREVIEW.txt >> $GITHUB_STEP_SUMMARY` encontram arquivo inexistente.
2. **Emissão de Artefatos Padronizados**: O artefato padrão emitido passa a ser SARIF 2.1.0 (`gitpr-results.sarif`), JSON ou JUnit XML, integrando-se nativamente à aba **Security > Code scanning alerts** do GitHub via `github/codeql-action/upload-sarif@v3`.
3. **Chave de IA Opcional**: O input `api-key` passou a ser opcional (`required: false`), permitindo execuções de CI a custo zero ou offline com `no-ia: "true"`.
4. **Critérios de Falha Determinísticos e Baseline**: O código de saída do pipeline é governado por `--fail-on` (padrão `error`), com supressão de achados legados catalogados via `.gitpr/baseline.json`.

Decidimos manter a quebra de contrato sem criar shims artificiais que gravassem arquivos `.txt` legados em disco, priorizando a aderência a padrões abertos da indústria (SARIF 2.1.0) e fornecendo um guia completo de migração.

## Opções Consideradas

- **Manter gravação legada de `*_PR_FULLREVIEW.txt` em disco pelo `gitpr check`:** Rejeitado. Poluiria o workspace de CI com arquivos de texto duplicados e mascararia o propósito estruturado do SARIF e do Code Scanning nativo do GitHub.
- **Manter a composite action executando `--linter` e `--fullreview` separadamente:** Rejeitado. Duplicaria análises de diff, ignoraria pontuações de risco e baseline, geraria custos redundantes de IA e impediria a geração unificada de SARIF.
- **Substituição direta com guia de migração detalhado:** **Adotado.** O `action.yml` torna-se uma casca limpa sobre `gitpr check`, acompanhado de documentação multilíngue exaustiva de migração "Antes vs Depois".

## Consequências

- Pipelines legados que consumiam `*_PR_FULLREVIEW.txt` precisam ser atualizados para enviar o `gitpr-results.sarif` via `github/codeql-action/upload-sarif@v3` ou ler o relatório JSON gerado com `--format json`.
- O guia detalhado de migração com exemplos de YAML antes e depois está documentado na Seção 7 de `docs/check-ci.md` (e suas 4 traduções: `pt_br`, `pt_pt`, `es_es`, `fr_fr`).
- O conceito ubíquo `Legacy CI action contract` está formalizado no `CONTEXT.md`.
- A paridade das seções e palavras-chave da migração é assegurada de forma contínua pelo teste `tests/unit/test_check_ci_docs_parity.py`.
