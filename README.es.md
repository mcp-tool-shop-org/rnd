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

El banco de investigación del estudio. Los hallazgos de cualquier campo llegan rápidamente como entradas cortas en formato Markdown, con cada fuente etiquetada y cada afirmación marcada como verificada o no. Los experimentos se colocan junto a las entradas que evalúan. Los catálogos externos se replican y se clasifican, y un registro enumera las herramientas del estudio que la investigación puede utilizar. Un solo comando busca en todo.

## Dónde se encuentra: el banco antes de readouts

Dos almacenes contienen el conocimiento del estudio, y realizan diferentes funciones.

| | Investigación y Desarrollo (este repositorio) | [readouts](https://github.com/mcp-tool-shop-org/readouts) |
|---|---|---|
| Función | el banco: recepción, experimentos, preguntas abiertas | el estante: bases de conocimiento verificadas |
| Ritmo | una entrada en minutos, las afirmaciones comienzan en `unverified` | creado y verificado por grupos de estudio |
| Forma | Entradas en Markdown, un tema cada una | una base de conocimiento SQLite por dominio |
| Qué tan desordenado | desordenado a propósito: las afirmaciones disputadas, los callejones sin salida y los resultados provisionales permanecen visibles | nada desordenado: cada fila tiene su origen y está verificada |

El conocimiento se mueve en una sola dirección:

1. **Banco.** Un hallazgo llega aquí como una entrada. Sus afirmaciones comienzan en `[unverified]` y se marcan con `[verified]` solo con una nota de lo que lo verificó. Las mediciones realizadas en nuestras propias máquinas se incluyen como fuentes `rig`, con su configuración en `experiments/`.
2. **Estante interno.** Una vez que las afirmaciones fundamentales de un tema resultan ser válidas, se construye en una base de conocimiento en el repositorio de trabajo privado de readouts, o se agrega a una existente. **La promoción es parte del cierre de un experimento** (El Director, 2026-10-09). Cuando el resultado de un experimento se confirma aquí, su actualización readouts-internal sigue en la misma sesión o en la siguiente, con sus gráficos. Nada permanece en el banco por más de una semana. Las actualizaciones pequeñas y regulares son mejores que una grande. El archivo README de un experimento registra su promoción como una línea debajo de su resultado: "Promocionado: readouts-internal `<kb>` ola `<n>`, `<date>`", o por qué aún no.
3. **Estante público.** Una base de conocimiento se publica en el repositorio público readouts cuando se agrega a la lista de permisos de exportación.

`rnd readouts` busca en cada base de conocimiento readouts desde aquí, por lo que un asiento da acceso a ambos almacenes. Primero, busque en el banco, luego en el estante y, a continuación, investigue la brecha.

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
| `datapacks/<name>/datapack.json` | Manifiesto de `rnd datapack build`: SHA-256 de cada archivo, licencias, fijaciones | generado; nunca editar manualmente |
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
las ramas paralelas nunca entran en conflicto en la línea de versión:

```bash
python -m rnd change "Add study of XYZ"                # writes changes/YYYY-MM-DD-<hex>-<slug>.md (level: nano)
python -m rnd change "New tool feature" --level minor  # levels: nano | micro | patch | minor | major
python -m rnd bump --dry-run                           # preview version bump from changes/ fragments
python -m rnd bump                                     # release PR: bump once, update CHANGELOG.md, delete fragments
```

Sin archivos en `changes/`, `rnd bump [nano|micro|…] [--note …]` mantiene su
comportamiento git-diff. `rnd check` informa de cualquier fragmento mal formado como un error.

## Números vinculados

Un experimento puede mantener números de resumen seguros para el público en
`experiments/<id>/results.json` y vincular números en entradas, resúmenes o
notas del experimento inmediatamente después del literal:

```markdown
The judge scored 84.2%<!-- rnd:experiments/e4b/results.json#accuracy:.1% --> on the held-out split.
```

- Markdown sin formato, `grep` y el índice SQLite conservan el literal sin formato (`84.2%`);
GitHub y Starlight renderizan `84.2%` sin ningún marcador o enlace visible.
- `rnd sync [paths…]` reescribe los literales vinculados de `results.json` utilizando la especificación de formato de Python; `rnd sync --check` sale con código `1` sin escribir si algún literal es diferente.
- `rnd check` trata cualquier literal vinculado que no esté sincronizado, archivo faltante o clave faltante como un error y advierte sobre las afirmaciones `[verified]` cuyo `(via: …)` nombra un experimento de repositorio mientras aún mantienen números no vinculados.

## Identificadores y enlaces de afirmaciones

Las afirmaciones pueden contener identificadores `c-<hex>` estables y deterministas y relaciones explícitas
(`supersedes`, `contradicts`, `supports`) con afirmaciones anteriores por identificador:

```bash
python -m rnd claims                               # list indexed claims (--state superseded, --json)
python -m rnd claims assign <entry>                # add deterministic c-<hex> ids to one entry's claims
python -m rnd reconcile <entry>                    # mark older claims (superseded / disputed / supported-by)
```

`rnd reconcile <entry>` escribe solo el identificador (si falta), el estado actualizado y
la relación inversa (`superseded-by`, `contradicted-by`, `supported-by`) en la
línea de la afirmación más antigua en su propio archivo sin tocar su oración ni ninguna otra
línea. `rnd check` informa de errores en los identificadores de destino incorrectos o los enlaces unilaterales y sugiere
ejecutar `rnd reconcile`. `rnd search` y `rnd show` marcan `superseded` y
`disputed` afirmaciones y nombran la afirmación que las reemplazó o contradijo.

## Preguntas abiertas

Las preguntas abiertas se almacenan como archivos Markdown individuales en `questions/` con el estado
`open`, `investigating`, `answered` o `parked`:

```bash
python -m rnd new-question "Does X hold on Y?" --field systems
python -m rnd questions --status open --json
```

Cuando el `status` de una pregunta es `answered`, su lista `answered_by` en el encabezado
debe nombrar al menos un identificador de afirmación existente; `rnd check` trata una pregunta `answered`
sin un identificador de afirmación existente como un error. Las preguntas se indexan en
`rnd.db` y se devuelven mediante `rnd search` y `rnd show`.

## Registro de búsqueda local fallida

Cuando `rnd search` no devuelve coincidencias, agrega una línea JSON (`time` y
`query`) a un archivo `.misses.jsonl` local junto a `rnd.db` (`rnd.misses.jsonl` en
la raíz del repositorio, ignorado por Git; o `<db>.misses.jsonl` junto a `--db` / `RND_DB`).
No se registra nada más, no se envía nada a través de la red, `RND_NO_USAGE=1`
desactiva el registro y eliminar el archivo lo elimina por completo.
`rnd stats --usage` imprime el recuento total de resultados fallidos y las consultas fallidas más frecuentes.

## Archivos de instrumentación y extras opcionales

- **Archivos de instrumentos (`instruments/*.md`):** editados solo por el asiento de I+D en una diferencia revisada cuya descripción enumera cada archivo de instrumento modificado, nunca por un paso o comando que resuma contenido externo (`rnd watch`, `rnd probe`, `rnd collect`, `rnd catalog sync`).
- **Dependencias principales y extras:** la base de `rnd` sigue siendo solo la biblioteca estándar de Python.
Cualquier extra opcional se encuentra en un grupo de aceptación voluntaria y se importa de forma diferida; un
comando que necesita un extra faltante falla con `MISSING_EXTRA` y una sugerencia de instalación.

## Paquetes de datos

Los datos procesados que son demasiado grandes o voluminosos para la clonación se ofrecen como un **paquete de datos**: los bytes se almacenan
en un repositorio de conjuntos de datos de Hugging Face (privado hasta su publicación), y la biblioteca solo mantiene un
manifiesto pequeño. El modelo de integridad proviene de
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
- **Cada modelo generador está fijado** (resumen Ollama, revisión de HF o ID de modelo de API), con su función.
- **`rnd check` valida cada manifiesto** y falla si se edita manualmente.
- La carga contiene `datapack.json` junto con los archivos, para que cualquiera pueda verificar sin este repositorio:
`pip install mcptoolshop-rnd`.

## Registros de experimentos recopilados

Un repositorio de herramientas confirma sus propias especificaciones y registros de ejecución pre-registrados (los recibos de interlock),
de la misma manera que cada repositorio confirma su mapa de Atlas. La biblioteca publica solo una copia recortada de los
números, creada por `rnd collect` a partir del repositorio de herramientas en confirmaciones fijas:

```bash
rnd collect                 # list the experiments that collect records
rnd collect e4b             # read each source with git show, trim it, write experiments/e4b/results/
rnd collect e4b --check     # recompute every output; exit 1 if any differs from the committed file
```

- **`experiments/<name>/collect.json`** nombra el repositorio, el clon hermano del que se lee (`--clone` anula), y cada fuente: su ruta, la confirmación, el SHA-256 de sus bytes, la salida y la función de recorte en el `extract.py` del experimento.
- **Una fuente fijada nunca cambia.** Los bytes que ya no coinciden con la fijación se rechazan.
- **Cada registro contiene información de procedencia:** el repositorio, la ruta de la fuente y el SHA-256 de los
bytes recortados.
- **Cada salida es segura para el público antes de que se escriba.** Ninguna ruta de máquina, directorio de inicio o
campo de entorno sobrevive, y un módulo de experimento puede agregar una protección más estricta. No se escribe nada en caso de rechazo.

## Prueba de una herramienta antes de un ensayo

`rnd probe <url> …` responde a las primeras preguntas sobre una herramienta o modelo de la API de cada fuente,
no de un resumen de una página web:

- **GitHub** (a través de `gh api`, por lo que utiliza tu inicio de sesión GitHub CLI): la licencia, si el repositorio está archivado, el último push, la última versión y una búsqueda de código de "telemetría". Una coincidencia es una pista para leer, nunca una prueba;
cero coincidencias tampoco son una prueba.
- **Hugging Face:** la etiqueta de licencia o, para "otro", el nombre y el enlace de la licencia de la tarjeta; control de acceso; el último cambio.
- **PyPI y npm:** la licencia, la última versión y la fecha de publicación.
- **rnd en sí:** una búsqueda de palabras exactas del nombre, para que sepas si la biblioteca ya lo tiene.

Se informa de una fuente a la que no se puede acceder como desconocida, con la razón.

## Supervisión de fuentes

`rnd watch` verifica las fuentes en [docs/watchlist.json](docs/watchlist.json) e informa sobre lo que es nuevo desde
la última verificación:

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

Lo que detecta se guarda en un archivo de estado fuera del repositorio (`$RND_WATCH_STATE`, de lo contrario `~/.rnd/watch-state.json`).
La primera comprobación de una fuente es una línea de base: registra los elementos actuales e informa que no hay ninguno nuevo. Una versión preliminar nunca se informa como la última versión de una fuente; si hay una versión preliminar más reciente, se muestra junto a la última versión. Las notas de la versión GitHub y los mensajes de confirmación se guardan en la salida JSON, por lo que el lector no tiene que buscar cada página. Una fuente a la que
no se puede acceder se informa como desconocida y su estado se deja tal cual, para que no se omita nada silenciosamente.

El comando es la mitad determinista de un ritual semanal (Director, 2026-10-13). Un explorador lee los nuevos elementos,
prueba cualquier herramienta candidata con `rnd probe`, comprueba la biblioteca con `rnd search --exact` y escribe un breve
informe clasificado: qué archivar, qué probar y qué omitir. Agregue una fuente mediante una solicitud de incorporación de cambios e indique por qué
es importante.

## Relación con otras herramientas del estudio

- **readouts** es el estante verificado al que alimenta este banco (ver arriba).
- **research-os** crea un paquete de evidencia congelado y controlado para un tema. Un tema en el que
se basa una decisión puede convertirse en un paquete research-os, enlazado desde la entrada.
- **repo-knowledge** indexa los propios repositorios del estudio; esta biblioteca cubre
el conocimiento de fuentes externas.
- Los hallazgos recopilados durante el diseño de algo también pertenecen aquí, para que perduren
más allá de la sesión que los produjo.

Consulte `python -m rnd tools` para obtener el registro completo de herramientas y
[docs/standards.md](docs/standards.md) para ver cómo el flujo de trabajo se evalúa según
los estándares de flujo de trabajo del estudio.

## Seguridad y confianza

- **Datos accedidos:** archivos dentro de este repositorio (`entries/`, `questions/`, `changes/`,
`instruments/`, `catalogs/`, `experiments/`), el índice `rnd.db` y su
archivo de registro local complementario `rnd.misses.jsonl`. `rnd readouts` abre las bases de conocimiento readouts en modo de
**solo lectura**. `rnd sql` se ejecuta contra una conexión de solo lectura.
- **Datos no accedidos:** nada fuera del repositorio y la copia de trabajo local (checkout) de readouts. No almacena ni lee ninguna credencial.
- **Red:** ninguna, excepto `rnd catalog sync`, `rnd probe` y `rnd watch`,
que leen metadatos públicos o llaman a la API GitHub a través de su propia sesión `gh`
cuando se ejecutan.
- **Permisos:** acceso normal a archivos. Ningún privilegio elevado, ningún servicio en segundo plano.
- **Registro de uso solo local:** no se recopila ni se envía nada a ningún lugar. Cuando `rnd search` no devuelve coincidencias, agrega una línea (hora UTC y consulta) a `rnd.misses.jsonl` junto a `rnd.db` (ignorado por Git en el repositorio, o `<db>.misses.jsonl` junto a `--db` / `$RND_DB`). Establezca `RND_NO_USAGE=1` para desactivarlo y elimine `.misses.jsonl` en cualquier momento para borrarlo. No se registra ningún otro dato de uso.
- **Higiene del repositorio público:** antes de cada envío, el árbol se analiza en busca de
rutas del directorio de inicio y la identidad del operador.

Informe de las vulnerabilidades según se describe en [SECURITY.md](SECURITY.md).

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
