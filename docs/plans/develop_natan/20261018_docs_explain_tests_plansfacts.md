# Plano — Documentar `explain` e `tests` nos 5 idiomas e corrigir blockers de runtime

## Contexto

`explain` e `tests` são os dois últimos recursos do produto sem tópico próprio em `docs/`. As duas features desta janela (`check-ci` e `editor-extension`) nasceram documentadas no padrão canônico em inglês + `.pt_br` / `.pt_pt` / `.es_es` / `.fr_fr`. A documentação de `explain` hoje aponta para `pull-request-publication.md`, que não menciona a feature; `tests` não tem link de documentação em lugar nenhum.

Durante o levantamento, dois defeitos de runtime foram confirmados por reprodução: `call_ai_model` devolve um `dict`, mas `generate_pr_explanation` e `generate_test_file` o tratam como string JSON e abortam com `AttributeError`; `tests generate --finding` acessa atributos que não existem no contrato de `PatchCandidate`. Documentar o caminho feliz sem corrigir isso produziria um guia falso.

## Decisões (grilling)

1. **Nomes:** `docs/explain-pr.md` e `docs/tests-generate.md`.
2. **Superfícies:** `explain-pr.md` cobre o comando standalone, a flag `--explain`, `GITPR_EXPLAIN_BY_DEFAULT`, a skill `.gitpr.explain.md` e uma referência curta ao MCP/extensão. `tests-generate.md` cobre apenas `gitpr tests generate`; o `/tests` do chat fica fora (não compartilha o motor de geração).
3. **Wiring:** corrigir `HELP_MAP["explain"]`, o epilog de `gitpr explain`, adicionar epilogs ao grupo `tests` e ao subcomando `generate`, e corrigir `gitpr -h --explain` (o parâmetro Click chama-se `explain_flag`, mas o `HELP_MAP` procura `explain`).
4. **README:** atualizar os 5 READMEs (link de `explain`, link de `tests` e `--explain`). `docs/ARCHITECTURE.md` não é tocado — a lista já está desatualizada para vários tópicos recentes; dívida registrada no survey.
5. **Formato:** guia técnico completo no padrão dos tópicos recentes, com tabelas de flags, pipeline, exemplos e limitações.
6. **Limitações:** seção explícita, descrevendo apenas o comportamento atual.
7. **Idiomas:** 10 arquivos (2 tópicos × 5 idiomas), tradução integral.
8. **Correções de runtime:** normalizar dict/str nos dois parsers; corrigir `cand.suggested_test` e `cand.diff_unified`; atualizar os mocks dos testes para o contrato dict real e adicionar regressões.
9. **Sem chave de IA:** o fluxo de PR omite a seção e avisa no terminal; o standalone sai com código 1. Reutilizar a chave i18n existente `❌ No API key configured for {provider}. Generate one with --install.`

## Implementação

### 1. Correções de runtime

- `src/domain/pr/explain_section_builder.py`: `parse_explain_payload` aceita `dict` (contrato real) e `str` (compatibilidade e fallback de texto bruto). Valores `None` são normalizados para string vazia.
- `src/application/use_cases/generate_pr_explanation.py`: sem chave, imprime a mensagem localizada em stderr e devolve `PrExplanation` vazio (`markdown=""`); o fluxo de PR omite a seção e o standalone falha com exit 1.
- `src/application/use_cases/generate_test_file.py`: aceita `dict` e `str`; o fallback de texto bruto só roda para string não-JSON.
- `src/main.py`: `cand.suggested_test` e `cand.diff_unified` no contexto de `--finding`.
- Testes: mocks passam a devolver dict; novos testes para dict, ausência de chave, `--finding` e ajuda contextual.

### 2. Wiring

- `HELP_MAP["explain"]["url"]` → `get_doc_url("explain-pr.md")`.
- Epilog de `gitpr explain` → `explain-pr.md`.
- Epilog do grupo `tests` e do subcomando `tests generate` → `tests-generate.md`.
- `--explain` passa a usar o dest `explain`; `HELP_PRIORITY` ganha a entrada.

### 3. Documentação

- `docs/explain-pr.md` (+ `.pt_br`, `.pt_pt`, `.es_es`, `.fr_fr`).
- `docs/tests-generate.md` (+ `.pt_br`, `.pt_pt`, `.es_es`, `.fr_fr`).
- Estrutura: Overview, Command Reference, conteúdo/pipeline, configuração, skill, exemplos, limitações, documentação relacionada.

### 4. READMEs

- Linha de `gitpr explain` aponta para `explain-pr`; linha de `gitpr tests generate` e `--explain` ganham o link completo no idioma correspondente.

## Verificação

- `python -m pytest tests/test_explain_command.py tests/test_tests_command.py tests/domain/pr/test_explain_section_builder.py tests/application/use_cases/test_generate_pr_explanation.py tests/application/use_cases/test_generate_test_file.py -v`
- `python -m pytest tests/test_skill_context.py tests/test_config_schema.py -q`
- Conferência de existência dos 10 arquivos e dos links dos 5 READMEs.
