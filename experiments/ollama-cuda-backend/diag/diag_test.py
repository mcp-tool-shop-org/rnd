"""Diagnosis harness v6: why the CUDA 13.4 Update 2 backend's outputs differ from stock (Ollama 0.40.4, qwen3:8b).

It generalises the reviewed sandbox test v3 to N arms. Every GPU arm runs as a sandbox on 11500 from its own tree
under E:\\AI\\ollama-diag-0404\\<arm>\\run, one arm and one model at a time. The environment is identical across arms
except the tree's cuda_v13 folder, and OLLAMA_FLASH_ATTENTION=0 on the two FA-off arms. The installed Ollama on
11434 isn't used, and must answer empty before every generation. Card memory.used is sampled every 1 s against the
running arm's cap (9,216 MiB on every S arm; 14,336 MiB on the reference arm only, when it is q8_0); a breach kills
the running arm's process tree and unloads 11434. Total CPU is sampled during the CPU reference
arm, which stops if it holds above 60% for 10 s. Every record is flushed as it is written. Analysis uses rnd's
ab_dataminer (mcptoolshop_rnd/abmine.py), whose sha256 is frozen with this script's.

Nothing runs unless this script's sha256 and abmine.py's both match diag_test.FROZEN.sha256, every arm's DLL hashes
match ARMS below, and REFERENCE has been chosen. Stdlib only.
"""

import hashlib
import json
import os
import re
import subprocess
import sys
import threading
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
RND = r"E:\AI\Research and Development"
sys.path.insert(0, RND)
from mcptoolshop_rnd import abmine  # noqa: E402

RECORD = os.path.join(HERE, "diag-record.jsonl")
FROZEN = os.path.join(HERE, "diag_test.FROZEN.sha256")
MODELS = r"E:\AI-Models\Ollama"
STOCK, SANDBOX = "http://127.0.0.1:11434", "http://127.0.0.1:11500"
CAP_MIB = 9216  # the running arm's cap, set per arm in run_arm: 14336 only on the q8_0 reference arm
OPTIONS = {"num_ctx": 2048, "num_predict": 64, "temperature": 0, "top_k": 1, "seed": 42}
TOP_LOGPROBS = 10
WARMUP = ("Say hello.", {**OPTIONS, "num_predict": 16})
NEAR_TIE = 1e-3
MAE_MARGIN = 0.005  # activation rule (c): S2's chosen-token MAE against the reference within this of S0's

# The reference arm is the Director's choice: "cpu" (stock tree, CUDA hidden, Q4_K_M on 6 E-cores) or "q8_0"
# (stock tree on the GPU, qwen3:8b-q8_0, downloaded beforehand under its own approval). None refuses to run.
REFERENCE = "q8_0"  # the Director's choice, 2026-10-15: qwen3:8b-q8_0 on the GPU (stock tree), its arm capped at 14,336 MiB

# The model files, pinned: the model layer's digest and size in each manifest, and the shared template.
MODEL_PINS = {
    "8b": ("sha256:a3de86cd1c132c822487ededd47a324c50491393e6565cd14bafa40d0b8e686f", 5225374496),
    "8b-q8_0": ("sha256:d87f4a5a2f1a6051d9fac010c12f76f3ba2137b137d413ba8f4d3a3d06b3a25b", 8851075872),
}
TEMPLATE_DIGEST = "sha256:ae370d884f108d16e7cc8fd5259ebc5773a0afa6e078b11f4ed7e39a27e0dfc4"

STOCK_DLL = ("2f7f959a70c6f8a7ccc4f59d9bdf6dbaa60e40266179d36a738c70f7e448b2bf",
             "f0acb41173e8d9214b043156d2b3944f1f9183164c3f691518da4231e1b8d302",
             "a755763c497315caabade7f04b69dfea2a138be5f5d53907d8531e1cf9d0b157")
B1341 = ("ab9bef88f8bf016b95e2d39a57ae2a1e140305b7d6f1e365a49e78ec37b4cb2c",
         "1119dbca0a808e0c8850bb4221e330daf0b5ddb348d62d37b6ac533854723df9",
         "0f5bc315fef706b5626248ebd74e8a48a9e82fa2f0cad38330f5f70984913107")
B1343 = ("0ebc0e61c7288e6a7367f21c1fbd9a8501e423927e55902c0f0476cdd8608c6a",
         "60bbba8868290311e9c1657b2193ddec667744eb555ff843f87acb7c039f9efa",
         "cad63434448e7141629e240ea093ad596a7ef6a0f67b468ba9bc1df6e1eeee33")
CB1343 = (STOCK_DLL[0], B1343[1], B1343[2])

# name, tree, expected (ggml-cuda, cublas64_13, cublasLt64_13), flash attention ("auto" or "off"), prompts, kind
ARMS = [
    ("S0", "S0", STOCK_DLL, "auto", "all", "gpu"),
    ("S1", "S1", B1341, "auto", "all", "gpu"),
    ("S2", "S2", B1343, "auto", "all", "gpu"),
    ("S0_cb1343", "S0_cb1343", CB1343, "auto", "all", "gpu"),
    ("S0_nofa", "S0", STOCK_DLL, "off", "all", "gpu"),
    ("S2_nofa", "S2", B1343, "off", "all", "gpu"),
    ("REF", "S0", STOCK_DLL, "auto", "all", "reference"),
    ("S0p", "S0", STOCK_DLL, "auto", "all", "gpu"),  # S0′, last
]

# The prompts, fixed before the run. A check that fails is a task failure for activation rule (c).
PROMPTS = [
    {"id": "orig_sky", "set": "original", "prompt": "Explain in three sentences why the sky is blue.", "check": None},
    {"id": "orig_fib", "set": "original", "prompt": "Write a Python function that returns the n-th Fibonacci number iteratively.", "check": None},
    {"id": "orig_hammer", "set": "original", "prompt": "List five uses of a hammer, one per line.", "check": None},
    {"id": "prose_rainbow", "set": "prose", "prompt": "Explain in two sentences what a rainbow is.", "check": {"contains_any": ["light", "sun", "refract", "water"]}},
    {"id": "prose_library", "set": "prose", "prompt": "Describe a quiet library in three sentences.", "check": {"contains_any": ["book", "quiet", "silen"]}},
    {"id": "prose_advice", "set": "prose", "prompt": "Give one piece of advice to a new programmer, in two sentences.", "check": {"contains_any": ["code", "learn", "practice", "program"]}},
    {"id": "prose_romeo", "set": "prose", "prompt": "Summarise the plot of Romeo and Juliet in two sentences.", "check": {"contains_any": ["Romeo", "Juliet"]}},
    {"id": "math_mul", "set": "code_math", "prompt": "What is 17 multiplied by 23? Answer with the number only.", "check": {"contains_any": ["391"]}},
    {"id": "math_sum", "set": "code_math", "prompt": "What is the sum of the integers from 1 to 20? Answer with the number only.", "check": {"contains_any": ["210"]}},
    {"id": "code_reverse", "set": "code_math", "prompt": "Write a Python expression that reverses a string s. Answer with the expression only.", "check": {"contains_any": ["[::-1]", "reversed("]}},
    {"id": "code_len", "set": "code_math", "prompt": "In Python, what does len([1, 2, 3]) return? Answer with the number only.", "check": {"contains_any": ["3"]}},
    {"id": "json_person", "set": "extraction", "prompt": 'Return only JSON with keys "name" and "age" for this sentence: "Maria is 34 years old."', "check": {"json": {"name": "Maria", "age": 34}}},
    {"id": "json_place", "set": "extraction", "prompt": 'Return only JSON with keys "city" and "country" for this sentence: "The Louvre is in Paris, France."', "check": {"json": {"city": "Paris", "country": "France"}}},
    {"id": "json_price", "set": "extraction", "prompt": 'Return only JSON with keys "item" and "price" for this sentence: "A coffee costs 4 dollars."', "check": {"json": {"item": None, "price": 4}}},
    {"id": "json_colors", "set": "extraction", "prompt": 'Return only JSON with the key "colors" as a list, for this sentence: "The flag is red, white and blue."', "check": {"json": {"colors": ["red", "white", "blue"]}}},
]

state = {"peak": 0, "breach": None, "stop": False, "arm_dir": None, "cpu_watch": False, "cpu_over": 0, "cpu_stop": None}


def record(kind, **data):
    with open(RECORD, "a", encoding="utf-8") as f:
        f.write(json.dumps({"t": time.strftime("%H:%M:%S"), "kind": kind, **data}, ensure_ascii=False) + "\n")
        f.flush()
        os.fsync(f.fileno())


def http(base, path, body=None, timeout=600):
    req = urllib.request.Request(base + path, data=None if body is None else json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def sha_file(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def memory_used():
    return int(subprocess.run(["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
                              capture_output=True, text=True, timeout=10).stdout.strip().splitlines()[0])


def total_cpu():
    out = subprocess.run(["typeperf", r"\Processor(_Total)\% Processor Time", "-sc", "1"],
                         capture_output=True, text=True, timeout=15).stdout
    vals = re.findall(r'"[^"]*","([\d.]+)"', out)
    return float(vals[-1]) if vals else None


def kill_arm():
    """Kill every ollama.exe and llama-server.exe started from the running arm's tree."""
    d = state["arm_dir"]
    if not d:
        return
    ps = ("Get-CimInstance Win32_Process | Where-Object { ($_.Name -eq 'ollama.exe' -or $_.Name -eq 'llama-server.exe') "
          f"-and $_.ExecutablePath -like '{d}*' }} | ForEach-Object {{ taskkill /PID $_.ProcessId /T /F | Out-Null }}")
    subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, timeout=60)


def arm_cap(kind):
    """The arm's memory cap: 14,336 MiB only on the reference arm when it is q8_0, 9,216 MiB on every other arm."""
    return 14336 if (kind == "reference" and REFERENCE == "q8_0") else 9216


def check_memory(used):
    """One memory.used sample against the running arm's cap (the global, read on every sample)."""
    state["peak"] = max(state["peak"], used)
    if used > CAP_MIB and not state["breach"]:
        state["breach"] = used
        record("BREACH", memory_used_mib=used, cap_mib=CAP_MIB)
        threading.Thread(target=kill_arm, daemon=True).start()
        threading.Thread(target=unload, args=(STOCK,), daemon=True).start()


def sampler():
    while not state["stop"]:
        try:
            check_memory(memory_used())
        except Exception as e:
            record("vram_read_error", error=repr(e))
        if state["cpu_watch"]:
            try:
                c = total_cpu()
                state["cpu_over"] = state["cpu_over"] + 1 if c is not None and c > 60 else 0
                if state["cpu_over"] >= 4 and not state["cpu_stop"]:  # about 10 s at one sample per ~2.5 s
                    state["cpu_stop"] = c
                    record("CPU_STOP", total_cpu_pct=c)
                    threading.Thread(target=kill_arm, daemon=True).start()
            except Exception as e:
                record("cpu_read_error", error=repr(e))
        time.sleep(1)


def loaded(base):
    try:
        return [m["name"] for m in http(base, "/api/ps", timeout=10)["models"]]
    except Exception:
        return None


def unload(base, model="qwen3:8b"):
    try:
        http(base, "/api/generate", {"model": model, "keep_alive": 0}, timeout=60)
    except Exception as e:
        record("unload_error", server=base, error=repr(e))
    for _ in range(30):
        if loaded(base) == []:
            return True
        time.sleep(1)
    return False


def check_stops():
    if state["breach"]:
        raise SystemExit(f"STOP: memory.used {state['breach']} MiB passed the {CAP_MIB} MiB cap")
    if state["cpu_stop"]:
        raise SystemExit(f"STOP: total CPU held above 60% ({state['cpu_stop']}%) during the reference arm")


def stock_empty():
    if loaded(STOCK) != []:
        raise SystemExit("STOP: the installed Ollama on 11434 does not answer empty; never two models at once")


def task_check(spec, text):
    if not spec:
        return True
    if "contains_any" in spec:
        return any(s in text for s in spec["contains_any"])
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        return False
    try:
        obj = json.loads(m.group(0))
    except json.JSONDecodeError:
        return False
    for k, v in spec["json"].items():
        if k not in obj:
            return False
        if v is None:
            continue
        got = obj[k]
        if isinstance(v, list):
            if [str(x).lower() for x in got] != [str(x).lower() for x in v]:
                return False
        elif str(got).lower() != str(v).lower():
            return False
    return True


def arm_env(arm_dir, fa, kind):
    env = dict(os.environ)
    for k in ("CUDA_VISIBLE_DEVICES", "GGML_VK_VISIBLE_DEVICES", "OLLAMA_VULKAN", "OLLAMA_IGPU_ENABLE", "OLLAMA_NUM_GPU",
              "OMP_NUM_THREADS", "OLLAMA_LLM_LIBRARY", "OLLAMA_MODELS", "OLLAMA_FLASH_ATTENTION", "OLLAMA_KV_CACHE_TYPE"):
        env.pop(k, None)
    parts = env.get("PATH", "").split(os.pathsep)
    env["PATH"] = os.pathsep.join(p for p in parts if "\\programs\\ollama" not in p.lower().replace("/", "\\"))
    env.update(USERPROFILE=arm_dir, HOME=arm_dir, OLLAMA_HOST="127.0.0.1:11500", OLLAMA_MODELS=MODELS,
               OLLAMA_NOPRUNE="1", OLLAMA_KEEP_ALIVE="30s", OLLAMA_DEBUG="1")
    if kind == "reference" and REFERENCE == "cpu":
        env.update(CUDA_VISIBLE_DEVICES="-1", GGML_VK_VISIBLE_DEVICES="-1", OLLAMA_VULKAN="0", OLLAMA_IGPU_ENABLE="0")
    else:
        env.update(CUDA_VISIBLE_DEVICES="0", OLLAMA_LLM_LIBRARY="cuda_v13")
    if fa == "off":
        env["OLLAMA_FLASH_ATTENTION"] = "0"
    return env


def generate(model, prompt, options):
    body = {"model": model, "prompt": prompt, "think": False, "stream": False, "options": options,
            "keep_alive": "30s", "logprobs": True, "top_logprobs": TOP_LOGPROBS}
    return body, http(SANDBOX, "/api/generate", body)


def run_arm(name, tree, expected, fa, which, kind):
    global CAP_MIB
    CAP_MIB = arm_cap(kind)  # set before the arm starts; the previous arm has unloaded and been killed
    run_dir = os.path.join(HERE, tree, "run")
    cuda = os.path.join(run_dir, "lib", "ollama", "cuda_v13")
    got = tuple(sha_file(os.path.join(cuda, f)) for f in ("ggml-cuda.dll", "cublas64_13.dll", "cublasLt64_13.dll"))
    if got != expected:
        raise SystemExit(f"STOP: arm {name}'s tree {tree} does not hold its expected DLLs: {got}")
    stock_empty()
    if loaded(SANDBOX) is not None:
        raise SystemExit("STOP: something already answers on 11500")
    cpu_ref = kind == "reference" and REFERENCE == "cpu"
    model = "qwen3:8b-q8_0" if kind == "reference" and REFERENCE == "q8_0" else "qwen3:8b"
    options = {**OPTIONS, **({"num_gpu": 0, "num_thread": 6} if cpu_ref else {})}
    env = arm_env(run_dir, fa, kind)
    log_path = os.path.join(HERE, f"{name}-11500.log")
    state["arm_dir"] = run_dir
    record("arm_start", arm=name, tree=tree, fa=fa, arm_kind=kind, model=model, options=options, cap_mib=CAP_MIB,
           env={k: env.get(k) for k in ("CUDA_VISIBLE_DEVICES", "OLLAMA_LLM_LIBRARY", "OLLAMA_FLASH_ATTENTION", "OLLAMA_DEBUG", "USERPROFILE")})
    exe = os.path.join(run_dir, "ollama.exe")
    if cpu_ref:  # E-cores 2-7 at below-normal priority, inherited by the runner
        cmd = f'start "" /B /BELOWNORMAL /AFFINITY FC "{exe}" serve > "{log_path}" 2>&1'
        subprocess.Popen(["cmd.exe", "/c", cmd], env=env, cwd=run_dir)
        state["cpu_watch"] = True
    else:
        with open(log_path, "w", encoding="utf-8") as log:
            subprocess.Popen([exe, "serve"], env=env, stdout=log, stderr=log, cwd=run_dir)
    for _ in range(90):
        check_stops()
        if loaded(SANDBOX) is not None:
            break
        time.sleep(1)
    else:
        raise SystemExit(f"STOP: arm {name}'s server did not come up")
    prompts = [p for p in PROMPTS if which == "all" or p["set"] == "original"]
    try:
        stock_empty()
        _, r = generate(model, WARMUP[0], WARMUP[1])
        record("warmup", arm=name, load_duration_ns=r.get("load_duration"), peak_mib_so_far=state["peak"])
        for i, p in enumerate(PROMPTS):
            if p not in prompts:
                continue
            check_stops()
            stock_empty()
            body, r = generate(model, p["prompt"], options)
            lps = r.get("logprobs") or []
            text = r.get("response", "")
            record("result", arm=name, prompt=i, prompt_id=p["id"], response=text,
                   tokens=[t.get("token") for t in lps],
                   top=[[[c.get("token"), c.get("logprob")] for c in (t.get("top_logprobs") or [])] for t in lps],
                   eval_count=r.get("eval_count"), eval_duration_ns=r.get("eval_duration"),
                   prompt_eval_count=r.get("prompt_eval_count"), done_reason=r.get("done_reason"),
                   task_ok=task_check(p["check"], text), peak_mib_so_far=state["peak"],
                   body={k: v for k, v in body.items() if k != "prompt"})
        check_stops()
        ok = unload(SANDBOX, model)
        record("arm_unloaded", arm=name, empty=ok, peak_mib_so_far=state["peak"])
        if not ok:
            raise SystemExit(f"STOP: arm {name} did not unload")
    finally:
        kill_arm()
        state["cpu_watch"] = False
        time.sleep(3)
        record("arm_stopped", arm=name, sandbox_answering=loaded(SANDBOX) is not None)
        state["arm_dir"] = None


def evidence(name, tree, expected, fa, kind):
    """Criterion 1 for a GPU arm: the log names this tree's cuda_v13 DLL, CUDA, compute 12.0, and the expected
    FlashAttention resolution. Skipped on the CPU reference arm, where CUDA is hidden on purpose."""
    try:
        with open(os.path.join(HERE, f"{name}-11500.log"), encoding="utf-8", errors="replace") as f:
            text = f.read()
    except OSError as e:
        return {"ok": False, "error": repr(e)}
    lg = abmine.parse_log(text)
    if kind == "reference" and REFERENCE == "cpu":
        return {"skipped": "CPU reference arm", "no_cuda_backend": not any(b["kind"] == "CUDA" for b in lg["backends"]),
                "flash_attn": lg["flash_attn_resolved"], "kv": lg["kv_types"]}
    want = os.path.join(HERE, tree, "run", "lib", "ollama", "cuda_v13").lower()
    cuda = [b for b in lg["backends"] if b["kind"] == "CUDA"]
    ok = (bool(cuda) and want in cuda[-1]["path"].lower() and (lg["device"] or {}).get("compute") == "12.0"
          and (lg["inference_compute"] or {}).get("library") == "CUDA"
          and lg["flash_attn_resolved"] == ("disabled" if fa == "off" else "enabled"))
    return {"ok": ok, "backend": cuda[-1]["path"] if cuda else None, "device": lg["device"],
            "flash_attn": [lg["flash_attn_setting"], lg["flash_attn_resolved"]], "kv": lg["kv_types"],
            "dll_ok": expected[0] == sha_file(os.path.join(HERE, tree, "run", "lib", "ollama", "cuda_v13", "ggml-cuda.dll"))}


def same(recs, a, b, prompts=None):
    """Token for token on every prompt both arms ran (or the given ones)."""
    ps = sorted(set(recs.get(a, {})) & set(recs.get(b, {})))
    if prompts is not None:
        ps = [p for p in ps if p in prompts]
    return bool(ps) and all(recs[a][p].tokens == recs[b][p].tokens for p in ps)


def verdict(recs, task_ok):
    """The pre-registered activation rule (Argon's change 3, the Director's direction), computed exactly:
    activate S2 only if
      (a) S2 = S1 token for token on all prompts, AND
      (b) the S0 vs S2 shift isolates to native sm_120a kernels (fattn or MMQ/MMVQ) or the cuBLAS 13.0 to 13.4
          change, by the arm matrix, AND
      (c) S2 has zero task failures and its matched-prefix logprob MAE against the reference is within 0.005 nats
          of S0's.
    S0 must equal S0′ token for token, or the run can't decide. A pass makes S2 eligible; activation is still the
    Director's separate go."""
    out = {"S0_equals_S0p": same(recs, "S0", "S0p")}
    a = same(recs, "S2", "S1")
    shift = not same(recs, "S0", "S2")
    attrib = []  # every attribution that holds is reported
    if same(recs, "S0_cb1343", "S2"):
        attrib.append("cuBLAS 13.0 to 13.4: stock ggml-cuda with 13.4.3's cuBLAS reproduces S2")
    if same(recs, "S0_nofa", "S2_nofa") and shift:
        attrib.append("fattn: with FlashAttention off, S0 and S2 agree on all prompts")
    if (same(recs, "S0_cb1343", "S0") and not same(recs, "S0_nofa", "S2_nofa")
            and not same(recs, "S1", "S0")):
        attrib.append("native sm_120a MMQ/MMVQ: cuBLAS alone changes nothing, FA off doesn't remove it, and the 13.4.1 native build also differs")
    b = (not shift) or bool(attrib)
    s2_failures = sum(1 for p, ok in task_ok.get("S2", {}).items() if not ok)
    mae = abmine.analyze(recs, reference="REF", arms=[a_ for a_ in ("S0", "S2", "REF") if a_ in recs]).get("mae_vs_reference", {})
    m_s0, m_s2 = mae.get("S0"), mae.get("S2")
    c = s2_failures == 0 and m_s0 is not None and m_s2 is not None and (m_s2 - m_s0) <= MAE_MARGIN
    out.update({"a_S2_equals_S1": a, "b_shift_present": shift, "b_attribution": attrib, "b": b,
                "c_S2_task_failures": s2_failures, "c_mae_vs_ref": {"S0": m_s0, "S2": m_s2}, "c": c,
                "task_failures_by_arm": {arm: [PROMPTS[p]["id"] for p, ok in t.items() if not ok] for arm, t in task_ok.items()}})
    if not out["S0_equals_S0p"]:
        out["decision"] = "INCONCLUSIVE: S0 and S0′ differ, so stock is not repeatable across server starts"
    elif a and b and c:
        out["decision"] = "S2 ELIGIBLE for activation (the Director's go still required)"
    else:
        failed = [k for k, v in (("a", a), ("b", b), ("c", c)) if not v]
        out["decision"] = f"DO NOT ACTIVATE S2: rule part(s) {', '.join(failed)} not met"
    return out


def check_models():
    """Each model the run uses is in the store with its pinned model layer (digest and blob size) and template.
    The 5-9 GB blobs are not re-hashed here; the manifest digest and the blob's size are compared."""
    tags = ["8b"] + (["8b-q8_0"] if REFERENCE == "q8_0" else [])
    seen = {}
    for tag in tags:
        man_path = os.path.join(MODELS, "manifests", "registry.ollama.ai", "library", "qwen3", tag)
        try:
            with open(man_path, encoding="utf-8") as f:
                man = json.load(f)
        except OSError as e:
            raise SystemExit(f"REFUSED: qwen3:{tag} is not in the store ({e})")
        layers = {l["mediaType"].rsplit(".", 1)[-1]: l for l in man["layers"]}
        digest, size = MODEL_PINS[tag]
        if layers.get("model", {}).get("digest") != digest or layers["model"].get("size") != size:
            raise SystemExit(f"REFUSED: qwen3:{tag}'s model layer is {layers.get('model')}, not the pinned {digest}")
        if layers.get("template", {}).get("digest") != TEMPLATE_DIGEST:
            raise SystemExit(f"REFUSED: qwen3:{tag}'s template is not the pinned {TEMPLATE_DIGEST}")
        blob = os.path.join(MODELS, "blobs", digest.replace(":", "-"))
        if not os.path.isfile(blob) or os.path.getsize(blob) != size:
            raise SystemExit(f"REFUSED: qwen3:{tag}'s model blob is missing or the wrong size")
        seen[tag] = digest
    return seen


def self_check():
    try:
        with open(FROZEN, encoding="utf-8") as f:
            want = dict(line.split()[::-1][:2] for line in f if line.strip())
    except OSError:
        raise SystemExit(f"REFUSED: {FROZEN} does not exist; the script and abmine.py are frozen only after review")
    have = {"diag_test.py": sha_file(os.path.abspath(__file__)),
            "abmine.py": sha_file(os.path.join(RND, "mcptoolshop_rnd", "abmine.py"))}
    for name, h in have.items():
        if want.get(name) != h:
            raise SystemExit(f"REFUSED: {name} sha256 {h} is not the frozen {want.get(name)}")
    return have


def main():
    for stream in (sys.stdout, sys.stderr):  # the verdict prints S0′; a cp1252 console would crash at the very end
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    t0 = time.time()
    if REFERENCE not in ("cpu", "q8_0"):
        raise SystemExit("REFUSED: REFERENCE is not chosen ('cpu' or 'q8_0'); it is the Director's choice")
    shas = self_check()
    models = check_models()
    open(RECORD, "w").close()
    baseline = memory_used()
    record("start", script_sha256=shas, models=models, baseline_mib=baseline,
           cap_mib={a[0]: arm_cap(a[5]) for a in ARMS}, reference=REFERENCE, options=OPTIONS,
           top_logprobs=TOP_LOGPROBS, prompts=[p["id"] for p in PROMPTS])
    threading.Thread(target=sampler, daemon=True).start()
    try:
        for arm in ARMS:
            run_arm(*arm)
    finally:
        cleanup = {}
        try:
            if loaded(STOCK):
                cleanup["stock_unloaded"] = unload(STOCK)
        except Exception as e:
            cleanup["stock_unload_error"] = repr(e)
        kill_arm()
        time.sleep(3)
        state["stop"] = True
        try:
            cleanup["memory_used_end_mib"] = memory_used()
        except Exception as e:
            cleanup["end_read_error"] = repr(e)
        try:
            cleanup["sandbox_runner_left"] = subprocess.run(
                ["powershell", "-NoProfile", "-Command",
                 "(Get-CimInstance Win32_Process | Where-Object { $_.ExecutablePath -like '*ollama-diag-0404*' }).ProcessId"],
                capture_output=True, text=True, timeout=60).stdout.strip() or None
        except Exception as e:
            cleanup["runner_check_error"] = repr(e)
        record("cleanup", stock_ps=loaded(STOCK), sandbox_answering=loaded(SANDBOX) is not None, baseline_mib=baseline,
               peak_mib=state["peak"], wall_s=round(time.time() - t0, 1), **cleanup)

    recs = abmine.load_record_file(RECORD)
    task_ok = {}
    with open(RECORD, encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            if r["kind"] == "result":
                task_ok.setdefault(r["arm"], {})[r["prompt"]] = r["task_ok"]
    crit1 = {a[0]: evidence(a[0], a[1], a[2], a[3], a[5]) for a in ARMS}
    v = verdict(recs, task_ok)
    report = abmine.analyze(recs, reference="REF", arms=[a[0] for a in ARMS if a[0] in recs])
    record("verdict", criterion_1=crit1, **v)
    with open(os.path.join(HERE, "diag-analysis.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, indent=1, ensure_ascii=False, default=str)
    print(json.dumps({"criterion_1": crit1, **v, "peak_mib": state["peak"]}, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
