"""Build the "knowledge in context" request set: the same 124 records, plus what we want.

Each request keeps the identical sense-si state the other models saw and adds:
  - phrase_evidence: ai-jam-sessions' per-phrase join measurements (scalars only);
  - a rubric in the question's instructions: the defect kinds the Director marks
    and the evidence fields that measure each;
  - four labelled examples (two clean, two not), drawn leave-one-mix-out: none
    comes from the mix being scored. Examples carry evidence only, not the full
    state, to stay inside Kev's validated 8,192-token context.

    python build_knowledge_requests.py [--evidence-root DIR]

Reads $OPENJEV_WORK/requests.jsonl and sense-si's phrases.json; writes
$OPENJEV_WORK/requests-knowledge.jsonl. The evidence files stay where they are
(they record a local path and are not ours to publish as-is).
"""

import argparse
import json
import os
import random
from pathlib import Path

WORK = Path(os.environ.get("OPENJEV_WORK", "E:/AI-Models/openjev/work"))
FIELDS = ("joins", "switches", "air_ms_max", "shift_diff_ms_max", "stretch_min", "stretch_max",
          "segment_boundary_s", "spectral_jump_max", "repeat_similarity_max", "click_z_max",
          "f0_step_cents_max", "octave_jumps", "pitch_step_cents_max", "pct_max")

RUBRIC = """Is this sung phrase clean, as the Director would mark it? A phrase is NOT clean if it has any of:
- audio replayed or skipped at a join (evidence: repeat_similarity_max high, joins and switches present);
- noise or a click at a segment start (evidence: click_z_max high, segment_boundary_s set, air_ms_max > 0);
- a pitch slip, octave jump or voicing flip (evidence: f0_step_cents_max large, octave_jumps > 0);
- a stutter or abrupt timbre change at a join (evidence: spectral_jump_max high, switches > 0).
pct_max is the largest percentile of any join measurement against 60 non-join control points (1.0 = beyond every control).
shift_diff_ms_max is non-zero only in cut-placement mixes and is not itself a defect.
Labelled examples from other mixes are given in state.examples."""


def mix_of(pid):
    return pid.rsplit("/", 1)[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--evidence-root", default="E:/AI/ajs-fullsong/tmp/vocal-clock/sing")
    ap.add_argument("--k", type=int, default=4)
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args()

    rows = [json.loads(l) for l in (WORK / "requests.jsonl").read_text(encoding="utf-8").splitlines()]
    ref = {f"{p['song']}/{p['mix']}/{p['index']}": p for p in
           json.loads((WORK / "sense-si-main/docs/calibration/phrases.json").read_text(encoding="utf-8"))["phrases"]}

    evidence = {}
    for f in sorted(Path(args.evidence_root).glob("*/*/phrase-evidence.json")):
        doc = json.loads(f.read_text(encoding="utf-8"))
        song, mix = f.parent.parent.name, f.parent.name
        for p in doc["phrases"]:
            pid = f"{song}/{mix}/{p['index']}"
            if pid in ref:
                r = ref[pid]
                assert abs(p["start"] - r["start"]) <= 0.002 and abs(p["end"] - r["end"]) <= 0.002, pid
            evidence[pid] = {k: p.get(k) for k in FIELDS}
    missing = [r["id"] for r in rows if r["id"] not in evidence]
    assert not missing, f"no evidence for {missing[:5]}"

    label = {r["id"]: r["label"] for r in rows}
    examples_for = {}
    for mix in sorted({mix_of(r["id"]) for r in rows}):
        rng = random.Random(f"{args.seed}:{mix}")
        pool = [pid for pid in label if mix_of(pid) != mix]
        clean = sorted(p for p in pool if label[p] == 1)
        dirty = sorted(p for p in pool if label[p] == 0)
        picks = rng.sample(clean, args.k // 2) + rng.sample(dirty, args.k - args.k // 2)
        rng.shuffle(picks)
        examples_for[mix] = [{"phrase_evidence": evidence[p], "director_mark": "clean" if label[p] else "not clean"}
                             for p in picks]

    out = WORK / "requests-knowledge.jsonl"
    with out.open("w", encoding="utf-8") as fh:
        for r in rows:
            body = json.loads(json.dumps(r["body"]))
            body["state"] = {**body["state"], "phrase_evidence": evidence[r["id"]],
                             "examples": examples_for[mix_of(r["id"])]}
            q = body["questions"]["phrase_clean"]
            q["instructions"] = RUBRIC
            fh.write(json.dumps({**r, "body": body}) + "\n")
    print(f"wrote {out} ({len(rows)} requests, {len(examples_for)} held-out mixes, k={args.k})")


if __name__ == "__main__":
    main()
