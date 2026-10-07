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

## Dónde se encuentra: el banco, antes de las lecturas

Dos almacenes contienen el conocimiento del estudio, y realizan diferentes funciones.

| | Investigación y desarrollo (este repositorio). | [readouts](https://github.com/mcp-tool-shop-org/readouts) |
|---|---|---|
| Función. | El banco: recopilación, experimentos, preguntas abiertas. | El estante: bases de conocimiento verificadas. |
| Ritmo. | Una entrada en minutos, las afirmaciones comienzan en `unverified`. | Creado y verificado por grupos de estudio. |
| Forma. | Entradas en Markdown, un tema por cada una. | Una base de conocimiento SQLite por dominio. |
| Qué desordenado. | desorden intencionado: las afirmaciones controvertidas, los callejones sin salida y los resultados provisionales permanecen visibles. | nada desordenado: cada dato está documentado y verificado. |

El conocimiento se mueve en una sola dirección:

1. **Banco.** Un hallazgo llega aquí como una entrada. Sus afirmaciones comienzan en `[unverified]` y se marcan con `[verified]` solo con una nota de lo que lo verificó. Las mediciones realizadas en nuestras propias máquinas se incluyen como fuentes `rig`, con su configuración en `experiments/`.
2. **Estante interno.** Una vez que las afirmaciones fundamentales de un tema se mantienen, se construye en una base de conocimiento en el repositorio de trabajo privado de las lecturas, o se agrega a él.
3. **Estante público.** Una base de conocimiento se publica en el repositorio público de lecturas cuando se agrega a la lista de permisos de exportación.

`rnd readouts` busca en todas las bases de conocimiento de lecturas desde aquí, por lo que un asiento llega a ambos almacenes. Primero, busque en el banco, luego en el estante y, a continuación, investigue la brecha.

La investigación aquí no se limita a los campos del estudio. Cada entrada registra dos cosas por separado: cuál es el conocimiento y qué significa para el estudio (`relevance: act | watch | reference`). `reference` es un buen veredicto.

## Úselo

Requiere Python 3.10 o posterior y nada más (solo la biblioteca estándar). Se ejecuta en Windows, macOS y Linux. Desde la raíz del repositorio:

```bash
python -m rnd search cuda graphs            # full-text over entries + catalogues
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

La biblioteca se actualiza diariamente, por lo que las versiones tienen cinco segmentos: `MAJOR.MINOR.PATCH.MICRO.NANO`. Las tres primeras versiones corresponden a la herramienta `rnd`; MICRO indica un cambio estructural en la biblioteca y NANO, una actualización ordinaria. `rnd bump` incrementa el último segmento de forma predeterminada y escribe una sección de CHANGELOG a partir de los archivos que se han modificado desde la última etiqueta, de modo que cada actualización obtiene su propia versión etiquetada.

Códigos de salida: `0` correcto · `1` archivos de biblioteca no válidos · `2` error de uso o no encontrado · `3` error en tiempo de ejecución (una herramienta externa o un error inesperado). Los errores imprimen un código, un mensaje y una pista; `--debug` agrega el rastreo de la pila.

## Disposición

| Ruta. | Qué. | Quién edita. |
|------|------|-----------|
| `entries/YYYY/*.md` | Entradas de investigación: la fuente de la verdad. | Personas y agentes. |
| `experiments/<name>/` | Configuraciones, entradas fijas y recibos de resultados para las mediciones del equipo. | Personas y agentes. |
| `instruments/*.md` | Herramientas y protocolos del estudio que el asiento puede utilizar (`kind: instrument`). | Personas y agentes. |
| `catalogs/<name>/source.json` | De dónde proviene un catálogo. | Personas. |
| `catalogs/<name>/catalog.json` | Instantánea fija de `rnd catalog sync`. | Generado; nunca editar manualmente. |
| `catalogs/<name>/review.json` | Ajuste y notas del estudio por familia y artículo. | Personas. |
| `rnd/` | La CLI. | Código. |
| `rnd.db` | Índice SQLite FTS5, reconstruido automáticamente cuando cambian los archivos. | Generado; no está en git. |

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

## Relación con otras herramientas del estudio

- **readouts** es el estante verificado al que alimenta este banco (véase arriba).
- **research-os** crea un paquete de evidencia congelado y con control de acceso para un tema. Un tema en el que depende una decisión puede pasar a ser un paquete de research-os, vinculado desde la entrada.
- **repo-knowledge** indexa los repositorios del estudio; esta biblioteca cubre el conocimiento de fuera de ellos.
- Los hallazgos recopilados durante el diseño de algo también pertenecen aquí, para que sobrevivan a la sesión que los produjo.

Consulte `python -m rnd tools` para obtener el registro completo de instrumentos y [docs/standards.md](docs/standards.md) para ver cómo el flujo de trabajo se califica según los estándares de flujo de trabajo del estudio.

## Seguridad y confianza

- **Datos afectados:** archivos dentro de este repositorio (`entries/`, `instruments/`, `catalogs/`, `experiments/`) y el índice `rnd.db`, que reconstruye. `rnd readouts` opens the readouts knowledge bases **read-only**. `rnd sql` se ejecuta contra una conexión de solo lectura.
- **Datos no afectados:** nada fuera del repositorio y la copia de seguridad de readouts. No almacena credenciales y no lee ninguna.
- **Red:** ninguna, excepto `rnd catalog sync`, que llama a la API de GitHub a través de su propio inicio de sesión de la CLI `gh` cuando lo ejecuta.
- **Permisos:** acceso normal a archivos. No se requieren derechos elevados ni servicios en segundo plano.
- **No hay telemetría.** No se recopila ni se envía nada.
- **Higiene del repositorio público:** antes de cada envío, el árbol se analiza en busca de rutas del directorio de inicio y la identidad del operador.

Informe de vulnerabilidades según se describe en [SECURITY.md](SECURITY.md).

## Pruebas

```bash
bash verify.sh                               # tests, library check, index build, smoke
python -m unittest discover -s tests -t .    # tests only
```

## Estado y licencia

Mantenido por el estudio y en uso diario. Código: [MIT](LICENSE). Entradas: CC BY 4.0. El espejo de habilidades de NVIDIA en `catalogs/nvidia-skills/catalog.json` reproduce los nombres y descripciones de las habilidades de [NVIDIA/skills](https://github.com/NVIDIA/skills) bajo las licencias de ese proyecto (Apache-2.0 para el código, CC-BY-4.0 para el texto de las habilidades).

---

<p align="center">Built by <a href="https://mcp-tool-shop.github.io/">MCP Tool Shop</a></p>
