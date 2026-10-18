# Window 13f: Qwen3.8 prebuild on CPU, not byte-matched

**Finding (an inference from the recorded pip freezes; unverified):** the torch build changes GGUF bytes.
- The same BF16 → Q8_0 conversion, at the same revision (1d4bf0f2), llama.cpp commit (620d2225) and transformers
  (4.57.6), gave `6beabf07…` here and the pinned `2ab268e0…` on window 12f's A100. The file size was identical.
- The only material difference in the converter's environment is torch: `2.11.0+cpu` on the CPU image, against
  `2.11.0+cu130` preinstalled on the A100 image. Qwen3.8 has no `env` in pin_window.MODELS, so it converts with the
  image's system python and inherits the image's torch.
- The control: Muse, with its own venv, has `2.11.0+cpu` on both hosts and byte-matches across them (12h's A100 and
  13e's CPU). The same is expected for Gemma (own venv).
- Under the rule "byte-match or don't host", nothing was uploaded, and the prebuild chain stopped here.

**Ruling (R&D):** Qwen3.8 and Granite, whose pins were made with the system python on the A100, are prebuilt on an
A100. Gemma is prebuilt on CPU.

**Follow-up measurement (after W-A, CPU at 0.26/hr):** install torch `2.11.0+cu130` in a venv on a CPU VM and convert
Qwen3.8 there. If the result is `2ab268e0`, the inference is confirmed.
