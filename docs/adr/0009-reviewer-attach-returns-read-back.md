# 0009 — `request_pull_request_reviewers` devolve o read-back

- **Status:** Aceito
- **Data:** 2026-10-31
- **Decisores:** Natan Fiuza, Antigravity
- **Contexto:** ADR-002 (emenda de 2026-09-17), commit `eb55400`, item herdado do relatório `2026-09-17_reviewer_login_resolution.md`

## Contexto e Decisão

O GitHub responde `201` a um login que não existe e simplesmente não anexa ninguém. Com retorno `None`, o chamador não tinha como detectar o revisor descartado. Desde a **v1.2.0**, `ScmProvider.request_pull_request_reviewers()` devolve `list[str]` com os logins que o forge **realmente anexou**, lidos do corpo da resposta; lista vazia significa "aceito e ignorado".

Isso quebra subclasses de terceiros que **sobrescrevem** o método e devolvem `None`. Decidimos manter a quebra, mas torná-la inofensiva e documentada:

1. O chamador (`PrPublishApp._unattached_warnings`) trata `None` como "não dá para verificar": sem aviso de não anexado e sem falha. O PR já existe e o attach nunca é fatal.
2. A documentação orienta quem migra a devolver o que o forge anexou ou, se o forge não devolve corpo, a lista pedida (otimista).
3. O método segue **não abstrato**, com default `ScmNotSupportedError`.

## Opções Consideradas

- **Tornar o método abstrato:** Rejeitado. Forçaria os quatro providers e quebraria todo terceiro que não o implementa, embora só o GitHub tenha API de revisores.
- **Levantar erro quando o retorno for `None`:** Rejeitado. Um terceiro legado passaria a falhar justamente num passo que já é não fatal, sem ganho: o PR continua criado.
- **Manter `None` e criar um método novo para o read-back:** Rejeitado. Duplica a superfície do contrato para um único forge e deixa a API antiga enganosa.

## Consequências

- Terceiros que só **chamam** o método não são afetados. Quem o **sobrescreve** deve migrar para `list[str]`; quem não migra perde a detecção de revisor ignorado, mas nada falha.
- Quem devolve a lista pedida em vez do read-back real também desliga essa detecção para o seu forge. A doc registra o trade-off.
- Contrato documentado em `docs/scm-multiforge.md` §6.1 (e traduções) e em `docs/suggested-reviewers.md` §5.
- A tolerância a `None` fica coberta por testes em `tests/test_pr_publish_app.py` (`TestLegacyNoneReadBack`). Remover essa tolerância exige novo ADR.
