"""Offline tests for the diagnosis harness: no GPU, no server. Run: python -m unittest test_diag_test

DryRun runs main() end to end with the rig faked (nvidia-smi, typeperf, PowerShell, both Ollama servers and the arm
processes), so every line a GPU run executes is executed here first."""

import contextlib
import hashlib
import io
import json
import os
import re
import tempfile
import threading
import time
import types
import unittest
import urllib.error
from unittest import mock

import diag_test as dt
from mcptoolshop_rnd import abmine

BASE, ALT = ["a", "b", "c"], ["a", "b", "x"]


def gen(tokens):
    return abmine.Gen(tokens=list(tokens), top=[[(t, -0.1), ("z", -5.0)] for t in tokens], prompt_eval_count=10)


def arms(**which):
    """recs for every arm on all 15 prompts: BASE unless the arm is named, ALT (or a callable per prompt) if it is."""
    names = ["S0", "S1", "S2", "S0_cb1343", "S0_nofa", "S2_nofa", "REF", "S0p"]
    out = {}
    for name in names:
        w = which.get(name)
        out[name] = {p: gen(w(p) if callable(w) else (ALT if w else BASE)) for p in range(len(dt.PROMPTS))}
    return out


def ok_all(recs):
    return {a: {p: True for p in ps} for a, ps in recs.items()}


class TreeCase(unittest.TestCase):
    """A temporary HERE holding tree S0 with three DLL files."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        p = mock.patch.object(dt, "HERE", self.tmp.name)
        p.start()
        self.addCleanup(p.stop)
        self.cuda = os.path.join(self.tmp.name, "S0", "run", "lib", "ollama", "cuda_v13")
        os.makedirs(self.cuda)
        for f in ("ggml-cuda.dll", "cublas64_13.dll", "cublasLt64_13.dll"):
            with open(os.path.join(self.cuda, f), "wb") as fh:
                fh.write(f.encode())
        self.expected = tuple(dt.sha_file(os.path.join(self.cuda, f))
                              for f in ("ggml-cuda.dll", "cublas64_13.dll", "cublasLt64_13.dll"))


class TestEvidence(TreeCase):
    def log(self, name, *fa_lines):
        lines = [
            'time=2026-10-15T14:09:15.021-04:00 level=INFO source=types.go:32 msg="inference compute" id=0 filter_id=0 '
            'library=CUDA compute=12.0 name=CUDA0 description="NVIDIA GeForce RTX 5090" libdirs=ollama,cuda_v13',
            "  Device 0: NVIDIA GeForce RTX 5090, compute capability 12.0, VMM: yes, VRAM: 32579 MiB",
            "load_backend: loaded CUDA backend from " + os.path.join(self.cuda, "ggml-cuda.dll"),
            *fa_lines,
        ]
        with open(os.path.join(self.tmp.name, f"{name}-11500.log"), "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")

    def test_an_fa_off_arm_passes_on_the_real_forced_off_line(self):
        self.log("S0_nofa", "llama_context: flash_attn            = disabled")
        ev = dt.evidence("S0_nofa", "S0", self.expected, "off", "gpu")
        self.assertTrue(ev["ok"], ev)
        self.assertEqual(ev["flash_attn"], ["disabled", "disabled"])

    def test_an_fa_auto_arm_needs_flash_attention_enabled(self):
        self.log("S0", "llama_context: flash_attn            = auto", "resolve_fused_ops: Flash Attention enabled")
        self.assertTrue(dt.evidence("S0", "S0", self.expected, "auto", "gpu")["ok"])
        self.log("S0", "llama_context: flash_attn            = auto", "resolve_fused_ops: Flash Attention disabled")
        self.assertFalse(dt.evidence("S0", "S0", self.expected, "auto", "gpu")["ok"])

    def test_an_fa_off_arm_fails_if_flash_attention_ran(self):
        self.log("S0_nofa", "llama_context: flash_attn            = auto", "resolve_fused_ops: Flash Attention enabled")
        self.assertFalse(dt.evidence("S0_nofa", "S0", self.expected, "off", "gpu")["ok"])


class TestCap(TreeCase):
    def setUp(self):
        super().setUp()
        for name, value in (("record", mock.DEFAULT), ("kill_arm", mock.DEFAULT), ("unload", mock.DEFAULT)):
            p = mock.patch.object(dt, name)
            self.__dict__[name] = p.start()
            self.addCleanup(p.stop)
        self.addCleanup(dt.state.update, dict(dt.state))
        dt.state.update(peak=0, breach=None)
        self.addCleanup(setattr, dt, "CAP_MIB", dt.CAP_MIB)

    def start_arm(self, kind):
        """run_arm sets the cap first; a DLL mismatch then stops it before any server starts."""
        with self.assertRaises(SystemExit):
            dt.run_arm("arm", "S0", ("not", "these", "dlls"), "auto", "all", kind)

    def test_the_caps_per_arm(self):
        self.assertEqual(dt.arm_cap("gpu"), 9216)
        self.assertEqual(dt.arm_cap("reference"), 14336)
        with mock.patch.object(dt, "REFERENCE", "cpu"):
            self.assertEqual(dt.arm_cap("reference"), 9216)

    def test_an_s_arm_after_the_reference_arm_trips_at_9300(self):
        dt.CAP_MIB = 14336  # as the REF arm left it
        self.start_arm("gpu")
        self.assertEqual(dt.CAP_MIB, 9216)
        dt.check_memory(9300)
        self.assertEqual(dt.state["breach"], 9300)
        self.record.assert_any_call("BREACH", memory_used_mib=9300, cap_mib=9216)

    def test_the_reference_arm_runs_at_14336(self):
        self.start_arm("reference")
        self.assertEqual(dt.CAP_MIB, 14336)
        dt.check_memory(9300)
        self.assertIsNone(dt.state["breach"])
        dt.check_memory(14400)
        self.assertEqual(dt.state["breach"], 14400)

    def test_main_no_longer_raises_the_cap(self):
        with open(dt.__file__, encoding="utf-8") as f:
            src = f.read()
        body = src[src.index("def main():"):]
        self.assertNotIn("CAP_MIB =", body)


class TestVerdict(unittest.TestCase):
    def v(self, recs):
        return dt.verdict(recs, ok_all(recs))

    def test_fattn_when_the_fa_off_arms_agree_on_all_prompts(self):
        v = self.v(arms(S2=True, S1=True))
        self.assertTrue(v["b_shift_present"])
        self.assertEqual(len(v["b_attribution"]), 1)
        self.assertTrue(v["b_attribution"][0].startswith("fattn"))
        self.assertTrue(v["b"])
        self.assertTrue(v["decision"].startswith("S2 ELIGIBLE"))

    def test_no_fattn_when_the_fa_off_arms_agree_on_the_original_prompts_only(self):
        late = lambda p: ALT if p >= 3 else BASE  # noqa: E731
        v = self.v(arms(S2=True, S1=True, S2_nofa=late))
        self.assertFalse(any(a.startswith("fattn") for a in v["b_attribution"]))
        self.assertEqual([a.split(":")[0] for a in v["b_attribution"]], ["native sm_120a MMQ/MMVQ"])

    def test_native_when_cublas_changes_nothing_and_fa_off_keeps_the_shift(self):
        v = self.v(arms(S2=True, S1=True, S2_nofa=True))
        self.assertEqual([a.split(":")[0] for a in v["b_attribution"]], ["native sm_120a MMQ/MMVQ"])
        self.assertTrue(v["b"])

    def test_cublas_and_fattn_are_both_reported_when_both_hold(self):
        v = self.v(arms(S2=True, S1=True, S0_cb1343=True))
        self.assertEqual([a.split(":")[0] for a in v["b_attribution"]], ["cuBLAS 13.0 to 13.4", "fattn"])

    def test_cublas_alone(self):
        v = self.v(arms(S2=True, S1=True, S0_cb1343=True, S2_nofa=True))
        self.assertEqual([a.split(":")[0] for a in v["b_attribution"]], ["cuBLAS 13.0 to 13.4"])

    def test_a_compound_cause_attributes_nothing_and_fails_b(self):
        third = lambda p: ["a", "q", "r"]  # noqa: E731  # cuBLAS swapped alone matches neither S0 nor S2
        v = self.v(arms(S2=True, S1=True, S0_cb1343=third, S2_nofa=True))
        self.assertEqual(v["b_attribution"], [])
        self.assertFalse(v["b"])
        self.assertIn("part(s) b", v["decision"])

    def test_no_shift_needs_no_attribution(self):
        v = self.v(arms())
        self.assertFalse(v["b_shift_present"])
        self.assertTrue(v["b"])

    def test_s0_and_s0p_differing_is_inconclusive(self):
        self.assertTrue(self.v(arms(S0p=True))["decision"].startswith("INCONCLUSIVE"))


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

        # The frozen harness appends to the record from several threads (main, sampler, kill and unload). On
        # Windows, concurrent appends from separate handles can overwrite one another, which dropped the BREACH
        # line under full-suite load. Serialise the writes here; diag_test.py stays frozen.
        record_lock, real_record = threading.Lock(), dt.record

        def record(kind, **data):
            with record_lock:
                real_record(kind, **data)

        patches = {"HERE": self.here, "RECORD": os.path.join(self.here, "diag-record.jsonl"), "FROZEN": frozen,
                   "MODELS": store, "MODEL_PINS": pins, "RND": os.path.dirname(os.path.dirname(abmine_path)),
                   "ARMS": arms, "sampler": sampler, "record": record,
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


if __name__ == "__main__":
    unittest.main()
