# Plano de Execução — Documentação da Mudança de Semântica de GITPR_SKIP_UPDATE_CHECK

**Data:** 2026-11-09  
**Branch:** develop_natan  
**Task:** document_gitpr_skip_update_check_migration_note  

---

## 1. Objetivo

Documentar formalmente a mudança semântica de `GITPR_SKIP_UPDATE_CHECK` introduzida na versão 1.4.3 como uma nota de migração nos documentos técnicos de referência (`docs/auto-update.*.md`) e tutoriais (`docs/tutorial/install-from-source.*.md`) em todos os 5 idiomas suportados (EN, PT-BR, PT-PT, ES-ES, FR-FR), além de formalizar o termo ubíquo correspondente em `CONTEXT.md`.

---

## 2. Decisões Consolidadas

1. **Locais de Documentação**:
   - `docs/auto-update.*.md`: Adicionar a subseção `### Escape Switch for Local Development (GITPR_SKIP_UPDATE_CHECK)` com callout `> [!WARNING]` de Nota de Migração explicando o parser estrito e o impacto em automações.
   - `docs/tutorial/install-from-source.*.md`: Na Seção 5, adicionar callout `> [!WARNING]` detalhando a quebra semântica de automações legadas que definiam `=false` ou `=0` esperando silenciar a checagem.
2. **Cobertura de Internacionalização**:
   - Atualização completa em 5 idiomas: Inglês, Português (Brasil), Português (Portugal), Espanhol e Francês.
3. **Glossário (`CONTEXT.md`)**:
   - Formalização do termo `Update check switch` documentando a semântica booleana estrita e termos a evitar.

---

## 3. Detalhamento das Alterações

### 3.1. `CONTEXT.md`
Adicionar logo abaixo do termo `Update check`:
```markdown
**Update check switch**:
The environment switch (`GITPR_SKIP_UPDATE_CHECK`) that mutes the update check
during local checkout development and offline automation. Parsed strictly as a
boolean, only explicit truthy values (`1`, `true`, `yes`, `on`, `y`) disable the
check, while falsey values such as `0` or `false` leave it enabled.
_Avoid_: skip flag, update bypass, disable check, bypass switch
```

### 3.2. `docs/auto-update.*.md` (5 arquivos)
Adicionar na Seção 2 a subseção dedicada à chave de escape e o alerta de migração:
- **EN (`docs/auto-update.md`)**:
  ```markdown
  ### Escape Switch for Local Development (`GITPR_SKIP_UPDATE_CHECK`)

  For local checkout development and offline test environments, GitPR supports muting the update check via `GITPR_SKIP_UPDATE_CHECK=1` in `~/.gitpr/.env` or the execution shell.

  > [!WARNING]
  > **Migration Note (Strict Boolean Parsing):**  
  > Since version 1.4.3, `GITPR_SKIP_UPDATE_CHECK` is evaluated by a strict boolean parser: only explicit truthy values (`1`, `true`, `yes`, `on`, `y`, case-insensitive) disable the update check.  
  > In earlier versions, any non-empty string in the environment was treated as truthy by variable presence checks. Legacy automations or scripts that configured `GITPR_SKIP_UPDATE_CHECK=false` or `=0` expecting to mute the check now leave the check **enabled**, causing the update gate to run and potentially block execution. To mute the check, explicitly set `GITPR_SKIP_UPDATE_CHECK=1` or `true`.
  ```
- **PT-BR (`docs/auto-update.pt_br.md`)**:
  ```markdown
  ### Chave de Escape para Desenvolvimento Local (`GITPR_SKIP_UPDATE_CHECK`)

  Para desenvolvimento em checkout local e ambientes de teste offline, o GitPR permite silenciar a checagem de atualização via `GITPR_SKIP_UPDATE_CHECK=1` no arquivo `~/.gitpr/.env` ou no shell.

  > [!WARNING]
  > **Nota de Migração (Parser Booleano Estrito):**  
  > Desde a versão 1.4.3, `GITPR_SKIP_UPDATE_CHECK` é interpretado por um parser booleano estrito: somente valores explicitamente verdadeiros (`1`, `true`, `yes`, `on`, `y`, case-insensitive) desativam a verificação de versão.  
  > Em versões anteriores, qualquer string não-vazia no ambiente era tratada como verdadeira por verificação de presença da variável. Automações ou scripts legados que definiam `GITPR_SKIP_UPDATE_CHECK=false` ou `=0` esperando silenciar a checagem agora deixam a checagem **ativa**, fazendo o portão de atualização rodar e potencialmente bloquear a execução. Para silenciar a checagem, defina explicitamente `GITPR_SKIP_UPDATE_CHECK=1` ou `true`.
  ```
- **PT-PT (`docs/auto-update.pt_pt.md`)**:
  ```markdown
  ### Chave de Escape para Desenvolvimento Local (`GITPR_SKIP_UPDATE_CHECK`)

  Para desenvolvimento em checkout local e ambientes de teste offline, o GitPR permite silenciar a verificação de atualização via `GITPR_SKIP_UPDATE_CHECK=1` no ficheiro `~/.gitpr/.env` ou no terminal.

  > [!WARNING]
  > **Nota de Migração (Analisador Booleano Estrito):**  
  > Desde a versão 1.4.3, `GITPR_SKIP_UPDATE_CHECK` é interpretado por um analisador booleano estrito: apenas valores explicitamente verdadeiros (`1`, `true`, `yes`, `on`, `y`, insensíveis a maiúsculas/minúsculas) desativam a verificação de versão.  
  > Em versões anteriores, qualquer cadeia de caracteres não-vazia no ambiente era considerada verdadeira pela verificação de presença da variável. Automações ou scripts legados que definiam `GITPR_SKIP_UPDATE_CHECK=false` ou `=0` esperando silenciar a verificação deixam agora a verificação **ativa**, fazendo o portão de versão correr e potencialmente bloquear a execução. Para silenciar a verificação, defina explicitamente `GITPR_SKIP_UPDATE_CHECK=1` ou `true`.
  ```
- **ES-ES (`docs/auto-update.es_es.md`)**:
  ```markdown
  ### Interruptor de Escape para Desarrollo Local (`GITPR_SKIP_UPDATE_CHECK`)

  Para desarrollo en checkout local y entornos de prueba offline, GitPR permite silenciar la comprobación de actualización mediante `GITPR_SKIP_UPDATE_CHECK=1` en el archivo `~/.gitpr/.env` o en la consola.

  > [!WARNING]
  > **Nota de Migración (Analizador Booleano Estricto):**  
  > Desde la versión 1.4.3, `GITPR_SKIP_UPDATE_CHECK` se evalúa mediante un analizador booleano estricto: solo los valores explícitamente verdaderos (`1`, `true`, `yes`, `on`, `y`, sin distinción entre mayúsculas y minúsculas) desactivan la comprobación de actualización.  
  > En versiones anteriores, cualquier cadena no vacía en el entorno se consideraba verdadera por simple comprobación de presencia de la variable. Las automatizaciones o scripts heredados que configuraban `GITPR_SKIP_UPDATE_CHECK=false` o `=0` esperando silenciar la comprobación ahora la dejan **activa**, provocando que el portero de actualización se ejecute y potencialmente bloquee la ejecución. Para silenciar la comprobación, configure explícitamente `GITPR_SKIP_UPDATE_CHECK=1` o `true`.
  ```
- **FR-FR (`docs/auto-update.fr_fr.md`)**:
  ```markdown
  ### Commutateur d'Échappement pour le Développement Local (`GITPR_SKIP_UPDATE_CHECK`)

  Pour le développement sur un checkout local et les environnements de test hors ligne, GitPR permet de désactiver la vérification des mises à jour via `GITPR_SKIP_UPDATE_CHECK=1` dans le fichier `~/.gitpr/.env` ou dans le terminal.

  > [!WARNING]
  > **Note de Migration (Analyseur Booléen Strict) :**  
  > Depuis la version 1.4.3, `GITPR_SKIP_UPDATE_CHECK` est interprété par un analyseur booléen strict : seules les valeurs explicitement vraies (`1`, `true`, `yes`, `on`, `y`, insensibles à la casse) désactivent la vérification de mise à jour.  
  > Dans les versions antérieures, toute chaîne non vide dans l'environnement était traitée comme vraie par une simple vérification de présence de variable. Les automatisations ou scripts existants qui définissaient `GITPR_SKIP_UPDATE_CHECK=false` ou `=0` en espérant désactiver la vérification laissent désormais la vérification **activée**, ce qui fait fonctionner le portail de mise à jour et peut bloquer l'exécution. Pour désactiver la vérification, définissez explicitement `GITPR_SKIP_UPDATE_CHECK=1` ou `true`.
  ```

### 3.3. `docs/tutorial/install-from-source.*.md` (5 arquivos)
Na Seção 5, incluir após os 4 detalhes o bloco de nota de migração:
- **EN**:
  ```markdown
  > [!WARNING]
  > **Migration Note (Strict Boolean Parsing):**  
  > Since GitPR 1.4.3, `GITPR_SKIP_UPDATE_CHECK` is evaluated strictly. In earlier versions, any non-empty string in the environment was treated as truthy by variable presence checks. Automations or scripts that previously set `GITPR_SKIP_UPDATE_CHECK=false` or `0` expecting to mute the check now leave it **enabled**, causing the update gate to execute. Always use `1` or `true` if you intend to mute the check.
  ```
- **PT-BR**:
  ```markdown
  > [!WARNING]
  > **Nota de Migração (Parser Booleano Estrito):**  
  > Desde o GitPR 1.4.3, `GITPR_SKIP_UPDATE_CHECK` é interpretado de forma estrita. Em versões anteriores, qualquer string não-vazia no ambiente era tratada como verdadeira por verificação de presença da variável. Automações ou scripts que anteriormente definiam `GITPR_SKIP_UPDATE_CHECK=false` ou `0` esperando silenciar a checagem agora a deixam **ativa**, fazendo o portão de atualização rodar. Use sempre `1` ou `true` se a sua intenção for desativar a verificação.
  ```
- **PT-PT**:
  ```markdown
  > [!WARNING]
  > **Nota de Migração (Analisador Booleano Estrito):**  
  > Desde o GitPR 1.4.3, `GITPR_SKIP_UPDATE_CHECK` é interpretado de forma estrita. Em versões anteriores, qualquer cadeia de caracteres não-vazia no ambiente era considerada verdadeira pela verificação de presença da variável. Automações ou scripts que anteriormente definiam `GITPR_SKIP_UPDATE_CHECK=false` ou `0` esperando silenciar a verificação deixam-na agora **ativa**, fazendo o portão de versão correr. Utilize sempre `1` ou `true` se a sua intenção for desativar a verificação.
  ```
- **ES-ES**:
  ```markdown
  > [!WARNING]
  > **Nota de Migración (Analizador Booleano Estricto):**  
  > Desde GitPR 1.4.3, `GITPR_SKIP_UPDATE_CHECK` se evalúa estrictamente. En versiones anteriores, cualquier cadena no vacía en el entorno se trataba como verdadera mediante comprobación de presencia de variable. Las automatizaciones o scripts que anteriormente configuraban `GITPR_SKIP_UPDATE_CHECK=false` o `0` esperando silenciar la comprobación ahora la dejan **activa**, provocando que el portero de actualización se ejecute. Utilice siempre `1` o `true` si su intención es silenciar la comprobación.
  ```
- **FR-FR**:
  ```markdown
  > [!WARNING]
  > **Note de Migration (Analyseur Booléen Strict) :**  
  > Depuis GitPR 1.4.3, `GITPR_SKIP_UPDATE_CHECK` est interprété de manière stricte. Dans les versions antérieures, toute chaîne non vide dans l'environnement était traitée comme vraie par une simple vérification de présence de variable. Les automatisations ou scripts qui définissaient auparavant `GITPR_SKIP_UPDATE_CHECK=false` ou `0` en espérant désactiver la vérification la laissent désormais **activée**, ce qui fait fonctionner le portail de mise à jour. Utilisez toujours `1` ou `true` si votre intention est de désactiver la vérification.
  ```

---

## 4. Verificação

1. **Validação de Links e Paridade**:
   - Garantir que todos os links e nomes de seções correspondam entre os 5 idiomas.
2. **Testes Automatizados do Updater**:
   - Os testes existentes em `tests/test_updater.py` já cobrem exaustivamente os valores aceitos (`1`, `true`, `yes`, `on`, `y`) e rejeitados (`0`, `false`, `no`, `off`, `n`, `banana`, etc.).
3. **Revisão de Conteúdo**:
   - Verificar precisão terminológica com base no `CONTEXT.md`.
