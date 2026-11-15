# Relatório de Auditoria e Roteiro de Execução — Pendências de `🚧 Próximos Passos` e `🌐 Internacionalização e Documentação`

- **Data da auditoria:** 2026-11-15
- **Branch de referência:** `develop_natan`
- **Escopo analisado:** Todos os 25 relatórios de estado em `docs/reports/` (`relatorio_estado_ GitPR-CLI.md` até `relatorio_estado_v0.0.25.md`), confrontados com o código-fonte, arquivos de idioma (`langs/`, `docs/`, `extensions/vscode/`), ADRs e suíte de testes vigentes.
- **Idioma deste prompt/roteiro:** Português (`pt-BR`) — as alterações de código, docstrings e comentários produzidas pelo agente executor devem ser estritamente em inglês, conforme `GEMINI.md` / `CLAUDE.md`.

---

## Regras Globais para o Agente Executor

1. **Idioma e codificação:** Todo código, comentário, docstring e identificador novo ou modificado deve estar em **inglês**. Toda leitura/escrita de arquivo texto e chamada `subprocess.run()` em Python deve usar `encoding="utf-8"` e `errors="replace"` (nunca `errors="strict"` ou `errors="ignore"`).
2. **Controle de versão:** **Nunca** execute `git add`, `git commit`, `git push` ou `--no-verify`. Deixe todas as alterações na working tree para revisão humana.
3. **Sem código especulativo:** Não gere código de exemplo nem adicione funcionalidades fora do escopo de cada etapa. Antes de editar qualquer arquivo, leia o trecho exato no repositório.
4. **Contrato estrutural de documentação (`docs/`):** `tests/unit/test_docs_translation_parity.py` compara todos os 5 idiomas (`.md`, `.pt_br.md`, `.pt_pt.md`, `.es_es.md`, `.fr_fr.md`) contando headings `^(#{1,6})\s`, linhas começando com `|`, bullets `^\s*[-*]\s` e cercas ` ``` `. Exceto arquivos explicitamente listados em `_PARITY_EXCEPTIONS`, todas as traduções devem ter assinatura estrutural idêntica à do arquivo em inglês.
5. **Contrato de i18n CLI (`langs/`):** `tests/test_i18n.py` extrai via AST todas as chamadas `__()` em `src/` e exige: zero chaves faltantes (`missing == 0`), zero chaves órfãs em `langs/*.json`, paridade exata entre os 6 arquivos (`pt_br.json`, `pt_pt.json`, `es.json`, `es_es.json`, `fr.json`, `fr_fr.json`) e nenhuma chave de interface de usuário deixada igual ao inglês. Qualquer mudança de string dentro de `__()` deve atualizar os 6 JSONs no mesmo passo.
6. **Cache e testes:** Execute o comando de verificação indicado ao final de cada etapa antes de avançar para a próxima. Ao concluir todas as etapas aplicáveis, rode a suíte completa e produza o relatório obrigatório em `docs/gemini/reports/{branch}/`.

---

## 1. Matriz Consolidada da Auditoria (`docs/reports/` vs. Estado Atual)

### 1.1 Itens de `🚧 Próximos Passos` / `🌐 i18n` já concluídos

| Origem (Relatórios) | Item Reportado | Evidência no Código Atual (`develop_natan`) | Status |
| --- | --- | --- | --- |
| `v0.0.2` – `v0.0.24` | Comandos centrais (`-c`, `-r`, `-f`, `-i`, `-l`, `-b`, `-ch`, `-is`, `-ht`, `config`, `check`, `metrics`, `review-pr`, `release`, `fix`, `split`, `risk`, `policy`, `baseline`, `demo`, `badge`, `seed`) | Implementados em `src/` com suítes de teste dedicadas em `tests/` | Concluído |
| `v0.0.10` – `v0.0.25` | Provedores Multi-IA (`gemini`, `deepseek`, `ollama`), cache MD5 e partição Map-Reduce por provedor | `src/ai_providers.py`, `src/cache.py`, `src/config.py`, `docs/adr/0022-map-reduce-per-provider-token-partitioning.md` | Concluído |
| `v0.0.12` – `v0.0.25` | Remoção de `FileStageScreen` de `src/ui/pr_publish_app.py` e limpeza de chaves órfãs no `langs/` | Commit `4570646` listado em `CHANGELOG.md`; `FileStageScreen` ausente em `src/ui/pr_publish_app.py`; `tests/test_i18n.py` exige zero chaves órfãs | Concluído |
| `v0.0.23` – `v0.0.25` | Documentação de `gitpr --mcp` em `docs/mcp-integration.md` | Seções de uso `gitpr --mcp` presentes em `docs/mcp-integration.md` | Concluído |
| `v0.0.24` – `v0.0.25` | Summary da versão `[1.8.0]` no `CHANGELOG.md` | Linha 6 de `CHANGELOG.md` já inicia com `"Version 1.8.0 improves usability, documentation, and setup workflows..."` | Concluído |
| `v0.0.24` – `v0.0.25` | Correção do detector de forge (`detect_provider_from_remote`) e aviso de fallback para hosts self-hosted não reconhecidos | `src/infrastructure/scm/factory.py`, `src/scm_settings.py`, `docs/scm-multiforge.*` (§1.2) e `tests/scm/test_factory.py` / `test_scm_settings.py` | Concluído |
| `v0.0.17` – `v0.0.25` | Cobertura dos 6 dicionários JSON do CLI (`langs/*.json`, `__lang_version__ = "v0.0.43"`) e 51 guias com 5 idiomas em `docs/` | Auditoria de `docs/` contabiliza 52 base stems: 51 completos nos 5 idiomas + 1 exceção (`github-issue-prompt-com-gh.md`) | Concluído (exceto P3) |

### 1.2 Itens Pendentes (Não Executados ou Incompletos no Repositório)

| ID | Origem / Referência | Pendência Verificada no Repositório | Destino |
| --- | --- | --- | --- |
| **P1** | SSOT de versão (`v0.0.24`/`v0.0.25`, `tests/unit/test_version_consistency.py`) | `CLAUDE.md` (linha 8) e `GEMINI.md` (linha 8) ainda exibem `1.7.0`, divergindo de `src/updater.py` (`__version__ = "1.8.0"`) | Etapa 1 (Concluída) |
| **P2** | Auditoria ADR-0019 / dívida de paridade (`tests/unit/test_docs_translation_parity.py`) | Traduções `.pt_br`, `.pt_pt`, `.es_es`, `.fr_fr` de `docs/config-tui.*` e `docs/pull-request-publication.*` estão defasadas em relação ao inglês (ausência de `GITPR_SKIP_PROJECT_CONFIG_SEED`, §4, §9.1 `[!IMPORTANT]`, §9.4, §14 e §15 Ex. 9–10); `"pull-request-publication"` segue em `_PARITY_EXCEPTIONS`; `tests/unit/test_project_config_seed_docs.py` não existe | Etapa 2 |
| **P3** | Auditoria i18n/docs (`v0.0.25`, `tests/unit/test_docs_translation_parity.py`, `README*.md`) | `docs/github-issue-prompt-com-gh.md` permanece na raiz de `docs/` listado em `_EN_ONLY`, impedindo 100% (51/51) de cobertura multilíngue na raiz de `docs/`; os 5 `README*.md` não linkam 6 guias (`gitpr-issue-option`, `guia-regex-gitpr`, `marketplace-publishing-guide`, `otimizacao-de-tokens`, `untracked-files`, `version-markers`), e os 4 READMEs traduzidos também omitem `mentor-mode` | Etapa 3 |
| **P4** | Observabilidade de Map-Reduce (ADR-0022, `src/config.py`, `src/metrics.py`) | `docs/metricas-telemetria.*` (5 idiomas) ainda não documenta o impacto de custo e latência do Map-Reduce (`GITPR_MAP_REDUCE_MAX_TOKENS`, `GITPR_MAP_REDUCE_MAX_PART_TOKENS`, variantes por provedor e colunas `map_reduce`/`chunks_count`/`duration_ms`), e `docs/adr/0022-map-reduce-per-provider-token-partitioning.md` não referencia métricas | Etapa 4 |
| **P5** | Migração SCM em ambientes efêmeros (ADR-0020, `src/scm_settings.py`) | `docs/scm-multiforge.*` (5 idiomas) e `docs/adr/0020-per-repo-scm-provisioning-migration.md` ainda não explicitam o comportamento de `migrate_legacy_scm_config()` quando `.env` é read-only ou gera `OSError`/`PermissionError` (`persisted=False` com fallback ativo em `os.environ`) | Etapa 5 |
| **P6** | Self-hosted / GitHub Enterprise (`docs/scm-multiforge.md` §1.2 e §3, `src/infrastructure/scm/github_provider.py`) | `GitHubProvider.parse_repo_ref` aceita apenas o literal `github.com`, fazendo remotes GitHub Enterprise (`github.acme.com`) falharem mesmo com `GITHUB_BASE_URL`; `docs/scm-multiforge.*` ainda documenta essa limitação | Etapa 6 |
| **P7** | Consistência CLI/i18n em `src/mcp_server.py` | `_install_for_editor` (`src/mcp_server.py`, linha ~2901) omite `claude-code` da mensagem de erro de editor inválido, apesar de `--install` (`choices` na linha ~3058) aceitar `claude-code` | Etapa 7 |
| **P8** | Cobertura `pt_pt` da extensão VS Code (`v0.0.25`, `extensions/vscode/`) | Existem bundles `en`, `pt-br`, `es` e `fr`, porém faltam `extensions/vscode/package.nls.pt-pt.json` e `extensions/vscode/l10n/bundle.l10n.pt-pt.json` | Etapa 8 |
| **M1** | Operação de release Git / PyPI (`v0.0.25`) | Recriação/ajuste da tag `v1.7.0` (se necessário) e publicação de release/tag da `1.8.0` no repositório remoto | Seção 3 |
| **M2** | Publicação da extensão nos marketplaces (`v0.0.25`) | Execução de `scripts/marketplace-setup-wizard.sh` / workflow `ext-v*` com PATs reais do VS Marketplace e Open VSX | Seção 3 |
| **M3** | Roadmap futuro de provedores de IA (`v0.0.25`) | Suporte direto à API OpenAI e a novos backends locais compatíveis além de Ollama | Seção 3 |

---

## 2. Etapas Executáveis pelo Agente de Código

### Etapa 1 — Alinhar versão SSOT em `CLAUDE.md` e `GEMINI.md` ✅ Concluída

- **Objetivo:** Eliminar o drift de versão entre `src/updater.py` (`__version__ = "1.8.0"`) e os arquivos de instruções de projeto `CLAUDE.md` e `GEMINI.md`.
- **Origem no Relatório:** Auditoria de consistência SSOT (`v0.0.24` / `v0.0.25`) e `tests/unit/test_version_consistency.py`.
- **Arquivos-Alvo:**
  - `CLAUDE.md`
  - `GEMINI.md`
- **Instruções Passo a Passo:**
  1. Ler `src/updater.py` (linhas 1–20) e confirmar o valor corrente de `__version__` (`1.8.0`).
  2. Ler os cabeçalhos de `CLAUDE.md` (linha 8) e `GEMINI.md` (linha 8).
  3. Atualizar a linha `- **Current version:** 1.7.0 (Canonical SSOT in \`src/updater.py\`)` em `CLAUDE.md` e `GEMINI.md` para refletir exatamente `1.8.0` sem alterar formatação ou comentários adjacentes.
  4. Inspecionar `tests/unit/test_version_consistency.py` para confirmar todos os alvos verificados pelo teste de consistência.
- **Critérios de Aceite:**
  - `CLAUDE.md` e `GEMINI.md` declaram `Current version: 1.8.0` idêntica a `src/updater.py`.
  - Nenhum teste de consistência de versão falha ou é pulado.
- **Comando de Verificação:**
  - `python -m pytest tests/unit/test_version_consistency.py -v`

---

### Etapa 2 — Sincronizar traduções de `docs/config-tui.*` e `docs/pull-request-publication.*` e criar testes de paridade ADR-0019

- **Objetivo:** Levar `GITPR_SKIP_PROJECT_CONFIG_SEED` e as seções expandidas de `docs/config-tui.md` e `docs/pull-request-publication.md` às quatro traduções, zerar a dívida `"pull-request-publication"` em `_PARITY_EXCEPTIONS` e cobrir o contrato ADR-0019 com teste unitário dedicado.
- **Origem no Relatório:** Auditoria pós-ADR-0019 (`GITPR_SKIP_PROJECT_CONFIG_SEED`) e dívida registrada em `tests/unit/test_docs_translation_parity.py`.
- **Arquivos-Alvo:**
  - `docs/config-tui.md` (referência canônica)
  - `docs/config-tui.pt_br.md`, `docs/config-tui.pt_pt.md`, `docs/config-tui.es_es.md`, `docs/config-tui.fr_fr.md`
  - `docs/pull-request-publication.md` (referência canônica)
  - `docs/pull-request-publication.pt_br.md`, `docs/pull-request-publication.pt_pt.md`, `docs/pull-request-publication.es_es.md`, `docs/pull-request-publication.fr_fr.md`
  - `docs/adr/0019-project-configuration-seed-segregation.md` (apenas leitura de referência, salvo se faltar link cruzado)
  - `tests/unit/test_docs_translation_parity.py`
  - `tests/unit/test_project_config_seed_docs.py` *(novo arquivo)*
- **Instruções Passo a Passo:**
  1. Ler `docs/config-tui.md` próximo à linha 159 e atualizar `config-tui.pt_br.md`, `config-tui.pt_pt.md`, `config-tui.es_es.md` e `config-tui.fr_fr.md` adicionando a descrição traduzida de `GITPR_SKIP_PROJECT_CONFIG_SEED=true` e o link localizado correspondente para `pull-request-publication.<lang>.md#94-...` (preservando contagem exata de headings, linhas `|`, bullets e blocos ` ``` `).
  2. Ler integralmente `docs/pull-request-publication.md` e mapear todas as seções divergentes nas quatro traduções (incluindo §4 com `gitpr -c`/`-r`/`-f`/`-is`, `--status` e `--no-unstaged-check`; callout `> [!IMPORTANT]` em §9.1; subseção `### 9.4` completa sobre CI/CD, monorepos, clean trees e `GITPR_SKIP_PROJECT_CONFIG_SEED=1`; linha `GITPR_SKIP_PROJECT_CONFIG_SEED` na tabela de §14; e Exemplos 9 e 10 completos em §15).
  3. Atualizar `docs/pull-request-publication.pt_br.md`, `.pt_pt.md`, `.es_es.md` e `.fr_fr.md` traduzindo o conteúdo integralmente no idioma-alvo (pt-BR vs pt-PT distintos) e garantindo que cada arquivo possua exatamente a mesma contagem estrutural (`headings`, `table_rows`, `bullets`, `fences`) que `docs/pull-request-publication.md`.
  4. Remover `"pull-request-publication"` do dicionário `_PARITY_EXCEPTIONS` em `tests/unit/test_docs_translation_parity.py` (a função `test_parity_exceptions_are_still_real()` falha caso a entrada não seja removida após a correção).
  5. Criar `tests/unit/test_project_config_seed_docs.py` seguindo o padrão de `tests/unit/test_scm_multiforge_docs_parity.py` e `tests/unit/test_auto_update_docs_parity.py`, validando nos 5 idiomas: presença de `### 9.4` e `GITPR_SKIP_PROJECT_CONFIG_SEED` em `docs/pull-request-publication.*`, menção a `GITPR_SKIP_PROJECT_CONFIG_SEED` em `docs/config-tui.*`, e existência de `docs/adr/0019-project-configuration-seed-segregation.md` com referências cruzadas esperadas.
- **Critérios de Aceite:**
  - Todas as traduções de `config-tui` e `pull-request-publication` contêm `GITPR_SKIP_PROJECT_CONFIG_SEED`, §9.4 e assinatura estrutural idêntica ao inglês.
  - `"pull-request-publication"` não consta mais em `_PARITY_EXCEPTIONS`.
  - `tests/unit/test_project_config_seed_docs.py` existe e passa nos 5 idiomas.
- **Comando de Verificação:**
  - `python -m pytest tests/unit/test_project_config_seed_docs.py tests/unit/test_docs_translation_parity.py -v`

---

### Etapa 3 — Mover `github-issue-prompt-com-gh.md` para `docs/extra/`, remover `_EN_ONLY` e completar os índices dos `README*.md`

- **Objetivo:** Alcançar cobertura 51/51 (100%) de 5 idiomas na raiz de `docs/` movendo o how-to avulso para `docs/extra/`, e atualizar a seção `📚` dos cinco `README*.md` com os guias canônicos ausentes.
- **Origem no Relatório:** Auditoria de i18n/docs (`v0.0.25`) e inventário de `docs/` vs. `README*.md`.
- **Arquivos-Alvo:**
  - `docs/github-issue-prompt-com-gh.md` → mover para `docs/extra/github-issue-prompt-com-gh.md`
  - `tests/unit/test_docs_translation_parity.py` (`_EN_ONLY`)
  - `README.md`, `README.pt_br.md`, `README.pt_pt.md`, `README.es_es.md`, `README.fr_fr.md`
  - Qualquer arquivo em `docs/` ou `tests/` que aponte para `github-issue-prompt-com-gh.md` (verificar via busca antes de concluir)
- **Instruções Passo a Passo:**
  1. Verificar se algum arquivo em `docs/`, `README*.md`, `src/` ou `tests/` referencia `github-issue-prompt-com-gh`.
  2. Mover `docs/github-issue-prompt-com-gh.md` para `docs/extra/github-issue-prompt-com-gh.md` e atualizar eventuais referências encontradas no passo 1.
  3. Em `tests/unit/test_docs_translation_parity.py`, remover `"github-issue-prompt-com-gh"` de `_EN_ONLY` (linhas 14–16), deixando `_EN_ONLY = {}`.
  4. Ler os primeiros parágrafos de cada guia ausente para redigir descrições fiéis e traduzidas na seção `📚` dos `README*.md`:
     - Em **todos os 5 READMEs**: adicionar links para `gitpr-issue-option`, `guia-regex-gitpr`, `marketplace-publishing-guide`, `otimizacao-de-tokens`, `untracked-files` e `version-markers`.
     - Adicionalmente nos **4 READMEs traduzidos** (`README.pt_br.md`, `README.pt_pt.md`, `README.es_es.md`, `README.fr_fr.md`): adicionar link para `mentor-mode`.
  5. Usar exclusivamente os parâmetros de URL aceitos pelo site e validados por `tests/test_doc_links.py`: sem `?lang=` em `README.md`, `?lang=pt_br` em `README.pt_br.md`, `?lang=pt_pt` em `README.pt_pt.md`, `?lang=es` em `README.es_es.md` e `?lang=fr` em `README.fr_fr.md`.
- **Critérios de Aceite:**
  - `docs/github-issue-prompt-com-gh.md` não existe na raiz de `docs/` e existe em `docs/extra/github-issue-prompt-com-gh.md`.
  - 100% dos arquivos `.md` de topo em `docs/` têm exatamente 5 variantes de idioma sem exceção em `_EN_ONLY`.
  - Os 5 `README*.md` linkam todos os guias listados no passo 4 usando os query params `?lang=` corretos.
- **Comando de Verificação:**
  - `python -m pytest tests/test_doc_links.py tests/unit/test_docs_translation_parity.py -v`

---

### Etapa 4 — Documentar custo e latência de Map-Reduce (`GITPR_MAP_REDUCE_MAX_TOKENS` / `MAX_PART_TOKENS`) nos 5 idiomas

- **Objetivo:** Explicar em `docs/metricas-telemetria.*` e na ADR-0022 como o particionamento Map-Reduce multiplica chamadas e tokens de entrada/saída, e como ajustar os limiares por provedor e analisar `map_reduce`, `chunks_count` e `duration_ms` nos relatórios de telemetria.
- **Origem no Relatório:** `docs/adr/0022-map-reduce-per-provider-token-partitioning.md` + `v0.0.24` / `v0.0.25`.
- **Arquivos-Alvo:**
  - `docs/metricas-telemetria.md`, `docs/metricas-telemetria.pt_br.md`, `docs/metricas-telemetria.pt_pt.md`, `docs/metricas-telemetria.es_es.md`, `docs/metricas-telemetria.fr_fr.md`
  - `docs/adr/0022-map-reduce-per-provider-token-partitioning.md`
  - Somente leitura de referência antes da redação: `src/config.py` (linhas 252–353), `src/metrics.py`, `docs/map-reduce-diff.md`
- **Instruções Passo a Passo:**
  1. Confirmar em `src/config.py` e `docs/map-reduce-diff.md` os nomes exatos e valores padrão vigentes: `GITPR_MAP_REDUCE_MAX_TOKENS` (`90000`), `GITPR_MAP_REDUCE_MAX_PART_TOKENS` (`50000`), overrides por provedor `GITPR_MAP_REDUCE_MAX_TOKENS_<PROVIDER>` / `GITPR_MAP_REDUCE_MAX_PART_TOKENS_<PROVIDER>`, preços em `DEFAULT_MODEL_PRICES` (ex.: `gemini-2.5-flash-lite` USD 0.10/0.40, `gemini-2.5-pro` USD 1.25/10.00, `deepseek-v4-flash` USD 0.14/0.28, `deepseek-v4-pro` USD 0.435/0.87 por 1M tokens) e custo zero para `LOCAL_PROVIDERS = ("ollama", "local")`.
  2. Adicionar subseção nova em `docs/metricas-telemetria.md` (e nos 4 espelhos `.pt_br.md`, `.pt_pt.md`, `.es_es.md`, `.fr_fr.md`) cobrindo: impacto em custo/latência de diffs grandes (`N` chunks de Map + 1 chamada de Reduce), leitura das colunas `map_reduce`, `chunks_count` e `duration_ms` no ledger/CSV/JSON, e ajuste prático via `GITPR_MAP_REDUCE_MAX_TOKENS` / `GITPR_MAP_REDUCE_MAX_PART_TOKENS` e variantes `<PROVIDER>` para equilibrar latência vs. orçamento.
  3. Garantir paridade estrutural idêntica nos 5 arquivos de `docs/metricas-telemetria.*` (mesmo número de headings, linhas de tabela, bullets e fences).
  4. Atualizar `docs/adr/0022-map-reduce-per-provider-token-partitioning.md` adicionando referência cruzada para a nova seção em `docs/metricas-telemetria.md` sobre observabilidade de custo e latência.
- **Critérios de Aceite:**
  - Todos os 5 arquivos `docs/metricas-telemetria.*` documentam os nomes reais `GITPR_MAP_REDUCE_MAX_TOKENS` e `GITPR_MAP_REDUCE_MAX_PART_TOKENS` (padrões `90,000` / `50,000`), `chunks_count`, `duration_ms` e impacto financeiro baseado nos preços reais de `src/config.py`.
  - Paridade estrutural preservada nos 5 idiomas e link/nota adicionados em ADR-0022.
- **Comando de Verificação:**
  - `python -m pytest tests/unit/test_docs_translation_parity.py tests/test_metrics.py -v`

---

### Etapa 5 — Documentar migração SCM em `.env` somente leitura / efêmero (`persisted=False`) em `docs/scm-multiforge.*` e ADR-0020

- **Objetivo:** Documentar claramente o comportamento resiliente de `migrate_legacy_scm_config()` em runners CI/CD ou sistemas com `~/.gitpr/.env` protegido/somente leitura, onde a persistência falha (`persisted=False`) sem abortar a execução.
- **Origem no Relatório:** Auditoria pós-ADR-0020 (`src/scm_settings.py` e `docs/scm-multiforge.*`).
- **Arquivos-Alvo:**
  - `docs/scm-multiforge.md`, `docs/scm-multiforge.pt_br.md`, `docs/scm-multiforge.pt_pt.md`, `docs/scm-multiforge.es_es.md`, `docs/scm-multiforge.fr_fr.md`
  - `docs/adr/0020-per-repo-scm-provisioning-migration.md`
  - `tests/unit/test_scm_multiforge_docs_parity.py` (opcionalmente expandir asserção para cobrir a nota de fallback read-only/`persisted=False`)
  - Somente leitura de referência: `src/scm_settings.py` (linhas 217–342) e `tests/scm/test_scm_settings.py`
- **Instruções Passo a Passo:**
  1. Ler `src/scm_settings.py` (linhas 217–342) para confirmar o comportamento exato de `_migrate_legacy_scm_config` / `migrate_legacy_scm_config`: captura `(OSError, PermissionError)`, retorna `MigrationResult(..., persisted=False, warning=...)`, aplica `writes` em `os.environ` e remove `GITPR_SCM_PROVIDER`, `GITPR_SCM_TOKEN_ENCRYPTED` e `GITPR_SCM_BASE_URL` do ambiente da execução.
  2. Expandir `### 3.1` em `docs/scm-multiforge.md` e em suas 4 traduções (`.pt_br.md`, `.pt_pt.md`, `.es_es.md`, `.fr_fr.md`) explicando que, quando `~/.gitpr/.env` é somente leitura (ex.: volumes montados `:ro` ou containers efêmeros), a migração retorna `persisted=False`, emite aviso a cada comando e degrada com segurança para `os.environ` em memória (recomendando remover as chaves legadas da imagem/script ou usar `GITPR_SCM_TOKEN`). Preservar integralmente todos os termos exigidos por `tests/unit/test_scm_multiforge_docs_parity.py` e a paridade estrutural idêntica nos 5 idiomas.
  3. Registrar esse comportamento na seção de consequências/implementação de `docs/adr/0020-per-repo-scm-provisioning-migration.md`.
- **Critérios de Aceite:**
  - Os 5 arquivos `docs/scm-multiforge.*` e a ADR-0020 descrevem explicitamente a degradação segura com `persisted=False` em `.env` read-only.
  - Todos os testes de paridade de documentação SCM e testes unitários de `scm_settings` passam.
- **Comando de Verificação:**
  - `python -m pytest tests/unit/test_scm_multiforge_docs_parity.py tests/unit/test_docs_translation_parity.py tests/scm/test_scm_settings.py -v`

---

### Etapa 6 — Suportar domínios customizados do GitHub Enterprise em `GitHubProvider.parse_repo_ref`

- **Objetivo:** Permitir que repositórios hospedados em GitHub Enterprise Server (ex.: `github.acme.com`) tenham `owner/repo` extraídos corretamente em URLs HTTPS e SSH, alinhando `GitHubProvider.parse_repo_ref` ao padrão host-agnóstico de `GitLabProvider.parse_repo_ref`, e atualizar a documentação que hoje aponta essa limitação.
- **Origem no Relatório:** `docs/survey/20261114_self_hosted_forge_detection_surveyfacts.md` (item 3) e `docs/scm-multiforge.md` (§1.2 linha 61 e §3 linha 104).
- **Arquivos-Alvo:**
  - `src/infrastructure/scm/github_provider.py` (`parse_repo_ref`, linhas 81–94)
  - `tests/scm/test_github_provider.py`
  - `docs/scm-multiforge.md`, `docs/scm-multiforge.pt_br.md`, `docs/scm-multiforge.pt_pt.md`, `docs/scm-multiforge.es_es.md`, `docs/scm-multiforge.fr_fr.md`
  - Somente leitura de referência: `src/infrastructure/scm/gitlab_provider.py` (`_REMOTE_RE` e `parse_repo_ref`, linhas 38–101), `src/infrastructure/scm/web_links.py`, `src/infrastructure/scm/factory.py`
- **Instruções Passo a Passo:**
  1. Ler `src/infrastructure/scm/github_provider.py` (linhas 1–120) e `src/infrastructure/scm/gitlab_provider.py` (linhas 30–110) para reutilizar o mesmo padrão de parsing agnóstico de host (`https://`, `http://`, `ssh://git@host/...`, `git@host:owner/repo.git` — avaliando também subgrupos/prefixos se houver, ou exigindo `owner/repo` válido para GitHub sem aceitar URLs inválidas/vazias).
  2. Refatorar `GitHubProvider.parse_repo_ref` para aceitar hosts customizados além de `github.com`, mantendo `ValueError` descritivo quando o formato não contiver um par `owner/repo` válido. Confirmar que `self.base_url` (controlado por `GITHUB_BASE_URL`) e os testes de contrato continuam íntegros.
  3. Adicionar testes unitários em `tests/scm/test_github_provider.py` cobrindo: URLs HTTPS/SSH em `github.com`, HTTPS/SSH/SSH-scheme em GitHub Enterprise (ex.: `https://github.acme.com/owner/repo.git` e `git@github.acme.com:owner/repo.git`) e rejeição com `ValueError` para URLs malformadas.
  4. Atualizar §1.2 (linha 61) e §3 (linha 104, linha da tabela de `GITHUB_BASE_URL`) nos 5 arquivos `docs/scm-multiforge.*` removendo a afirmação de que domínios customizados do GitHub Enterprise falham no parse (mantendo a explicação para domínios arbitrários que não contêm `github` no hostname, ex.: `git.acme.com`, onde `scm.provider: github` em `gitpr.config.yml` continua necessário), preservando estrita paridade estrutural.
- **Critérios de Aceite:**
  - `GitHubProvider.parse_repo_ref` extrai `RepoRef(owner=..., repo=...)` para remotes `github.com` e domínios GitHub Enterprise customizados.
  - Documentação `docs/scm-multiforge.*` (5 idiomas) reflete o novo comportamento sem quebra de paridade estrutural.
- **Comando de Verificação:**
  - `python -m pytest tests/scm/test_github_provider.py tests/scm/test_contract.py tests/scm/test_factory.py tests/unit/test_docs_translation_parity.py tests/unit/test_scm_multiforge_docs_parity.py -v`

---

### Etapa 7 — Incluir `claude-code` na mensagem de erro de `--install` em `src/mcp_server.py` e sincronizar i18n

- **Objetivo:** Alinhar a mensagem de erro de editor desconhecido em `_install_for_editor` (`src/mcp_server.py`, linha ~2901) com as opções reais aceitas pelo argumento `--install` (`choices` na linha ~3058), mantendo 100% de paridade nos 6 dicionários JSON de idioma.
- **Origem no Relatório:** Auditoria de consistência CLI/MCP e contrato `TestNoMissingKeys` (`tests/test_i18n.py`).
- **Arquivos-Alvo:**
  - `src/mcp_server.py`
  - `langs/pt_br.json`, `langs/pt_pt.json`, `langs/es.json`, `langs/es_es.json`, `langs/fr.json`, `langs/fr_fr.json`
  - `scripts/sync_all_langs.py` (verificar se contém a chave antiga antes de editar)
  - `tests/test_mcp_server.py`
- **Instruções Passo a Passo:**
  1. Ler `src/mcp_server.py` ao redor das linhas 2895–2915 e 3050–3065 para confirmar todas as opções em `--install` `choices` (`vscode`, `cursor`, `claude-code`, `claude`, `zed`, `auto`) e qualquer outra ocorrência dessa lista em `_install_for_editor`.
  2. Atualizar a string de erro em `_install_for_editor` dentro de `__(...)` para listar todas as opções válidas, incluindo `claude-code`.
  3. Substituir a chave antiga (`"Unknown editor: '{editor}'. Valid options: vscode, cursor, claude, zed, auto"`) pela nova chave nos 6 arquivos JSON de `langs/` preservando a tradução real em cada idioma (e atualizar eventual entrada equivalente em `scripts/sync_all_langs.py` se presente).
  4. Inspecionar `tests/test_mcp_server.py` e adicionar teste unitário garantindo que chamar `_install_for_editor` com um editor inválido reporta `claude-code` entre as opções válidas.
- **Critérios de Aceite:**
  - Mensagem de erro de `_install_for_editor` corresponde exatamente a `choices` da CLI.
  - `tests/test_i18n.py` passa sem chaves faltantes, órfãs ou sem tradução.
- **Comando de Verificação:**
  - `python -m pytest tests/test_i18n.py tests/test_mcp_server.py -v`

---

### Etapa 8 — Adicionar tradução `pt-pt` à extensão VS Code (`extensions/vscode/`)

- **Objetivo:** Completar a cobertura de Português Europeu (`pt-pt`) nos bundles de localização da extensão `extensions/vscode/`, equiparando-a aos idiomas já suportados (`en`, `pt-br`, `es`, `fr`).
- **Origem no Relatório:** `docs/reports/relatorio_estado_v0.0.25.md` (`🌐 Internacionalização e Documentação` — extensão VS Code sem `pt-pt`).
- **Arquivos-Alvo:**
  - `extensions/vscode/package.nls.json` e `extensions/vscode/package.nls.pt-br.json` (referência de chaves/estilo)
  - `extensions/vscode/l10n/bundle.l10n.json` e `extensions/vscode/l10n/bundle.l10n.pt-br.json` (referência de chaves/estilo)
  - `extensions/vscode/package.nls.pt-pt.json` *(novo arquivo)*
  - `extensions/vscode/l10n/bundle.l10n.pt-pt.json` *(novo arquivo)*
- **Instruções Passo a Passo:**
  1. Ler integralmente `extensions/vscode/package.nls.json` (14 chaves), `package.nls.pt-br.json`, `extensions/vscode/l10n/bundle.l10n.json` (26 chaves) e `l10n/bundle.l10n.pt-br.json`.
  2. Criar `extensions/vscode/package.nls.pt-pt.json` traduzindo todas as 14 chaves para Português Europeu (PT-PT natural, usando convenções de Portugal já adotadas em `langs/pt_pt.json` / `docs/*.pt_pt.md`, mantendo chaves JSON idênticas).
  3. Criar `extensions/vscode/l10n/bundle.l10n.pt-pt.json` traduzindo todas as 26 chaves para Português Europeu, preservando placeholders `{0}`, `{1}`, `{2}` exatamente na mesma sintaxe do arquivo base.
  4. Validar com script Python que o conjunto de chaves e todos os placeholders `{n}` em `package.nls.pt-pt.json` e `bundle.l10n.pt-pt.json` são 100% idênticos aos arquivos base em inglês e que todos os valores difiram do inglês (exceto termos técnicos universais como nome próprio, se aplicável). Se houver scripts de teste/lint em `extensions/vscode/package.json`, executá-los também.
- **Critérios de Aceite:**
  - `extensions/vscode/package.nls.pt-pt.json` e `extensions/vscode/l10n/bundle.l10n.pt-pt.json` existem, são JSON válidos e têm 100% de paridade de chaves e placeholders `{n}` com os originais em inglês.
- **Comando de Verificação:**
  - `python -c "import json, re; check = lambda a, b: (set(json.load(open(a, encoding='utf-8')).keys()) == set(json.load(open(b, encoding='utf-8')).keys())); assert check('extensions/vscode/package.nls.json', 'extensions/vscode/package.nls.pt-pt.json') and check('extensions/vscode/l10n/bundle.l10n.json', 'extensions/vscode/l10n/bundle.l10n.pt-pt.json'); print('VS Code pt-pt l10n parity OK')"`

---

### Verificação Global Final (após concluir Etapas 1 a 8)

Executar a suíte completa de testes Python antes de gerar o relatório final em `docs/gemini/reports/{branch}/`:

- `python -m pytest -v`

---

## 3. Ações Operacionais do Mantenedor & Backlog Futuro

Os itens abaixo também aparecem nas seções `🚧 Próximos Passos` dos relatórios em `docs/reports/`, porém **não devem ser automatizados pelo agente de código local**, pois dependem de credenciais externas, decisões de produto ou reescrita de histórico/tags remotas:

1. **M1 — Publicação e Tagging de Release (`v1.7.0` / `v1.8.0` no PyPI e GitHub Releases):**
   - Acompanhamento de eventual ajuste manual da tag `v1.7.0` no remoto (se aplicável) e disparo humano da tag `v1.8.0` para acionar `.github/workflows/release.yml` após revisão e commit das alterações acumuladas.
2. **M2 — Publicação da Extensão VS Code / Open VSX (`scripts/marketplace-setup-wizard.sh` e `ext-v*`):**
   - Requer execução interativa pelo mantenedor com PATs reais do Visual Studio Marketplace (`VSCE_PAT`) e Open VSX (`OVSX_PAT`), configuração de publishers/secrets no GitHub e disparo da tag `ext-v*` conforme documentado em `docs/marketplace-publishing-guide.md`.
3. **M3 — Expansão do Roadmap de Provedores de IA (Backlog Aberto):**
   - Implementação futura de suporte direto à API OpenAI e eventuais novos provedores locais compatíveis além de Ollama, dependente de especificação arquitetural dedicada (`Strategy` em `src/ai_providers.py`, variáveis `.env`, tabela de preços e testes).
