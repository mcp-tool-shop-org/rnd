# Stage 1 run records: relay-s1-20261014b (and the refused relay-s1-20261014)

The raw records of interlock-relay stage 1 on the 5090, 2026-10-14, moved here from the interlock worktree before it was pruned. They are the inputs the frozen analysis (`../../analyze.py`, rnd `cbaed82`) read; its output is `../relay-s1-20261014b.analysis.json`.

- `relay-s1-20261014b-{decode,long,unload,stop,companion}.jsonl`: the five receipts, as interlock wrote them. Held for the Director's review and never imported into interlock's routing table (the working-tree rows that reached it were reverted; see the result note).
- `relay-s1-20261014b-*.atof.jsonl`: the Relay traces, one per step. `*.calls.json`: the tracer's call tables. `*.http.json`: the driver's count of requests below the hook. `relay-s1-20261014b-import.json`: the process import check.
- `relay-s1-20261014b.driver.json`: the driver's run record (preflight facts, steps, VRAM peaks, the final unload).
- `relay-s1-20261014.driver.json` and `relay-s1-20261014-decode.http.json`: the first attempt, refused after 8 s by interlock's in-repo-interpreter guard, with nothing loaded.

**Redaction:** each driver record's `needles` field held the H3 search strings (the rig's home path, host name and user name). It is removed from these public copies and replaced by `needles_redacted`. Everything else is as written. To re-run the frozen analysis on these files, place them under an interlock checkout's `receipts/` and `logs/` and restore a `needles` dict; the H3 check needs it.
