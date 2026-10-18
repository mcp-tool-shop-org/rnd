"""The dataminer's thinking count (2026-10-17): before the fix it came back null for every reply cut off at the length
limit and for every reply from a harmony-style template, and the summaries summed null as 0."""

import json
import tempfile
import unittest
from pathlib import Path

from mcptoolshop_rnd.localbuilders import proxy
from mcptoolshop_rnd.localbuilders.recount import recount

GEMMA = json.loads((Path(__file__).parent / "fixtures" / "gemma-4-w0-call-redacted.json").read_text(encoding="utf-8"))
FIXTURE = json.loads((Path(__file__).parent / "fixtures" / "muse-glimmer-w0-call-redacted.json").read_text(encoding="utf-8"))


def _reply(content: str, reasoning: str, finish: str, usage: dict | None = None) -> dict:
    return {"usage": usage or {"completion_tokens": 50}, "timings": {},
            "choices": [{"finish_reason": finish, "message": {"content": content, "reasoning_content": reasoning}}]}


class ThinkingCountTests(unittest.TestCase):
    def test_a_reply_cut_off_at_the_limit_with_no_answer_is_all_thinking(self):
        resp = _reply("", "the plan goes on and on", "length")
        self.assertEqual(proxy._thinking_count(resp, ["t"] * 48, "the plan goes on and on", 50), (50, "length"))
        _, n, words, _ = proxy._count_tokens(resp, ["t"] * 48, "the plan goes on and on")
        self.assertEqual((n, words), (50, None))

    def test_a_cut_off_reply_that_had_started_its_answer_stays_unknown(self):
        resp = _reply("{\"partial\":", "thinking", "length")
        self.assertEqual(proxy._thinking_count(resp, ["t"] * 48, "thinking", 50), (None, None))

    def test_a_muse_reply_counts_its_thinking_to_the_channel_end(self):
        f = FIXTURE
        self.assertIsNone(f["thinking_tokens_recorded"])  # what window 12d's proxy wrote
        n, source = proxy._thinking_count(f["upstream_response"], f["tokens"], f["reasoning_content"], f["output_tokens"])
        self.assertEqual(source, "marker")
        self.assertEqual(n, f["tokens"].index("<|eom|>") + 1)
        self.assertLess(n, f["output_tokens"])

    def test_a_normal_reply_keeps_its_count(self):
        toks = ["a", "b", "</think>", "x"]
        resp = _reply("x", "ab", "stop")
        self.assertEqual(proxy._thinking_count(resp, toks, "ab", 4), (3, "marker"))
        usage = {"completion_tokens": 9, "completion_tokens_details": {"reasoning_tokens": 7}}
        self.assertEqual(proxy._thinking_count(_reply("x", "ab", "stop", usage), toks, "ab", 9), (7, "usage"))
        self.assertEqual(proxy._thinking_count(_reply("x", "", "stop"), ["x"], None, 1), (0, "none"))
        # A harmony end token in a reply with no reasoning isn't read as thinking.
        self.assertEqual(proxy._thinking_count(_reply("x", "", "stop"), ["x", "<|end|>"], None, 2), (0, "none"))

    def test_a_gemma_reply_counts_its_thinking_to_the_channel_close(self):
        g = GEMMA
        self.assertIsNone(g["thinking_tokens_recorded"])  # what window 12f's proxy wrote
        n, source = proxy._thinking_count(g["upstream_response"], g["tokens"], g["reasoning_content"], g["output_tokens"])
        self.assertEqual((n, source), (g["tokens"].index("<channel|>") + 1, "marker"))
        self.assertLess(n, g["output_tokens"])
        resp = _reply("answer", "thinking", "stop")
        self.assertEqual(proxy._thinking_count(resp, ["<|channel>", "thought", "x", "<channel|>"], "thinking", 4), (None, None))

    def test_a_channel_end_as_the_last_token_is_not_the_end_of_thinking(self):
        resp = _reply("answer", "some reasoning", "stop")
        self.assertEqual(proxy._thinking_count(resp, ["a", "b", "c", "<|end|>"], "some reasoning", 4), (None, None))
        self.assertEqual(proxy._thinking_count(resp, ["a", "<|end|>", "c", "<|end|>"], "some reasoning", 4), (2, "marker"))

    def test_recount_fills_the_nulls_and_never_touches_its_input(self):
        with tempfile.TemporaryDirectory() as d:
            src, dest = Path(d) / "g.jsonl", Path(d) / "g.recount.jsonl"
            rec = {"thinking_tokens": None, "output_tokens": FIXTURE["output_tokens"], "tokens": FIXTURE["tokens"],
                   "reasoning_content": "(cut)", "upstream_response": FIXTURE["upstream_response"]}
            plain = {"thinking_tokens": 3, "output_tokens": 4, "tokens": ["a", "b", "</think>", "x"], "reasoning_content": "ab",
                     "upstream_response": _reply("x", "ab", "stop")}
            src.write_text(json.dumps(rec) + "\n" + json.dumps(plain) + "\n", encoding="utf-8")
            before = src.read_bytes()
            s = recount(src, dest)
            self.assertEqual(src.read_bytes(), before)
            self.assertEqual((s["calls"], s["null_before"], s["null_after"], s["changed"]), (2, 1, 0, 1))
            rows = [json.loads(x) for x in dest.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(rows[0]["thinking_tokens_source"], "marker")
            self.assertIsNone(rows[0]["thinking_tokens_was"])
            self.assertEqual((rows[1]["thinking_tokens"], rows[1]["thinking_tokens_source"]), (3, "marker"))
            self.assertNotIn("thinking_tokens_was", rows[1])
            with self.assertRaises(SystemExit):
                recount(src, dest)  # never overwrites


if __name__ == "__main__":
    unittest.main()
