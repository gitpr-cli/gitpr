# Survey — Host self-hosted não reconhecido

- **Data:** 2026-11-14
- **Branch:** `develop_natan`
- **Task:** `self_hosted_forge_detection`

## Contexto da tarefa

A resolução da forge por repositório depende de uma heurística por substring na URL do
`origin` (`src/infrastructure/scm/factory.py`). Um GitLab ou GitHub self-hosted em
domínio customizado (ex.: `git.acme.com`) não contém o nome da forge, então cai no
default `github` em silêncio (`src/scm_settings.py`) e o fluxo falha depois com
`Could not parse GitHub repository from remote URL: …`, porque o parser do GitHub exige
o literal `github.com` (`src/infrastructure/scm/github_provider.py`). O override em
`.gitpr/conf/gitpr.config.yml` resolve, mas só depois de alguém rodar `gitpr --init`.

## Fatos levantados

1. **Bug de ordem no detector (verificado executando o código):**
   `detect_provider_from_remote(url, default=None)` devolvia `None` até para
   `github.com`, porque `if default is None: return None` antecedia o teste
   `"github" in url`. Consequências reais: o wizard chamava de "not recognised" todo
   repositório GitHub e gravava um `scm.provider: github` espúrio no arquivo versionado.
   O detector é chamado com `default=None` em `core.run_scm_init_wizard` (linha 2533) e
   em `scm_settings.resolve_provider_choice` (linha 154) — os dois pontos que decidem
   SOURCE_REMOTE vs SOURCE_DEFAULT.
2. **Matching na URL inteira:** `https://github.com/acme/gitlab-mirror.git` é detectado
   como `gitlab` porque a checagem de forge ocorre sobre o URL completo. Falso positivo
   verificado; decidido documentar, não corrigir.
3. **GitHub Enterprise:** `github.acme.com` é detectado como GitHub (contém `github`),
   mas `GitHubProvider.parse_repo_ref` exige o literal `github.com`;
   `GITHUB_BASE_URL` muda só a base da API. Limitação documentada, não corrigida.
4. **Pontos de impressão do aviso:** `src/main.py` (`release --publish` e
   `_resolve_scm_context` para PR/issues) passam `warnings`; `metrics.py`,
   `release_engine.py`, MCP e a TUI de config não passam — ficam silenciosos.
5. **Contrato de paridade dos docs:** `tests/unit/test_docs_translation_parity.py::_scan`
   conta linhas que começam com `|` (incluindo o separador), headings por `^(#{1,6})\s`,
   bullets por `^\s*[-*]\s` e fences por `line.startswith("```")` (2 por bloco), ignorando
   conteúdo dentro de fences. `scm-multiforge` **não** está em `_PARITY_EXCEPTIONS` —
   os 5 arquivos precisam da mesma estrutura.
6. **Contrato de i18n:** `tests/test_i18n.py::TestNoMissingKeys` exige toda chave
   extraída por AST de `__()` nos 6 arquivos JSON; chave idêntica ao inglês (identity)
   falha. A concatenação implícita de literais adjacentes vira um único `ast.Constant`,
   então a string quebrada em duas linhas é extraída corretamente.
7. **Âncoras internas** não são validadas por `tests/test_doc_links.py`.

## Decisões das rodadas

### Rodada 1
- **Escopo:** documentação + aviso em runtime + correção do detector.
- **Formato da doc:** nova subseção `### 1.2`.
- **Cenários da tabela:** os quatro levantados (fallback e PR/issues; `--init` "not
  recognised"; GitHub Enterprise; contrato repo vs máquina).
- **Idiomas:** os 5 arquivos.

### Rodada 2
- **Ordem do detector:** corrigir (github antes de `default=None`).
- **Local do aviso:** `resolve_scm_settings`.
- **Frequência/estilo:** toda execução, em amarelo.
- **Registros:** termos no `CONTEXT.md`, linha no glossário, consequência no ADR-016.

### Rodada 3
- **Conteúdo da §1.2:** intro + tabela + passo a passo.
- **§3:** ressalva na linha de `GITHUB_BASE_URL` apontando para a §1.2.
- **Texto do aviso:** estilo do aviso de migração.
- **`CLAUDE.md`:** uma linha.

## Resultado

Plano aprovado e implementado. O aviso deixa de ser um alarme falso em GitHub e passa a
explicar, antes da falha de parse, por que um host self-hosted cai no GitHub e como
corrigi-lo com `gitpr --init`.
