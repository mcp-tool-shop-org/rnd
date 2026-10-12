---
id: switchyard
title: switchyard — the device-aware model router (in build)
date: 2026-10-09
kind: instrument
relevance: act
fields: [studio-tooling, gpu-computing]
tags: [instrument, router, npu, openvino, offrig]
instrument_status: planned
invoke: "Not built yet. Planned: `switchyard route --task <t> [--min-<metric> x] [--max-latency-ms y] --json`; `switchyard run <spec>` for pre-registered experiments; `switchyard table`."
when: "Choosing which model, engine, device (NPU / iGPU / CPU / 5090 / rented GPU) and settings to use for a task, from measured receipts; or running a pre-registered device experiment that fills a gap in the routing table."
where: "github.com/mcp-tool-shop-org/switchyard (internal, going public as a prototype) · clone E:/AI/switchyard"
---

## Summary

A dispatcher: given a task and its constraints, it picks the model, engine, device and settings from a routing
table where **every row cites a receipt**, and explains the choice. OpenVINO's AUTO picks a device for a model you
already chose; nothing picks the model. That gap is the product.

Ordered by the Director on 2026-10-09 ("start building this out, so that we can start running experiments to get
the data we need"). **Grok** builds the core; **Kimi** owns the Intel lane (the OpenVINO adapter, experiments
E1–E3); R&D reviews every PR; the Publisher holds the devices and merges.

## Key points

- **Experiment-first.** A pre-registered harness produces routing rows. The first experiments:
  - E1: cold vs warm start, per device;
  - E2: Qwen3-Embedding-0.6B on the Intel devices;
  - E3: small OpenVINO LLMs on the NPU and iGPU;
  - E4: NPU/iGPU/5090 contention;
  - E5: "fill the card", the largest context per model that stays fully on the GPU.
- **It imports what exists:** the calibration chain, the math ladder, and the npu-probe and NLI-floor receipts.
- **The tie-in with offrig:** it reads calibrate runs and budget JSON (v1). It emits a versioned route
  decision, with offrig plan suggestions for remote routes. It **never** rents, sets caps or opens offrig's
  store, and a verify route needs a matching calibration receipt.
- **Guards:** a 5090 step needs a Publisher grant, an NPU step a ledgered session; the 15-minute rest; the
  device resolver refuses `GPU.1` (the 5090 in OpenVINO) and decides Intel by vendor id.
- **Design draft:** a self-repairing runner with an allowlist of measurement-neutral repairs, a fingerprint
  checked around and between repairs, and escalation for everything else. Reviewed by Kimi.
- **The bar:** 90% coverage before a 0.1.0 prototype release. Going public is the Director's call.
- **The run path (#31, reviewed 2026-10-10).** Until a778696, `switchyard run` only did dry runs, and E1's
  receipts came from an uncommitted driver calling `run_interleaved`. Neither review caught that.
  - **What #31 adds:** `run_spec` puts the guards in front of that same function: interpreter, spec, flags,
    the blob lock, a receipt-name check, card checks, the rest, card checks again, then `run_interleaved`.
  - **Remaining gap, which blocks E4 only:** the "empty card" check asks only Ollama (`/api/ps`), which
    can't see a torch, ComfyUI or offrig job on the 5090, and a malformed reply reads as empty.
  - **Fixes asked for:**
    - an `nvidia-smi` VRAM ceiling, failing closed (`--query-compute-apps` is useless under Windows WDDM);
    - polling at intervals of 60 s or less during the 15-minute rest, not just at its two ends.
  - E2 and E3 don't touch the 5090, so they can run on #31 as is.
- **OpenVINO IR weights (#32, reviewed 2026-10-10).** E2's first cold load failed with "Empty weights data in bin
  file". The hub fetch took `openvino_model.xml` without its sibling `.bin`; E1 never hit this, because its
  embedders came through the single-file ONNX path.
  - **The fix:** fetch the `.bin` at the same pinned revision, so both files sit in one snapshot directory.
  - **Timing is unaffected:** the download sits outside every timer.
  - **Same pattern later:** ONNX external-data files (`.onnx_data`) would need it too.
- **E2's first run aborted with zero rows (issue #33, ruled 2026-10-10).** The NPU rejected the compiled l512
  binary at execute (`ZE_RESULT_ERROR_INVALID_NATIVE_BINARY`). The compile had succeeded, l128 had passed, and
  the health check afterwards was clean. Only `device_lost` and `hang` were recorded outcomes, and the abort
  flush wrote finished arms only, so in an A-B-A schedule nothing was kept.
  - **New outcome, `native_binary_rejected`:** NPU only, that exact code, at execute after a successful
    compile, and only if that shape hasn't already run in the run. It's scoped to model × device × static
    shape.
  - **What it doesn't do:** skip anything beyond same-key arms, or mark the NPU off.
  - **Replication:** one occurrence is provisional. "Not supported" needs a recurrence in a run with a fresh
    compile cache; if it passes there instead, the shape is flaky and doesn't route.
  - **Any abort** now flushes completed slots as `aborted: true` rows, which never import into the routing
    table.
  - **Implemented:** #34 (harness) and #35 (the E2 amendment; spec blob 69f3e6db → `bd88da4b`), both reviewed
    2026-10-10 and passed. The rerun uses that blob on a commit containing both, under a new run id, after the
    first run's compile cache is cleared and a health check passes.
- **E2's rerun (`e2-2026-10-10b`, issue #36, ruled 2026-10-10):**
  - **The l512 NPU rejection replicated** in a second fresh-cache run (same blob size, driver 32.0.100.5540).
    **Confirmed on the receipts (#37):** code `0x7800000f` at execute, a 1,208,717,446 B blob, compile 31.0 s.
    "Not supported at NPU 1×512 for Qwen3-Embedding-0.6B-fp16-ov on driver 32.0.100.5540"; a driver change
    reopens it.
  - **A CPU arm (8×2048) passed its cold call, then exceeded the fixed 60 s per-call bound at warmup.** That's
    a slow shape, not a stuck device.
  - **The abort flush worked:** 13 aborted rows (CPU 5, iGPU 6, NPU 2) were kept out of the table. The CPU hang
    row must also stay out of the table, since #36 ruled it a slow shape, not a stuck device.
  - **Ruling:** the bound becomes per arm on every device, by amendment to E2 and E3. The cold call is bounded
    at 600 s; warm calls at max(60 s, 3 × the arm's own cold call), capped at 600 s.
  - **Next:** a full rerun (`-10c`) without the l512 arm, then the b8 tail. E3 waits for the bound change,
    since its 8B generate arms would hit 60 s too.
- **E2 reads GO (`e2-2026-10-10c`, #41).** At the decision length, the iGPU embeds in 348.8 ms against the
  CPU's 544.4 ms (ratio 0.64). Parity was valid on all 14 rows.
- **The batch-8 tail (2026-10-10):**
  - **`-10c`:** the NPU compiler refused l512-b8 at compile time (`[NPU_VCL] Compiler returned msg`,
    `0x78000007`, "Target buffer size '2048' does not match source buffer size '256'").
  - **New outcome, `compile_rejected` (#43):** NPU only, raised inside `compile_model`, and both markers
    required. It's scoped like `native_binary_rejected` and never retried. The l512-b8 row was re-recorded
    from the log (#44), holding only the rejection evidence and nothing measured.
  - **`-10d`:** l2048-b8's compile ran 70 min, wrote 0 bytes and grew to 35.3 GB. It was stopped by hand.
    CTRL+C could not interrupt the native compile, so the process was hard-killed and no receipt exists.
    There was no pre-registered compile bound, so this is recorded as an abort, **not** a capability result.
    l2048-b8 has had its one try.
  - **Design flaw found:** under interleaving, l128-b8's repeats waited on l2048-b8's cold, so two runs lost
    l128-b8. The next tail runs arms sequentially, l128-b8 alone.
- **Superseded 2026-10-11: the rest is out of switchyard (maintainer).** Rests were never meant to be a tool
  rule. They're the Publisher's scheduling call, between consecutive long runs only.
  - rest_s, plan_rest, the conditional rest and the forced 5090 rest are removed. Specs carry a dated
    superseding line.
  - Run markers remain only as the record of a killed run.
  - Kept: the heartbeat and empty-card guards, which prevent collisions.
  - Device state at run start is recorded, never gated on.
  - The two bullets below are history.
- **The rest became conditional (maintainer, 2026-10-10; #43, #46).**
  - The 15-minute rest is owed only after a run of over 30 minutes on the same devices that ended less than
    rest_s ago, and only for the remainder.
  - The harness takes the largest amount owed across every earlier receipt. A receipt with no times, or one
    that won't load, counts as long, timed from the file's save time.
  - The 5090 always rests in full: grants are messages, so nothing else enforces the card's rule.
  - #46 tops up a sleep that wakes a fraction of a second early.
- **Harness lessons from the night:**
  - A native compile can't be interrupted from Python, so a compile bound (15 min) and a memory stop
    (88%, sampled every 2 s) need a watcher that saves results and then ends the process.
  - A run-start marker file will make a killed run visible to the rest rule.
  - The NPU genai pipeline cache had to be keyed by compile config, since its KV cache is sized per prompt
    (#45). #42 fixed the genai call shape for NPU list prompts.
- **E3 is parked on memory (2026-10-10).**
  - `-b` stopped on the pipeline-cache bug. `-10c` piled up resident 8B pipelines in steps of 5–15 GB and was
    hard-killed at 89% RAM (95% in the rig monitor's 2-s samples). Neither produced a row.
  - The VRAM watchdog doesn't guard the switchyard environment, so the harness's own stop is the only guard.
  - **Amendment (R&D):** blocks per (model, device, compile config), at most one pipeline resident, a check
    that RAM is released between blocks, a pre-build memory guard, cheapest blocks first, and a descriptive
    drift block at the end. The viability floor and the other pre-registered settings are unchanged.
- **E3 reads VIABLE (`e3-2026-10-11b`, #51, 2026-10-11).** It ran in blocked order with peak RAM 43%, and all
  27 rows completed.
  - **Gate:** decode ≥ 15 tok/s at l1024 with thinking off, on at least one Intel device for at least one model.
    - Phi-3.5-mini int4 passes on the CPU (20.4), the iGPU (21.7) and the NPU (15.3, marginal).
    - Qwen3-8B int4 fails on all three: 12.0, 11.8 and 9.6.
  - **Expectation check, confirmed:** the NPU is slowest for both models at every length. At l4096, Phi on the
    NPU runs at 8.9 against 17.2 on the iGPU.
  - **Drift block:** 1.038, so devices measured an hour apart are comparable within about 4%.
  - **Both models are bandwidth-bound:** decode × weight size is about 58 GB/s for Qwen and 48 GB/s for Phi. A
    larger memory allocation can't speed up the 8B, so speculative decoding is the candidate if an off-5090 8B
    is wanted.
  - **Caveat:** on the CPU and iGPU, warm TTFT is likely a prefix-cached prefill. TTFT is reported as "first
    token, cache state as configured", and the prefix-cache setting is to be pinned in specs.
  - **A bug found on the way:** a fake that returned floats hid the real library's MeanStdPair metrics, and a
    bare `except` dropped every counter. The first blocked run was stopped and the harness fixed (#50). The
    lesson: test fakes must mirror the real return types, and nothing is dropped silently.
  - **The 5090 reference (e3-ref) measured nothing on its first run (2026-10-11, R&D's spec defect).** Its
    arms never referenced the 1024 prompt, and the Ollama adapter defaults a missing prompt to "", so all 14
    calls were empty and every rate was null.
    - The fix is switchyard #52: E3's prompts copied byte for byte, think true/false, num_ctx 4096.
    - The harness gets an empty-prompt refusal and a required-metric andon.
    - The re-run needs a new grant.
  - **The re-run reads (`e3-ref-2026-10-11b`, #54):** qwen3:8b on the 5090 at l1024 decodes at 207.8 tok/s
    with thinking off and 211.0 with thinking on, after 17 s of card time and no rest.
    - R_speed, the Intel side's Qwen3-8B as a share of the 5090: CPU 0.058, iGPU 0.057, NPU 0.046. The Intel
      side runs the 8B about 17–22× slower.
    - The 5090 stays the place for an 8B coach; the Intel side suits a Phi-class always-on generator.
- **The tail closed (`e2-b8tail-2026-10-11`):** NPU 8×128 warm p50 597.8 ms after a 52 s compile.
- **The Shared GPU/NPU Memory Override stays at 57% (36.1 GB)** for the series (maintainer, 2026-10-10). Every
  receipt records it in its environment capture.
- **The Phase-5 README (#57), R&D review 2026-10-11: pass with two wording changes.**
  - **Checked:**
    - every figure in "What the table says today", against routing.jsonl;
    - the route claim, by running it: Qwen3-8B at 15 tok/s with the 5090 busy is refused, and the refusal names E3;
    - the run flags and guards, and the SECURITY.md edits, against the code.
  - **Required:** the Qwen3-8B line is qualified to l1024 with thinking off, since the Intel side runs 4.5–12 tok/s
    across lengths.
  - **Required:** the pre-registration paragraph separates what the code enforces (a spec edited after its commit
    is refused, and its blob is recorded) from practice (no rule changes after results are seen).
- **E3's Phi slow start** (#59, run notes only; R&D review 2026-10-11: pass with two wording changes).
  - **What was seen:** the arm's first three CPU calls ran at about 7 tok/s, and the rest at about 21.
  - **The probes:** two exploratory probes outside the harness (scheduling settings, and cold storage with mmap on and
    off) never reproduced it.
  - **Required:** say the probes didn't reproduce it, so storage and scheduling alone don't explain it, rather than
    "ruled out". Don't give an untested cause for the 8-thread result.
  - **Suggested:** the episode was the arm's first three calls, which points to the arm's start more than to a rare
    transient.
- **The harness for E4, E5 and the Phi re-run** (Grok, Seat B; R&D review 2026-10-11).
  - **#60, the Ollama token count: pass with one change.** `prompt_eval_count` counts only the tokens the server
    evaluated, so prompt-cache reuse between resident calls could undercount a prefix search. The fix: count the final
    prefix again from a cold load, and refuse the arm on a mismatch (`cached_count_undercount`).
  - **#62, the fill-card executor: changes needed.**
    - **What's sound:** missing readings fail closed. A missing shared or prompt-rate reading is a spill, and a missing
      card reading is over margin.
    - **The abort unloads but doesn't cancel the request in flight.** Ollama keeps a busy model, so it must cancel,
      then unload, then re-read the card (`abort_without_cancel`).
    - **A sampler can't stop one large allocation.** The 30500 abort sits 700 MiB under the 31200 ceiling, and a
      doubling step can add gigabytes of KV in one allocation. So before each load, predict the peak from the earlier
      loads and skip any window predicted to cross `abort_mib` (`unguarded_allocation_step`).
  - **#63, hot cache, mmap, cold copy and steady warm-up: changes needed.**
    - **Continuous system sampling during each call is missing,** and that sampling is the point of the re-run
      (`requirement_dropped`).
    - **The pipeline cache key ignores where the model loads from,** so a hot arm and an archive arm can share one
      compiled pipeline (`cache_key_missing_dimension`).
    - **The tokenizer loads from the hub id,** so a hot arm can fall back to the E: archive or download
      (`silent_fallback`).
    - **What's right:** until_steady, robocopy /J with exit codes, and the storage fields on the receipt.
  - **#60 re-check at aa5c9ad: pass.** The final prefix is counted again from a cold load. A mismatch refuses the arm
    before measuring. Both counts are recorded, and the cold count is used.
  - **#63 re-check at 8ed048d: three of four pass.**
    - **Passing:** the cache key now includes the load source, the tokenizer loads from the local snapshot with hot arms
      offline, and gaps.md is updated.
    - **The sampler's disk rate is never recorded on Windows.** psutil's per-disk keys are `PhysicalDriveN`, not drive
      letters, and the test's fake keyed them by letter. The drive letter has to be mapped to its physical disk
      (`test_fake_hides_platform`, new class).
  - **#63 disk key at 3f9c836: pass, conditional on CI going green.** The drive letter maps to `PhysicalDrive<n>` through
    Get-Partition | Get-Disk (on the rig, E: is 2 and C: is 0). A failed map records `unrecorded` with its reason.
  - **#62 re-check at 8b82eda: changes needed.**
    - **Right:** close, unload with keep_alive 0, then re-read the card. `predicted_over` is never a pass. The cold
      re-count refuses on a mismatch. Not scaling one reading through the origin was the right call.
    - **The close does nothing during a load.** The flight is armed only after urllib has the response headers, and a
      non-streaming generate sends none until it's done. A local server holding its reply for 3 s showed `cancel()`
      returning at once and the request still completing. The tests used a fake transport
      (`test_fake_hides_platform`). Fix: arm an `http.client` connection before `getresponse()`, then shut down the socket.
    - **The second window has no bound.** With one measured window there's no line, so a doubling loads unguarded,
      and one allocation can pass the untested 31200 MiB ceiling between 200 ms samples
      (`unguarded_allocation_step`). Ruled: bound it with window 1's growing share, i.e. the reading minus the idle
      baseline minus the weights from `/api/tags`, scaled linearly. If there's no bound, don't load.
  - **#62 early read at 2235eb9 (before the rebase): three small changes needed.** Right: the connection is armed
    before `getresponse`, the socket is shut down, and the wait is sliced on a cancel flag (Windows leaves a blocked
    `recv` running). The window-2 bound is in, aborted windows are excluded, and the card settles for up to 10 s after
    an unload. Required:
    - the settle runs on the sampler thread, but `cover` joins it with a 5 s timeout, so the next load can start
      first (`abort_race`, new);
    - a share of 0 or less was floored to 0 (R&D's own formula), which predicts no growth. It now means no bound,
      with a residency check (`unsafe_floor`, new);
    - the unload's `arm()` clears the generate's cancel flag on the shared flight (`shared_cancel_state`, new).
  - **#62 re-check at 0af901e (rebased): pass, merge left to the Publisher.** The probe waits on an abort-done event
    with no timeout, tested threaded. A share of 0 or less, or a first window not fully resident, means no bound.
    Each request has its own cancel ticket. Optional: give the unload its own timeout.
  - **#65, num_predict 0 in the token count: pass once two guards are in.** E4's first live run sat at 575 W for about 12
    minutes and wrote no row. #60's count sent `num_predict` 0, which Ollama 0.35.1 reads as no limit. On the rig, 0
    gave no reply in 90 s, and 1 gave the count in 3.0 s. The fixes: count with 1, no zero-retry, and a fake that fails
    on 0. Required: `generate_body` refuses a missing, null or < 1 `num_predict`, fill rejects
    `confirm_num_predict` 0, and a stale docstring is fixed. Optional: a timeout on the count call.
    `test_fake_hides_platform`, second instance: the fake gave 0 a meaning the server doesn't. The remedy is recorded
    real exchanges per adapter parameter, replayed by the fakes.
    - **Re-check at 125842f: pass, merge left to the Publisher.** Both guards are in with tests, and the docstring is fixed. E4 and E5 are unblocked on R&D's side.
  - **#66, E4's NPU static shape: pass.** E4's re-run counted tokens fine, then stopped at the NPU arm, which needs a static
    BxL. The shape is "1x256" on both NPU arms. The runner fits bge-base's own 256-token prefix, so the shape matches
    it. `truncated_tokens` should be 0 or 1; more is a failed step. The partial rows were moved aside, and E4 re-runs whole.
  - **#70, the prefix search cost: pass.** E5 stalled for over 30 minutes on llama3.1:8b, because `fit_prompt_words` added
    one seed per count toward a target of about 118k tokens. Ollama itself prefilled 122k tokens in 19.6 s. The fix
    estimates the repeats from the seed's own count, tops up in proportion, and bisects only past the longest prefix
    known to be short. The output is unchanged, and 118k takes 25 counts or fewer. To watch: the trim now counts
    prefixes of a prompt the server just evaluated, so the cold re-count stays the guard.
    `test_fake_hides_platform`, third instance: the fakes never measured cost, so a count budget per fit is now part
    of their contract.
  - **#71, recorded-exchange fakes (the remedy for `test_fake_hides_platform`): two changes before recording.** The
    recorder captures one real exchange per adapter parameter. Fakes refuse what a recording doesn't answer, a test
    fails on any option without a fixture, and a count timeout is added. Required: bound the three deliberate
    no-limit calls with `num_ctx` 64 and `shift: false`, because a client timeout isn't shown to stop Ollama
    (`unbounded_probe`, new). The recorder also takes the harness's grant, heartbeat and empty-card guards. Optional:
    measure the cold-load constant on the rig, give the count budget a prompt-length term, and build every settings
    branch in the coverage test.
  - **#72, the Ollama supervisor: changes needed (not measurement-neutral yet).** Right: no restart during a measurement,
    slow-but-healthy is left alone, only the port owner is stopped, a failed restart stops the run, and there's no
    sign-in. The three departures:
    - no grant ledger: accepted, if the restart re-checks the grant, the heartbeat and `/api/ps` exclusivity itself;
    - `OLLAMA_CUDA_BACKEND`: rejected. It isn't an Ollama variable (the rig's `ollama serve --help` lists
      `OLLAMA_LLM_LIBRARY`), and the fingerprint read the driver's CUDA version, which a restart can't change
      (`check_reads_invariant`, new; `config_name_invented`, new);
    - retry defaulting to 0: accepted.

    Also required: replay the recorded start line and full environment, including `OLLAMA_MODELS` and the log
    (`environment_not_replayed`, new); compare flash attention and the KV type for real; never restart 11490; and
    re-warm, or mark cold, the step after a restart.
  - **E5 run 2, diagnosis (2026-10-12): no row valid, and the fixes are scoped as one job.**
    - **Every confirm spilled because no shared reading was found.** The 5090 Ollama runs elevated, so its
      processes' command lines are unreadable to the harness. `runner_pids` matches "runner" in the command line and
      finds none, and a missing shared reading is a spill. The null peaks were a reporting artifact: the row's peak
      comes from a confirmed window, and none confirmed.
    - **The fingerprint fields had the wrong sources.** `--query-gpu=cuda_version` isn't a valid field on driver 617.14,
      and flash attention, the KV type and the ggml sha were read from `/api/show`, which holds model info only.
    - **Fixes:**
      - find the runner by its parent pid (the 11434 listener);
      - read the server facts from its log (the server config and load_backend lines), plus the ggml-cuda.dll sha;
      - cap the search at the trained `context_length`;
      - search downward when the first window doesn't fit, using the lowest resident window as the spill reference;
      - record per-call readings in `search_calls`.
    - **Prerequisite:** restart 11434 once, logging and preferably unelevated.
  - **#74, E4's iGPU static shape: pass.** Run 5 (11434 restarted unelevated) ran every 5090 and NPU arm, then
    stopped in the iGPU plugin (`rank().is_static()`). The fix is 1x256 on both iGPU arms. The `nli` step encodes one prompt,
    fitted to 256 tokens on the model's own tokenizer, so the shape matches. These are latency rows, not NLI quality.
    Asked for: the adapter refuses an iGPU step without `static_shape` before compiling, unless the spec opts in to a
    dynamic shape.
  - **#75, NLI flat logits: pass, with a follow-up required.** E4 run 6 ran every 5090 and NPU arm, with NPU
    `truncated_tokens` 0. Then igpu-alone failed: a real cross-encoder returns `[batch, labels]`, `[0]` leaves a flat row,
    and `pool('none')` iterated floats. The fix takes a flat row. Follow-up: the fake returns the real shape per task,
    `none` refuses several rows, and the embed `[0]` is checked against pooled exports. `test_fake_hides_platform`,
    fourth instance.
  - **#72 re-check at 8d9b934: five of seven pass.** The gate re-check, the invented variable removed, retry, 11490 never
    stopped, and cold-after-restart all pass. Still open:
    - the backend line is the last one in an appended log, so after a restart it can be the old server's line
      (`check_reads_invariant`, second instance). Parse only the new segment;
    - the replayed start record is never compared in full with the live server's `OLLAMA_*` set. A stale record
      should mean no restarts.
  - **E4 run 7 readout (#76): valid run, all four pairs inconclusive.** The alone spreads were 0.356, 0.256, 0.234 and
    0.113, against the 0.05 half-band. Nothing was slower when paired, and the iGPU was 15% faster (most likely power
    management). The 4.1 s 5090 calls are reloads, probably from the option-less companion stop
    (`companion_reloads_model`, new). The per-slot clocks are null (`probe_field_null`, new). Ruled: no re-run as is,
    and an E4b pre-registered on these fixes. See [[2026-10-12-e4-co-scheduling-inconclusive]].
  - **#71 fixtures at cc3e57d: pass** (16 cases, Ollama 0.35.1, qwen3:8b, recorded under a grant, every load unloaded).
    The recordings corrected two assumptions:
    - a small `num_ctx` (64, 8) is raised to a floor, so it bounds nothing;
    - `truncate: false` with an over-long prompt replied at `num_ctx` 8, where the catalogue expected an error.

    `companion_stop` returned `done_reason: load`, which supports the E4 reload diagnosis. Follow-up: re-record
    the truncate case at a realistic window, set the catalogue from the recording, and fix `stop_session`.
  - **R&D rulings on Kimi K3's consult on the live runs (2026-10-12):**
    - **Spill:** the adapter-level `\GPU Adapter Memory(*)\Shared Usage` delta replaces per-PID attribution as the
      counter. The 5090's instance is matched by its Dedicated Usage against nvidia-smi, and ambiguous counts as
      missing. Rejected: the 2-of-3 rule, because it would loosen the pre-registered either-or rule after seeing data.
      The allocator leg is already a hard gate.
    - **E4b** (accepted, Kimi may draft, R&D reviews):
      - triplet log-ratios and a TOST decision (90% CI inside ±0.10), with "not free" on both sides;
      - slot refusal on a load or on more than 2 clock steps;
      - 10 repeats plus a pre-registered extension to 15.
    - **Live integration tier:** accepted, run on demand against the harness's own CPU Ollama, never 11490.
    - **Design rules:** accepted. Runs launch their own Ollama or read a declared sidecar, probes never mutate, and
      state is read at measurement time.
    - **The iGPU speed-up:** `cpu_freq_mhz` is a constant 3700 (psutil reports the nominal clock), so use
      `% Processor Performance` plus a decoupling arm.
    - **Clock settling:** longer decodes, an until-steady rule on `clocks.sm`, and the null probe fixed first.
  - **The E4b draft (#77, Kimi): changes needed before the numbers settle.** The design is right: triplets, TOST
    on both sides, slot refusals, its own Ollama on 11441, and probes that never mutate. Required:
    - the clock step is 7.5 MHz (read on the rig), not 15, and the tolerances come from a 5090-alone pilot;
    - the estimator becomes Hodges–Lehmann with the exact Wilcoxon 90% interval, because a bootstrap BCa of a median
      at n = 10 is unreliable;
    - a short decode is refused (`eval_count` below `num_predict`);
    - the companion starts before the warm-up;
    - the d_i are written within each triplet.

    Confirmed: the warm-up of 768 tokens and at least 3 s, the 1 s gap, and `load_refuse_s` 1.0.

## Studio relevance

The router is the product the NPU and verifier work points at: the right model on the right device, from
receipts, not guesses. The brief lives in R&D's memory (`switchyard-router-buildout-handoff.md`, with Kimi's
`kimi-switchyard-intel-lane-handoff.md`) and is snapshotted into the repo's `docs/handoff/`.

## Sources

- [primary] switchyard Phase 0 pull request, 2026-10-09 — https://github.com/mcp-tool-shop-org/switchyard/pull/1
