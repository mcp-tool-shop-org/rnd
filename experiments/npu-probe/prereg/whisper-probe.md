# Probe: Whisper speech-to-text through OpenVINO GenAI on the NPU

Pre-registered 2026-10-09, before any audio runs. Measurement only — **no decision is attached** (the
handoff: mark it "hypothesis tested", not "studio-ready"). The point: transcription is a plausible
always-on studio workload; the probe prices the NPU against the CPU for it.

## Pinned

- **Model:** `openai/whisper-base` (English, 74M; small enough that the NPU stands a chance), revision
  pinned at run time from the HF resolve API and recorded in the receipt. Through **OpenVINO GenAI**
  (`openvino-genai` 2026.4.1.0, the venv's OpenVINO train), `WhisperPipeline`, on NPU. Reference: the
  same weights on the same pipeline on CPU.
- **Audio:** 5–10 short English clips from **LibriSpeech** (`dev-clean`, flac, fetched from
  `https://www.openslr.org/` over HTTP, CC BY 4.0), staged read-only under `E:/AI/rnd-npu-index/` with
  their reference transcripts. The clip list (speaker/chapter/clip ids) is recorded in the receipt.
- **Metrics per clip and device:** real-time factor (RTF = wall / clip seconds); word error rate (WER)
  of each device's transcript against the clip's reference transcript (lowercased, punctuation stripped —
  the normalisation function lives in the runner and its unit test). Also reported: WER of the NPU
  transcript against the CPU transcript (device agreement, not truth), first-clip load included
  separately as cold start.
- **Runs:** each clip once per device, CPU first as the reference, three full passes interleaved by
  device (CPU, NPU, CPU, NPU, …); RTF reported as median over passes with min–max spread; WER from the
  first pass (transcripts are deterministic at temperature 0 — if GenAI doesn't expose temperature for
  Whisper, say so in the receipt and use its default).

## Rules

- The NPU leg only inside a Publisher-logged window announced via Mike. The CPU leg is minutes at most;
  if the Publisher prefers it outside the NPU window, it reruns there — the prereg doesn't care, the
  receipt says which.
- If `WhisperPipeline` on NPU fails to load or produce English text (a known-hard device path), that is
  a recorded outcome — `load_error` / `garbage output` with the error text in the receipt — not a
  retried-until-it-works session. One retry after a device reset is allowed and recorded.
- Downloads: LibriSpeech only, over plain HTTPS from openslr.org; the venv gains `openvino-genai` (a
  venv-only change, inside the handoff's rule). Nothing else new.
- Receipt: `results/2026-10-09-whisper-probe.json` (date at run); the README section reads only from it.

## Amendments

(none yet — any change after the first clip runs lands here with its date and reason)
