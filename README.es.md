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

| | Investigación y Desarrollo (este repositorio). | [readouts](https://github.com/mcp-tool-shop-org/readouts) |
|---|---|---|
| Función. | El banco: recopilación, experimentos, preguntas abiertas. | El estante: bases de conocimiento verificadas. |
| Ritmo. | Una entrada en minutos, las afirmaciones comienzan en `unverified`. | Creado y verificado por grupos de estudio. |
| Forma. | Entradas en formato Markdown, un tema por cada una. | Una base de conocimiento SQLite por dominio. |
| Qué tan desordenado. | Desordenado a propósito: las afirmaciones disputadas, los callejones sin salida y los resultados provisionales permanecen visibles. | Nada desordenado: cada fila tiene su origen y está verificada. |

El conocimiento se mueve en una sola dirección:

1. **Banco de pruebas.** Un resultado se registra aquí como una entrada. Sus afirmaciones comienzan en `[unverified]`,
y se marcan con `[verified]` solo con una nota que indica quién las verificó.
Las mediciones realizadas en nuestras propias máquinas se registran como fuentes `rig`, con su
configuración bajo `experiments/`.
2. **Estante interno.** Una vez que las afirmaciones de un tema que soportan una carga se mantienen, se integra
en una base de conocimientos en el repositorio de trabajo privado de readouts, o se añade a uno existente.
**La promoción es parte del cierre de un experimento** (el Director, 2026-10-09). Cuando
el resultado de un experimento se registra aquí, su actualización readouts-internal se realiza
en la misma sesión o en la siguiente, junto con sus gráficos. Nada permanece en el banco de pruebas
durante más de una semana. Las actualizaciones pequeñas y regulares son mejores que una grande. El
archivo README de un experimento registra su promoción como una línea debajo de su resultado:
"Promocionado: readouts-internal `<kb>` ola `<n>`, `<date>`", o por qué aún no.
3. **Estante público.** Una base de conocimientos se publica en el repositorio público readouts
cuando se añade a la lista de permisos de exportación.

`rnd readouts` busca en cada base de conocimiento readouts desde aquí, por lo que un asiento
llega a ambos almacenes. Primero, busque en el banco, luego en el estante y, a continuación, investigue la diferencia.

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
python -m rnd check                         # validate every file (exit 1 on errors)
python -m rnd sql "SELECT tier, count(*) FROM sources GROUP BY tier"
python -m rnd bump --note "what changed"  # micro version bump + CHANGELOG section
```

Cada comando de listado toma `--json` para los agentes. `rnd.cmd` (Windows) y `rnd.sh` (shells POSIX) son envoltorios delgados, por lo que el comando funciona desde cualquier directorio.

Para utilizar la herramienta desde otros proyectos, instálela desde PyPI:

```bash
pip install mcptoolshop-rnd
```

Eso instala el comando `rnd`, no la biblioteca: las entradas se encuentran en este repositorio. El comando encuentra una biblioteca en este orden: `--library DIR`, luego `$RND_ROOT` y, a continuación, la carpeta más cercana en o por encima del directorio actual que contenga `entries/` y `instruments/`. Fuera de una biblioteca, se detiene con `NO_LIBRARY`; solo `rnd readouts` funciona sin ella.

En Python, importe `mcptoolshop_rnd`: ese nombre siempre funciona. `rnd` se mantiene como un alias de compatibilidad, pero también existe un paquete PyPI no relacionado que se llama `rnd`, y si ambos están instalados, puede reemplazar el alias. El comando `rnd` y `python -m mcptoolshop_rnd` siguen funcionando de cualquier manera.

La biblioteca cambia a diario, por lo que las versiones tienen cinco segmentos, `MAJOR.MINOR.PATCH.MICRO.NANO`. Los tres primeros versionan la herramienta `rnd`; MICRO marca un cambio estructural en la biblioteca y NANO una actualización ordinaria. `rnd bump` aumenta el último segmento de forma predeterminada y escribe una sección de CHANGELOG a partir de los archivos modificados desde la última etiqueta, por lo que cada actualización obtiene su propia versión pequeña etiquetada.

Códigos de salida: `0` correcto · `1` archivos de biblioteca no válidos · `2` error de uso o no encontrado · `3` error en tiempo de ejecución (una herramienta externa o un error inesperado). Los errores imprimen un código, un mensaje y una pista; `--debug` añade el rastreo de la pila.

## Diseño

| Ruta. | Qué. | Quién edita. |
|------|------|-----------|
| `entries/YYYY/*.md` | Entradas de investigación: la fuente de la verdad. | Personas y agentes. |
| `experiments/<name>/` | Configuraciones, entradas fijas y recibos de resultados para las mediciones del equipo. | Personas y agentes. |
| `experiments/<name>/collect.json` | Registros recopilados de un repositorio de herramientas en confirmaciones fijas (`rnd collect`). | Personas. |
| `instruments/*.md` | Herramientas y protocolos del estudio que el asiento puede utilizar (`kind: instrument`). | Personas y agentes. |
| `catalogs/<name>/source.json` | De dónde proviene un catálogo. | Personas. |
| `catalogs/<name>/catalog.json` | Instantánea fija de `rnd catalog sync`. | Generado; nunca editar manualmente. |
| `catalogs/<name>/review.json` | Ajuste y notas del estudio por familia y artículo. | Personas. |
| `datapacks/<name>/spec.json` | Qué contiene un paquete de datos: incluir patrones glob, licencias, generadores, host. | Personas. |
| `datapacks/<name>/datapack.json` | Manifiesto de `rnd datapack build`: SHA-256 de cada archivo, licencias, confirmaciones. | Generado; nunca editar manualmente. |
| `datapacks/<name>/hosted.json` | Dónde aterrizó la carga (revisión del repositorio). | Después de una carga. |
| `mcptoolshop_rnd/` | La CLI. | Código. |
| `rnd/` | Alias de compatibilidad para `mcptoolshop_rnd`. | Código. |
| `rnd.db` | SQLite FTS5 índice, reconstruido automáticamente cuando cambian los archivos. | Generado; no está en git. |

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
- [verified] A checked statement. (via: what checked it, date)
## Sources
- [primary] https://… — publisher
```

- **Niveles de fuente:** `primary` (documentación del proveedor, artículos, repositorios), `secondary` (reseñas de buena reputación), `aggregator` (sitios de resumen, resultados de búsqueda de IA), `user` (proporcionado por una persona: diapositivas, notas), `rig` (medido en nuestras máquinas).
- **Confianza de la afirmación:** `unverified`, `verified`, `disputed`, `wrong`. Una afirmación `verified` o `wrong` debe indicar qué la verificó con `(via: …)`.
- `[[entry-id]]` vincula las entradas; `rnd show` enumera los enlaces inversos.

## Paquetes de datos

Los datos procesados que son demasiado grandes o voluminosos para la clonación se ofrecen como un **paquete de datos**: los bytes se encuentran en un repositorio de conjuntos de datos de Hugging Face (privado hasta que se publica), y la biblioteca solo mantiene un manifiesto pequeño. El modelo de integridad proviene de [research-packs](https://github.com/mcp-tool-shop-org/research-packs): un manifiesto, un SHA-256 para cada archivo, una verificación de un solo comando y un listado.

```bash
rnd datapack build natural-errors --source experiments/natural-errors  # reads datapacks/natural-errors/spec.json
rnd datapack list
hf download mcp-tool-shop/rnd-natural-errors --repo-type dataset --local-dir ne
rnd datapack verify natural-errors --copy ne/files                      # PASS when every byte matches
```

- **Cada archivo necesita una licencia** en las especificaciones. Las salidas del modelo llevan los términos de su modelo (por
ejemplo, "Creado con Llama" para las salidas de Llama 3.1). `rnd datapack build` rechaza un paquete que
deja un archivo sin cubrir.
- **Cada modelo generador está fijado** (resumen Ollama, revisión de HF o ID de modelo de API), con su función.
- **`rnd check` valida cada manifiesto** y falla si se edita manualmente.
- La carga incluye `datapack.json` junto con los archivos, para que cualquiera pueda verificar sin este repositorio:
`pip install mcptoolshop-rnd`.

## Registros de experimentos recopilados

Un repositorio de herramientas registra sus propias especificaciones y registros de ejecución pre-registrados (los comprobantes de interlock),
de la misma manera que cada repositorio registra su mapa de Atlas. La biblioteca publica solo una copia recortada de los
números, creada por `rnd collect` a partir del repositorio de herramientas en los commits fijados:

```bash
rnd collect                 # list the experiments that collect records
rnd collect e4b             # read each source with git show, trim it, write experiments/e4b/results/
rnd collect e4b --check     # recompute every output; exit 1 if any differs from the committed file
```

- **`experiments/<name>/collect.json`** nombra el repositorio, el clon hermano del que se lee (`--clone` anula), y cada fuente: su ruta, el commit, el SHA-256 de sus bytes, la salida y la función de recorte en el `extract.py` del experimento.
- **Una fuente fijada nunca cambia.** Los bytes que ya no coinciden con la fijación se rechazan.
- **Cada registro lleva información de procedencia:** el repositorio, la ruta de la fuente y el SHA-256 de los bytes recortados.
- **Cada salida es segura para el público antes de ser escrita.** No sobrevive ninguna ruta de máquina, directorio de inicio o campo de entorno, y un módulo de experimento puede agregar una protección más estricta. No se escribe nada en caso de rechazo.

## Evaluación de una herramienta antes de una prueba

`rnd probe <url> …` responde a las primeras preguntas sobre una herramienta o modelo a partir de la propia API de cada fuente, no a partir de un resumen de una página web:

- **GitHub** (a través de `gh api`, por lo que utiliza su inicio de sesión GitHub CLI): la licencia, si está archivada,
la última actualización, la última versión y una búsqueda de código para "telemetría". Un resultado es una pista para leer, nunca una prueba;
cero resultados tampoco son una prueba.
- **Hugging Face:** la etiqueta de la licencia, o para "otro", el nombre y el enlace de la licencia de la tarjeta; control de acceso; la última modificación.
- **PyPI y npm:** la licencia, la última versión y la fecha de publicación.
- **rnd en sí:** una búsqueda exacta de la palabra para el nombre, para que sepa si la biblioteca ya lo contiene.

Una fuente a la que no se puede acceder se informa como desconocida, junto con el motivo.

## Supervisión de fuentes

`rnd watch` comprueba las fuentes en [docs/watchlist.json](docs/watchlist.json) e informa de lo que es nuevo desde la última comprobación:

- El blog técnico de NVIDIA;
- la versión del conjunto de herramientas CUDA;
- los nuevos modelos de Hugging Face de NVIDIA;
- el catálogo de habilidades de NVIDIA;
- las versiones de los motores y las herramientas que utiliza el estudio, como Ollama, OpenVINO, PyTorch, ComfyUI y Claude Code.

```bash
python -m rnd watch                  # what's new; records what it saw
python -m rnd watch --no-save --json # look without recording
python -m rnd watch --only ollama    # one source
```

Lo que se ha visto se guarda en un archivo de estado fuera del repositorio (`$RND_WATCH_STATE`, de lo contrario `~/.rnd/watch-state.json`). La primera comprobación de una fuente es una línea de base: registra los elementos actuales e informa de que no hay ninguno de nuevo. Una versión preliminar nunca se informa como la última versión de una fuente; se muestra una versión más reciente junto a ella. Las notas de la versión GitHub y los mensajes de commit se guardan en la salida JSON, para que el lector no tenga que buscar cada página. Una fuente a la que no se puede acceder se informa como desconocida, y su estado se deja intacto para que no se omita nada en silencio.

El comando es la mitad determinista de un ritual semanal (Director, 2026-10-13). Un explorador lee los nuevos elementos, evalúa cualquier herramienta candidata con `rnd probe`, comprueba la biblioteca con `rnd search --exact` y escribe un breve informe clasificado: qué archivar, qué probar y qué omitir. Agrega una fuente mediante una solicitud de extracción y explica por qué es importante.

## Relación con otras herramientas del estudio

- **readouts** es el estante verificado al que alimenta este banco (ver arriba).
- **research-os** construye un paquete de evidencia congelado y con control de acceso para un tema. Un tema en el que
depende una decisión puede pasar a ser un paquete research-os, enlazado desde la entrada.
- **repo-knowledge** indexa los repositorios propios del estudio; esta biblioteca cubre
el conocimiento de fuera de ellos.
- Los resultados recopilados durante el diseño de algo también pertenecen aquí, para que sobrevivan
a la sesión que los produjo.

Consulta `python -m rnd tools` para obtener el registro completo de instrumentos y [docs/standards.md](docs/standards.md) para ver cómo se evalúa el flujo de trabajo en comparación con los estándares de flujo de trabajo del estudio.

## Seguridad y confianza

- **Datos modificados:** archivos dentro de este repositorio (`entries/`, `instruments/`,
`catalogs/`, `experiments/`) y el índice `rnd.db`, que reconstruye. `rnd
readouts` opens the readouts knowledge bases **read-only**. `rnd sql` se ejecuta
contra una conexión de solo lectura.
- **Datos no modificados:** nada fuera del repositorio y el readouts.
No almacena ni lee ninguna credencial.
- **Red:** ninguna, excepto `rnd catalog sync`, que llama a la API GitHub
a través de su propio inicio de sesión `gh` CLI cuando la ejecuta.
- **Permisos:** acceso normal a archivos. Ningún derecho elevado, ningún servicio en segundo plano.
- **Sin telemetría.** No se recopila ni se envía nada.
- **Higiene del repositorio público:** antes de cada actualización, el árbol se analiza en busca de
rutas del directorio de inicio y la identidad del operador.

Informa de las vulnerabilidades según se describe en [SECURITY.md](SECURITY.md).

## Pruebas

```bash
bash verify.sh                               # tests, library check, index build, smoke
python -m unittest discover -s tests -t .    # tests only
```

## Estado y licencia

Mantenido por el estudio y en uso diario. Código: [MIT](LICENSE). Entradas: CC BY 4.0. El espejo de habilidades de NVIDIA en `catalogs/nvidia-skills/catalog.json` reproduce los nombres y las descripciones de las habilidades de [NVIDIA/skills](https://github.com/NVIDIA/skills) bajo las licencias de ese proyecto (Apache-2.0 para el código, CC-BY-4.0 para el texto de las habilidades).

---

<p align="center">Built by <a href="https://mcp-tool-shop.github.io/">MCP Tool Shop</a></p>
