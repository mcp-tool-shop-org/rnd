"""Sandbox test of the 0.40.4 CUDA 13.4 backend, as SANDBOX-PLAN.md sets it out, v3 after Argon's review.
Stock A and stock B on 11434, then the sandbox on 11500; one model loaded at a time, checked before every prompt; card
memory.used sampled every 1 s against a 9,216 MiB cap, a breach killing the sandbox tree and unloading 11434 at once;
every record flushed as it is written; both servers unloaded and the sandbox stopped on every exit path. The script
refuses to run unless its own sha256 matches sandbox_test.FROZEN.sha256. Stdlib only."""

import hashlib
import json
import os
import subprocess
import threading
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
# The build under test is the CUDA 13.4 Update 2 (13.4.3) rebuild to the studio standard; its sandbox tree and DLL hash live in its folder.
BUILD = r"E:\AI\ollama-cu1343-0404"
RUN = os.path.join(BUILD, "run")
RECORD = os.path.join(BUILD, "sandbox-record.jsonl")
SANDBOX_LOG = os.path.join(BUILD, "sandbox-11500.log")
FROZEN = os.path.join(HERE, "sandbox_test.FROZEN.sha256")
STOCK, SANDBOX = "http://127.0.0.1:11434", "http://127.0.0.1:11500"
CAP_MIB = 9216
MODEL = "qwen3:8b"
# top_k 1 is kept. In 0.40.4, top_logprobs come from the full pre-sampling logits, so the sampler's truncation cannot
# leave fewer than two candidates. Ollama sets only n_probs = max(top_logprobs, 1) (llm/llama_server.go:1697-1699),
# never post_sampling_probs, whose default is false (llama.cpp b11521 tools/server/server-task.h:77). With it false,
# populate_token_probs takes get_token_probabilities over llama_get_logits_ith, with backend sampling off for pre-sample
# logits (server-context.cpp:1923-1927, 2095-2127; server-common.cpp:1594-1625).
OPTIONS = {"num_ctx": 2048, "num_predict": 128, "temperature": 0, "top_k": 1, "seed": 42}
WARMUP_OPTIONS = {**OPTIONS, "num_predict": 16}
TOP_LOGPROBS = 2
NEAR_TIE = 1e-3  # Argon: a divergence passes only where the top two candidates are within this log-probability
PROMPTS = [
    "Explain in three sentences why the sky is blue.",
    "Write a Python function that returns the n-th Fibonacci number iteratively.",
    "List five uses of a hammer, one per line.",
]
WARMUP_PROMPT = "Say hello."
def new_dll():
    """The build's own recorded ggml-cuda.dll hash; the run refuses if the build has not recorded one."""
    try:
        with open(os.path.join(BUILD, "sha256.txt"), encoding="utf-8") as f:
            return next(ln.split()[0] for ln in f if ln.split() and ln.split()[-1] == "ggml-cuda.dll")
    except (OSError, StopIteration):
        raise SystemExit(f"REFUSED: no ggml-cuda.dll hash in {BUILD}\sha256.txt; the build is not assembled")

state = {"peak": 0, "breach": None, "stop": False, "sandbox_pid": None}


def record(kind, **data):
    with open(RECORD, "a", encoding="utf-8") as f:
        f.write(json.dumps({"t": time.strftime("%H:%M:%S"), "kind": kind, **data}) + "\n")
        f.flush()
        os.fsync(f.fileno())


def http(base, path, body=None, timeout=300):
    req = urllib.request.Request(base + path, data=None if body is None else json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def memory_used():
    return int(subprocess.run(["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
                              capture_output=True, text=True, timeout=10).stdout.strip().splitlines()[0])


def kill_sandbox():
    pid = state["sandbox_pid"]
    if pid:
        subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True, timeout=30)


def vram_sampler():
    while not state["stop"]:
        try:
            used = memory_used()
            state["peak"] = max(state["peak"], used)
            if used > CAP_MIB and not state["breach"]:
                state["breach"] = used
                record("BREACH", memory_used_mib=used, cap_mib=CAP_MIB)
                # At once, not after the request in flight: the sandbox tree is killed and 11434 unloaded.
                threading.Thread(target=kill_sandbox, daemon=True).start()
                threading.Thread(target=unload, args=(STOCK,), daemon=True).start()
        except Exception as e:  # a failed read is recorded, never ignored silently
            record("vram_read_error", error=str(e))
        time.sleep(1)


def loaded(base):
    """The models a server has loaded, or None when it does not answer: unreachable is never read as empty."""
    try:
        return [m["name"] for m in http(base, "/api/ps", timeout=10)["models"]]
    except Exception:
        return None


def unload(base):
    try:
        http(base, "/api/generate", {"model": MODEL, "keep_alive": 0}, timeout=60)
    except Exception as e:
        record("unload_error", server=base, error=str(e))
    for _ in range(30):
        if loaded(base) == []:
            return True
        time.sleep(1)
    return False


def check_breach():
    if state["breach"]:
        raise SystemExit(f"STOP: memory.used {state['breach']} MiB passed the {CAP_MIB} MiB cap")


def check_exclusive(base, other, other_may_be_down):
    """Before every generation: the other server answers with nothing loaded (11500 before launch excepted)."""
    other_state = loaded(other)
    if other_state is None and not other_may_be_down:
        raise SystemExit(f"STOP: {other} does not answer, so it cannot be shown empty")
    if other_state:
        raise SystemExit(f"STOP: {other} has a model loaded; never two at once")


def generate(base, prompt, options):
    body = {"model": MODEL, "prompt": prompt, "think": False, "stream": False, "options": options,
            "keep_alive": "30s", "logprobs": True, "top_logprobs": TOP_LOGPROBS}
    return body, http(base, "/api/generate", body)


def run_block(name, base, other, other_may_be_down=False):
    check_exclusive(base, other, other_may_be_down)
    if loaded(base) != []:
        raise SystemExit(f"STOP: {base} is not answering empty before the load")
    # One warm-up after the load, before the timed prompts; it is recorded as having run, its output is not used.
    check_breach()
    body, r = generate(base, WARMUP_PROMPT, WARMUP_OPTIONS)
    record("warmup", block=name, body={k: v for k, v in body.items() if k != "prompt"},
           load_duration_ns=r.get("load_duration"), peak_mib_so_far=state["peak"])
    out = []
    for i, prompt in enumerate(PROMPTS):
        check_breach()
        check_exclusive(base, other, other_may_be_down)
        body, r = generate(base, prompt, OPTIONS)
        record("sent", block=name, prompt=i, body={k: v for k, v in body.items() if k != "prompt"})
        lps = r.get("logprobs") or []
        res = {"block": name, "prompt": i, "response": r.get("response", ""),
               "tokens": [t.get("token") for t in lps],
               "top": [[(c.get("token"), c.get("logprob")) for c in (t.get("top_logprobs") or [])] for t in lps],
               "eval_count": r.get("eval_count"), "eval_duration_ns": r.get("eval_duration"),
               "tok_per_s": round(r["eval_count"] / (r["eval_duration"] / 1e9), 2) if r.get("eval_duration") else None,
               "load_duration_ns": r.get("load_duration"), "prompt_eval_count": r.get("prompt_eval_count"),
               "prompt_eval_duration_ns": r.get("prompt_eval_duration"), "done_reason": r.get("done_reason"),
               "peak_mib_so_far": state["peak"]}
        record("result", **res)
        out.append(res)
    check_breach()
    ok = unload(base)
    record("unloaded", block=name, server=base, empty=ok, peak_mib_so_far=state["peak"])
    if not ok:
        raise SystemExit(f"STOP: {base} did not unload")
    return out


def first_divergence(a, b):
    for i, (x, y) in enumerate(zip(a, b)):
        if x != y:
            return i
    return None if len(a) == len(b) else min(len(a), len(b))


def compare(ref, other):
    """Exact match, or (Argon's rule, made exact) a divergence at a near-tie: at the first differing position i,
    abs(top_a[0].logprob - top_a[1].logprob) < NEAR_TIE AND the other run's token at i is the reference's second
    candidate top_a[1].token. Otherwise it fails. With no top_logprobs at i, the rule is exact match only, and that is
    said."""
    if ref["tokens"] and other["tokens"]:
        unit, a, b = "token", ref["tokens"], other["tokens"]
    else:
        unit, a, b = "character", ref["response"], other["response"]
    i = first_divergence(b, a)
    out = {"unit": unit, "exact": i is None, "first_divergence": i}
    if i is None:
        out["pass"] = True
        return out
    have_top = unit == "token" and i < len(ref["top"]) and len(ref["top"][i]) >= 2
    if not have_top:
        out.update(rule="exact match only (no top_logprobs at the divergence)", **{"pass": False})
        return out
    (t1, l1), (t2, l2) = ref["top"][i][0], ref["top"][i][1]
    chosen = b[i] if i < len(b) else None
    gap = abs(l1 - l2)
    out.update(rule="near-tie", ref_top2=[[t1, l1], [t2, l2]], gap=gap, chosen=chosen,
               **{"pass": gap < NEAR_TIE and chosen == t2})
    return out


def self_check():
    want = open(FROZEN, encoding="utf-8").read().split()[0]
    have = hashlib.sha256(open(os.path.abspath(__file__), "rb").read()).hexdigest()
    if have != want:
        raise SystemExit(f"REFUSED: this script's sha256 {have} is not the frozen {want}")
    return have


def sandbox_env():
    env = dict(os.environ)
    for k in ("CUDA_VISIBLE_DEVICES", "GGML_VK_VISIBLE_DEVICES", "OLLAMA_VULKAN", "OLLAMA_IGPU_ENABLE",
              "OLLAMA_NUM_GPU", "OMP_NUM_THREADS", "OLLAMA_LLM_LIBRARY", "OLLAMA_MODELS"):
        env.pop(k, None)  # the CPU-only switches from the embed work must not reach the GPU sandbox
    # No stock Ollama DLL may resolve from PATH: 13.4's cuBLAS needs cublasLt symbols 13.0 lacks.
    parts = env.get("PATH", "").split(os.pathsep)
    kept = [p for p in parts if "\\programs\\ollama" not in p.lower().replace("/", "\\")]
    env.update(PATH=os.pathsep.join(kept), USERPROFILE=RUN, HOME=RUN, CUDA_VISIBLE_DEVICES="0",
               OLLAMA_HOST="127.0.0.1:11500", OLLAMA_LLM_LIBRARY="cuda_v13", OLLAMA_MODELS=r"E:\AI-Models\Ollama",
               OLLAMA_NOPRUNE="1", OLLAMA_KEEP_ALIVE="30s", OLLAMA_DEBUG="1")
    return env, len(parts) - len(kept)


def log_evidence():
    try:
        text = open(SANDBOX_LOG, encoding="utf-8", errors="replace").read()
    except OSError as e:
        return {"log_error": repr(e)}
    want = os.path.join(RUN, "lib", "ollama", "cuda_v13").lower()
    lines = [ln.strip() for ln in text.splitlines()
             if want in ln.lower() or "compute=12.0" in ln or "library=cuda" in ln.lower()]
    dll = os.path.join(RUN, "lib", "ollama", "cuda_v13", "ggml-cuda.dll")
    return {"path_named": any(want in ln.lower() for ln in lines), "compute_12_0": any("compute=12.0" in ln for ln in lines),
            "library_cuda": any("library=cuda" in ln.lower() for ln in lines), "lines": lines[:12],
            "dll_sha256": hashlib.sha256(open(dll, "rb").read()).hexdigest(),
            "dll_is_new_build": hashlib.sha256(open(dll, "rb").read()).hexdigest() == new_dll()}


def main():
    t0 = time.time()
    script_sha = self_check()
    new_dll()  # refuse before anything starts if the build under test has no recorded DLL hash
    open(RECORD, "w").close()
    baseline = memory_used()
    record("start", script_sha256=script_sha, baseline_mib=baseline, cap_mib=CAP_MIB, model=MODEL, options=OPTIONS)
    threading.Thread(target=vram_sampler, daemon=True).start()
    sandbox = None
    log = None
    results = {}
    try:
        results["A"] = run_block("stock A", STOCK, SANDBOX, other_may_be_down=True)
        results["B"] = run_block("stock B", STOCK, SANDBOX, other_may_be_down=True)
        env, stripped = sandbox_env()
        record("sandbox_env", path_entries_stripped=stripped,
               **{k: env[k] for k in ("OLLAMA_HOST", "OLLAMA_LLM_LIBRARY", "OLLAMA_MODELS", "OLLAMA_NOPRUNE",
                                      "OLLAMA_KEEP_ALIVE", "OLLAMA_DEBUG", "CUDA_VISIBLE_DEVICES", "USERPROFILE", "HOME")})
        log = open(SANDBOX_LOG, "w", encoding="utf-8")
        sandbox = subprocess.Popen([os.path.join(RUN, "ollama.exe"), "serve"], env=env, stdout=log, stderr=log, cwd=RUN)
        state["sandbox_pid"] = sandbox.pid
        record("sandbox_started", pid=sandbox.pid)
        for _ in range(60):
            check_breach()
            try:
                v = http(SANDBOX, "/api/version", timeout=3)
                record("sandbox_up", version=v.get("version"))
                break
            except Exception:
                time.sleep(1)
        else:
            raise SystemExit("STOP: the sandbox server did not come up")
        results["S"] = run_block("sandbox", SANDBOX, STOCK)
    finally:
        cleanup = {}
        for base in (STOCK, SANDBOX):
            try:
                if loaded(base):
                    cleanup[f"unloaded_{base[-5:]}"] = unload(base)
            except Exception as e:
                cleanup[f"unload_error_{base[-5:]}"] = repr(e)
        if sandbox is not None:
            try:
                kill_sandbox()
                sandbox.wait(timeout=30)
            except Exception as e:  # TimeoutExpired included: the checks below still run
                cleanup["sandbox_stop_error"] = repr(e)
        if log is not None:
            try:
                log.close()
            except Exception as e:
                cleanup["log_close_error"] = repr(e)
        time.sleep(3)
        state["stop"] = True
        try:
            cleanup["sandbox_runner_left"] = subprocess.run(
                ["powershell", "-NoProfile", "-Command",
                 "(Get-CimInstance Win32_Process -Filter \"Name='llama-server.exe'\" | "
                 "Where-Object { $_.ExecutablePath -like '*ollama-cu1343-0404*' }).ProcessId"],
                capture_output=True, text=True, timeout=60).stdout.strip() or None
        except Exception as e:
            cleanup["runner_check_error"] = repr(e)
        try:
            cleanup["memory_used_end_mib"] = memory_used()
        except Exception as e:
            cleanup["end_read_error"] = repr(e)
        record("cleanup", stock_ps=loaded(STOCK), sandbox_answering=_answers(SANDBOX), baseline_mib=baseline,
               peak_mib=state["peak"], wall_s=round(time.time() - t0, 1), **cleanup)

    comp = []
    for i in range(len(PROMPTS)):
        a, b, s = results["A"][i], results["B"][i], results["S"][i]
        comp.append({"prompt": i, "S_vs_A": compare(a, s), "B_vs_A": compare(a, b),
                     "tok_per_s": {"A": a["tok_per_s"], "B": b["tok_per_s"], "S": s["tok_per_s"]}})
    ratios = [c["tok_per_s"]["S"] / c["tok_per_s"]["A"] for c in comp if c["tok_per_s"]["A"] and c["tok_per_s"]["S"]]
    verdict = {"criterion_1_dll_loaded": log_evidence(),
               "criterion_2_outputs": all(c["S_vs_A"]["pass"] for c in comp),
               "criterion_3_speed_ratio_mean": round(sum(ratios) / len(ratios), 3) if ratios else None,
               "criterion_3_pass": bool(ratios) and sum(ratios) / len(ratios) >= 0.95}
    record("comparison", prompts=comp, **verdict)
    print(json.dumps({"comparison": comp, **verdict, "peak_mib": state["peak"], "baseline_mib": baseline}, indent=1))


def _answers(base):
    try:
        http(base, "/api/version", timeout=3)
        return True
    except Exception:
        return False


if __name__ == "__main__":
    main()
