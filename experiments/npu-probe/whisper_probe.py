#!/usr/bin/env python3
"""Whisper speech-to-text through OpenVINO GenAI on the NPU vs the CPU — the pre-registered probe
(prereg/whisper-probe.md, 2026-10-09). Measurement only; no decision attached.

Model: openai/whisper-base, revision resolved from the HF API at run time and recorded in the
receipt, exported to OpenVINO with optimum-cli (automatic-speech-recognition), then run with
openvino-genai's WhisperPipeline. English is pinned (language <|en|>, task transcribe); temperature
is set to 0 if the config exposes it, otherwise the default is used and the receipt says so, per
the prereg.

Audio: 8 clips from LibriSpeech dev-clean (CC BY 4.0), staged with their reference transcripts by
a single streaming pass over the archive (flac payloads retained for the lexicographically
smallest 8 ids — deterministic by construction), decoded to 16 kHz mono WAV with ffmpeg, clip
seconds parsed from the flac STREAMINFO header (no decoder needed). WER normalization is lowercase
+ ASCII punctuation stripped; the edit alignment prefers substitution over deletion over insertion
on ties, pinned so receipts cannot drift.

Metrics per clip and device: RTF = wall / clip seconds (median of 3 passes with min-max spread);
WER from the first pass against the reference transcript; WER(NPU vs CPU) as device agreement.
Cold start per device (pipeline build + first clip) is recorded separately. Failures are recorded
outcomes — load_error / garbage with the error text; one retry after rebuilding the pipeline, no
retry loops.

    whisper_probe.py stage --dest E:/AI/rnd-npu-index/librispeech --clips 8
    whisper_probe.py run --export-dir E:/AI/rnd-npu-index/whisper-base-ov \
        --clips-dir E:/AI/rnd-npu-index/librispeech --cache E:/AI-Models/hf-cache \
        --out results/2026-10-09-whisper-probe.json
"""

from __future__ import annotations

import argparse
import array
import gc
import hashlib
import json
import statistics
import string
import subprocess
import sys
import time
import urllib.request
import wave
from pathlib import Path

MODEL_ID = "openai/whisper-base"
ARCHIVE_URL = "https://www.openslr.org/resources/12/dev-clean.tar.gz"
SAMPLE_RATE = 16000
DEFAULT_CLIPS = 8          # the prereg's 5-10; 8 pinned
PASSES = 3
DEVICES = ("CPU", "NPU")   # CPU is the reference leg, first
GARBAGE_WER = 0.9          # first-clip WER above this triggers the one allowed retry


def normalize_text(s: str) -> list:
    """The pinned WER normalization: lowercase, ASCII punctuation characters removed, split on
    whitespace. (Removing punctuation merges hyphenated compounds; the pin keeps it simple.)"""
    return s.lower().translate(str.maketrans("", "", string.punctuation)).split()


def wer_ops(ref: list, hyp: list) -> tuple:
    """(wer, substitutions, deletions, insertions): the standard word-edit alignment, ties broken
    diagonal (match/substitution), then deletion, then insertion. wer is None for an empty ref."""
    n, m = len(ref), len(hyp)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for x in range(1, n + 1):
        dp[x][0] = x
    for y in range(1, m + 1):
        dp[0][y] = y
    for x in range(1, n + 1):
        for y in range(1, m + 1):
            dp[x][y] = min(dp[x - 1][y] + 1, dp[x][y - 1] + 1,
                           dp[x - 1][y - 1] + (ref[x - 1] != hyp[y - 1]))
    s = d = i = 0
    x, y = n, m
    while x > 0 or y > 0:
        if x > 0 and y > 0 and dp[x][y] == dp[x - 1][y - 1] + (ref[x - 1] != hyp[y - 1]):
            if ref[x - 1] != hyp[y - 1]:
                s += 1
            x -= 1
            y -= 1
        elif x > 0 and dp[x][y] == dp[x - 1][y] + 1:
            d += 1
            x -= 1
        else:
            i += 1
            y -= 1
    return ((s + d + i) / n if n else None), s, d, i


def flac_duration(path) -> float:
    """Seconds from the STREAMINFO block: total_samples / sample_rate. No decoder needed."""
    with open(path, "rb") as f:
        head = f.read(26)
    if head[:4] != b"fLaC":
        raise ValueError(f"{path}: not a flac file")
    if head[4] & 0x7F != 0:
        raise ValueError(f"{path}: first metadata block is not STREAMINFO")
    packed = int.from_bytes(head[18:26], "big")
    rate = (packed >> 44) & 0xFFFFF
    total = packed & 0xFFFFFFFFF
    if not rate or not total:
        raise ValueError(f"{path}: STREAMINFO lacks sample rate or total samples")
    return total / rate


def wav_floats(path) -> list:
    """16-bit PCM mono WAV -> float samples in [-1, 1), stdlib only."""
    with wave.open(str(path), "rb") as w:
        if (w.getframerate(), w.getnchannels(), w.getsampwidth()) != (SAMPLE_RATE, 1, 2):
            raise SystemExit(f"{path}: expected {SAMPLE_RATE} Hz mono s16 wav, got "
                             f"{w.getframerate()} Hz, {w.getnchannels()} ch, {w.getsampwidth() * 8}-bit")
        raw = w.readframes(w.getnframes())
    pcm = array.array("h")
    pcm.frombytes(raw)
    if sys.byteorder == "big":
        pcm.byteswap()
    return [s / 32768.0 for s in pcm]


def parse_transcript(payload: str) -> dict:
    """LibriSpeech .trans.txt lines: "<clip-id> <WORDS AND WORDS>" -> {id: words}."""
    out = {}
    for line in payload.splitlines():
        line = line.strip()
        if not line:
            continue
        cid, _, words = line.partition(" ")
        out[cid] = words
    return out


def retain(retained: dict, clip_id: str, payload: bytes, n: int) -> None:
    """Single-pass deterministic selection: keep the n smallest ids seen so far."""
    retained[clip_id] = payload
    while len(retained) > n:
        retained.pop(max(retained))


def stage(url: str, dest: Path, n: int) -> dict:
    """One streaming pass over the dev-clean archive: every .trans.txt text is collected, flac
    payloads retained only while an id is among the n smallest seen. Files and manifest.json are
    written under dest; the archive's sha256 is computed as it streams by."""
    import tarfile
    dest.mkdir(parents=True, exist_ok=True)
    transcripts, flacs = {}, {}
    digest = hashlib.sha256()

    class HashingReader:
        def __init__(self, raw):
            self.raw = raw
        def read(self, size=-1):
            b = self.raw.read(size)
            digest.update(b)
            return b

    with urllib.request.urlopen(url, timeout=120) as r, \
            tarfile.open(fileobj=HashingReader(r), mode="r:gz") as tar:
        for member in tar:
            name = Path(member.name).name
            if name.endswith(".trans.txt"):
                text = tar.extractfile(member).read().decode("utf-8")
                for cid, words in parse_transcript(text).items():
                    transcripts.setdefault(cid, words)
            elif member.name.endswith(".flac"):
                cid = Path(member.name).stem
                retain(flacs, cid, tar.extractfile(member).read(), n)
    candidates = sorted(set(flacs) & set(transcripts))[:n]
    missing = [c for c in candidates if c not in flacs or c not in transcripts]
    if len(candidates) < n or missing:
        raise SystemExit(f"archive scan could not cover {n} clips (have {len(flacs)} flacs, "
                         f"{len(transcripts)} transcripts); the selection rule is off-deterministic")
    clips = []
    for cid in candidates:
        flac_path = dest / f"{cid}.flac"
        flac_path.write_bytes(flacs[cid])
        wav_path = dest / f"{cid}.wav"
        ffmpeg_to_wav(flac_path, wav_path)
        clips.append({"id": cid, "flac": flac_path.name, "wav": wav_path.name,
                      "transcript": transcripts[cid],
                      "duration_s": round(flac_duration(flac_path), 3)})
    manifest = {"archive": url, "archive_sha256": digest.hexdigest(), "clips": clips,
                "selector": f"first {n} clip ids in sorted order (flac payload retained streaming)"}
    (dest / "manifest.json").write_text(json.dumps(manifest, indent=1) + "\n", encoding="utf-8")
    return manifest


def ffmpeg_to_wav(src: Path, dst: Path) -> None:
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(src),
           "-ac", "1", "-ar", str(SAMPLE_RATE), "-acodec", "pcm_s16le", str(dst)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode or not dst.exists():
        raise SystemExit(f"ffmpeg failed on {src}: {r.stderr.strip()[:400]}")


def hf_revision(model: str) -> str:
    """The run-time resolve the prereg pins, read off the HF model API."""
    with urllib.request.urlopen(f"https://huggingface.co/api/models/{model}", timeout=30) as r:
        return json.loads(r.read())["sha"]


def export_model(export_dir: Path, revision: str, cache: Path) -> dict:
    """optimum-cli export openvino for whisper; reused when the encoder IR is already there."""
    encoder = export_dir / "openvino_encoder_model.xml"
    if encoder.exists():
        return {"reused": True, "seconds": None, "export_dir": str(export_dir)}
    export_dir.mkdir(parents=True, exist_ok=True)
    cmd = [sys.executable, "-m", "optimum.commands.optimum_cli", "export", "openvino",
           "--model", MODEL_ID, "--revision", revision, "--task", "automatic-speech-recognition",
           "--cache_dir", str(cache), str(export_dir)]
    t0 = time.perf_counter()
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode or not encoder.exists():
        raise SystemExit(f"optimum-cli export failed ({r.returncode}): "
                         f"{(r.stderr or r.stdout).strip()[:600]}")
    return {"reused": False, "seconds": round(time.perf_counter() - t0, 1),
            "export_dir": str(export_dir)}


def build_pipeline_with_retry(export_dir: Path, device: str):
    """(pipeline, meta): load_error is a recorded outcome; one retry after gc, no loops."""
    import openvino_genai as ov_genai
    attempts, err, pipe, build_seconds = 0, None, None, None
    while attempts < 2:
        attempts += 1
        try:
            t0 = time.perf_counter()
            pipe = ov_genai.WhisperPipeline(str(export_dir), device)
            build_seconds = round(time.perf_counter() - t0, 1)
            err = None
            break
        except Exception as e:  # noqa: BLE001 -- the failure text is the finding
            err = f"{type(e).__name__}: {str(e)[:600]}"
            pipe = None
            gc.collect()
    return pipe, {"attempts": attempts, "build_seconds": build_seconds, "load_error": err}


def configure(pipe) -> dict:
    """Pin English transcription, temperature 0 when the config exposes it; the receipt records
    exactly what the installed GenAI lets us set, per the prereg's allowance."""
    cfg = pipe.get_generation_config()
    report = {"has_temperature": hasattr(cfg, "temperature")}
    for name, want in (("language", "<|en|>"), ("task", "transcribe"), ("return_timestamps", False)):
        if hasattr(cfg, name):
            setattr(cfg, name, want)
            report[name] = want
    if report["has_temperature"]:
        cfg.temperature = 0.0
        report["temperature"] = 0.0
    pipe.set_generation_config(cfg)
    return report


def transcribe(pipe, samples: list) -> str:
    out = pipe.generate(samples)
    texts = getattr(out, "texts", None)
    if not texts or not texts[0].strip():
        raise ValueError("empty transcript from WhisperPipeline.generate")
    return texts[0].strip()


def rtf_stats(rows: list) -> dict:
    """rows: per-clip {median, per-pass rtfs}. Device summary: median with min-max over clips."""
    meds = sorted(r["median"] for r in rows)
    return {"clips": len(rows), "median_rtf": round(statistics.median(meds), 3) if rows else None,
            "min_rtf": meds[0] if rows else None, "max_rtf": meds[-1] if rows else None}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="mode", required=True)
    sp = sub.add_parser("stage", help="download + decode the pinned LibriSpeech clips")
    sp.add_argument("--dest", type=Path, required=True)
    sp.add_argument("--clips", type=int, default=DEFAULT_CLIPS)
    sp.add_argument("--url", default=ARCHIVE_URL)
    rp = sub.add_parser("run", help="the probe itself (needs the NPU window for its NPU leg)")
    rp.add_argument("--export-dir", type=Path, required=True)
    rp.add_argument("--clips-dir", type=Path, required=True)
    rp.add_argument("--cache", type=Path, required=True, help="HF cache dir for the model download")
    rp.add_argument("--out", type=Path, required=True)
    rp.add_argument("--limit", type=int, default=None, help="first N clips only; marks smoke")
    a = ap.parse_args()

    if a.mode == "stage":
        manifest = stage(a.url, a.dest, a.clips)
        print(f"staged {len(manifest['clips'])} clips under {a.dest}")
        return

    process_start = time.time()
    t0_wall = time.perf_counter()
    manifest = json.loads((a.clips_dir / "manifest.json").read_text(encoding="utf-8"))
    clips = manifest["clips"][:a.limit] if a.limit else manifest["clips"]
    samples = {}
    for c in clips:
        wav = a.clips_dir / c["wav"]
        if not wav.exists():
            ffmpeg_to_wav(a.clips_dir / c["flac"], wav)
        samples[c["id"]] = wav_floats(wav)

    revision = hf_revision(MODEL_ID)
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from siglip2_probe import hub_cache  # one normalizer, shared
    export = export_model(a.export_dir, revision, hub_cache(a.cache))
    import importlib.metadata as im
    genai_version = im.version("openvino-genai")

    pipes, dev_report = {}, {}
    for dev in DEVICES:
        pipe, meta = build_pipeline_with_retry(a.export_dir, dev)
        dev_report[dev] = dict(meta)
        if pipe is not None:
            dev_report[dev]["config"] = configure(pipe)
            pipes[dev] = pipe
    if "CPU" not in pipes:
        raise SystemExit("the CPU reference pipeline failed to build; aborting before any timing")

    pass_texts = {d: {} for d in pipes}          # first pass only: clip id -> transcript
    per_clip = {d: {} for d in pipes}            # clip id -> {"rtfs": [...], "errors": [...]}
    cold = {}
    for p in range(PASSES):
        for dev in DEVICES:
            if dev not in pipes:
                continue
            for c in clips:
                row = per_clip[dev].setdefault(c["id"], {"rtfs": [], "errors": []})
                try:
                    t0 = time.perf_counter()
                    text = transcribe(pipes[dev], samples[c["id"]])
                except Exception as e:  # noqa: BLE001 -- per-clip failures are findings
                    row["errors"].append(f"pass {p}: {type(e).__name__}: {str(e)[:300]}")
                    continue
                row["rtfs"].append(round((time.perf_counter() - t0) / c["duration_s"], 4))
                if p == 0:
                    pass_texts[dev][c["id"]] = text
                    if dev not in cold:
                        cold[dev] = round(dev_report[dev]["build_seconds"]
                                          + (time.perf_counter() - t0), 1)
        print(f"pass {p + 1}/{PASSES} done", flush=True)

    for dev, meta in list(dev_report.items()):
        if dev not in pipes:
            continue
        # The one allowed retry if the first NPU/CPU clip came back garbage (> 0.9 WER).
        first = clips[0]["id"]
        ref = normalize_text(clips[0]["transcript"])
        if first in pass_texts[dev]:
            w = wer_ops(ref, normalize_text(pass_texts[dev][first]))[0]
            if w is not None and w > GARBAGE_WER and meta["attempts"] < 2:
                pipes[dev] = None
                gc.collect()
                pipe, extra = build_pipeline_with_retry(a.export_dir, dev)
                if pipe is not None:
                    text2 = transcribe(pipe, samples[clips[0]["id"]])
                    meta["garbage_retry"] = {"first_wer": round(w, 4),
                                             "after_retry_wer": round(
                                                 wer_ops(ref, normalize_text(text2))[0], 4)}
                    if meta["garbage_retry"]["after_retry_wer"] <= GARBAGE_WER:
                        pipes[dev] = pipe
                        pass_texts[dev][first] = text2
                    else:
                        meta["status"] = "garbage after retry"
                meta["attempts"] += extra["attempts"] - 1  # cumulative count, one retry max

    for dev in pipes:
        rows = []
        for c in clips:
            row = per_clip[dev].get(c["id"], {"rtfs": [], "errors": []})
            if not row["rtfs"]:
                continue
            r = row["rtfs"]
            rows.append({"id": c["id"], "rtfs": r, "median": round(statistics.median(r), 4),
                         **({"errors": row["errors"]} if row["errors"] else {})})
        dev_report[dev]["cold_start_seconds"] = cold.get(dev)
        dev_report[dev]["rtf"] = rtf_stats(rows)
        ref = [normalize_text(c["transcript"]) for c in clips]
        hyp = [pass_texts[dev].get(c["id"], "") for c in clips]
        dev_report[dev]["wer_vs_reference"] = [
            {"id": c["id"], "wer": (None if not h else round(wer_ops(r0, normalize_text(h))[0], 4))}
            for c, r0, h in zip(clips, ref, hyp)]
        dev_report[dev]["per_clip"] = rows

    agreement = []
    if "NPU" in pass_texts and "CPU" in pass_texts:
        for c in clips:
            cid = c["id"]
            if pass_texts["NPU"].get(cid) and pass_texts["CPU"].get(cid):
                w = wer_ops(normalize_text(pass_texts["CPU"][cid]),
                            normalize_text(pass_texts["NPU"][cid]))[0]
                agreement.append({"id": cid, "wer": round(w, 4)})

    receipt = {"date": time.strftime("%Y-%m-%d"),
               "kind": "npu-probe: Whisper speech-to-text, NPU vs CPU (measurement only)",
               "prereg": "experiments/npu-probe/prereg/whisper-probe.md",
               "smoke": a.limit is not None, "limit": a.limit,
               "model": {"id": MODEL_ID, "revision_sha": revision, "export": export,
                         "export_cli": "optimum-cli export openvino --task automatic-speech-recognition"},
               "openvino_genai": genai_version,
               "clips": {"archive": manifest["archive"],
                         "archive_sha256": manifest["archive_sha256"],
                         "n": len(clips), "ids": [c["id"] for c in clips],
                         "durations_s": {c["id"]: c["duration_s"] for c in clips}},
               "passes": PASSES, "devices": dev_report,
               "wer_npu_vs_cpu": {"note": "device agreement, not truth", "clips": agreement},
               "wall_seconds_total": round(time.perf_counter() - t0_wall, 1)}
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(receipt, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {a.out}")
    for dev in DEVICES:
        d = dev_report.get(dev, {})
        r = d.get("rtf") or {}
        if r.get("median_rtf") is not None:
            print(f"{dev:4s} median RTF {r['median_rtf']} ({r['min_rtf']}-{r['max_rtf']}), "
                  f"cold start {d.get('cold_start_seconds')}s", flush=True)
        else:
            print(f"{dev:4s} no timing: {d.get('load_error')}", flush=True)


if __name__ == "__main__":
    main()
