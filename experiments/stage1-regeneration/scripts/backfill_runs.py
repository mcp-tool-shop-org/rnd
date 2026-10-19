"""Backfill stage1-regeneration's runs from the Publisher's window records (scale plan P2, 2026-10-19).

Usage: python experiments/stage1-regeneration/scripts/backfill_runs.py <the Publisher's receipts folder> [--dry-run]

- **Which records:** exactly the outcome.json files in RECORDS, never a draft. Membership was confirmed by the
  Publisher, who owns them, on 2026-10-19:
  - every Colab window and rung of the stage 1 study, windows 1 to 14f;
  - the four RunPod plans of critic-signal's §10 step 1.

  Windows 1–3 are stage 1 runs made before the 300-unit budget began. experiment.json's budget excludes them, by
  id, with the reason.
- **How each run is written:** through `rnd runs record`'s own code path (runs.from_outcome and runs.record), so
  every run is validated exactly as a live one would be.
- **What older records lack:** a file with a `run` object (written by `publisher outcome write`) is read as written.
  An older file without one is mapped field by field, and gets:
  - venue colab and cost_unit colab_units (every older file is a Colab window);
  - the date from the window folder's YYYYMMDD suffix, when the file has none;
  - its `commit` pinned as role-set's, as the Publisher confirmed for every one of those files.
- **Never overwrites.** A run already recorded is left alone, and the script says so.
"""

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from mcptoolshop_rnd import layout, runs  # noqa: E402

EXPERIMENT = "stage1-regeneration"
_OLD_WINDOWS = [
    "window1-20261016", "window2-20261017", "window3-20261017",
    "window4-20261017", "window5-20261017", "window6-20261017", "window6b-20261017", "window6c-20261017",
    "window7-20261017", "window7b-20261017", "window8-20261017", "window9-20261017",
    "window10-20261017", "window10b-20261017", "window10c-20261017", "window10d-20261017",
    "window11a-20261017", "window11b-20261017", "window11c-20261017", "window11d-20261017",
    "window12a-20261017", "window12b-20261017", "window12c-20261017", "window12d-20261017", "window12e-20261017",
    "window12f-20261017", "window12g-20261017", "window12h-20261017",
    "window12s5a-20261018", "window12s5b-20261018", "window12s6a-20261018", "window12s6b-20261018",
    "cpu-measure-20261018",
    "window13b-20261018", "window13c-survival-20261018", "window13d-cpusmoke-20261018",
    "window13e-prebuild-muse-20261018", "window13f-prebuild-qwen3.8-20261018", "window13g-prebuild-gemma-20261018",
    "window13i-prebuild-qwen3.8-a100-20261018", "window13j-prebuild-qwen3.8-a100-20261018",
    "window13k-prebuild-granite-a100-20261018", "window13l-20261018", "window13m-rung-wa-20261018",
    "window13o-probe-bolt-20261018", "window13p-rung-deadline-20261018", "window13q-dead-kernel-20261018",
    "window13r-dead-kernel-stall600-20261018", "window13s-rung-rescore-20261018", "window13t-rescore-20261018",
    "window13u-probe-xet-20261019", "window13v-rung-critic-eval-a-20261019", "window13v-rung-critic-eval-b-20261019",
    "window13v-rung-critic-eval-c-20261019", "window13w-critic-eval-muse-s0-20261019",
    "window13x-critic-eval-muse-s1-20261019", "window13y-critic-eval-lightning-s0-20261019",
    "window13z-rung-c-confirm-write-20261019", "window14a-c-confirm-write-20261019",
    "window14b-critic-eval-confirm-muse-s0-20261019",
]
RECORDS = (
    [f"colab/{w}/outcome.json" for w in _OLD_WINDOWS]
    + ["colab/window13w-critic-eval-muse-s0-20261019/try1/outcome.json"]
    # 14c-14f: each try its own run, written with a `run` object (publisher outcome write).
    + ["colab/rung-via-bf16-20261019/try1-gate/outcome.json", "colab/rung-via-bf16-20261019/out/outcome.json",
       "colab/rung-gate-floor-20261019/try1-ram/outcome.json", "colab/rung-gate-floor-20261019/out/outcome.json",
       "colab/rung-prestep-muse-20261019/try1-gate/outcome.json",
       "colab/rung-prestep-muse-20261019/try2-content-path/outcome.json",
       "colab/rung-prestep-muse-20261019/try3-stopped/outcome.json",
       "colab/rung-prestep-muse-20261019/try4/outcome.json", "colab/rung-prestep-muse-20261019/try5/outcome.json"]
    # critic-signal §10 step 1 on RunPod.
    + ["offrig-supervl-convert-20261019/plan1/outcome.json", "offrig-supervl-convert-20261019/plan2/outcome.json",
       "offrig-supervl-critic-h200-20261019/plan3/outcome.json",
       "offrig-supervl-critic-h200-20261019/plan4/outcome.json"]
)
DATE_SUFFIX = re.compile(r"-(\d{4})(\d{2})(\d{2})/")


def run_from(path: Path, rel: str) -> dict:
    outcome = json.loads(path.read_text(encoding="utf-8"))
    if "run" in outcome:
        return runs.from_outcome(outcome)
    commit = outcome.pop("commit", None)
    m = DATE_SUFFIX.search(rel)
    date = None if outcome.get("date") else f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    return runs.from_outcome(outcome, venue="colab", cost_unit="colab_units", date=date,
                             pins={"role-set": commit} if commit else None)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("receipts", help="the Publisher's receipts folder")
    ap.add_argument("--dry-run", action="store_true", help="map and validate every run, write nothing")
    ap.add_argument("--link-raw", metavar="RND_DATA",
                    help="re-record every run with raw_manifest_id, the id of its run in this rnd-data checkout "
                         "(scale plan P3); a run whose manifest isn't there fails")
    args = ap.parse_args(argv)
    receipts = Path(args.receipts)
    written, kept, failed = 0, 0, []
    rec_path = ROOT / "experiments" / EXPERIMENT / "experiment.json"
    candidate = json.loads(rec_path.read_text(encoding="utf-8")) if args.dry_run else None
    for rel in RECORDS:
        path = receipts / rel
        if not path.is_file():
            failed.append(f"{rel}: missing")
            continue
        try:
            run = run_from(path, rel)
            if args.link_raw:
                # The run's folder is the one holding its outcome.json; its rnd-data id is that path under receipts.
                raw_id = "receipts--" + rel.rsplit("/", 1)[0].replace("/", "--")
                if not (Path(args.link_raw) / "runs" / raw_id / "manifest.json").is_file():
                    failed.append(f"{rel}: no rnd-data run {raw_id}")
                    continue
                run["raw_manifest_id"] = raw_id
            if args.dry_run:
                candidate["runs"].append(run)
                print(f"would record {run['id']}: {run['outcome']}, {run['cost']} {run['cost_unit']}")
                continue
            runs.record(ROOT, EXPERIMENT, run, replace=bool(args.link_raw))
            written += 1
        except runs.RecordError as exc:
            if exc.code == "RUN_EXISTS":
                kept += 1
            else:
                failed.append(f"{rel}: {exc.code}: {exc}")
    if args.dry_run:
        failed += [f"record would be invalid: {m}" for m in
                   layout.validate_data(ROOT, EXPERIMENT, candidate, layout.registry_ids(ROOT))]
    print(f"recorded {written}, already there {kept}, failed {len(failed)}")
    for line in failed:
        print(f"  {line}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
