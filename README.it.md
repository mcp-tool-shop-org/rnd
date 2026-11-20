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

Il banco di ricerca dello studio. Le scoperte provenienti da qualsiasi campo vengono inserite rapidamente come brevi voci in formato Markdown, con ogni fonte contrassegnata e ogni affermazione indicata come verificata o meno. Gli esperimenti sono affiancati alle voci che li riguardano. I cataloghi esterni vengono replicati e valutati, e un registro elenca gli strumenti dello studio che la ricerca può utilizzare. Un singolo comando consente di effettuare una ricerca su tutti gli elementi.

## Dove si trova: il banco prima di readouts

Due archivi contengono le conoscenze dello studio e svolgono funzioni diverse.

| | Ricerca e sviluppo (questo repository) | [readouts](https://github.com/mcp-tool-shop-org/readouts) |
|---|---|---|
| Ruolo | il banco: acquisizione, esperimenti, domande aperte | la scaffalatura: basi di conoscenza verificate |
| Ritmo | una voce in pochi minuti, le affermazioni iniziano con `unverified` | create e verificate da gruppi di studio |
| Forma | Voci in formato Markdown, un argomento per ciascuna | una base di conoscenza SQLite per dominio |
| Quanto è disordinato | disordinato intenzionalmente: le affermazioni contestate, i vicoli ciechi e i risultati intermedi rimangono visibili | per niente disordinato: ogni riga è corredata di fonte e verificata |

La conoscenza si muove in una sola direzione:

1. **Banco.** Una scoperta viene inserita qui come voce. Le sue affermazioni iniziano con `[unverified]` e vengono contrassegnate con `[verified]` solo con una nota che indica cosa le ha verificate. Le misurazioni effettuate sulle nostre macchine vengono inserite come fonti `rig`, con i relativi strumenti sotto `experiments/`.
2. **Scaffalatura interna.** Una volta che le affermazioni fondamentali di un argomento si dimostrano valide, vengono integrate in una base di conoscenza nel repository di lavoro privato readouts, oppure vengono aggiunte a una base esistente. **La promozione fa parte della conclusione di un esperimento** (il Direttore, 2026-10-09). Quando il risultato di un esperimento viene registrato qui, il relativo aggiornamento readouts-internal segue nella stessa sessione o in quella successiva, insieme ai relativi grafici. Nessun elemento rimane sul banco per più di circa una settimana. Aggiornamenti piccoli e regolari sono preferibili a un aggiornamento unico e corposo. Il file README di un esperimento registra la sua promozione come una riga sotto il relativo risultato: "Promosso: readouts-internal `<kb>` onda `<n>`, `<date>`", oppure perché non è ancora stato promosso.
3. **Scaffalatura pubblica.** Una base di conoscenza viene pubblicata nel repository pubblico readouts quando viene aggiunta alla lista di esportazione consentita.

`rnd readouts` esegue la ricerca su ogni base di conoscenza readouts da qui, quindi un singolo punto di accesso consente di accedere a entrambi gli archivi. Cerca prima sul banco, poi sulla scaffalatura e infine analizza le lacune.

La ricerca qui non è limitata ai soli campi dello studio. Ogni voce registra separatamente due elementi: cosa rappresenta la conoscenza e cosa significa per lo studio (`relevance: act | watch | reference`). `reference` è un giudizio valido.

## Come usarlo

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
python -m rnd new-question "Why does X happen?" --field audio
python -m rnd sync --check                  # verify numbers bound to experiments/<id>/results.json
python -m rnd check                         # validate every file (exit 1 on errors)
python -m rnd similar 2026-10-07-cuda-graphs --limit 3  # closest claims in other entries (read-only)
python -m rnd digest --since v1.1.24.0.14   # entries, claims and questions changed since a tag or date
python -m rnd sql "SELECT tier, count(*) FROM sources GROUP BY tier"
python -m rnd change "what changed"         # add a changelog fragment under changes/ (nano by default)
python -m rnd bump --note "release note"    # release PR: apply changes/ fragments, bump version + CHANGELOG
```

Ogni comando di elenco accetta `--json` per gli agenti. `rnd.cmd` (Windows) e `rnd.sh` (shell POSIX) sono semplici wrapper, quindi il comando funziona da qualsiasi directory.

Per utilizzare lo strumento da altri progetti, installalo da PyPI:

```bash
pip install mcptoolshop-rnd
```

Questo installa il comando `rnd`, non la libreria: le voci sono contenute in questo repository. Il comando cerca una libreria in questo ordine: `--library DIR`, quindi `$RND_ROOT`, quindi la cartella più vicina, a partire dalla directory corrente o superiore, che contiene `entries/` e `instruments/`. Al di fuori di una libreria, il programma si interrompe con `NO_LIBRARY`; solo `rnd readouts` funziona senza una libreria.

In Python, importa `mcptoolshop_rnd`: questo nome funziona sempre. `rnd` viene mantenuto come alias di compatibilità, ma un pacchetto PyPI non correlato ha anche il nome `rnd` e, se entrambi sono installati, può sostituire l'alias. Il comando `rnd` e `python -m mcptoolshop_rnd` continuano a funzionare in entrambi i casi.

La libreria cambia quotidianamente, quindi le versioni hanno cinque segmenti, `MAJOR.MINOR.PATCH.MICRO.NANO`. I primi tre segmenti definiscono la versione dello strumento `rnd`; MICRO indica una modifica strutturale della libreria e NANO un aggiornamento ordinario. Gli aggiornamenti ordinari aggiungono un frammento del registro delle modifiche sotto `changes/` tramite `rnd change`; al momento del rilascio, `rnd bump` elabora tutti i frammenti, sposta la versione di un livello in base al frammento più alto e scrive una sezione del registro delle modifiche.

Codici di uscita: `0` ok · `1` file della libreria non validi · `2` errore di utilizzo o non trovato · `3` errore di runtime (uno strumento esterno o un errore imprevisto). Gli errori stampano un codice, un messaggio e un suggerimento; `--debug` aggiunge il traceback.

## Layout

| Percorso | Cosa | Chi modifica |
|------|------|-----------|
| `entries/YYYY/*.md` | Voci di ricerca: la fonte di verità | persone e agenti |
| `questions/*.md` | Domande di ricerca aperte e risolte | persone e agenti |
| `changes/*.md` | Frammenti del registro delle modifiche non pubblicati (`rnd change`) | persone e agenti (`rnd bump` elabora) |
| `experiments/<name>/` | Strumenti, input fissati, `results.json` e ricevute dei risultati | persone e agenti |
| `experiments/<name>/collect.json` | Record raccolti da un repository di strumenti a commit fissati (`rnd collect`) | persone |
| `instruments/*.md` | Strumenti e protocolli dello studio che il sistema può utilizzare (`kind: instrument`) | Solo per il sistema di R&S (diff revisionato) |
| `catalogs/<name>/source.json` | Da dove proviene un catalogo | persone |
| `catalogs/<name>/catalog.json` | Snapshot fissato da `rnd catalog sync` | generato; non modificare manualmente |
| `catalogs/<name>/review.json` | Adattamento e note dello studio per famiglia e elemento | persone |
| `datapacks/<name>/spec.json` | Cosa contiene un pacchetto di dati: includi modelli glob, licenze, generatori, host | persone |
| `datapacks/<name>/datapack.json` | Manifest da `rnd datapack build`: SHA-256 di ogni file, licenze, fissaggi | generato; non modificare manualmente |
| `datapacks/<name>/hosted.json` | Dove è stato caricato (revisione del repository) | dopo un caricamento |
| `mcptoolshop_rnd/` | L'interfaccia a riga di comando | codice |
| `rnd/` | Alias di compatibilità per `mcptoolshop_rnd` | codice |
| `rnd.db` | SQLite FTS5 indice, ricostruito automaticamente quando i file cambiano | generato; non presente in git |
| `rnd.misses.jsonl` | Registro di ricerca locale a zero hit accanto a `rnd.db` (`RND_NO_USAGE=1` disabilita) | generato; non presente in git |

## Formato della voce

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

- **Livelli di origine:** `primary` (documentazione del fornitore, articoli, repository), `secondary` (recensioni autorevoli), `aggregator` (siti di riepilogo, output di ricerca AI), `user` (fornito da una persona: diapositive, note), `rig` (misurato sulle nostre macchine).
- **Affidabilità dell'affermazione:** `unverified`, `verified`, `disputed`, `wrong`, `superseded`. Un'affermazione `verified` o `wrong` deve indicare cosa l'ha verificata con `(via: …)`.
- `[[entry-id]]` collega le voci; `rnd show` elenca i collegamenti in entrata.

## Frammenti del registro delle modifiche

Gli aggiornamenti non modificano direttamente `mcptoolshop_rnd/__init__.py` o `CHANGELOG.md`, quindi
i rami paralleli non entrano mai in conflitto sulla linea delle versioni:

```bash
python -m rnd change "Add study of XYZ"                # writes changes/YYYY-MM-DD-<hex>-<slug>.md (level: nano)
python -m rnd change "New tool feature" --level minor  # levels: nano | micro | patch | minor | major
python -m rnd bump --dry-run                           # preview version bump from changes/ fragments
python -m rnd bump                                     # release PR: bump once, update CHANGELOG.md, delete fragments
```

In assenza di file in `changes/`, `rnd bump [nano|micro|…] [--note …]` mantiene il suo
comportamento git-diff. Sia `__init__.py` che `CHANGELOG.md` vengono preparati tramite
file temporanei e sostituiti con `os.replace`, ripristinando `__init__.py` se la
sostituzione del CHANGELOG fallisce. Se un errore lascia `__init__.py` in anticipo rispetto a `CHANGELOG.md`,
rieseguendo al livello corrispondente si completa l'aggiornamento e qualsiasi altro livello
rifiuta con `BAD_CHANGELOG`. Rimane un'unica lacuna: un errore dopo che entrambi i file sono
stati sostituiti, ma prima che i frammenti in `changes/` vengano eliminati, li lascia in
posizione e una riesecuzione li aggiornerebbe una seconda volta, quindi elimina prima quei frammenti manualmente. `rnd check` segnala qualsiasi
frammento malformato come errore.

## Numeri vincolati

Un esperimento può mantenere numeri di riepilogo sicuri per il pubblico in
`experiments/<id>/results.json` e associare numeri alle voci, ai riassunti o alle
note dell'esperimento immediatamente dopo il letterale:

```markdown
The judge scored 84.2%<!-- rnd:experiments/e4b/results.json#accuracy:.1% --> on the held-out split.
```

- Markdown grezzo, `grep` e l'indice SQLite mantengono il letterale semplice (`84.2%`);
GitHub e Starlight rendono `84.2%` senza alcun marcatore o collegamento visibile.
- `rnd sync [paths…]` riscrive i letterali vincolati da `results.json` utilizzando la
  specifica di formato Python; `rnd sync --check` esce con codice `1` senza scrivere se un
  letterale è diverso.
- `rnd check` tratta qualsiasi letterale vincolato non sincronizzato, file mancante o chiave mancante
come un errore e avvisa su `[verified]` quando `(via: …)` fa riferimento a un esperimento del repository
mentre contiene ancora numeri non vincolati, ignorando i numeri interi semplici (senza
punto decimale, segno di percentuale, separatore delle migliaia o unità finale) che
si associano alla parola precedente nel titolo o nei tag della voce o seguono
`RTX` o `GTX` (3-4 cifre) o `CUDA`, `PTX`, `Gemma`, `Llama`, `Qwen`,
`Claude`, `GPT` o `Phi` (1-2 cifre).

## ID e collegamenti delle affermazioni

Le affermazioni possono contenere ID `c-<hex>` stabili e deterministici e relazioni esplicite
(`supersedes`, `contradicts`, `supports`) con affermazioni precedenti tramite ID:

```bash
python -m rnd claims                               # list indexed claims (--state superseded, --json)
python -m rnd claims assign <entry>                # add deterministic c-<hex> ids to one entry's claims
python -m rnd similar <entry> [--limit 5]          # closest claims in other entries (read-only)
python -m rnd reconcile <entry>                    # mark older claims (superseded / disputed / supported-by)
```

`rnd similar <entry>` esegue una query SQLite FTS5 BM25 in sola lettura su `claims_fts`
per ogni affermazione di `<entry>` rispetto ad altre voci (`--limit` ha un valore predefinito di 5),
evidenzia le corrispondenze di `superseded` o `disputed` con ciò che le ha sostituite o contraddette,
stampa le clausole esatte `(supersedes: id)` / `(contradicts: id)` / `(supports: id)`
e il comando `rnd reconcile <entry>` e non scrive mai `rnd.db` o alcuna
voce. `rnd reconcile <entry>` scrive solo l'ID (se mancante), lo stato aggiornato e
la relazione inversa (`superseded-by`, `contradicted-by`, `supported-by`) sulla
riga dell'affermazione più vecchia nel suo file, senza toccare la sua frase o qualsiasi altra
riga (lasciando un'affermazione `[wrong]` `[wrong]` quando contraddetta). Sia
`rnd claims assign` che `rnd reconcile` rifiutano (`MULTIPLE_CLAIMS_HEADINGS`)
senza scrivere se una voce contiene più di un'intestazione reale `## Claims`.
`rnd check` segnala errori sugli ID di destinazione non validi, sui collegamenti a senso unico (suggerendo di eseguire
`rnd reconcile` o di rimuovere la clausola e ripristinare uno stato `superseded` o `disputed`) o su un blocco di codice non chiuso,
e avvisa su un'affermazione `[superseded]` senza un collegamento `(superseded-by: …)`.
`rnd search` e `rnd show` contrassegnano le affermazioni `superseded` e `disputed` e indicano
l'affermazione che le ha sostituite o contraddette.

## Cosa è cambiato (digest)

`rnd digest --since <git ref or YYYY-MM-DD> [--json]` confronta la libreria in un
commit precedente (analizzato dagli oggetti git in memoria senza toccare l'area di lavoro, l'indice git, `rnd.db` o i file temporanei) con l'albero corrente:

```bash
python -m rnd digest --since v1.1.24.0.14
python -m rnd digest --since 2026-11-19 --json
```

Segnala le voci aggiunte, le affermazioni aggiunte, le affermazioni rimosse, le modifiche allo stato delle affermazioni
(`old_state -> new_state` con ciò che le ha sostituite o contraddette) e
le domande aperte, a cui è stato dato una risposta (con gli ID delle affermazioni che rispondono) e messe in pausa, insieme ai
conteggi. Una data `YYYY-MM-DD` si risolve nell'ultimo commit lungo
la linea del primo genitore (`first-parent`) del ramo corrente (`HEAD`) la cui data del committer cade in quel giorno o in precedenza. Le affermazioni corrispondono per `id` quando entrambe le parti ne hanno una, altrimenti per
`(entry, exact text)`, quindi un'affermazione riformulata senza un ID appare come un'affermazione
rimossa e un'affermazione aggiunta, mai come una modifica di stato.

## Domande aperte

Le domande aperte sono memorizzate come file Markdown individuali in `questions/` con lo stato
`open`, `investigating`, `answered` o `parked`:

```bash
python -m rnd new-question "Does X hold on Y?" --field systems
python -m rnd questions --status open --json
```

Quando il campo `status` di una domanda è `answered`, la lista `answered_by` nel suo frontmatter
deve indicare almeno un ID di affermazione esistente; `rnd check` tratta una domanda `answered`
senza un ID di affermazione esistente come un errore. Le domande sono indicizzate in
`rnd.db` e restituite da `rnd search` e `rnd show`.

## Registro delle ricerche locali non riuscite

Quando `rnd search` non restituisce corrispondenze, aggiunge una riga JSON (`time` e
`query`) a un file `.misses.jsonl` locale accanto a `rnd.db` (`rnd.misses.jsonl` nella
directory principale del repository, ignorato da git; oppure `<stem>.misses.jsonl` accanto a `--db` / `RND_DB`,
quindi `--db foo.db` scrive `foo.misses.jsonl` accanto ad esso, non `foo.db.misses.jsonl`).
Nient'altro viene registrato, nulla viene mai inviato tramite la rete, `RND_NO_USAGE=1`
disattiva la registrazione e l'eliminazione del file lo rimuove completamente.
`rnd stats --usage` stampa il conteggio totale delle ricerche non riuscite e le query non riuscite più frequenti.

## File di strumentazione e funzionalità aggiuntive facoltative

- **File di strumentazione (`instruments/*.md`):** modificati solo dal team di ricerca e sviluppo in una
diff revisionata la cui descrizione elenca ogni file di strumentazione modificato, mai da un
passaggio o un comando che riassume contenuti esterni (`rnd watch`, `rnd probe`,
`rnd collect`, `rnd catalog sync`).
- **Dipendenze principali e funzionalità aggiuntive:** `rnd` mantiene la libreria principale solo con la libreria standard di Python.
Qualsiasi funzionalità aggiuntiva facoltativa si trova in un gruppo facoltativo ed è importata in modo lazy; un
comando che richiede una funzionalità aggiuntiva mancante fallisce con `MISSING_EXTRA` e un suggerimento per l'installazione.

## Pacchetti di dati

I dati elaborati troppo grandi o troppo ingombranti per essere inclusi nel clone vengono offerti come **pacchetto di dati**: i byte sono memorizzati
su un repository di set di dati di Hugging Face (privato fino alla pubblicazione) e la libreria mantiene solo un piccolo
manifest. Il modello di integrità deriva da
[research-packs](https://github.com/mcp-tool-shop-org/research-packs): un manifest, un SHA-256 per
ogni file, una verifica con un solo comando e un elenco.

```bash
rnd datapack build natural-errors --source experiments/natural-errors  # reads datapacks/natural-errors/spec.json
rnd datapack list
hf download mcp-tool-shop/rnd-natural-errors --repo-type dataset --local-dir ne
rnd datapack verify natural-errors --copy ne/files                      # PASS when every byte matches
```

- **Ogni file deve avere una licenza** nella specifica. Gli output del modello contengono i termini del modello (ad esempio, "Creato con Llama" per gli output di Llama 3.1). `rnd datapack build` rifiuta un pacchetto che
lascia un file senza una licenza.
- **Ogni modello di generazione è fissato** (digest Ollama, revisione HF o ID del modello API), con il suo ruolo.
- **`rnd check` convalida ogni manifest** e fallisce se è stato modificato manualmente.
- L'upload include `datapack.json` accanto ai file, in modo che chiunque possa verificarlo senza questo repository:
`pip install mcptoolshop-rnd`.

## Record di esperimenti raccolti

Un repository di strumenti esegue il commit delle proprie specifiche preregistrate e dei record di esecuzione (le ricevute di interlock),
come ogni repository esegue il commit della sua mappa di Atlas. La libreria pubblica solo una copia ridotta dei
numeri, creata da `rnd collect` dal repository di strumenti in commit fissati:

```bash
rnd collect                 # list the experiments that collect records
rnd collect e4b             # read each source with git show, trim it, write experiments/e4b/results/
rnd collect e4b --check     # recompute every output; exit 1 if any differs from the committed file
```

- **`experiments/<name>/collect.json`** indica il nome del repository e del clone da cui vengono letti i dati
(`--clone` sovrascrive), e per ogni sorgente: il percorso, il commit, la SHA-256 dei suoi byte,
l'output e la funzione di troncamento nell'`extract.py` dell'esperimento.
- **Una sorgente "fissa" non cambia mai.** I byte che non corrispondono più all'hash della "fissazione" vengono rifiutati.
- **Ogni record contiene informazioni sulla provenienza:** il repository, il percorso della sorgente e la SHA-256 dei
byte troncati.
- **Ogni output è sicuro prima di essere scritto.** Nessun percorso di macchina, directory home o
campo di ambiente viene conservato, e un modulo dell'esperimento può aggiungere una protezione più rigorosa. Nulla viene
scritto in caso di rifiuto.

## Verifica di uno strumento prima di un test

`rnd probe <url> …` risponde alle prime domande su uno strumento o modello, utilizzando l'API di ciascuna sorgente,
e non un riepilogo di una pagina web:

- **GitHub** (tramite `gh api`, quindi utilizza il tuo login GitHub CLI): la licenza, se è archiviato,
l'ultimo aggiornamento, l'ultima versione e una ricerca del codice per "telemetria". Un risultato positivo è un indizio da esaminare, mai una prova;
nessun risultato positivo non è comunque una prova.
- **Hugging Face:** il tag della licenza o, per "altro", il nome e il link della licenza nella scheda; restrizioni; l'ultima modifica.
- **PyPI e npm:** la licenza, l'ultima versione e la data di pubblicazione.
- **rnd stesso:** una ricerca esatta del nome, in modo da sapere se la libreria lo contiene già.

Una sorgente a cui non è possibile accedere viene segnalata come sconosciuta, indicando il motivo.

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

Ciò che viene rilevato viene memorizzato in un file di stato al di fuori del repository (`--state`, altrimenti `$RND_WATCH_STATE`, altrimenti `Path.home() / ".rnd" / "watch-state.json"`, `~/.rnd/watch-state.json`), a meno che non venga passato `--no-save`.
La prima verifica di una sorgente consiste in un confronto con una base di riferimento: registra gli elementi correnti e segnala che non ce ne sono di nuovi. Una versione preliminare non viene mai segnalata come l’ultima versione di una sorgente; se esiste una versione preliminare più recente, viene mostrata accanto all’ultima versione. Le note di rilascio GitHub e i messaggi di commit vengono conservati nell’output JSON, in modo che il lettore non debba recuperare ogni singola pagina. Una sorgente a cui non è possibile accedere viene segnalata come sconosciuta e il suo stato viene lasciato invariato, in modo che nulla venga omesso in silenzio.

Il comando rappresenta la metà deterministica di un rituale settimanale (Director, 2026-10-13). Un addetto alla ricerca esamina i nuovi elementi,
verifica qualsiasi strumento candidato con `rnd probe`, controlla la libreria con `rnd search --exact` e scrive un breve
rapporto classificato: cosa archiviare, cosa provare e cosa saltare. Aggiungi una sorgente tramite una richiesta di pull e spiega perché
è importante.

## Relazione con altri strumenti dello studio

- **readouts** è la scaffalatura verificata che questo banco alimenta (vedi sopra).
- **research-os** crea un pacchetto di evidenze "congelato" e protetto per un singolo argomento. Un argomento da cui
dipende una decisione può essere promosso a un pacchetto research-os, collegato dalla voce.
- **repo-knowledge** indicizza i repository dello studio; questa libreria copre
le conoscenze provenienti dall'esterno.
- Le informazioni raccolte durante la progettazione di qualcosa appartengono anche qui, in modo che sopravvivano
alla sessione che le ha prodotte.

Consulta `python -m rnd tools` per il registro completo degli strumenti e
[docs/standards.md](docs/standards.md) per capire come il flusso di lavoro si confronta con
gli standard del flusso di lavoro dello studio.

## Sicurezza e affidabilità

- **Dati scritti**, in base alla loro posizione:
- **All'interno di questo repository** (la libreria: `--library`, altrimenti `$RND_ROOT`, altrimenti la cartella più vicina alla directory di lavoro, o sopra di essa,
  che contiene `entries/` e `instruments/`, altrimenti la copia locale del repository da cui viene eseguito il pacchetto): `rnd new` (un nuovo file sotto `entries/` o `instruments/`, senza mai sovrascrivere), `rnd new-question` (`questions/`), `rnd new-experiment`,
  `rnd runs record` e `rnd collect <name>` (`experiments/<name>/`),
  `rnd claims assign`, `rnd reconcile` e `rnd sync` (righe delle affermazioni e numeri vincolati nei file Markdown esistenti), `rnd change` (`changes/`), `rnd bump`
  (`mcptoolshop_rnd/__init__.py` e `CHANGELOG.md`, tramite file temporanei
  accanto a ciascuno, e cancella i frammenti `changes/` che ha utilizzato),
  `rnd catalog sync` (`catalogs/<name>/catalog.json`), `rnd datapack build`
  (`datapacks/<name>/datapack.json`) e `rnd layout` (`docs/layout.json`).
- **L'indice:** `rnd.db`, o il percorso fornito da `--db` o `$RND_DB`, con un
file temporaneo `.db.tmp` accanto, durante la sua creazione. `rnd build` lo scrive,
e ogni comando che legge l'indice (`search`, `show`, `list`, `tools`,
`stats`, `catalog`, `claims`, `questions`, `sql`, `runs`, `ledger`, `where`,
`probe`) lo ricostruisce prima quando un file di origine è stato modificato. Il registro delle ricerche senza risultati `rnd.misses.jsonl` si trova accanto (vedere di seguito).
- **La cartella home:** `rnd watch` scrive il file degli elementi visualizzati in `--state`, altrimenti
`$RND_WATCH_STATE`, altrimenti `~/.rnd/watch-state.json` (creato nel codice come
`Path.home() / ".rnd" / "watch-state.json"`), dove rimane tra un'esecuzione e l'altra. Viene scritto tramite un file `.tmp` accanto.
`--no-save` salta la scrittura.
- **Gli archivi di dati grezzi, al di fuori di questo repository:** `rnd raw ingest`, `rnd raw private` e
`rnd raw relicense` scrivono nell'archivio pubblico (`--public`, altrimenti `$RND_DATA`,
altrimenti `../rnd-data`) e nell'archivio privato (`--private`, altrimenti `$RND_DATA_PRIVATE`, altrimenti `../rnd-data-private`
accanto alla libreria; quando `rnd raw` viene eseguito al di fuori di una libreria, `rnd-data-private`
accanto all'archivio pubblico). `rnd raw ingest` inserisce anche
ogni file di dimensioni superiori a 256 KB nell'archivio di blob, sotto `blobs/` nella cartella
denominata da `$RND_DATA_STORE_D` o dalla voce `"d"` dell'archivio pubblico
`store.local.json` (non esiste un valore predefinito; in assenza, l'importazione viene rifiutata). I blob vengono scritti tramite un file `.tmp` accanto e contrassegnati come di sola lettura. Con `--link`, un nuovo blob
è un collegamento fisico al file di origine, quindi **anche quel file di origine diventa di sola lettura** (un blob
già presente nell'archivio rimane invariato, così come il suo file di origine); senza `--link`,
l'origine non viene modificata. `rnd raw ingest --update` elimina nei due archivi i file piccoli precedenti di un'esecuzione prima di scrivere quelli nuovi. `--dry-run` non scrive nulla.
- **Lettura, mai scrittura:** `rnd readouts` (SQLite in modalità di sola lettura), i cloni di origine di `rnd collect` (`git show`), `rnd raw verify`, `rnd datapack verify --copy`,
  `rnd runs record --from`, `rnd abmine`, e `rnd similar` e `rnd digest`,
  che operano in memoria e non scrivono nulla da nessuna parte: nessun file temporaneo, nessuna
  modifica all'albero di lavoro, all'indice git o a `rnd.db`.
- **Codice eseguito:** `rnd collect <name>`, con o senza `--check`, carica ed esegue
  `experiments/<name>/extract.py` (o il modulo indicato dal file `collect.json` di quella cartella)
  dalla libreria (`mcptoolshop_rnd/collect.py:142-149`). Python potrebbe
memorizzare nella cache il bytecode di quel modulo in `experiments/<name>/__pycache__/`. `rnd` limita
ciò che scrive direttamente a `experiments/<name>/`; non limita ciò che fa il codice
del modulo stesso, quindi eseguirlo solo su una libreria di cui ci si fida.
- **Al di fuori del comando `rnd`:** il pacchetto include anche
`mcptoolshop_rnd.localbuilders`, l'impalcatura dell'esperimento local-builders. Nessun comando `rnd` lo esegue. Se eseguito direttamente (ad esempio
`python -m mcptoolshop_rnd.localbuilders.runner`), sulla macchina noleggiata per cui è stato scritto e in parte come root, crea, elimina e modifica il proprietario e i permessi dei file nei percorsi
passati dal chiamante (percorsi di lavoro, home, cronologia, ambiente virtuale, ricevuta, log,
report, cartella segreta e sonda di contenimento), e il suo valutatore utilizza una cartella temporanea nella cartella temporanea del sistema operativo, rimossa al termine.
- **Dati non toccati:** nessun comando `rnd` scrive, elimina o modifica un file
altrove. Non memorizza credenziali e non ne legge.
- **Rete:** nessuna, tranne `rnd catalog sync`, `rnd probe` e `rnd watch`,
che leggono metadati pubblici o chiamano l'API GitHub tramite la propria CLI `gh`
quando vengono eseguiti.
- **Permessi:** accesso ordinario ai file. Nessun comando `rnd` richiede privilegi elevati e non esiste alcun servizio in background.
- **Log di utilizzo solo locale:** nulla viene raccolto o inviato da nessuna parte. Quando `rnd search`
non restituisce corrispondenze, aggiunge una riga (ora UTC e query) a `rnd.misses.jsonl`
accanto a `rnd.db` (ignorato da Git nel repository; con `--db foo.db`, `foo.misses.jsonl`
accanto, non `foo.db.misses.jsonl`, e allo stesso modo per `$RND_DB`). Impostare
`RND_NO_USAGE=1` per disattivarlo e eliminare il file `.misses.jsonl` in qualsiasi momento per cancellarlo. Nessun altro dato di utilizzo viene registrato.
- **Igiene del repository pubblico:** prima di ogni push, l'albero viene scansionato alla ricerca di
percorsi della cartella home e dell'identità dell'operatore.

Segnala le vulnerabilità come descritto in [SECURITY.md](SECURITY.md).

## Test

```bash
bash verify.sh                               # tests, library check, index build, smoke
python -m unittest discover -s tests -t .    # tests only
```

## Stato e licenza

Manutenuto dallo studio e utilizzato quotidianamente. Codice: [MIT](LICENSE). Voci: CC BY
4.0. Lo specchio delle competenze NVIDIA in `catalogs/nvidia-skills/catalog.json`
riproduce i nomi e le descrizioni delle competenze da
[NVIDIA/skills](https://github.com/NVIDIA/skills) in base alle licenze di quel progetto
(Apache-2.0 per il codice, CC-BY-4.0 per il testo delle competenze).

---

<p align="center">Built by <a href="https://mcp-tool-shop.github.io/">MCP Tool Shop</a></p>
