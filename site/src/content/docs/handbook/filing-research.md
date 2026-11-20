---
title: Filing research
description: The entry format, source tiers, claim confidence and links.
sidebar:
  order: 2
---

One entry per topic. Scaffold it, fill the sections in your own words, then
validate.

```bash
python -m rnd new "Singing pitch trackers" --kind finding --field audio --tag pitch
# edit entries/2026/2026-10-07-singing-pitch-trackers.md
python -m rnd check
```

## The file

```markdown
---
id: 2026-10-07-cuda-graphs        # defaults to the file name
title: CUDA Graphs
date: 2026-10-07
kind: concept
relevance: reference              # act | watch | reference
status: active                    # active | draft | superseded (optional)
fields: [gpu-computing]           # at least one; open vocabulary
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

Frontmatter is a small YAML subset: scalars, inline `[a, b]` lists, block lists,
lists of maps and block scalars.

## Kinds

| kind | for |
|---|---|
| `finding` | a fact or result learned from a source |
| `concept` | an idea, technique or principle worth knowing |
| `release` | a product, toolkit or library release |
| `paper` | a paper or formal study |
| `tool` | an external tool, library or catalogue item |
| `catalog` | a pointer to an ingested catalogue |
| `rig-fact` | a measured fact about our own machines |
| `event` | a talk, webinar or conference |
| `question` | an open question being tracked |
| `decision` | a decision taken on the strength of research |
| `instrument` | a studio tool the seat can use (lives in `instruments/`) |

## Two questions, kept apart

**What is it?** Summary and Key points describe the knowledge as it stands,
with no studio framing.

**What does it mean for us?** Studio relevance says what to do with it, and the
`relevance` field sums that up:

- `act`: something should change because of this.
- `watch`: it may matter; revisit when it moves.
- `reference`: worth knowing; nothing to do.

## Source tiers

Every source line starts with its tier.

| tier | means | needs a URL |
|---|---|---|
| `primary` | vendor docs, papers, repos, model cards | yes |
| `secondary` | reputable write-ups of primary material | yes |
| `aggregator` | summary sites, AI search output | yes |
| `user` | supplied by a person: slides, notes, pasted text | no |
| `rig` | measured on our own machines | no |

Pasted AI-search output is `aggregator` or `user`, never `primary`. If a claim
matters, find its primary source.

## Claim confidence

| tag | means |
|---|---|
| `[unverified]` | not checked yet (the default) |
| `[verified]` | checked; must end with `(via: …)` naming what checked it and when |
| `[disputed]` | sources conflict, or a later claim contradicts it |
| `[wrong]` | checked and false; must say what showed it, with `(via: …)` |
| `[superseded]` | replaced by a later claim, which it names with `(superseded-by: …)` |

Verification is proportional. Check a claim when it looks wrong, when sources
conflict, or when a decision depends on it. Do not run a verifier over every
entry by default.

Interim results are fine. Say they are interim in the title and the claim, and
update the entry when the rest lands.

## Links

`[[entry-id]]` links one entry to another. `rnd show` lists each entry's
backlinks, and `rnd check` warns about a link that points at no entry.

## Linking a claim to the one it replaces

A new finding often overturns an old claim. Say so on the new claim, by the old
claim's id, and let `rnd reconcile` mark the old one:

```markdown
- [verified] [c-7a1f03d2] The fix cuts load time to 2.1 s. (via: bench run, 2026-11-19) (supersedes: c-41c0e9aa)
```

- `rnd claims assign <entry>` gives an entry's claims stable `c-<hex>` ids.
- Run `python -m rnd similar <entry>` before filing to see the closest claims in
  other entries and print the link clauses and `rnd reconcile` command.
- A claim may state `(supersedes: id)`, `(contradicts: id)` or `(supports: id)`.
  The target must be a claim id.
- `rnd reconcile <entry>` then marks each older claim in its own file
  (`superseded-by` and `[superseded]`; `contradicted-by` and `[disputed]`, or
  keeping `[wrong]` as `[wrong]` with `contradicted-by`; `supported-by`). It
  never changes the older claim's sentence.
- `rnd search` and `rnd show` mark superseded and disputed claims and name the
  claim that replaced or contradicted them.

## Binding a number to a results file

A number copied by hand from a working file can drift. An experiment can keep its
public-safe summary numbers in `experiments/<id>/results.json`, and a number in an
entry, brief, question or experiment note can be bound to a key in it by a comment
directly after the literal:

```markdown
The judge scored 84.2%<!-- rnd:experiments/e4b/results.json#accuracy:.1% --> on the held-out split.
```

The raw file, `grep` and the index keep the plain `84.2%`; GitHub and this site
show it with no marker. `rnd sync` rewrites every bound number from its results
file, and `rnd check` fails if one differs.

## Open questions

An open question is one file under `questions/`, made with
`rnd new-question "<title>"`. Its `status` is `open`, `investigating`, `answered`
or `parked`. An `answered` question lists, in `answered_by`, the ids of the claims
that answer it.

## Recording the change

An update does not edit the version or `CHANGELOG.md`. Record it with
`rnd change "<what changed>"` (add `--level micro` for a new experiment or
catalogue). The version moves once, when a release pull request runs `rnd bump`.

## What `rnd check` enforces

Errors (exit 1): unreadable frontmatter, a bad `id`, a missing `title`, a
`date` not in `YYYY-MM-DD`, an unknown `kind`, `relevance` or `status`, no
`fields`, an unknown source tier, a URL-less `primary`/`secondary`/`aggregator`
source, an unknown claim tag, a `verified`/`wrong` claim without `(via: …)`, a
duplicate `id`, and an instrument missing `instrument_status` or `invoke`. Also:
more than one `## Claims` heading in an entry, an unclosed code fence in an entry
body, a duplicate claim id, a relation to a claim id that does not exist or a
link present on one side only (run `rnd reconcile`), a bound number that differs
from its results file or names a missing file or key, an `answered` question
with no existing claim id, and a malformed changelog fragment.

Warnings: an entry with no sources (except rig-facts and instruments), a
`[[link]]` to no entry, a `[superseded]` claim with no `(superseded-by: …)`
link, and a `[verified]` claim whose `(via: …)` names one of this repo's
experiments while its text still holds an unbound number—ignoring plain integers
(with no decimal point, percent sign, thousands separator or trailing unit) that
pair with the preceding word in the entry's title or tags or follow `RTX` or
`GTX` (3–4 digits) or `CUDA`, `PTX`, `Gemma`, `Llama`, `Qwen`, `Claude`, `GPT`
or `Phi` (1–2 digits).

## Writing rules

- Your own words. Never paste copyrighted text into an entry.
- No home-directory paths, secrets or anything that is not ours to publish. The
  repo is public.
