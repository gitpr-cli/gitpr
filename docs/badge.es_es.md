# Documentación Técnica: Insignia de Pull Request

Todo pull request publicado por GitPR lleva una insignia pequeña al pie del cuerpo: `GitPR` y los recuentos del linter para el cambio. Se arma a partir de una medición que GitPR hizo de verdad — el linter estático local, sobre el diff que se está publicando — y es una imagen Markdown que shields.io renderiza en el navegador de quien lee, así que no se pide nada a la red mientras se escribe el pull request.

Hay una segunda insignia, estática, para el README de tu proyecto. `gitpr badge --readme` imprime el fragmento y no escribe nada.

---

## 1. Visión General

La insignia es un recurso con opt-out. Viene activada por defecto, nunca pregunta nada — ni prompt, ni confirmación en la primera ejecución — y se avisa dos veces: una cuando `gitpr --init` configura un forge, que es donde publicar pasa a ser posible, y otra en una publicación que la añade sin que hayas visto el cuerpo antes.

### 1.1 Referencia del Comando — `gitpr badge`

Todas las opciones del subcomando, como las muestra `gitpr badge -h` (o `--help`):

```bash
gitpr badge                          # qué es, más el fragmento
gitpr badge --readme                 # solo el fragmento, listo para pipe
gitpr badge --style for-the-badge    # otro estilo de shields.io
```

| Opción | Descripción |
| --- | --- |
| **`--readme`** | Imprime solo el fragmento, sin nada alrededor — seguro para `>>` y para pipe |
| **`--style <style>`** | `flat` (por defecto), `flat-square` o `for-the-badge`. Un valor desconocido avisa en stderr y recurre a `flat` |
| **`-h` / `--help`** | Ayuda más el enlace de la documentación en el idioma actual |

| Característica | Descripción |
| --- | --- |
| **Archivos escritos** | Ninguno. El comando imprime; nunca edita tu README |
| **Red** | Ninguna. La URL se arma, nunca se solicita |
| **Configuración** | No se lee ninguna: el fragmento no depende de tu proveedor, de tu forge ni de tu idioma |
| **Código de salida** | 0. Un `--style` desconocido es un aviso, no un fallo |

---

## 2. Qué Dice la Insignia

Los recuentos vienen de las reglas YAML del linter estático local, ejecutadas sobre el mismo diff del pull request. Solo se usan las reglas — el puente de linters externos se salta, porque ejecuta binarios contra el árbol de trabajo, y no contra la revisión que se está publicando.

| errors | warnings | Color | Mensaje |
| --- | --- | --- | --- |
| **> 0** | cualquiera | `red` | `N errors · M warnings` |
| **0** | **> 0** | `yellow` | `0 errors · M warnings` |
| **0** | **0** | `brightgreen` | `no issues` |

Dos reglas moldean el texto:

- **Un cero aparece junto a un recuento distinto de cero.** `0 errors · 2 warnings` dice lo que se midió; esconder el cero daría a entender que los errores nunca se contaron. Cada recuento se pluraliza por su cuenta, así que `1 error · 1 warning` se escribe así.
- **La insignia nunca afirma una revisión.** Informa lo que el linter contó, en el vocabulario del linter. Una insignia verde significa *no se encontró ninguna violación de regla*, no *este código fue revisado y aprobado* — la revisión por IA es otro paso, sin participación alguna en esto.

Lo que ves en el pull request es una sola imagen. `GitPR | 0 errors · 2 warnings` es como la dibuja shields.io, no una segunda línea de texto en el cuerpo, y la imagen es un enlace a [gitpr.natanfiuza.dev.br](https://gitpr.natanfiuza.dev.br/).

El texto de la insignia es **inglés fijo**, sea cual sea el idioma de la interfaz. Como el cuerpo del pull request en el que está, es un artefacto público que sobrevive a la máquina que lo escribió, y aterriza en un repositorio cuyos lectores pueden no hablar tu idioma.

---

## 3. Dónde Se Añade

La insignia se añade en un único lugar, después de que el cuerpo del pull request esté completo y antes de que lo lea cualquiera de los publicadores:

| Camino | La insignia |
| --- | --- |
| **`gitpr`** (TUI) | **Sí** — sembrada en el cuerpo editable, así que puedes cambiarla o borrarla antes de publicar |
| **`gitpr --no-edit`** | **Sí** — compuesta en la petición que se envía |
| **`gitpr --no-publish`** | **No** — el `.md` escrito localmente es la salida de la IA, antes de que se arme la insignia |
| **`gitpr review-pr`** | **No** — un comentario de revisión es otro artefacto, y GitPR no lo firma |
| **Herramientas MCP** | **No** — las herramientas devuelven lo que produjo el modelo |

La TUI es la razón de que la insignia se siembre en lugar de inyectarse en el momento del envío: está en pantalla, en el área de texto que ya estás editando, y la última palabra es tuya. Actualizar un pull request existente reenvía el cuerpo que está en pantalla — incluida la insignia, si la mantuviste.

El añadido es idempotente. Un cuerpo que ya lleva una insignia se deja como está, así que republicar nunca apila dos.

---

## 4. Cuándo No Hay Insignia

**Sin reglas de linter, sin insignia.** Un `.gitpr/skill/.gitpr.linter.yml` vacío — el estado de quien nunca ejecutó `gitpr --skill` — significa que el linter no tiene nada que ejecutar, y su resultado vacío es indistinguible de un diff limpio. Una insignia verde sobre un diff que nadie comprobó sería una afirmación que GitPR no puede sostener, así que se omite por completo.

**El opt-out es `GITPR_BADGE=false`.** Como en el trailer de coautoría, `false`, `0`, `no`, `off` y `n` la desactivan, sin distinguir mayúsculas e ignorando espacios alrededor; cualquier otra cosa — o la variable ausente — la mantiene activada. Nunca se escribe en el `.env` en tu nombre.

Con la flag desactivada, no se arma ninguna insignia y no se imprime ningún aviso: el pull request sale exactamente como salía antes de que existiera este recurso.

---

## 5. La Insignia del README

La insignia que puedes poner en tu propio proyecto es otra: estática, siempre la misma, y dice lo que hace la herramienta, no lo que midió.

```markdown
[![GitPR](https://img.shields.io/badge/GitPR-quality--checked-blue)](https://gitpr.natanfiuza.dev.br/)
```

`gitpr badge` la imprime con una explicación breve; `gitpr badge --readme` imprime la línea sola, que es lo que quieres para `gitpr badge --readme >> README.md`. De una forma u otra el comando solo imprime — colocarla es decisión tuya, porque solo tú sabes dónde queda bien en tu README.

---

## 6. Configuración

| Dónde | Nombre | Observaciones |
| --- | --- | --- |
| `~/.gitpr/.env` | `GITPR_BADGE` | Activada por defecto; `false` desactiva la insignia. Solo lectura — GitPR nunca la escribe |
| Pantalla de configuración | **Insignia de pull request** | Sección General, el mismo interruptor, con el valor por defecto explícito en la descripción |
| `gitpr --init` | Aviso | Se muestra cuando se configura el forge, junto con el interruptor que la desactiva |
| `gitpr --no-edit` | Aviso | Se muestra cuando se añadió una insignia a un cuerpo que no viste |

---

## 7. Variables de Entorno

| Variable | Para qué sirve |
| --- | --- |
| `GITPR_BADGE` | `false` (o `0`, `no`, `off`, `n`) publica cuerpos de pull request sin la insignia |
| `GITPR_LANG` | Idioma de la interfaz. La insignia en sí es siempre en inglés |

> **Nota:** Consulta también la [documentación de Publicación de PR en GitHub](pull-request-publication.es_es.md) para el flujo al que se añade la insignia, y la [documentación del Linter Estático Personalizable](linter-regras-customizadas.es_es.md) para las reglas de donde vienen los recuentos — la insignia no tiene nada que informar mientras esas reglas no existan.
