"""whisper_probe's pure parts: the pinned WER normalization, the word-edit alignment with its tie
policy, the flac STREAMINFO duration parse, the s16 WAV decode, the transcript parser, the
deterministic streaming clip retention, and the RTF summary. Pure stdlib; no audio, no models."""

import struct
import sys
import tempfile
import unittest
import wave
from pathlib import Path

PROBE = Path(__file__).resolve().parent.parent / "experiments" / "npu-probe"
sys.path.insert(0, str(PROBE))
import whisper_probe as wp


class Normalization(unittest.TestCase):
    def test_normalize_text(self):
        self.assertEqual(wp.normalize_text("It's a Test-Case, OK!"),
                         ["its", "a", "testcase", "ok"])
        self.assertEqual(wp.normalize_text("  "), [])

    def test_wer_ops_known_alignment(self):
        wer, s, d, i = wp.wer_ops("the cat sat on".split(), "the cats sat".split())
        self.assertEqual((wer, s, d, i), (0.5, 1, 1, 0))

    def test_wer_ops_insertions_and_identity(self):
        wer, s, d, i = wp.wer_ops(["a", "b"], ["a", "b", "c"])
        self.assertEqual((wer, s, d, i), (0.5, 0, 0, 1))
        self.assertEqual(wp.wer_ops(["a"], ["a"]), (0.0, 0, 0, 0))

    def test_wer_ops_empty_reference(self):
        wer, s, d, i = wp.wer_ops([], ["ghost", "words"])
        self.assertEqual((wer, s, d, i), (None, 0, 0, 2))


def fake_flac(path: Path, rate: int, total: int, block_type: int = 0) -> None:
    packed = (rate << 44) | (0 << 41) | (15 << 36) | total  # ch-1=0 (mono), bps-1=15 (16-bit)
    body = b"\x00" * 10 + packed.to_bytes(8, "big") + b"\x00" * 2  # STREAMINFO (34 B)
    header = b"fLaC" + bytes([block_type]) + (34).to_bytes(3, "big") + body
    path.write_bytes(header)


class Audio(unittest.TestCase):
    def test_flac_duration_from_streaminfo(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "c.flac"
            fake_flac(p, 16000, 48000)
            self.assertAlmostEqual(wp.flac_duration(p), 3.0)

    def test_flac_duration_rejects_non_flac_and_non_streaminfo_first(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "x.flac"
            p.write_bytes(b"not a flac at all, really")
            with self.assertRaises(ValueError):
                wp.flac_duration(p)
            q = Path(td) / "y.flac"
            fake_flac(q, 16000, 48000, block_type=1)
            with self.assertRaises(ValueError):
                wp.flac_duration(q)

    def test_wav_floats_round_trip_and_shape_guard(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "a.wav"
            with wave.open(str(p), "wb") as w:
                w.setnchannels(1)
                w.setsampwidth(2)
                w.setframerate(16000)
                w.writeframes(struct.pack("<hhh", -32768, 0, 16384))
            self.assertEqual(wp.wav_floats(p), [-1.0, 0.0, 0.5])
            q = Path(td) / "b.wav"
            with wave.open(str(q), "wb") as w:
                w.setnchannels(1)
                w.setsampwidth(2)
                w.setframerate(8000)
                w.writeframes(struct.pack("<h", 0))
            with self.assertRaises(SystemExit):
                wp.wav_floats(q)


class StagingLogic(unittest.TestCase):
    def test_parse_transcript(self):
        got = wp.parse_transcript("84-121123-0000 THE COLD AIR\n\n"
                                  "84-121123-0001 THEY WERE KIND\n")
        self.assertEqual(got, {"84-121123-0000": "THE COLD AIR",
                               "84-121123-0001": "THEY WERE KIND"})

    def test_retain_keeps_the_n_smallest_streaming(self):
        import random
        ids = [f"84-1211{i:02d}-{j:04d}" for i in range(30) for j in range(3)]
        random.Random(3).shuffle(ids)
        retained = {}
        for cid in ids:
            wp.retain(retained, cid, cid.encode(), 3)
        self.assertEqual(sorted(retained), sorted(ids)[:3])
        self.assertEqual(retained[sorted(ids)[0]], sorted(ids)[0].encode())

    def test_rtf_stats(self):
        rows = [{"median": 0.2}, {"median": 0.4}, {"median": 0.9}]
        self.assertEqual(wp.rtf_stats(rows),
                         {"clips": 3, "median_rtf": 0.4, "min_rtf": 0.2, "max_rtf": 0.9})


if __name__ == "__main__":
    unittest.main()
