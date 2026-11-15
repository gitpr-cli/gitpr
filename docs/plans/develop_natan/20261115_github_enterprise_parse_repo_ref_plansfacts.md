# Plano de Execução — Suportar domínios customizados do GitHub Enterprise em `GitHubProvider.parse_repo_ref` (Etapa 6)

- **Data:** 2026-11-15
- **Branch:** `develop_natan`
- **Task:** `github_enterprise_parse_repo_ref`

## Objetivo

Permitir que `GitHubProvider.parse_repo_ref` extraia `RepoRef(workspace=owner, name=repo, provider="github")` de remotes hospedados em GitHub Enterprise Server (ex.: `github.acme.com`) nos formatos HTTPS, HTTP, `ssh://`, `git://` e SCP (`git@host:owner/repo.git`), exigindo exatamente 2 segmentos (`owner/repo`), e atualizar `docs/scm-multiforge.*` (5 idiomas) removendo a limitação documentada.

## Arquivos-Alvo

1. `src/infrastructure/scm/github_provider.py`
   - Adicionar `_REMOTE_RE` (mesmo padrão agnóstico de host do `GitLabProvider`).
   - Refatorar `GitHubProvider.parse_repo_ref` para aceitar hosts customizados, remover esquema (`://`), validar exatamente 2 segmentos não vazios (`owner/repo`) e lançar `ValueError` descritivo caso contrário.
2. `tests/scm/test_github_provider.py`
   - Adicionar `TestParseRepoRef` cobrindo:
     - `github.com` (HTTPS, HTTPS sem `.git`, barra final, `git@github.com:...`, `ssh://git@github.com/...`).
     - GitHub Enterprise customizado (HTTPS, HTTP, `git@github.acme.com:owner/repo.git`, `ssh://git@github.acme.com:2222/owner/repo.git`, credenciais embutidas `https://user:token@github.acme.com/owner/repo.git`).
     - Rejeição com `ValueError` para string vazia, URL sem `owner/repo` (1 segmento), URL com 3+ segmentos e formato inválido.
3. `docs/scm-multiforge.md`, `docs/scm-multiforge.pt_br.md`, `docs/scm-multiforge.pt_pt.md`, `docs/scm-multiforge.es_es.md`, `docs/scm-multiforge.fr_fr.md`
   - Atualizar linha 61 (§1.2), linhas 65–68 (bloco de exemplo) e linha 104 (§3, `GITHUB_BASE_URL`) nos 5 idiomas preservando paridade estrutural idêntica.

## Verificação

```bash
python -m pytest tests/scm/test_github_provider.py tests/scm/test_contract.py tests/scm/test_factory.py tests/unit/test_docs_translation_parity.py tests/unit/test_scm_multiforge_docs_parity.py -v
```
