<p align="center">
  <a href="README.ja.md">日本語</a> | <a href="README.zh.md">中文</a> | <a href="README.es.md">Español</a> | <a href="README.fr.md">Français</a> | <a href="README.hi.md">हिन्दी</a> | <a href="README.md">English</a> | <a href="README.pt-BR.md">Português (BR)</a>
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

La banca dati di ricerca dello studio. I risultati provenienti da qualsiasi ambito vengono inseriti rapidamente come brevi voci in formato Markdown, con ogni fonte contrassegnata e ogni affermazione indicata come verificata o meno. Gli esperimenti sono affiancati alle voci che li riguardano. I cataloghi esterni vengono replicati e valutati, e un registro elenca gli strumenti dello studio che possono essere utilizzati per la ricerca. Un singolo comando consente di effettuare una ricerca su tutti questi dati.

## Dove si trova: la "panchina" prima di readouts

Due archivi contengono le conoscenze dello studio e svolgono funzioni diverse.

| | Ricerca e sviluppo (questo repository). | [readouts](https://github.com/mcp-tool-shop-org/readouts) |
|---|---|---|
| Ruolo. | La banca dati: acquisizione dati, esperimenti, domande aperte. | La libreria: basi di conoscenza verificate. |
| Ritmo. | Una voce viene inserita in pochi minuti, le affermazioni iniziano con `unverified`. | Creata e verificata da gruppi di studio. |
| Formato. | Voci in formato Markdown, un argomento per ciascuna. | Una base di conoscenza SQLite per dominio. |
| Quanto è disordinato. | Disordinato intenzionalmente: le affermazioni contestate, i vicoli ciechi e i risultati intermedi rimangono visibili. | Per niente disordinato: ogni riga è corredata di fonte e verificata. |

La conoscenza si muove in una sola direzione:

1. **Area di test.** Un risultato viene inserito qui come voce. Le sue affermazioni iniziano con `[unverified]` e sono contrassegnate con `[verified]`, con una semplice nota che indica chi le ha verificate. Le misurazioni effettuate sulle nostre macchine vengono inserite come fonti `rig`, con la relativa configurazione sotto `experiments/`.
2. **Area interna.** Una volta che le affermazioni principali di un argomento si dimostrano valide, vengono integrate in una base di conoscenza nel repository di lavoro privato readouts, oppure vengono aggiunte a un repository esistente. **La promozione fa parte della conclusione di un esperimento** (il Direttore, 2026-10-09). Quando il risultato di un esperimento viene registrato qui, il relativo aggiornamento readouts-internal viene eseguito nella stessa sessione o in quella successiva, insieme ai relativi grafici. Nessun elemento rimane nell'area di test per più di una settimana. Aggiornamenti piccoli e regolari sono preferibili a un singolo aggiornamento importante. Il file README di un esperimento registra la sua promozione come una riga sotto il suo risultato: "Promosso: readouts-internal `<kb>` onda `<n>`, `<date>`", oppure indica il motivo per cui non è ancora stato promosso.
3. **Area pubblica.** Una base di conoscenza viene pubblicata nel repository pubblico readouts quando viene aggiunta alla lista di esportazione consentita.

`rnd readouts` esegue la ricerca in ogni base di conoscenza readouts da qui, quindi un singolo elemento
consente l'accesso a entrambi gli archivi. Cerca prima sulla panchina, poi sullo scaffale e infine analizza le differenze.

La ricerca qui non è limitata ai soli ambiti dello studio. Ogni voce registra separatamente due elementi: cosa rappresenta la conoscenza e cosa significa per lo studio (`relevance: act | watch | reference`). `reference` è un giudizio positivo.

## Come utilizzarlo

Richiede Python 3.10 o versioni successive e nient'altro (solo la libreria standard). Funziona su Windows, macOS e Linux. Dalla directory principale del repository:

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

Ogni comando di elenco richiede `--json` per gli agenti. `rnd.cmd` (Windows) e `rnd.sh` (shell POSIX) sono semplici wrapper, quindi il comando funziona da qualsiasi directory.

Per utilizzare lo strumento da altri progetti, installarlo da PyPI:

```bash
pip install mcptoolshop-rnd
```

Questo installa il comando `rnd`, non la libreria: le voci sono contenute in questo repository. Il comando individua una libreria in questo ordine: `--library DIR`, quindi `$RND_ROOT`, quindi la cartella più vicina, a partire dalla directory corrente o superiore, che contiene `entries/` e `instruments/`. Al di fuori di una libreria, il programma si interrompe con `NO_LIBRARY`; solo `rnd readouts` funziona senza una libreria.

In Python, importare `mcptoolshop_rnd`: questo nome funziona sempre. `rnd` viene mantenuto come alias di compatibilità, ma un pacchetto PyPI non correlato ha anche il nome `rnd` e, se entrambi sono installati, può sostituire l'alias. Il comando `rnd` e `python -m mcptoolshop_rnd` continuano a funzionare in entrambi i casi.

La libreria cambia quotidianamente, quindi le versioni hanno cinque segmenti, `MAJOR.MINOR.PATCH.MICRO.NANO`. I primi tre segmenti definiscono la versione dello strumento `rnd`; MICRO indica una modifica strutturale della libreria e NANO un aggiornamento ordinario. `rnd bump` incrementa l'ultimo segmento per impostazione predefinita e scrive una sezione CHANGELOG dai file modificati dall'ultimo tag, in modo che ogni aggiornamento abbia la propria piccola versione con tag.

Codici di uscita: `0` ok · `1` file della libreria non validi · `2` errore di utilizzo o non trovato · `3` errore di runtime (uno strumento esterno o un errore imprevisto). Gli errori stampano un codice, un messaggio e un suggerimento; `--debug` aggiunge il traceback.

## Layout

| Percorso. | Cosa. | Chi modifica. |
|------|------|-----------|
| `entries/YYYY/*.md` | Voci di ricerca: la fonte di verità. | Persone e agenti. |
| `experiments/<name>/` | Strumenti, input fissati e ricevute dei risultati per le misurazioni effettuate con gli strumenti. | Persone e agenti. |
| `experiments/<name>/collect.json` | Record raccolti da un repository di strumenti a commit fissi (`rnd collect`). | Persone. |
| `instruments/*.md` | Strumenti e protocolli dello studio che la banca dati può utilizzare (`kind: instrument`). | Persone e agenti. |
| `catalogs/<name>/source.json` | Da dove proviene un catalogo. | Persone. |
| `catalogs/<name>/catalog.json` | Snapshot fissato da `rnd catalog sync`. | Generato; non modificare manualmente. |
| `catalogs/<name>/review.json` | Adattamento e note dello studio per famiglia e articolo. | Persone. |
| `datapacks/<name>/spec.json` | Cosa contiene un pacchetto di dati: includere modelli glob, licenze, generatori, host. | Persone. |
| `datapacks/<name>/datapack.json` | Manifesto da `rnd datapack build`: SHA-256 di ogni file, licenze, fissaggi. | Generato; non modificare manualmente. |
| `datapacks/<name>/hosted.json` | Dove è stato caricato (revisione del repository). | Dopo un caricamento. |
| `mcptoolshop_rnd/` | La CLI. | Codice. |
| `rnd/` | Alias di compatibilità per `mcptoolshop_rnd`. | Codice. |
| `rnd.db` | SQLite FTS5 indice, ricostruito automaticamente quando i file cambiano. | Generato; non presente in git. |

## Formato delle voci

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

- **Livelli di fonte:** `primary` (documentazione del fornitore, articoli, repository), `secondary` (recensioni autorevoli), `aggregator` (siti di riepilogo, risultati di ricerca AI), `user` (fornito da una persona: diapositive, note), `rig` (misurato sulle nostre macchine).
- **Affidabilità dell'affermazione:** `unverified`, `verified`, `disputed`, `wrong`. Un'affermazione `verified` o `wrong` deve indicare cosa l'ha verificata con `(via: …)`.
- `[[entry-id]]` collega le voci; `rnd show` elenca i collegamenti in entrata.

## Pacchetti di dati

I dati elaborati troppo grandi o troppo ingombranti per essere inclusi nel clone vengono offerti come **pacchetto di dati**: i byte sono archiviati in un repository di set di dati di Hugging Face (privato fino alla pubblicazione) e la libreria mantiene solo un piccolo manifesto. Il modello di integrità deriva da [research-packs](https://github.com/mcp-tool-shop-org/research-packs): un manifesto, un SHA-256 per ogni file, una verifica con un solo comando e un elenco.

```bash
rnd datapack build natural-errors --source experiments/natural-errors  # reads datapacks/natural-errors/spec.json
rnd datapack list
hf download mcp-tool-shop/rnd-natural-errors --repo-type dataset --local-dir ne
rnd datapack verify natural-errors --copy ne/files                      # PASS when every byte matches
```

- **Ogni file deve avere una licenza** nelle specifiche. Gli output del modello includono i termini del modello (ad
esempio, "Creato con Llama" per gli output di Llama 3.1). `rnd datapack build` rifiuta un pacchetto che
lascia un file senza licenza.
- **Ogni modello di generazione è fissato** (hash Ollama, revisione HF o ID del modello API), con il suo ruolo.
- **`rnd check` convalida ogni manifesto** e fallisce se questo è stato modificato manualmente.
- L'upload include `datapack.json` insieme ai file, in modo che chiunque possa verificarlo senza questo repository:
`pip install mcptoolshop-rnd`.

## Registrazioni degli esperimenti raccolte

Un repository di strumenti registra le proprie specifiche e i record di esecuzione preregistrati (le ricevute di interlock),
proprio come ogni repository registra la sua mappa Atlas. La libreria pubblica solo una copia ridotta dei
dati, creata da `rnd collect` a partire dal repository di strumenti in corrispondenza di commit fissi:

```bash
rnd collect                 # list the experiments that collect records
rnd collect e4b             # read each source with git show, trim it, write experiments/e4b/results/
rnd collect e4b --check     # recompute every output; exit 1 if any differs from the committed file
```

- **`experiments/<name>/collect.json`** indica il nome del repository, il clone fratello da cui legge (`--clone` sovrascrive), e ogni sorgente: il suo percorso, il commit, il SHA-256 dei suoi byte, l'output e la funzione di riduzione nell'`extract.py` dell'esperimento.
- **Una sorgente fissata non cambia mai.** I byte che non corrispondono più al valore di hash del riferimento vengono rifiutati.
- **Ogni registrazione contiene informazioni sulla provenienza:** il repository, il percorso della sorgente e il SHA-256 dei byte ridotti.
- **Ogni output è sicuro per l'uso pubblico prima di essere scritto.** Nessun percorso di macchina, directory home o campo di ambiente viene conservato e un modulo di un esperimento può aggiungere una protezione più rigorosa. Nulla viene scritto in caso di rifiuto.

## Verifica di uno strumento prima di un test

`rnd probe <url> …` risponde alle prime domande su uno strumento o un modello, utilizzando l'API di ciascuna sorgente, e non da un riepilogo di una pagina web:

- **GitHub** (tramite `gh api`, quindi utilizza il tuo login GitHub CLI): la licenza, se è archiviato, l'ultimo aggiornamento, l'ultima versione e una ricerca del codice per "telemetria". Un risultato positivo è un indizio da approfondire, non una prova; l'assenza di risultati non è una prova.
- **Hugging Face:** il tag della licenza, oppure, per "altro", il nome e il link della licenza presenti nella scheda; restrizioni; l'ultima modifica.
- **PyPI e npm:** la licenza, l'ultima versione e la data di pubblicazione.
- **rnd stesso:** una ricerca esatta della parola per il nome, in modo da sapere se la libreria lo contiene già.

Una sorgente a cui non è possibile accedere viene segnalata come sconosciuta, con la relativa motivazione.

## Monitoraggio delle sorgenti

`rnd watch` controlla le sorgenti in [docs/watchlist.json](docs/watchlist.json) e segnala cosa è cambiato dall'ultimo controllo:

- Il blog tecnico di NVIDIA;
- la versione del toolkit CUDA;
- i nuovi modelli di NVIDIA su Hugging Face;
- il catalogo delle competenze di NVIDIA;
- le versioni dei motori e degli strumenti utilizzati dallo studio, come Ollama, OpenVINO, PyTorch, ComfyUI e Claude Code.

```bash
python -m rnd watch                  # what's new; records what it saw
python -m rnd watch --no-save --json # look without recording
python -m rnd watch --only ollama    # one source
```

What it saw is kept in a state file outside the repository (`$RND_WATCH_STATE`, else `~/.rnd/watch-state.json`).
A source's first check is a baseline: it records the current items and reports none as new. A pre-release is never reported as a source's latest version; a newer one is shown beside it. GitHub release notes and commit messages are kept in the JSON output, so a reader doesn't have to fetch each page. A source that
can't be reached is reported as unknown, and its state is left alone so nothing is skipped silently.

Il comando rappresenta la metà deterministica di un rituale settimanale (Director, 2026-10-13). Un addetto alla ricerca esamina i nuovi elementi, verifica eventuali strumenti candidati con `rnd probe`, controlla la libreria con `rnd search --exact` e scrive un breve rapporto classificato: cosa archiviare, cosa provare e cosa ignorare. Aggiungi una sorgente tramite una richiesta di pull e spiega perché è importante.

## Relazione con altri strumenti dello studio

- **readouts** è lo scaffale verificato a cui questa panchina fornisce dati (vedere sopra).
- **research-os** crea un pacchetto di prove protetto e congelato per un singolo argomento. Un argomento su cui
dipende una decisione può essere promosso a un pacchetto research-os, collegato alla voce.
- **repo-knowledge** indicizza i repository dello studio; questa libreria copre
le conoscenze provenienti dall'esterno.
- I risultati raccolti durante la progettazione di qualcosa appartengono anche qui, in modo che sopravvivano
alla sessione che li ha prodotti.

Consulta `python -m rnd tools` per il registro completo degli strumenti e [docs/standards.md](docs/standards.md) per vedere come il flusso di lavoro si confronta con gli standard di flusso di lavoro dello studio.

## Sicurezza e affidabilità

- **Dati interessati:** file all'interno di questo repository (`entries/`, `instruments/`,
`catalogs/`, `experiments/`) e l'indice `rnd.db`, che ricostruisce. `rnd
readouts` opens the readouts knowledge bases **read-only**. `rnd sql` viene eseguito
su una connessione di sola lettura.
- **Dati non interessati:** nulla al di fuori del repository e del checkout readouts.
Non memorizza credenziali e non ne legge.
- **Rete:** nessuna, tranne `rnd catalog sync`, che chiama l'API GitHub
tramite il tuo accesso CLI `gh` quando la esegui.
- **Autorizzazioni:** accesso ordinario ai file. Nessun diritto elevato, nessun servizio in background.
- **Nessuna telemetria.** Nulla viene raccolto o inviato.
- **Igiene del repository pubblico:** prima di ogni push, l'albero viene scansionato alla ricerca di
percorsi della directory home e dell'identità dell'operatore.

Segnala le vulnerabilità come descritto in [SECURITY.md](SECURITY.md).

## Test

```bash
bash verify.sh                               # tests, library check, index build, smoke
python -m unittest discover -s tests -t .    # tests only
```

## Stato e licenza

Manutenuto dallo studio e utilizzato quotidianamente. Codice: [MIT](LICENSE). Voci: CC BY 4.0. Lo specchio delle competenze NVIDIA in `catalogs/nvidia-skills/catalog.json` riproduce i nomi e le descrizioni delle competenze da [NVIDIA/skills](https://github.com/NVIDIA/skills) in base alle licenze di quel progetto (Apache-2.0 per il codice, CC-BY-4.0 per il testo delle competenze).

---

<p align="center">Built by <a href="https://mcp-tool-shop.github.io/">MCP Tool Shop</a></p>
