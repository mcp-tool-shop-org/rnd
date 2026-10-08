"""Does the studio's CUDA 13.4 PyTorch nightly work on a CUDA 13.0 host (RunPod's newest)?

CUDA's minor-version compatibility says a 13.x build runs on any 13 driver, except JIT of newer PTX
and features that need a newer driver. Triton compiles kernels at run time, so it is the part most
likely to break. Each check runs on its own and records pass or fail with the error; one JSON report
goes to stdout. No downloads: the training check builds a small model from a config.
"""

from __future__ import annotations

import json
import subprocess
import time
import traceback


def check(name, fn, out):
    t = time.perf_counter()
    try:
        detail = fn()
        out[name] = {"ok": True, "s": round(time.perf_counter() - t, 3), **(detail or {})}
    except Exception as e:  # the failure is the finding
        out[name] = {
            "ok": False,
            "s": round(time.perf_counter() - t, 3),
            "error": f"{type(e).__name__}: {str(e)[:600]}",
            "trace": traceback.format_exc()[-1500:],
        }


def main() -> None:
    import torch

    out: dict = {}
    smi = subprocess.run(
        ["nvidia-smi", "--query-gpu=name,driver_version,compute_cap,memory.total", "--format=csv,noheader"],
        capture_output=True,
        text=True,
    ).stdout.strip()
    head = subprocess.run(["nvidia-smi"], capture_output=True, text=True).stdout
    host_cuda = next((ln.split("CUDA Version:")[1].split()[0] for ln in head.splitlines() if "CUDA Version:" in ln), None)
    out["env"] = {
        "torch": torch.__version__,
        "torch_cuda": torch.version.cuda,
        "cudnn": torch.backends.cudnn.version(),
        "gpu": smi,
        "host_cuda": host_cuda,
    }
    dev = "cuda"

    def basic():
        x = torch.arange(10, device=dev, dtype=torch.float32)
        assert float(x.sum()) == 45.0
        return {"device": torch.cuda.get_device_name(0), "capability": list(torch.cuda.get_device_capability(0))}

    def matmul():
        g = torch.Generator().manual_seed(0)
        a = torch.randn(1024, 1024, generator=g, dtype=torch.float64)
        b = torch.randn(1024, 1024, generator=g, dtype=torch.float64)
        ref = a @ b
        res = {}
        for dt, tol in ((torch.float32, 1e-3), (torch.bfloat16, 3e-2)):
            torch.backends.cuda.matmul.allow_tf32 = False
            got = (a.to(dev, dt) @ b.to(dev, dt)).double().cpu()
            rel = float((got - ref).norm() / ref.norm())
            assert rel < tol, f"{dt} relative error {rel}"
            res[str(dt)] = rel
        return {"rel_err": res}

    def cudnn_conv():
        conv = torch.nn.Conv2d(16, 32, 3, padding=1).to(dev)
        x = torch.randn(8, 16, 64, 64, device=dev, requires_grad=True)
        y = conv(x)
        y.square().mean().backward()
        ref = torch.nn.functional.conv2d(x.detach().cpu(), conv.weight.detach().cpu(), conv.bias.detach().cpu(), padding=1)
        err = float((y.detach().cpu() - ref).abs().max())
        assert err < 1e-2, err
        return {"max_abs_err": err, "grad_finite": bool(torch.isfinite(x.grad).all())}

    def sdpa():
        from torch.nn.attention import SDPBackend, sdpa_kernel

        q, k, v = (torch.randn(4, 8, 512, 64, device=dev, dtype=torch.bfloat16, requires_grad=True) for _ in range(3))
        with sdpa_kernel([SDPBackend.FLASH_ATTENTION]):
            o = torch.nn.functional.scaled_dot_product_attention(q, k, v, is_causal=True)
        o.float().square().mean().backward()
        ref = torch.nn.functional.scaled_dot_product_attention(q.float(), k.float(), v.float(), is_causal=True)
        err = float((o.float() - ref).abs().max())
        assert err < 5e-2, err
        return {"backend": "flash", "max_abs_err": err}

    def triton_raw():
        import triton
        import triton.language as tl

        @triton.jit
        def add(x_ptr, y_ptr, o_ptr, n, BLOCK: tl.constexpr):
            i = tl.program_id(0) * BLOCK + tl.arange(0, BLOCK)
            m = i < n
            tl.store(o_ptr + i, tl.load(x_ptr + i, mask=m) + tl.load(y_ptr + i, mask=m), mask=m)

        n = 100_000
        x, y = torch.rand(n, device=dev), torch.rand(n, device=dev)
        o = torch.empty_like(x)
        add[(triton.cdiv(n, 1024),)](x, y, o, n, BLOCK=1024)
        assert torch.allclose(o, x + y)
        return {"triton": triton.__version__}

    def compile_train():
        net = torch.nn.Sequential(torch.nn.Linear(512, 1024), torch.nn.GELU(), torch.nn.Linear(1024, 1)).to(dev)
        opt = torch.optim.AdamW(net.parameters(), lr=1e-3)
        f = torch.compile(net)
        x = torch.randn(64, 512, device=dev)
        t = time.perf_counter()
        for _ in range(5):
            loss = f(x).square().mean()
            opt.zero_grad()
            loss.backward()
            opt.step()
        torch.cuda.synchronize()
        assert torch.isfinite(loss)
        return {"first_5_steps_s": round(time.perf_counter() - t, 2), "loss": float(loss)}

    def reduce_overhead():
        net = torch.nn.Sequential(torch.nn.Linear(512, 256), torch.nn.ReLU(), torch.nn.Linear(256, 1)).to(dev).eval()
        x = torch.randn(16, 512, device=dev)
        torch._dynamo.reset()
        f = torch.compile(net, mode="reduce-overhead")
        with torch.no_grad():
            for _ in range(4):
                y = f(x)
            err = float((y - net(x)).abs().max())
        assert err < 1e-4, err
        return {"max_abs_err": err}

    def cuda_graph():
        lin = torch.nn.Linear(256, 256).to(dev)
        static = torch.randn(32, 256, device=dev)
        s = torch.cuda.Stream()
        s.wait_stream(torch.cuda.current_stream())
        with torch.cuda.stream(s), torch.no_grad():
            for _ in range(3):
                lin(static)
        torch.cuda.current_stream().wait_stream(s)
        g = torch.cuda.CUDAGraph()
        with torch.no_grad(), torch.cuda.graph(g):
            out_ = lin(static)
        new = torch.randn(32, 256, device=dev)
        static.copy_(new)
        g.replay()
        with torch.no_grad():
            err = float((out_ - lin(new)).abs().max())
        assert err < 1e-5, err
        return {"max_abs_err": err}

    def lora_train():
        import peft
        import transformers
        from transformers import LlamaConfig, LlamaForCausalLM

        torch.manual_seed(0)
        cfg = LlamaConfig(
            vocab_size=2048, hidden_size=256, intermediate_size=704, num_hidden_layers=4,
            num_attention_heads=8, num_key_value_heads=4, max_position_embeddings=512,
        )
        model = LlamaForCausalLM(cfg).to(dev, torch.bfloat16)
        model = peft.get_peft_model(model, peft.LoraConfig(r=8, lora_alpha=16, target_modules=["q_proj", "v_proj"]))
        opt = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=5e-3)
        # A learnable task: a fixed repeating sequence, so the loss must fall.
        ids = torch.arange(256, device=dev).repeat(8, 1) % 97
        losses, norms = [], []
        for _ in range(30):
            outp = model(input_ids=ids, labels=ids)
            opt.zero_grad()
            outp.loss.backward()
            norms.append(float(torch.nn.utils.clip_grad_norm_(model.parameters(), 1e9)))
            opt.step()
            losses.append(float(outp.loss))
        assert all(map(lambda v: v == v and abs(v) != float("inf"), losses)), "non-finite loss"
        assert min(norms) > 0, "zero grad norm"
        assert losses[-1] < losses[0] * 0.8, f"loss did not fall: {losses[0]} -> {losses[-1]}"
        return {
            "transformers": transformers.__version__,
            "peft": peft.__version__,
            "loss_first": losses[0],
            "loss_last": losses[-1],
            "grad_norm_mean": sum(norms) / len(norms),
            "peak_gb": round(torch.cuda.max_memory_allocated() / 1e9, 3),
        }

    for name, fn in (
        ("basic", basic),
        ("matmul", matmul),
        ("cudnn_conv", cudnn_conv),
        ("sdpa_flash", sdpa),
        ("triton_raw", triton_raw),
        ("compile_train", compile_train),
        ("compile_reduce_overhead", reduce_overhead),
        ("cuda_graph", cuda_graph),
        ("lora_train", lora_train),
    ):
        check(name, fn, out)
    out["all_ok"] = all(v.get("ok") for k, v in out.items() if k != "env")
    print("PROBE-JSON " + json.dumps(out))


if __name__ == "__main__":
    main()
