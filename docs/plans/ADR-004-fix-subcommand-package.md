# ADR-004 — Feature `gitpr fix` em subpacote `src/fix/` (e não módulos flat)

- **Status:** Aceito
- **Data:** 2026-09-13
- **Contexto:** spec [20260913_skill_gitpr_fix_command_spec.md](20260913_skill_gitpr_fix_command_spec.md) §2–§3, grill rodada 1 (Q2)
- **Glossário:** [glossary-gitpr-fix.md](glossary-gitpr-fix.md)

## Contexto

A spec nomeia os arquivos da feature (`patch_extractor.py`,
`patch_safety_classifier.py`, `patch_provenance.py`, `patch_applier.py`,
`fix_history.py`, `apply_fix.py`, `rollback_fix.py`) e propõe uma árvore em
camadas DDD. O [ADR-003](ADR-003-gitpr-release-flat-modules.md) havia decidido,
para o `release`, o oposto: **módulos flat na raiz de `src/`**, e rejeitou
explicitamente o "pacote fatia `src/release/`", porque os dois subpacotes
existentes (`ui/`, `infrastructure/scm/`) existem por motivos estruturais e não
por fatia de feature.

O grill (rodada 1, Q2) fechou o layout antes de qualquer código: pacote
`src/fix/`, com os nomes de arquivo da spec e **sem camadas DDD**. Este ADR
registra por que o `fix` diverge da convenção que o `release` fixou — a decisão
é consciente, não um esquecimento.

## Decisão

Implementar a feature em **`src/fix/`**, um pacote flat por dentro (nenhuma
camada `domain/`/`application/`/`infrastructure/`), com sete módulos:

- `patch_provenance.py` — o contrato de dados (enums e dataclasses), sem I/O.
- `patch_extractor.py` — leitura do código que a IA devolve (blocos cercados +
  validação de diff unificado). **Compartilhado com o chat.**
- `patch_safety_classifier.py` — `SAFE`/`REVIEW_REQUIRED`/`EXPERIMENTAL`, lógica
  pura, sem I/O e sem IA.
- `patch_applier.py` — o primeiro invólucro compartilhado de `git apply` do
  projeto (`--check`, `apply`, `--reverse`, `checkout -b`, `status`).
- `fix_history.py` — o registro de patches aplicados que torna o `--rollback`
  determinístico.
- `apply_fix.py` — o caso de uso: review → IA → validar → classificar →
  dry-run/apply.
- `rollback_fix.py` — o caso de uso que desfaz um patch aplicado.

### Alternativas consideradas

| Alternativa | Veredito |
|---|---|
| Módulos flat na raiz de `src/` (convenção do ADR-003) | Rejeitada — seriam **+7 módulos** numa raiz que já tem 30; e, ao contrário das engines flat (`issue_engine`, `blame_engine`, `linter_engine`), esses módulos não são pontos de entrada independentes: são um grafo fechado com um contrato de dados comum, chamado pela CLI e pela tool MCP. |
| Camadas DDD da spec §2 (`domain/`, `application/use_cases/`, `infrastructure/git/`) | Rejeitada — introduziria uma terceira convenção arquitetural para uma feature; o projeto não é DDD. |
| Pacote `src/fix/` com `__init__.py` reexportando tudo (espelhando `infrastructure/scm/`) | Rejeitada — `src/ui/chat_app.py` importa `src.fix.patch_extractor` em toda sessão de chat; um `__init__` que reexporta arrastaria junto as camadas de IA e de git. O `__init__.py` fica só com o docstring que ordena os módulos. |
| `PatchSummary` dentro do pacote (em `patch_provenance.py`) | Rejeitada — a summary de diff unificado é parsing puro e já existe um parser puro no projeto (`src/diff_parser.py`); duplicar essa responsabilidade dentro do pacote criaria dois lugares que interpretam diff. |

## Justificativa da divergência em relação ao ADR-003

O critério que o ADR-003 usou para admitir um subpacote foi "existe por motivo
estrutural, não por fatia de feature". O `fix` atende a esse critério por um
motivo que o `release` não tinha: **`patch_extractor.py` é consumido fora da
feature**. F5 e `ctrl+s` da TUI de chat (`src/ui/chat_app.py`) passaram a chamar
a camada compartilhada, exatamente como a TUI de PRs e a de issues consomem
`infrastructure/scm/`. O pacote não é uma fatia privada: é um conjunto de
módulos com um consumidor externo e um contrato comum.

Além disso, o que o ADR-003 rejeitou nas camadas DDD — a hierarquia
`domain/application/infrastructure` — **não existe aqui**: o pacote é flat por
dentro, com dependências numa única direção declarada no docstring do
`__init__.py`.

## Desvios aprovados (vs. o plano)

1. **`PatchSummary` mora em `src/diff_parser.py`**, não no pacote. O plano pedia
   o acréscimo de `summarize_patch()` ao parser (reuso); o dataclass de retorno
   foi junto, para não partir o contrato em dois arquivos.
2. **`resolve_last_review()` foi antecipado** para a etapa do `apply_fix`, em
   `src/cache.py` — o plano o listava como etapa 8, depois dos casos de uso; sem
   ele não há como testar o pipeline ponta a ponta.
3. **`KIND_WORDS` → `KIND_STR`** no campo dos caminhos sensíveis em
   `config_schema.py`: a lista é separada por `;` e não por espaços, então o
   tipo de campo do schema é o de string, e não o de lista de palavras.
4. **Recurso MCP `skill://fix`** acrescentado ao plano: `mcp_server.SKILL_FILES`
   é um registro **separado** de `config.SKILL_FILES_BY_TYPE`, mantido em
   sincronia por `TestSkillRegistryAgreement`; registrar o tipo `fix` sem a
   entrada correspondente deixaria o teste vermelho, e registrar só a entrada
   anunciaria uma URI morta em `list_skills()`.
5. **`.gitpr.fix.md` entrou em `generate_skill_template()`** (`src/core.py`): o
   plano citava só `SKILL_FILES_BY_TYPE["fix"]`, mas é `files_to_download` que
   faz o `gitpr --skill` baixar de fato o template.
6. **Chaves i18n adicionadas à mão por script.** `tests/sync_i18n.py` casa
   literais com regex e é cego à concatenação implícita — rodá-lo **removeria 23
   chaves existentes**. As 67 chaves novas desta feature foram inseridas
   preservando a ordem dos seis arquivos de idioma.
7. **`CHANGELOG.md` não foi tocado.** A seção `## [1.1.0] - 2026-09-13` já está
   publicada (tag `v1.1.0`) e o `gitpr release` gera seções de versão a partir do
   git log — não existe convenção de seção "Unreleased". Uma entrada escrita à
   mão ou falsificaria uma seção já lançada, ou deixaria um bloco obsoleto
   duplicado quando o `release` rodar.
8. **`smart-excludes` implementado com o marcador existente.** O plano dizia
   "bump do `SMART_EXCLUDES_VERSION` no `updater.py`"; esse marcador é uma env
   var, e o único marcador de código é `__lang_version__` — o mesmo que comanda o
   OTA de traduções, thinking words, docs-excludes e presets. A entrada
   `.gitpr/fix_history.json` no `templates/gitpr.smart-excludes.json` viaja no
   bump de `v0.0.25` → `v0.0.26`, que esta feature já exigia por ter 67 chaves
   i18n novas (mesma prática do commit `bf9f1b9`).

## Consequências

**Positivas:**
- O contrato de dados tem um lugar só (`patch_provenance.py`), e os módulos
  puros (extractor, classifier) testam-se sem git, sem rede e sem IA.
- O extrator é compartilhado com o chat, então a regex de blocos cercados existe
  uma vez — a duplicação que havia entre F5 e `ctrl+s` deixou de ser possível.
- Quem lê a spec §2 antes do ADR vai estranhar a árvore; este registro e o
  docstring do `__init__.py` explicam a divergência.

**Negativas / custos:**
- Conviverão duas convenções para features grandes: flat (`release`) e
  subpacote (`fix`). A regra que sobra é o critério do ADR-003 — subpacote
  quando há consumidor externo —, e não "feature grande vira pacote".
- `src/fix/` é o terceiro subpacote de `src/`; o `pyproject.toml` depende de
  descoberta automática de pacotes (`__init__.py` presente), como nos outros.
