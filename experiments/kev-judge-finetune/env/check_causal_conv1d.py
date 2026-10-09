"""causal_conv1d's CUDA kernel against its own PyTorch reference, on the GPU, in Qwen3.5-like shapes.
Run in .venv-cu134 inside a granted slot. Prints one line per case and CC1D-OK or CC1D-FAIL."""
import torch
from causal_conv1d import causal_conv1d_fn
from causal_conv1d.causal_conv1d_interface import causal_conv1d_ref

torch.manual_seed(0)
ok = True
# bf16: the forward is checked in bf16 steps (below); `tol` bounds the backward's relative error.
for dtype, tol in ((torch.float32, 1e-4), (torch.bfloat16, 3e-2)):
    for (b, d, l, w) in ((1, 4096, 2048, 4), (2, 8192, 517, 4), (1, 2048, 1, 4)):
        x = torch.randn(b, d, l, device="cuda", dtype=dtype, requires_grad=True)
        wt = torch.randn(d, w, device="cuda", dtype=dtype, requires_grad=True)
        bias = torch.randn(d, device="cuda", dtype=dtype, requires_grad=True)
        for act in (None, "silu"):
            y = causal_conv1d_fn(x, wt, bias, activation=act)
            r = causal_conv1d_ref(x, wt, bias, activation=act)
            delta = (y.float() - r.float()).abs()
            if dtype == torch.bfloat16:
                # The bf16 reference rounds the conv to bf16 before the activation; the kernel rounds once, at
                # the end. So they can differ by several bf16 steps, most at small SiLU outputs. The test that
                # means something is against float64 truth: the kernel must be no less accurate than the bf16
                # reference. (First run, 2026-10-08, failed a fixed 3e-2 bound: max |Δ| 0.0625, one bf16 step
                # at |ref| 8.25, while against float64 the kernel was as close as the reference or closer.)
                truth = causal_conv1d_ref(x.detach().double(), wt.detach().double(), bias.detach().double(), activation=act)
                k_err = float((y.detach().double() - truth).abs().max())
                r_err = float((r.detach().double() - truth).abs().max())
                fwd_ok, fwd_txt = k_err <= r_err * 1.01, f"fwd vs float64: kernel {k_err:.2e}, bf16 ref {r_err:.2e}"
            else:
                fwd = float(delta.max())
                fwd_ok, fwd_txt = fwd <= tol, f"fwd max|Δ| {fwd:.2e}"
            g1 = torch.autograd.grad(y.float().square().sum(), (x, wt), retain_graph=False)
            g2 = torch.autograd.grad(r.float().square().sum(), (x, wt))
            bwd = max(float((a.float() - c.float()).abs().max() / (c.float().abs().max() + 1e-6)) for a, c in zip(g1, g2))
            good = fwd_ok and bwd <= tol
            ok &= good
            print(f"{str(dtype):15} b{b} d{d} l{l} act={act}: {fwd_txt}, bwd rel {bwd:.2e} {'ok' if good else 'FAIL'}")
print("CC1D-OK" if ok else "CC1D-FAIL")
