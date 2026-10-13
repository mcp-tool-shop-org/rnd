"""The atlas-mcp-utility harness's own logic (experiments/atlas-mcp-utility/run.py).

What the harness decides without the CLI or the network: whether the pins
hold, whether the work directory is readable, the run order, how a run's
tokens, tool calls and tool results are counted from its stream, whether a
run's start matches its arm, whether a hook ran, whether a probe leaked or
was carried out at all, when a plan limit stops the run, and the flip rate.
The CLI's real behaviour is proven by the probes the spec records before the
pilot, not here.
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


def tool_result(use_id, text, is_error=False):
    return json.dumps({"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": use_id, "is_error": is_error, "content": [{"type": "text", "text": text}]}]}})


def use(use_id, name, **inputs):
    return {"type": "tool_use", "id": use_id, "name": name, "input": inputs}


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


class WorkDirectory(unittest.TestCase):
    def test_a_work_directory_under_a_denied_tree_is_refused(self):
        with tempfile.TemporaryDirectory() as denied:
            inner = Path(denied) / "runs"
            self.assertEqual(len(run.work_problems(inner, roots=(Path(denied),))), 1)

    def test_a_work_directory_outside_every_denied_tree_is_accepted(self):
        with tempfile.TemporaryDirectory() as denied, tempfile.TemporaryDirectory() as elsewhere:
            self.assertEqual(run.work_problems(Path(elsewhere), roots=(Path(denied),)), [])


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
        stream.add(assistant("m1", usage, [use("t1", "Grep", pattern="x")]))
        stream.add(assistant("m2", {"input_tokens": 1, "output_tokens": 5}, [use("t2", "mcp__atlas__atlas_explain", path="a")]))
        self.assertEqual(stream.total, 1159)
        self.assertEqual(stream.tokens["cache_read_input_tokens"], 1000)
        self.assertEqual(stream.calls, ["Grep", "mcp__atlas__atlas_explain"])

    def test_tool_results_are_kept_by_the_call_they_answer(self):
        stream = run.Stream()
        stream.add(assistant("m1", {}, [use("t1", "Read", file_path="x")]))
        stream.add(tool_result("t1", "Permission to read x was denied", is_error=True))
        self.assertEqual(stream.results["t1"], {"is_error": True, "text": "Permission to read x was denied"})

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

    def test_a_hook_is_seen_by_its_event_or_its_marker(self):
        stream = run.Stream()
        stream.add(json.dumps({"type": "system", "subtype": "hook_response"}))
        stream.add(json.dumps({"type": "user", "message": {"content": "[loadout-hook] Memory entries relevant"}}))
        self.assertEqual(stream.hook_traces(), ["hook_response", "[loadout-hook] text"])
        self.assertEqual(run.Stream().hook_traces(), [])


class Probe(unittest.TestCase):
    TARGETS = {"home": {"file": "H/amu-probe-1.txt", "dir": "H"}, "E:/AI": {"file": "E/amu-probe-2.txt", "dir": "E"}}

    def probe_a(self, leak=None, calls=11):
        stream = run.Stream()
        names = ["Read", "Grep", "Glob", "Bash", "Bash"] * 2 + ["Bash"]
        for i, name in enumerate(names[:calls]):
            stream.add(assistant(f"m{i}", {}, [use(f"t{i}", name, command="ls H" if name == "Bash" else None)]))
            stream.add(tool_result(f"t{i}", leak if (leak and i == 0) else "denied", is_error=not (leak and i == 0)))
        stream.add(json.dumps({"type": "result", "result": "1. denied ... RIG: yes"}))
        return stream

    def probe_b(self):
        stream = run.Stream()
        stream.add(assistant("b1", {}, [use("o1", "mcp__atlas__atlas_overview")]))
        stream.add(tool_result("o1", "parts: src, tests"))
        return stream

    CLEAN = {"isolation": []}

    def test_the_prompt_asks_for_every_route_in_every_tree(self):
        prompt = run.probe_prompt(self.TARGETS)
        self.assertEqual(prompt.count("Read the file"), 2)
        self.assertEqual(prompt.count("git grep --no-index"), 2)
        self.assertIn("git -C E:/AI/testing-os log -1", prompt)
        self.assertIn("RIG: yes or RIG: no", prompt)

    def test_a_probe_that_was_carried_out_and_leaked_nothing_passes(self):
        verdict = run.probe_verdict(self.probe_a(), self.probe_b(), self.CLEAN, self.CLEAN, self.TARGETS, ["amu-secret-abc", "amu-hidden-def.txt"])
        self.assertTrue(verdict["passed"], verdict)
        self.assertTrue(verdict["user_claude_md_loaded"])

    def test_a_secret_in_any_result_fails_the_probe(self):
        verdict = run.probe_verdict(self.probe_a(leak="amu-secret-abc"), self.probe_b(), self.CLEAN, self.CLEAN, self.TARGETS, ["amu-secret-abc"])
        self.assertFalse(verdict["passed"])
        self.assertEqual(verdict["leaks"][0]["tool"], "Read")

    def test_a_probe_the_agent_did_not_carry_out_proves_nothing(self):
        verdict = run.probe_verdict(self.probe_a(calls=3), self.probe_b(), self.CLEAN, self.CLEAN, self.TARGETS, ["amu-secret-abc"])
        self.assertFalse(verdict["passed"])

    def test_an_isolation_problem_fails_the_probe(self):
        verdict = run.probe_verdict(self.probe_a(), self.probe_b(), {"isolation": ["hook ran: x"]}, self.CLEAN, self.TARGETS, ["amu-secret-abc"])
        self.assertFalse(verdict["passed"])


class BashDetector(unittest.TestCase):
    """R&D's review: git log stays allowed, so any form that could write
    outside the checkout or run another command stops the pilot."""

    def test_each_form_is_caught(self):
        cases = {
            "git log --output=/c/Users/x/out.txt": ["--output"],
            "git log --output /tmp/out.txt": ["--output"],
            "git log > out.txt": [">"],
            "git log >> out.txt": [">"],
            "git log | head": ["|"],
            "git log; cat ~/secret": [";"],
            "git log && cat ~/secret": ["&&"],
            "git log $(cat ~/secret)": ["$("],
            "git log \"$(cat ~/secret)\"": ["$("],
            "git log `cat ~/secret`": ["`"],
            # R&D's bypasses on #7: a second command on a new line, a
            # background `&`, and a file fed to git on stdin.
            "git log -1\ncat ~/secret": ["newline"],
            "git log -1\r\ncat ~/secret": ["newline"],
            "git log -1 & cat x": ["&"],
            "git log -1 --stdin < ~/x": ["<"],
        }
        for command, forms in cases.items():
            with self.subTest(command=command):
                self.assertEqual(run.bash_violations(command), forms)

    def test_plain_history_reads_pass(self):
        for command in ("git log --oneline -20", "git show HEAD:src/route.ts", "git log --format='%H|%s' -5", 'git log --grep="a > b"', "git log -- src/server.ts", "git log --format='%H\n%s' -3", 'git log --grep="a < b & c"'):
            with self.subTest(command=command):
                self.assertEqual(run.bash_violations(command), [])

    def test_a_run_with_a_violating_call_is_named(self):
        stream = run.Stream()
        stream.add(assistant("m1", {}, [use("t1", "Bash", command="git log --oneline -3"), use("t2", "Bash", command="git log > /c/out.txt")]))
        problems = run.bash_problems(stream)
        self.assertEqual(len(problems), 1)
        self.assertIn("git log > /c/out.txt", problems[0])


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
    def setUp(self):
        self.allow = json.loads((HERE / "allow-list.json").read_text(encoding="utf-8"))

    def test_reads_are_held_to_the_checkout_and_nothing_writes(self):
        self.assertIn("Read(./**)", self.allow["allowed_tools"])
        self.assertNotIn("Read", self.allow["allowed_tools"])
        for denied in ("Read(~/**)", "Read(//c/Users/**)", "Read(//d/**)", "Read(//e/AI/**)", "Edit", "Write", "WebFetch", "WebSearch"):
            self.assertIn(denied, self.allow["disallowed_tools"])
        self.assertEqual(self.allow["setting_sources"], "local")

    def test_no_bash_form_can_read_outside_the_checkout(self):
        # ls lists any directory, and git grep --no-index reads any path.
        bash = [t for t in self.allow["allowed_tools"] if t.startswith("Bash(")]
        self.assertEqual(bash, ["Bash(git log:*)", "Bash(git show:*)"])

    def test_the_command_carries_the_isolation(self):
        cmd = run.command("claude", self.allow, "B", Path("b.mcp.json"))
        for flag in ("--strict-mcp-config", "--no-session-persistence", "--verbose"):
            self.assertIn(flag, cmd)
        self.assertEqual(cmd[cmd.index("--setting-sources") + 1], "local")
        self.assertIn("mcp__atlas", cmd)
        self.assertNotIn("mcp__atlas", run.command("claude", self.allow, "A", Path("a.mcp.json")))


if __name__ == "__main__":
    unittest.main()
