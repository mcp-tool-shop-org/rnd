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

Le banc de recherche du studio. Les résultats de n’importe quel domaine sont enregistrés rapidement sous forme de courtes entrées Markdown, chaque source étant identifiée et chaque affirmation étant marquée comme vérifiée ou non. Les expériences sont placées à côté des entrées qu’elles testent. Les catalogues externes sont répliqués et évalués, et un registre répertorie les outils du studio que la recherche peut utiliser. Une seule commande permet de rechercher dans l’ensemble.

## Où il se trouve : le banc avant les affichages

Deux supports stockent les connaissances du studio, et ils remplissent des fonctions différentes.

| | Recherche et développement (ce dépôt). | [readouts](https://github.com/mcp-tool-shop-org/readouts) |
|---|---|---|
| Rôle. | le banc : collecte, expériences, questions ouvertes. | l’étagère : bases de connaissances vérifiées. |
| Rythme. | une entrée en quelques minutes, les affirmations commencent à `unverified`. | créé et vérifié par des groupes d’étude. |
| Forme. | entrées Markdown, un sujet par entrée. | une base de connaissances SQLite par domaine. |
| Quel désordre ! | désordre intentionnel : les affirmations contestées, les impasses et les résultats provisoires restent visibles | pas de désordre du tout : chaque ligne est référencée et vérifiée |

Les connaissances circulent dans un seul sens :

1. **Banc.** Un résultat y est enregistré sous forme d’entrée. Ses affirmations commencent à `[unverified]` et sont marquées `[verified]` uniquement avec une note indiquant ce qui les a vérifiées. Les mesures effectuées sur nos propres machines sont enregistrées sous forme de `rig` sources, avec leur configuration sous `experiments/`.
2. **Étagère interne.** Une fois que les affirmations essentielles d’un sujet sont confirmées, elles sont intégrées dans une base de connaissances dans le dépôt de travail privé des affichages, ou ajoutées à celle-ci.
3. **Étagère publique.** Une base de connaissances est publiée dans le dépôt public des affichages lorsqu’elle est ajoutée à la liste d’exportation autorisée.

`rnd readouts` effectue une recherche dans toutes les bases de connaissances des affichages à partir d’ici, de sorte qu’un seul emplacement donne accès aux deux supports. Recherchez d’abord dans le banc, puis dans l’étagère, et enfin étudiez les lacunes.

La recherche effectuée ici ne se limite pas aux domaines du studio. Chaque entrée enregistre deux éléments séparément : la nature des connaissances et leur importance pour le studio (`relevance: act | watch | reference`). `reference` est un verdict favorable.

## Utilisation

Nécessite Python 3.10 ou une version ultérieure, et rien d’autre (uniquement la bibliothèque standard). Fonctionne sous Windows, macOS et Linux. À partir du répertoire racine du dépôt :

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

Chaque commande de liste prend `--json` pour les agents. `rnd.cmd` (Windows) et `rnd.sh` (shells POSIX) sont de simples enveloppes, de sorte que la commande fonctionne à partir de n’importe quel répertoire.

Pour utiliser l’outil dans d’autres projets, installez-le depuis PyPI :

```bash
pip install mcptoolshop-rnd
```

Cela installe la commande `rnd`, et non la bibliothèque : les éléments se trouvent dans ce dépôt. La commande recherche une bibliothèque dans l’ordre suivant : `--library DIR`, puis `$RND_ROOT`, puis le dossier le plus proche, situé au niveau du dossier actuel ou au-dessus, qui contient `entries/` et `instruments/`. En dehors d’une bibliothèque, elle s’arrête avec `NO_LIBRARY` ; seule `rnd readouts` fonctionne sans bibliothèque. Le paquet est importé sous le nom `rnd`, tout comme un autre paquet PyPI sans lien, appelé `rnd`. Il est donc déconseillé d’installer les deux dans le même environnement.

La bibliothèque est mise à jour quotidiennement, c’est pourquoi les versions sont divisées en cinq segments : `MAJOR.MINOR.PATCH.MICRO.NANO`. Les trois premiers segments concernent l’outil `rnd` ; MICRO indique une modification structurelle de la bibliothèque, et NANO, une mise à jour ordinaire. `rnd bump` augmente par défaut le dernier segment et crée une section CHANGELOG à partir des fichiers modifiés depuis la dernière version, de sorte que chaque mise à jour se voit attribuer sa propre version mineure.

Codes de sortie : `0` ok ; `1` fichiers de bibliothèque non valides ; `2` erreur d’utilisation ou non trouvé ; `3` échec d’exécution (un outil externe ou une erreur inattendue). Les erreurs affichent un code, un message et un indice ; `--debug` ajoute la trace.

## Disposition

| Chemin. | Quoi. | Qui modifie. |
|------|------|-----------|
| `entries/YYYY/*.md` | Entrées de recherche : la source de vérité. | personnes et agents. |
| `experiments/<name>/` | Configurations, entrées épinglées et reçus de résultats pour les mesures d’équipement. | personnes et agents. |
| `instruments/*.md` | Outils et protocoles du studio que le système peut utiliser (`kind: instrument`). | personnes et agents. |
| `catalogs/<name>/source.json` | D’où provient un catalogue. | personnes. |
| `catalogs/<name>/catalog.json` | Instantané épinglé à partir de `rnd catalog sync`. | généré ; ne jamais modifier manuellement. |
| `catalogs/<name>/review.json` | Adaptation et notes du studio par famille et par élément. | personnes. |
| `rnd/` | L’interface en ligne de commande. | code. |
| `rnd.db` | Index FTS5 SQLite, reconstruit automatiquement lorsque les fichiers sont modifiés. | généré ; ne se trouve pas dans Git. |

## Format d’entrée

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

- **Niveaux de source :** `primary` (documentation du fournisseur, articles, dépôts), `secondary` (écrits réputés), `aggregator` (sites de résumé, résultats de recherche par IA), `user` (fournis par une personne : diapositives, notes), `rig` (mesurés sur nos machines).
- **Confiance dans les affirmations :** `unverified`, `verified`, `disputed`, `wrong`. Une affirmation `verified` ou `wrong` doit indiquer ce qui l’a vérifiée avec `(via: …)`.
- `[[entry-id]]` relie les entrées ; `rnd show` répertorie les liens retour.

## Relation avec les autres outils du studio

- **readouts** est l’étagère vérifiée que ce banc alimente (voir ci-dessus).
- **research-os** crée un ensemble de preuves gelé et protégé pour un sujet. Un sujet sur lequel une décision dépend peut passer à un ensemble research-os, lié à partir de l’entrée.
- **repo-knowledge** indexe les propres dépôts du studio ; cette bibliothèque couvre les connaissances provenant de l’extérieur.
- Les résultats recueillis lors de la conception de quelque chose doivent également s’y trouver, afin qu’ils survivent à la session qui les a produits.

Consultez `python -m rnd tools` pour obtenir le registre complet des instruments, et [docs/standards.md](docs/standards.md) pour savoir comment le flux de travail se compare aux normes de flux de travail du studio.

## Sécurité et confiance

- **Données concernées :** fichiers dans ce dépôt (`entries/`, `instruments/`, `catalogs/`, `experiments/`) et l’index `rnd.db`, qu’il reconstruit. `rnd readouts` opens the readouts knowledge bases **read-only**. `rnd sql` s’exécute sur une connexion en lecture seule.
- **Données non concernées :** rien en dehors du dépôt et de la copie de readouts. Il ne stocke aucune information d’identification et n’en lit aucune.
- **Réseau :** aucun, à l’exception de `rnd catalog sync`, qui appelle l’API GitHub via votre propre connexion CLI `gh` lorsque vous l’exécutez.
- **Autorisations :** accès normal aux fichiers. Aucun droit élevé, aucun service d’arrière-plan.
- **Pas de télémétrie.** Rien n’est collecté ni envoyé.
- **Hygiène du dépôt public :** avant chaque envoi, l’arborescence est analysée pour détecter les chemins du répertoire personnel et l’identité de l’opérateur.

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
