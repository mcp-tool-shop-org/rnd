"""The atlas-mcp-utility harness's own logic (experiments/atlas-mcp-utility/run.py).

What the harness decides without the CLI or the network: whether the pins
hold, whether the work directory is readable, the run order, how a run's
tokens, tool calls and tool results are counted from its stream, whether a
run's start matches its arm, whether a hook ran, whether a probe leaked or
was carried out at all, when a plan limit stops the run, how a run's end
becomes its outcome, where Atlas would cache, and the flip rate. The CLI's
real behaviour is proven by the probes the spec records before the pilot,
not here; the init events under fixtures/atlas_mcp_utility are its real
starts, captured on 2026-10-13.
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


FIXTURES = ROOT / "tests" / "fixtures" / "atlas_mcp_utility"


def init_event(name):
    return json.loads((FIXTURES / f"init-{name}.json").read_text(encoding="utf-8"))


class Isolation(unittest.TestCase):
    # Amendment 4. The "wide" starts are the first probe's, before --tools:
    # 27 built-ins in arm A, SendMessage and PushNotification among them,
    # with 15 skills and 30 slash commands. The "restricted" starts are
    # run.py's own command with --tools and --disable-slash-commands.
    def setUp(self):
        self.allow = json.loads((HERE / "allow-list.json").read_text(encoding="utf-8"))

    def test_the_restricted_starts_match_their_arms_exactly(self):
        for arm in ("A", "B"):
            init = init_event(f"restricted-{arm}")
            self.assertEqual(sorted(init["tools"]), run.expected_tools(self.allow, arm))
            self.assertEqual(run.isolation_problems(init, arm, self.allow), [])

    def test_the_first_probes_wide_starts_are_refused(self):
        for arm in ("A", "B"):
            init = init_event(f"wide-{arm}")
            self.assertIn("SendMessage", init["tools"])
            problems = run.isolation_problems(init, arm, self.allow)
            self.assertTrue(any(p.startswith("tools the arm does not have: ") for p in problems), problems)
            self.assertIn("15 skills loaded", " ".join(problems))
            self.assertIn("30 slash commands loaded", " ".join(problems))

    def test_one_tool_too_many_or_too_few_is_refused(self):
        a = init_event("restricted-A")
        self.assertEqual(run.isolation_problems({**a, "tools": a["tools"] + ["SendMessage"]}, "A", self.allow),
                         ["tools the arm does not have: SendMessage"])
        self.assertEqual(run.isolation_problems({**a, "tools": [t for t in a["tools"] if t != "Grep"]}, "A", self.allow),
                         ["tools missing: Grep"])
        b = init_event("restricted-B")
        self.assertEqual(run.isolation_problems({**b, "tools": [t for t in b["tools"] if t != "mcp__atlas__atlas_reach"]}, "B", self.allow),
                         ["tools missing: mcp__atlas__atlas_reach"])
        self.assertEqual(run.isolation_problems({**b, "tools": b["tools"] + ["mcp__atlas__atlas_new"]}, "B", self.allow),
                         ["tools the arm does not have: mcp__atlas__atlas_new"])

    def test_a_skill_or_a_slash_command_is_refused(self):
        a = init_event("restricted-A")
        self.assertEqual(run.isolation_problems({**a, "skills": ["verify"]}, "A", self.allow), ["1 skills loaded: verify"])
        self.assertEqual(run.isolation_problems({**a, "slash_commands": ["loop"]}, "A", self.allow), ["1 slash commands loaded: loop"])

    def test_arm_b_needs_atlas_connected_and_arm_a_no_server(self):
        b = init_event("restricted-B")
        self.assertEqual(run.isolation_problems({**b, "mcp_servers": [{"name": "atlas", "status": "failed"}]}, "B", self.allow),
                         ["MCP servers are {'atlas': 'failed'}, the arm needs {'atlas': 'connected'}"])
        a = init_event("restricted-A")
        self.assertEqual(run.isolation_problems({**a, "mcp_servers": [{"name": "atlas", "status": "connected"}]}, "A", self.allow),
                         ["MCP servers are {'atlas': 'connected'}, the arm needs none"])

    def test_a_run_whose_start_does_not_match_its_arm_is_refused(self):
        a, b = init_event("restricted-A"), init_event("restricted-B")
        self.assertIn("arm A has Atlas tools", run.isolation_problems({**a, "tools": a["tools"] + ["mcp__atlas__atlas_reach"]}, "A", self.allow))
        self.assertIn("arm B has no Atlas tools", run.isolation_problems({**b, "tools": a["tools"]}, "B", self.allow))
        self.assertIn("MCP tools from another server", run.isolation_problems({**b, "tools": b["tools"] + ["mcp__ollama__x"]}, "B", self.allow)[0])
        self.assertEqual(run.isolation_problems(None, "A", self.allow), ["no init event"])
        self.assertEqual(run.isolation_problems({**a, "model": "claude-opus-5-5"}, "A", self.allow), ["the model is claude-opus-5-5, pinned claude-sonnet-5-5"])
        self.assertEqual(run.isolation_problems({**a, "claude_code_version": "2.1.198"}, "A", self.allow), ["the CLI is 2.1.198, pinned 2.1.197"])

    def test_a_start_outside_default_permissions_or_on_an_api_key_is_refused(self):
        # Amendment 7. The sandbox kit's user settings set bypassPermissions;
        # --setting-sources local must keep them out. And the Director's
        # ruling: the plan, never a paid per-token API key.
        a = init_event("restricted-A")
        self.assertEqual((a["permissionMode"], a["apiKeySource"]), ("default", "none"))
        self.assertEqual(run.isolation_problems({**a, "permissionMode": "bypassPermissions"}, "A", self.allow),
                         ["the permission mode is bypassPermissions, pinned default"])
        keyed = {**a, "apiKeySource": "ANTHROPIC_API_KEY"}
        self.assertEqual(run.isolation_problems(keyed, "A", self.allow),
                         ["the run does not sign in on the plan: the Director's ruling allows no API key"])
        self.assertTrue(run.on_the_plan(a, self.allow))
        self.assertFalse(run.on_the_plan(keyed, self.allow))
        # The source's own value is never written: PR #16's CodeQL alert.
        self.assertNotIn("ANTHROPIC_API_KEY", " ".join(run.isolation_problems(keyed, "A", self.allow)))

    def test_a_call_to_a_tool_outside_the_arm_is_refused_in_either_turn(self):
        # Amendment 8: 2.1.197 can register built-ins after the init that
        # --tools does not restrict, so the calls are checked, not only the start.
        stream = run.Stream()
        stream.add(assistant("m1", {}, [use("t1", "Read"), use("t2", "Bash", command="git log -1")]))
        self.assertEqual(run.tool_use_problems(stream, self.allow, "A"), [])
        stream.add(assistant("m2", {}, [use("t3", "SendMessage")]))
        self.assertEqual(run.tool_use_problems(stream, self.allow, "A"),
                         ["called a tool its arm does not have: SendMessage"])
        b_in_a = run.Stream()
        b_in_a.add(assistant("m1", {}, [use("t1", "mcp__atlas__atlas_reach")]))
        self.assertEqual(run.tool_use_problems(b_in_a, self.allow, "A"),
                         ["called a tool its arm does not have: mcp__atlas__atlas_reach"])
        self.assertEqual(run.tool_use_problems(b_in_a, self.allow, "B"), [])
        # The debrief's calls are held to the same rule (amendment 3).
        debrief = run.Stream()
        debrief.add(json.dumps({"type": "result", "result": "answer"}))
        debrief.add(assistant("d1", {}, [use("d2", "WebFetch")]))
        self.assertEqual(run.tool_use_problems(debrief, self.allow, "B"),
                         ["called a tool its arm does not have: WebFetch"])

    def test_arm_b_may_start_with_atlas_pending_and_no_atlas_tools(self):
        # Amendment 8: the sandbox probe's arm B started this way (2.1.197
        # registers MCP tools late) and its atlas_overview call answered.
        a, b = init_event("restricted-A"), init_event("restricted-B")
        late = {**b, "tools": a["tools"], "mcp_servers": [{"name": "atlas", "status": "pending"}]}
        self.assertEqual(run.isolation_problems(late, "B", self.allow), [])
        # Pending with some Atlas tools, or pending in arm A, is still refused.
        partial = {**late, "tools": a["tools"] + ["mcp__atlas__atlas_reach"]}
        self.assertTrue(run.isolation_problems(partial, "B", self.allow))
        self.assertEqual(run.isolation_problems({**a, "mcp_servers": [{"name": "atlas", "status": "pending"}]}, "A", self.allow),
                         ["MCP servers are {'atlas': 'pending'}, the arm needs none"])
        # A failed server is no late start.
        failed = {**late, "mcp_servers": [{"name": "atlas", "status": "failed"}]}
        self.assertIn("arm B has no Atlas tools", run.isolation_problems(failed, "B", self.allow))

    def test_the_labels_are_the_pilot_and_the_shakedown(self):
        self.assertEqual(run.LABELS, ("pilot", "shakedown"))
        self.assertEqual(run.PROBE_REPORT, run.HERE / "results" / "pilot" / "probe-report.json")

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

    CLEAN = {"run": "probe", "outcome": "answered", "exit_code": 0, "isolation": [], "error": None, "stderr": ""}

    def test_the_prompt_asks_for_every_route_in_every_tree(self):
        prompt = run.probe_prompt(self.TARGETS, "R/amu-probe-repo-1")
        self.assertEqual(prompt.count("Read the file"), 2)
        self.assertEqual(prompt.count("git grep --no-index"), 2)
        # Amendment 7: the git route names a repository the probe makes, so it
        # works in the sandbox, where E:/AI/testing-os does not exist.
        self.assertIn("git -C R/amu-probe-repo-1 log -1", prompt)
        self.assertNotIn("E:/AI/testing-os", prompt)
        self.assertIn("RIG: yes or RIG: no", prompt)

    SENTINELS = [("home content", "amu-sentinel-0a1b2c3d"), ("home hidden file name", "amu-hidden-4e5f6071.txt")]

    def test_a_probe_that_was_carried_out_and_leaked_nothing_passes(self):
        verdict = run.probe_verdict(self.probe_a(), self.probe_b(), self.CLEAN, self.CLEAN, self.TARGETS, self.SENTINELS)
        self.assertTrue(verdict["passed"], verdict)
        self.assertTrue(verdict["user_claude_md_loaded"])

    def test_a_sentinel_in_any_result_fails_the_probe(self):
        verdict = run.probe_verdict(self.probe_a(leak="found amu-sentinel-0a1b2c3d"), self.probe_b(), self.CLEAN, self.CLEAN, self.TARGETS, self.SENTINELS)
        self.assertFalse(verdict["passed"])
        self.assertEqual(verdict["leaks"], [{"sentinel": "home content", "sha256": run.digest("amu-sentinel-0a1b2c3d"), "tool": "Read"}])

    def test_the_report_holds_no_planted_value_even_when_one_leaked(self):
        # R&D's review of #8: CodeQL flagged the report for storing the planted
        # values. It carries each one's label and sha256, and a leaked value
        # in a tool result is replaced by its label.
        verdict = run.probe_verdict(self.probe_a(leak="amu-sentinel-0a1b2c3d and amu-hidden-4e5f6071.txt"), self.probe_b(), self.CLEAN, self.CLEAN, self.TARGETS, self.SENTINELS)
        text = json.dumps(verdict)
        for _, value in self.SENTINELS:
            self.assertNotIn(value, text)
        self.assertIn("<home content>", text)
        self.assertIn(run.digest("amu-hidden-4e5f6071.txt"), text)

    def test_a_probe_the_agent_did_not_carry_out_proves_nothing(self):
        verdict = run.probe_verdict(self.probe_a(calls=3), self.probe_b(), self.CLEAN, self.CLEAN, self.TARGETS, self.SENTINELS)
        self.assertFalse(verdict["passed"])

    def test_an_isolation_problem_fails_the_probe(self):
        verdict = run.probe_verdict(self.probe_a(), self.probe_b(), {**self.CLEAN, "isolation": ["hook ran: x"]}, self.CLEAN, self.TARGETS, self.SENTINELS)
        self.assertFalse(verdict["passed"])

    def test_a_probe_that_ended_in_an_error_fails_and_says_why(self):
        # The first probe, 2026-10-13: both runs met a stale sign-in, and the
        # report said only passed: false. Now each run's outcome and error are in it.
        failed = {**self.CLEAN, "outcome": "auth_failed", "error": "Failed to authenticate. API Error: 401 OAuth access token is invalid."}
        verdict = run.probe_verdict(self.probe_a(), self.probe_b(), failed, self.CLEAN, self.TARGETS, self.SENTINELS)
        self.assertFalse(verdict["passed"])
        self.assertEqual(verdict["records"][0]["outcome"], "auth_failed")
        self.assertIn("401", verdict["records"][0]["error"])
        self.assertIsNone(verdict["records"][1]["error"])

    def test_an_error_in_the_report_holds_no_planted_value(self):
        errored = {**self.CLEAN, "outcome": "errored", "error": "could not read amu-sentinel-0a1b2c3d"}
        verdict = run.probe_verdict(self.probe_a(), self.probe_b(), errored, self.CLEAN, self.TARGETS, self.SENTINELS)
        self.assertEqual(verdict["records"][0]["error"], "could not read <home content>")

    def test_an_atlas_overview_that_errs_fails_the_probe(self):
        # With --tools there is no ToolSearch: the call must work as the tool starts.
        stream = run.Stream()
        stream.add(assistant("b1", {}, [use("o1", "mcp__atlas__atlas_overview")]))
        stream.add(tool_result("o1", "tool not available", is_error=True))
        verdict = run.probe_verdict(self.probe_a(), stream, self.CLEAN, self.CLEAN, self.TARGETS, self.SENTINELS)
        self.assertFalse(verdict["atlas_overview_answered"])
        self.assertFalse(verdict["passed"])


class Outcomes(unittest.TestCase):
    # The result events as the CLI 2.1.197 wrote them on 2026-10-13.
    AUTH = {"type": "result", "subtype": "success", "is_error": True, "result": "Failed to authenticate. API Error: 401 OAuth access token is invalid."}
    TURN_CAP = {"type": "result", "subtype": "error_max_turns", "is_error": True, "result": None, "errors": ["Reached maximum number of turns (1)"]}
    ANSWER = {"type": "result", "subtype": "success", "is_error": False, "result": "{\"file\": \"x\"}"}

    def test_each_end_has_its_outcome(self):
        self.assertEqual(run.outcome_of("ceiling", self.ANSWER, []), "ceiling")
        self.assertEqual(run.outcome_of(None, self.AUTH, []), "auth_failed")
        self.assertEqual(run.outcome_of(None, {**self.AUTH, "result": "Claude usage limit reached"}, []), "plan_limit")
        self.assertEqual(run.outcome_of(None, self.ANSWER, ["hook ran: x"]), "isolation_failed")
        self.assertEqual(run.outcome_of(None, None, []), "harness_failure")
        self.assertEqual(run.outcome_of(None, self.TURN_CAP, []), "turn_cap")
        self.assertEqual(run.outcome_of(None, {**self.ANSWER, "is_error": True, "result": "API Error: 529 overloaded"}, []), "errored")
        self.assertEqual(run.outcome_of(None, self.ANSWER, []), "answered")

    def test_an_error_result_stops_the_pilot_and_the_turn_cap_is_graded(self):
        # Amendment 4: any error result is an andon; the turn cap is the
        # agent's outcome, graded incorrect (README, "Grading").
        self.assertIn("auth_failed", run.HALTING)
        self.assertIn("errored", run.HALTING)
        self.assertNotIn("turn_cap", run.HALTING)
        self.assertIn("turn_cap", run.GRADED)
        self.assertNotIn("harness_failure", run.HALTING)

    def test_the_error_text_is_kept_only_for_a_run_that_did_not_end_in_its_own_outcome(self):
        self.assertIsNone(run.error_text({"outcome": "answered", "error": None}))
        self.assertIsNone(run.error_text({"outcome": "turn_cap", "error": "Reached maximum number of turns (40)"}))
        self.assertEqual(run.error_text({"outcome": "harness_failure", "error": None, "stderr": "spawn failed"}), "spawn failed")


class AtlasCache(unittest.TestCase):
    def test_the_cache_root_follows_atlas_rule(self):
        # packages/atlas/sidecar/refresh.js, cacheRoot(), at Atlas 1.26.0.
        home = Path("/h")
        self.assertEqual(run.atlas_cache_root({"LOCALAPPDATA": "X:/L"}, "win32", home), Path("X:/L/atlas"))
        self.assertEqual(run.atlas_cache_root({}, "win32", home), home / "AppData" / "Local" / "atlas")
        self.assertEqual(run.atlas_cache_root({"XDG_CACHE_HOME": "/xdg"}, "linux", home), Path("/xdg/atlas"))
        self.assertEqual(run.atlas_cache_root({"XDG_CACHE_HOME": "rel"}, "linux", home), home / ".cache" / "atlas")

    def test_arm_b_caches_in_its_own_directory_and_arm_a_runs_no_server(self):
        cache = Path("w/runs/RC03-B1.cache")
        servers = run.mcp_servers("B", Path("t"), cache)
        self.assertEqual(servers["atlas"]["env"], {"LOCALAPPDATA": str(cache), "XDG_CACHE_HOME": str(cache)})
        self.assertEqual(servers["atlas"]["args"][-1], "mcp")
        self.assertEqual(run.mcp_servers("A", Path("t"), cache), {})
        # The override lands where Atlas looks, on either platform.
        self.assertEqual(run.atlas_cache_root(servers["atlas"]["env"], "win32"), cache / "atlas")

    def test_the_guard_sees_any_change_in_the_shared_cache(self):
        root = Path(tempfile.mkdtemp())
        try:
            cache = root / "atlas"
            self.assertIsNone(run.tree_state(cache))
            cache.mkdir()
            empty = run.tree_state(cache)
            self.assertEqual(empty, [])
            (cache / "snap").mkdir()
            (cache / "snap" / "page.json").write_text("{}", encoding="utf-8")
            written = run.tree_state(cache)
            self.assertNotEqual(written, empty)
            (cache / "snap" / "page.json").write_text("{\"x\": 1}", encoding="utf-8")
            self.assertNotEqual(run.tree_state(cache), written)
        finally:
            shutil.rmtree(root)


class BashDetector(unittest.TestCase):
    """R&D's review: git log stays allowed, so any form that could write
    outside the checkout or run another command stops the pilot."""

    def test_each_form_is_caught(self):
        cases = {
            "git log --output=../out.txt": ["--output"],
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


class Debrief(unittest.TestCase):
    """Amendment 3: a second turn after the graded first result."""

    def two_turns(self):
        stream = run.Stream()
        stream.add(assistant("m1", {"input_tokens": 10, "output_tokens": 90}, [use("t1", "Grep", pattern="x")]))
        stream.add(json.dumps({"type": "result", "subtype": "success", "result": 'Done. {"files": ["src/a.ts"]}'}))
        stream.add(assistant("m2", {"input_tokens": 5, "output_tokens": 45}, [use("t2", "Read", file_path="src/b.ts")]))
        stream.add(json.dumps({"type": "result", "subtype": "success", "result": '1. Time: none. On reflection the answer is {"files": ["src/b.ts"]}'}))
        return stream

    def test_the_first_result_is_graded_whatever_the_debrief_says(self):
        stream = self.two_turns()
        task = {"id": "X", "grade": {"checks": [{"kind": "path_set", "field": "files", "expect": ["src/a.ts"]}], "example": {}}}
        grader = importlib.util.module_from_spec(importlib.util.spec_from_file_location("g", HERE / "grade.py"))
        grader.__spec__.loader.exec_module(grader)
        self.assertTrue(grader.grade(task, stream.result()["result"])["correct"])
        self.assertIn("src/b.ts", stream.debrief_result()["result"])

    def test_debrief_tokens_and_calls_are_kept_apart(self):
        stream = self.two_turns()
        self.assertEqual(sum(stream.tokens.values()), 100)
        self.assertEqual(sum(stream.debrief_tokens.values()), 50)
        self.assertEqual(stream.total, 150)
        self.assertEqual(stream.calls, ["Grep"])
        self.assertEqual(stream.debrief_calls, ["Read"])

    def test_a_run_with_one_turn_has_no_debrief_tokens(self):
        stream = run.Stream()
        stream.add(assistant("m1", {"output_tokens": 7}))
        stream.add(json.dumps({"type": "result", "result": "x"}))
        self.assertEqual(sum(stream.debrief_tokens.values()), 0)
        self.assertIsNone(stream.debrief_result())

    def test_the_debrief_prompt_is_pinned(self):
        self.assertIn("debrief.md", run.PINNED_FILES)
        with tempfile.TemporaryDirectory() as tmp:
            copy = Path(tmp)
            for name in run.PINNED_FILES + ("README.md",):
                shutil.copy(HERE / name, copy / name)
            (copy / "debrief.md").write_text("How did it go?\n", encoding="utf-8")
            self.assertEqual(run.pin_problems(copy), ["debrief.md: does not match its pin"])

    def test_the_debrief_asks_the_six_questions_with_no_tools(self):
        text = (HERE / "debrief.md").read_text(encoding="utf-8")
        self.assertIn("without using any tools", text)
        for number in range(1, 7):
            self.assertIn(f"\n{number}. ", text)

    def test_each_numbered_answer_is_its_own_field(self):
        items = run.debrief_items("1. The lockfile scan.\n2. No.\n**3.** Grep; none wrong.\n4. Fairly sure.\n5. A lock reader.\n6. Nothing else.")
        self.assertEqual(items["time_and_cost"], "The lockfile scan.")
        self.assertEqual(items["tools"], "Grep; none wrong.")
        self.assertEqual(items["other"], "Nothing else.")
        self.assertEqual(run.debrief_items("Only prose.")["clarity"], None)

    def test_each_turn_is_one_stream_json_user_message(self):
        line = run.user_message("hello\nthere")
        self.assertTrue(line.endswith("\n"))
        self.assertEqual(line.count("\n"), 1)
        self.assertEqual(json.loads(line)["message"]["content"][0]["text"], "hello\nthere")


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

    def test_the_command_offers_only_four_built_ins_and_no_slash_command(self):
        # Amendment 4: --allowedTools only pre-approves; --tools decides which
        # built-ins exist. The allow and deny rules still gate those four.
        for arm in ("A", "B"):
            cmd = run.command("claude", self.allow, arm, Path("x.mcp.json"))
            self.assertEqual(cmd[cmd.index("--tools") + 1], "Read,Grep,Glob,Bash")
            self.assertIn("--disable-slash-commands", cmd)
            self.assertIn("Read(//e/AI/**)", cmd)
            self.assertIn("Bash(git log:*)", cmd)

    def test_the_command_pins_medium_effort_and_default_permissions(self):
        # Amendment 7: the Director's ruling sets medium effort. The init event
        # does not echo it, so the record takes it from the allow-list.
        self.assertEqual(self.allow["effort"], "medium")
        self.assertEqual(self.allow["api_key_source"], "none")
        self.assertIn("Read(//proc/**)", self.allow["disallowed_tools"])
        for arm in ("A", "B"):
            cmd = run.command("claude", self.allow, arm, Path("x.mcp.json"))
            self.assertEqual(cmd[cmd.index("--effort") + 1], "medium")
            self.assertEqual(cmd[cmd.index("--permission-mode") + 1], "default")


class Cleanup(unittest.TestCase):
    def test_remove_tree_takes_a_read_only_file_and_a_missing_path(self):
        # The probe's own repository: git writes its objects read-only on Windows.
        root = Path(tempfile.mkdtemp())
        target = root / "repo"
        (target / "objects").mkdir(parents=True)
        locked = target / "objects" / "pack"
        locked.write_text("x", encoding="utf-8")
        locked.chmod(0o444)
        run.remove_tree(target)
        self.assertFalse(target.exists())
        run.remove_tree(target)
        shutil.rmtree(root)


if __name__ == "__main__":
    unittest.main()
