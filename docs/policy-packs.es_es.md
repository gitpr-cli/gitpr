# Documentación Técnica: Policy Packs (`gitpr policy`)

Un **Policy Pack** es un manifiesto YAML versionable que transporta toda la política de calidad de un equipo — skills de revisión, reglas de linter, overrides de severidad, rutas críticas, pesos de riesgo y las convenciones de PR/commit — en un único archivo que un repositorio puede adoptar, revisar y versionar junto con su propio código. `gitpr policy` registra *cuál* pack sigue el repositorio y es lo único que decide *qué* cambia ese pack.

Hasta ahora cada una de esas superficies se configuraba en otro lugar: `.gitpr/skill/.gitpr.review.md`, `.gitpr/skill/.gitpr.linter.yml`, `.gitpr/skill/gitpr.risk.yml`, `~/.gitpr/.env`. Nada unía el conjunto, así que "seguimos la política de Acme" era una convención, no algo que la herramienta pudiera comprobar. Con un pack, es una línea en un archivo bajo control de versiones.

---

## 1. Visión General

Los Policy Packs actúan en tres superficies:

1. **El grupo `gitpr policy`**: siete comandos para listar, validar, mostrar, adoptar, instalar, crear y abandonar una política. `list`, `validate` y `show` solo leen; `use`, `install`, `init` y `off` escriben y preguntan antes de hacerlo.
2. **Todos los comandos posteriores en el repositorio**: con un pack activo, `gitpr -r`, `gitpr -f`, `gitpr -c`, `gitpr` (descripción de PR), `gitpr -l` y `gitpr risk` se ejecutan bajo él, sin que ninguno gane un argumento nuevo.
3. **`.gitpr/policy.lock.yml`**: el archivo que registra la decisión. Nombra el pack, su versión, su origen y un checksum por pack, para que un compañero obtenga la misma política desde el mismo commit.

### 1.1 Referencia de Comandos

```bash
gitpr policy list                        # Los packs de esta máquina y el que está en vigor
gitpr policy validate gitpr/laravel-quality   # Schema, compatibilidad, skills, reglas, dependencias
gitpr policy show                        # La política efectiva, con el origen de cada valor
gitpr policy use acme/team-policy@1.0.0  # Fija un pack, escribiendo .gitpr/policy.lock.yml
gitpr policy init --stack laravel        # Sugiere y activa el pack oficial de la stack
gitpr policy install ./our-policy        # Copia un directorio local a ~/.gitpr/policies
gitpr policy off                         # Deja de seguir el pack
```

| Comando | Escribe | Descripción |
|---|---|---|
| **`list`** | — | El pack activo (con su grafo de dependencias) y todos los packs encontrados en esta máquina |
| **`validate <ruta\|nombre[@rango]>`** | — | Valida un pack e informa de lo que hace. Salida distinta de cero cuando el pack es inválido, para que el CI pueda bloquear |
| **`show`** | — | La política efectiva en vigor, con la procedencia de cada campo y el orden de precedencia que la produjo |
| **`use <nombre>[@<versión>]`** | `.gitpr/policy.lock.yml` | Fija un pack para este repositorio. Sustituye al pack que estuviera activo |
| **`init [--stack laravel\|vue\|php\|node]`** | `.gitpr/policy.lock.yml` | Detecta la stack a partir del proyecto y activa el pack oficial correspondiente |
| **`install <ruta> [--force]`** | `~/.gitpr/policies/` | Valida un pack en un directorio local y lo copia al almacén de packs del usuario. No hay registry ni descarga |
| **`off`** | elimina `.gitpr/policy.lock.yml` | Deja de seguir el pack. El pack y el archivo de overrides se conservan |

Todos los comandos que escriben aceptan `--yes`, que omite la confirmación pero **no** las comprobaciones que hay detrás. Sin terminal y sin `--yes`, un comando de escritura falla con la instrucción en lugar de bloquearse en un prompt que nadie va a leer — eso es lo que hace que el grupo sea seguro para llamarlo desde un hook o un job de CI que olvidó la flag.

### 1.2 De dónde puede venir un pack

Tres orígenes, buscados en este orden:

| Orden | Origen | Ubicación | `source` en el lockfile |
|---:|---|---|---|
| 1 | El propio repositorio | `<repo>/.gitpr/policies/<nombre>/` | `local_path` |
| 2 | El almacén del usuario | `~/.gitpr/policies/<nombre-aplanado>/` | `installed` |
| 3 | Lo que entrega GitPR | `src/policy_packs/<nombre>/` | `bundled` |

Un pack instalado vive en un directorio **aplanado** — `acme/team-policy` se guarda como `acme__team-policy` — porque el namespace forma parte de la identidad del pack, no del layout del sistema de archivos. Un pack versionado dentro del repositorio se encuentra por ruta, y eso es lo que permite a un equipo adoptar una política que nadie ha instalado.

No se descarga nada. Un pack es texto en disco; la resolución lo lee, calcula su hash y lo compone.

---

## 2. El Manifiesto

Un pack es un directorio con `policy.yml` y los assets que el manifiesto declare:

```
acme__team-policy/
├── policy.yml          # el manifiesto — el único archivo obligatorio
├── linter.yml          # declarado por linter.rules_file
├── README.md           # viaja con él; forma parte del pack, no lo lee nadie
└── CHANGELOG.md
```

### 2.1 Schema

El schema es **cerrado**: una clave desconocida es un error, no un aviso. Una errata como `test:` en lugar de `tests:` tiene que fallar alto, porque la alternativa es una política que silenciosamente no hace nada mientras su nombre sigue apareciendo en la salida.

| Clave | Obligatoria | Tipo | Significado |
|---|---|---|---|
| `schema_version` | ✅ | int | Versión del schema del manifiesto. Actualmente `1` |
| `name` | ✅ | str | `namespace/nombre`. El path traversal se rechaza |
| `version` | ✅ | str | La versión del propio pack |
| `min_gitpr_version` | ✅ | str | Rango `SpecifierSet`, ej.: `">=1.3.0"`. Validado contra el GitPR en ejecución |
| `description` | — | str | Texto libre, mostrado por `policy list` |
| `license` | — | str | Texto libre |
| `authors` | — | list[str] | Texto libre |
| `extends` | — | list | Dependencias: `[{name, version}]`. `version` es un rango |
| `baseline` | — | map | `suppressions`, `accepted_debt` — las decisiones que el pack trae al baseline, solo en memoria |
| `skills` | — | map | `skills.<tipo>.additional_context` — texto anexado al prompt de esa skill |
| `linter` | — | map | `rules_file`, `severity_overrides` |
| `risk` | — | map | `critical_paths`, `test_patterns`, `weights`, `thresholds` |
| `pr` | — | map | `required_sections` |
| `commit` | — | map | `allowed_types` |
| `protected_paths` | — | list[str] | Declarado para el prompt, no lo impone ningún motor |

### 2.2 Un ejemplo completo

```yaml
schema_version: 1
name: acme/team-policy
version: 1.0.0
description: The Acme house rules for PHP services.
min_gitpr_version: ">=1.3.0"
license: MIT
authors:
  - Acme Platform

extends:
  - name: acme/base-policy
    version: ">=1.0.0 <2.0.0"

skills:
  review:
    additional_context: |
      Money is an integer in minor units. A float in a monetary field is a bug
      regardless of how it got there.

linter:
  rules_file: linter.yml
  severity_overrides:
    - rule_name: acme-no-float-money
      level: warning
      reason: the float check is advisory while the migration is in flight

risk:
  critical_paths:
    - app/Services/**
  test_patterns:
    - spec/**
  weights:
    database_migration: 25

pr:
  required_sections:
    - Business impact
    - Rollback plan

commit:
  allowed_types:
    - feat
    - fix
    - chore

baseline:
  suppressions:
    - scope: rule
      rule_id: acme-no-float-money
      reason: The float check is advisory while the migration is in flight.
  accepted_debt:
    - fingerprint: "sha256:9f2c…"
      owner: acme-platform
      reason: Scheduled for the payments rewrite.
      due_date: 2026-12-31

protected_paths:
  - config/**
```

### 2.3 Las secciones

**`skills`** — un bloque por tipo de skill. Los tipos válidos son los que GitPR conoce: `commit`, `pr`, `review`, `filereview`, `blame`, `issue`, `release`, `fix`, `tests`, `explain`, `mentor`. Un tipo desconocido se rechaza en el parsing; un pack no puede inventar una skill, porque nada la leería. El texto se concatena con las contribuciones de los demás packs y se anexa al prompt como instrucciones de sistema, y por eso también entra en la clave de caché — véase la §4.3.

**`linter.rules_file`** — el nombre de un archivo YAML de reglas **dentro del directorio del pack**. Una ruta que escape del directorio se rechaza, así que un pack no puede apuntar a `/etc/passwd` ni a un archivo por encima de sí mismo. Las reglas entran en el catálogo por `name`, con las reglas del propio proyecto venciendo a las del pack.

**`linter.severity_overrides`** — cambia el nivel de una regla que ya existe, después de que todo catálogo se haya fusionado. `level` es `error` o `warning`. **Rebajar una regla de `error` a `warning` exige un `reason`** — un override que debilita la puerta es una decisión que alguien tomó a propósito, y el motivo viaja con él hacia `policy validate`, `policy show` y el informe de revisión. Endurecer una regla no necesita justificación. Un override que nombra una regla inexistente en cualquier punto del catálogo final es un **error**: no hacer nada en silencio dejaría al equipo creyendo que una regla se relajó cuando no fue así.

**`risk.critical_paths` / `risk.test_patterns`** — se unen entre packs, en orden de precedencia. `test_patterns` enseña al motor de riesgo qué archivos cuentan como test en el layout *de este* proyecto (`spec/**`, `**/*Cest.php`), que es lo que hace que `TEST_PRESENT` se dispare en un repositorio cuyo directorio de tests no se llama `test/` ni `tests/`.

**`risk.weights` / `risk.thresholds`** — un valor único, no una lista. Dos packs no relacionados por `extends` que discrepen sobre el mismo peso es un **error de validación**, nombrando a los dos; una dependencia y su dependiente que discrepen es refinamiento, y gana el dependiente.

**`pr.required_sections`, `commit.allowed_types`, `protected_paths`** — nada en el código lee estos tres. Existen para ser *dichos* al modelo, y por eso se renderizan en los contextos de las skills `pr` y `commit` como texto de prompt, en lugar de quedarse como dato.

### 2.4 `extends`

Un pack puede depender de otros packs. El grafo se resuelve en **orden topológico** — dependencias primero, pack raíz al final — así que los valores de una dependencia se aplican antes que los del pack que se basa en ellos. Un ciclo se rechaza con la cadena en el mensaje, porque "hay un ciclo" sin la ruta no es accionable.

Un pack raíz por repositorio. `gitpr policy use` **sustituye** la elección anterior en lugar de sumarse a ella; el grafo por debajo de la raíz se alcanza mediante `extends`, lo que mantiene la escalera de precedencia una línea en vez de una red.

### 2.5 `baseline`

Un pack puede llevar las supresiones y la deuda aceptada que su stack ya conoce, para que adoptar el pack y adoptar el baseline sean una sola decisión en vez de dos:

```yaml
baseline:
  suppressions:
    - scope: rule
      rule_id: acme-no-float-money
      reason: The float check is advisory while the migration is in flight.
  accepted_debt:
    - fingerprint: "sha256:9f2c…"
      owner: acme-platform
      reason: Scheduled for the payments rewrite.
      due_date: 2026-12-31
```

Las dos mitades tienen la **misma forma y los mismos cuatro escopos** que `.gitpr/baseline.overrides.yml` — `finding`, `line`, `file`, `rule` — y pasan por los **mismos validadores**: un pack que declarara una supresión sin motivo, o deuda aceptada que nadie asume, sería una forma de sortear la auditabilidad por la que existe el baseline. Un pack no compra una regla más débil declarándola en otro archivo. El bloque es cerrado como el resto del manifiesto: una clave desconocida es un error, y un fallo nombra el pack, la mitad y el índice de la entrada, porque eso es lo que imprime `gitpr policy validate`.

Tres propiedades separan esta capa de los archivos del propio repositorio:

| | Bloque del pack | `.gitpr/baseline.json` / `.overrides.yml` |
|---|---|---|
| **Dónde vive** | En memoria, durante la clasificación | En disco, commiteado |
| **Origen mostrado** | `policy:<nombre>@<versión>`, por entrada — la decisión de una dependencia nombra a la dependencia, no a la raíz | `local` |
| **Escrito por una ejecución** | Nunca. Nada de un pack llega al archivo de baseline | `baseline create`, `update`, `suppress` |

Por eso `gitpr baseline unsuppress` no puede quitar una de ellas: dice qué pack la lleva, y la respuesta es una edición al pack, no al repositorio. No se descarga nada para leer el bloque — el pack ya es texto en disco, cubierto por el checksum del lockfile como cualquier otro campo que declare, así que el baseline de un pack no puede editarse sin que el checksum lo note.

Un pack que use este bloque debería declarar un `min_gitpr_version` que incluya la versión contra la que se escribió: un GitPR más antiguo parsea el manifiesto, no conoce la clave y rechaza el pack entero, en lugar de aplicar una política con una mitad ausente en silencio.

---

## 3. Precedencia

De menor a mayor. Un valor con un número mayor se impone sobre uno con un número menor.

| # | Capa | Escrito por |
|---:|---|---|
| 1 | Defaults internos de GitPR | el código |
| 2 | Packs de dependencia | `extends`, en orden topológico |
| 3 | El pack raíz | `.gitpr/policy.lock.yml` |
| 4 | `.gitpr/policy.overrides.yml` | el repositorio |
| 5 | Configuración local del proyecto | `.gitpr/skill/*`, `.gitpr.linter.yml` |
| 6 | Flags de CLI | `--base`, `--provider`, … |
| 7 | Variables de entorno | `GITPR_*` |

El catálogo del linter se fusiona en su propio orden, porque sus capas no son las mismas:

**ruleset de seguridad embebido → reglas de los packs → reglas del proyecto → plugins globales → overrides de severidad**

Los overrides de severidad se aplican **al final**, contra el catálogo final, porque solo ahí el conjunto de nombres de regla conocidos está completo — y eso es lo que permite que un override con una errata falle en lugar de silenciosamente no hacer nada.

### 3.1 El lockfile

`gitpr policy use acme/team-policy@1.0.0` escribe:

```yaml
schema_version: 1
root:
  name: acme/team-policy
  version: 1.0.0
  source: installed
  checksum: 4f449708ac83901bffb4275e8d6d7c880154022bca0382962519c2270cb1842f
packs:
  - name: acme/base-policy
    version: 1.0.0
    source: installed
    checksum: 9c1f…
  - name: acme/team-policy
    version: 1.0.0
    source: installed
    checksum: 4f44…
```

El archivo está pensado para **commitearse**. Un pack dentro del repositorio se registra además por un `path` relativo al repositorio, en POSIX, para que un compañero lo lea desde el mismo lugar en vez de desde una copia propia; un pack del almacén del usuario se registra solo por nombre, porque dónde vive es un detalle de máquina.

### 3.2 Overrides

`.gitpr/policy.overrides.yml` es el repositorio hablando de sí mismo, un nivel por debajo de las flags de CLI. Usa la forma `{add, remove}` para listas, así que eliminar una ruta protegida o una sección obligatoria es una línea en un diff en lugar de una ausencia:

```yaml
protected_paths:
  add:
    - legacy/**
  remove:
    - .env.example

risk:
  weights:
    large_diff: 10
```

---

## 4. Integridad y Comportamiento ante Fallos

### 4.1 El checksum

El checksum de cada pack es SHA-256 sobre `policy.yml` más todos los assets declarados por el manifiesto, calculado cuando el pack se activa y reverificado en cada ejecución. Un asset editado es una política distinta, y una política distinta no fue la que el equipo acordó.

Nótese que el checksum es byte a byte: un pack versionado dentro del repositorio y reescrito por `core.autocrlf` en el checkout abortará con un mismatch. Un `gitpr policy use` sobre un pack con la copia de trabajo normalizada en LF — o un `.gitattributes` fijando el directorio del pack — lo resuelve.

### 4.2 Las tres abortaciones

La resolución **aborta** en lugar de degradar en exactamente tres casos:

| Fallo | Por qué aborta |
|---|---|
| Un pack ya no está en disco | Sus reglas han desaparecido; la salida seguiría llevando la etiqueta de la política |
| Una versión fijada desapareció (tras un upgrade, o un `use` en otro lugar) | La versión que el equipo acordó no es la que se ejecutaría |
| Un checksum ya no coincide | El contenido cambió desde la activación |

Cumplir la mitad de la promesa es peor que no cumplirla, porque la revisión, la salida del linter y la puntuación de riesgo seguirían afirmando ejecutarse bajo la política. Cada abortación nombra el pack, lo que ocurrió y el comando que lo repara.

`strict=False` es la única escotilla de escape, y solo la usan los propios comandos `gitpr policy` — son la herramienta que repara un lockfile roto, así que tienen que poder ejecutarse mientras uno está roto.

### 4.3 Ámbito de caché

GitPR cachea las respuestas de IA por MD5 sobre el prompt. El contexto de la skill es un **argumento separado** (`instrucao_sistema`) y no forma parte de ese hash — así que, sin una corrección, activar un pack sobre un diff ya cacheado no cambiaría absolutamente nada, y la etiqueta sería mentira.

La corrección es el ámbito de caché. Con un pack activo, `::policy::<nombre>@<versión>::<checksum>` se anexa a la clave de caché, lo que significa que un pack activado invalida las entradas afectadas y dos packs distintos nunca comparten una respuesta. Sin pack, el ámbito es la cadena vacía, así que nada cambia.

### 4.4 Garantías

- **Sin red, nunca**: un pack es local por diseño. La resolución lee un lockfile, calcula hashes de archivos y compone texto.
- **Sin ejecución arbitraria**: `policy validate` no lanza ningún subproceso, y la validación es offline y sin efectos secundarios. Un pack es texto que escribió otra persona, y el comando que lo inspecciona no ejecuta nada de lo que contiene.
- **Sin secretos en un manifiesto**: un manifiesto que coincida con una de las reglas embebidas de detección de secretos se rechaza en el parsing, usando el mismo ruleset que ejecuta el linter en lugar de un segundo escáner que podría divergir de él.

---

## 5. Configuración

| Clave | Tipo | Por defecto | Descripción |
|---|---|---|---|
| `GITPR_POLICY_ENABLED` | bool | `true` | Lee y aplica el lockfile. Desactivarlo hace que todo comando se comporte como si el repositorio no tuviera pack, sin tocar el lockfile |
| `GITPR_POLICY_CONTEXT_MAX_CHARACTERS` | int | `12000` | Techo de cuánto contexto puede añadir un pack a un prompt. Más allá, las contribuciones se descartan primero del pack de menor precedencia y el descarte se informa como aviso |

Cuál pack está activo deliberadamente **no** es una clave de configuración: pertenece al repositorio, no a la máquina, así que vive en el lockfile donde puede revisarse y versionarse junto con el código al que se aplica.

---

## 6. Packs Oficiales

| Pack | Reglas en cadena | Para qué sirve |
|---|---:|---|
| `gitpr/php-security` | 8 | Baseline de seguridad PHP: interpolación en SQL, `eval`, hashes de contraseña débiles, `unserialize` ajeno, includes dinámicos, `extract()` desde input, CORS con comodín, cookies de sesión inseguras |
| `gitpr/laravel-quality` | 7 (+8) | Puerta de calidad Laravel: autorización, mass assignment, transacciones, N+1, migraciones reversibles, colas, datos personales. **Extiende `gitpr/php-security`** |
| `gitpr/node-quality` | 7 | Servicios Node: promesas flotantes, validación de entrada, estados no tratados, higiene de dependencias, configuración y secretos |
| `gitpr/vue-quality` | 6 | Componentes Vue 3: props y emits, reactividad, limpieza de efectos secundarios, estados asíncronos, accesibilidad, tamaño del componente |

Cada uno lleva contexto de revisión que un revisor genérico no tiene (lo que cuesta un `down()` que no revierte su `up()`, por qué un job lanzado dentro de una transacción puede ejecutarse antes de que la fila esté commiteada), rutas críticas y patrones de test para su layout, y convenciones de PR/commit. Son deliberadamente pequeños y opinativos: añaden lo que los defaults aún no cubren, en lugar de repetirlos.

`gitpr policy init` elige uno a partir de los marcadores del propio proyecto — `composer.json` + `artisan` para Laravel, `package.json` + Vue para Vue, y así sucesivamente — del más específico al más genérico.

---

## 7. Adoptar una Política en un Equipo

```bash
# Una persona, una vez: valida e instala el pack
gitpr policy install ./our-policy --yes

# En el repositorio: fija y commitea la decisión
gitpr policy use acme/team-policy@1.0.0
git add .gitpr/policy.lock.yml && git commit -m "chore: adopt the Acme quality policy"

# Todo el mundo: nada que instalar si el pack está commiteado con el repo
gitpr policy show
```

Tres formas de compartir una política, según cuánto quiera el equipo depender de una máquina:

- **Un pack dentro del repositorio** (`.gitpr/policies/<nombre>/`) — versionado con el código, sin paso de instalación, y el lockfile registra la ruta relativa. La mejor opción para una política que es del propio repositorio.
- **Un pack instalado** (`~/.gitpr/policies/`) — una copia para todos los repositorios de la máquina. Cada compañero lo instala desde el mismo origen; el lockfile registra nombre y versión.
- **Un pack oficial** — leído directamente de lo que entrega GitPR. Nada que distribuir, y una nueva versión de GitPR puede traer una nueva versión de él.

El ciclo de vida del pack es independiente del de GitPR: sube el `version` en el manifiesto y el checksum cambia, lo que es un diff en el lockfile, lo que es una revisión. Ese es el sentido de fijar la versión.
