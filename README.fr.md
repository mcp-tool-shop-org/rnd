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

Le banc de recherche du studio. Les résultats de n'importe quel domaine sont rapidement intégrés sous forme de courtes entrées Markdown, chaque source étant identifiée et chaque affirmation étant marquée comme vérifiée ou non. Les expériences sont placées à côté des entrées qu'elles testent. Les catalogues externes sont mis en miroir et évalués, et un registre répertorie les outils du studio que la recherche peut utiliser. Une seule commande permet de rechercher dans l'ensemble.

## Où il se trouve : le banc devant readouts

Deux ensembles de données contiennent les connaissances du studio, et ils remplissent des fonctions différentes.

| | Recherche et développement (ce dépôt) | [readouts](https://github.com/mcp-tool-shop-org/readouts) |
|---|---|---|
| Rôle | le banc : collecte, expériences, questions ouvertes | l'étagère : bases de connaissances vérifiées |
| Rythme | une entrée en quelques minutes, les affirmations commencent à `unverified` | créées et vérifiées par des groupes d'étude |
| Forme | entrées Markdown, un sujet par entrée | une SQLite base de connaissances par domaine |
| Quel est le niveau de désordre ? | désordre intentionnel : les affirmations contestées, les impasses et les résultats intermédiaires restent visibles | pas de désordre du tout : chaque ligne est sourcée et vérifiée |

Les connaissances évoluent dans un seul sens :

1. **Banc d’essai.** Une découverte est enregistrée ici sous forme d’entrée. Ses affirmations commencent par `[unverified]`,
et sont marquées `[verified]` uniquement par une note indiquant ce qui les a vérifiées.
Les mesures effectuées sur nos propres machines sont enregistrées en tant que sources `rig`, avec leur
ensemble de tests sous `experiments/`.
2. **Étagère interne.** Une fois que les affirmations d’un sujet concernant sa capacité de charge sont confirmées, il est intégré
dans une base de connaissances dans le dépôt de travail privé readouts, ou ajouté à un dépôt existant.
**La promotion fait partie de la clôture d’une expérience** (le Directeur, 2026-10-09). Lorsqu’un résultat d’expérience est enregistré ici, sa mise à jour readouts-internal suit
dans la même session ou dans la session suivante, avec ses graphiques. Rien ne reste sur le banc d’essai
plus d’une semaine environ. Des mises à jour régulières et mineures sont préférables à une seule mise à jour importante. Le fichier README d’une expérience enregistre sa promotion sous forme d’une ligne sous son résultat :
« Promu : readouts-internal `<kb>`, vague `<n>`, `<date>` », ou la raison pour laquelle ce n’est pas encore le cas.
3. **Étagère publique.** Une base de connaissances est publiée dans le dépôt public readouts
lorsqu’elle est ajoutée à la liste d’exportation autorisée.

`rnd readouts` effectue une recherche dans chaque base de connaissances readouts à partir d’ici, de sorte qu’un seul élément
permette d’accéder aux deux dépôts. Recherchez d’abord sur le banc, puis sur l’étagère, et enfin étudiez les lacunes.

La recherche ici ne se limite pas aux domaines du studio. Chaque entrée enregistre séparément deux éléments : la nature de la connaissance et ce qu'elle signifie pour le studio (`relevance: act | watch | reference`). `reference` est un jugement favorable.

## Utilisation

Nécessite Python 3.10 ou une version ultérieure, et rien d'autre (uniquement la bibliothèque standard). Fonctionne sur Windows, macOS et Linux. À partir du répertoire racine du dépôt :

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

Chaque commande de liste prend `--json` pour les agents. `rnd.cmd` (Windows) et `rnd.sh` (shells POSIX) sont de simples wrappers, de sorte que la commande fonctionne à partir de n'importe quel répertoire.

Pour utiliser l'outil à partir d'autres projets, installez-le à partir de PyPI :

```bash
pip install mcptoolshop-rnd
```

Cela installe la commande `rnd`, et non la bibliothèque : les entrées se trouvent dans ce dépôt. La commande trouve une bibliothèque dans l'ordre suivant : `--library DIR`, puis `$RND_ROOT`, puis le dossier le plus proche, situé au niveau du répertoire actuel ou au-dessus, qui contient `entries/` et `instruments/`. En dehors d'une bibliothèque, elle s'arrête avec `NO_LIBRARY` ; seule `rnd readouts` fonctionne sans bibliothèque.

En Python, importez `mcptoolshop_rnd` : ce nom fonctionne toujours. `rnd` est conservé comme alias de compatibilité, mais un package PyPI non lié est également appelé `rnd`, et si les deux sont installés, il peut remplacer l'alias. La commande `rnd` et `python -m mcptoolshop_rnd` continuent de fonctionner de toute façon.

La bibliothèque change quotidiennement, de sorte que les versions ont cinq segments, `MAJOR.MINOR.PATCH.MICRO.NANO`. Les trois premiers segments définissent la version de l'outil `rnd` ; MICRO indique un changement structurel de la bibliothèque et NANO une mise à jour ordinaire. `rnd bump` incrémente le dernier segment par défaut et écrit une section CHANGELOG à partir des fichiers modifiés depuis le dernier tag, de sorte que chaque mise à jour reçoit sa propre petite version taguée.

Codes de sortie : `0` ok · `1` fichiers de bibliothèque non valides · `2` erreur d'utilisation ou non trouvé · `3` échec d'exécution (un outil externe ou une erreur inattendue). Les erreurs affichent un code, un message et un indice ; `--debug` ajoute la trace de la pile.

## Disposition

| Chemin | Quoi | Qui modifie |
|------|------|-----------|
| `entries/YYYY/*.md` | Entrées de recherche : la source de vérité | personnes et agents |
| `experiments/<name>/` | Configurations, entrées épinglées et reçus de résultats pour les mesures de l'équipement | personnes et agents |
| `experiments/<name>/collect.json` | Enregistrements collectés à partir d'un dépôt d'outils à des commits épinglés (`rnd collect`) | personnes |
| `instruments/*.md` | Outils et protocoles du studio que l'emplacement peut utiliser (`kind: instrument`) | personnes et agents |
| `catalogs/<name>/source.json` | D'où provient un catalogue | personnes |
| `catalogs/<name>/catalog.json` | Instantané épinglé à partir de `rnd catalog sync` | généré ; ne jamais modifier manuellement |
| `catalogs/<name>/review.json` | Adaptation et notes du studio par famille et par élément | personnes |
| `datapacks/<name>/spec.json` | Ce que contient un ensemble de données : inclure des motifs globaux, des licences, des générateurs, un hôte | personnes |
| `datapacks/<name>/datapack.json` | Manifeste à partir de `rnd datapack build` : SHA-256 de chaque fichier, licences, épingles | généré ; ne jamais modifier manuellement |
| `datapacks/<name>/hosted.json` | Où l'upload a atterri (révision du dépôt) | après un upload |
| `mcptoolshop_rnd/` | L'interface de ligne de commande | code |
| `rnd/` | Alias de compatibilité pour `mcptoolshop_rnd` | code |
| `rnd.db` | SQLite FTS5 index, reconstruit automatiquement lorsque les fichiers changent | généré ; pas dans git |

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
- [verified] A checked statement. (via: what checked it, date)
## Sources
- [primary] https://… — publisher
```

- **Niveaux de source :** `primary` (documentation du fournisseur, articles, dépôts), `secondary` (articles de référence), `aggregator` (sites de résumé, résultats de recherche par IA), `user` (fournis par une personne : diapositives, notes), `rig` (mesurés sur nos machines).
- **Confiance dans l'affirmation :** `unverified`, `verified`, `disputed`, `wrong`. Une affirmation `verified` ou `wrong` doit indiquer ce qui l'a vérifiée avec `(via: …)`.
- `[[entry-id]]` relie les entrées ; `rnd show` répertorie les liens retour.

## Ensembles de données

Les données traitées trop volumineuses ou trop complexes pour être clonées sont proposées sous forme d'**ensemble de données** : les octets se trouvent sur un dépôt de données Hugging Face (privé jusqu'à sa publication), et la bibliothèque ne conserve qu'un petit manifeste. Le modèle d'intégrité provient de [research-packs](https://github.com/mcp-tool-shop-org/research-packs) : un manifeste, un SHA-256 pour chaque fichier, une commande de vérification et une liste.

```bash
rnd datapack build natural-errors --source experiments/natural-errors  # reads datapacks/natural-errors/spec.json
rnd datapack list
hf download mcp-tool-shop/rnd-natural-errors --repo-type dataset --local-dir ne
rnd datapack verify natural-errors --copy ne/files                      # PASS when every byte matches
```

- **Chaque fichier doit avoir une licence** dans les spécifications. Les résultats des modèles contiennent les conditions de leur modèle (par
exemple, « Créé avec Llama » pour les résultats de Llama 3.1). `rnd datapack build` refuse un ensemble qui
laisse un fichier sans licence.
- **Chaque modèle de génération est verrouillé** (hachage Ollama, révision HF ou ID de modèle API), avec son rôle.
- **`rnd check` valide chaque manifeste** et échoue si un manifeste a été modifié manuellement.
- Le téléchargement inclut `datapack.json` à côté des fichiers, afin que chacun puisse vérifier sans ce dépôt :
`pip install mcptoolshop-rnd`.

## Enregistrements d’expériences collectés

Un dépôt d’outils enregistre ses propres spécifications et enregistrements d’exécution préenregistrés (les reçus de interlock),
de la même manière que chaque dépôt enregistre sa carte Atlas. La bibliothèque ne publie qu’une copie réduite des
chiffres, créée par `rnd collect` à partir du dépôt d’outils à des versions spécifiques :

```bash
rnd collect                 # list the experiments that collect records
rnd collect e4b             # read each source with git show, trim it, write experiments/e4b/results/
rnd collect e4b --check     # recompute every output; exit 1 if any differs from the committed file
```

- **`experiments/<name>/collect.json`** nomme le dépôt, le clone frère à partir duquel il est lu (`--clone` a priorité), et chaque source : son chemin, la version, le SHA-256 de ses octets, la sortie et la fonction de réduction dans le `extract.py` de l’expérience.
- **Une source verrouillée ne change jamais.** Les octets qui ne correspondent plus au hachage du verrou sont refusés.
- **Chaque enregistrement contient des informations sur sa provenance :** le dépôt, le chemin de la source et le SHA-256 des octets réduits.
- **Chaque sortie est sécurisée avant d’être écrite.** Aucun chemin d’accès à la machine, répertoire personnel ou champ d’environnement n’est conservé, et un module d’expérience peut ajouter une protection plus stricte. Rien n’est écrit en cas de refus.

## Test d’un outil avant un essai

`rnd probe <url> …` répond aux premières questions sur un outil ou un modèle à partir de l’API de chaque source, et non à partir d’un résumé d’une page web :

- **GitHub** (via `gh api`, ce qui utilise votre identifiant GitHub CLI) : la licence, si elle est archivée,
la dernière mise à jour, la dernière version et une recherche de code pour « télémétrie ». Un résultat est une piste à explorer, jamais une preuve ;
l’absence de résultat n’est pas non plus une preuve.
- **Hugging Face :** la balise de licence, ou pour « autre », le nom et le lien de la licence de la carte ; contrôle d’accès ; la dernière modification.
- **PyPI et npm :** la licence, la dernière version et la date de publication.
- **rnd lui-même :** une recherche de mot exact pour le nom, afin de savoir si la bibliothèque le contient déjà.

Une source inaccessible est signalée comme inconnue, avec la raison.

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

Ce qu’il a trouvé est conservé dans un fichier d’état en dehors du dépôt (`$RND_WATCH_STATE`, sinon `~/.rnd/watch-state.json`). La première vérification d’une source sert de référence : elle enregistre les éléments actuels et ne signale rien de nouveau. Une version préliminaire n’est jamais signalée comme la dernière version d’une source ; une version plus récente est affichée à côté. Les notes de version et les messages de validation de GitHub sont conservés dans la sortie JSON, afin qu’un lecteur n’ait pas à récupérer chaque page. Une source inaccessible est signalée comme inconnue, et son état est laissé tel quel, afin que rien ne soit ignoré silencieusement.

La commande représente la moitié déterministe d’un rituel hebdomadaire (Director, 2026-10-13). Un explorateur lit les nouveaux éléments, teste tout outil candidat avec `rnd probe`, vérifie la bibliothèque avec `rnd search --exact`, et rédige un court rapport classé : ce qu’il faut archiver, ce qu’il faut essayer et ce qu’il faut ignorer. Ajoutez une source par le biais d’une demande de tirage et expliquez pourquoi elle est importante.

## Relation avec les autres outils du studio

- **readouts** est l’étagère vérifiée à laquelle ce banc se connecte (voir ci-dessus).
- **research-os** crée un ensemble de preuves gelé et contrôlé pour une thématique. Une thématique sur laquelle
une décision dépend peut évoluer vers un ensemble research-os, lié à l’entrée.
- **repo-knowledge** indexe les propres dépôts du studio ; cette bibliothèque couvre
les connaissances provenant de sources externes.
- Les informations recueillies lors de la conception de quelque chose doivent également s’y trouver, afin qu’elles survivent
à la session qui les a produites.

Consultez `python -m rnd tools` pour obtenir le registre complet des instruments, et [docs/standards.md](docs/standards.md) pour savoir comment le flux de travail se compare aux normes de flux de travail du studio.

## Sécurité et confiance

- **Données concernées :** fichiers dans ce dépôt (`entries/`, `instruments/`,
`catalogs/`, `experiments/`) et l’index `rnd.db`, qu’il reconstruit. `rnd
readouts` opens the readouts knowledge bases **read-only**. `rnd sql` s’exécute
contre une connexion en lecture seule.
- **Données non concernées :** rien en dehors du dépôt et de la copie readouts. Il
ne stocke aucune information d’identification et n’en lit aucune.
- **Réseau :** aucun, à l’exception de `rnd catalog sync`, qui appelle l’API GitHub
via votre propre connexion CLI `gh` lorsque vous l’exécutez.
- **Autorisations :** accès ordinaire aux fichiers. Aucun droit élevé, aucun service en arrière-plan.
- **Pas de télémétrie.** Rien n’est collecté ou envoyé.
- **Hygiène du dépôt public :** avant chaque envoi, l’arborescence est analysée pour détecter
les chemins du répertoire personnel et l’identité de l’opérateur.

Signalez les vulnérabilités comme décrit dans [SECURITY.md](SECURITY.md).

## Tests

```bash
bash verify.sh                               # tests, library check, index build, smoke
python -m unittest discover -s tests -t .    # tests only
```

## État et licence

Maintenu par le studio et utilisé quotidiennement. Code : [MIT](LICENSE). Entrées : CC BY 4.0. Le miroir des compétences NVIDIA dans `catalogs/nvidia-skills/catalog.json` reproduit les noms et descriptions des compétences à partir de [NVIDIA/skills](https://github.com/NVIDIA/skills) sous les licences de ce projet (Apache-2.0 pour le code, CC-BY-4.0 pour le texte des compétences).

---

<p align="center">Built by <a href="https://mcp-tool-shop.github.io/">MCP Tool Shop</a></p>
