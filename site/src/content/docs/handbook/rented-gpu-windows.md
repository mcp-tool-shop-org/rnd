---
title: Rented GPU windows (Claude + Colab)
description: The golden path for running model work on Colab from Claude Code, with the templates we use. Built over two nights of the Stage 1 writer pilot.
sidebar:
  order: 8
---

A **window** is one rented Colab session that does one job: convert a model, run a wave of writing, critique a batch.
Claude Code drives it from the rig through Google's `google-colab-cli`, and nobody watches a notebook. This page is
the path we settled on after the Stage 1 writer pilot spent about half of its first 71 units on windows that gave
nothing back ([issue 11](../../newsletter/issue-11/)). Every rule below exists because a window failed without it.
The raw data behind it, one row per window, is in [`experiments/colab-golden-path/data`](https://github.com/mcp-tool-shop-org/rnd/tree/main/experiments/colab-golden-path/data).
For the short version written for any Colab plan, see [Colab golden path, for any plan](../colab-golden-path/).

The working code is in role-set (`scripts/colab/`): `smoke_window.sh` runs a window from the rig, `pin_window.py` is
the job on the VM, `vm_gate.py` is the health gate, and `tests/fake_colab/colab` is a fake CLI for tests.

## 0. Licences first

Check every model the window will download, convert or host against
[`licences/registry.json`](https://github.com/mcp-tool-shop-org/rnd/blob/main/licences/registry.json) for that use,
as in the [model comparisons](../model-comparisons/) template. Hosting a converted model, even privately, is a use.

## 1. Two lanes: CPU for preparation, GPU for serving

Measured on our account (`colab usage`, 2026-10-16 to 2026-10-18):

| Runtime | Units/hour | Use it for |
|---|---|---|
| CPU, default (2 cores, 12 GB RAM, 220 GB disk) | 0.08 | stub runs, measurements, survival tests |
| CPU, `--high-mem` (8 cores, 52 GB RAM) | 0.26 | converting models to GGUF, hashing |
| A100 40 GB | 5.30 | serving models: writing and critique waves |

- **Never do CPU work on the A100.** Download and conversion took 15–21 minutes per model on night one, about 40% of
  the projected time for our five-model window. Convert once on CPU, host the file privately, and let the A100 download a finished file. The one exception is a pin that only reproduces on the A100's image (section 5).
- **One card type per study.** Seconds and units per result are part of what you measure, so don't mix cards
  inside one study. Choose the card before the study starts.

## 2. The budget rules

- **A ledger, by the balance.** Every window gets a row: start balance, end balance, spent. When two windows overlap,
  count each by its own rate × runtime and reconcile with the balance afterwards.
- **Projections from measured rates only.** Each rate cites the receipt it came from. Night one's critique step was
  projected from a one-shot test at 20 s an item; real waves took 29 minutes per 8 drafts.
- **Cap = projection + 15%** for steps measured on real hardware, **+30%** for any kind of wave with fewer than
  four measured slots. The window script stops the session at the cap.
- **Show savings and overruns separately.** Our W-A came in 19% under its projection, but only because faster model
  downloads saved 4,461 s while the twin waves ran 2,997 s over. One net figure would have hidden the overrun.
- **Open only if the cap + 2 units is left** in the study's budget. A top-up on the account doesn't raise the
  study's budget unless the person who set it says so.
- **Measure the unknown first, on the smallest window.** When one cost is a guess (our twin waves had never run on
  a GPU), run the cheaper window first and re-project the rest from what it measured.

## 3. The window, from the rig

`smoke_window.sh` runs these steps, in this order:

1. **Refusals before any VM:** a stub run on a GPU, a GPU window with no disk floor, a token that doesn't match its
   role, and an input file whose sha256 isn't its pin.
2. **The open lock,** so two windows never read the account rate at the same moment.
3. **`colab new`, then the health gate** (`vm_gate.py`, one short exec). It checks the card name, memory, that the
   card isn't already in use, disk ≥ the window's peak + 20 GB, RAM, and a 200 MB read from Hugging Face. A VM that
   fails, or whose first exec dies, is stopped and a fresh one requested, up to 3 tries. One row per try goes into
   `gate.jsonl`. The gate only catches VMs that are bad at the start; drops later in the run are the resume path's
   job (step 5).
   - **Set each floor on the metric the gate measures.** A 200 MB read never gets past ramp-up: one VM read 96 MB/s
     on the gate and then downloaded at 259 MB/s. Our first A100 floor (129, half the sustained median) would have
     rejected good VMs. We now use 60 on the short read, on CPU and GPU alike, and log every read so the floor can be
     recalibrated against real downloads.
   - **It does reject bad VMs.** Its first catch was a CPU VM reading 45 MB/s; the next VM passed.
4. **Uploads,** each checked by sha256. Then the token, if the job needs one (section 6).
5. **The job,** started with `colab exec`. Every `PIN_*` setting goes over as `--env`. Never rely on the exec's
   output stream: in our windows it stopped reaching the rig while the job ran on. The rig follows the job's own
   `job.log` instead, with a stall limit (10 minutes before the first line, then 20).
6. **The cap watcher.** It counts this window's spend as its own rate × runtime, not the account balance, which
   would include a neighbour's spend.
   - **The job gets a deadline:** the moment its window's spend will reach the cap less a margin. Past it, nothing
     new starts; a wave under way is stopped (SIGTERM, then SIGKILL), and the job writes its result files. The call
     journal keeps every finished call, so a cut wave loses only the call in flight, and a resume replays the rest.
   - **Measured:** the cut took under a second on a stub run, and a real exit fetch took 56 s. So the job gets 60 s
     past the deadline and the fetch 120 s, which is 0.265 units at the A100's 5.3 an hour, inside a 0.3 margin. The
     script refuses to open a window whose grace and fetch allowance don't fit its margin.
   - Before the deadline existed, a cap stop returned only `job.log` and what `checkpoints.py extract` could rebuild.
7. **Every way out fetches what the job has written first** (always `job.log`; the result files when the job got
   that far), then stops the session in an `EXIT` trap and checks the session
   list is empty. Read the balance after.

## 4. The job, on the VM

- **It writes its own log** (`job.log`) and a heartbeat line every few minutes.
- **It saves as it goes.** Every finished model call and every finished wave is written to `job.log` as a checkpoint
  line, so a killed window's work can be extracted from the log (`checkpoints.py extract`).
- **It can resume.** A window can start from another window's sealed drafts (`resume.tar`). Every file carries a
  sha256 seal, and a file that doesn't match its seal is refused.
- **A job that is killed outright leaves no log line, and Colab won't tell you.** We killed a test job's kernel on
  purpose: `colab status` kept reading BUSY for 22 minutes and the exec never returned, because the status follows the
  command-line tool's exec, not the kernel. Only the stall limit (20 minutes without a new log line) ended the window.
  A rule we had built on the status passed against our fake CLI and could never fire on real Colab, so we removed it.
  Shortening the stall, with a heartbeat on every long step, is next.
- **One job per VM.** The job takes a lock and carries a token for its window, so a late duplicate exec waits, then
  stops if the first job finished.
- **It writes `pin-result.json`** with everything it pinned and measured, and `ok` true or false.
- **It never pip-installs into its own interpreter.** One of our jobs installed the converter's requirements into
  the Python it was running in, partway through. That swapped `huggingface_hub` on disk under modules already
  loaded, and the upload at the end failed on an import error, after a 15-minute conversion had matched its pin.
  Install into a separate venv, or run the later step in a fresh interpreter.

## 5. Models

- **Pin everything:** the model's Hugging Face revision, the GGUF's sha256, the llama-server binary's sha256, the
  sampling settings. A model that doesn't reproduce its pin is never served.
- **Pre-build once, byte for byte.** A prebuild window converts one model and uploads it to a private repo only if
  the file's sha256 equals the pin from the earlier conversion. That proves it is the same file. Never re-pin to make
  a file fit. On the high-mem CPU runtime one 30B model took about 15 minutes and 0.07 units: download 230 s, convert
  354 s, hash 101 s, upload 138 s.
- **The converter's environment is part of the pin.** The same conversion, at the same model revision, llama.cpp
  commit and library versions, gave different bytes on a CPU VM. The one material difference in the recorded
  `pip freeze` was the torch build: `2.11.0+cu130`, preinstalled in the GPU image's system Python, against
  `2.11.0+cpu` on the CPU image. llama.cpp's conversion requirements point pip at PyTorch's CPU index, so a fresh
  venv always gets `+cpu`, and the two models we had converted in their own venv matched on both hosts. The host
  CPU's instruction set is a second possible cause, not yet ruled out.
  - **For new pins:** convert in a venv with the exact torch wheel pinned by URL or hash, never the image's system
    Python. Record the CPU model and `torch.backends.cpu.get_cpu_capability()` with the pin.
  - **For pins made with a system Python:** pre-build them on the same card and image that made them. Ours did.
  - **Record `pip freeze` with every conversion.** Comparing the freezes is how we found the cause in minutes.
  - **Record the image too.** Colab's runtime image (`COLAB_RELEASE_TAG`) can change between days. All our windows
    ran on one image; a new one can change the system Python's packages and so the bytes of a system-Python
    conversion.
- **Download everything before the first wave,** after checking that the whole set plus 20 GB fits the free disk.
  One file at a time ran at about 179 MB/s on the A100; parallel snapshot downloads reached about 305.
  `HF_HUB_ENABLE_HF_TRANSFER` does nothing in current `huggingface_hub`; the Xet backend's high-performance setting is
  what we'll try next, clearing its chunk cache after each file so it can't eat the disk margin. Not yet tested.
- **Pin the hub version per process.** Colab's kernel carried `huggingface_hub` 1.33.0, while llama.cpp's conversion
  requirements installed 0.36.2 for the converter. Record both.

## 6. Tokens

- **One fine-grained token per role,** scoped to the one repo it needs: read for GPU windows, write for the CPU
  window that uploads. Check the scopes after making them (`whoami`); the form's account-wide section is easy to
  leave ticked.
- **Never on a command line, never in `--env`, never in a log.** The rig writes the token to a mode-600 file,
  uploads it to the VM's RAM-backed `/dev/shm`, and deletes its own copy at once and again in the exit trap.
- **Read once.** The job reads the file at its very start, deletes it, drops the Hub's environment variables and
  passes the value only as a `token=` argument.
- **Turn off the implicit token.** With no token given, `huggingface_hub` looks in the environment, its own cache
  and, inside Colab, the account's secrets vault. In a command-line session the vault lookup timed out after about
  10 s (google-colab-cli [issue #48](https://github.com/googlecolab/google-colab-cli/issues/48)); with a notebook
  attached it could succeed and use whatever token the account stores. Set `HF_HUB_DISABLE_IMPLICIT_TOKEN=1` before
  anything imports the hub, and pass `token=False` on every public call. On our probe the 11 s wait went to 0 and the
  vault was never asked.
- **Prove the token is gone.** After the downloads, the job checks five places: the token file, its own variable, the
  Hub's environment variables, the Hub's token cache, and the vault secret the hub caches. Any one still set stops the
  window before the models start.
- **Test the leak paths.** A test pushes a fake token in a real token's shape through the real window script and
  checks that it appears in no file the window keeps or returns. Check the CLI's own history once with a real run.
  The push scan refuses anything in the `hf_` token shape.

## 7. The test ladder

No paid window runs on new code until it has climbed the ladder:

1. **Unit tests.**
2. **The fake CLI:** the real `smoke_window.sh`, against a fake `colab` that records what it was asked to do.
3. **A CPU stub run, at about 0 units:** the real job on a real Colab CPU VM, with mock models in place of the real
   ones. Run it from the same inputs the paid window will use. Ours caught a refused rewrite that two review rounds
   had missed, which would otherwise have failed on paid units.
4. **The paid window.**

A stub can only test the paths its mock models take. Our first paid window after the ladder found one more defect:
an arm whose slots all failed was still sent to a critique, because no mock model ever failed every slot. Give the
mocks the failure modes you expect from real models. A checklist for the stand-ins:

- every slot of an arm dropped;
- a reply cut off at the token limit;
- a refusal;
- a window stopped mid-wave and resumed from its checkpoints.

**A fake encodes what you believe about the real system.** Check its behaviour against one real run before trusting
a rule that only the fake has passed.

## 8. The review loop

- **Three seats:** a Claude session builds, a second Claude session reviews the diff (not the summary), and an
  outside model from another family reviews from a brief.
- **Loop until it passes.** A reviewer who asked for fixes sees the fixed version before anything paid uses it.
- **The outside review gets a bundle with its own checksum.** The file starts with `SHA256:` and `LINES:` lines, the
  reviewer checks them before reading, and the reply cites file:line.

## 9. Templates

### Launch file (one per window, kept in its receipts folder)

```bash
#!/usr/bin/env bash
# Window <id>: <one line on what it does>. Cap <n> units. From the rig in WSL.
set -uo pipefail
D=<receipts folder for this window>
cd "$D" || exit 2
check() { [ "$(sha256sum "$1" | cut -d' ' -f1)" = "$2" ] || { echo "REFUSED: $1 is not $2" >&2; exit 2; }; }
check <input file> <full sha256>
export PIN_GPU=A100 PIN_SESSION=<id> PIN_CAP_UNITS=<projection x 1.15> PIN_WALL_S=<above the cap in seconds>
export PIN_ROLE=<role> PIN_ROLESET_COMMIT=<full sha>
export PIN_GGUF_REPO=<org/repo> PIN_GGUF_REVISION=<full sha> PIN_HF_TOKEN_FROM=<read token variable>
export PIN_GATE_MIN_DISK_GB=<peak + 20>
export PIN_UPLOADS="$D/<input file>"
bash "$D/smoke_window.sh" <server binary> "$D" 2>&1 | tee "$D/rig.log"
```

### Projection worksheet

| Part | Count | Measured rate | Receipt | Seconds |
|---|---|---|---|---|
| setup or download, per model | | | | |
| each wave: slots × seconds per slot | | | | |
| critique: drafts × seconds per draft | | | | |
| sent back for rewrite (measured share) | | | | |
| model swaps, rig side, gate | | | | |
| **total** → hours × units/hour = projection; cap = projection × 1.15; open only if cap + 2 ≤ budget left | | | | |

### Ledger row

```markdown
| <window> | <what, card, cap> | <start balance> | <end balance> | <spent> (<basis: balance or rate x runtime>) | <running total> |
```

### Receipts folder (one per window)

`launch.sh`, `rig.log`, `job.log`, `pin-result.json`, `gate.jsonl`, the returned tar, and a one-line
`outcome.json` written when the window closes:

```json
{"window": "<id>", "date": "YYYY-MM-DD", "commit": "<sha>", "card": "A100", "cap": 8.8, "spent": 7.95, "basis": "rate_x_runtime", "outcome": "results | partial | lost-vm | cap-stop | tooling-fault | not-assigned | test", "why": "<one line>"}
```

Hash the tar into the README; keep drafts and logs out of public repos. Our own receipts lacked `outcome.json`, and
classifying 44 windows afterwards from prose notes took keyword rules and guesses.

### Outside-review brief

```markdown
# <REVIEWER> BRIEF | <subject> | from <seat> | <date>
Reply's first line: `# <REVIEWER> REPLY | <subject> | to <seat> | <date>`

**The ask.** For each item, say closed or open, with file:line on the + side of `git diff <base>..<head>`.
List anything the change breaks. End with PASS or FAIL. This review repeats until it passes.

| Item | What changed | Evidence (bundle section) |
|---|---|---|

**Files:** `<bundle>.txt`, header `SHA256: <hash>`, `LINES: <n>`. Check both before reading.
Answer in chat, under about 450 words. Mark anything the diff doesn't show as an assumption.
```
