# Survey — Suporte a domínios customizados do GitHub Enterprise em `GitHubProvider.parse_repo_ref`

- **Data:** 2026-11-15
- **Branch:** `develop_natan`
- **Task:** `github_enterprise_parse_repo_ref`

## Contexto da tarefa

Na Etapa 6 de `docs/prompts/relatorio_pendencias_proximos_passos_i18n.md`, `GitHubProvider.parse_repo_ref` (`src/infrastructure/scm/github_provider.py`, linhas 81–94) aceita apenas o literal `github.com`, fazendo remotes de GitHub Enterprise Server (ex.: `github.acme.com`) falharem com `ValueError` mesmo quando `GITHUB_BASE_URL` está configurado e `detect_provider_from_remote()` já os reconhece como `github`. A limitação também está documentada em `docs/scm-multiforge.*` (§1.2 e §3).

## Fatos levantados

1. **Parser atual do `GitHubProvider` (`src/infrastructure/scm/github_provider.py:81-94`):**
   Usa `re.search(r"github\.com[:/]([^/]+)/([^/]+?)(?:\.git)?/?$", remote_url.strip())`, exigindo o literal `github.com` e exatamente 2 segmentos (`owner/repo`).
2. **Parser de referência do `GitLabProvider` (`src/infrastructure/scm/gitlab_provider.py:38, 81-101`):**
   Usa `_REMOTE_RE = re.compile(r"^(?:[^/@]+@)?(?P<host>[^/:]+(?::\d+)?)[:/](?P<path>.+?)(?:\.git)?/?$")` após remover o esquema (`if "://" in url: url = url.split("://", 1)[1]`), aceitando hosts arbitrários, portas opcionais (`:2222`) e credenciais (`user@` / `user:token@`).
3. **Contrato de `ScmProvider` (`tests/scm/test_contract.py`):**
   `ProviderContractCase.test_parse_repo_ref` valida `RepoRef(raw=..., workspace=..., name=..., provider="github")` com `workspace` e `name` não vazios.
4. **Cobertura de testes atual (`tests/scm/test_github_provider.py`):**
   Não há classe dedicada `TestParseRepoRef` cobrindo `github.com`, hosts GitHub Enterprise (`github.acme.com`), `ssh://` com porta e rejeição de URLs malformadas.
5. **Documentação `docs/scm-multiforge.*` (5 idiomas):**
   - `§1.2` linha 61 afirma que `github.acme.com` falha no parse e não é suportado.
   - `§1.2` linhas 65–68 exibem `Could not parse GitHub repository from remote URL: https://github.acme.com/owner/repo.git` abaixo do aviso de host desconhecido.
   - `§3` linha 104 (`GITHUB_BASE_URL`) afirma que um remote em domínio customizado continua falhando no parse.
   - `tests/unit/test_docs_translation_parity.py` exige paridade estrutural idêntica (`headings`, `table_rows`, `bullets`, `fences`) entre os 5 idiomas de `docs/scm-multiforge.*`.

## Decisões das rodadas

### Rodada 1
- **Q1 (Profundidade de caminho em `GitHubProvider.parse_repo_ref`):** Exigir **exatamente 2 segmentos** (`owner/repo`) após o host/porta, lançando `ValueError` se houver menos ou mais de 2 segmentos (evitando aceitar URLs malformadas ou com subcaminhos inválidos para GitHub).
- **Q2 (Atualização de `docs/scm-multiforge.*` nos 5 idiomas):** Atualizar a linha 61 da tabela da §1.2 para explicar que hosts GHE com `github` no hostname são detectados e parseados normalmente precisando apenas de `GITHUB_BASE_URL` (mantendo a orientação de `scm.provider: github` em `gitpr.config.yml` para domínios arbitrários sem `github`, ex.: `git.acme.com`); no bloco das linhas 65–68, manter apenas o aviso de host não reconhecido; na linha 104 (§3), remover a ressalva de falha de parse.
- **Q3 (Modelagem de domínio — `CONTEXT.md` e ADR):** Não criar ADR nem alterar `CONTEXT.md`, pois trata-se de remoção de limitação de parser alinhada ao contrato existente.
