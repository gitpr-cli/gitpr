"""Tour scenario: a cross-tenant invoice download (IDOR) in an Express API.

The diff is repository content, so it stays in English in every language — the
same way the real tool answers in English about English code. Only the prose
the tour narrates is translated. A language missing from ``TEXT`` falls back to
English, so the scenario is usable while a translation is still being written.
"""

NAME = "security-issue"

DIFF = r"""diff --git a/src/routes/invoices.ts b/src/routes/invoices.ts
index c41e7a3..9b20f58 100644
--- a/src/routes/invoices.ts
+++ b/src/routes/invoices.ts
@@ -4,13 +4,18 @@ const router = Router();
 const router = Router();

 router.get('/invoices/:id/download', async (req, res) => {
-  const invoice = await Invoice.findByPk(req.params.id);
+  const invoice = await Invoice.findOne({
+    where: {
+      id: req.params.id,
+      organisationId: req.user.organisationId,
+    },
+  });

   if (!invoice) {
     return res.status(404).json({ error: 'Invoice not found' });
   }

-  return res.redirect(await invoice.pdfUrl());
+  return res.redirect(await invoice.signedPdfUrl());
 });

 export default router;
diff --git a/tests/invoices.test.ts b/tests/invoices.test.ts
index 2ae9d64..f70b1c8 100644
--- a/tests/invoices.test.ts
+++ b/tests/invoices.test.ts
@@ -44,4 +44,26 @@ it('returns 404 for an invoice that does not exist', async () => {
     expect(response.status).toBe(404);
   });

+  it('does not let a user download another organisation invoice', async () => {
+    const attacker = await createUser({ organisationId: 'org-b' });
+    const invoice = await createInvoice({ organisationId: 'org-a' });
+
+    const response = await request(app)
+      .get(`/invoices/${invoice.id}/download`)
+      .set('Authorization', `Bearer ${attacker.token}`);
+
+    expect(response.status).toBe(404);
+  });
+
+  it('still redirects the owner to the signed url', async () => {
+    const owner = await createUser({ organisationId: 'org-a' });
+    const invoice = await createInvoice({ organisationId: 'org-a' });
+
+    const response = await request(app)
+      .get(`/invoices/${invoice.id}/download`)
+      .set('Authorization', `Bearer ${owner.token}`);
+
+    expect(response.status).toBe(302);
+    expect(response.headers.location).toContain('signature=');
+  });
 });
"""

TEXT = {
    "en": {
        "title": "Express — invoice download leaks across organisations",
        "description": (
            "An IDOR: the download route looked the invoice up by primary key "
            "alone, so any authenticated user could fetch any other "
            "organisation's invoice."
        ),
        "commit_message": (
            "fix: scope invoice downloads to the caller's organisation\n"
            "\n"
            "`GET /invoices/:id/download` resolved the invoice with\n"
            "`findByPk`, so the row was fetched regardless of who owned it and\n"
            "any authenticated user could download another organisation's\n"
            "invoice by guessing the id.\n"
            "\n"
            "Resolve the invoice with a compound `where` on id and\n"
            "organisationId, and redirect to the signed url instead of the\n"
            "plain one. Reported by @marcos on 2026-09-11."
        ),
        "review": (
            "## Summary\n"
            "\n"
            "Correct fix for the reported issue: the ownership check now lives\n"
            "in the query itself, and returning 404 instead of 403 avoids\n"
            "confirming that an invoice id exists. Two follow-ups.\n"
            "\n"
            "### 1. The redirect is cacheable\n"
            "\n"
            "`res.redirect()` emits a 302 with no `Cache-Control`. The signed\n"
            "url is stable for the whole TTL, so a shared proxy can hand the\n"
            "same URL to a later requester — which re-opens the leak the query\n"
            "just closed. Send `Cache-Control: private, no-store` on this route.\n"
            "\n"
            "### 2. `req.user` is dereferenced without a guard\n"
            "\n"
            "If the auth middleware is ever detached from this route,\n"
            "`req.user.organisationId` throws and the client gets a 500 with a\n"
            "stack trace instead of a 401. Nothing in the suite covers an\n"
            "unauthenticated request to this endpoint.\n"
            "\n"
            "### Positive\n"
            "\n"
            "- 404 over 403 is the right call for a resource you do not own.\n"
            "- The regression test asserts the cross-tenant path directly, not a\n"
            "  proxy for it."
        ),
        "linter": {
            "errors": [
                "src/routes/invoices.ts:9 — 'req.user' dereferenced without a "
                "null check (rule: no-unchecked-session)."
            ],
            "warnings": [
                "tests/invoices.test.ts:50 — test name exceeds 60 characters "
                "(rule: max-test-name-length)."
            ],
        },
        "pr_description": (
            "## What\n"
            "\n"
            "Scopes the invoice download endpoint to the caller's organisation.\n"
            "\n"
            "## Why\n"
            "\n"
            "`GET /invoices/:id/download` resolved the invoice with `findByPk`.\n"
            "The row was returned for any authenticated caller, so an id was\n"
            "enough to download another organisation's invoice. Reported by\n"
            "@marcos on 2026-09-11 and confirmed by the regression test added\n"
            "here.\n"
            "\n"
            "## How\n"
            "\n"
            "- Replace `findByPk(id)` with a `findOne` scoped by both `id` and\n"
            "  `organisationId`.\n"
            "- Redirect to `signedPdfUrl()` so the object storage URL carries an\n"
            "  expiry and is not guessable.\n"
            "- Add a cross-organisation 404 test and an owner-path 302 test.\n"
            "\n"
            "## Notes for the reviewer\n"
            "\n"
            "The rename from `pdfUrl()` to `signedPdfUrl()` changes the redirect\n"
            "target, not just the query. Confirm no client stores the resolved\n"
            "URL past its TTL. The cache-control header is being handled in a\n"
            "separate change."
        ),
    },
    "pt_br": {
        "title": "Express — download de fatura vaza entre organizações",
        "description": (
            "Um IDOR: a rota de download buscava a fatura apenas pela chave "
            "primária, então qualquer usuário autenticado conseguia baixar a "
            "fatura de outra organização."
        ),
        "commit_message": (
            "fix: restringir o download de faturas à organização do solicitante\n"
            "\n"
            "`GET /invoices/:id/download` resolvia a fatura com `findByPk`,\n"
            "então a linha era buscada independentemente do dono e qualquer\n"
            "usuário autenticado conseguia baixar a fatura de outra organização\n"
            "adivinhando o id.\n"
            "\n"
            "Resolve a fatura com um `where` composto por id e organisationId, e\n"
            "redireciona para a url assinada em vez da url simples. Relatado por\n"
            "@marcos em 2026-09-11."
        ),
        "review": (
            "## Resumo\n"
            "\n"
            "Correção certa para o problema relatado: a checagem de posse agora\n"
            "está na própria consulta, e devolver 404 em vez de 403 evita\n"
            "confirmar que um id de fatura existe. Dois pontos de continuidade.\n"
            "\n"
            "### 1. O redirecionamento é cacheável\n"
            "\n"
            "`res.redirect()` emite um 302 sem `Cache-Control`. A url assinada é\n"
            "estável durante todo o TTL, então um proxy compartilhado pode\n"
            "entregar a mesma URL a um solicitante posterior — o que reabre o\n"
            "vazamento que a consulta acabou de fechar. Envie\n"
            "`Cache-Control: private, no-store` nesta rota.\n"
            "\n"
            "### 2. `req.user` é acessado sem verificação\n"
            "\n"
            "Se o middleware de autenticação for algum dia desligado desta rota,\n"
            "`req.user.organisationId` lança exceção e o cliente recebe um 500\n"
            "com stack trace em vez de um 401. Nada na suíte cobre uma requisição\n"
            "não autenticada a este endpoint.\n"
            "\n"
            "### Pontos positivos\n"
            "\n"
            "- 404 em vez de 403 é a escolha certa para um recurso que não é seu.\n"
            "- O teste de regressão verifica o caminho entre organizações\n"
            "  diretamente, não por procuração."
        ),
        "linter": {
            "errors": [
                "src/routes/invoices.ts:9 — 'req.user' acessado sem verificação "
                "de nulo (regra: no-unchecked-session)."
            ],
            "warnings": [
                "tests/invoices.test.ts:50 — nome do teste excede 60 caracteres "
                "(regra: max-test-name-length)."
            ],
        },
        "pr_description": (
            "## O que\n"
            "\n"
            "Restringe o endpoint de download de faturas à organização do\n"
            "solicitante.\n"
            "\n"
            "## Por quê\n"
            "\n"
            "`GET /invoices/:id/download` resolvia a fatura com `findByPk`. A\n"
            "linha era devolvida para qualquer solicitante autenticado, então\n"
            "bastava um id para baixar a fatura de outra organização. Relatado\n"
            "por @marcos em 2026-09-11 e confirmado pelo teste de regressão\n"
            "adicionado aqui.\n"
            "\n"
            "## Como\n"
            "\n"
            "- Troca `findByPk(id)` por um `findOne` restrito por `id` e\n"
            "  `organisationId`.\n"
            "- Redireciona para `signedPdfUrl()` para que a URL do object storage\n"
            "  carregue expiração e não seja adivinhável.\n"
            "- Adiciona um teste de 404 entre organizações e um de 302 no caminho\n"
            "  do dono.\n"
            "\n"
            "## Notas para quem revisa\n"
            "\n"
            "A renomeação de `pdfUrl()` para `signedPdfUrl()` muda o alvo do\n"
            "redirecionamento, não só a consulta. Confirme que nenhum cliente\n"
            "guarda a URL resolvida além do TTL. O header de cache está sendo\n"
            "tratado em uma mudança separada."
        ),
    },
    "pt_pt": {
        "title": "Express — download de fatura vaza entre organizações",
        "description": (
            "Um IDOR: a rota de download procurava a fatura apenas pela chave "
            "primária, por isso qualquer utilizador autenticado conseguia "
            "descarregar a fatura de outra organização."
        ),
        "commit_message": (
            "fix: restringir o download de faturas à organização do requerente\n"
            "\n"
            "`GET /invoices/:id/download` resolvia a fatura com `findByPk`, por\n"
            "isso a linha era devolvida independentemente do dono e qualquer\n"
            "utilizador autenticado conseguia descarregar a fatura de outra\n"
            "organização adivinhando o id.\n"
            "\n"
            "Resolve a fatura com um `where` composto por id e organisationId, e\n"
            "redireciona para o url assinado em vez do url simples. Relatado por\n"
            "@marcos em 2026-09-11."
        ),
        "review": (
            "## Resumo\n"
            "\n"
            "Correção certa para o problema relatado: a verificação de posse\n"
            "passou a estar na própria consulta, e devolver 404 em vez de 403\n"
            "evita confirmar que um id de fatura existe. Dois pontos de\n"
            "continuidade.\n"
            "\n"
            "### 1. O redirecionamento é cacheável\n"
            "\n"
            "`res.redirect()` emite um 302 sem `Cache-Control`. O url assinado é\n"
            "estável durante todo o TTL, por isso um proxy partilhado pode\n"
            "entregar o mesmo URL a um requerente posterior — o que reabre o\n"
            "vazamento que a consulta acabou de fechar. Envie\n"
            "`Cache-Control: private, no-store` nesta rota.\n"
            "\n"
            "### 2. `req.user` é acedido sem verificação\n"
            "\n"
            "Se o middleware de autenticação for algum dia retirado desta rota,\n"
            "`req.user.organisationId` lança exceção e o cliente recebe um 500\n"
            "com stack trace em vez de um 401. Nada na suíte cobre um pedido não\n"
            "autenticado a este endpoint.\n"
            "\n"
            "### Pontos positivos\n"
            "\n"
            "- 404 em vez de 403 é a escolha certa para um recurso que não é seu.\n"
            "- O teste de regressão verifica o caminho entre organizações\n"
            "  diretamente, não um substituto dele."
        ),
        "linter": {
            "errors": [
                "src/routes/invoices.ts:9 — 'req.user' acedido sem verificação "
                "de nulo (regra: no-unchecked-session)."
            ],
            "warnings": [
                "tests/invoices.test.ts:50 — nome do teste excede 60 caracteres "
                "(regra: max-test-name-length)."
            ],
        },
        "pr_description": (
            "## O que\n"
            "\n"
            "Restringe o endpoint de download de faturas à organização do\n"
            "requerente.\n"
            "\n"
            "## Porquê\n"
            "\n"
            "`GET /invoices/:id/download` resolvia a fatura com `findByPk`. A\n"
            "linha era devolvida a qualquer requerente autenticado, por isso\n"
            "bastava um id para descarregar a fatura de outra organização.\n"
            "Relatado por @marcos em 2026-09-11 e confirmado pelo teste de\n"
            "regressão acrescentado aqui.\n"
            "\n"
            "## Como\n"
            "\n"
            "- Troca `findByPk(id)` por um `findOne` restrito por `id` e\n"
            "  `organisationId`.\n"
            "- Redireciona para `signedPdfUrl()` para que o URL do object storage\n"
            "  traga expiração e não seja adivinhável.\n"
            "- Acrescenta um teste de 404 entre organizações e um de 302 no\n"
            "  caminho do dono.\n"
            "\n"
            "## Notas para quem revê\n"
            "\n"
            "A renomeação de `pdfUrl()` para `signedPdfUrl()` muda o alvo do\n"
            "redirecionamento, não só a consulta. Confirme que nenhum cliente\n"
            "guarda o URL resolvido para além do TTL. O header de cache está a\n"
            "ser tratado numa alteração separada."
        ),
    },
    "es_es": {
        "title": "Express — la descarga de facturas se filtra entre organizaciones",
        "description": (
            "Un IDOR: la ruta de descarga buscaba la factura solo por clave "
            "primaria, así que cualquier usuario autenticado podía descargar la "
            "factura de otra organización."
        ),
        "commit_message": (
            "fix: acotar la descarga de facturas a la organización del solicitante\n"
            "\n"
            "`GET /invoices/:id/download` resolvía la factura con `findByPk`, así\n"
            "que la fila se devolvía sin importar quién fuera el dueño y\n"
            "cualquier usuario autenticado podía descargar la factura de otra\n"
            "organización adivinando el id.\n"
            "\n"
            "Resuelve la factura con un `where` compuesto por id y\n"
            "organisationId, y redirige a la url firmada en lugar de la url\n"
            "simple. Reportado por @marcos el 2026-09-11."
        ),
        "review": (
            "## Resumen\n"
            "\n"
            "Corrección correcta para el problema reportado: la comprobación de\n"
            "propiedad ahora está en la propia consulta, y devolver 404 en vez de\n"
            "403 evita confirmar que un id de factura existe. Dos continuaciones.\n"
            "\n"
            "### 1. La redirección es cacheable\n"
            "\n"
            "`res.redirect()` emite un 302 sin `Cache-Control`. La url firmada es\n"
            "estable durante todo el TTL, así que un proxy compartido puede\n"
            "entregar la misma URL a un solicitante posterior — lo que reabre la\n"
            "fuga que la consulta acaba de cerrar. Envía\n"
            "`Cache-Control: private, no-store` en esta ruta.\n"
            "\n"
            "### 2. Se accede a `req.user` sin comprobación\n"
            "\n"
            "Si algún día se desengancha el middleware de autenticación de esta\n"
            "ruta, `req.user.organisationId` lanza una excepción y el cliente\n"
            "recibe un 500 con stack trace en lugar de un 401. Nada en la suite\n"
            "cubre una petición sin autenticar a este endpoint.\n"
            "\n"
            "### Puntos positivos\n"
            "\n"
            "- 404 en vez de 403 es la decisión correcta para un recurso que no es\n"
            "  tuyo.\n"
            "- La prueba de regresión comprueba el camino entre organizaciones\n"
            "  directamente, no un sucedáneo."
        ),
        "linter": {
            "errors": [
                "src/routes/invoices.ts:9 — se accede a 'req.user' sin comprobar "
                "si es nulo (regla: no-unchecked-session)."
            ],
            "warnings": [
                "tests/invoices.test.ts:50 — el nombre de la prueba supera los 60 "
                "caracteres (regla: max-test-name-length)."
            ],
        },
        "pr_description": (
            "## Qué\n"
            "\n"
            "Acota el endpoint de descarga de facturas a la organización del\n"
            "solicitante.\n"
            "\n"
            "## Por qué\n"
            "\n"
            "`GET /invoices/:id/download` resolvía la factura con `findByPk`. La\n"
            "fila se devolvía a cualquier solicitante autenticado, así que\n"
            "bastaba un id para descargar la factura de otra organización.\n"
            "Reportado por @marcos el 2026-09-11 y confirmado por la prueba de\n"
            "regresión añadida aquí.\n"
            "\n"
            "## Cómo\n"
            "\n"
            "- Sustituye `findByPk(id)` por un `findOne` acotado por `id` y\n"
            "  `organisationId`.\n"
            "- Redirige a `signedPdfUrl()` para que la URL del almacenamiento de\n"
            "  objetos lleve caducidad y no sea adivinable.\n"
            "- Añade una prueba de 404 entre organizaciones y una de 302 en el\n"
            "  camino del dueño.\n"
            "\n"
            "## Notas para quien revisa\n"
            "\n"
            "El renombrado de `pdfUrl()` a `signedPdfUrl()` cambia el destino de\n"
            "la redirección, no solo la consulta. Confirma que ningún cliente\n"
            "guarde la URL resuelta más allá de su TTL. La cabecera de caché se\n"
            "está tratando en un cambio aparte."
        ),
    },
    "fr_fr": {
        "title": "Express — le téléchargement de factures fuit entre organisations",
        "description": (
            "Un IDOR : la route de téléchargement cherchait la facture par clé "
            "primaire seule, donc tout utilisateur authentifié pouvait récupérer "
            "la facture d'une autre organisation."
        ),
        "commit_message": (
            "fix: restreindre le téléchargement des factures à l'organisation de l'appelant\n"
            "\n"
            "`GET /invoices/:id/download` résolvait la facture avec `findByPk`,\n"
            "donc la ligne était renvoyée quel qu'en soit le propriétaire et tout\n"
            "utilisateur authentifié pouvait télécharger la facture d'une autre\n"
            "organisation en devinant l'id.\n"
            "\n"
            "Résout la facture avec un `where` composé sur id et organisationId,\n"
            "et redirige vers l'url signée plutôt que l'url simple. Signalé par\n"
            "@marcos le 2026-09-11."
        ),
        "review": (
            "## Résumé\n"
            "\n"
            "Correctif juste pour le problème signalé : la vérification de\n"
            "propriété est désormais dans la requête elle-même, et renvoyer 404\n"
            "plutôt que 403 évite de confirmer qu'un id de facture existe. Deux\n"
            "suites à donner.\n"
            "\n"
            "### 1. La redirection est cachable\n"
            "\n"
            "`res.redirect()` émet un 302 sans `Cache-Control`. L'url signée est\n"
            "stable pendant toute la durée du TTL, donc un proxy partagé peut\n"
            "livrer la même URL à un demandeur ultérieur — ce qui rouvre la fuite\n"
            "que la requête vient de fermer. Envoyez\n"
            "`Cache-Control: private, no-store` sur cette route.\n"
            "\n"
            "### 2. `req.user` est déréférencé sans garde\n"
            "\n"
            "Si le middleware d'authentification est un jour détaché de cette\n"
            "route, `req.user.organisationId` lève une exception et le client\n"
            "reçoit un 500 avec une stack trace au lieu d'un 401. Rien dans la\n"
            "suite ne couvre une requête non authentifiée sur ce point d'entrée.\n"
            "\n"
            "### Points positifs\n"
            "\n"
            "- 404 plutôt que 403 est le bon choix pour une ressource qui n'est pas\n"
            "  la vôtre.\n"
            "- Le test de non-régression vérifie le chemin inter-organisations\n"
            "  directement, pas un substitut."
        ),
        "linter": {
            "errors": [
                "src/routes/invoices.ts:9 — 'req.user' déréférencé sans "
                "vérification de nullité (règle : no-unchecked-session)."
            ],
            "warnings": [
                "tests/invoices.test.ts:50 — le nom du test dépasse 60 caractères "
                "(règle : max-test-name-length)."
            ],
        },
        "pr_description": (
            "## Quoi\n"
            "\n"
            "Restreint le point d'entrée de téléchargement des factures à\n"
            "l'organisation de l'appelant.\n"
            "\n"
            "## Pourquoi\n"
            "\n"
            "`GET /invoices/:id/download` résolvait la facture avec `findByPk`.\n"
            "La ligne était renvoyée à tout appelant authentifié, donc un id\n"
            "suffisait pour télécharger la facture d'une autre organisation.\n"
            "Signalé par @marcos le 2026-09-11 et confirmé par le test de\n"
            "non-régression ajouté ici.\n"
            "\n"
            "## Comment\n"
            "\n"
            "- Remplace `findByPk(id)` par un `findOne` restreint sur `id` et\n"
            "  `organisationId`.\n"
            "- Redirige vers `signedPdfUrl()` pour que l'URL du stockage objet\n"
            "  porte une expiration et ne soit pas devinable.\n"
            "- Ajoute un test 404 inter-organisations et un test 302 sur le\n"
            "  chemin du propriétaire.\n"
            "\n"
            "## Notes pour la relecture\n"
            "\n"
            "Le renommage de `pdfUrl()` en `signedPdfUrl()` change la cible de la\n"
            "redirection, pas seulement la requête. Confirmez qu'aucun client ne\n"
            "conserve l'URL résolue au-delà de son TTL. L'en-tête de cache est\n"
            "traité dans une modification séparée."
        ),
    },
}
