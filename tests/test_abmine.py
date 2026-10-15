"""rnd abmine (ab_dataminer).

Synthetic generations with known Δz exercise each rule: an exact match, a rank flip at the fork, censored steps, no
top_logprobs at all, and a fork by length. The fixture is the 2026-10-15 cu1343 sandbox record (one log line's PATH
values removed), and the test checks it against the outside reviewer's hand figures: sky step 15 Δz 0.770, hammer
step 6 Δz 1.345, sky step 14 runner-up shift 1.30.
"""
import contextlib
import hashlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from mcptoolshop_rnd import abmine, cli

HERE = Path(__file__).resolve().parent
FIX = HERE / "fixtures" / "abmine"
RECORD = FIX / "cu1343-record.jsonl"
LOG = FIX / "cu1343-11500-excerpt.log"


def gen(tokens, top, pec=10, **kw):
    return abmine.Gen(tokens=list(tokens), top=[list(s) for s in top], prompt_eval_count=pec, **kw)


def row(arm, prompt, tokens, top, **kw):
    return json.dumps({"kind": "result", "arm": arm, "prompt": prompt, "tokens": tokens,
                       "top": [[list(c) for c in s] for s in top], **kw})


class DeltaZ(unittest.TestCase):
    def test_known_value(self):
        dz, why = abmine.delta_z([("a", -0.1), ("b", -1.1)], [("a", -0.3), ("b", -0.8)])
        self.assertEqual(why, "")
        self.assertAlmostEqual(dz, 1.0 - 0.5)

    def test_rank_flip_gives_a_gap_larger_than_the_reference_gap(self):
        dz, _ = abmine.delta_z([("a", -0.2), ("b", -1.0)], [("b", -0.3), ("a", -0.6)])
        self.assertAlmostEqual(dz, 0.8 - (-0.3))

    def test_censored_when_a_reference_candidate_is_missing(self):
        dz, why = abmine.delta_z([("a", -0.1), ("b", -1.1)], [("a", -0.1), ("z", -2.0)])
        self.assertIsNone(dz)
        self.assertIn("censored", why)

    def test_needs_two_reference_candidates(self):
        self.assertIsNone(abmine.delta_z([("a", -0.1)], [("a", -0.1), ("b", -1)])[0])

    def test_logprob_lookup(self):
        self.assertEqual(abmine.logprob([("a", -1.0)], "a"), -1.0)
        self.assertIsNone(abmine.logprob([("a", -1.0)], "b"))


class Helpers(unittest.TestCase):
    def test_fork_index(self):
        self.assertIsNone(abmine.fork_index(["a", "b"], ["a", "b"]))
        self.assertEqual(abmine.fork_index(["a", "b"], ["a", "c"]), 1)
        self.assertEqual(abmine.fork_index(["a"], ["a", "b"]), 1)

    def test_slope(self):
        self.assertAlmostEqual(abmine.slope([(0, 0.0), (1, 1.0), (2, 2.0)]), 1.0)
        self.assertIsNone(abmine.slope([(0, 1.0)]))
        self.assertIsNone(abmine.slope([(3, 1.0), (3, 2.0)]))

    def test_p95(self):
        self.assertIsNone(abmine.p95([]))
        self.assertAlmostEqual(abmine.p95([0.0, 1.0]), 0.95)
        self.assertEqual(abmine.p95([2.0]), 2.0)

    def test_tok_per_s(self):
        self.assertAlmostEqual(gen([], [], eval_count=100, eval_duration_ns=2_000_000_000).tok_per_s, 50.0)
        self.assertIsNone(gen([], []).tok_per_s)


class Compare(unittest.TestCase):
    def test_exact_match_reads_every_step(self):
        top = [[("a", -0.1), ("b", -2.0)], [("c", -0.2), ("d", -1.5)]]
        c = abmine.compare(gen("ac", top), gen("ac", top))
        self.assertTrue(c["identical"])
        self.assertIsNone(c["fork"])
        self.assertEqual(c["steps_read"], 2)
        self.assertEqual(c["step0_dz"], 0.0)
        self.assertEqual(c["prefix_abs_dz"]["max"], 0.0)
        self.assertNotIn("fork_detail", c)
        self.assertEqual(c["chosen_token_mae"], 0.0)

    def test_rank_flip_at_the_fork(self):
        ref = gen("xa", [[("x", -0.1), ("y", -3.0)], [("a", -0.3), ("b", -1.0)]])
        test = gen("xb", [[("x", -0.1), ("y", -2.9)], [("b", -0.4), ("a", -0.9)]])
        c = abmine.compare(ref, test)
        self.assertFalse(c["identical"])
        self.assertEqual(c["fork"], 1)
        self.assertAlmostEqual(c["step0_dz"], 2.9 - 2.8)
        fd = c["fork_detail"]
        self.assertEqual((fd["ref_token"], fd["test_token"]), ("a", "b"))
        self.assertAlmostEqual(fd["dz"], 0.7 - (-0.5))
        self.assertFalse(fd["censored"])
        self.assertEqual(c["prefix_abs_dz"]["n"], 1)  # the fork step is not part of the matched prefix
        self.assertEqual(c["chosen_token_n"], 1)

    def test_censored_steps_are_flagged_not_read(self):
        ref = gen("ab", [[("a", -0.1), ("q", -2.0)], [("b", -0.1), ("r", -3.0)]])
        test = gen("ab", [[("a", -0.1), ("z", -2.0)], [("b", -0.1), ("r", -3.1)]])
        c = abmine.compare(ref, test)
        self.assertEqual([x["step"] for x in c["censored"]], [0])
        self.assertIsNone(c["step0_dz"])
        self.assertEqual(c["steps_read"], 1)

    def test_no_top_logprobs(self):
        c = abmine.compare(gen("ab", []), gen("ac", []))
        self.assertEqual(c["steps_read"], 0)
        self.assertIsNone(c["prefix_abs_dz"]["mean"])
        self.assertIsNone(c["chosen_token_mae"])
        self.assertIsNone(c["fork_detail"]["ref_top"])
        self.assertIsNone(c["fork_detail"]["dz"])

    def test_fork_by_length(self):
        top = [[("a", -0.1), ("b", -2.0)]]
        c = abmine.compare(gen("a", top), gen("ab", top + [[("b", -0.1), ("c", -1.0)]]))
        self.assertEqual(c["fork"], 1)
        self.assertIsNone(c["fork_detail"]["ref_token"])

    def test_a_spike_stands_out_from_the_prefix(self):
        steps = [[("a", -0.1), ("b", -2.0)]] * 5
        test = [[("a", -0.1), ("b", -2.0)]] * 4 + [[("a", -0.1), ("b", -1.0)]]
        c = abmine.compare(gen("aaaaa", steps), gen("aaaaa", test))
        self.assertEqual(c["spikes"], [{"step": 4, "abs_dz": c["prefix_abs_dz"]["max"]}])


class Records(unittest.TestCase):
    def test_load_records(self):
        lines = ["", json.dumps({"kind": "start"}),
                 row("A", 0, ["x"], [[("x", -0.1), ("y", -1.0)]], prompt_eval_count=7),
                 json.dumps({"kind": "result", "block": "B", "prompt": 0, "tokens": ["x"], "top": []})]
        recs = abmine.load_records(lines)
        self.assertEqual(sorted(recs), ["A", "B"])
        self.assertEqual(recs["A"][0].prompt_eval_count, 7)
        self.assertEqual(recs["A"][0].top[0][1], ("y", -1.0))

    def test_bad_lines(self):
        with self.assertRaises(abmine.AbmineError):
            abmine.load_records(["{not json"])
        with self.assertRaises(abmine.AbmineError):
            abmine.load_records([json.dumps({"kind": "result", "prompt": 0})])


class MatrixAndTieBreak(unittest.TestCase):
    def setUp(self):
        t = [[("a", -0.1), ("b", -1.0)], [("c", -0.2), ("d", -0.9)], [("e", -0.1), ("f", -2.0)]]
        self.recs = {
            "S0": {0: gen("ace", t), 1: gen("ace", t)},
            "S2": {0: gen("ade", t), 1: gen("ace", t)},
            "ref": {0: gen("acx", t), 1: gen("ace", t)},
        }

    def test_matrix(self):
        m = abmine.matrix(self.recs, ["S0", "S2"])["S0 vs S2"]
        self.assertEqual((m["prompts"], m["identical"]), (2, 1))
        self.assertEqual(m["forks"], {0: 1})

    def test_tie_break(self):
        rows = abmine.tie_break(self.recs, "ref", "S0", "S2")
        self.assertEqual(rows, [{"prompt": 0, "fork": 1, "reference_token": "c", "reference": "S0",
                                 "reference_top": [("c", -0.2), ("d", -0.9)]}])

    def test_tie_break_cases(self):
        t = [[("a", -0.1), ("b", -1.0)]] * 3
        recs = {"A": {0: gen("abc", t), 1: gen("abc", t), 2: gen("abc", t), 3: gen("abc", t)},
                "B": {0: gen("abd", t), 1: gen("abd", t), 2: gen("abd", t), 3: gen("abd", t)},
                "R": {0: gen("xbc", t), 1: gen("ab", t), 2: gen("abz", t)}}
        got = {r["prompt"]: r["reference"] for r in abmine.tie_break(recs, "R", "A", "B")}
        self.assertEqual(got, {0: "diverged earlier, at step 0", 1: "ended before the fork", 2: "neither", 3: "missing"})

    def test_analyze_with_reference(self):
        rep = abmine.analyze(self.recs, reference="ref")
        self.assertIn("S0 vs S2", rep["tie_break"])
        self.assertEqual(set(rep["mae_vs_reference"]), {"S0", "S2"})
        text = abmine.render(rep)
        self.assertIn("tie-break S0 vs S2, prompt 0 fork 1: reference -> S0", text)
        self.assertIn("chosen-token MAE vs reference", text)


class Logs(unittest.TestCase):
    def test_parse_the_cu1343_excerpt(self):
        lg = abmine.parse_log(LOG.read_text(encoding="utf-8"))
        self.assertEqual([b["kind"] for b in lg["backends"]], ["CPU", "CUDA"])
        self.assertTrue(lg["backends"][1]["path"].endswith("cuda_v13\\ggml-cuda.dll"))
        self.assertEqual(lg["device"], {"name": "NVIDIA GeForce RTX 5090", "compute": "12.0", "vmm": "yes"})
        self.assertEqual(lg["inference_compute"]["library"], "CUDA")
        self.assertEqual((lg["flash_attn_setting"], lg["flash_attn_resolved"]), ("auto", "enabled"))
        self.assertEqual(lg["kv_types"], {"k": "f16", "v": "f16"})
        self.assertEqual(lg["n_ctx"], 2048)
        self.assertEqual(lg["graphs_reused"], [11])
        self.assertEqual(lg["prompt_tokens"], [19])

    def test_a_forced_flash_attention_setting_is_its_own_resolution(self):
        # With OLLAMA_FLASH_ATTENTION=0, Ollama passes --flash-attn off; llama.cpp logs the setting as "disabled"
        # and never prints a "Flash Attention ..." resolution line (resolve_fused_ops runs only for "auto").
        lg = abmine.parse_log("llama_context: flash_attn            = disabled")
        self.assertEqual((lg["flash_attn_setting"], lg["flash_attn_resolved"]), ("disabled", "disabled"))
        lg = abmine.parse_log("llama_context: flash_attn            = enabled")
        self.assertEqual(lg["flash_attn_resolved"], "enabled")
        lg = abmine.parse_log("\n".join(["llama_context: flash_attn            = auto",
                                         "resolve_fused_ops: Flash Attention disabled"]))
        self.assertEqual((lg["flash_attn_setting"], lg["flash_attn_resolved"]), ("auto", "disabled"))

    def test_an_empty_log(self):
        lg = abmine.parse_log("")
        self.assertIsNone(lg["flash_attn_resolved"])
        self.assertEqual(lg["backends"], [])


class TheCu1343Record(unittest.TestCase):
    """The reviewer's hand figures, recomputed by the tool from the record."""

    @classmethod
    def setUpClass(cls):
        cls.recs = abmine.load_record_file(RECORD)
        cls.pairs = abmine.matrix(cls.recs, ["stock A", "sandbox"])["stock A vs sandbox"]["per_prompt"]

    def test_arms_and_prompts(self):
        self.assertEqual(sorted(self.recs), ["sandbox", "stock A", "stock B"])
        self.assertEqual(sorted(self.recs["sandbox"]), [0, 1, 2])

    def test_stock_matches_itself(self):
        m = abmine.matrix(self.recs, ["stock A", "stock B"])["stock A vs stock B"]
        self.assertEqual(m["identical"], 3)
        self.assertEqual(m["mean_abs_step0_dz"], 0.0)

    def test_sky_fork(self):
        c = self.pairs[0]
        self.assertEqual(c["fork"], 15)
        self.assertAlmostEqual(c["fork_detail"]["dz"], 0.770, places=3)

    def test_hammer_fork(self):
        c = self.pairs[2]
        self.assertEqual(c["fork"], 6)
        self.assertAlmostEqual(c["fork_detail"]["dz"], 1.345, places=3)

    def test_sky_step14_runner_up_shift(self):
        a, s = self.recs["stock A"][0].top[14], self.recs["sandbox"][0].top[14]
        shift = s[1][1] - a[1][1]
        self.assertAlmostEqual(shift, 1.294, places=3)  # the reviewer's hand figure, 1.30, was rounded
        self.assertAlmostEqual(shift, 1.30, delta=0.01)
        self.assertEqual(self.pairs[0]["spikes"][0]["step"], 14)

    def test_fibonacci_matches_but_still_moves(self):
        c = self.pairs[1]
        self.assertTrue(c["identical"])
        self.assertGreater(c["prefix_abs_dz"]["max"], 1.0)
        self.assertEqual(len(c["censored"]), 4)

    def test_step0_differs_on_every_prompt(self):
        for p in (0, 1, 2):
            self.assertGreater(abs(self.pairs[p]["step0_dz"]), 0.1)


class Probe(unittest.TestCase):
    TEMPLATE = "{{ .Content }} a stand-in template"

    def pinned(self):
        return mock.patch.object(abmine, "QWEN3_TEMPLATE_SHA256",
                                 hashlib.sha256(self.TEMPLATE.encode("utf-8")).hexdigest())

    def test_render_qwen3(self):
        with self.pinned():
            self.assertEqual(abmine.render_qwen3("Hi", False, self.TEMPLATE),
                             "<|im_start|>user\nHi /no_think<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n")
            self.assertEqual(abmine.render_qwen3("Hi", True, self.TEMPLATE),
                             "<|im_start|>user\nHi /think<|im_end|>\n<|im_start|>assistant\n")

    def test_render_refuses_another_template(self):
        with self.assertRaises(abmine.AbmineError):
            abmine.render_qwen3("Hi", False, "something else")

    def test_template_from_store(self):
        with tempfile.TemporaryDirectory() as d:
            base = Path(d)
            (base / "manifests/registry.ollama.ai/library/m").mkdir(parents=True)
            (base / "blobs").mkdir()
            (base / "blobs/sha256-abc").write_text(self.TEMPLATE, encoding="utf-8")
            man = {"layers": [{"mediaType": "application/vnd.ollama.image.template", "digest": "sha256:abc"}]}
            (base / "manifests/registry.ollama.ai/library/m/t").write_text(json.dumps(man), encoding="utf-8")
            self.assertEqual(abmine.template_from_store(base, "m", "t"), self.TEMPLATE)
            (base / "manifests/registry.ollama.ai/library/m/u").write_text(json.dumps({"layers": []}), encoding="utf-8")
            with self.assertRaises(abmine.AbmineError):
                abmine.template_from_store(base, "m", "u")

    def test_replay_body_is_raw_and_one_token(self):
        b = abmine.replay_body("m", "PROMPT", ["a", "b"], 5, {"temperature": 0, "num_predict": 64})
        self.assertTrue(b["raw"])
        self.assertEqual(b["prompt"], "PROMPTab")
        self.assertEqual(b["options"]["num_predict"], 1)
        self.assertEqual(b["top_logprobs"], 5)

    def reply(self, top, pec):
        return {"logprobs": [{"token": top[0][0], "top_logprobs": [{"token": t, "logprob": lp} for t, lp in top]}],
                "prompt_eval_count": pec}

    def test_probe_reproduces_step0_then_scans(self):
        g = gen("ab", [[("a", -0.1), ("b", -2.0)], [("b", -0.2), ("c", -1.0)]], pec=10)
        replies = {0: self.reply([("a", -0.1), ("b", -2.0)], 10), 1: self.reply([("b", -0.25), ("c", -1.0)], 11),
                   2: self.reply([("x", -0.1), ("y", -1.0)], 14)}
        sent = []

        def post(body):
            sent.append(body)
            return replies[len(body["prompt"]) - len("R")]

        rows = abmine.probe(post, "m", "R", g, [2, 1], 2, {"temperature": 0})
        self.assertEqual([r["position"] for r in rows], [0, 2, 1])
        self.assertTrue(rows[0]["reproduces_step0"])
        self.assertTrue(rows[1]["retokenized"])
        self.assertFalse(rows[2]["retokenized"])
        vd = abmine.replay_vs_decode(g, rows)
        self.assertEqual([v["position"] for v in vd], [0, 1])
        self.assertAlmostEqual(vd[1]["dz"], 0.8 - 0.75)

    def test_probe_stops_when_step0_is_not_reproduced(self):
        g = gen("ab", [[("a", -0.1), ("b", -2.0)]], pec=10)
        with self.assertRaises(abmine.AbmineError):
            abmine.probe(lambda b: self.reply([("a", -0.1), ("b", -2.0)], 12), "m", "R", g, [], 2, {})
        with self.assertRaises(abmine.AbmineError):
            abmine.probe(lambda b: self.reply([("a", -0.5), ("b", -2.0)], 10), "m", "R", g, [], 2, {})
        with self.assertRaises(abmine.AbmineError):
            abmine.probe(lambda b: {"prompt_eval_count": 10}, "m", "R", g, [], 2, {})

    def test_probe_refuses_a_position_past_the_end(self):
        g = gen("a", [[("a", -0.1), ("b", -2.0)]], pec=10)
        with self.assertRaises(abmine.AbmineError):
            abmine.probe(lambda b: self.reply([("a", -0.1), ("b", -2.0)], 10), "m", "R", g, [5], 2, {})


class Cli(unittest.TestCase):
    def run_cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = cli.main(list(argv))
        return code, out.getvalue(), err.getvalue()

    def test_analyze_text_and_json(self):
        code, out, _ = self.run_cli("abmine", "analyze", str(RECORD), "--arm", "stock A", "--arm", "sandbox",
                                    "--log", f"sandbox={LOG}")
        self.assertEqual(code, 0)
        self.assertIn("stock A vs sandbox: 1 of 3 prompts identical", out)
        self.assertIn("flash_attn auto -> enabled", out)
        code, out, _ = self.run_cli("abmine", "analyze", str(RECORD), "--json", "--reference", "stock B")
        self.assertEqual(code, 0)
        data = json.loads(out)
        self.assertIn("sandbox vs stock A", data["tie_break"])

    def test_errors(self):
        with tempfile.TemporaryDirectory() as d:
            empty = Path(d) / "empty.jsonl"
            empty.write_text(json.dumps({"kind": "start"}) + "\n", encoding="utf-8")
            self.assertEqual(self.run_cli("abmine", "analyze", str(Path(d) / "none.jsonl"))[0], 2)
            self.assertEqual(self.run_cli("abmine", "analyze", str(empty))[0], 2)
        self.assertEqual(self.run_cli("abmine", "analyze", str(RECORD), "--log", "nonsense")[0], 2)
        self.assertEqual(self.run_cli("abmine", "analyze", str(RECORD), "--log", "x=Z:/no/such.log")[0], 2)
        code, _, err = self.run_cli("abmine", "analyze", str(RECORD), "--arm", "nope")
        self.assertEqual(code, 2)
        self.assertIn("ABMINE_ARM", err)


if __name__ == "__main__":
    unittest.main()
