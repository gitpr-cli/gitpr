# Plano de Execução — Host self-hosted não reconhecido

- **Branch:** `develop_natan`
- **Data:** 2026-11-14
- **Task:** `self_hosted_forge_detection`
- **Origem:** sessão `/grill-with-docs` — "Acompanhar o host self-hosted não reconhecido"

## Objetivo

Documentar o sintoma do host self-hosted cujo domínio não nomeia a forge, avisar o
usuário em runtime antes de a publicação falhar, e corrigir a ordem do detector para
que o aviso não dispare em repositórios GitHub.

## Decisões

1. **Escopo:** documentação (5 idiomas) + aviso em runtime + correção do detector.
2. **Documentação:** nova subseção `### 1.2` em `docs/scm-multiforge.md` e nos 4
   espelhos, com paridade estrutural exata (o arquivo não está em
   `_PARITY_EXCEPTIONS`).
3. **Aviso:** em `resolve_scm_settings`, condição `remote` presente e
   `choice.source == SOURCE_DEFAULT`; impresso por `release --publish` e pelo fluxo
   de PR/issues, em amarelo, a cada execução.
4. **Texto EN:** `⚠️ The origin remote does not name a forge, so GitPR is using
   GitHub. Run 'gitpr --init' to choose the right forge for this repository.`
5. **Registros:** dois termos em `CONTEXT.md`, linha do detector no glossário,
   consequência no ADR-016 e uma cláusula na seção Multi-Forge SCM do `CLAUDE.md`.

## Mudanças

| Área | Arquivo | Mudança |
| --- | --- | --- |
| Código | `src/infrastructure/scm/factory.py` | `detect_provider_from_remote`: teste `"github" in url` movido para antes de `default is None` |
| Código | `src/scm_settings.py` | `_default_provider_warning()` + append quando `remote` existe e a origem é `default` |
| i18n | `langs/{pt_br,pt_pt,es,es_es,fr,fr_fr}.json` | Chave nova, tradução real, mesma posição |
| Docs | `docs/scm-multiforge.{md,pt_br.md,pt_pt.md,es_es.md,fr_fr.md}` | §1.2 (intro + tabela de 3 linhas + parágrafo repo/máquina + bloco de código) e ressalva na linha `GITHUB_BASE_URL` da §3 |
| Testes | `tests/scm/test_factory.py` | `github.com` (https e ssh) com `default=None` → `github` |
| Testes | `tests/scm/test_scm_settings.py` | Aviso em remote desconhecido; silêncio sem remote, em `github.com` e com override |
| Testes | `tests/scm/test_init_wizard.py` | Detecção real: `github.com` mostra "Detected forge: GitHub" e não grava override |
| Registros | `CONTEXT.md`, `docs/plans/glossary-scm-multiforge.md`, `docs/plans/ADR-016-per-provider-scm-settings.md`, `CLAUDE.md` | Termos, linha corrigida, consequência, cláusula |

## Contrato estrutural da §1.2 (por arquivo)

- 1 heading `###`
- 5 linhas de tabela (cabeçalho + separador + 3 linhas)
- 0 bullets
- 2 fences (` ```text ` de abertura e fechamento)

## Riscos e limites aceitos

- O aviso repete a cada comando de publicação até `--init` — decisão aceita em favor
  da visibilidade.
- GitHub Enterprise (`github.acme.com`) continua sem parse; agora documentado na §1.2.
- Falso positivo de caminho (`github.com/acme/gitlab-mirror` → gitlab) documentado,
  não corrigido.

## Verificação

```bash
python -m pytest tests/scm/test_factory.py tests/scm/test_scm_settings.py tests/scm/test_init_wizard.py -q
python -m pytest tests/test_i18n.py tests/unit/test_docs_translation_parity.py tests/unit/test_scm_multiforge_docs_parity.py tests/test_doc_links.py -q
python -m pytest tests -q
```
