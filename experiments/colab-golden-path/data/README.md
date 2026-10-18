# Colab receipts: raw data

This folder is the raw-data layer for the Colab golden-path article. It is built from the
Publisher's Colab receipts. Everything here can be rebuilt; nothing is edited by hand.

## Files

- `windows.csv`: one row per Colab window folder, plus the CPU measurement folder and the
  token-scope-check folder. Columns: `window, date, card, role, purpose, cap_units, spent_units,
  spent_basis, exec_wall_s, ok, outcome_class, outcome_source, outcome_why, rate_units_per_hr, ledger_text`.
  - `spent_units`, `purpose`, `cap_units` and `ledger_text` come from the rows of `units-ledger.md`.
    A blank means the ledger has no row (or an open row) for that window.
  - `spent_basis` is `balance` (start and end balance read), `rate_x_runtime` (rate times runtime)
    or `estimate` (the ledger gave an approximate figure). Windows 2 and 3 come from one ledger
    sentence and have no basis.
  - `ok`, `role` and `card` come from `pin-result.json` and the launch script when present.
  - `exec_wall_s` is the last `wall=` figure in the window's `rig.log`; if there is none, the
    time between `started` and `ended` in `pin-result.json`.
  - `outcome_class` comes, in order of precedence, from the window's own `outcome.json` (written by
    the Publisher when the window closed), from R&D's overrides in the script (`OUTCOME_OVERRIDES`,
    for windows whose cause the ledger text doesn't name), or from keyword rules on the ledger text.
    `outcome_source` says which, and `outcome_why` gives the one-line reason. Blank when none applies. Classes: `results`, `partial`, `lost-vm`, `cap-stop`, `tooling-fault`, `not-assigned`, `test`.
- `windows/<folder>/`: the small text records of each window: `pin-result.json`, `gate.jsonl`,
  launch scripts (`launch*.sh`, `run*.sh`), `outcome.json`, `smoke-report.txt`, `result*.json` and `*.md` notes,
  each at most 200 KB. `windows/_top/` holds one top-level note, `highmem-rate-probe.txt`.
- `MANIFEST.tsv`: every file under the source folder, copied or not: path, bytes, sha256, whether
  it was copied, and why not.
- `units-ledger.md`: the units ledger, scrubbed.

## Rebuild

```
python scripts/colab/collect_windows.py --src <receipts dir> --out experiments/colab-golden-path/data
```

The script is Python 3 and uses only the standard library. It never writes to the source folder.
It prints each row's outcome class with the keyword that set it, then totals.

## What is not copied

Tars, `.gguf` files, binaries (including `llama-server` and anything under `upload/` or `build/`),
all `*.log` files (`job.log`, `rig.log`, `exec-*.log`), draft `*.jsonl` files, and everything in
`token-scope-check/`. These are in `MANIFEST.tsv` by sha256 and size only. Some `job.log` files carry
encoded checkpoint lines that hold model drafts, which is why logs stay out.

## Scrubbing

Every text file is scrubbed before it is written:

- the private GGUF repo name becomes `<private-gguf-repo>`, and the Hugging Face account name
  becomes `<hf-account>`;
- absolute paths (`/mnt/x/...`, `/home/<name>/...`, `X:\...`) keep only the part after
  `receipts/colab/`, or become `<path>`; the local user name becomes `<user>`;
- email addresses become `<email>`;
- Colab session ids and VM host names (`m-s-...`) become `<session>`.

The script exits with an error, naming the file, if any output still contains a token-shaped
string (`hf_` followed by 30 or more characters, or `ya29.`). It does not print the match.
Environment variable names such as `HF_TOKEN_GGUF_WRITE` are kept; values are never present.
