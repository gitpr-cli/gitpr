# Plano — Documentar a quebra de contrato de `request_pull_request_reviewers`

## Objetivo

O retorno de `ScmProvider.request_pull_request_reviewers()` passou de `None` para `list[str]` (logins realmente anexados, lidos do corpo do `201`). Isso quebra subclasses de terceiros que **sobrescrevem** o método. O relatório `2026-09-17_reviewer_login_resolution.md` (linha 121) chamou isso de "único ponto de contato alterado" e parou aí. Nenhuma doc de usuário registra a quebra. Este plano fecha o item herdado.

## Fatos verificados

- Quebra introduzida pelo commit `eb55400` (2026-09-17). Primeira release que a contém: **v1.2.0**. Versão atual: **1.4.4**, `__lang_version__` **v0.0.37**.
- Base: [base.py L277-294](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/src/infrastructure/scm/base.py#L277-L294) já declara `-> list[str]`; o default levanta `ScmNotSupportedError`. Só o GitHub implementa.
- O chamador **já tolera `None`**: [`_unattached_warnings`](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/src/ui/pr_publish_app.py#L894-L903) trata `None` como "não dá para verificar" e devolve `[]`. Mas o docstring da base não diz que `None` é aceito, nenhum teste cobre esse caminho, e o `_log` imprime `attached None`.
- `docs/scm-multiforge.md` só fala de terceiros na nota do shim `github_api.py` (linha 141). Não há seção de contrato para quem escreve um `ScmProvider`.
- `CHANGELOG.md` é gerado por release (`gitpr release`); não tem seção `Unreleased`.
- ADRs: `docs/adr/` vai até `0008`. O próximo é **0009**. O `CONTEXT.md` não tem `read-back` nem `ScmProvider`.

## Decisões (grill)

| # | Decisão |
|---|---|
| Q1 | Documentar em `scm-multiforge` (seção nova) e `suggested-reviewers` (§5), nos 5 idiomas cada. |
| Q2 | **B**: documentar e deixar o chamador tolerar `None`. A tolerância já existe no código; falta contratá-la na base, testá-la e documentá-la. |
| Q3 | Quebra "desde v1.2.0". Contrato do `ScmProvider` documentado como estável a partir da 1.x, com esta exceção registrada. |
| Q4 | Subclasse deve devolver os logins realmente anexados. Se o forge não devolve corpo, devolver a lista pedida (otimista), e a doc avisa que isso desliga a detecção de revisor ignorado. |
| Q5 | **B**: ADR novo `0009`. |

> [!IMPORTANT]
> Q2-B e Q4 se sobrepõem: o código aceita `None` (cannot verify), mas a doc recomenda devolver a lista pedida. Proponho documentar `None` como **legado tolerado, não recomendado**, e a lista pedida como o jeito certo de migrar.

## Mudanças propostas

### 1. Código (mínimo, só contrato e teste)

- **[MODIFY] `src/infrastructure/scm/base.py`**: acrescentar ao docstring de `request_pull_request_reviewers` que `None` (contrato pré-v1.2.0) é tolerado pelo chamador como "sem read-back", mas a implementação nova deve devolver `list[str]`. Sem mudança de assinatura nem de comportamento.
- **[MODIFY] `src/ui/pr_publish_app.py`**: nenhuma mudança de lógica. Só ajustar o `_log` para não imprimir `attached None` de forma enganosa (ex.: `attached (no read-back)`), nos dois pontos (L852 e L927), se isso não quebrar testes de log existentes.
- **[MODIFY] `tests/test_pr_publish_app.py`**: dois testes novos com provider fake que devolve `None`:
  - envio em lote: sem aviso de "not attached", PR segue criado;
  - envio um a um (caminho do `422`): idem.

### 2. Documentação (5 idiomas cada, paridade linha a linha)

- **[MODIFY] `docs/scm-multiforge.md` + `.pt_br/.pt_pt/.es_es/.fr_fr`**: seção nova "Contrato para provedores de terceiros" ao lado da nota do shim (L141), contendo:
  - tabela "antes (≤1.1.x) / depois (≥1.2.0)" do retorno;
  - quem é afetado (só quem **sobrescreve** o método; quem só chama não é);
  - guia de migração com snippet;
  - semântica: `[]` = aceito e ignorado; sem corpo no forge → devolver a lista pedida; `None` tolerado, mas legado.
- **[MODIFY] `docs/suggested-reviewers.md` + 4 idiomas**: em §5, uma frase e link para a seção nova.
- **[MODIFY] `docs/plans/ADR-002-reviewer-suggestion.md`**: uma linha na emenda datada apontando para o ADR-0009.

Snippet do guia de migração:

```python
class MyForgeProvider(ScmProvider):
    def request_pull_request_reviewers(self, repo, pr_id, reviewers) -> list[str]:
        body = self._post_reviewers(repo, pr_id, reviewers)
        # Return what the forge actually attached; [] means "accepted but ignored".
        return [r["login"] for r in body.get("requested_reviewers", [])] or []
        # Forge returns no body? Return `list(reviewers)` (optimistic, disables
        # the "not attached" warning for this forge).
```

### 3. ADR e glossário

- **[NEW] `docs/adr/0009-reviewer-attach-returns-read-back.md`**: segue o formato de `ADR-FORMAT.md` (status, contexto/decisão, opções consideradas, consequências). Registra: retorno `list[str]` em vez de `None`; `None` tolerado como "cannot verify"; opções rejeitadas (tornar o método abstrato, que forçaria os 4 providers; levantar erro em `None`, que quebraria terceiros em silêncio total).
- **[MODIFY] `CONTEXT.md`**: termos novos **Read-back** e **Requested reviewers attach** (glossário apenas, sem detalhes de implementação), conforme `domain-modeling`.

### 4. Relatório final

- **[NEW] `docs/gemini/reports/develop_natan/2026-10-31_document_reviewers_contract_break.md`** (exigido pelo `GEMINI.md`).

## Perguntas abertas

> [!IMPORTANT]
> **CHANGELOG.md** (você aprovou Q1 "recomendado", que incluía o item de changelog "se o projeto mantém um"): ele é gerado por `gitpr release`, sem seção `Unreleased`. Proponho **não editar à mão** e deixar a quebra registrada nas docs e no ADR. Se quiser a nota em "Breaking" na próxima release, diga e eu ajusto.

> [!NOTE]
> Há também o fato de o `scm-multiforge` falar de "11 métodos abstratos" e a base já ter vários não abstratos (`create_release`, `get_pull_request`, `request_pull_request_reviewers`). Isso pode entrar na seção nova, mas não vou corrigir o texto antigo sem você pedir.

## Plano de verificação

### Testes automatizados

```bash
python -m pytest tests/test_pr_publish_app.py tests/scm -v
python -m pytest tests/ -v
```

Também rodar o teste de paridade i18n/docs, se existir, e conferir que as 5 cópias de cada doc têm o mesmo número de cabeçalhos.

### Verificação manual

- Ler a seção nova em `scm-multiforge.md` e conferir se o guia de migração é suficiente para quem herda de `ScmProvider`.
- Conferir os links entre `suggested-reviewers`, `scm-multiforge`, ADR-0009 e ADR-002.

## Restrições do projeto

Sem `git add`, `commit` ou `push`. Tudo fica na working tree para a sua revisão.
