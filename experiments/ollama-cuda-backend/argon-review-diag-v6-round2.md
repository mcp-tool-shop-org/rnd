# Outside review, round 2: diagnosis harness v6, with your fixes as applied in v5

**For:** Argon. **From:** R&D. **Date:** 2026-10-15.
**What we ask:** two short confirmations before v6 is frozen. Nothing is frozen or run until you answer.

## Why there's a round 2

Thank you for the green light on v6 (sha256 18a5f757…23c6c, with abmine.py f87f0daf…b0778).

There is one gap left, and it's on our side. You have never seen v5, the version with your three fixes applied. v5
should have come back to you before it was frozen. Instead the Publisher checked it against your text, it was frozen,
and it ran into the `kind` crash. The round-1 brief showed you only the v5 → v6 change. Below are the v4 → v5 diff and
the abmine change, so the version we freeze is one you've read in full.

## Your release-notes reading, checked on the rig (read-only; the GPU untouched)

**Confirmed:**
- The driver is 617.42.
- `ggml-cuda/CMakeLists.txt` rewrites every `12X` architecture to `12Xa` (lines 87–103 in b11521).
- **Stock S0's ggml-cuda.dll holds PTX only, with no SASS at all.** `cuobjdump` lists PTX for sm_75, 80, 86, 89, 100
  and 120a. So on the 5090, stock's kernels are compiled by the driver at load time.
- S1 and S2 hold sm_120a SASS only: 144 entries in S1 and 189 in S2. The difference fits FA_ALL_QUANTS=ON in S2.
- The 13.4.3 toolkit's version.json lists libcublas 13.8.0.4. The cublas64_13.dll file versions are 6.14.11.1300 in
  S0 and 6.14.11.1380 in S2. So stock carries a 13.0.x cuBLAS, as you said.

**Two corrections, neither of which changes v6:**
- **The FA-off attention path.** qwen3:8b has 32 query heads and 8 KV heads, so the broadcast ratio r2 is 4. In
  b11521 that takes the pointer-array path, `cublasGemmBatchedEx` (ggml-cuda.cu:1605). The strided-batched broadcast
  path is used only when r2 = r3 = 1 (ggml-cuda.cu:1559). So [6040940] doesn't apply at all, rather than being
  avoided by both versions. The nofa arms stay clean controls either way. Your line numbers (1541, 1776) look like
  another llama.cpp revision; in b11521, 1776 is a fused-FFN check.
- **The compiler delta, if cuBLAS doesn't explain the shift.** S0 is cicc 13.0 PTX JIT-compiled by the R615 driver;
  S2 is cicc 13.4.3 PTX compiled offline by ptxas 13.4.92. The driver's JIT and the offline ptxas are both 13.4-era,
  but nothing guarantees they are the same build with the same options. So we'd read a native-kernel shift as "cicc
  13.0 vs 13.4, or driver JIT vs offline ptxas", with S1 vs S2 isolating the build flags. That's slightly weaker than
  "strictly cicc".

## Questions

1. Are your three fixes applied as you meant them? They are: the FA-off resolution in `parse_log` and `evidence()`,
   `arm_cap` per arm with no global raise in `main()`, and the nofa arms on "all" with all-prompt attributions.
2. Does your green light for v6 (18a5f75780ed6c4d8fd9682ccddfa343626728b315c1ecf66643a0f251823c6c) stand?

## Your three fixes as applied: the v4 → v5 diff

Besides your three fixes, v5 has two behaviour-neutral changes:
- the per-sample check moved into `check_memory(used)`, and the cap into `arm_cap(kind)`, so the tests can reach them;
- `evidence()` closes its log file.

```diff
--- diag_test.py@v4
+++ diag_test.py@v5
@@ -1,10 +1,11 @@
-"""Diagnosis harness v4: why the CUDA 13.4 Update 2 backend's outputs differ from stock (Ollama 0.40.4, qwen3:8b).
+"""Diagnosis harness v5: why the CUDA 13.4 Update 2 backend's outputs differ from stock (Ollama 0.40.4, qwen3:8b).
 
 It generalises the reviewed sandbox test v3 to N arms. Every GPU arm runs as a sandbox on 11500 from its own tree
 under E:\\AI\\ollama-diag-0404\\<arm>\\run, one arm and one model at a time. The environment is identical across arms
 except the tree's cuda_v13 folder, and OLLAMA_FLASH_ATTENTION=0 on the two FA-off arms. The installed Ollama on
 11434 isn't used, and must answer empty before every generation. Card memory.used is sampled every 1 s against the
-cap; a breach kills the running arm's process tree and unloads 11434. Total CPU is sampled during the CPU reference
+running arm's cap (9,216 MiB on every S arm; 14,336 MiB on the reference arm only, when it is q8_0); a breach kills
+the running arm's process tree and unloads 11434. Total CPU is sampled during the CPU reference
 arm, which stops if it holds above 60% for 10 s. Every record is flushed as it is written. Analysis uses rnd's
 ab_dataminer (mcptoolshop_rnd/abmine.py), whose sha256 is frozen with this script's.
 
@@ -31,7 +32,7 @@
 FROZEN = os.path.join(HERE, "diag_test.FROZEN.sha256")
 MODELS = r"E:\AI-Models\Ollama"
 STOCK, SANDBOX = "http://127.0.0.1:11434", "http://127.0.0.1:11500"
-CAP_MIB = 9216  # raised to 14336 if REFERENCE is "q8_0"
+CAP_MIB = 9216  # the running arm's cap, set per arm in run_arm: 14336 only on the q8_0 reference arm
 OPTIONS = {"num_ctx": 2048, "num_predict": 64, "temperature": 0, "top_k": 1, "seed": 42}
 TOP_LOGPROBS = 10
 WARMUP = ("Say hello.", {**OPTIONS, "num_predict": 16})
@@ -40,7 +41,7 @@
 
 # The reference arm is the Director's choice: "cpu" (stock tree, CUDA hidden, Q4_K_M on 6 E-cores) or "q8_0"
 # (stock tree on the GPU, qwen3:8b-q8_0, downloaded beforehand under its own approval). None refuses to run.
-REFERENCE = "q8_0"  # the Director's choice, 2026-10-15: qwen3:8b-q8_0 on the GPU (stock tree), cap raised to 14,336 MiB
+REFERENCE = "q8_0"  # the Director's choice, 2026-10-15: qwen3:8b-q8_0 on the GPU (stock tree), its arm capped at 14,336 MiB
 
 # The model files, pinned: the model layer's digest and size in each manifest, and the shared template.
 MODEL_PINS = {
@@ -66,8 +67,8 @@
     ("S1", "S1", B1341, "auto", "all", "gpu"),
     ("S2", "S2", B1343, "auto", "all", "gpu"),
     ("S0_cb1343", "S0_cb1343", CB1343, "auto", "all", "gpu"),
-    ("S0_nofa", "S0", STOCK_DLL, "off", "original", "gpu"),
-    ("S2_nofa", "S2", B1343, "off", "original", "gpu"),
+    ("S0_nofa", "S0", STOCK_DLL, "off", "all", "gpu"),
+    ("S2_nofa", "S2", B1343, "off", "all", "gpu"),
     ("REF", "S0", STOCK_DLL, "auto", "all", "reference"),
     ("S0p", "S0", STOCK_DLL, "auto", "all", "gpu"),  # S0′, last
 ]
@@ -135,16 +136,25 @@
     subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, timeout=60)
 
 
+def arm_cap(kind):
+    """The arm's memory cap: 14,336 MiB only on the reference arm when it is q8_0, 9,216 MiB on every other arm."""
+    return 14336 if (kind == "reference" and REFERENCE == "q8_0") else 9216
+
+
+def check_memory(used):
+    """One memory.used sample against the running arm's cap (the global, read on every sample)."""
+    state["peak"] = max(state["peak"], used)
+    if used > CAP_MIB and not state["breach"]:
+        state["breach"] = used
+        record("BREACH", memory_used_mib=used, cap_mib=CAP_MIB)
+        threading.Thread(target=kill_arm, daemon=True).start()
+        threading.Thread(target=unload, args=(STOCK,), daemon=True).start()
+
+
 def sampler():
     while not state["stop"]:
         try:
-            used = memory_used()
-            state["peak"] = max(state["peak"], used)
-            if used > CAP_MIB and not state["breach"]:
-                state["breach"] = used
-                record("BREACH", memory_used_mib=used, cap_mib=CAP_MIB)
-                threading.Thread(target=kill_arm, daemon=True).start()
-                threading.Thread(target=unload, args=(STOCK,), daemon=True).start()
+            check_memory(memory_used())
         except Exception as e:
             record("vram_read_error", error=repr(e))
         if state["cpu_watch"]:
@@ -242,6 +252,8 @@
 
 
 def run_arm(name, tree, expected, fa, which, kind):
+    global CAP_MIB
+    CAP_MIB = arm_cap(kind)  # set before the arm starts; the previous arm has unloaded and been killed
     run_dir = os.path.join(HERE, tree, "run")
     cuda = os.path.join(run_dir, "lib", "ollama", "cuda_v13")
     got = tuple(sha_file(os.path.join(cuda, f)) for f in ("ggml-cuda.dll", "cublas64_13.dll", "cublasLt64_13.dll"))
@@ -256,7 +268,7 @@
     env = arm_env(run_dir, fa, kind)
     log_path = os.path.join(HERE, f"{name}-11500.log")
     state["arm_dir"] = run_dir
-    record("arm_start", arm=name, tree=tree, fa=fa, kind=kind, model=model, options=options,
+    record("arm_start", arm=name, tree=tree, fa=fa, kind=kind, model=model, options=options, cap_mib=CAP_MIB,
            env={k: env.get(k) for k in ("CUDA_VISIBLE_DEVICES", "OLLAMA_LLM_LIBRARY", "OLLAMA_FLASH_ATTENTION", "OLLAMA_DEBUG", "USERPROFILE")})
     exe = os.path.join(run_dir, "ollama.exe")
     if cpu_ref:  # E-cores 2-7 at below-normal priority, inherited by the runner
@@ -310,7 +322,8 @@
     """Criterion 1 for a GPU arm: the log names this tree's cuda_v13 DLL, CUDA, compute 12.0, and the expected
     FlashAttention resolution. Skipped on the CPU reference arm, where CUDA is hidden on purpose."""
     try:
-        text = open(os.path.join(HERE, f"{name}-11500.log"), encoding="utf-8", errors="replace").read()
+        with open(os.path.join(HERE, f"{name}-11500.log"), encoding="utf-8", errors="replace") as f:
+            text = f.read()
     except OSError as e:
         return {"ok": False, "error": repr(e)}
     lg = abmine.parse_log(text)
@@ -321,7 +334,7 @@
     cuda = [b for b in lg["backends"] if b["kind"] == "CUDA"]
     ok = (bool(cuda) and want in cuda[-1]["path"].lower() and (lg["device"] or {}).get("compute") == "12.0"
           and (lg["inference_compute"] or {}).get("library") == "CUDA"
-          and (fa != "off" or lg["flash_attn_resolved"] == "disabled"))
+          and lg["flash_attn_resolved"] == ("disabled" if fa == "off" else "enabled"))
     return {"ok": ok, "backend": cuda[-1]["path"] if cuda else None, "device": lg["device"],
             "flash_attn": [lg["flash_attn_setting"], lg["flash_attn_resolved"]], "kv": lg["kv_types"],
             "dll_ok": expected[0] == sha_file(os.path.join(HERE, tree, "run", "lib", "ollama", "cuda_v13", "ggml-cuda.dll"))}
@@ -345,16 +358,15 @@
           of S0's.
     S0 must equal S0′ token for token, or the run can't decide. A pass makes S2 eligible; activation is still the
     Director's separate go."""
-    orig = {i for i, p in enumerate(PROMPTS) if p["set"] == "original"}
     out = {"S0_equals_S0p": same(recs, "S0", "S0p")}
     a = same(recs, "S2", "S1")
     shift = not same(recs, "S0", "S2")
-    attrib = []
+    attrib = []  # every attribution that holds is reported
     if same(recs, "S0_cb1343", "S2"):
         attrib.append("cuBLAS 13.0 to 13.4: stock ggml-cuda with 13.4.3's cuBLAS reproduces S2")
-    if same(recs, "S0_nofa", "S2_nofa", orig) and not same(recs, "S0", "S2", orig):
-        attrib.append("fattn: with FlashAttention off, S0 and S2 agree on the original prompts")
-    if (same(recs, "S0_cb1343", "S0") and not same(recs, "S0_nofa", "S2_nofa", orig)
+    if same(recs, "S0_nofa", "S2_nofa") and shift:
+        attrib.append("fattn: with FlashAttention off, S0 and S2 agree on all prompts")
+    if (same(recs, "S0_cb1343", "S0") and not same(recs, "S0_nofa", "S2_nofa")
             and not same(recs, "S1", "S0")):
         attrib.append("native sm_120a MMQ/MMVQ: cuBLAS alone changes nothing, FA off doesn't remove it, and the 13.4.1 native build also differs")
     b = (not shift) or bool(attrib)
@@ -413,20 +425,18 @@
 
 
 def main():
-    global CAP_MIB
     for stream in (sys.stdout, sys.stderr):  # the verdict prints S0′; a cp1252 console would crash at the very end
         if hasattr(stream, "reconfigure"):
             stream.reconfigure(encoding="utf-8", errors="replace")
     t0 = time.time()
     if REFERENCE not in ("cpu", "q8_0"):
         raise SystemExit("REFUSED: REFERENCE is not chosen ('cpu' or 'q8_0'); it is the Director's choice")
-    if REFERENCE == "q8_0":
-        CAP_MIB = 14336
     shas = self_check()
     models = check_models()
     open(RECORD, "w").close()
     baseline = memory_used()
-    record("start", script_sha256=shas, models=models, baseline_mib=baseline, cap_mib=CAP_MIB, reference=REFERENCE, options=OPTIONS,
+    record("start", script_sha256=shas, models=models, baseline_mib=baseline,
+           cap_mib={a[0]: arm_cap(a[5]) for a in ARMS}, reference=REFERENCE, options=OPTIONS,
            top_logprobs=TOP_LOGPROBS, prompts=[p["id"] for p in PROMPTS])
     threading.Thread(target=sampler, daemon=True).start()
     try:
```

## The abmine change (rnd commit 40f7400)

```diff
diff --git a/mcptoolshop_rnd/abmine.py b/mcptoolshop_rnd/abmine.py
index 2f02d1e..8453999 100644
--- a/mcptoolshop_rnd/abmine.py
+++ b/mcptoolshop_rnd/abmine.py
@@ -281,6 +281,10 @@ def parse_log(text: str) -> dict:
             out["inference_compute"] = {"library": m.group(1), "compute": m.group(2), "description": m.group(3)}
         elif m := _LOG_PATTERNS["flash_attn_setting"].search(line):
             out["flash_attn_setting"] = m.group(1)
+            # A forced setting is its own resolution: with --flash-attn off (or on), llama.cpp logs
+            # "flash_attn = disabled" (or "enabled") and skips resolve_fused_ops, which only resolves "auto".
+            if m.group(1) in ("enabled", "disabled"):
+                out["flash_attn_resolved"] = m.group(1)
         elif m := _LOG_PATTERNS["flash_attn_resolved"].search(line):
             out["flash_attn_resolved"] = m.group(1)
         elif m := _LOG_PATTERNS["kv_types"].search(line):
diff --git a/tests/test_abmine.py b/tests/test_abmine.py
index 34487d7..612d4f2 100644
--- a/tests/test_abmine.py
+++ b/tests/test_abmine.py
@@ -196,6 +196,17 @@ class Logs(unittest.TestCase):
         self.assertEqual(lg["graphs_reused"], [11])
         self.assertEqual(lg["prompt_tokens"], [19])
 
+    def test_a_forced_flash_attention_setting_is_its_own_resolution(self):
+        # With OLLAMA_FLASH_ATTENTION=0, Ollama passes --flash-attn off; llama.cpp logs the setting as "disabled"
+        # and never prints a "Flash Attention ..." resolution line (resolve_fused_ops runs only for "auto").
+        lg = abmine.parse_log("llama_context: flash_attn            = disabled")
+        self.assertEqual((lg["flash_attn_setting"], lg["flash_attn_resolved"]), ("disabled", "disabled"))
+        lg = abmine.parse_log("llama_context: flash_attn            = enabled")
+        self.assertEqual(lg["flash_attn_resolved"], "enabled")
+        lg = abmine.parse_log("\n".join(["llama_context: flash_attn            = auto",
+                                         "resolve_fused_ops: Flash Attention disabled"]))
+        self.assertEqual((lg["flash_attn_setting"], lg["flash_attn_resolved"]), ("auto", "disabled"))
+
     def test_an_empty_log(self):
         lg = abmine.parse_log("")
         self.assertIsNone(lg["flash_attn_resolved"])
```
