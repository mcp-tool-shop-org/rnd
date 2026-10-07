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

La postazione di ricerca dello studio. Le scoperte provenienti da qualsiasi ambito vengono inserite rapidamente come brevi voci in formato Markdown, con ogni fonte indicata e ogni affermazione contrassegnata come verificata o meno. Gli esperimenti sono affiancati alle voci che li riguardano. I cataloghi esterni vengono replicati e valutati, e un registro elenca gli strumenti dello studio che la ricerca può utilizzare. Un singolo comando consente di effettuare una ricerca su tutti questi dati.

## Dove si trova: la postazione di lavoro prima della visualizzazione dei risultati

Due archivi contengono le conoscenze dello studio e svolgono funzioni diverse.

| | Ricerca e sviluppo (questo repository). | [readouts](https://github.com/mcp-tool-shop-org/readouts) |
|---|---|---|
| Ruolo. | La postazione: acquisizione dati, esperimenti, domande aperte. | La scaffalatura: basi di conoscenza verificate. |
| Ritmo. | Una voce viene inserita in pochi minuti, le affermazioni iniziano con `unverified`. | Creata e verificata da gruppi di studio. |
| Formato. | Voci in formato Markdown, un argomento per ciascuna. | Una base di conoscenza SQLite per dominio. |
| Disordine. | Previsto: le affermazioni contestate, i vicoli ciechi e i risultati intermedi rimangono visibili. | Nessuno: le righe sono tracciabili e verificate. |

La conoscenza si muove in una sola direzione:

1. **Postazione.** Una scoperta viene inserita qui come voce. Le sue affermazioni iniziano con `[unverified]` e sono contrassegnate con `[verified]`, con una nota che indica cosa le ha verificate. Le misurazioni effettuate sulle nostre macchine vengono inserite come fonti `rig`, con i relativi strumenti sotto `experiments/`.
2. **Scaffalatura interna.** Una volta che le affermazioni fondamentali di un argomento si dimostrano valide, vengono integrate in una base di conoscenza nel repository di lavoro privato dei risultati, oppure vengono aggiunte a quest'ultimo.
3. **Scaffalatura pubblica.** Una base di conoscenza viene pubblicata nel repository pubblico dei risultati quando viene aggiunta alla lista di esportazione consentita.

`rnd readouts` esegue la ricerca in tutte le basi di conoscenza dei risultati da qui, quindi un singolo punto di accesso consente di raggiungere entrambi gli archivi. Cercare prima nella postazione, poi nella scaffalatura e infine analizzare le lacune.

La ricerca qui non è limitata ai soli ambiti dello studio. Ogni voce registra separatamente due elementi: cosa rappresenta la conoscenza e cosa significa per lo studio (`relevance: act | watch | reference`). `reference` è una valutazione positiva.

## Come utilizzarlo

Richiede Python 3.10 o versioni successive e nient'altro (solo la libreria standard). Funziona su Windows, macOS e Linux. Dalla directory principale del repository:

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
```

Ogni comando di elenco richiede `--json` per gli agenti. `rnd.cmd` (Windows) e `rnd.sh` (shell POSIX) sono semplici wrapper, quindi il comando funziona da qualsiasi directory.

Codici di uscita: `0` ok · `1` file di libreria non validi · `2` errore di utilizzo o file non trovato · `3` errore di runtime (uno strumento esterno o un errore imprevisto). Gli errori visualizzano un codice, un messaggio e un suggerimento; `--debug` aggiunge il traceback.

## Layout

| Percorso. | Cosa. | Chi modifica. |
|------|------|-----------|
| `entries/YYYY/*.md` | Voci di ricerca: la fonte della verità. | Persone e agenti. |
| `experiments/<name>/` | Strumenti, input fissi e ricevute dei risultati per le misurazioni effettuate con gli strumenti. | Persone e agenti. |
| `instruments/*.md` | Strumenti e protocolli dello studio che la postazione può utilizzare (`kind: instrument`). | Persone e agenti. |
| `catalogs/<name>/source.json` | Da dove proviene un catalogo. | Persone. |
| `catalogs/<name>/catalog.json` | Snapshot fissato da `rnd catalog sync`. | Generato; non modificare manualmente. |
| `catalogs/<name>/review.json` | Adattamento e note dello studio per famiglia e articolo. | Persone. |
| `rnd/` | La CLI. | Codice. |
| `rnd.db` | Indice SQLite FTS5, ricostruito automaticamente quando i file cambiano. | Generato; non presente in Git. |

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
- [verified] A checked statement. (via: what checked it, date)
## Sources
- [primary] https://… — publisher
```

- **Livelli di fonte:** `primary` (documentazione del fornitore, articoli, repository), `secondary` (recensioni autorevoli), `aggregator` (siti di riepilogo, risultati di ricerca AI), `user` (fornito da una persona: diapositive, note), `rig` (misurato sulle nostre macchine).
- **Affidabilità dell'affermazione:** `unverified`, `verified`, `disputed`, `wrong`. Un'affermazione `verified` o `wrong` deve indicare cosa l'ha verificata con `(via: …)`.
- `[[entry-id]]` collega le voci; `rnd show` elenca i collegamenti in entrata.

## Relazione con gli altri strumenti dello studio

- **readouts** è la scaffalatura verificata a cui questa postazione fornisce dati (vedere sopra).
- **research-os** crea un pacchetto di prove protetto e congelato per un singolo argomento. Un argomento su cui si basa una decisione può essere promosso a un pacchetto research-os, collegato dalla voce.
- **repo-knowledge** indicizza i repository dello studio; questa libreria copre le conoscenze provenienti dall'esterno.
- Le scoperte raccolte durante la progettazione di qualcosa appartengono anche qui, in modo che sopravvivano alla sessione che le ha prodotte.

Consultare `python -m rnd tools` per il registro completo degli strumenti e [docs/standards.md](docs/standards.md) per vedere come il flusso di lavoro si confronta con gli standard di flusso di lavoro dello studio.

## Sicurezza e affidabilità

- **Dati interessati:** file all'interno di questo repository (`entries/`, `instruments/`, `catalogs/`, `experiments/`) e l'indice `rnd.db`, che vengono ricostruiti. `rnd readouts` opens the readouts knowledge bases **read-only**. `rnd sql` viene eseguito su una connessione di sola lettura.
- **Dati non interessati:** nulla al di fuori del repository e della copia di controllo di readouts. Non memorizza credenziali e non ne legge.
- **Rete:** nessuna, tranne `rnd catalog sync`, che chiama l'API di GitHub tramite il proprio accesso CLI `gh` quando viene eseguito.
- **Autorizzazioni:** accesso ordinario ai file. Nessun diritto elevato, nessun servizio in background.
- **Nessun telemetria.** Nulla viene raccolto o inviato.
- **Igiene del repository pubblico:** prima di ogni push, l'albero viene scansionato alla ricerca di percorsi della directory home e dell'identità dell'operatore.

Segnalare le vulnerabilità come descritto in [SECURITY.md](SECURITY.md).

## Test

```bash
bash verify.sh                               # tests, library check, index build, smoke
python -m unittest discover -s tests -t .    # tests only
```

## Stato e licenza

Gestito dallo studio e utilizzato quotidianamente. Codice: [MIT](LICENSE). Voci: CC BY 4.0. Lo specchio delle competenze NVIDIA in `catalogs/nvidia-skills/catalog.json` riproduce i nomi e le descrizioni delle competenze da [NVIDIA/skills](https://github.com/NVIDIA/skills) in base alle licenze di tale progetto (Apache-2.0 per il codice, CC-BY-4.0 per il testo delle competenze).

---

<p align="center">Built by <a href="https://mcp-tool-shop.github.io/">MCP Tool Shop</a></p>
