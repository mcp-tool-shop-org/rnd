---
id: 2026-10-13-multi-repository-atlas-research-grounding-for-the-build-up
title: "Multi-repository Atlas: research grounding for the build-up"
date: 2026-10-13
kind: decision
relevance: act
fields: [studio-tooling]
tags: [atlas, multi-repo, study-swarm, mcp]
---

> **Note (2026-10-13):** the atlas-mcp-utility experiment this entry refers to was withdrawn as badly designed. Only its harness remains, and it is unvalidated. No result from that experiment should be cited.

## Summary

On 2026-10-13 the Director ruled that Atlas is built up before any testing. Testing means the atlas-mcp-utility
pilot and its repository ladder. The build-up has three parts:
- AM's CI annotations;
- the test-file rule fix (testing-os#158);
- multi-repository Atlas.

Atlas 1.26.0 answers about one checkout per server, and its maps hold no edges between repositories. An import of
another repository's published package is not an edge.

To ground the multi-repository design, R&D ran a study-swarm: four Sonnet researchers in parallel, one per
load-bearing question.
1. How do production tools key dependency edges between repositories?
2. What does the evidence say about tool count, schema overhead and repository maps for agents?
3. How does a change propagate across package boundaries, and how well can static analysis follow it?
4. How should cross-repository agent tasks be designed and measured?

Each answer below is tied to a design implication. The researchers read their sources through a summarising fetch
tool, and some only at abstract level. Every claim is therefore `[unverified]` until someone reads the source for a
decision that depends on it.

## Key points

**1. The surface: one server with a repository argument, not one server per repository.**
- **Context files:** Gloaguen et al. 2026 found that context files such as AGENTS.md gave no significant gain and
  raised cost by about 20%. Repository overviews didn't help agents find the right files faster. Tools the file
  named were used far more.
- **Tool count:** RAG-MCP (2025) and MCPVerse (2025) found that tool-selection accuracy falls as the tool set grows.
  Anthropic's tool-search report (2025) puts 58 tools at about 55K tokens of definitions.
- **Name collisions:** Microsoft Research (2025) found 775 tool names shared across 1,470 MCP servers.
- **So:** N servers means 7×N schemas and repeated names on every turn. One server keeps the same seven tools for
  any N, with an optional `repo` argument that defaults to the working repository, plus a cheap repository-listing
  call. This also removes the fixed-overhead bias the ladder had to report around.

**2. The edge: a package-import fact in the consumer's map, joined at query time.**
- **How production tools do it:**
  - SCIP gives every symbol a package (manager, name, version) and links repositories only at the exact imported
    version.
  - GitHub's dependency graph pins each snapshot to a commit and lists resolved dependencies as purls.
  - deps.dev and Renovate keep the declared range apart from the resolved version.
  - deps.dev labels each version-to-repository link by its basis: attested or unverified.
  - Backstage marks a stale entity as an orphan instead of deleting it.
  - Bazel gives unpublished code its own override route.
- **So:**
  - The consumer's map records a `package-import` edge, from a file to a package purl. The resolved version comes
    from the lockfile, and the declared range is kept as its own field.
  - The producer's map already lists the packages it publishes.
  - The multi-repository server joins the two at query time. No map holds the join, so each map stays a fact about
    its own repository, and the org's one-map-per-repository rule is unchanged.
  - Each joined edge states:
    - the declared range;
    - the resolved version;
    - both map commits;
    - its basis: attested, the `repository` field, or manual.
  - It flags **skew** when the producer checkout isn't the commit that published the resolved version, and
    **orphan** when the producer has no map.
  - Unpublished workspace packages get their own `local-override` kind.

**3. Reach across repositories: two tiers, counted, never a promise.**
- **The evidence:**
  - Ochoa et al. 2022 (Maven) found that about 15% of patch and 38% of minor upgrades still broke the API. Yet only
    7.9% of clients were hit, because most changed declarations are never used.
  - Hejderup and Gousios 2022 found that client tests exercise only about 58% of direct and 20% of transitive
    dependency calls, and a static reachability check caught more injected faults than the tests did.
  - Legunsen et al. 2016 found that file-level static dependency tracing is the workable resolution, and is
    sometimes unsafe.
- **So:** reach crosses a repository boundary in two tiers.
  - **Declared dependency** is certain: the lockfile installs the package.
  - **Uses the changed export** is inferred: a named import of that symbol. Barrel re-exports, dynamic `require` and
    type-only changes are marked uncertain.
- **The answer reads like BreakBot's:** "2 of 3 consumers in this workspace use this export". It never says "will
  break".
- **A semver bump is shown only as context,** beside an API-surface diff.
- **Every answer lists what Atlas can't see:**
  - unmapped or private consumers;
  - runtime loading;
  - the version actually installed;
  - whether downstream tests cover the call site.
- **Before "inferred" is trusted,** Atlas's own precision and recall are measured on past breaking changes seeded
  from fleet history. Li et al. 2013 found published impact-analysis figures aren't comparable, so the only number
  that counts is our own.

**4. Measuring it: what the ladder takes from the benchmark literature.**
- **Keys from the import graph,** so each key provably needs the added repository (CrossCodeEval).
- **Each task tagged** by hop count and files in its key (Multi-SWE-bench), and by whether it needs a fact first
  seen in the newest repository (RepoBench).
- **A no-workspace probe per task,** to drop tasks a model answers from memory. The SWE-Bench Illusion paper found
  file-naming accuracy of up to 76% on benchmark repositories against up to 53% elsewhere, and SWE-QA-Pro drops
  questions a no-tools baseline can answer.
- **Repeats sized from the pilot's variance.** Bjarnason et al. 2026 found single-run pass@1 shifting 2 to 6 points
  even at temperature 0.
- **Pairs clustered by task** (Miller 2024).

**5. An outside model's consult (Kimi K3, 2026-10-13), and R&D's rulings.**

The Director asked for an outside model's view. Kimi K3 wrote its own design first, before reading ours. It landed
on the same structure:
- one server with a `repo` argument and a listing tool;
- edges recorded in the consumer's map, with the declared range and the resolved version kept apart;
- a join at query time;
- counted, tiered reach;
- a seeded precision check.

Two independent routes reaching one design is some evidence the design is sound.

R&D checked its two load-bearing claims about Atlas's code at testing-os main:
- **The repository allow-list:** the production spec's Part 1 item 6 already plans it, as Kimi said. It takes roots
  fixed at start, compares real paths after links resolve, and refuses with `ATLAS_SIDECAR_REPO_NOT_ALLOWED`.
- **`--ref`:** it exists, but only for `explain` and `gaps`, not for reach or the sidecar. Kimi's "already does
  exactly this" overstates it.

| Point | Ruling |
|---|---|
| 5.1 Join to the locked version's map, not the producer checkout (high) | **Accepted, with a change.** The join walks the producer's map at the commit that published the locked version, when that commit is known and holds a map. Otherwise it uses the checkout's map and states the skew. Extending `--ref` reading to reach and the sidecar is build work. |
| 5.2 Gate the decision on the seeded check (medium-high) | **Accepted, with a change.** A reach tier that hasn't passed the check is switched off in the pinned build, rather than left on and its tasks excluded later. |
| 5.3 A skew state of unknown (medium) | **Accepted.** States are match, ahead, behind and unknown. Unknown is the default and is never read as match. |
| 5.4 TypeScript's type-level breaks (medium) | **Accepted, with a change.** For TS edges, three tiers: declared dependency (certain); a value import of the changed export (inferred, runtime consequence); a type-only import (inferred, build consequence). Kimi's "deterministically breaks" overstates it, because a type change can be compatible. Reach reports use, not breakage. |
| 5.5 Adopt the production spec's allow-list (low) | **Accepted,** including its one security review. |
| 6.1 The anchors' trend measures distraction cost (high) | **Accepted.** The ladder decides on the cross-repository tasks pooled over rungs 2 to 4. The anchors become a reported distraction-cost curve. |
| 6.2 Authors who know Atlas shape the tasks (medium-high) | **Accepted.** Four of each rung's twelve cross-repository tasks are written blind to Atlas, or mined from fleet history, and reported apart. |
| 6.3 Page's L is thin (medium) | **Accepted.** Anchors run twice per rung, with Spearman's correlation reported beside the test. |
| 6.4 "Nearest commit before" can invent a state (medium) | **Accepted.** Pins are the release commit, and a fallback is a declared skew fact. |
| 6.5, 6.6 Format errors; drift sentinel (low) | **Accepted,** both reported. |
| 7 CF09 to CF13; cut lists read as whole; correlated map defects | **The first two are accepted:** CF09 to CF13 leave rung 1's decision set, and cut-list misreads are reported. **The third is named as a threat and not fixed;** known defects at the pin are listed in every report. |
| 8 Evidence | **No misreading found.** The Anthropic figure is already marked vendor, and no decision rests on it. Three missed npm sources are recorded below as recalled and unverified, to be read before any decision uses them. |
| 9 Build order and scope | **Accepted.** The seeded check is built alongside reach, and it blocks the labels, not reach. Skew and orphan states show in the repository listing. One server per checkout runs as arm N on rungs 2 to 4. |

**Sources Kimi says we missed** (recalled by Kimi, not yet read by R&D):
- Bogart, Kästner, Herbsleb and Thung 2016, on how ecosystems negotiate breaking changes. Our own researcher dropped
  it because it couldn't confirm the venue.
- Decan and Mens, on npm's semantic-versioning compliance and range-versus-lock behaviour.
- Mirhosseini and Parnin 2017, on how npm projects respond to automated dependency-update pull requests.

## Studio relevance

**The decision for the Atlas session's build-up** (R&D's ruling, amended after Kimi K3's consult), in this order:
1. AM and testing-os#158, already under way.
2. **The surface:**
   - `repo` arguments, under the production spec's allow-list (start-time roots, real paths,
     `ATLAS_SIDECAR_REPO_NOT_ALLOWED`, one security review);
   - a repository-listing tool that reports each map's commit and engine version, and the skew or orphan state of
     each link.
3. **The edge:** `package-import` in each map, npm and pnpm lockfiles first because the ladder's chain is TypeScript,
   with uv later. This changes every map, so it ships with the fleet's next engine pin wave.
   - A link can have two publishers of one name. When it does, every candidate is reported, never one picked.
   - `workspace:` and `file:` links are a kind of their own.
4. **Cross-repository reach, joined at query time,** to the locked version's map where it is known:
   - tier 1, the declared dependency, is certain;
   - the inferred tiers are value imports and type-only imports;
   - skew is match, ahead, behind or unknown.
5. **A seeded precision and recall check** in testing-os, built alongside reach. A tier that hasn't passed it is off
   in the pinned build.

**The smallest version worth testing** is points 2 to 4 with tier 1 only, then the inferred tiers once they pass.

**Then one pin amendment,** and the pilot and the ladder run on that release. The ladder's arm B becomes this
server, and one server per checkout runs as arm N (experiment amendment 6).

**Slices, as Atlas scoped them and R&D ruled (2026-10-13):** AN, AO, AP, then AQ alongside AP's end. That's
about six Atlas sessions, plus the pin wave.
- **AN, the surface:**
  - `--repos <file>` is the allow-list when given, and the ladder always uses it;
  - roots never widen after start;
  - an ambiguous name is refused with every candidate listed, and a network (UNC) root is refused;
  - the security review is a different-family check: R&D writes the brief, and Mike runs it by hand.
- **AO, the edge:**
  - purls follow the spec (`pkg:npm/%40scope/name`);
  - an unknown resolved version carries a reason;
  - the fleet check allows zero wrong facts in the sample.
- **AP, reach:** a "manual" basis is a declared mapping in `boundaries.yaml`, never inferred.
- **AQ, the bar, set before mining:**
  - the inferred tiers annotate tier 1 and never remove a consumer from it;
  - a tier turns on only with a seed of at least 20 breaking changes, recall at least 0.8 on the Wilson 95% lower
    bound, and precision at least 0.8;
  - labels are fixed in advance, and consumers that never adopted the version are excluded.
- **One release for the whole ladder,** pinned when AQ reports. A tier that passes later gets its own amendment,
  never a mid-ladder engine change.

**The ladder's rung banks adopt the four measurement points in Key points 4,** by the bank amendments.

**Not adopted yet:** an AGENTS.md arm. Gloaguen predicts no gain and higher cost, and the ladder's question is
Atlas, not context files. One finding is worth a later look: tools a context file names get used far more. That
belongs in a kickoff-wording experiment, not this one.

## Claims

- [unverified] Bogart et al. 2016, Decan and Mens, and Mirhosseini and Parnin 2017 bear on npm breaking-change and update behaviour (recalled by Kimi K3, 2026-10-13; not yet read)
- [verified] Atlas's production spec plans a `repo` argument honoured only under start-time roots by real path, refused as `ATLAS_SIDECAR_REPO_NOT_ALLOWED` (via: R&D's read of docs/atlas-production.spec.md at testing-os main, 2026-10-13)
- [verified] Atlas 1.26.0's `--ref` reads a map at a ref for `explain` and `gaps` only (via: R&D's read of packages/atlas README and adapter at testing-os main, 2026-10-13)

- [unverified] Context files (AGENTS.md) gave no significant resolve-rate gain and raised agent cost by about 20% (Gloaguen et al. 2026, read by a researcher through a summarising fetch)
- [unverified] Tool-selection accuracy falls as the tool set grows, and retrieving only relevant tool descriptions raises it (RAG-MCP 2025; MCPVerse 2025, abstract level)
- [unverified] About 15% of patch and 38% of minor Maven upgrades broke the API, but only 7.9% of clients were affected (Ochoa et al. 2022)
- [unverified] Client tests exercised about 58% of direct and 20% of transitive dependency calls (Hejderup and Gousios 2022)
- [unverified] SCIP links repositories only when both are indexed at the exact imported version (Sourcegraph docs)
- [unverified] Single-run agent pass@1 shifts by 2 to 6 points depending on the run, even at temperature 0 (Bjarnason et al. 2026)

## Sources

- [primary] https://arxiv.org/abs/2602.11988 — Gloaguen, Mündler-Sasahara, Müller, Raychev, Vechev 2026, Evaluating AGENTS.md
- [primary] https://arxiv.org/abs/2505.03275 — Gan and Sun 2025, RAG-MCP
- [primary] https://arxiv.org/abs/2508.16260 — Lei, Yang, Sun, Lin 2025, MCPVerse
- [primary] https://www.anthropic.com/engineering/advanced-tool-use — Anthropic engineering, 2025-11-24 (vendor report)
- [primary] https://www.microsoft.com/en-us/research/blog/tool-space-interference-in-the-mcp-era-designing-for-agent-compatibility-at-scale/ — Fourney, Payne, Murad, Amershi 2025
- [primary] https://arxiv.org/abs/2503.09089 — Chen et al. 2025, LocAgent
- [primary] https://arxiv.org/abs/2309.12499 — Bairi et al. 2023, CodePlan
- [primary] https://aider.chat/2023/10/22/repomap.html — Aider's repository map, 2023
- [primary] https://ecma-international.org/publications-and-standards/standards/ecma-427/ — Package-URL, ECMA-427
- [primary] https://github.com/sourcegraph/scip/blob/main/scip.proto — SCIP schema
- [primary] https://docs.github.com/en/rest/dependency-graph/dependency-submission — GitHub dependency submission API
- [primary] https://docs.deps.dev/api/v3/ — deps.dev API v3
- [primary] https://slsa.dev/spec/v1.0/provenance — SLSA Provenance v1.0
- [primary] https://kythe.io/docs/schema/ — Kythe schema
- [primary] https://bazel.build/external/module — Bazel modules
- [primary] https://backstage.io/docs/features/software-catalog/descriptor-format — Backstage descriptor format
- [primary] https://github.com/renovatebot/renovate/blob/main/docs/development/adding-a-package-manager.md — Renovate
- [primary] https://doi.org/10.1016/j.jss.2016.04.008 — Raemaekers, van Deursen, Visser 2017
- [primary] https://doi.org/10.1007/s10664-021-10052-y — Ochoa, Degueule, Falleri, Vinju 2022, Breaking Bad?
- [primary] https://arxiv.org/abs/2111.05132 — BreakBot
- [primary] https://doi.org/10.4230/LIPIcs.ECOOP.2018.7 — Mezzetti, Møller, Torp 2018
- [primary] https://arxiv.org/abs/2109.11921 — Hejderup and Gousios 2022
- [primary] https://doi.org/10.1007/s10664-021-10071-9 — Hejderup et al. 2022, Präzi
- [primary] https://doi.org/10.1145/3460319.3464836 — Nielsen, Torp, Møller 2021
- [primary] https://mir.cs.illinois.edu/~marinov/publications/LegunsenETAL16StaticRTS.pdf — Legunsen et al. 2016
- [primary] https://doi.org/10.1002/stvr.1475 — Li, Sun, Leung, Zhang 2013
- [primary] https://arxiv.org/abs/2306.03091 — Liu, Xu, McAuley 2023, RepoBench
- [primary] https://arxiv.org/abs/2310.11248 — Ding et al. 2023, CrossCodeEval
- [primary] https://arxiv.org/abs/2603.03194 — Chen et al. 2026, BeyondSWE
- [primary] https://arxiv.org/abs/2506.12286 — Liang, Garg, Zilouchian Moghaddam 2025, The SWE-Bench Illusion
- [primary] https://arxiv.org/abs/2603.16124 — SWE-QA-Pro 2026
- [primary] https://arxiv.org/abs/2504.02605 — Zan et al. 2025, Multi-SWE-bench
- [primary] https://arxiv.org/abs/2602.07150 — Bjarnason, Silva, Monperrus 2026, On Randomness in Agentic Evals
- [primary] https://arxiv.org/abs/2411.00640 — Miller 2024, Adding Error Bars to Evals
- [[2026-10-13-atlas-testing-os-rnd-buildup]] — the build-up program this extends
