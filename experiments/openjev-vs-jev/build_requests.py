"""Build the 124 phrase requests exactly as sense-si's calibration sent them to hosted Jev.

Runs CPU-only with sense-si's own code (an archived copy of its main branch), so the
state and question bytes match the hosted-Jev run in docs/calibration/phrases.json.

    <sense-si venv python> build_requests.py

Writes $OPENJEV_WORK/requests.jsonl: one line per phrase with the request body,
the Director's clean/not-clean label and hosted Jev's raw P(clean).
"""

import json
import os
import sys
from pathlib import Path

WORK = Path(os.environ.get("OPENJEV_WORK", "E:/AI-Models/openjev/work"))
SENSE = WORK / "sense-si-main"
for pkg in ("ears", "decisions", "eyes"):
    src = SENSE / "packages" / pkg / "src"
    if src.is_dir():
        sys.path.insert(0, str(src))
sys.path.insert(0, str(SENSE / "tools"))

import phrase_calibration as pc  # noqa: E402
from decisions.client import NoulQuestion  # noqa: E402


def main():
    hosted = json.loads((SENSE / "docs" / "calibration" / "phrases.json").read_text(encoding="utf-8"))
    by_key = {(p["song"], p["mix"], p["index"]): p for p in hosted["phrases"]}
    items = pc.load_items()
    out = WORK / "requests.jsonl"
    with out.open("w", encoding="utf-8") as fh:
        for item in items:
            jev = by_key[(item["song"], item["mix"], item["index"])]
            label = int(item["label"])
            if int(jev["clean"]) != label:
                raise SystemExit(f"label mismatch for {item['id']}: rebuilt {label}, hosted run {jev['clean']}")
            question = NoulQuestion(instructions=pc.INSTRUCTIONS, true=pc.TRUE_CRITERION, false=pc.FALSE_CRITERION)
            body = {"model": "openjev", "state": item["record"].to_state(),
                    "questions": {"phrase_clean": question.to_wire()}}
            fh.write(json.dumps({"id": item["id"], "label": label, "jev_p_yes": jev["p_yes"],
                                 "held_out": jev["held_out"], "bytes": item["bytes"], "body": body},
                                ensure_ascii=False) + "\n")
    print(f"wrote {len(items)} requests to {out.as_posix()}")


if __name__ == "__main__":
    main()
