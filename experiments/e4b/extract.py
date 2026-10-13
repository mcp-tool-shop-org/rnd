"""Trim interlock's E4b receipts down to the numbers the public charts read.

The interlock receipts carry argv, environment and paths. rnd is public, so the
charts read this directory's results/ and nothing else. Re-run when a new
receipt lands:

  python experiments/e4b/extract.py --interlock <checkout> --pilot <e4b-pilot.json>
  python experiments/e4b/extract.py --interlock <checkout> --pilot <e4b-pilot.json> \\
      --receipt receipts/e4b-block-4.jsonl=block-4.json

The checkout is only read, via git show, so it does not need to be on main.
The commit recorded on each file is the harness commit inside the receipt, and
the sha256 is of the source bytes that were trimmed.
"""

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_NAME = "mcp-tool-shop-org/interlock"
SPEC_PATH = "experiments/e4b/spec.yaml"
# Harness commits named for the receipts this experiment already published.
# A new receipt is not in this map; its own header commit is what gets written.
KNOWN_HARNESS = {
    "receipts/e4b-block-2.jsonl": "f3f5e44",
    "receipts/e4b-block-3.jsonl": "426f106",
    "e4b-pilot.json": "0ea9506",
}
DEFAULT_RECEIPTS = (
    "receipts/e4b-block-2.jsonl=block-2.json",
    "receipts/e4b-block-3.jsonl=block-3.json",
)
TOKEN = re.compile(r"[A-Za-z0-9_.-]+")


def git_bytes(checkout: Path, rev: str, path: str) -> bytes:
    got = subprocess.run(["git", "-C", str(checkout), "show", f"{rev}:{path}"], capture_output=True)
    if got.returncode != 0:
        detail = got.stderr.decode("utf-8", "replace").strip()
        raise SystemExit(f"could not read {rev}:{path} from {checkout}: {detail}")
    return got.stdout


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def token(value, what: str) -> str:
    if not isinstance(value, str) or TOKEN.fullmatch(value) is None:
        raise SystemExit(f"{what} is not a plain token")
    return value


def number(value, what: str):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise SystemExit(f"{what} is not a number")
    return value


def optional_number(value, what: str):
    if value is None:
        return None
    return number(value, what)


def parse_rule(spec: bytes, commit: str) -> dict:
    text = spec.decode("utf-8")

    def grab(pattern: str, label: str) -> str:
        found = re.search(pattern, text, re.M)
        if found is None:
            raise SystemExit(f"{SPEC_PATH} at {commit[:7]} has no {label}")
        return found.group(1)

    return {
        "band_log": float(grab(r"^band:\s*([0-9.]+)\s*$", "band")),
        "method": token(grab(r"^  method:\s*(\S+)\s*$", "method"), "interval method"),
        "nominal_confidence": float(grab(r"^  ci:\s*([0-9.]+)\s*$", "nominal confidence")),
        "spec": SPEC_PATH,
        "spec_commit": commit,
        "spec_sha256": sha256(spec),
    }


def events_of(slots: list) -> list:
    events = []
    counted = 0
    for index, slot in enumerate(slots):
        count = slot.get("refusal_events") or 0
        if isinstance(count, bool) or not isinstance(count, int):
            raise SystemExit("a slot refusal_events count is not an integer")
        counted += count
        reasons = slot.get("attempt_reasons") or []
        if not isinstance(reasons, list):
            raise SystemExit("attempt_reasons is not a list")
        reasons = [token(r, "refusal reason") for r in reasons]
        refusal = slot.get("refusal")
        if refusal is not None:
            refusal = token(refusal, "refusal")
        if count or reasons or refusal is not None:
            events.append({
                "index": index,
                "role": token(slot.get("role"), "slot role"),
                "repeat": slot.get("repeat"),
                "refusal": refusal,
                "refusal_events": count,
                "attempt_reasons": reasons,
            })
    return events, counted


def trim_pair(row: dict) -> dict:
    slots = row.get("slots")
    if not isinstance(slots, list):
        raise SystemExit(f"{row.get('pair')} has no slot list")
    events, counted = events_of(slots)
    pair_count = row.get("refusal_events")
    if not isinstance(pair_count, int) or isinstance(pair_count, bool):
        raise SystemExit(f"{row.get('pair')} refusal_events is not an integer count")
    if counted != pair_count:
        raise SystemExit(f"{row.get('pair')}: slot refusals sum to {counted}, pair says {pair_count}")
    kept_slots = []
    for slot in slots:
        kept_slots.append({
            "role": token(slot.get("role"), "slot role"),
            "value": optional_number(slot.get("value"), "slot value"),
        })
    effects = row.get("d_i")
    if not isinstance(effects, list):
        raise SystemExit(f"{row.get('pair')} has no d_i list")
    return {
        "pair": token(row.get("pair"), "pair"),
        "verdict": token(row.get("verdict"), "verdict"),
        "hodges_lehmann": optional_number(row.get("hodges_lehmann"), "Hodges-Lehmann"),
        "low": optional_number(row.get("low"), "interval low"),
        "high": optional_number(row.get("high"), "interval high"),
        "achieved": optional_number(row.get("achieved"), "achieved level"),
        "d_i": [number(x, "d_i") for x in effects],
        "refusal_events": pair_count,
        "events": events,
        "slots": kept_slots,
    }


def trim_receipt(raw: bytes, source: str, checkout: Path) -> dict:
    rows = [json.loads(line) for line in raw.decode("utf-8").splitlines() if line.strip()]
    header = next((row for row in rows if row.get("kind") == "e4b-header"), None)
    if header is None:
        raise SystemExit(f"{source} has no e4b header")
    commit = token(header.get("git_sha"), "harness commit")
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise SystemExit(f"{source} harness commit is not 40 hex digits")
    expected = KNOWN_HARNESS.get(source)
    if expected and not commit.startswith(expected):
        raise SystemExit(f"{source} harness commit does not start with {expected}")
    pairs = [trim_pair(row) for row in rows if row.get("kind") == "e4b-pair"]
    if not pairs:
        raise SystemExit(f"{source} has no pairs")
    return {
        "provenance": {
            "repo": REPO_NAME,
            "commit": commit,
            "source": source,
            "sha256": sha256(raw),
        },
        "run_id": token(header.get("run_id"), "run id"),
        "aborted": bool(header.get("aborted")),
        "rule": parse_rule(git_bytes(checkout, commit, SPEC_PATH), commit),
        "pairs": pairs,
    }


def collect_receipt(raw: bytes, ctx) -> dict:
    """`rnd collect e4b` entry point (collect.json): the same trim, reading the spec through the clone."""
    return trim_receipt(raw, ctx.source, ctx.clone)


def linear_percentile(values: list, fraction: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def trim_pilot(raw: bytes, source_name: str) -> dict:
    doc = json.loads(raw.decode("utf-8"))
    commit = token(doc.get("git_sha"), "pilot harness commit")
    expected = KNOWN_HARNESS.get(source_name)
    if expected and not commit.startswith(expected):
        raise SystemExit(f"pilot harness commit does not start with {expected}")
    ranges = doc.get("ranges_mhz")
    if not isinstance(ranges, list) or not ranges:
        raise SystemExit("pilot has no clock ranges")
    ranges = [number(x, "clock range") for x in ranges]
    p95 = number(doc.get("p95_clock_range_mhz"), "p95")
    if abs(p95 - linear_percentile(ranges, 0.95)) > 1e-9:
        raise SystemExit("pilot p95 does not match the linear 95th percentile of ranges_mhz")
    return {
        "provenance": {
            "repo": REPO_NAME,
            "commit": commit,
            "source": source_name,
            "sha256": sha256(raw),
        },
        "ranges_mhz": ranges,
        "p95_clock_range_mhz": p95,
        "clock_tolerance_mhz": number(doc.get("clock_tolerance_mhz"), "clock tolerance"),
    }


def assert_public(text: str, name: str) -> None:
    """Refuse a trim that still carries a machine path or an environment dump."""
    problems = []
    if "\\" in text or re.search(r"[A-Za-z]:/", text):
        problems.append("a path")
    folded = text.lower()
    for needle in ("users", "ollama", "appdata", "localappdata", "argv", "environment", "server_config"):
        if needle in folded:
            problems.append(needle)
    if "@" in text:
        problems.append("an at-sign")
    if problems:
        raise SystemExit(f"{name} is not safe to publish: {', '.join(problems)}")


def dump(doc: dict) -> str:
    return json.dumps(doc, indent=2) + "\n"


def percent(value) -> str:
    if value is None:
        return "     "
    return f"{100 * value:+.2f}"


def report(doc: dict) -> None:
    print(f"{doc['run_id']}  harness {doc['provenance']['commit'][:7]}  "
          f"band {doc['rule']['band_log']}  {doc['rule']['method']}  "
          f"nominal {doc['rule']['nominal_confidence']}")
    for pair in doc["pairs"]:
        print(f"  {pair['pair']:10} {pair['verdict']:12} "
              f"HL {percent(pair['hodges_lehmann'])}  "
              f"[{percent(pair['low'])}, {percent(pair['high'])}]  "
              f"achieved {pair['achieved']}  d_i {len(pair['d_i'])}  "
              f"refusals {pair['refusal_events']}  slots {len(pair['slots'])}")
        if pair["d_i"]:
            effects = [100 * x for x in pair["d_i"]]
            print(f"    d_i percent  min {min(effects):+.2f}  max {max(effects):+.2f}")
        if pair["events"]:
            print(f"    events {json.dumps(pair['events'])}")


def split_receipt(spec: str) -> tuple[str, str]:
    if "=" not in spec:
        raise SystemExit(f"--receipt needs source=output, not {spec}")
    source, output = spec.split("=", 1)
    if "/" not in source or not output.endswith(".json"):
        raise SystemExit(f"--receipt looks wrong: {spec}")
    return source, output


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Trim E4b receipts for the public charts.")
    parser.add_argument("--interlock", required=True, type=Path, help="interlock checkout, read with git show")
    parser.add_argument("--pilot", required=True, type=Path, help="pilot document (not in the interlock tree)")
    parser.add_argument("--rev", default="origin/main", help="git rev of the receipt blobs")
    parser.add_argument("--receipt", action="append", default=None,
                        help="source=output.json, repeatable; default is block 2 and block 3")
    args = parser.parse_args(argv)
    out_dir = HERE / "results"
    out_dir.mkdir(parents=True, exist_ok=True)
    receipts = args.receipt or list(DEFAULT_RECEIPTS)
    for spec in receipts:
        source, output = split_receipt(spec)
        doc = trim_receipt(git_bytes(args.interlock, args.rev, source), source, args.interlock)
        text = dump(doc)
        assert_public(text, output)
        (out_dir / output).write_text(text, encoding="utf-8", newline="\n")
        report(doc)
        print(f"  wrote results/{output}")
    pilot_raw = args.pilot.read_bytes()
    pilot = trim_pilot(pilot_raw, args.pilot.name)
    text = dump(pilot)
    assert_public(text, "pilot.json")
    (out_dir / "pilot.json").write_text(text, encoding="utf-8", newline="\n")
    ranges = pilot["ranges_mhz"]
    print(f"pilot  harness {pilot['provenance']['commit'][:7]}  "
          f"ranges {len(ranges)}  p95 {pilot['p95_clock_range_mhz']}  "
          f"tolerance {pilot['clock_tolerance_mhz']}  "
          f"min {min(ranges)}  max {max(ranges)}")
    print("  wrote results/pilot.json")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
