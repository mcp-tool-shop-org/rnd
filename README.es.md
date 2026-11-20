<p align="center">
  <a href="README.ja.md">日本語</a> | <a href="README.zh.md">中文</a> | <a href="README.md">English</a> | <a href="README.fr.md">Français</a> | <a href="README.hi.md">हिन्दी</a> | <a href="README.it.md">Italiano</a> | <a href="README.pt-BR.md">Português (BR)</a>
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/mcp-tool-shop-org/brand/main/logos/rnd/readme.png" alt="Research and Development" width="400">
</p>

<p align="center">
  <a href="https://github.com/mcp-tool-shop-org/rnd/actions/workflows/ci.yml"><img src="https://github.com/mcp-tool-shop-org/rnd/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="https://codecov.io/gh/mcp-tool-shop-org/rnd"><img src="https://codecov.io/gh/mcp-tool-shop-org/rnd/branch/main/graph/badge.svg" alt="Coverage"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="MIT License"></a>
  <a href="https://mcp-tool-shop-org.github.io/rnd/"><img src="https://img.shields.io/badge/Landing_Page-live-blue" alt="Landing Page"></a>
</p>

El banco de investigación del estudio. Los hallazgos de cualquier campo llegan rápidamente como entradas cortas en formato Markdown, con cada fuente etiquetada y cada afirmación marcada como verificada o no. Los experimentos se colocan junto a las entradas que evalúan. Los catálogos externos se replican y se clasifican, y un registro enumera las herramientas del estudio que la investigación puede utilizar. Un solo comando busca en todo ello.

## Dónde se encuentra: el banco antes de readouts

Dos almacenes contienen el conocimiento del estudio, y realizan diferentes funciones.

| | Investigación y Desarrollo (este repositorio) | [readouts](https://github.com/mcp-tool-shop-org/readouts) |
|---|---|---|
| Función | el banco: recepción, experimentos, preguntas abiertas | el estante: bases de conocimiento verificadas |
| Ritmo | una entrada en minutos, las afirmaciones comienzan en `unverified` | creado y verificado por grupos de estudio |
| Forma | Entradas en formato Markdown, un tema por entrada | una base de conocimiento SQLite por dominio |
| Qué tan desordenado | desordenado a propósito: las afirmaciones disputadas, los callejones sin salida y los resultados provisionales permanecen visibles | nada desordenado: cada fila tiene su origen y está verificada |

El conocimiento se mueve en una sola dirección:

1. **Banco.** Un hallazgo llega aquí como una entrada. Sus afirmaciones comienzan en `[unverified]` y se marcan con `[verified]` solo con una nota de lo que lo verificó. Las mediciones realizadas en nuestras propias máquinas se incluyen como fuentes `rig`, con su configuración en `experiments/`.
2. **Estante interno.** Una vez que las afirmaciones fundamentales de un tema resultan ser válidas, se construye en una base de conocimiento en el repositorio de trabajo privado de readouts, o se agrega a uno. **La promoción es parte del cierre de un experimento** (El Director, 2026-10-09). Cuando el resultado de un experimento se confirma aquí, su actualización readouts-internal sigue en la misma sesión o en la siguiente, con sus gráficos. Nada permanece en el banco por más de una semana. Las actualizaciones pequeñas y regulares son mejores que una grande. El archivo README de un experimento registra su promoción como una línea debajo de su resultado: "Promocionado: readouts-internal `<kb>` ola `<n>`, `<date>`", o por qué aún no.
3. **Estante público.** Una base de conocimiento se publica en el repositorio público readouts cuando se agrega a la lista de permisos de exportación.

`rnd readouts` busca en cada base de conocimiento readouts desde aquí, por lo que un asiento da acceso a ambos almacenes. Busque primero en el banco, luego en el estante y, a continuación, investigue la brecha.

La investigación aquí no se limita a los campos del estudio. Cada entrada registra dos cosas por separado: cuál es el conocimiento y qué significa para el estudio (`relevance: act | watch | reference`). `reference` es un buen veredicto.

## Úselo

Requiere Python 3.10 o posterior y nada más (solo la biblioteca estándar). Se ejecuta en Windows, macOS y Linux. Desde la raíz del repositorio:

```bash
python -m rnd search cuda graphs            # full-text over entries + catalogues (stemmed: pair finds pairs)
python -m rnd search --exact PAIR           # whole words, same case: the product, not the word
python -m rnd probe https://github.com/NVIDIA/NeMo-Relay   # licence, release, telemetry hits, already in rnd?
python -m rnd show 2026-10-07-cuda-graphs   # one entry, with backlinks
python -m rnd list --relevance act          # what needs doing
python -m rnd tools                         # instruments this seat can use
python -m rnd readouts splice glitch --any  # search the readouts knowledge bases too
python -m rnd catalog lanes                 # NVIDIA skills by lane, with studio fit
python -m rnd catalog list --fit adjacent   # skills worth using when the need arises
python -m rnd new "Paper title" --kind paper --field audio --tag pitch
python -m rnd new-question "Why does X happen?" --field audio
python -m rnd sync --check                  # verify numbers bound to experiments/<id>/results.json
python -m rnd check                         # validate every file (exit 1 on errors)
python -m rnd similar 2026-10-07-cuda-graphs --limit 3  # closest claims in other entries (read-only)
python -m rnd digest --since v1.1.24.0.14   # entries, claims and questions changed since a tag or date
python -m rnd sql "SELECT tier, count(*) FROM sources GROUP BY tier"
python -m rnd change "what changed"         # add a changelog fragment under changes/ (nano by default)
python -m rnd bump --note "release note"    # release PR: apply changes/ fragments, bump version + CHANGELOG
```

Cada comando de listado toma `--json` para agentes. `rnd.cmd` (Windows) y `rnd.sh` (shells POSIX) son envoltorios delgados, por lo que el comando funciona desde cualquier directorio.

Para usar la herramienta desde otros proyectos, instálela desde PyPI:

```bash
pip install mcptoolshop-rnd
```

Eso instala el comando `rnd`, no la biblioteca: las entradas se encuentran en este repositorio. El comando encuentra una biblioteca en este orden: `--library DIR`, luego `$RND_ROOT` y, a continuación, la carpeta más cercana en o por encima del directorio actual que contenga `entries/` y `instruments/`. Fuera de una biblioteca, se detiene con `NO_LIBRARY`; solo `rnd readouts` funciona sin una.

En Python, importe `mcptoolshop_rnd`: ese nombre siempre funciona. `rnd` se mantiene como un alias de compatibilidad, pero también existe un paquete PyPI no relacionado que se llama `rnd`, y si ambos están instalados, puede reemplazar el alias. El comando `rnd` y `python -m mcptoolshop_rnd` siguen funcionando de cualquier manera.

La biblioteca cambia diariamente, por lo que las versiones tienen cinco segmentos, `MAJOR.MINOR.PATCH.MICRO.NANO`. Los tres primeros versionan la herramienta `rnd`; MICRO marca un cambio estructural en la biblioteca y NANO una actualización ordinaria. Las actualizaciones ordinarias agregan un fragmento de registro de cambios debajo de `changes/` a través de `rnd change`; en el momento de la publicación, `rnd bump` consume todos los fragmentos, mueve la versión una vez por el nivel de fragmento más alto y escribe una sección de CHANGELOG.

Códigos de salida: `0` correcto · `1` archivos de biblioteca no válidos · `2` error de uso o no encontrado · `3` falla en tiempo de ejecución (una herramienta externa o un error inesperado). Los errores imprimen un código, un mensaje y una pista; `--debug` agrega el rastreo de la pila.

## Diseño

| Ruta | Qué | Quién edita |
|------|------|-----------|
| `entries/YYYY/*.md` | Entradas de investigación: la fuente de la verdad | personas y agentes |
| `questions/*.md` | Preguntas de investigación abiertas y respondidas | personas y agentes |
| `changes/*.md` | Fragmentos de registro de cambios no publicados (`rnd change`) | personas y agentes (`rnd bump` consume) |
| `experiments/<name>/` | Configuraciones, entradas fijas, `results.json` y recibos de resultados | personas y agentes |
| `experiments/<name>/collect.json` | Registros recopilados de un repositorio de herramientas en confirmaciones fijas (`rnd collect`) | personas |
| `instruments/*.md` | Herramientas y protocolos del estudio que el asiento puede utilizar (`kind: instrument`) | Solo asiento de I+D (diferencia revisada) |
| `catalogs/<name>/source.json` | De dónde proviene un catálogo | personas |
| `catalogs/<name>/catalog.json` | Instantánea fija de `rnd catalog sync` | generado; nunca editar manualmente |
| `catalogs/<name>/review.json` | Ajuste y notas del estudio por familia y artículo | personas |
| `datapacks/<name>/spec.json` | Qué contiene un paquete de datos: incluir patrones glob, licencias, generadores, host | personas |
| `datapacks/<name>/datapack.json` | Manifiesto de `rnd datapack build`: SHA-256 de cada archivo, licencias, fijaciones de modelos | generado; nunca editar manualmente |
| `datapacks/<name>/hosted.json` | Dónde aterrizó la carga (revisión del repositorio) | después de una carga |
| `mcptoolshop_rnd/` | La CLI | código |
| `rnd/` | Alias de compatibilidad para `mcptoolshop_rnd` | código |
| `rnd.db` | SQLite FTS5 índice, reconstruido automáticamente cuando cambian los archivos | generado; no está en git |
| `rnd.misses.jsonl` | Registro de búsqueda local de cero aciertos junto a `rnd.db` (`RND_NO_USAGE=1` deshabilita) | generado; no está en git |

## Formato de entrada

```markdown
---
id: 2026-10-07-cuda-graphs        # defaults to the file name
title: CUDA Graphs
date: 2026-10-07
kind: concept                     # finding concept release paper tool catalog rig-fact event question decision instrument
relevance: reference              # act | watch | reference
fields: [gpu-computing]           # any research field, open vocabulary
tags: [cuda-graphs, pytorch]
---

## Summary
## Key points
## Studio relevance
## Claims
- [unverified] A checkable statement.
- [verified] [c-a1b2c3d4] A checked statement. (via: what checked it, date)
## Sources
- [primary] https://… — publisher
```

- **Niveles de fuente:** `primary` (documentación del proveedor, artículos, repositorios), `secondary` (reseñas de buena reputación), `aggregator` (sitios de resumen, resultados de búsqueda de IA), `user` (proporcionado por una persona: diapositivas, notas), `rig` (medido en nuestras máquinas).
- **Confianza de la afirmación:** `unverified`, `verified`, `disputed`, `wrong`, `superseded`. Una afirmación `verified` o `wrong` debe indicar qué la verificó con `(via: …)`.
- `[[entry-id]]` vincula las entradas; `rnd show` enumera los enlaces inversos.

## Fragmentos de registro de cambios

Las actualizaciones no modifican directamente `mcptoolshop_rnd/__init__.py` o `CHANGELOG.md`, por lo que
las ramas paralelas nunca entran en conflicto en la línea de versiones:

```bash
python -m rnd change "Add study of XYZ"                # writes changes/YYYY-MM-DD-<hex>-<slug>.md (level: nano)
python -m rnd change "New tool feature" --level minor  # levels: nano | micro | patch | minor | major
python -m rnd bump --dry-run                           # preview version bump from changes/ fragments
python -m rnd bump                                     # release PR: bump once, update CHANGELOG.md, delete fragments
```

Sin archivos en `changes/`, `rnd bump [nano|micro|…] [--note …]` mantiene su
comportamiento git-diff. Tanto `__init__.py` como `CHANGELOG.md` se preparan a través de
archivos temporales y se intercambian con `os.replace`, revirtiendo `__init__.py` si el
intercambio de CHANGELOG falla. Si un error deja `__init__.py` por delante de `CHANGELOG.md`,
volver a ejecutarlo en el nivel correspondiente completa la actualización y cualquier otro nivel
la rechaza con `BAD_CHANGELOG`. Queda un problema: un error después de que se hayan intercambiado ambos archivos, pero antes de que se eliminen los fragmentos en `changes/`, los deja en
su lugar, y una nueva ejecución provocaría una segunda actualización, por lo que primero elimine esos fragmentos manualmente. `rnd check` informa de cualquier
fragmento mal formado como un error.

## Números vinculados

Un experimento puede mantener números resumidos seguros para el público en
`experiments/<id>/results.json` y vincular números en entradas, resúmenes o
notas de experimento inmediatamente después del literal:

```markdown
The judge scored 84.2%<!-- rnd:experiments/e4b/results.json#accuracy:.1% --> on the held-out split.
```

- Markdown sin formato, `grep` y el índice SQLite conservan el literal sin formato (`84.2%`);
GitHub y Starlight renderizan `84.2%` sin ningún marcador o enlace visible.
- `rnd sync [paths…]` reescribe los literales vinculados de `results.json` utilizando la
  especificación de formato de Python; `rnd sync --check` sale con código `1` sin escribir si algún
  literal es diferente.
- `rnd check` trata cualquier literal vinculado que no esté sincronizado, archivo faltante o clave faltante
como un error y advierte sobre las afirmaciones `[verified]` cuyo `(via: …)` nombra un experimento de repositorio
mientras aún mantiene números no vinculados, ignorando los enteros sin formato (sin
punto decimal, signo de porcentaje, separador de miles o unidad final) que
se emparejan con la palabra anterior en el título o las etiquetas de la entrada, o que siguen a
`RTX` o `GTX` (3–4 dígitos) o `CUDA`, `PTX`, `Gemma`, `Llama`, `Qwen`,
`Claude`, `GPT` o `Phi` (1–2 dígitos).

## Identificadores y enlaces de afirmaciones

Las afirmaciones pueden contener identificadores `c-<hex>` estables y deterministas y relaciones explícitas
(`supersedes`, `contradicts`, `supports`) con afirmaciones anteriores por identificador:

```bash
python -m rnd claims                               # list indexed claims (--state superseded, --json)
python -m rnd claims assign <entry>                # add deterministic c-<hex> ids to one entry's claims
python -m rnd similar <entry> [--limit 5]          # closest claims in other entries (read-only)
python -m rnd reconcile <entry>                    # mark older claims (superseded / disputed / supported-by)
```

`rnd similar <entry>` ejecuta una consulta SQLite FTS5 BM25 de solo lectura sobre `claims_fts`
para cada afirmación de `<entry>` en comparación con otras entradas (`--limit` tiene un valor predeterminado de 5),
marca las coincidencias de `superseded` o `disputed` con lo que las reemplazó o contradijo,
imprime las cláusulas exactas `(supersedes: id)` / `(contradicts: id)` / `(supports: id)`
y el comando `rnd reconcile <entry>`, y nunca escribe `rnd.db` ni ninguna
entrada. `rnd reconcile <entry>` escribe solo el identificador (si falta), el estado actualizado y
la relación inversa (`superseded-by`, `contradicted-by`, `supported-by`) en la
línea de la afirmación anterior en su propio archivo sin tocar su oración ni ninguna otra
línea (dejando una afirmación `[wrong]` `[wrong]` cuando se contradice). Tanto
`rnd claims assign` como `rnd reconcile` se niegan (`MULTIPLE_CLAIMS_HEADINGS`)
sin escribir si una entrada contiene más de un encabezado real `## Claims`.
`rnd check` informa de errores en los identificadores de destino incorrectos, los enlaces unilaterales (sugiriendo ejecutar
`rnd reconcile` o eliminar la cláusula y restablecer un estado `superseded` o `disputed`) o una cerca de código no cerrada,
y advierte sobre una afirmación `[superseded]` sin un enlace `(superseded-by: …)`.
`rnd search` y `rnd show` marcan las afirmaciones `superseded` y `disputed` y nombran la
afirmación que las reemplazó o contradijo.

## Qué cambió (resumen)

`rnd digest --since <git ref or YYYY-MM-DD> [--json]` compara la biblioteca en un
commit anterior (analizado a partir de objetos git en la memoria sin tocar el árbol de trabajo, el índice git, `rnd.db` o los archivos temporales) con el árbol actual:

```bash
python -m rnd digest --since v1.1.24.0.14
python -m rnd digest --since 2026-11-19 --json
```

Informa de las entradas agregadas, las afirmaciones agregadas, las afirmaciones eliminadas, los cambios de estado de las afirmaciones
(`old_state -> new_state` con lo que las reemplazó o contradijo) y
las preguntas abiertas, respondidas (con los identificadores de las afirmaciones que responden) y archivadas, junto con
los recuentos. Una fecha `YYYY-MM-DD` se resuelve en el commit más reciente a lo largo de
la línea del primer padre de la rama actual (`HEAD`) cuya fecha del committer es de ese mismo día o
anterior. Las afirmaciones coinciden por `id` cuando ambos lados tienen una, de lo contrario, por
`(entry, exact text)`, por lo que una afirmación reformulada sin un identificador aparece como una afirmación
eliminada y una afirmación agregada, nunca como un cambio de estado.

## Preguntas abiertas

Las preguntas abiertas se almacenan como archivos Markdown individuales en `questions/` con el estado
`open`, `investigating`, `answered` o `parked`:

```bash
python -m rnd new-question "Does X hold on Y?" --field systems
python -m rnd questions --status open --json
```

Cuando la propiedad `status` de una pregunta es `answered`, su lista `answered_by` en el encabezado
debe nombrar al menos un identificador de afirmación existente; `rnd check` trata una pregunta `answered`
sin un identificador de afirmación existente como un error. Las preguntas se indexan en
`rnd.db` y se devuelven mediante `rnd search` y `rnd show`.

## Registro de búsquedas locales fallidas

Cuando `rnd search` no devuelve ninguna coincidencia, agrega una línea JSON (`time` y
`query`) a un archivo `.misses.jsonl` local junto a `rnd.db` (`rnd.misses.jsonl` en
la raíz del repositorio, ignorado por git; o `<stem>.misses.jsonl` junto a `--db` / `RND_DB`,
por lo que `--db foo.db` escribe `foo.misses.jsonl` junto a él, no `foo.db.misses.jsonl`).
No se registra nada más, no se envía nada a través de la red, `RND_NO_USAGE=1`
desactiva el registro y eliminar el archivo lo elimina por completo.
`rnd stats --usage` imprime el recuento total de búsquedas fallidas y las consultas fallidas más frecuentes.

## Archivos de instrumentación y extras opcionales

- **Archivos de instrumentación (`instruments/*.md`):** editados solo por el responsable de I+D en un
diff revisado cuya descripción enumera cada archivo de instrumentación modificado, nunca por un
paso o comando que resuma contenido externo (`rnd watch`, `rnd probe`,
`rnd collect`, `rnd catalog sync`).
- **Dependencias principales y extras:** la base de `rnd` sigue siendo solo la biblioteca estándar de Python.
Cualquier extra opcional se encuentra en un grupo opcional y se importa de forma diferida; un
comando que necesita un extra faltante falla con `MISSING_EXTRA` y una sugerencia de instalación.

## Paquetes de datos

Los datos procesados que son demasiado grandes o voluminosos para el clon se ofrecen como un **paquete de datos**: los bytes se almacenan
en un repositorio de conjuntos de datos de Hugging Face (privado hasta que se publica) y la biblioteca solo mantiene un manifiesto pequeño. El modelo de integridad proviene de
[research-packs](https://github.com/mcp-tool-shop-org/research-packs): un manifiesto, un SHA-256 para
cada archivo, una verificación de un solo comando y una lista.

```bash
rnd datapack build natural-errors --source experiments/natural-errors  # reads datapacks/natural-errors/spec.json
rnd datapack list
hf download mcp-tool-shop/rnd-natural-errors --repo-type dataset --local-dir ne
rnd datapack verify natural-errors --copy ne/files                      # PASS when every byte matches
```

- **Cada archivo necesita una licencia** en la especificación. Las salidas del modelo llevan los términos de su modelo (por
ejemplo, "Creado con Llama" para las salidas de Llama 3.1). `rnd datapack build` rechaza un paquete que
deja un archivo sin cubrir.
- **Cada modelo generador está fijado** (resumen Ollama, revisión de HF o identificador de modelo de API), con su función.
- **`rnd check` valida cada manifiesto** y falla si se edita manualmente.
- La carga lleva `datapack.json` junto con los archivos, por lo que cualquiera puede verificar sin este repositorio:
`pip install mcptoolshop-rnd`.

## Registros de experimentos recopilados

Un repositorio de herramientas confirma sus propias especificaciones y registros de ejecución preregistrados (los recibos de interlock),
de la misma manera que cada repositorio confirma su mapa de Atlas. La biblioteca publica solo una copia recortada de los
números, creada por `rnd collect` a partir del repositorio de herramientas en commits fijados:

```bash
rnd collect                 # list the experiments that collect records
rnd collect e4b             # read each source with git show, trim it, write experiments/e4b/results/
rnd collect e4b --check     # recompute every output; exit 1 if any differs from the committed file
```

- **`experiments/<name>/collect.json`** identifica el repositorio y el repositorio clonado del que se lee la información
(`--clone` anula la configuración predeterminada), así como cada fuente: su ruta, el commit, el SHA-256 de sus bytes, la
salida y la función de recorte en el `extract.py` del experimento.
- **Una fuente fijada nunca cambia.** Los bytes que ya no coinciden con el hash de la fijación se rechazan.
- **Cada registro contiene información de procedencia:** el repositorio, la ruta de la fuente y el SHA-256 de los
bytes recortados.
- **Cada salida es segura para el público antes de ser escrita.** No se conservan ninguna ruta de máquina, directorio de inicio o
campo de entorno, y un módulo de experimento puede agregar una protección más estricta. No se escribe nada
en caso de rechazo.

## Evaluación de una herramienta antes de una prueba

`rnd probe <url> …` responde a las primeras preguntas sobre una herramienta o modelo a partir de la propia API de cada fuente,
no a partir de un resumen de una página web:

- **GitHub** (a través de `gh api`, por lo que utiliza tu inicio de sesión de GitHub CLI): la licencia, si está archivada, la
última actualización, la última versión y una búsqueda de código de "telemetría". Un resultado positivo es una pista para leer, nunca una prueba;
cero resultados tampoco son una prueba.
- **Hugging Face:** la etiqueta de licencia o, para "otros", el nombre y el enlace de la licencia de la tarjeta; control de acceso; el último cambio.
- **PyPI y npm:** la licencia, la última versión y la fecha de publicación.
- **La propia rnd:** una búsqueda exacta de la palabra del nombre, para que sepas si la biblioteca ya lo contiene.

Una fuente a la que no se puede acceder se informa como desconocida, indicando el motivo.

## Supervisión de fuentes

`rnd watch` comprueba las fuentes en [docs/watchlist.json](docs/watchlist.json) e informa de las novedades desde
la última comprobación:

- El blog técnico de NVIDIA;
- la versión del kit de herramientas CUDA;
- los nuevos modelos de Hugging Face de NVIDIA;
- el catálogo de habilidades de NVIDIA;
- las versiones de los motores y las herramientas que utiliza el estudio, como Ollama, OpenVINO, PyTorch, ComfyUI y Claude Code.

```bash
python -m rnd watch                  # what's new; records what it saw
python -m rnd watch --no-save --json # look without recording
python -m rnd watch --only ollama    # one source
```

Lo que se ha encontrado se guarda en un archivo de estado fuera del repositorio (`--state`, de lo contrario `$RND_WATCH_STATE`, de lo contrario `Path.home() / ".rnd" / "watch-state.json"`, `~/.rnd/watch-state.json`), a menos que se pase `--no-save`.
La primera comprobación de una fuente sirve como referencia: registra los elementos actuales y no informa de ninguno como nuevo. Una versión preliminar nunca se informa como la última versión de una fuente; si hay una versión preliminar más reciente, se muestra junto a la última versión. Las notas de la versión GitHub y los mensajes de commit se guardan en la salida JSON, para que el lector no tenga que buscar cada página. Una fuente a la que
no se puede acceder se informa como desconocida y su estado se deja intacto para que no se omita nada silenciosamente.

El comando es la mitad determinista de un ritual semanal (Director, 2026-10-13). Un explorador lee los nuevos elementos,
evalúa cualquier herramienta candidata con `rnd probe`, comprueba la biblioteca con `rnd search --exact` y escribe un breve
informe clasificado: qué archivar, qué probar y qué omitir. Agrega una fuente mediante una solicitud de incorporación y explica por qué
es importante.

## Relación con otras herramientas del estudio

- **readouts** es el estante verificado al que alimenta este banco (véase arriba).
- **research-os** crea un paquete de evidencia congelado y con control de acceso para un tema. Un tema del que
depende una decisión puede convertirse en un paquete research-os, enlazado desde la entrada.
- **repo-knowledge** indexa los propios repositorios del estudio; esta biblioteca cubre
el conocimiento de fuentes externas.
- Los hallazgos recopilados durante el diseño de algo también deben estar aquí, para que perduren
más allá de la sesión que los produjo.

Consulte `python -m rnd tools` para obtener el registro completo de instrumentos y
[docs/standards.md](docs/standards.md) para ver cómo se evalúa el flujo de trabajo en relación con
los estándares de flujo de trabajo del estudio.

## Seguridad y confianza

- **Datos escritos**, según dónde se almacenen:
- **Dentro de este repositorio** (la biblioteca: `--library`, de lo contrario `$RND_ROOT`, de lo contrario la carpeta más cercana en o por encima del directorio de trabajo que contiene `entries/` y `instruments/`, de lo contrario la copia del repositorio desde la que se ejecuta el paquete): `rnd new` (un archivo nuevo en `entries/` o `instruments/`, nunca sobrescribiendo), `rnd new-question` (`questions/`), `rnd new-experiment`,
  `rnd runs record` y `rnd collect <name>` (`experiments/<name>/`),
  `rnd claims assign`, `rnd reconcile` y `rnd sync` (líneas de afirmación y números vinculados en los archivos Markdown existentes), `rnd change` (`changes/`), `rnd bump`
  (`mcptoolshop_rnd/__init__.py` y `CHANGELOG.md`, a través de archivos temporales
  junto a cada uno, y elimina los fragmentos de `changes/` que utilizó),
  `rnd catalog sync` (`catalogs/<name>/catalog.json`), `rnd datapack build`
  (`datapacks/<name>/datapack.json`) y `rnd layout` (`docs/layout.json`).
- **El índice:** `rnd.db`, o la ruta proporcionada por `--db` o `$RND_DB`, con un archivo temporal `.db.tmp` junto a él mientras se construye. `rnd build` lo escribe, y cada comando que lee el índice (`search`, `show`, `list`, `tools`,
`stats`, `catalog`, `claims`, `questions`, `sql`, `runs`, `ledger`, `where`,
`probe`) lo reconstruye primero cuando se ha modificado un archivo de origen. El registro de búsquedas sin coincidencias `rnd.misses.jsonl` se encuentra junto a él (véase más abajo).
- **Tu carpeta de inicio:** `rnd watch` escribe su archivo de elementos vistos en `--state`, de lo contrario `$RND_WATCH_STATE`, de lo contrario `~/.rnd/watch-state.json` (construido en el código como `Path.home() / ".rnd" / "watch-state.json"`), donde permanece entre ejecuciones. Se escribe a través de un archivo `.tmp` junto a él.
`--no-save` omite la escritura.
- **Los almacenes de datos sin procesar, fuera de este repositorio:** `rnd raw ingest`, `rnd raw private` y
`rnd raw relicense` escriben en el almacén público (`--public`, de lo contrario `$RND_DATA`,
de lo contrario `../rnd-data`) y en el almacén privado (`--private`, de lo contrario `$RND_DATA_PRIVATE`, de lo contrario `../rnd-data-private` junto a la biblioteca; cuando se ejecuta `rnd raw` fuera de una biblioteca, `rnd-data-private` junto al almacén público). `rnd raw ingest` también coloca cada archivo de más de 256 KB en el almacén de blobs, en `blobs/` en la carpeta con el nombre especificado por `$RND_DATA_STORE_D` o por la entrada `"d"` del `store.local.json` del almacén público (no hay un valor predeterminado; sin uno, la ingestión se niega). Los blobs se escriben a través de un archivo `.tmp` junto a ellos y se marcan como de solo lectura. Con `--link`, un nuevo blob es un enlace físico al archivo de origen, por lo que **ese archivo de origen también se vuelve de solo lectura** (un blob que ya está en el almacén se deja intacto, y lo mismo ocurre con su archivo de origen); sin `--link`, el archivo de origen no se modifica. `rnd raw ingest --update` elimina los archivos pequeños anteriores de una ejecución en los dos almacenes antes de escribir los nuevos. `--dry-run` no escribe nada.
- **Se lee, nunca se escribe:** `rnd readouts` (SQLite en modo de solo lectura), los clones de origen de `rnd collect` (`git show`), `rnd raw verify`, `rnd datapack verify --copy`,
  `rnd runs record --from`, `rnd abmine`, y `rnd similar` y `rnd digest`,
  que funcionan en memoria y no escriben nada en ninguna parte: ningún archivo temporal ni ningún cambio en el árbol de trabajo, el índice git o `rnd.db`.
- **Código que se ejecuta:** `rnd collect <name>`, con o sin `--check`, carga y ejecuta `experiments/<name>/extract.py` (o el módulo que la entrada `collect.json` de esa carpeta
especifica) desde la biblioteca (`mcptoolshop_rnd/collect.py:142-149`). Python puede
almacenar en caché el código de bytes de ese módulo en `experiments/<name>/__pycache__/`. `rnd` limita
lo que escribe por sí mismo a `experiments/<name>/`; no limita lo que hace el propio código de ese
módulo, por lo que ejecútelo solo en una biblioteca en la que confíe.
- **Fuera del comando `rnd`:** el paquete también incluye `mcptoolshop_rnd.localbuilders`, el conjunto de herramientas del experimento de compiladores locales. Ningún comando `rnd` lo ejecuta. Si se ejecuta directamente (por ejemplo, `python -m mcptoolshop_rnd.localbuilders.runner`), en la máquina alquilada para la que
se escribió y en parte como root, crea, elimina y cambia el propietario y los permisos de los archivos bajo las rutas
que le pasa quien lo invoca (rutas de trabajo, inicio, historial, entorno virtual, recibo, registro,
informe, directorio secreto y sonda de contención), y su evaluador utiliza una carpeta temporal dentro de la carpeta temporal del sistema
operativo, que se elimina cuando finaliza.
- **Datos que no se tocan:** ningún comando `rnd` escribe, elimina o modifica un archivo
en cualquier otro lugar. No almacena credenciales ni lee ninguna.
- **Red:** ninguna, excepto `rnd catalog sync`, `rnd probe` y `rnd watch`,
que leen metadatos públicos o llaman a la API GitHub a través de su propio inicio de sesión de la CLI `gh`
cuando los ejecuta.
- **Permisos:** acceso normal a archivos. Ningún comando `rnd` necesita derechos elevados y no hay ningún servicio en segundo plano.
- **Registro de uso solo local:** no se recopila ni se envía nada a ninguna parte. Cuando `rnd search`
no devuelve coincidencias, agrega una línea (hora UTC y consulta) a `rnd.misses.jsonl`
junto a `rnd.db` (ignorada por git en el repositorio; con `--db foo.db`, `foo.misses.jsonl`
junto a él, no `foo.db.misses.jsonl`, y lo mismo para `$RND_DB`). Establezca
`RND_NO_USAGE=1` para desactivarlo y elimine el archivo `.misses.jsonl` en cualquier
momento para borrarlo. No se registra ningún otro dato de uso.
- **Higiene del repositorio público:** antes de cada envío, el árbol se analiza en busca de
rutas de la carpeta de inicio y la identidad del operador.

Informe de vulnerabilidades según se describe en [SECURITY.md](SECURITY.md).

## Pruebas

```bash
bash verify.sh                               # tests, library check, index build, smoke
python -m unittest discover -s tests -t .    # tests only
```

## Estado y licencia

Mantenido por el estudio y en uso diario. Código: [MIT](LICENSE). Entradas: CC BY
4.0. El espejo de habilidades de NVIDIA en `catalogs/nvidia-skills/catalog.json`
reproduce los nombres y descripciones de las habilidades de
[NVIDIA/skills](https://github.com/NVIDIA/skills) bajo las licencias de ese proyecto
(Apache-2.0 para el código, CC-BY-4.0 para el texto de las habilidades).

---

<p align="center">Built by <a href="https://mcp-tool-shop.github.io/">MCP Tool Shop</a></p>
