[R&D → Argon] rnd at scale, round 1: review a plan for where the research library's data lives, and the databases that find it. A full review, please.

## What this is

rnd (`mcp-tool-shop-org/rnd`, public) is a game studio's research bench: Markdown entries, experiment folders and
a generated SQLite index, driven by a Python CLI. readouts is the shelf, with verified knowledge bases. The
Director wants rnd built up so it can scale without becoming a mess: databases, and maybe another repository,
outside readouts, for raw and bulk data.

## What to audit

`PLAN.md` (plan v1), in the bundle `rnd-scale-plan-v1-code.txt`. The bundle starts with `SHA256:` over its body and
`LINES:`.

The bundle also holds, for reference, from rnd main `c04ab4e`:
- `README.md`'s Layout, Data packs and Collected experiment records sections;
- `mcptoolshop_rnd/store.py`'s schema;
- the `natural-errors` data pack's `spec.json`, as an example of the existing manifest format.

## Where to look hardest

1. **§1, the measured state.** Do the problems in §2 follow from it, and is anything missing?
2. **§3, the tiers.** Is each file's home unambiguous? Are the T2 limits right?
3. **§5, the databases.** Is rebuilding from text and manifests the right model for runs and ledgers, as their
   number grows?
4. **§6–7, rnd-data and the phases.** Is P3 (backups first) correctly placed? Is anything irreversible not in §8?
5. **Simplicity.** Anything over-built for a one-human studio? The plan should stay lean. Say what to cut.

The plan's own questions are in §9. Answer them, and add anything else you find.

**Severity levels:** `blocking`, `before P4`, `not blocking`.

Reply under `## <date> · rnd scale plan · round 1 · v1`.
