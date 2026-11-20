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
| Quel est le niveau de désordre | désordre intentionnel : les affirmations contestées, les impasses et les résultats intermédiaires restent visibles | pas de désordre du tout : chaque ligne est sourcée et vérifiée |

Les connaissances circulent dans un seul sens :

1. **Banc.** Un résultat y est enregistré sous forme d'entrée. Ses affirmations commencent à `[unverified]` et sont marquées `[verified]` uniquement avec une note indiquant ce qui les a vérifiées. Les mesures effectuées sur nos propres machines sont enregistrées sous forme de `rig` sources, avec leur configuration sous `experiments/`.
2. **Étagère interne.** Une fois que les affirmations essentielles d'un sujet se confirment, elles sont intégrées dans une base de connaissances dans le dépôt de travail privé readouts, ou ajoutées à une base existante. **La promotion fait partie de la clôture d'une expérience** (le directeur, 2026-10-09). Lorsqu'un résultat d'expérience est validé ici, sa mise à jour readouts-internal suit dans la même session ou dans la session suivante, avec ses graphiques. Rien ne reste sur le banc pendant plus d'une semaine environ. Des mises à jour régulières et mineures sont préférables à une seule mise à jour importante. Le fichier README d'une expérience enregistre sa promotion sous forme d'une ligne sous son résultat : « Promu : readouts-internal `<kb>` vague `<n>`, `<date>` », ou la raison pour laquelle ce n'est pas encore le cas.
3. **Étagère publique.** Une base de connaissances est publiée dans le dépôt public readouts lorsqu'elle est ajoutée à la liste d'exportation autorisée.

`rnd readouts` recherche dans chaque readouts base de connaissances à partir d'ici, de sorte qu'un seul point d'accès donne accès aux deux supports. Recherchez d'abord sur le banc, puis sur l'étagère, puis étudiez la différence.

La recherche ici ne se limite pas aux domaines du studio. Chaque entrée enregistre deux éléments séparément : la nature de la connaissance et ce qu'elle signifie pour le studio (`relevance: act | watch | reference`). `reference` est un verdict favorable.

## Utilisation

Nécessite Python 3.10 ou une version ultérieure, et rien d'autre (uniquement la bibliothèque standard). Fonctionne sous Windows, macOS et Linux. À partir du répertoire racine du dépôt :

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

Chaque commande de liste prend `--json` pour les agents. `rnd.cmd` (Windows) et `rnd.sh` (shells POSIX) sont de simples wrappers, de sorte que la commande fonctionne à partir de n'importe quel répertoire.

Pour utiliser l'outil à partir d'autres projets, installez-le à partir de PyPI :

```bash
pip install mcptoolshop-rnd
```

Cela installe la commande `rnd`, et non la bibliothèque : les entrées se trouvent dans ce dépôt. La commande trouve une bibliothèque dans l'ordre suivant : `--library DIR`, puis `$RND_ROOT`, puis le dossier le plus proche, au niveau du répertoire actuel ou au-dessus, qui contient `entries/` et `instruments/`. En dehors d'une bibliothèque, elle s'arrête avec `NO_LIBRARY` ; seule `rnd readouts` fonctionne sans bibliothèque.

En Python, importez `mcptoolshop_rnd` : ce nom fonctionne toujours. `rnd` est conservé comme alias de compatibilité, mais un package PyPI non lié porte également le nom `rnd`, et si les deux sont installés, il peut remplacer l'alias. La commande `rnd` et `python -m mcptoolshop_rnd` continuent de fonctionner de toute façon.

La bibliothèque change quotidiennement, de sorte que les versions ont cinq segments, `MAJOR.MINOR.PATCH.MICRO.NANO`. Les trois premiers segments définissent la version de l'outil `rnd` ; MICRO indique un changement structurel de la bibliothèque et NANO une mise à jour ordinaire. Les mises à jour ordinaires ajoutent un fragment de journal des modifications sous `changes/` via `rnd change` ; au moment de la publication, `rnd bump` consomme tous les fragments, déplace la version d'un niveau en fonction du fragment le plus élevé et écrit une section CHANGELOG.

Codes de sortie : `0` ok · `1` fichiers de bibliothèque non valides · `2` erreur d'utilisation ou non trouvé · `3` échec d'exécution (un outil externe ou une erreur inattendue). Les erreurs affichent un code, un message et un indice ; `--debug` ajoute la trace de la pile.

## Disposition

| Chemin | Quoi | Qui modifie |
|------|------|-----------|
| `entries/YYYY/*.md` | Entrées de recherche : la source de vérité | personnes et agents |
| `questions/*.md` | Questions de recherche ouvertes et résolues | personnes et agents |
| `changes/*.md` | Fragments de journal des modifications non publiés (`rnd change`) | personnes et agents (`rnd bump` consomme) |
| `experiments/<name>/` | Configurations, entrées fixées, `results.json` et reçus de résultats | personnes et agents |
| `experiments/<name>/collect.json` | Enregistrements collectés à partir d'un dépôt d'outils à des commits fixés (`rnd collect`) | personnes |
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

En l’absence de fichiers dans `changes/`, `rnd bump [nano|micro|…] [--note …]` conserve son comportement git-diff. Les deux, `__init__.py` et `CHANGELOG.md`, sont mis en attente via des fichiers temporaires et échangés avec `os.replace`, ce qui annule `__init__.py` si l’échange CHANGELOG échoue. Si un plantage laisse `__init__.py` en avance sur `CHANGELOG.md`, une nouvelle exécution au niveau correspondant complète la mise à jour et tout autre niveau est refusé avec `BAD_CHANGELOG`. Il reste un seul problème : un plantage après l’échange des deux fichiers, mais avant la suppression des fragments sous `changes/`, les laisse en place, et une nouvelle exécution entraînerait une deuxième mise à jour. Il faut donc supprimer ces fragments manuellement en premier. `rnd check` signale tout fragment malformé comme une erreur.

## Nombres liés

Une expérience peut conserver des nombres de résumé sécurisés pour le public dans `experiments/<id>/results.json` et lier les nombres dans les entrées, les résumés ou les notes d’expérience directement après le littéral :

```markdown
The judge scored 84.2%<!-- rnd:experiments/e4b/results.json#accuracy:.1% --> on the held-out split.
```

- Markdown brut, `grep` et l’index SQLite conservent le littéral brut (`84.2%`) ; GitHub et Starlight rendent `84.2%` sans aucun marqueur ou lien visible.
- `rnd sync [paths…]` réécrit les littéraux liés à partir de `results.json` en utilisant la spécification de format Python ; `rnd sync --check` se termine avec le code `1` sans écrire si un littéral est différent.
- `rnd check` traite tout littéral lié hors synchronisation, fichier manquant ou clé manquante comme une erreur, et affiche un avertissement sur `[verified]` lorsque `(via: …)` nomme une expérience de dépôt alors qu’il contient encore des nombres non liés, en ignorant les entiers simples (sans point décimal, signe de pourcentage, séparateur de milliers ou unité de fin) qui sont associés au mot précédent dans le titre ou les balises de l’entrée, ou qui suivent `RTX` ou `GTX` (3 à 4 chiffres) ou `CUDA`, `PTX`, `Gemma`, `Llama`, `Qwen`, `Claude`, `GPT` ou `Phi` (1 à 2 chiffres).

## Identifiants et liens des affirmations

Les affirmations peuvent contenir des identifiants `c-<hex>` stables et déterministes, ainsi que des relations explicites (`supersedes`, `contradicts`, `supports`) vers des affirmations plus anciennes, identifiées par leur identifiant :

```bash
python -m rnd claims                               # list indexed claims (--state superseded, --json)
python -m rnd claims assign <entry>                # add deterministic c-<hex> ids to one entry's claims
python -m rnd similar <entry> [--limit 5]          # closest claims in other entries (read-only)
python -m rnd reconcile <entry>                    # mark older claims (superseded / disputed / supported-by)
```

`rnd similar <entry>` exécute une requête SQLite FTS5 BM25 en lecture seule sur `claims_fts`
pour chaque affirmation de `<entry>` par rapport aux autres entrées (`--limit` a une valeur par défaut de 5),
signale les correspondances `superseded` ou `disputed` en indiquant ce qui les a remplacées ou contredit,
affiche les clauses et la commande `rnd reconcile <entry>` exactes `(supersedes: id)` / `(contradicts: id)` / `(supports: id)`, et n’écrit jamais `rnd.db` ni aucune
entrée. `rnd reconcile <entry>` écrit uniquement l’identifiant (s’il est manquant), l’état mis à jour et
la relation inverse (`superseded-by`, `contradicted-by`, `supported-by`) sur la
ligne de l’affirmation la plus ancienne dans son propre fichier, sans modifier sa phrase ou toute autre
ligne (laissant une affirmation `[wrong]` `[wrong]` lorsqu’elle est contredite). Les deux,
`rnd claims assign` et `rnd reconcile`, refusent (`MULTIPLE_CLAIMS_HEADINGS`)
sans écrire si une entrée contient plus d’un en-tête `## Claims` réel.
`rnd check` signale les erreurs concernant les identifiants de cible non valides, les liens unilatéraux (suggérant d’exécuter
`rnd reconcile`, ou de supprimer la clause et de réinitialiser un état `superseded` ou `disputed`) ou une clôture de code non fermée,
et avertit en cas d’affirmation `[superseded]` sans lien `(superseded-by: …)`.
`rnd search` et `rnd show` marquent les affirmations `superseded` et `disputed` et indiquent le nom de
l’affirmation qui les a remplacées ou contredites.

## Ce qui a changé (résumé)

`rnd digest --since <git ref or YYYY-MM-DD> [--json]` compare la bibliothèque à un commit antérieur (analysé à partir des objets Git en mémoire sans toucher à l’arborescence de travail, à l’index Git, à `rnd.db` ou aux fichiers temporaires) par rapport à l’arborescence actuelle :

```bash
python -m rnd digest --since v1.1.24.0.14
python -m rnd digest --since 2026-11-19 --json
```

Il signale les entrées ajoutées, les affirmations ajoutées, les affirmations supprimées, les modifications d’état des affirmations (`old_state -> new_state` avec ce qui les a remplacées ou contredites), et les questions ouvertes, répondues (avec les identifiants des affirmations de réponse) et mises en attente, ainsi que les nombres. Une date `YYYY-MM-DD` correspond au commit le plus récent le long de la ligne du premier parent de la branche actuelle (`HEAD`) dont la date du committer est ce jour-là ou avant. Les affirmations correspondent par `id` lorsque les deux côtés en ont une, sinon par `(entry, exact text)`, de sorte qu’une affirmation reformulée sans identifiant apparaît comme une affirmation supprimée et une affirmation ajoutée, et non comme une modification d’état.

## Questions ouvertes

Les questions ouvertes sont stockées sous forme de fichiers Markdown individuels dans `questions/` avec les statuts `open`, `investigating`, `answered` ou `parked` :

```bash
python -m rnd new-question "Does X hold on Y?" --field systems
python -m rnd questions --status open --json
```

Lorsque le `status` d’une question est `answered`, sa liste `answered_by` dans l’en-tête doit nommer au moins un identifiant d’affirmation existant ; `rnd check` traite une question `answered` sans identifiant d’affirmation existant comme une erreur. Les questions sont indexées dans `rnd.db` et renvoyées par `rnd search` et `rnd show`.

## Journal des échecs de recherche locale

Lorsque `rnd search` ne renvoie aucune correspondance, il ajoute une ligne JSON (`time` et `query`) à un fichier `.misses.jsonl` local à côté de `rnd.db` (`rnd.misses.jsonl` dans le répertoire du dépôt, ignoré par Git ; ou `<stem>.misses.jsonl` à côté de `--db` / `RND_DB`, de sorte que `--db foo.db` écrive `foo.misses.jsonl` à côté, et non `foo.db.misses.jsonl`).
Rien d’autre n’est enregistré, rien n’est jamais envoyé sur le réseau, `RND_NO_USAGE=1` désactive l’enregistrement, et la suppression du fichier le supprime complètement. `rnd stats --usage` affiche le nombre total d’échecs et les requêtes les plus fréquemment non trouvées.

## Fichiers d’instrumentation et éléments facultatifs

- **Fichiers d’instrumentation (`instruments/*.md`) :** modifiés uniquement par l’équipe de R&D dans une diff examinée dont la description répertorie chaque fichier d’instrumentation modifié, et non par une étape ou une commande qui résume le contenu externe (`rnd watch`, `rnd probe`, `rnd collect`, `rnd catalog sync`).
- **Dépendances de base et éléments facultatifs :** la base de `rnd` reste uniquement la bibliothèque standard de Python. Tout élément facultatif se trouve dans un groupe d’adhésion et est importé de manière paresseuse ; une commande qui nécessite un élément facultatif manquant échoue avec `MISSING_EXTRA` et un indice d’installation.

## Packs de données

Les données traitées trop volumineuses ou trop complexes pour être incluses dans le clone sont proposées sous forme de **pack de données :** les octets sont stockés dans un dépôt de jeu de données Hugging Face (privé jusqu’à sa publication), et la bibliothèque ne conserve qu’un petit manifeste. Le modèle d’intégrité provient de [research-packs](https://github.com/mcp-tool-shop-org/research-packs) : un manifeste, un SHA-256 pour chaque fichier, une commande de vérification et une liste.

```bash
rnd datapack build natural-errors --source experiments/natural-errors  # reads datapacks/natural-errors/spec.json
rnd datapack list
hf download mcp-tool-shop/rnd-natural-errors --repo-type dataset --local-dir ne
rnd datapack verify natural-errors --copy ne/files                      # PASS when every byte matches
```

- **Chaque fichier doit avoir une licence** dans la spécification. Les résultats du modèle sont soumis aux conditions du modèle (par exemple, « Créé avec Llama » pour les résultats de Llama 3.1). `rnd datapack build` refuse un pack qui laisse un fichier sans couverture de licence.
- **Chaque modèle de génération est verrouillé** (digest Ollama, révision HF ou identifiant de modèle API), avec son rôle.
- **`rnd check` valide chaque manifeste** et échoue si un manifeste a été modifié manuellement.
- Le chargement inclut `datapack.json` à côté des fichiers, de sorte que chacun puisse vérifier sans ce dépôt : `pip install mcptoolshop-rnd`.

## Enregistrements d’expériences collectés

Un dépôt d’outils enregistre ses propres spécifications et enregistrements d’exécution préenregistrés (les reçus de interlock), de la même manière que chaque dépôt enregistre sa carte Atlas. La bibliothèque ne publie qu’une copie réduite des nombres, créée par `rnd collect` à partir du dépôt d’outils à des commits fixes :

```bash
rnd collect                 # list the experiments that collect records
rnd collect e4b             # read each source with git show, trim it, write experiments/e4b/results/
rnd collect e4b --check     # recompute every output; exit 1 if any differs from the committed file
```

- **`experiments/<name>/collect.json`** indique le nom du dépôt, le clone frère à partir duquel il est lu
(`--clone` permet de remplacer cette valeur), ainsi que chaque source : son chemin, le commit, le SHA-256 de ses octets, la
sortie et la fonction de suppression dans le `extract.py` de l’expérience.
- **Une source fixe ne change jamais.** Les octets qui ne correspondent plus au hachage de la référence sont rejetés.
- **Chaque enregistrement contient des informations sur son origine :** le dépôt, le chemin de la source et le SHA-256 des
  octets sources réduits.
- **Chaque sortie est sécurisée avant d’être écrite.** Aucun chemin d’accès à la machine, aucun répertoire personnel ou
aucun champ d’environnement n’est conservé, et un module d’expérience peut ajouter une protection plus stricte. Rien n’est
écrit en cas de refus.

## Tester un outil avant une expérience

`rnd probe <url> …` répond aux premières questions concernant un outil ou un modèle à partir de l’API propre à chaque source,
et non à partir d’un résumé d’une page web :

- **GitHub** (via `gh api`, ce qui utilise votre identifiant GitHub CLI) : la licence, si le dépôt est archivé, le dernier push, la dernière version et une recherche de code pour « télémétrie ». Une correspondance est une piste à explorer, et non une preuve ;
l’absence de correspondance n’est pas non plus une preuve.
- **Hugging Face :** la balise de licence, ou pour « autre », le nom et le lien de la licence de la fiche ; contrôle d’accès ; la dernière modification.
- **PyPI et npm :** la licence, la dernière version et la date de publication.
- **rnd lui-même :** une recherche de mot exact pour le nom, afin de savoir si la bibliothèque le contient déjà.

Une source inaccessible est signalée comme inconnue, avec la raison.

## Surveillance des sources

`rnd watch` vérifie les sources dans [docs/watchlist.json](docs/watchlist.json) et signale ce qui est nouveau depuis
la dernière vérification :

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

Ce qui a été observé est conservé dans un fichier d’état en dehors du dépôt (`--state`, sinon `$RND_WATCH_STATE`, sinon `Path.home() / ".rnd" / "watch-state.json"`, `~/.rnd/watch-state.json`), sauf si `--no-save` est spécifié.
La première vérification d’une source sert de référence : elle enregistre les éléments actuels et ne signale aucun élément comme étant nouveau. Une version préliminaire n’est jamais signalée comme étant la dernière version d’une source ; s’il existe une version préliminaire plus récente, elle est affichée à côté de la dernière version. Les notes de version GitHub et les messages de commit sont conservés dans la sortie JSON, afin qu’un lecteur n’ait pas à récupérer chaque page. Une source qui
est inaccessible est signalée comme inconnue, et son état est laissé tel quel afin que rien ne soit ignoré silencieusement.

La commande représente la moitié déterministe d’un rituel hebdomadaire (Director, 2026-10-13). Un explorateur examine les nouveaux éléments,
teste tout outil candidat avec `rnd probe`, vérifie la bibliothèque avec `rnd search --exact` et rédige un court
rapport classé : ce qu’il faut archiver, ce qu’il faut essayer et ce qu’il faut ignorer. Ajoutez une source par le biais d’une demande de tirage et expliquez pourquoi elle
est importante.

## Relation avec les autres outils du studio

- **readouts** est l’étagère vérifiée que ce banc alimente (voir ci-dessus).
- **research-os** crée un ensemble de preuves gelées et contrôlées pour un sujet. Un sujet sur lequel
une décision dépend peut évoluer vers un ensemble research-os, lié à l’entrée.
- **repo-knowledge** indexe les propres dépôts du studio ; cette bibliothèque couvre
les connaissances provenant de sources externes.
- Les informations recueillies lors de la conception de quelque chose doivent également être conservées ici, afin qu’elles survivent
à la session qui les a produites.

Consultez `python -m rnd tools` pour obtenir le registre complet des instruments, et
[docs/standards.md](docs/standards.md) pour savoir comment le flux de travail se compare aux
normes de flux de travail du studio.

## Sécurité et confiance

- **Données écrites**, en fonction de leur emplacement :
- **À l’intérieur de ce dépôt** (la bibliothèque : `--library`, sinon `$RND_ROOT`, sinon le dossier le plus proche, situé dans ou au-dessus du répertoire de travail, qui contient `entries/` et `instruments/`, sinon la copie de travail du dépôt depuis laquelle le paquet est exécuté) : `rnd new` (un nouveau fichier sous `entries/` ou `instruments/`, sans jamais écraser), `rnd new-question` (`questions/`), `rnd new-experiment`,
  `rnd runs record` et `rnd collect <name>` (`experiments/<name>/`),
  `rnd claims assign`, `rnd reconcile` et `rnd sync` (lignes d’affirmations et nombres liés dans les fichiers Markdown existants), `rnd change` (`changes/`), `rnd bump`
  (`mcptoolshop_rnd/__init__.py` et `CHANGELOG.md`, via des fichiers temporaires
  à côté de chacun, et il supprime les fragments `changes/` qu’il a utilisés),
  `rnd catalog sync` (`catalogs/<name>/catalog.json`), `rnd datapack build`
  (`datapacks/<name>/datapack.json`) et `rnd layout` (`docs/layout.json`).
- **L’index :** `rnd.db`, ou le chemin indiqué par `--db` ou `$RND_DB`, avec un fichier `.db.tmp` temporaire à côté, pendant sa construction. `rnd build` l’écrit, et chaque commande qui lit l’index (`search`, `show`, `list`, `tools`,
`stats`, `catalog`, `claims`, `questions`, `sql`, `runs`, `ledger`, `where`,
`probe`) le reconstruit d’abord lorsqu’un fichier source a été modifié. Le journal des échecs de recherche `rnd.misses.jsonl` se trouve à côté (voir ci-dessous).
- **Votre dossier personnel :** `rnd watch` écrit son fichier d’éléments consultés dans `--state`, sinon
`$RND_WATCH_STATE`, sinon `~/.rnd/watch-state.json` (construit dans le code comme
`Path.home() / ".rnd" / "watch-state.json"`), où il reste entre les exécutions. Il est écrit via un fichier `.tmp` à côté.
`--no-save` saute l’écriture.
- **Les espaces de stockage de données brutes, en dehors de ce dépôt :** `rnd raw ingest`, `rnd raw private` et
`rnd raw relicense` écrivent dans l’espace de stockage public (`--public`, sinon `$RND_DATA`,
sinon `../rnd-data`) et l’espace de stockage privé (`--private`, sinon `$RND_DATA_PRIVATE`, sinon `../rnd-data-private`
à côté de la bibliothèque ; lorsque `rnd raw` est exécuté en dehors d’une bibliothèque, `rnd-data-private`
à côté de l’espace de stockage public). `rnd raw ingest` place également
chaque fichier de plus de 256 Ko dans l’espace de stockage des blobs, sous `blobs/` dans le dossier
dont le nom est défini par `$RND_DATA_STORE_D` ou par l’entrée `"d"` de l’espace de stockage public `store.local.json` (il n’y a pas de valeur par défaut ; en l’absence de valeur, l’ingestion est refusée). Les blobs sont écrits via un fichier `.tmp` à côté et marqués comme étant en lecture seule. Avec `--link`, un nouveau blob est
un lien physique vers le fichier source, de sorte que **ce fichier source devient également en lecture seule** (un blob
déjà présent dans l’espace de stockage est laissé tel quel, ainsi que son fichier source) ; sans `--link`, le
fichier source n’est pas modifié. `rnd raw ingest --update` supprime les anciens petits fichiers d’une exécution dans
les deux espaces de stockage avant d’écrire les nouveaux. `--dry-run` n’écrit rien.
- **Lecture, jamais écriture :** `rnd readouts` (SQLite en mode lecture seule), les clones sources de `rnd collect` (`git show`), `rnd raw verify`, `rnd datapack verify --copy`,
  `rnd runs record --from`, `rnd abmine`, ainsi que `rnd similar` et `rnd digest`,
  qui fonctionnent en mémoire et n’écrivent rien nulle part : aucun fichier temporaire, aucune
  modification de l’arbre de travail, de l’index Git ou de `rnd.db`.
- **Code exécuté :** `rnd collect <name>`, avec ou sans `--check`, charge et exécute
  `experiments/<name>/extract.py` (ou le module nommé par le fichier `collect.json` de ce dossier)
  à partir de la bibliothèque (`mcptoolshop_rnd/collect.py:142-149`). Python peut
mettre en cache le bytecode de ce module dans `experiments/<name>/__pycache__/`. `rnd` limite
ce qu’il écrit lui-même à `experiments/<name>/` ; il ne limite pas ce que le code
du module lui-même fait, donc exécutez-le uniquement sur une bibliothèque en laquelle vous avez confiance.
- **En dehors de la commande `rnd` :** le paquet inclut également
`mcptoolshop_rnd.localbuilders`, l’ensemble d’outils de l’expérience local-builders. Aucune commande `rnd` ne l’exécute. Exécuté directement (par exemple
`python -m mcptoolshop_rnd.localbuilders.runner`), sur la machine louée pour laquelle il
a été écrit et en partie en tant que root, il crée, supprime et modifie le propriétaire et les permissions des fichiers situés sous les chemins
que son appelant transmet (chemins de travail, de dossier personnel, d’historique, d’environnement virtuel, de reçu, de journal,
de rapport, de répertoire secret et de sonde de confinement), et son système de notation utilise un dossier temporaire dans le dossier temporaire du système d’exploitation, supprimé une fois l’opération terminée.
- **Données non modifiées :** aucune commande `rnd` n’écrit, ne supprime ou ne modifie un fichier
ailleurs. Elle ne stocke ni ne lit d’informations d’identification.
- **Réseau :** aucun, sauf `rnd catalog sync`, `rnd probe` et `rnd watch`,
qui lisent les métadonnées publiques ou appellent l’API GitHub via votre propre connexion CLI `gh`
lorsque vous les exécutez.
- **Permissions :** accès ordinaire aux fichiers. Aucune commande `rnd` n’a besoin de droits élevés, et il n’y a pas de service d’arrière-plan.
- **Journal d’utilisation locale uniquement :** rien n’est collecté ni envoyé nulle part. Lorsque `rnd search`
ne renvoie aucune correspondance, il ajoute une ligne (heure UTC et requête) à `rnd.misses.jsonl`
à côté de `rnd.db` (ignoré par Git dans le dépôt ; avec `--db foo.db`, `foo.misses.jsonl`
à côté, pas `foo.db.misses.jsonl`, et de même pour `$RND_DB`). Définissez
`RND_NO_USAGE=1` pour le désactiver et supprimez le fichier `.misses.jsonl` à tout moment pour l’effacer. Aucune autre donnée d’utilisation n’est enregistrée.
- **Hygiène du dépôt public :** avant chaque envoi, l’arborescence est analysée pour détecter
les chemins du répertoire personnel et l’identité de l’opérateur.

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
[NVIDIA/skills](https://github.com/NVIDIA/skills) sous les licences de ce projet
(Apache-2.0 pour le code, CC-BY-4.0 pour le texte des compétences).

---

<p align="center">Built by <a href="https://mcp-tool-shop.github.io/">MCP Tool Shop</a></p>
