"""Tour scenario: a Laravel profile form that rejects the user's own email.

The diff is repository content, so it stays in English in every language — the
same way the real tool answers in English about English code. Only the prose
the tour narrates is translated. A language missing from ``TEXT`` falls back to
English, so the scenario is usable while a translation is still being written.
"""

NAME = "laravel-bug-fix"

DIFF = r"""diff --git a/app/Http/Requests/UpdateProfileRequest.php b/app/Http/Requests/UpdateProfileRequest.php
index 3f1a2c7..b8e4d90 100644
--- a/app/Http/Requests/UpdateProfileRequest.php
+++ b/app/Http/Requests/UpdateProfileRequest.php
@@ -1,6 +1,7 @@
 <?php

 namespace App\Http\Requests;

 use Illuminate\Foundation\Http\FormRequest;
+use Illuminate\Validation\Rule;

@@ -12,8 +13,12 @@ class UpdateProfileRequest extends FormRequest
     public function rules(): array
     {
         return [
             'name'  => ['required', 'string', 'max:120'],
-            'email' => ['required', 'email', 'unique:users,email'],
+            'email' => [
+                'required',
+                'email',
+                Rule::unique('users', 'email')->ignore($this->user()->id),
+            ],
             'bio'   => ['nullable', 'string', 'max:500'],
         ];
     }
diff --git a/tests/Feature/ProfileUpdateTest.php b/tests/Feature/ProfileUpdateTest.php
index 5d0c118..a7f3b62 100644
--- a/tests/Feature/ProfileUpdateTest.php
+++ b/tests/Feature/ProfileUpdateTest.php
@@ -31,6 +31,18 @@ public function test_email_must_be_unique(): void
         $response->assertSessionHasErrors('email');
     }

+    public function test_user_can_keep_their_own_email(): void
+    {
+        $user = User::factory()->create(['email' => 'ana@example.com']);
+
+        $response = $this->actingAs($user)->patch('/profile', [
+            'name'  => 'Ana Souza',
+            'email' => 'ana@example.com',
+        ]);
+
+        $response->assertOk();
+    }
+
     public function test_bio_is_optional(): void
     {
         $response = $this->actingAs(User::factory()->create())->patch('/profile', [
"""

TEXT = {
    "en": {
        "title": "Laravel — profile update rejects your own email",
        "description": (
            "A form request reused the store-time uniqueness rule, so saving "
            "your profile without changing the email failed validation."
        ),
        "commit_message": (
            "fix: allow a user to keep their own email when updating the profile\n"
            "\n"
            "The profile form reused the store-time rule, so `unique:users,email`\n"
            "matched the user's own row and every save without an email change\n"
            "failed with \"The email has already been taken\".\n"
            "\n"
            "Scope the rule to the authenticated user with\n"
            "Rule::unique()->ignore() and cover the path with a regression test."
        ),
        "review": (
            "## Summary\n"
            "\n"
            "The fix is correct and the regression test reproduces the reported\n"
            "path. Two things are worth handling before this merges.\n"
            "\n"
            "### 1. The controller still writes unvalidated input\n"
            "\n"
            "`ProfileController::update()` calls `$user->update($request->all())`,\n"
            "so the rules you just tightened are not what reaches the model. Any\n"
            "extra key in the request body is persisted. Switch to\n"
            "`$request->validated()`.\n"
            "\n"
            "### 2. The `unique` rule is never asserted against another user\n"
            "\n"
            "`test_email_must_be_unique` only covers the unauthenticated failure\n"
            "branch. Add a case where user B tries to take user A's address, so a\n"
            "future mistake in the `ignore()` argument cannot quietly disable the\n"
            "rule altogether.\n"
            "\n"
            "### Positive\n"
            "\n"
            "- The import keeps PSR-12 alphabetical ordering.\n"
            "- The test name states the behaviour rather than the implementation."
        ),
        "linter": {
            "errors": [],
            "warnings": [
                "app/Http/Requests/UpdateProfileRequest.php:13 — method 'rules' "
                "declares no return type (PSR-12)."
            ],
        },
        "pr_description": (
            "## What\n"
            "\n"
            "Fixes the profile update form rejecting a user's own email address.\n"
            "\n"
            "## Why\n"
            "\n"
            "`UpdateProfileRequest` reused the store-time `unique:users,email` rule.\n"
            "On update the authenticated user's row is already in the table, so any\n"
            "save that did not change the email failed with \"The email has already\n"
            "been taken\". Reported in #482.\n"
            "\n"
            "## How\n"
            "\n"
            "- Scope the rule to the authenticated user with\n"
            "  `Rule::unique(...)->ignore($this->user()->id)`.\n"
            "- Import `Illuminate\\Validation\\Rule` explicitly.\n"
            "- Add `test_user_can_keep_their_own_email` so the regression cannot\n"
            "  come back.\n"
            "\n"
            "## Notes for the reviewer\n"
            "\n"
            "`ProfileController::update()` still passes `$request->all()` to the\n"
            "model. That is out of scope here but is worth a separate change."
        ),
    },
    "pt_br": {
        "title": "Laravel — atualização de perfil rejeita o próprio e-mail",
        "description": (
            "Um form request reaproveitou a regra de unicidade do cadastro, então "
            "salvar o perfil sem trocar o e-mail falhava na validação."
        ),
        "commit_message": (
            "fix: permitir que o usuário mantenha o próprio e-mail ao atualizar o perfil\n"
            "\n"
            "O formulário de perfil reaproveitou a regra do cadastro, então\n"
            "`unique:users,email` encontrava a própria linha do usuário e todo\n"
            "salvamento sem troca de e-mail falhava com \"The email has already\n"
            "been taken\".\n"
            "\n"
            "Restringe a regra ao usuário autenticado com\n"
            "Rule::unique()->ignore() e cobre o caminho com um teste de regressão."
        ),
        "review": (
            "## Resumo\n"
            "\n"
            "A correção está certa e o teste de regressão reproduz o caminho\n"
            "relatado. Dois pontos merecem atenção antes do merge.\n"
            "\n"
            "### 1. O controller continua gravando entrada não validada\n"
            "\n"
            "`ProfileController::update()` chama `$user->update($request->all())`,\n"
            "então as regras que você acabou de endurecer não são o que chega ao\n"
            "model. Qualquer chave extra no corpo da requisição é persistida. Troque\n"
            "por `$request->validated()`.\n"
            "\n"
            "### 2. A regra `unique` nunca é verificada contra outro usuário\n"
            "\n"
            "`test_email_must_be_unique` cobre apenas o ramo de falha sem\n"
            "autenticação. Adicione um caso em que o usuário B tenta assumir o\n"
            "endereço do usuário A, para que um erro futuro no argumento do\n"
            "`ignore()` não desative a regra em silêncio.\n"
            "\n"
            "### Pontos positivos\n"
            "\n"
            "- O import mantém a ordem alfabética da PSR-12.\n"
            "- O nome do teste descreve o comportamento, não a implementação."
        ),
        "linter": {
            "errors": [],
            "warnings": [
                "app/Http/Requests/UpdateProfileRequest.php:13 — o método 'rules' "
                "não declara tipo de retorno (PSR-12)."
            ],
        },
        "pr_description": (
            "## O que\n"
            "\n"
            "Corrige o formulário de atualização de perfil, que rejeitava o próprio\n"
            "e-mail do usuário.\n"
            "\n"
            "## Por quê\n"
            "\n"
            "`UpdateProfileRequest` reaproveitou a regra `unique:users,email` do\n"
            "cadastro. Na atualização, a linha do usuário autenticado já está na\n"
            "tabela, então todo salvamento sem troca de e-mail falhava com \"The\n"
            "email has already been taken\". Relatado em #482.\n"
            "\n"
            "## Como\n"
            "\n"
            "- Restringe a regra ao usuário autenticado com\n"
            "  `Rule::unique(...)->ignore($this->user()->id)`.\n"
            "- Importa `Illuminate\\Validation\\Rule` explicitamente.\n"
            "- Adiciona `test_user_can_keep_their_own_email` para impedir a volta\n"
            "  da regressão.\n"
            "\n"
            "## Notas para quem revisa\n"
            "\n"
            "`ProfileController::update()` ainda passa `$request->all()` para o\n"
            "model. Está fora do escopo deste PR, mas merece uma mudança separada."
        ),
    },
    "pt_pt": {
        "title": "Laravel — atualização de perfil rejeita o próprio e-mail",
        "description": (
            "Um form request reaproveitou a regra de unicidade do registo, por "
            "isso guardar o perfil sem alterar o e-mail falhava na validação."
        ),
        "commit_message": (
            "fix: permitir que o utilizador mantenha o próprio e-mail ao atualizar o perfil\n"
            "\n"
            "O formulário de perfil reaproveitou a regra do registo, por isso\n"
            "`unique:users,email` encontrava a própria linha do utilizador e todas\n"
            "as gravações sem alteração de e-mail falhavam com \"The email has\n"
            "already been taken\".\n"
            "\n"
            "Restringe a regra ao utilizador autenticado com\n"
            "Rule::unique()->ignore() e cobre o caminho com um teste de regressão."
        ),
        "review": (
            "## Resumo\n"
            "\n"
            "A correção está certa e o teste de regressão reproduz o caminho\n"
            "relatado. Há dois pontos a resolver antes do merge.\n"
            "\n"
            "### 1. O controller continua a gravar entrada não validada\n"
            "\n"
            "`ProfileController::update()` chama `$user->update($request->all())`,\n"
            "por isso as regras que acabou de endurecer não são as que chegam ao\n"
            "model. Qualquer chave extra no corpo do pedido é persistida. Troque\n"
            "por `$request->validated()`.\n"
            "\n"
            "### 2. A regra `unique` nunca é verificada contra outro utilizador\n"
            "\n"
            "`test_email_must_be_unique` cobre apenas o ramo de falha sem\n"
            "autenticação. Acrescente um caso em que o utilizador B tenta ficar com\n"
            "o endereço do utilizador A, para que um erro futuro no argumento do\n"
            "`ignore()` não desative a regra em silêncio.\n"
            "\n"
            "### Pontos positivos\n"
            "\n"
            "- O import mantém a ordem alfabética da PSR-12.\n"
            "- O nome do teste descreve o comportamento, não a implementação."
        ),
        "linter": {
            "errors": [],
            "warnings": [
                "app/Http/Requests/UpdateProfileRequest.php:13 — o método 'rules' "
                "não declara tipo de retorno (PSR-12)."
            ],
        },
        "pr_description": (
            "## O que\n"
            "\n"
            "Corrige o formulário de atualização de perfil, que rejeitava o próprio\n"
            "e-mail do utilizador.\n"
            "\n"
            "## Porquê\n"
            "\n"
            "`UpdateProfileRequest` reaproveitou a regra `unique:users,email` do\n"
            "registo. Na atualização, a linha do utilizador autenticado já está na\n"
            "tabela, por isso todas as gravações sem alteração de e-mail falhavam\n"
            "com \"The email has already been taken\". Relatado em #482.\n"
            "\n"
            "## Como\n"
            "\n"
            "- Restringe a regra ao utilizador autenticado com\n"
            "  `Rule::unique(...)->ignore($this->user()->id)`.\n"
            "- Importa `Illuminate\\Validation\\Rule` explicitamente.\n"
            "- Acrescenta `test_user_can_keep_their_own_email` para impedir o\n"
            "  regresso da regressão.\n"
            "\n"
            "## Notas para quem revê\n"
            "\n"
            "`ProfileController::update()` ainda passa `$request->all()` ao model.\n"
            "Está fora do âmbito deste PR, mas merece uma alteração separada."
        ),
    },
    "es_es": {
        "title": "Laravel — la actualización de perfil rechaza tu propio correo",
        "description": (
            "Un form request reutilizó la regla de unicidad del registro, así que "
            "guardar el perfil sin cambiar el correo fallaba en la validación."
        ),
        "commit_message": (
            "fix: permitir que el usuario conserve su propio correo al actualizar el perfil\n"
            "\n"
            "El formulario de perfil reutilizó la regla del registro, así que\n"
            "`unique:users,email` encontraba la propia fila del usuario y cada\n"
            "guardado sin cambio de correo fallaba con \"The email has already been\n"
            "taken\".\n"
            "\n"
            "Acota la regla al usuario autenticado con\n"
            "Rule::unique()->ignore() y cubre el camino con una prueba de regresión."
        ),
        "review": (
            "## Resumen\n"
            "\n"
            "La corrección es correcta y la prueba de regresión reproduce el camino\n"
            "reportado. Hay dos puntos que conviene resolver antes del merge.\n"
            "\n"
            "### 1. El controlador sigue escribiendo entrada sin validar\n"
            "\n"
            "`ProfileController::update()` llama a `$user->update($request->all())`,\n"
            "así que las reglas que acabas de endurecer no son las que llegan al\n"
            "modelo. Cualquier clave extra en el cuerpo de la petición se persiste.\n"
            "Cambia a `$request->validated()`.\n"
            "\n"
            "### 2. La regla `unique` nunca se comprueba contra otro usuario\n"
            "\n"
            "`test_email_must_be_unique` solo cubre la rama de fallo sin\n"
            "autenticación. Añade un caso en el que el usuario B intenta quedarse\n"
            "con la dirección del usuario A, para que un error futuro en el\n"
            "argumento de `ignore()` no desactive la regla en silencio.\n"
            "\n"
            "### Puntos positivos\n"
            "\n"
            "- El import mantiene el orden alfabético de PSR-12.\n"
            "- El nombre de la prueba describe el comportamiento, no la implementación."
        ),
        "linter": {
            "errors": [],
            "warnings": [
                "app/Http/Requests/UpdateProfileRequest.php:13 — el método 'rules' "
                "no declara tipo de retorno (PSR-12)."
            ],
        },
        "pr_description": (
            "## Qué\n"
            "\n"
            "Corrige el formulario de actualización de perfil, que rechazaba el\n"
            "propio correo del usuario.\n"
            "\n"
            "## Por qué\n"
            "\n"
            "`UpdateProfileRequest` reutilizó la regla `unique:users,email` del\n"
            "registro. En la actualización, la fila del usuario autenticado ya está\n"
            "en la tabla, así que cada guardado sin cambio de correo fallaba con\n"
            "\"The email has already been taken\". Reportado en #482.\n"
            "\n"
            "## Cómo\n"
            "\n"
            "- Acota la regla al usuario autenticado con\n"
            "  `Rule::unique(...)->ignore($this->user()->id)`.\n"
            "- Importa `Illuminate\\Validation\\Rule` de forma explícita.\n"
            "- Añade `test_user_can_keep_their_own_email` para impedir que la\n"
            "  regresión vuelva.\n"
            "\n"
            "## Notas para quien revisa\n"
            "\n"
            "`ProfileController::update()` sigue pasando `$request->all()` al\n"
            "modelo. Queda fuera del alcance de este PR, pero merece un cambio\n"
            "aparte."
        ),
    },
    "fr_fr": {
        "title": "Laravel — la mise à jour du profil rejette votre propre e-mail",
        "description": (
            "Un form request a réutilisé la règle d'unicité de l'inscription, donc "
            "enregistrer le profil sans changer l'e-mail échouait à la validation."
        ),
        "commit_message": (
            "fix: permettre à l'utilisateur de garder son propre e-mail lors de la mise à jour du profil\n"
            "\n"
            "Le formulaire de profil a réutilisé la règle de l'inscription, donc\n"
            "`unique:users,email` trouvait la propre ligne de l'utilisateur et\n"
            "chaque enregistrement sans changement d'e-mail échouait avec \"The\n"
            "email has already been taken\".\n"
            "\n"
            "Restreint la règle à l'utilisateur authentifié avec\n"
            "Rule::unique()->ignore() et couvre le cas par un test de non-régression."
        ),
        "review": (
            "## Résumé\n"
            "\n"
            "Le correctif est juste et le test de non-régression reproduit le cas\n"
            "signalé. Deux points restent à traiter avant la fusion.\n"
            "\n"
            "### 1. Le contrôleur écrit toujours des données non validées\n"
            "\n"
            "`ProfileController::update()` appelle `$user->update($request->all())`,\n"
            "donc les règles que vous venez de durcir ne sont pas celles qui\n"
            "atteignent le modèle. Toute clé supplémentaire dans le corps de la\n"
            "requête est persistée. Passez à `$request->validated()`.\n"
            "\n"
            "### 2. La règle `unique` n'est jamais testée contre un autre utilisateur\n"
            "\n"
            "`test_email_must_be_unique` ne couvre que la branche d'échec sans\n"
            "authentification. Ajoutez un cas où l'utilisateur B tente de prendre\n"
            "l'adresse de l'utilisateur A, pour qu'une erreur future dans\n"
            "l'argument de `ignore()` ne désactive pas la règle en silence.\n"
            "\n"
            "### Points positifs\n"
            "\n"
            "- L'import respecte l'ordre alphabétique de la PSR-12.\n"
            "- Le nom du test décrit le comportement, pas l'implémentation."
        ),
        "linter": {
            "errors": [],
            "warnings": [
                "app/Http/Requests/UpdateProfileRequest.php:13 — la méthode 'rules' "
                "ne déclare pas de type de retour (PSR-12)."
            ],
        },
        "pr_description": (
            "## Quoi\n"
            "\n"
            "Corrige le formulaire de mise à jour du profil, qui rejetait le propre\n"
            "e-mail de l'utilisateur.\n"
            "\n"
            "## Pourquoi\n"
            "\n"
            "`UpdateProfileRequest` a réutilisé la règle `unique:users,email` de\n"
            "l'inscription. Lors de la mise à jour, la ligne de l'utilisateur\n"
            "authentifié est déjà dans la table, donc chaque enregistrement sans\n"
            "changement d'e-mail échouait avec \"The email has already been\n"
            "taken\". Signalé dans #482.\n"
            "\n"
            "## Comment\n"
            "\n"
            "- Restreint la règle à l'utilisateur authentifié avec\n"
            "  `Rule::unique(...)->ignore($this->user()->id)`.\n"
            "- Importe `Illuminate\\Validation\\Rule` explicitement.\n"
            "- Ajoute `test_user_can_keep_their_own_email` pour empêcher le retour\n"
            "  de la régression.\n"
            "\n"
            "## Notes pour la relecture\n"
            "\n"
            "`ProfileController::update()` passe encore `$request->all()` au modèle.\n"
            "Hors périmètre de cette PR, mais cela mérite une modification séparée."
        ),
    },
}
