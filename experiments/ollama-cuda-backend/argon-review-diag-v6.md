# Outside review: diagnosis harness v6 (CUDA 13.4 Update 2 backend, Ollama 0.40.4)

**For:** Argon. **From:** R&D. **Date:** 2026-10-15.
**What we ask:** a green light, or the fixes needed, before v6 is frozen and run on the GPU.

## What happened

You reviewed v4, and v5 applied your three fixes (FA-off resolution, the cap per arm, the nofa arms on all prompts).
The Publisher checked v5 against your text, it was frozen, and the run was granted. It stopped in 8.5 s, at the first
arm's start record, before any server or model started:

    record("arm_start", arm=name, tree=tree, fa=fa, kind=kind, ...)
    TypeError: record() got multiple values for argument 'kind'

`record(kind, **data)` takes the record type as its first parameter, so the arm's `kind=` keyword collides with it.
The line has been there since v4, and no review caught it. The v5 tests reached `run_arm` only up to the DLL check,
which exits before that line. So no test had run the path a GPU run takes.

The cleanup record showed no harm: peak 2,272 MiB on a 2,276 baseline, 11434 empty, 11500 not answering, no runner
left. The grant was closed.

## v6: the change (diff below)

1. **The fix:** the field is now `arm_kind=kind`. A grep of every `record(` call finds no other collision.
2. **Unclosed files:** three files are now closed with `with open(...)`, in `check_models`, `self_check` and the
   verdict's record loop. The behaviour doesn't change. The new dry run (below) turns warnings into errors, and these
   were the only ones it raised.

Everything else is v5 as you passed it: the arms, the prompts, the caps, the verdict and the evidence checks. The rnd
ab_dataminer (abmine.py, with the FA-off fix) is unchanged at sha256 f87f0daf…b0778.

## The dry run: main() end to end, offline

A new test class runs `main()` itself, unchanged, against a fake rig:
- **What's faked:** `nvidia-smi` and `typeperf` (through `subprocess.run`), PowerShell's kill and the runner query,
  both Ollama servers (`http`), and each arm's server process (`subprocess.Popen`).
- **What's real:**
  - the self-check, against a freeze file holding the real hashes of the files under test;
  - `check_models`, against a small store with the pinned layout;
  - every arm in ARMS order, with the sampler thread running and every record written and fsynced;
  - the verdict, the criterion-1 evidence from the server logs the fake writes, and `diag-analysis.json`.

**Three scenarios:**
1. **All arms run to the verdict.** S1 and S2 differ from stock only with FlashAttention on, a fattn-shaped shift.
   The run is checked for:
   - the record sequence: start, then 8 × (arm_start, warmup, 15 results, arm_unloaded, arm_stopped), cleanup and
     verdict, with no BREACH, CPU_STOP or error record;
   - per arm: the cap (14,336 on REF only), the arm kind and the model (q8_0 on REF only);
   - `OLLAMA_FLASH_ATTENTION=0` on exactly the two nofa arms, and 11500 plus `cuda_v13` on every arm;
   - 11434 found empty before every generation;
   - criterion 1 passing on every arm (FA `[disabled, disabled]` on nofa, `[auto, enabled]` otherwise);
   - the outcome: attribution `fattn` only, decision ELIGIBLE, the analysis file, a peak of 11,800 and a clean
     cleanup.
2. **An S-arm breach.** memory.used reads 9,300 while S1's model is loaded. The run stops with "passed the 9216 MiB
   cap". The record holds BREACH at cap 9,216, only S0 and S1 started, cleanup comes last, and the arm was killed.
3. **The CPU reference.** REF starts through `cmd.exe` with `/BELOWNORMAL /AFFINITY FC` and `CUDA_VISIBLE_DEVICES=-1`,
   using qwen3:8b with `num_gpu 0` and `num_thread 6` at cap 9,216. Criterion 1 is skipped for REF, and there's no
   CPU_STOP.

**Negative control:** the same dry run against v5 fails all three scenarios with the exact TypeError from the aborted
run. Against v6, all 18 tests pass under `python -W error` in about 1.2 s (15 from v5, plus these 3).

**What the fake can't show:**
- Ollama's real response shape. It is the same `generate` and record code that ran in the reviewed cu1343 sandbox
  test, which recorded real logprobs.
- The real server log. The fake writes lines copied from that run's log.
- Timing.
- The refusal branches: the server not coming up, the unload failing, 11434 not empty, and a CPU hold above 60%.
  Each raises SystemExit on a single line.

The dry run will be committed to rnd as a test, with the result, so this class of bug can't reach a grant again.

## For reading the result (written before the run; it changes nothing in v6)

qwen3:8b Q4_K_M keeps attn_v.weight in f16 in all 36 layers. Every other matrix is q4_K or q6_K. In llama.cpp
b11521 on compute 12.0, the routing is:
- quantized matmuls go to MMQ/MMVQ;
- the f16 V projection in prefill (27–30 tokens, over MMF's 16-column limit) goes to `cublasGemmEx`, f16 in and out,
  with `CUBLAS_COMPUTE_16F` and `CUBLAS_GEMM_DEFAULT_TENSOR_OP`;
- decode uses the native MMVF kernel.

So cuBLAS touches prefill only, with FA on as well as off. Prefill decides step 0, where the cu1343 build disagreed on
every prompt. That makes S0_cb1343 the key arm.

With FA off, prefill KQ and KQV are also f16 GEMMs on cuBLAS, so the nofa pair differs in cuBLAS on attention shapes as
well as in native kernels.

ggml never sets a cuBLAS pointer mode; alpha and beta are host statics. So the cuBLAS 13.x known issue about device
alpha/beta read before `cudaGridDependencySynchronize` under PDL doesn't apply.

## Questions

1. Is the v6 diff right and complete for the bug?
2. Does the dry run exercise what a GPU run executes? Is there a gap in the fake's fidelity that you'd close before
   the run?
3. Green light to freeze v6 (sha256 18a5f757…23c6c) with abmine.py f87f0daf…b0778, and run?

## The v5 → v6 diff

```diff
--- diag_test.py@v5
+++ diag_test.py@v6
@@ -1,4 +1,4 @@
-"""Diagnosis harness v5: why the CUDA 13.4 Update 2 backend's outputs differ from stock (Ollama 0.40.4, qwen3:8b).
+"""Diagnosis harness v6: why the CUDA 13.4 Update 2 backend's outputs differ from stock (Ollama 0.40.4, qwen3:8b).
 
 It generalises the reviewed sandbox test v3 to N arms. Every GPU arm runs as a sandbox on 11500 from its own tree
 under E:\\AI\\ollama-diag-0404\\<arm>\\run, one arm and one model at a time. The environment is identical across arms
@@ -268,7 +268,7 @@
     env = arm_env(run_dir, fa, kind)
     log_path = os.path.join(HERE, f"{name}-11500.log")
     state["arm_dir"] = run_dir
-    record("arm_start", arm=name, tree=tree, fa=fa, kind=kind, model=model, options=options, cap_mib=CAP_MIB,
+    record("arm_start", arm=name, tree=tree, fa=fa, arm_kind=kind, model=model, options=options, cap_mib=CAP_MIB,
            env={k: env.get(k) for k in ("CUDA_VISIBLE_DEVICES", "OLLAMA_LLM_LIBRARY", "OLLAMA_FLASH_ATTENTION", "OLLAMA_DEBUG", "USERPROFILE")})
     exe = os.path.join(run_dir, "ollama.exe")
     if cpu_ref:  # E-cores 2-7 at below-normal priority, inherited by the runner
@@ -395,7 +395,8 @@
     for tag in tags:
         man_path = os.path.join(MODELS, "manifests", "registry.ollama.ai", "library", "qwen3", tag)
         try:
-            man = json.load(open(man_path, encoding="utf-8"))
+            with open(man_path, encoding="utf-8") as f:
+                man = json.load(f)
         except OSError as e:
             raise SystemExit(f"REFUSED: qwen3:{tag} is not in the store ({e})")
         layers = {l["mediaType"].rsplit(".", 1)[-1]: l for l in man["layers"]}
@@ -413,7 +414,8 @@
 
 def self_check():
     try:
-        want = dict(line.split()[::-1][:2] for line in open(FROZEN, encoding="utf-8") if line.strip())
+        with open(FROZEN, encoding="utf-8") as f:
+            want = dict(line.split()[::-1][:2] for line in f if line.strip())
     except OSError:
         raise SystemExit(f"REFUSED: {FROZEN} does not exist; the script and abmine.py are frozen only after review")
     have = {"diag_test.py": sha_file(os.path.abspath(__file__)),
@@ -468,10 +470,11 @@
 
     recs = abmine.load_record_file(RECORD)
     task_ok = {}
-    for line in open(RECORD, encoding="utf-8"):
-        r = json.loads(line)
-        if r["kind"] == "result":
-            task_ok.setdefault(r["arm"], {})[r["prompt"]] = r["task_ok"]
+    with open(RECORD, encoding="utf-8") as f:
+        for line in f:
+            r = json.loads(line)
+            if r["kind"] == "result":
+                task_ok.setdefault(r["arm"], {})[r["prompt"]] = r["task_ok"]
     crit1 = {a[0]: evidence(a[0], a[1], a[2], a[3], a[5]) for a in ARMS}
     v = verdict(recs, task_ok)
     report = abmine.analyze(recs, reference="REF", arms=[a[0] for a in ARMS if a[0] in recs])
```

## The dry run (test_diag_test.py: FakeRig and DryRun)

The rest of the file holds the 15 v5 tests you saw. Imports: contextlib, hashlib, io, json, os, re, tempfile,
threading, time, types, unittest, urllib.error, unittest.mock; `import diag_test as dt` and
`from mcptoolshop_rnd import abmine`.

```python
REAL_SLEEP = time.sleep
DLLS = ("ggml-cuda.dll", "cublas64_13.dll", "cublasLt64_13.dll")


def text_for(prompt):
    """A response that passes the prompt's task check."""
    c = prompt["check"]
    if not c:
        return "Some plain text"
    if "contains_any" in c:
        return "Answer " + c["contains_any"][0]
    return json.dumps({k: ("coffee" if v is None else v) for k, v in c["json"].items()})


class FakeRig:
    """Stands in for nvidia-smi, typeperf, PowerShell, the two Ollama servers and the arm's server process.

    alt(up, model) says whether the running arm takes the alternative last token; breach_tree makes memory.used read
    9,300 MiB while that tree's model is loaded, and holds its first generation until the sampler has seen it."""

    def __init__(self, alt=lambda up, model: False, breach_tree=None):
        self.alt, self.breach_tree = alt, breach_tree
        self.up = None  # the running sandbox server: tree, fa, cpu
        self.models = []
        self.popens = []
        self.kills = 0
        self.stock_checks = 0
        self.generations = 0
        self.peak = 0

    def memory(self):
        up, models = self.up, self.models
        if up and models and up["tree"] == self.breach_tree:
            used = 9300
        elif up and not up["cpu"]:
            used = 2000 + sum(9800 if m.endswith("q8_0") else 5400 for m in models)
        else:
            used = 2000
        self.peak = max(self.peak, used)
        return used

    def run(self, cmd, **kw):
        if cmd[0] == "nvidia-smi":
            return types.SimpleNamespace(stdout=f"{self.memory()}\n", returncode=0)
        if cmd[0] == "typeperf":
            return types.SimpleNamespace(returncode=0, stdout='"(PDH-CSV 4.0)","\\\\rig\\Processor(_Total)\\% Processor Time"\n'
                                                              '"10/15/2026 15:10:21.000","12.5"\n')
        if cmd[0] == "powershell":
            if "taskkill" in cmd[-1]:
                self.kills += 1
                self.up, self.models = None, []
            return types.SimpleNamespace(stdout="", returncode=0)
        raise AssertionError(f"unexpected command {cmd}")

    def popen(self, args, env=None, cwd=None, stdout=None, stderr=None):
        if self.up is not None:
            raise AssertionError("a second server started while one runs")
        fa = "off" if env.get("OLLAMA_FLASH_ATTENTION") == "0" else "auto"
        cpu = env.get("CUDA_VISIBLE_DEVICES") == "-1"
        self.up = {"tree": os.path.basename(os.path.dirname(cwd)), "fa": fa, "cpu": cpu}
        self.popens.append({"args": args, "env": env, "cwd": cwd})
        lines = ["load_backend: loaded CPU backend from " + os.path.join(cwd, "lib", "ollama", "ggml-cpu-alderlake.dll")]
        if not cpu:
            lines = ['time=2026-10-15T15:10:30.000-04:00 level=INFO source=types.go:32 msg="inference compute" id=0 '
                     'library=CUDA compute=12.0 name=CUDA0 description="NVIDIA GeForce RTX 5090" libdirs=ollama,cuda_v13',
                     "  Device 0: NVIDIA GeForce RTX 5090, compute capability 12.0, VMM: yes, VRAM: 32579 MiB",
                     *lines,
                     "load_backend: loaded CUDA backend from " + os.path.join(cwd, "lib", "ollama", "cuda_v13", "ggml-cuda.dll")]
        if fa == "off":
            lines.append("llama_context: flash_attn            = disabled")
        else:
            lines += ["llama_context: flash_attn            = auto",
                      f"resolve_fused_ops: Flash Attention {'disabled' if cpu else 'enabled'}"]
        text = "\n".join(lines) + "\n"
        if stdout is not None:
            stdout.write(text)
        else:  # the CPU reference arm: cmd.exe redirects the server's output into the log
            with open(re.search(r'> "([^"]+)"', args[-1]).group(1), "w", encoding="utf-8") as f:
                f.write(text)
        return types.SimpleNamespace(pid=4242)

    def http(self, base, path, body=None, timeout=600):
        if base == dt.STOCK:
            if path == "/api/ps":
                self.stock_checks += 1
                return {"models": []}
            return {"done": True}
        up = self.up
        if up is None:
            raise urllib.error.URLError("connection refused")
        if path == "/api/ps":
            return {"models": [{"name": m} for m in self.models]}
        if body.get("keep_alive") == 0:
            self.models = []
            return {"done": True}
        self.models = [body["model"]]
        self.generations += 1
        if up["tree"] == self.breach_tree:
            for _ in range(400):
                if dt.state["breach"]:
                    break
                REAL_SLEEP(0.005)
        i = next((i for i, p in enumerate(dt.PROMPTS) if p["prompt"] == body["prompt"]), None)
        base_text = "Hello" if i is None else text_for(dt.PROMPTS[i])
        chunks = [base_text[j:j + 4] for j in range(0, len(base_text), 4)]
        last = ["!", "."] if self.alt(up, body["model"]) else [".", "!"]
        lps = [{"token": c, "logprob": -0.05, "top_logprobs": [{"token": c, "logprob": -0.05}, {"token": "~", "logprob": -4.0}]}
               for c in chunks]
        lps.append({"token": last[0], "logprob": -0.1,
                    "top_logprobs": [{"token": last[0], "logprob": -0.1}, {"token": last[1], "logprob": -2.5}]})
        return {"response": base_text + last[0], "logprobs": lps, "eval_count": len(lps), "eval_duration": 1000,
                "prompt_eval_count": 27, "done_reason": "stop", "load_duration": 1}


class DryRun(unittest.TestCase):
    """main() end to end, offline: every arm in ARMS order, the verdict and the analysis file."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.here = tmp.name
        fake = {}  # each tree's fake DLLs; ARMS keep their names, trees, FA settings, prompt sets and kinds
        for tree in sorted({a[1] for a in dt.ARMS}):
            cuda = os.path.join(self.here, tree, "run", "lib", "ollama", "cuda_v13")
            os.makedirs(cuda)
            for f in DLLS:
                with open(os.path.join(cuda, f), "wb") as fh:
                    fh.write(f"{tree}/{f}".encode())
            fake[tree] = tuple(dt.sha_file(os.path.join(cuda, f)) for f in DLLS)
        arms = [(n, t, fake[t], fa, w, k) for n, t, _, fa, w, k in dt.ARMS]
        store, pins = os.path.join(self.here, "models"), {}  # the pinned store layout, at small sizes
        man_dir = os.path.join(store, "manifests", "registry.ollama.ai", "library", "qwen3")
        os.makedirs(man_dir)
        os.makedirs(os.path.join(store, "blobs"))
        for tag in dt.MODEL_PINS:
            blob = f"qwen3:{tag} weights".encode()
            digest = "sha256:" + hashlib.sha256(blob).hexdigest()
            with open(os.path.join(store, "blobs", digest.replace(":", "-")), "wb") as f:
                f.write(blob)
            with open(os.path.join(man_dir, tag), "w", encoding="utf-8") as f:
                json.dump({"layers": [{"mediaType": "application/vnd.ollama.image.model", "digest": digest, "size": len(blob)},
                                      {"mediaType": "application/vnd.ollama.image.template", "digest": dt.TEMPLATE_DIGEST,
                                       "size": 1}]}, f)
            pins[tag] = (digest, len(blob))
        abmine_path = os.path.abspath(abmine.__file__)
        frozen = os.path.join(self.here, "diag_test.FROZEN.sha256")  # the real self-check, against these very files
        with open(frozen, "w", encoding="utf-8") as f:
            f.write(f"{dt.sha_file(os.path.abspath(dt.__file__))}  diag_test.py\n{dt.sha_file(abmine_path)}  abmine.py\n")
        self.sampler_done = threading.Event()
        real_sampler = dt.sampler

        def sampler():
            try:
                real_sampler()
            finally:
                self.sampler_done.set()

        patches = {"HERE": self.here, "RECORD": os.path.join(self.here, "diag-record.jsonl"), "FROZEN": frozen,
                   "MODELS": store, "MODEL_PINS": pins, "RND": os.path.dirname(os.path.dirname(abmine_path)),
                   "ARMS": arms, "sampler": sampler,
                   "time": types.SimpleNamespace(sleep=lambda s: REAL_SLEEP(0.001), time=time.time, strftime=time.strftime)}
        for name, value in patches.items():
            p = mock.patch.object(dt, name, value)
            p.start()
            self.addCleanup(p.stop)
        self.addCleanup(dt.state.update, dict(dt.state))
        self.addCleanup(setattr, dt, "CAP_MIB", dt.CAP_MIB)
        dt.state.update(peak=0, breach=None, stop=False, arm_dir=None, cpu_watch=False, cpu_over=0, cpu_stop=None)

    def main(self, rig, reference="q8_0"):
        with mock.patch.object(dt, "http", rig.http), mock.patch.object(dt, "REFERENCE", reference), \
                mock.patch.object(dt, "subprocess", types.SimpleNamespace(run=rig.run, Popen=rig.popen)), \
                contextlib.redirect_stdout(io.StringIO()) as out:
            try:
                dt.main()
            finally:
                self.assertTrue(self.sampler_done.wait(5), "the sampler thread did not stop")
                REAL_SLEEP(0.05)  # a breach's kill and unload threads finish against the fakes
        return out.getvalue()

    def records(self):
        with open(dt.RECORD, encoding="utf-8") as f:
            return [json.loads(line) for line in f]

    def test_every_arm_runs_to_the_verdict(self):
        rig = FakeRig(alt=lambda up, model: up["tree"] in ("S1", "S2") and up["fa"] == "auto")  # a fattn-shaped shift
        printed = json.loads(self.main(rig))
        recs = self.records()
        names, n = [a[0] for a in dt.ARMS], len(dt.ARMS)
        kinds = [r["kind"] for r in recs]
        self.assertEqual((kinds[0], kinds[-2], kinds[-1]), ("start", "cleanup", "verdict"))
        for kind, count in (("arm_start", n), ("warmup", n), ("result", n * len(dt.PROMPTS)), ("arm_unloaded", n),
                            ("arm_stopped", n)):
            self.assertEqual(kinds.count(kind), count, kind)
        self.assertFalse([k for k in kinds if k in ("BREACH", "CPU_STOP") or k.endswith("_error")])
        starts = [r for r in recs if r["kind"] == "arm_start"]
        self.assertEqual([r["arm"] for r in starts], names)
        self.assertEqual([r["arm_kind"] for r in starts], [a[5] for a in dt.ARMS])
        self.assertEqual([r["cap_mib"] for r in starts], [14336 if a[5] == "reference" else 9216 for a in dt.ARMS])
        self.assertEqual([r["model"] for r in starts], ["qwen3:8b-q8_0" if a[5] == "reference" else "qwen3:8b" for a in dt.ARMS])
        self.assertTrue(all(r["empty"] for r in recs if r["kind"] == "arm_unloaded"))
        self.assertFalse(any(r["sandbox_answering"] for r in recs if r["kind"] == "arm_stopped"))
        self.assertEqual([p["env"].get("OLLAMA_FLASH_ATTENTION") for p in rig.popens],
                         ["0" if a[3] == "off" else None for a in dt.ARMS])
        for p in rig.popens:
            self.assertEqual((p["env"]["OLLAMA_HOST"], p["env"]["OLLAMA_LLM_LIBRARY"], p["env"]["CUDA_VISIBLE_DEVICES"]),
                             ("127.0.0.1:11500", "cuda_v13", "0"))
        self.assertGreaterEqual(rig.stock_checks, rig.generations)  # 11434 checked empty before every generation
        v = recs[-1]
        self.assertTrue(all(c["ok"] and c["dll_ok"] for c in v["criterion_1"].values()), v["criterion_1"])
        self.assertEqual(v["criterion_1"]["S0_nofa"]["flash_attn"], ["disabled", "disabled"])
        self.assertEqual(v["criterion_1"]["S0"]["flash_attn"], ["auto", "enabled"])
        self.assertTrue(v["S0_equals_S0p"] and v["a_S2_equals_S1"] and v["b_shift_present"] and v["b"] and v["c"])
        self.assertEqual([a.split(":")[0] for a in v["b_attribution"]], ["fattn"])
        self.assertTrue(v["decision"].startswith("S2 ELIGIBLE"))
        self.assertEqual(printed["decision"], v["decision"])
        with open(os.path.join(self.here, "diag-analysis.json"), encoding="utf-8") as f:
            analysis = json.load(f)
        self.assertEqual(analysis["arms"], names)
        self.assertEqual(set(analysis["mae_vs_reference"]), set(names) - {"REF"})
        cleanup = recs[-2]
        self.assertEqual((cleanup["peak_mib"], cleanup["stock_ps"], cleanup["sandbox_answering"]), (11800, [], False))
        self.assertIsNone(rig.up)

    def test_an_s_arm_breach_stops_the_run_and_cleans_up(self):
        rig = FakeRig(breach_tree="S1")
        with self.assertRaises(SystemExit) as cm:
            self.main(rig)
        self.assertIn("passed the 9216 MiB cap", str(cm.exception))
        recs = self.records()
        breach = [r for r in recs if r["kind"] == "BREACH"]
        self.assertEqual((breach[0]["memory_used_mib"], breach[0]["cap_mib"]), (9300, 9216))
        self.assertEqual([r["arm"] for r in recs if r["kind"] == "arm_start"], ["S0", "S1"])
        self.assertEqual(recs[-1]["kind"], "cleanup")
        self.assertGreaterEqual(rig.kills, 2)  # the breach's kill, and run_arm's own
        self.assertIsNone(rig.up)

    def test_the_cpu_reference_arm(self):
        rig = FakeRig()
        printed = json.loads(self.main(rig, reference="cpu"))
        recs = self.records()
        i = [a[0] for a in dt.ARMS].index("REF")
        ref = rig.popens[i]
        self.assertEqual(ref["args"][:2], ["cmd.exe", "/c"])
        self.assertIn("/BELOWNORMAL /AFFINITY FC", ref["args"][2])
        self.assertEqual(ref["env"]["CUDA_VISIBLE_DEVICES"], "-1")
        start = [r for r in recs if r["kind"] == "arm_start"][i]
        self.assertEqual((start["model"], start["cap_mib"], start["options"]["num_gpu"], start["options"]["num_thread"]),
                         ("qwen3:8b", 9216, 0, 6))
        self.assertIn("skipped", printed["criterion_1"]["REF"])
        self.assertFalse(any(r["kind"] == "CPU_STOP" for r in recs))
        self.assertFalse(printed["b_shift_present"])
        self.assertTrue(printed["decision"].startswith("S2 ELIGIBLE"))

```

## Hashes (sha256)

- diag_test.py v6: 18a5f75780ed6c4d8fd9682ccddfa343626728b315c1ecf66643a0f251823c6c
- diag_test.py v5 (aborted): c787f0e92cc8b43a39212ef3c36024efdfd3cfd35abcacf3a83c7d07e27efb7f
- abmine.py (unchanged since v5): f87f0daf0736fe2131e87820b1a3696ee7e1457ce8697352157763443f7b0778
- test_diag_test.py: 9d2d7fa2602a76da5de95ea65d04624d0702f7bfa4e5cce52e891233039c73dc
