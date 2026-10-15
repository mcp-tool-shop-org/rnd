# Argon, embed-serve resource review: the disposition

**Argon's verdict (2026-10-15):** hold for seven exact changes before running on the shared rig. R&D applied all of them in offrig `6a7ae0b`, on the feat/embeddinggemma-2 branch. The server's test count went from 15 to 29, at 98% line coverage.

| # | Argon's change | Done |
|---|---|---|
| 1 | Cap every thread pool before torch loads, not just torch's intra-op pool | `thread_env()` sets `OMP_NUM_THREADS` and `MKL_NUM_THREADS` to N, with `OPENBLAS_NUM_THREADS=1`, `OMP_WAIT_POLICY=PASSIVE`, `TOKENIZERS_PARALLELISM=false` and `RAYON_NUM_THREADS=1`, before the import. It also calls `torch.set_num_interop_threads(1)` |
| 2 | A single-threaded server | `HTTPServer` with `request_queue_size = 8` |
| 3 | Default threads 6, and below-normal priority | `default_threads()` is a quarter of the logical cores, at most 6. `lower_process_priority()` runs first in `main()` |
| 4 | Memory bounds | `max_seq_length` is 2048. The body is capped at 4 MiB, 256 texts, 12,000 characters a text and 2,000,000 in all |
| 5 | HTTP hardening | Requests are refused for a non-numeric or out-of-range `Content-Length` (411 or 413), `Transfer-Encoding` (411), a non-JSON `Content-Type` (415), an `Origin` or `Sec-Fetch-Site` header, or a non-loopback `Host` (403). The socket timeout is 30 s, and `BrokenPipeError` and `ConnectionResetError` are ignored on reply |
| 6 | `torch.inference_mode()` around encoding | Through an injectable `no_grad`, so the CI tests still need no torch |
| 7 | A rerun gate | Below |

Two checks R&D made before applying the changes:
- **Requiring JSON can't break offrig.** offrig's client (ureq 3, `send_json`) sends `Content-Type: application/json` with a `Content-Length`. The earlier end-to-end rebuild worked through the server, which reads `Content-Length`.
- **The 2048 cap truncates no real input.** The model's own config sets no `max_seq_length`, and the benchmark's longest chunk was 1,528 tokens, so nothing real is cut and parity holds.

**Confirmed against the code:** a negative `Content-Length` passed the old `length > MAX_BODY_BYTES` check and read to end of stream.

**Argon's figures that are estimates, not measured:**
- 15–25 GiB at 8,192 tokens;
- 90–130 s for 202 chunks at 6 threads.

**The rerun gate, as Argon set it:**
- 6 threads at below-normal priority;
- a 16-chunk smoke test first, which checks the priority class, a thread count that doesn't grow across requests, process CPU at most 26% of the machine, and a peak working set of at most 3.6 GiB;
- then the 202-chunk rebuild, stopped if the process itself holds above 30% of machine CPU for 5 s.

**Not covered by Argon:** the affinity mask and the measured core map (P-cores are logical 0, 1, 10–13, 22 and 23). They were added to the brief after it had been sent.
- Argon reasoned that 6 threads at normal priority would stay on the P-cores.
- R&D's ruling is to launch on 6 E-cores (`0xFC`, logical 2–7) at below-normal priority. That's stricter than Argon's plan and keeps the P-cores free for the Director, so it needs no further round.
- Timings taken this way are E-core figures.
