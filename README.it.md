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

Il banco di ricerca dello studio. Le scoperte provenienti da qualsiasi ambito vengono rapidamente inserite come brevi voci in formato Markdown, con ogni fonte indicata e ogni affermazione contrassegnata come verificata o meno. Gli esperimenti sono affiancati alle voci che li riguardano. I cataloghi esterni vengono replicati e valutati, e un registro elenca gli strumenti dello studio che possono essere utilizzati per la ricerca. Un singolo comando consente di effettuare una ricerca su tutti gli elementi.

## Dove si trova: il banco prima di readouts

Due archivi contengono le conoscenze dello studio e svolgono funzioni diverse.

| | Ricerca e sviluppo (questo repository) | [readouts](https://github.com/mcp-tool-shop-org/readouts) |
|---|---|---|
| Ruolo | il banco: acquisizione, esperimenti, domande aperte | la scaffalatura: basi di conoscenza verificate |
| Ritmo | una voce in pochi minuti, le affermazioni iniziano con `unverified` | create e verificate da gruppi di studio |
| Forma | Voci in formato Markdown, un argomento per ciascuna | una base di conoscenza SQLite per dominio |
| Quanto è disordinato | disordinato intenzionalmente: le affermazioni contestate, i vicoli ciechi e i risultati intermedi rimangono visibili | per niente disordinato: ogni riga è corredata di fonte e verificata |

La conoscenza si muove in una sola direzione:

1. **Banco.** Una scoperta viene inserita qui come voce. Le sue affermazioni iniziano con `[unverified]` e sono contrassegnate con `[verified]` solo con una nota che indica cosa le ha verificate. Le misurazioni effettuate sulle nostre macchine vengono inserite come fonti `rig`, con i relativi strumenti sotto `experiments/`.
2. **Scaffalatura interna.** Una volta che le affermazioni fondamentali di un argomento si dimostrano valide, vengono integrate in una base di conoscenza nel repository di lavoro privato readouts, oppure vengono aggiunte a una base esistente. **La promozione fa parte della conclusione di un esperimento** (il Direttore, 2026-10-09). Quando il risultato di un esperimento viene registrato qui, il relativo aggiornamento readouts-internal segue nella stessa sessione o in quella successiva, insieme ai relativi grafici. Nessun elemento rimane sul banco per più di circa una settimana. Aggiornamenti piccoli e regolari sono preferibili a un singolo aggiornamento importante. Il file README di un esperimento registra la sua promozione come una riga sotto il relativo risultato: "Promosso: readouts-internal `<kb>` onda `<n>`, `<date>`", oppure perché non è ancora stato promosso.
3. **Scaffalatura pubblica.** Una base di conoscenza viene pubblicata nel repository pubblico readouts quando viene aggiunta alla lista di esportazione consentita.

`rnd readouts` esegue la ricerca su ogni base di conoscenza readouts da qui, quindi un singolo punto di accesso consente di accedere a entrambi gli archivi. Cercare prima sul banco, poi sulla scaffalatura e infine analizzare le lacune.

La ricerca qui non è limitata ai soli ambiti dello studio. Ogni voce registra separatamente due elementi: cosa rappresenta la conoscenza e cosa significa per lo studio (`relevance: act | watch | reference`). `reference` è un giudizio valido.

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
python -m rnd sql "SELECT tier, count(*) FROM sources GROUP BY tier"
python -m rnd change "what changed"         # add a changelog fragment under changes/ (nano by default)
python -m rnd bump --note "release note"    # release PR: apply changes/ fragments, bump version + CHANGELOG
```

Ogni comando di elenco accetta `--json` per gli agenti. `rnd.cmd` (Windows) e `rnd.sh` (shell POSIX) sono wrapper leggeri, quindi il comando funziona da qualsiasi directory.

Per utilizzare lo strumento da altri progetti, installarlo da PyPI:

```bash
pip install mcptoolshop-rnd
```

Questo installa il comando `rnd`, non la libreria: le voci sono contenute in questo repository. Il comando cerca una libreria in questo ordine: `--library DIR`, quindi `$RND_ROOT`, quindi la cartella più vicina, a partire dalla directory corrente o in una directory superiore, che contiene `entries/` e `instruments/`. Al di fuori di una libreria, il programma si interrompe con `NO_LIBRARY`; solo `rnd readouts` funziona senza una libreria.

In Python, importare `mcptoolshop_rnd`: questo nome funziona sempre. `rnd` viene mantenuto come alias di compatibilità, ma un pacchetto PyPI non correlato ha anche il nome `rnd` e, se entrambi sono installati, può sostituire l'alias. Il comando `rnd` e `python -m mcptoolshop_rnd` continuano a funzionare in entrambi i casi.

La libreria cambia quotidianamente, quindi le versioni hanno cinque segmenti, `MAJOR.MINOR.PATCH.MICRO.NANO`. I primi tre segmenti definiscono la versione dello strumento `rnd`; MICRO indica una modifica strutturale della libreria e NANO un aggiornamento ordinario. Gli aggiornamenti ordinari aggiungono un frammento del registro delle modifiche sotto `changes/` tramite `rnd change`; al momento del rilascio, `rnd bump` elabora tutti i frammenti, avanza la versione una sola volta in base al livello di frammento più alto e scrive un'unica sezione CHANGELOG.

Codici di uscita: `0` ok · `1` file della libreria non validi · `2` errore di utilizzo o non trovato · `3` errore di runtime (uno strumento esterno o un errore imprevisto). Gli errori stampano un codice, un messaggio e un suggerimento; `--debug` aggiunge il traceback.

## Layout

| Percorso | Cosa | Chi modifica |
|------|------|-----------|
| `entries/YYYY/*.md` | Voci di ricerca: la fonte di verità | persone e agenti |
| `questions/*.md` | Domande di ricerca aperte e risolte | persone e agenti |
| `changes/*.md` | Frammenti del registro delle modifiche non pubblicati (`rnd change`) | persone e agenti (`rnd bump` elabora) |
| `experiments/<name>/` | Strumenti, input fissati, `results.json` e ricevute dei risultati | persone e agenti |
| `experiments/<name>/collect.json` | Record raccolti da un repository di strumenti a commit fissati (`rnd collect`) | persone |
| `instruments/*.md` | Strumenti e protocolli dello studio che la postazione può utilizzare (`kind: instrument`) | Solo la postazione R&S (diff revisionato) |
| `catalogs/<name>/source.json` | Da dove proviene un catalogo | persone |
| `catalogs/<name>/catalog.json` | Snapshot fissato da `rnd catalog sync` | generato; non modificare manualmente |
| `catalogs/<name>/review.json` | Adattamento e note dello studio per famiglia e articolo | persone |
| `datapacks/<name>/spec.json` | Cosa contiene un pacchetto di dati: glob di inclusione, licenze, generatori, host | persone |
| `datapacks/<name>/datapack.json` | Manifesto da `rnd datapack build`: SHA-256 di ogni file, licenze, fissaggi | generato; non modificare manualmente |
| `datapacks/<name>/hosted.json` | Dove è stato caricato (revisione del repository) | dopo un caricamento |
| `mcptoolshop_rnd/` | La CLI | codice |
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

- **Livelli di fonte:** `primary` (documentazione del fornitore, articoli, repository), `secondary` (recensioni autorevoli), `aggregator` (siti di riepilogo, output di ricerca AI), `user` (fornito da una persona: diapositive, note), `rig` (misurato sulle nostre macchine).
- **Affidabilità dell'affermazione:** `unverified`, `verified`, `disputed`, `wrong`, `superseded`. Un'affermazione `verified` o `wrong` deve indicare cosa l'ha verificata con `(via: …)`.
- `[[entry-id]]` collega le voci; `rnd show` elenca i collegamenti in entrata.

## Frammenti del registro delle modifiche

Gli aggiornamenti non modificano direttamente `mcptoolshop_rnd/__init__.py` o `CHANGELOG.md`, quindi
le branche parallele non entrano mai in conflitto sulla linea delle versioni:

```bash
python -m rnd change "Add study of XYZ"                # writes changes/YYYY-MM-DD-<hex>-<slug>.md (level: nano)
python -m rnd change "New tool feature" --level minor  # levels: nano | micro | patch | minor | major
python -m rnd bump --dry-run                           # preview version bump from changes/ fragments
python -m rnd bump                                     # release PR: bump once, update CHANGELOG.md, delete fragments
```

In assenza di file in `changes/`, `rnd bump [nano|micro|…] [--note …]` mantiene il suo
comportamento git-diff. `rnd check` segnala qualsiasi frammento non valido come errore.

## Numeri vincolati

Un esperimento può conservare numeri riepilogativi sicuri per il pubblico in
`experiments/<id>/results.json` e associare numeri alle voci, ai riepiloghi o
alle note dell'esperimento immediatamente dopo il letterale:

```markdown
The judge scored 84.2%<!-- rnd:experiments/e4b/results.json#accuracy:.1% --> on the held-out split.
```

- Markdown grezzo, `grep` e l'indice SQLite mantengono il letterale semplice (`84.2%`);
GitHub e Starlight rendono `84.2%` senza alcun indicatore o collegamento visibile.
- `rnd sync [paths…]` riscrive i letterali vincolati da `results.json` utilizzando la specifica di formato Python; `rnd sync --check` esce con codice `1` senza scrivere se un letterale è diverso.
- `rnd check` tratta qualsiasi letterale vincolato non sincronizzato, file mancante o chiave mancante come un errore e avvisa in caso di affermazioni `[verified]` il cui `(via: …)` fa riferimento a un esperimento del repository mentre contengono ancora numeri non vincolati.

## ID e collegamenti delle affermazioni

Le affermazioni possono contenere ID deterministici stabili `c-<hex>` e relazioni esplicite
(`supersedes`, `contradicts`, `supports`) con affermazioni precedenti tramite ID:

```bash
python -m rnd claims                               # list indexed claims (--state superseded, --json)
python -m rnd claims assign <entry>                # add deterministic c-<hex> ids to one entry's claims
python -m rnd reconcile <entry>                    # mark older claims (superseded / disputed / supported-by)
```

`rnd reconcile <entry>` scrive solo l'ID (se mancante), lo stato aggiornato e
la relazione inversa (`superseded-by`, `contradicted-by`, `supported-by`) sulla
riga dell'affermazione precedente nel proprio file, senza toccare la sua frase o qualsiasi altra
riga. `rnd check` segnala errori in caso di ID di destinazione non validi o collegamenti unilaterali e suggerisce di
eseguire `rnd reconcile`. `rnd search` e `rnd show` contrassegnano `superseded` e
`disputed` e indicano l'affermazione che le ha sostituite o contraddette.

## Domande aperte

Le domande aperte sono memorizzate come singoli file Markdown in `questions/` con lo stato
`open`, `investigating`, `answered` o `parked`:

```bash
python -m rnd new-question "Does X hold on Y?" --field systems
python -m rnd questions --status open --json
```

Quando l'`status` di una domanda è `answered`, la sua sezione frontmatter `answered_by` deve
contenere almeno un ID di affermazione esistente; `rnd check` tratta una domanda `answered`
senza un ID di affermazione esistente come un errore. Le domande sono indicizzate in
`rnd.db` e restituite da `rnd search` e `rnd show`.

## Registro locale delle ricerche non riuscite

Quando `rnd search` non restituisce corrispondenze, aggiunge una riga JSON (`time` e
`query`) a un file `.misses.jsonl` locale accanto a `rnd.db` (`rnd.misses.jsonl` nella
directory principale del repository, ignorato da Git; oppure `<db>.misses.jsonl` accanto a `--db` / `RND_DB`).
Non viene registrato altro, nulla viene mai inviato tramite la rete, `RND_NO_USAGE=1`
disattiva la registrazione e l'eliminazione del file lo rimuove completamente.
`rnd stats --usage` stampa il numero totale di ricerche non riuscite e le query non riuscite più frequenti.

## File di strumentazione e funzionalità aggiuntive opzionali

- **File degli strumenti (`instruments/*.md`):** modificati solo dalla postazione R&S in un diff revisionato la cui descrizione elenca ogni file di strumento modificato, mai da un passaggio o comando che riassume contenuti esterni (`rnd watch`, `rnd probe`, `rnd collect`, `rnd catalog sync`).
- **Dipendenze principali e funzionalità aggiuntive:** il core di `rnd` rimane solo la libreria standard di Python.
Qualsiasi funzionalità aggiuntiva opzionale è presente in un gruppo a cui è possibile aderire e viene importata in modo lazy; un
comando che richiede una funzionalità aggiuntiva mancante fallisce con `MISSING_EXTRA` e un suggerimento per l'installazione.

## Pacchetti di dati

I dati elaborati troppo grandi o troppo ingombranti per essere inclusi nel clone vengono offerti come **pacchetto di dati**: i byte sono memorizzati
su un repository di dataset di Hugging Face (privato fino alla pubblicazione) e la libreria conserva solo un piccolo
manifest. Il modello di integrità deriva da
[research-packs](https://github.com/mcp-tool-shop-org/research-packs): un manifest, un SHA-256 per
ogni file, una verifica con un solo comando e un elenco.

```bash
rnd datapack build natural-errors --source experiments/natural-errors  # reads datapacks/natural-errors/spec.json
rnd datapack list
hf download mcp-tool-shop/rnd-natural-errors --repo-type dataset --local-dir ne
rnd datapack verify natural-errors --copy ne/files                      # PASS when every byte matches
```

- **Ogni file deve avere una licenza** nelle specifiche. Gli output del modello contengono i termini del modello (ad esempio, "Creato con Llama" per gli output di Llama 3.1). `rnd datapack build` rifiuta un pacchetto che
lascia un file senza licenza.
- **Ogni modello di generazione è fissato** (digest Ollama, revisione HF o ID del modello API), con il suo ruolo.
- **`rnd check` convalida ogni manifest** e fallisce se è stato modificato manualmente.
- L'upload include `datapack.json` insieme ai file, in modo che chiunque possa verificarlo senza questo repository:
`pip install mcptoolshop-rnd`.

## Record di esperimenti raccolti

Un repository di strumenti esegue il commit delle proprie specifiche preregistrate e dei record di esecuzione (le ricevute di interlock),
come ogni repository esegue il commit della sua mappa Atlas. La libreria pubblica solo una copia ridotta dei
numeri, creata da `rnd collect` dal repository di strumenti in commit fissati:

```bash
rnd collect                 # list the experiments that collect records
rnd collect e4b             # read each source with git show, trim it, write experiments/e4b/results/
rnd collect e4b --check     # recompute every output; exit 1 if any differs from the committed file
```

- **`experiments/<name>/collect.json`** indica il repository, il clone fratello da cui viene letto
(`--clone` sovrascrive), e ogni sorgente: il suo percorso, il commit, l'SHA-256 dei suoi byte, l'
output e la funzione di riduzione nella sezione `extract.py` dell'esperimento.
- **Una sorgente fissata non cambia mai.** I byte che non corrispondono più all'hash del pin vengono rifiutati.
- **Ogni record contiene la provenienza:** il repository, il percorso della sorgente e l'SHA-256 dei
byte ridotti.
- **Ogni output è sicuro per il pubblico prima di essere scritto.** Nessun percorso di macchina, directory home o
campo di ambiente sopravvive e un modulo di un esperimento può aggiungere una protezione più rigorosa. Nulla viene
scritto in caso di rifiuto.

## Test di uno strumento prima di una prova

`rnd probe <url> …` risponde alle prime domande su uno strumento o un modello dall'API di ciascuna sorgente,
non da un riepilogo di una pagina web:

- **GitHub** (tramite `gh api`, quindi utilizza il tuo login GitHub CLI): la licenza, se è archiviato,
l'ultimo push, l'ultima versione e una ricerca del codice per "telemetria". Un risultato è un indizio da leggere, mai una prova;
zero risultati non sono una prova.
- **Hugging Face:** il tag della licenza o, per "altro", il nome e il collegamento della licenza nella scheda; il gating; l'ultima modifica.
- **PyPI e npm:** la licenza, l'ultima versione e la data di pubblicazione.
- **rnd stesso:** una ricerca esatta della parola per il nome, in modo da sapere se la libreria lo ha già.

Una sorgente a cui non è possibile accedere viene segnalata come sconosciuta, con il motivo.

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

Ciò che viene rilevato viene memorizzato in un file di stato al di fuori del repository (`$RND_WATCH_STATE`, altrimenti `~/.rnd/watch-state.json`).
La prima verifica di una sorgente è una base di riferimento: registra gli elementi correnti e segnala che non ce ne sono di nuovi. Una versione preliminare non viene mai segnalata come l'ultima versione di una sorgente; se esiste una versione preliminare più recente, viene mostrata accanto all'ultima versione. Le note di rilascio e i messaggi di commit (GitHub) vengono conservati nell'output JSON, in modo che l'utente non debba recuperare ogni pagina. Una sorgente che
non può essere raggiunta viene segnalata come sconosciuta e il suo stato viene lasciato invariato, in modo che nulla venga saltato silenziosamente.

Il comando rappresenta la metà deterministica di un rituale settimanale (Director, 2026-10-13). Un "esploratore" legge i nuovi elementi,
verifica qualsiasi strumento candidato con `rnd probe`, controlla la libreria con `rnd search --exact` e scrive un breve
rapporto classificato: cosa archiviare, cosa provare e cosa saltare. Aggiungi una sorgente tramite una richiesta di pull e spiega perché
è importante.

## Relazione con altri strumenti dello studio

- **readouts** è la scaffalatura verificata alimentata da questo banco (vedere sopra).
- **research-os** crea un pacchetto di evidenze "protetto" e "congelato" per un singolo argomento. Un argomento su cui
dipende una decisione può essere promosso a un pacchetto research-os, collegato dalla voce corrispondente.
- **repo-knowledge** indicizza i repository dello studio; questa libreria copre
le conoscenze provenienti da fonti esterne.
- Le informazioni raccolte durante la progettazione di qualcosa appartengono anche qui, in modo che sopravvivano
alla sessione che le ha generate.

Consulta `python -m rnd tools` per il registro completo degli strumenti e
[docs/standards.md](docs/standards.md) per capire come il flusso di lavoro si confronta con gli
standard di flusso di lavoro dello studio.

## Sicurezza e affidabilità

- **Dati interessati:** file all'interno di questo repository (`entries/`, `questions/`, `changes/`,
`instruments/`, `catalogs/`, `experiments/`), l'indice `rnd.db` e il relativo
file di registro locale `rnd.misses.jsonl`. `rnd readouts` apre le basi di conoscenza readouts in modalità
**sola lettura**. `rnd sql` viene eseguito su una connessione in sola lettura.
- **Dati non interessati:** nulla al di fuori del repository e dell'area di checkout readouts. Non
memorizza credenziali e non ne legge.
- **Rete:** nessuna, tranne `rnd catalog sync`, `rnd probe` e `rnd watch`, che leggono metadati pubblici o chiamano l'API GitHub tramite il tuo login `gh` CLI quando vengono eseguiti.
- **Autorizzazioni:** accesso ordinario ai file. Nessun diritto elevato, nessun servizio in background.
- **Registro di utilizzo solo locale:** nulla viene raccolto o inviato da nessuna parte. Quando `rnd search`
non restituisce corrispondenze, aggiunge una riga (ora UTC e query) a `rnd.misses.jsonl`
accanto a `rnd.db` (ignorato da Git nel repository, o `<db>.misses.jsonl` accanto a `--db` /
`$RND_DB`). Imposta `RND_NO_USAGE=1` per disattivarlo e elimina `.misses.jsonl` in qualsiasi momento per cancellarlo. Nessun altro dato di utilizzo viene registrato.
- **Igiene del repository pubblico:** prima di ogni push, l'albero viene scansionato alla ricerca di
percorsi della directory home e dell'identità dell'operatore.

Segnala le vulnerabilità come descritto in [SECURITY.md](SECURITY.md).

## Test

```bash
bash verify.sh                               # tests, library check, index build, smoke
python -m unittest discover -s tests -t .    # tests only
```

## Stato e licenza

Mantenuto dallo studio e utilizzato quotidianamente. Codice: [MIT](LICENSE). Voci: CC BY
4.0. Lo "specchio" delle competenze NVIDIA in `catalogs/nvidia-skills/catalog.json`
riproduce i nomi e le descrizioni delle competenze da
[NVIDIA/skills](https://github.com/NVIDIA/skills) in base alle licenze di quel progetto
(Apache-2.0 per il codice, CC-BY-4.0 per il testo delle competenze).

---

<p align="center">Built by <a href="https://mcp-tool-shop.github.io/">MCP Tool Shop</a></p>
