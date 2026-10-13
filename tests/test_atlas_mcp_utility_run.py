"""The atlas-mcp-utility harness's own logic (experiments/atlas-mcp-utility/run.py).

What the harness decides without the CLI or the network: whether the pins
hold, the run order, how a run's tokens and tool calls are counted from its
stream, whether a run's start matches its arm, when a plan limit stops the
run, and the flip rate. The CLI's real stream is proven by the probes the
spec records before the pilot, not here.
"""
import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HERE = ROOT / "experiments" / "atlas-mcp-utility"

spec = importlib.util.spec_from_file_location("atlas_mcp_utility_run", HERE / "run.py")
run = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run)


def assistant(message_id, usage=None, blocks=()):
    return json.dumps({"type": "assistant", "message": {"id": message_id, "usage": usage or {}, "content": list(blocks)}})


class Pins(unittest.TestCase):
    def test_the_committed_files_match_the_readme(self):
        self.assertEqual(run.pin_problems(), [])

    def test_a_changed_file_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            copy = Path(tmp)
            for name in run.PINNED_FILES + ("README.md",):
                shutil.copy(HERE / name, copy / name)
            (copy / "prompt.md").write_text("a different prompt\n", encoding="utf-8")
            self.assertEqual(run.pin_problems(copy), ["prompt.md: does not match its pin"])

    def test_the_readme_table_is_read_with_its_notes(self):
        text = "| `tasks.json` | `" + "a" * 64 + "` (amendment 1) |\n| Seed | 20261013 |\n"
        self.assertEqual(run.readme_pins(text), {"tasks.json": "a" * 64})


class Plan(unittest.TestCase):
    def test_the_pilot_plan_is_fixed_by_the_seed(self):
        plan = run.run_plan(run.PILOT, run.PILOT_REPEATS)
        self.assertEqual([(p["task"], p["rep"]) for p in plan], [("RC03", 1), ("RC03", 2), ("CF09", 1), ("CF02", 1), ("CF04", 1), ("CF04", 2)])
        self.assertEqual(plan, run.run_plan(run.PILOT, run.PILOT_REPEATS))
        for pair in plan:
            self.assertEqual(sorted(pair["order"]), ["A", "B"])

    def test_the_pilot_is_twelve_runs(self):
        self.assertEqual(sum(len(p["order"]) for p in run.run_plan(run.PILOT, run.PILOT_REPEATS)), 12)


class Counting(unittest.TestCase):
    def test_a_message_split_over_events_counts_once(self):
        stream = run.Stream()
        usage = {"input_tokens": 3, "cache_creation_input_tokens": 100, "cache_read_input_tokens": 1000, "output_tokens": 50}
        stream.add(assistant("m1", usage, [{"type": "text", "text": "looking"}]))
        stream.add(assistant("m1", usage, [{"type": "tool_use", "id": "t1", "name": "Grep"}]))
        stream.add(assistant("m2", {"input_tokens": 1, "output_tokens": 5}, [{"type": "tool_use", "id": "t2", "name": "mcp__atlas__atlas_explain"}]))
        self.assertEqual(stream.total, 1159)
        self.assertEqual(stream.tokens["cache_read_input_tokens"], 1000)
        self.assertEqual(stream.calls, ["Grep", "mcp__atlas__atlas_explain"])

    def test_lines_that_are_not_json_are_skipped(self):
        stream = run.Stream()
        stream.add("not json\n")
        stream.add("\n")
        self.assertEqual((stream.events, stream.total), ([], 0))

    def test_the_init_and_result_events_are_found(self):
        stream = run.Stream()
        stream.add(json.dumps({"type": "system", "subtype": "init", "tools": ["Read"], "model": "claude-sonnet-5-5"}))
        stream.add(json.dumps({"type": "result", "subtype": "success", "result": "{\"file\": \"x\"}"}))
        self.assertEqual(stream.init()["tools"], ["Read"])
        self.assertEqual(stream.result()["result"], "{\"file\": \"x\"}")


class Isolation(unittest.TestCase):
    MODEL = "claude-sonnet-5-5"

    def test_each_arm_has_the_tools_it_should(self):
        a = {"tools": ["Read", "Grep"], "model": self.MODEL}
        b = {"tools": ["Read", "mcp__atlas__atlas_overview"], "model": self.MODEL}
        self.assertEqual(run.isolation_problems(a, "A", self.MODEL), [])
        self.assertEqual(run.isolation_problems(b, "B", self.MODEL), [])

    def test_a_run_whose_start_does_not_match_its_arm_is_refused(self):
        self.assertEqual(run.isolation_problems({"tools": ["mcp__atlas__atlas_reach"], "model": self.MODEL}, "A", self.MODEL), ["arm A has Atlas tools"])
        self.assertEqual(run.isolation_problems({"tools": ["Read"], "model": self.MODEL}, "B", self.MODEL), ["arm B has no Atlas tools"])
        self.assertIn("MCP tools from another server", run.isolation_problems({"tools": ["mcp__ollama__x", "mcp__atlas__y"], "model": self.MODEL}, "B", self.MODEL)[0])
        self.assertEqual(run.isolation_problems(None, "A", self.MODEL), ["no init event"])
        self.assertEqual(run.isolation_problems({"tools": [], "model": "claude-opus-5-5"}, "A", self.MODEL), ["the model is claude-opus-5-5, pinned claude-sonnet-5-5"])


class Stops(unittest.TestCase):
    def test_a_spent_plan_stops_the_run(self):
        self.assertTrue(run.plan_limit_hit({"type": "result", "is_error": True, "result": "Claude usage limit reached. Your limit will reset at 5pm"}))
        self.assertFalse(run.plan_limit_hit({"type": "result", "is_error": True, "result": "API Error: 500"}))
        self.assertFalse(run.plan_limit_hit({"type": "result", "is_error": False, "result": "the rate limit in config.ts is 10"}))
        self.assertFalse(run.plan_limit_hit(None))


class FlipRate(unittest.TestCase):
    def test_a_repeat_that_disagrees_with_its_first_run_is_a_flip(self):
        records = [
            {"task": "RC03", "arm": "A", "rep": 1, "correct": True},
            {"task": "RC03", "arm": "A", "rep": 2, "correct": False},
            {"task": "RC03", "arm": "B", "rep": 1, "correct": True},
            {"task": "RC03", "arm": "B", "rep": 2, "correct": True},
            {"task": "CF09", "arm": "A", "rep": 1, "correct": True},
        ]
        self.assertEqual(run.flip_rate(records), {"repeated_runs": 2, "flips": 1, "rate": 0.5})

    def test_no_repeats_is_no_rate(self):
        self.assertIsNone(run.flip_rate([{"task": "CF09", "arm": "A", "rep": 1, "correct": True}]))


class Allowlist(unittest.TestCase):
    def test_reads_are_held_to_the_checkout_and_nothing_writes(self):
        allow = json.loads((HERE / "allow-list.json").read_text(encoding="utf-8"))
        self.assertIn("Read(./**)", allow["allowed_tools"])
        self.assertNotIn("Read", allow["allowed_tools"])
        for denied in ("Edit", "Write", "WebFetch", "WebSearch"):
            self.assertIn(denied, allow["disallowed_tools"])
        self.assertEqual(allow["setting_sources"], "local")

    def test_the_command_carries_the_isolation(self):
        allow = json.loads((HERE / "allow-list.json").read_text(encoding="utf-8"))
        cmd = run.command("claude", allow, "B", Path("b.mcp.json"))
        for flag in ("--strict-mcp-config", "--no-session-persistence", "--verbose"):
            self.assertIn(flag, cmd)
        self.assertEqual(cmd[cmd.index("--setting-sources") + 1], "local")
        self.assertIn("mcp__atlas", cmd)
        self.assertNotIn("mcp__atlas", run.command("claude", allow, "A", Path("a.mcp.json")))


if __name__ == "__main__":
    unittest.main()
