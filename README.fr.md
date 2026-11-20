<p align="center">
  <a href="README.ja.md">日本語</a> | <a href="README.zh.md">中文</a> | <a href="README.es.md">Español</a> | <a href="README.md">English</a> | <a href="README.hi.md">हिन्दी</a> | <a href="README.it.md">Italiano</a> | <a href="README.pt-BR.md">Português (BR)</a>
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

Le banc de recherche du studio. Les résultats de n'importe quel domaine arrivent rapidement sous forme de courtes entrées Markdown, chaque source étant étiquetée et chaque affirmation étant marquée comme vérifiée ou non. Les expériences sont placées à côté des entrées qu'elles testent. Les catalogues externes sont mis en miroir et évalués, et un registre répertorie les outils du studio que la recherche peut utiliser. Une seule commande permet de rechercher dans tout cela.

## Où il se trouve : le banc avant readouts

Deux supports stockent les connaissances du studio, et ils remplissent des fonctions différentes.

| | Recherche et développement (ce dépôt) | [readouts](https://github.com/mcp-tool-shop-org/readouts) |
|---|---|---|
| Rôle | le banc : collecte, expériences, questions ouvertes | l'étagère : bases de connaissances vérifiées |
| Rythme | une entrée en quelques minutes, les affirmations commencent à `unverified` | créées et vérifiées par des groupes d'étude |
| Forme | entrées Markdown, un sujet par entrée | une SQLite base de connaissances par domaine |
| Niveau de désordre | désordre intentionnel : les affirmations contestées, les impasses et les résultats intermédiaires restent visibles | pas de désordre du tout : chaque ligne est sourcée et vérifiée |

Les connaissances circulent dans un seul sens :

1. **Banc.** Un résultat y est enregistré sous forme d'entrée. Ses affirmations commencent à `[unverified]` et sont marquées `[verified]` uniquement avec une note indiquant ce qui les a vérifiées. Les mesures effectuées sur nos propres machines sont enregistrées sous forme de `rig` sources, avec leur configuration sous `experiments/`.
2. **Étagère interne.** Une fois que les affirmations essentielles d'un sujet se confirment, elles sont intégrées dans une base de connaissances dans le dépôt de travail privé readouts, ou ajoutées à une base existante. **La promotion fait partie de la conclusion d'une expérience** (le directeur, 2026-10-09). Lorsqu'un résultat d'expérience est validé ici, sa mise à jour readouts-internal suit dans la même session ou dans la session suivante, avec ses graphiques. Rien ne reste sur le banc pendant plus d'une semaine. Des mises à jour régulières et mineures sont préférables à une seule mise à jour importante. Le fichier README d'une expérience enregistre sa promotion sous forme d'une ligne sous son résultat : « Promu : readouts-internal `<kb>` vague `<n>`, `<date>` », ou la raison pour laquelle ce n'est pas encore le cas.
3. **Étagère publique.** Une base de connaissances est publiée dans le dépôt public readouts lorsqu'elle est ajoutée à la liste d'exportation autorisée.

`rnd readouts` recherche dans chaque readouts base de connaissances à partir d'ici, de sorte qu'un seul point d'accès donne accès aux deux supports. Recherchez d'abord sur le banc, puis sur l'étagère, puis menez des recherches sur les lacunes.

La recherche ici ne se limite pas aux domaines du studio. Chaque entrée enregistre deux éléments séparément : la nature de la connaissance et ce qu'elle signifie pour le studio (`relevance: act | watch | reference`). `reference` est un verdict tout à fait valable.

## Utilisation

Nécessite Python 3.10 ou une version ultérieure et rien d'autre (uniquement la bibliothèque standard). Fonctionne sous Windows, macOS et Linux. À partir du répertoire racine du dépôt :

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

Chaque commande de liste prend `--json` pour les agents. `rnd.cmd` (Windows) et `rnd.sh` (shells POSIX) sont de simples enveloppes, de sorte que la commande fonctionne à partir de n'importe quel répertoire.

Pour utiliser l'outil à partir d'autres projets, installez-le à partir de PyPI :

```bash
pip install mcptoolshop-rnd
```

Cela installe la commande `rnd`, et non la bibliothèque : les entrées se trouvent dans ce dépôt. La commande trouve une bibliothèque dans l'ordre suivant : `--library DIR`, puis `$RND_ROOT`, puis le dossier le plus proche, au niveau du répertoire actuel ou au-dessus, qui contient `entries/` et `instruments/`. En dehors d'une bibliothèque, elle s'arrête avec `NO_LIBRARY` ; seule `rnd readouts` fonctionne sans bibliothèque.

En Python, importez `mcptoolshop_rnd` : ce nom fonctionne toujours. `rnd` est conservé comme alias de compatibilité, mais un package PyPI non lié est également appelé `rnd`, et si les deux sont installés, il peut remplacer l'alias. La commande `rnd` et `python -m mcptoolshop_rnd` continuent de fonctionner de toute façon.

La bibliothèque change quotidiennement, de sorte que les versions ont cinq segments, `MAJOR.MINOR.PATCH.MICRO.NANO`. Les trois premiers segments définissent la version de l'outil `rnd` ; MICRO indique un changement structurel de la bibliothèque et NANO une mise à jour ordinaire. Les mises à jour ordinaires ajoutent un fragment de journal des modifications sous `changes/` via `rnd change` ; au moment de la publication, `rnd bump` consomme tous les fragments, incrémente la version une seule fois selon le niveau de fragment le plus élevé et écrit une seule section CHANGELOG.

Codes de sortie : `0` ok · `1` fichiers de bibliothèque non valides · `2` erreur d'utilisation ou non trouvé · `3` échec d'exécution (un outil externe ou une erreur inattendue). Les erreurs affichent un code, un message et un indice ; `--debug` ajoute la trace de la pile.

## Disposition

| Chemin | Quoi | Qui modifie |
|------|------|-----------|
| `entries/YYYY/*.md` | Entrées de recherche : la source de vérité | personnes et agents |
| `questions/*.md` | Questions de recherche ouvertes et résolues | personnes et agents |
| `changes/*.md` | Fragments de journal des modifications non publiés (`rnd change`) | personnes et agents (`rnd bump` consomme) |
| `experiments/<name>/` | Configurations, entrées fixées, `results.json` et reçus de résultats | personnes et agents |
| `experiments/<name>/collect.json` | Enregistrements collectés à partir d'un dépôt d'outils à des révisions fixées (`rnd collect`) | personnes |
| `instruments/*.md` | Outils et protocoles du studio que le siège peut utiliser (`kind: instrument`) | siège R&D uniquement (différentiel examiné) |
| `catalogs/<name>/source.json` | D'où provient un catalogue | personnes |
| `catalogs/<name>/catalog.json` | Instantané fixé à partir de `rnd catalog sync` | généré ; ne jamais modifier manuellement |
| `catalogs/<name>/review.json` | Adaptation et notes du studio par famille et par élément | personnes |
| `datapacks/<name>/spec.json` | Ce que contient un pack de données : motifs glob d'inclusion, licences, générateurs, hôte | personnes |
| `datapacks/<name>/datapack.json` | Manifeste à partir de `rnd datapack build` : SHA-256 de chaque fichier, licences, versions fixées | généré ; ne jamais modifier manuellement |
| `datapacks/<name>/hosted.json` | Où l'upload a atterri (révision du dépôt) | après un upload |
| `mcptoolshop_rnd/` | L'interface en ligne de commande | code |
| `rnd/` | Alias de compatibilité pour `mcptoolshop_rnd` | code |
| `rnd.db` | SQLite FTS5 index, reconstruit automatiquement lorsque les fichiers changent | généré ; pas dans git |
| `rnd.misses.jsonl` | Journal de recherche local sans correspondance à côté de `rnd.db` (`RND_NO_USAGE=1` désactive) | généré ; pas dans git |

## Format d'entrée

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

- **Niveaux de source :** `primary` (documentation du fournisseur, articles, dépôts), `secondary` (articles de référence), `aggregator` (sites de résumé, résultats de recherche IA), `user` (fournis par une personne : diapositives, notes), `rig` (mesurés sur nos machines).
- **Confiance dans l'affirmation :** `unverified`, `verified`, `disputed`, `wrong`, `superseded`. Une affirmation `verified` ou `wrong` doit indiquer ce qui l'a vérifiée avec `(via: …)`.
- `[[entry-id]]` relie les entrées ; `rnd show` répertorie les liens retour.

## Fragments du journal des modifications

Les mises à jour ne modifient pas directement `mcptoolshop_rnd/__init__.py` ou `CHANGELOG.md`, de sorte que les branches parallèles ne se croisent jamais sur la ligne de version :

```bash
python -m rnd change "Add study of XYZ"                # writes changes/YYYY-MM-DD-<hex>-<slug>.md (level: nano)
python -m rnd change "New tool feature" --level minor  # levels: nano | micro | patch | minor | major
python -m rnd bump --dry-run                           # preview version bump from changes/ fragments
python -m rnd bump                                     # release PR: bump once, update CHANGELOG.md, delete fragments
```

En l’absence de fichiers dans `changes/`, `rnd bump [nano|micro|…] [--note …]` conserve son comportement git-diff. `rnd check` signale tout fragment malformé comme une erreur.

## Nombres liés

Une expérience peut conserver des nombres de résumé sécurisés pour le public dans `experiments/<id>/results.json` et lier des nombres dans les entrées, les résumés ou les notes d’expérience immédiatement après le littéral :

```markdown
The judge scored 84.2%<!-- rnd:experiments/e4b/results.json#accuracy:.1% --> on the held-out split.
```

- Markdown brut, `grep` et l’index SQLite conservent le littéral brut (`84.2%`) ; GitHub et Starlight rendent `84.2%` sans aucun marqueur ou lien visible.
- `rnd sync [paths…]` réécrit les littéraux liés à partir de `results.json` en utilisant la spécification de format Python ; `rnd sync --check` se termine avec le code `1` sans écrire si un littéral est différent.
- `rnd check` traite tout littéral lié hors synchronisation, fichier manquant ou clé manquante comme une erreur, et émet un avertissement pour les affirmations `[verified]` dont `(via: …)` nomme une expérience du dépôt alors qu’elles contiennent encore des nombres non liés.

## Identifiants et liens d’affirmation

Les affirmations peuvent contenir des identifiants `c-<hex>` stables et déterministes et des relations explicites (`supersedes`, `contradicts`, `supports`) vers des affirmations plus anciennes par identifiant :

```bash
python -m rnd claims                               # list indexed claims (--state superseded, --json)
python -m rnd claims assign <entry>                # add deterministic c-<hex> ids to one entry's claims
python -m rnd reconcile <entry>                    # mark older claims (superseded / disputed / supported-by)
```

`rnd reconcile <entry>` n’écrit que l’identifiant (s’il est manquant), l’état mis à jour et la relation inverse (`superseded-by`, `contradicted-by`, `supported-by`) sur la ligne de l’affirmation plus ancienne dans son propre fichier, sans toucher à sa phrase ou à toute autre ligne. `rnd check` signale comme une erreur les identifiants cibles cassés ou les liens unilatéraux et suggère d’exécuter `rnd reconcile`. `rnd search` et `rnd show` marquent `superseded` et `disputed` et nomment l’affirmation qui les a remplacées ou contredites.

## Questions ouvertes

Les questions ouvertes sont stockées sous forme de fichiers Markdown individuels dans `questions/` avec les statuts `open`, `investigating`, `answered` ou `parked` :

```bash
python -m rnd new-question "Does X hold on Y?" --field systems
python -m rnd questions --status open --json
```

Lorsque le `status` d’une question est `answered`, sa liste `answered_by` dans l’en-tête doit nommer au moins un identifiant d’affirmation existant ; `rnd check` traite une question `answered` sans identifiant d’affirmation existant comme une erreur. Les questions sont indexées dans `rnd.db` et renvoyées par `rnd search` et `rnd show`.

## Journal local des recherches infructueuses

Lorsque `rnd search` ne renvoie aucune correspondance, il ajoute une ligne JSON (`time` et `query`) à un fichier `.misses.jsonl` local à côté de `rnd.db` (`rnd.misses.jsonl` dans le répertoire racine du dépôt, ignoré par Git ; ou `<db>.misses.jsonl` à côté de `--db` / `RND_DB`). Rien d’autre n’est enregistré, rien n’est jamais envoyé sur le réseau, `RND_NO_USAGE=1` désactive la journalisation et la suppression du fichier le supprime complètement. `rnd stats --usage` affiche le nombre total d’échecs et les requêtes les plus fréquemment non trouvées.

## Fichiers d’instrumentation et éléments facultatifs

- **Fichiers d’instruments (`instruments/*.md`) :** modifiés uniquement par le siège R&D dans un différentiel examiné dont la description répertorie chaque fichier d’instrument modifié, jamais par une étape ou une commande qui résume du contenu externe (`rnd watch`, `rnd probe`, `rnd collect`, `rnd catalog sync`).
- **Dépendances principales et éléments facultatifs :** la base de `rnd` reste uniquement la bibliothèque standard de Python. Tout élément facultatif se trouve dans un groupe d’adhésion et est importé de manière paresseuse ; une commande qui nécessite un élément facultatif manquant échoue avec `MISSING_EXTRA` et une indication d’installation.

## Packs de données

Les données traitées trop volumineuses ou trop lourdes pour être incluses dans le clone sont proposées sous forme de **pack de données :** les octets sont stockés dans un dépôt de jeu de données Hugging Face (privé jusqu’à sa publication), et la bibliothèque ne conserve qu’un petit manifeste. Le modèle d’intégrité provient de [research-packs](https://github.com/mcp-tool-shop-org/research-packs) : un manifeste, un SHA-256 pour chaque fichier, une vérification en une seule commande et une liste.

```bash
rnd datapack build natural-errors --source experiments/natural-errors  # reads datapacks/natural-errors/spec.json
rnd datapack list
hf download mcp-tool-shop/rnd-natural-errors --repo-type dataset --local-dir ne
rnd datapack verify natural-errors --copy ne/files                      # PASS when every byte matches
```

- **Chaque fichier doit avoir une licence** dans la spécification. Les résultats du modèle contiennent les conditions de son modèle (par exemple, « Créé avec Llama » pour les résultats de Llama 3.1). `rnd datapack build` refuse un pack qui laisse un fichier sans licence.
- **Chaque modèle de génération est verrouillé** (digest Ollama, révision HF ou identifiant de modèle API), avec son rôle.
- **`rnd check` valide chaque manifeste** et échoue si un manifeste a été modifié manuellement.
- Le chargement inclut `datapack.json` à côté des fichiers, de sorte que chacun puisse vérifier sans ce dépôt : `pip install mcptoolshop-rnd`.

## Enregistrements d’expérience collectés

Un dépôt d’outils enregistre ses propres spécifications et enregistrements d’exécution préenregistrés (les reçus de interlock), de la même manière que chaque dépôt enregistre sa carte Atlas. La bibliothèque ne publie qu’une copie réduite des nombres, créée par `rnd collect` à partir du dépôt d’outils à des versions spécifiques :

```bash
rnd collect                 # list the experiments that collect records
rnd collect e4b             # read each source with git show, trim it, write experiments/e4b/results/
rnd collect e4b --check     # recompute every output; exit 1 if any differs from the committed file
```

- **`experiments/<name>/collect.json`** nomme le dépôt, le clone frère à partir duquel il est lu (`--clone` remplace), et chaque source : son chemin, la validation, le SHA-256 de ses octets, la sortie et la fonction de réduction dans le `extract.py` de l’expérience.
- **Une source verrouillée ne change jamais.** Les octets qui ne correspondent plus au hachage du verrou sont refusés.
- **Chaque enregistrement contient une provenance :** le dépôt, le chemin de la source et le SHA-256 des octets réduits.
- **Chaque sortie est sécurisée avant d’être écrite.** Aucun chemin d’accès à la machine, répertoire personnel ou champ d’environnement ne survit, et un module d’expérience peut ajouter une protection plus stricte. Rien n’est écrit en cas de refus.

## Test d’un outil avant un essai

`rnd probe <url> …` répond aux premières questions sur un outil ou un modèle à partir de l’API de chaque source, et non à partir d’un résumé d’une page Web :

- **GitHub** (via `gh api`, de sorte qu’il utilise votre connexion GitHub CLI) : la licence, s’il est archivé, le dernier push, la dernière version et une recherche de code pour « télémétrie ». Une correspondance est une piste à étudier, jamais une preuve ; zéro correspondance n’est pas non plus une preuve.
- **Hugging Face :** le tag de licence, ou pour « autre », le nom de la licence et le lien de la carte ; la restriction ; la dernière modification.
- **PyPI et npm :** la licence, la dernière version et la date de publication.
- **rnd lui-même :** une recherche de mot exact pour le nom, afin que vous sachiez si la bibliothèque le contient déjà.

Une source à laquelle on ne peut pas accéder est signalée comme inconnue, avec la raison.

## Surveillance des sources

`rnd watch` vérifie les sources dans [docs/watchlist.json](docs/watchlist.json) et signale ce qui est nouveau depuis la dernière vérification :

- le blog technique de NVIDIA ;
- la version du kit d’outils CUDA ;
- les nouveaux modèles Hugging Face de NVIDIA ;
- le catalogue de compétences de NVIDIA ;
- les versions des moteurs et des outils utilisés par le studio, tels que Ollama, OpenVINO, PyTorch, ComfyUI et Claude Code.

```bash
python -m rnd watch                  # what's new; records what it saw
python -m rnd watch --no-save --json # look without recording
python -m rnd watch --only ollama    # one source
```

Ce qu’il a trouvé est conservé dans un fichier d’état situé en dehors du dépôt (`$RND_WATCH_STATE`, sinon `~/.rnd/watch-state.json`).
La première vérification d’une source consiste en une base de référence : elle enregistre les éléments actuels et signale qu’aucun n’est nouveau. Une version préliminaire n’est jamais signalée comme étant la dernière version d’une source ; s’il existe une version préliminaire plus récente, elle est affichée à côté de la dernière version. Les notes de version GitHub et les messages de validation sont conservés dans la sortie JSON, de sorte qu’un lecteur n’a pas besoin de récupérer chaque page. Une source qui
ne peut pas être atteinte est signalée comme inconnue, et son état est laissé tel quel afin que rien ne soit ignoré silencieusement.

La commande représente la moitié déterministe d’un rituel hebdomadaire (Director, 2026-10-13). Un explorateur lit les nouveaux éléments,
teste tout outil candidat avec `rnd probe`, vérifie la bibliothèque avec `rnd search --exact` et rédige un court
rapport classé : ce qu’il faut archiver, ce qu’il faut essayer et ce qu’il faut ignorer. Ajoutez une source par le biais d’une demande de fusion et expliquez pourquoi elle
est importante.

## Relation avec les autres outils du studio

- **readouts** est l’étagère vérifiée que ce banc alimente (voir ci-dessus).
- **research-os** crée un ensemble de preuves limité et figé pour un sujet. Un sujet sur lequel
une décision dépend peut évoluer vers un ensemble research-os, lié à l’entrée.
- **repo-knowledge** indexe les propres dépôts du studio ; cette bibliothèque couvre
les connaissances provenant de sources externes.
- Les informations recueillies lors de la conception de quelque chose s’y trouvent également, afin qu’elles survivent
à la session qui les a produites.

Consultez `python -m rnd tools` pour obtenir le registre complet des instruments, et
[docs/standards.md](docs/standards.md) pour savoir comment le flux de travail se compare aux
normes de flux de travail du studio.

## Sécurité et confiance

- **Données concernées :** fichiers dans ce dépôt (`entries/`, `questions/`, `changes/`,
`instruments/`, `catalogs/`, `experiments/`), l’index `rnd.db` et son
fichier journal local associé `rnd.misses.jsonl`. `rnd readouts` ouvre les bases de connaissances readouts en mode **lecture seule**. `rnd sql` s’exécute sur une connexion en lecture seule.
- **Données non concernées :** rien en dehors du dépôt et de la copie readouts. Il
ne stocke ni ne lit aucun identifiant.
- **Réseau :** aucun, à l’exception de `rnd catalog sync`, `rnd probe` et `rnd watch`,
qui lisent les métadonnées publiques ou appellent l’API GitHub via votre propre connexion `gh` CLI
lorsque vous les exécutez.
- **Autorisations :** accès ordinaire aux fichiers. Aucun droit élevé, aucun service en arrière-plan.
- **Journal d’utilisation uniquement local :** rien n’est collecté ni envoyé. Lorsque `rnd search`
ne renvoie aucune correspondance, il ajoute une ligne (heure UTC et requête) à `rnd.misses.jsonl`
à côté de `rnd.db` (ignoré dans le dépôt Git, ou `<db>.misses.jsonl` à côté de `--db` /
`$RND_DB`). Définissez `RND_NO_USAGE=1` pour le désactiver et supprimez `.misses.jsonl` à tout moment pour l’effacer. Aucune autre donnée d’utilisation n’est enregistrée.
- **Hygiène du dépôt public :** avant chaque envoi, l’arborescence est analysée pour
détecter les chemins du répertoire personnel et l’identité de l’opérateur.

Signalez les vulnérabilités comme décrit dans [SECURITY.md](SECURITY.md).

## Tests

```bash
bash verify.sh                               # tests, library check, index build, smoke
python -m unittest discover -s tests -t .    # tests only
```

## État et licence

Maintenu par le studio et utilisé quotidiennement. Code : [MIT](LICENSE). Entrées : CC BY
4.0. Le miroir des compétences NVIDIA dans `catalogs/nvidia-skills/catalog.json`
reproduit les noms et descriptions des compétences à partir de
[NVIDIA/skills](https://github.com/NVIDIA/skills) selon les licences de ce projet
(Apache-2.0 pour le code, CC-BY-4.0 pour le texte des compétences).

---

<p align="center">Built by <a href="https://mcp-tool-shop.github.io/">MCP Tool Shop</a></p>
