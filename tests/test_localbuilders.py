"""Unit tests for `mcptoolshop_rnd.localbuilders` (J2 harness and logging proxy, amendment C).

All tests are `unittest.TestCase` classes with no GPU and no external network:
- ProxyTests: against a local `http.server` stub llama-server returning canned responses (F1, F3, F4, F5)
- ScorerTests: canned JUnit XML and workspace fixtures for pass and every refusal kind (F10, NB2)
- WorkspaceTests: 2-task fixture bank from repo history; no git history reaches the fix;
  `docs/runs/`, `CHANGELOG.md`, and design notes removed; `GIT_CONFIG_NOSYSTEM=1` (F7, F9)
- ContainmentAndProbeTests: iptables owner rules, Drive mount refusal, and injected success/failure
  for every one of the 10 containment probe checks (F9, section 8)
- PreflightTests: F13 context sizing from 30-call validation run, F5 top-5 logprobs check from
  index 1 on, F6 Q6_K flagging and non-exiting fit report
- RunnerAndReceiptTests: exact Aider command line flags, `Coder.create` `max_reflections=29`
  wrapper, and section-7 receipt completeness (NB1, F2, F4, F7, F9, F10, section 7)
"""
from __future__ import annotations

import contextlib
import http.server
import io
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from unittest import mock

from mcptoolshop_rnd import abmine
from mcptoolshop_rnd.localbuilders import (
    contain,
    preflight,
    probe,
    proxy,
    runner,
    score,
    workspace,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "localbuilders"
BANK_JSON = FIXTURE_DIR / "bank.json"
CANDIDATE_CONFIG_JSON = FIXTURE_DIR / "candidate_config.json"


def _make_five_top(prefix: str, step: int) -> list[dict]:
    return [
        {"token": f"{prefix}{step}_c{i}", "logprob": round(-0.1 * (i + 1), 4)}
        for i in range(5)
    ]


def _canned_llama_response(
    *,
    content: str = "Fixed the bug.",
    reasoning_content: str = "Let me inspect the function first.",
    finish_reason: str = "stop",
    steps: int = 4,
    prompt_tokens: int = 120,
    completion_tokens: int = 18,
    reasoning_tokens: int = 10,
) -> dict:
    lp_content = []
    for s in range(steps):
        top5 = _make_five_top("tok", s)
        lp_content.append(
            {
                "token": top5[0]["token"],
                "logprob": top5[0]["logprob"],
                "top_logprobs": top5,
            }
        )
    return {
        "id": "chatcmpl-stub-1",
        "object": "chat.completion",
        "model": "fixture-candidate-q8_0",
        "choices": [
            {
                "index": 0,
                "finish_reason": finish_reason,
                "message": {
                    "role": "assistant",
                    "content": content,
                    "reasoning_content": reasoning_content,
                },
                "logprobs": {
                    "content": lp_content,
                },
            }
        ],
        "usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
            "completion_tokens_details": {
                "reasoning_tokens": reasoning_tokens,
            },
        },
        "timings": {
            "prompt_n": prompt_tokens,
            "prompt_ms": 14.5,
            "predicted_n": completion_tokens,
            "predicted_ms": 82.0,
        },
    }


class _StubLlamaServer:
    """Local loopback `http.server` returning canned OpenAI/llama-server responses."""

    def __init__(self, response_fn=None):
        self.received_requests: list[dict] = []
        self.response_fn = response_fn or (lambda req_body, idx: _canned_llama_response())
        outer = self

        class Handler(http.server.BaseHTTPRequestHandler):
            def log_message(self, fmt, *args):
                return

            def do_POST(self):  # noqa: N802
                length = int(self.headers.get("Content-Length", "0"))
                raw = self.rfile.read(length)
                body = json.loads(raw.decode("utf-8"))
                idx = len(outer.received_requests)
                outer.received_requests.append({"path": self.path, "body": body})
                reply = outer.response_fn(body, idx)
                payload = json.dumps(reply).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

        self.httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.port = self.httpd.server_address[1]
        self.url = f"http://127.0.0.1:{self.port}"
        self._thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)

    def __enter__(self):
        self._thread.start()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.httpd.shutdown()
        self.httpd.server_close()
        self._thread.join(timeout=5.0)


def _post_json(url: str, payload: dict) -> tuple[int, dict]:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(req, timeout=10) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as err:
        return err.code, json.loads(err.read().decode("utf-8"))


class ProxyTests(unittest.TestCase):
    """Tests for `mcptoolshop_rnd.localbuilders.proxy` (F1, F3, F4, F5)."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.gen_path = self.tmp / "generations.jsonl"

    def test_f1_f3_f5_upstream_overrides_stripping_and_abmine_format(self):
        with _StubLlamaServer() as stub:
            state = proxy.ProxyState(
                upstream_url=stub.url,
                config=CANDIDATE_CONFIG_JSON,
                generations_path=self.gen_path,
            )
            self.assertGreater(state.remaining_wall_s(), 0.0)
            with proxy.LoggingProxyServer(state) as srv:
                status, reply = _post_json(
                    f"{srv.openai_base_url}/chat/completions",
                    {
                        "model": "fixture-candidate-q8_0",
                        "stream": True,  # Aider might ask to stream; F1 must force stream: false
                        "temperature": 0.0,  # Aider's default; F3 must override with card config
                        "top_p": 1.0,
                        "top_k": 1,
                        "min_p": 0.5,
                        "messages": [{"role": "user", "content": "Fix the bug"}],
                    },
                )

                opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
                with opener.open(f"{srv.base_url}/health") as hresp:
                    self.assertEqual(hresp.status, 200)
                with opener.open(f"{srv.base_url}/v1/models") as mresp:
                    self.assertEqual(mresp.status, 200)
                try:
                    opener.open(f"{srv.base_url}/unknown")
                except urllib.error.HTTPError as e404:
                    self.assertEqual(e404.code, 404)

                bad_req = urllib.request.Request(
                    f"{srv.openai_base_url}/chat/completions",
                    data=b"{not-json",
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                try:
                    opener.open(bad_req)
                except urllib.error.HTTPError as e400:
                    self.assertEqual(e400.code, 400)

        self.assertEqual(status, 200)
        self.assertEqual(len(stub.received_requests), 1)
        sent_up = stub.received_requests[0]["body"]

        # F1: stream is forced to False upstream
        self.assertIs(sent_up["stream"], False)
        # F3: sampling overridden from candidate_config.json and chat_template_kwargs injected
        self.assertEqual(sent_up["temperature"], 0.6)
        self.assertEqual(sent_up["top_p"], 0.95)
        self.assertEqual(sent_up["top_k"], 20)
        self.assertEqual(sent_up["min_p"], 0.0)
        self.assertEqual(sent_up["chat_template_kwargs"], {"enable_thinking": True})
        # F5: logprobs requested upstream
        self.assertIs(sent_up["logprobs"], True)
        self.assertEqual(sent_up["top_logprobs"], 5)

        # F5: logprobs and reasoning_content stripped from the reply returned to Aider
        choice0 = reply["choices"][0]
        self.assertNotIn("logprobs", choice0)
        self.assertNotIn("reasoning_content", choice0)
        self.assertNotIn("reasoning_content", choice0["message"])
        self.assertNotIn("logprobs", choice0["message"])
        self.assertEqual(choice0["message"]["content"], "Fixed the bug.")

        # F5 & F3: generations.jsonl has abmine-loadable result with reasoning_content, logprobs, timings, injected
        lines = self.gen_path.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), 1)
        rec = json.loads(lines[0])
        self.assertEqual(rec["kind"], "result")
        self.assertEqual(rec["arm"], "fixture-candidate-q8_0")
        self.assertEqual(rec["prompt"], 0)
        self.assertEqual(rec["reasoning_content"], "Let me inspect the function first.")
        self.assertIsNotNone(rec["logprobs"])
        self.assertEqual(len(rec["tokens"]), 4)
        self.assertEqual(len(rec["top"]), 4)
        self.assertEqual(len(rec["top"][1]), 5)
        self.assertEqual(rec["thinking_tokens"], 10)
        self.assertEqual(rec["output_tokens"], 18)
        self.assertEqual(rec["prompt_tokens"], 120)
        self.assertFalse(rec["truncated"])
        self.assertIn("predicted_ms", rec["timings"])
        self.assertGreaterEqual(rec["wall_time_s"], 0.0)
        self.assertEqual(
            rec["injected"],
            {
                "sampling": {"temperature": 0.6, "top_p": 0.95, "top_k": 20, "min_p": 0.0},
                "chat_template_kwargs": {"enable_thinking": True},
            },
        )

        # Verify `mcptoolshop_rnd.abmine.load_record_file` loads `generations.jsonl` directly
        loaded = abmine.load_record_file(self.gen_path)
        self.assertIn("fixture-candidate-q8_0", loaded)
        gen0 = loaded["fixture-candidate-q8_0"][0]
        self.assertEqual(gen0.tokens, ["tok0_c0", "tok1_c0", "tok2_c0", "tok3_c0"])
        self.assertEqual(len(gen0.top[1]), 5)
        self.assertEqual(gen0.prompt_eval_count, 120)
        self.assertEqual(gen0.eval_count, 18)

    def test_f4_refuses_31st_call_with_http_429_and_records_it(self):
        with _StubLlamaServer() as stub:
            state = proxy.ProxyState(
                upstream_url=stub.url,
                config=CANDIDATE_CONFIG_JSON,
                generations_path=self.gen_path,
                max_calls=30,
            )
            with proxy.LoggingProxyServer(state) as srv:
                url = f"{srv.openai_base_url}/chat/completions"
                for i in range(30):
                    code, _ = _post_json(url, {"messages": [{"role": "user", "content": f"turn {i}"}]})
                    self.assertEqual(code, 200)

                # 31st call must be refused with 429 and never sent to stub llama-server
                code31, body31 = _post_json(url, {"messages": [{"role": "user", "content": "turn 30"}]})
                self.assertEqual(code31, 429)
                self.assertEqual(body31["error"]["type"], "call_cap_exceeded")

        self.assertEqual(len(stub.received_requests), 30)
        summary = state.summary()
        self.assertEqual(summary["call_count"], 30)
        self.assertEqual(summary["call_cap_hits"], 1)
        self.assertTrue(summary["cap_hits"]["call_cap"])

        rows = [json.loads(line) for line in self.gen_path.read_text(encoding="utf-8").splitlines()]
        self.assertEqual(len(rows), 31)
        self.assertEqual(rows[-1]["kind"], "refused")
        self.assertEqual(rows[-1]["reason"], "call_cap")
        self.assertEqual(rows[-1]["status"], 429)
        self.assertEqual(rows[-1]["call_index"], 31)

    def test_f4_wall_cap_and_truncation_recorded(self):
        fake_now = [100.0]

        def clock():
            return fake_now[0]

        def resp_fn(body, idx):
            if idx == 0:
                return _canned_llama_response(finish_reason="length")
            fake_now[0] += 905.0
            return _canned_llama_response(finish_reason="stop")

        with _StubLlamaServer(response_fn=resp_fn) as stub:
            state = proxy.ProxyState(
                upstream_url=stub.url,
                config=CANDIDATE_CONFIG_JSON,
                generations_path=self.gen_path,
                wall_limit_s=900.0,
                clock=clock,
            )
            with proxy.LoggingProxyServer(state) as srv:
                url = f"{srv.openai_base_url}/chat/completions"
                c1, _ = _post_json(url, {"messages": [{"role": "user", "content": "1"}]})
                self.assertEqual(c1, 200)
                c2, b2 = _post_json(url, {"messages": [{"role": "user", "content": "2"}]})
                self.assertEqual(c2, 429)
                self.assertEqual(b2["error"]["type"], "wall_cap_exceeded")
                c3, b3 = _post_json(url, {"messages": [{"role": "user", "content": "3"}]})
                self.assertEqual(c3, 429)
                self.assertEqual(b3["error"]["type"], "wall_cap_exceeded")

        self.assertEqual(len(stub.received_requests), 2)
        summary = state.summary()
        self.assertTrue(summary["truncated"])
        self.assertEqual(summary["truncated_calls"], 1)
        self.assertEqual(summary["wall_cap_hits"], 2)
        self.assertTrue(summary["cap_hits"]["wall_cap"])

    def test_config_validation_and_token_fallbacks(self):
        with self.assertRaises(proxy.ProxyConfigError):
            proxy.load_candidate_config(self.tmp / "missing.json")

        bad_json = self.tmp / "bad.json"
        bad_json.write_text("{bad", encoding="utf-8")
        with self.assertRaises(proxy.ProxyConfigError):
            proxy.load_candidate_config(bad_json)

        not_obj = self.tmp / "list.json"
        not_obj.write_text("[]", encoding="utf-8")
        with self.assertRaises(proxy.ProxyConfigError):
            proxy.load_candidate_config(not_obj)

        no_sampling = self.tmp / "no_sampling.json"
        no_sampling.write_text('{"chat_template_kwargs": {}}', encoding="utf-8")
        with self.assertRaises(proxy.ProxyConfigError):
            proxy.load_candidate_config(no_sampling)

        no_kwargs = self.tmp / "no_kwargs.json"
        no_kwargs.write_text('{"sampling": {"temperature": 0.2}}', encoding="utf-8")
        with self.assertRaises(proxy.ProxyConfigError):
            proxy.load_candidate_config(no_kwargs)

        # Fallback logprobs and reasoning shapes
        toks, top = proxy.extract_abmine_logprobs(
            {"logprobs": ["skip", {"token": "a", "top_logprobs": [["a", -0.1], ["b", -1.2]]}]}
        )
        self.assertEqual(toks, ["a"])
        self.assertEqual(top, [[["a", -0.1], ["b", -1.2]]])
        self.assertEqual(proxy._extract_reasoning_and_content({"response": "hi", "reasoning_content": "r"}), ("hi", "r"))
        self.assertEqual(
            proxy._extract_reasoning_and_content(
                {"choices": [{"text": "t", "reasoning_content": "r2"}]}
            ),
            ("t", "r2"),
        )
        self.assertEqual(
            proxy._extract_reasoning_and_content(
                {"choices": [{"message": {"content": "c"}}], "reasoning_content": "r3"}
            ),
            ("c", "r3"),
        )

        p_tok, th_tok, out_tok = proxy._count_tokens(
            {"timings": {"prompt_n": 15}},
            ["<think>", "step", "</think>", "ans"],
            None,
        )
        self.assertEqual((p_tok, th_tok, out_tok), (15, 3, 4))

        p_tok2, th_tok2, out_tok2 = proxy._count_tokens({}, ["ans"], "one two three")
        self.assertEqual((p_tok2, th_tok2, out_tok2), (0, 3, 1))

        # Upstream connection error returns 502; TimeoutError returns 429 wall_cap
        state = proxy.ProxyState(
            upstream_url="http://127.0.0.1:9",
            config=CANDIDATE_CONFIG_JSON,
            generations_path=self.gen_path,
        )
        code, err_body = state.handle_completion("/v1/chat/completions", {"messages": []})
        self.assertEqual(code, 502)
        self.assertEqual(err_body["error"]["type"], "upstream_error")

        with mock.patch.object(proxy.urllib.request, "urlopen", side_effect=TimeoutError("timed out")):
            code_to, body_to = state.handle_completion("/v1/chat/completions", {"messages": []})
            self.assertEqual(code_to, 429)
            self.assertEqual(body_to["error"]["type"], "wall_cap_exceeded")


class ScorerTests(unittest.TestCase):
    """Tests for `mcptoolshop_rnd.localbuilders.score` on canned JUnit XML and workspace fixtures (F10, NB2)."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.ws = self.tmp / "ws"
        (self.ws / "mcptoolshop_rnd").mkdir(parents=True)
        (self.ws / "tests").mkdir(parents=True)
        (self.ws / "mcptoolshop_rnd" / "abmine.py").write_text("x = 1\n", encoding="utf-8")
        (self.ws / "tests" / "test_abmine_fa.py").write_text("def test_target(): pass\n", encoding="utf-8")
        self.pre_hashes = workspace.snapshot_test_hashes(self.ws)
        self.task = workspace.load_task_bank(BANK_JSON)[0]

    def _canned_xml(
        self,
        *,
        passed_extra: int = 200,
        skipped: int = 1,
        xfail: int = 0,
        target_status: str = "passed",
        twin_status: str = "passed",
        suite_failures: int = 0,
        suite_errors: int = 0,
    ) -> str:
        cases: list[str] = []
        for i in range(passed_extra):
            cases.append(f'<testcase file="tests/test_suite.py" classname="tests.test_suite.Suite" name="test_ok_{i}"/>')
        for i in range(skipped):
            cases.append(
                f'<testcase classname="tests.test_suite" name="test_skip_{i}">'
                f'<skipped type="pytest.skip" message="skip"/></testcase>'
            )
        for i in range(xfail):
            cases.append(
                f'<testcase classname="tests.test_suite.Suite" name="test_xfail_{i}">'
                f'<skipped type="pytest.xfail" message="xfail"/></testcase>'
            )
        for i in range(suite_failures):
            cases.append(
                f'<testcase classname="tests.test_suite.Suite" name="test_fail_{i}">'
                f'<failure message="boom"/></testcase>'
            )
        for i in range(suite_errors):
            cases.append(
                f'<testcase classname="tests.test_suite.Suite" name="test_err_{i}">'
                f'<error message="err"/></testcase>'
            )

        def render_node(node_id: str, status: str) -> str:
            inner = ""
            if status == "failure":
                inner = '<failure message="failed"/>'
            elif status == "error":
                inner = '<error message="error"/>'
            elif status == "skipped":
                inner = '<skipped type="pytest.skip" message="skipped in prod"/>'
            return f'<testcase nodeid="{node_id}" name="{node_id.split("::")[-1]}">{inner}</testcase>'

        cases.append(render_node(self.task.target_nodes[0], target_status))
        cases.append(render_node(self.task.twin_nodes[0], twin_status))
        return f'<testsuite name="pytest">{"".join(cases)}</testsuite>'

    def test_pass_when_all_f10_and_nb2_conditions_hold(self):
        xml_file = self.tmp / "canned.xml"
        xml_file.write_text(self._canned_xml(), encoding="utf-8")
        res = score.score_task(
            self.task,
            self.ws,
            self.pre_hashes,
            junit_xml=str(xml_file),
            git_status_output=" M mcptoolshop_rnd/abmine.py\n",
        )
        self.assertTrue(res["passed"], res["reasons"])
        self.assertTrue(res["correct"])
        self.assertEqual(res["reasons"], [])

    def test_refuses_edited_test_file(self):
        (self.ws / "tests" / "test_abmine_fa.py").write_text("def test_target(): assert True\n", encoding="utf-8")
        res = score.score_task(
            self.task,
            self.ws,
            self.pre_hashes,
            junit_xml=self._canned_xml(),
            git_status_output=" M mcptoolshop_rnd/abmine.py\n M tests/test_abmine_fa.py\n",
        )
        self.assertFalse(res["passed"])
        self.assertTrue(any("edited test file" in r for r in res["reasons"]), res["reasons"])

    def test_refuses_untracked_conftest_py(self):
        (self.ws / "conftest.py").write_text("import pytest\n", encoding="utf-8")
        res = score.score_task(
            self.task,
            self.ws,
            self.pre_hashes,
            junit_xml=self._canned_xml(),
            git_status_output=" M mcptoolshop_rnd/abmine.py\n?? conftest.py\n",
        )
        self.assertFalse(res["passed"])
        self.assertTrue(any("untracked conftest.py" in r for r in res["reasons"]), res["reasons"])

    def test_refuses_pytest_skip_in_production_code(self):
        res = score.score_task(
            self.task,
            self.ws,
            self.pre_hashes,
            junit_xml=self._canned_xml(skipped=2),
            git_status_output=" M mcptoolshop_rnd/abmine.py\n",
        )
        self.assertFalse(res["passed"])
        self.assertTrue(any("skipped count" in r for r in res["reasons"]), res["reasons"])

    def test_refuses_shrunken_parametrization_passed_count_short(self):
        res = score.score_task(
            self.task,
            self.ws,
            self.pre_hashes,
            junit_xml=self._canned_xml(passed_extra=195),
            git_status_output=" M mcptoolshop_rnd/abmine.py\n",
        )
        self.assertFalse(res["passed"])
        self.assertTrue(any("passed count short" in r for r in res["reasons"]), res["reasons"])

    def test_refuses_failing_twin(self):
        res = score.score_task(
            self.task,
            self.ws,
            self.pre_hashes,
            junit_xml=self._canned_xml(twin_status="failure"),
            git_status_output=" M mcptoolshop_rnd/abmine.py\n",
        )
        self.assertFalse(res["passed"])
        self.assertTrue(any("failing twin" in r for r in res["reasons"]), res["reasons"])

    def test_refuses_changed_path_outside_allowed_paths(self):
        res = score.score_task(
            self.task,
            self.ws,
            self.pre_hashes,
            junit_xml=self._canned_xml(),
            git_status_output=" M mcptoolshop_rnd/abmine.py\n M mcptoolshop_rnd/cli.py\n?? scratch.py\n",
        )
        self.assertFalse(res["passed"])
        self.assertTrue(
            any("changed path outside allowed_paths: mcptoolshop_rnd/cli.py" in r for r in res["reasons"]),
            res["reasons"],
        )
        self.assertTrue(
            any("changed path outside allowed_paths: scratch.py" in r for r in res["reasons"]),
            res["reasons"],
        )

    def test_junit_edge_cases_and_twin_runner(self):
        # Test outcome_for suffix matching and None fallback, <xfail/> tag, and empty/short status lines
        s = score.parse_junitxml(
            '<testsuite><testcase classname="tests.test_m.Cls" name="test_one"/><testcase name="test_xf"><xfail/></testcase></testsuite>'
        )
        self.assertEqual(s.outcome_for("tests/test_m.py::Cls::test_one"), "passed")
        self.assertEqual(s.outcome_for("other/path.py::Cls::test_one"), "passed")
        self.assertIsNone(s.outcome_for("nonexistent_node"))
        self.assertEqual(s.xfail, 1)
        self.assertEqual(score.parse_git_status_porcelain("\nxx\n M a.py\n"), [(" M", "a.py")])
        self.assertFalse(score.path_is_allowed("", ["mcptoolshop_rnd/abmine.py"]))
        self.assertEqual(
            score.check_workspace_integrity(self.ws, self.pre_hashes, ["tests/test_x.py"]),
            ["tests/** is never permitted in allowed_paths: 'tests/test_x.py'"],
        )

        # Exercise run_pytest_and_score with a stub command that writes canned XML (no pytest subprocess needed)
        canned_xml_text = self._canned_xml()
        stub_writer = self.tmp / "write_xml.py"
        stub_writer.write_text(
            "import sys, pathlib\n"
            f"xml = {canned_xml_text!r}\n"
            "for arg in sys.argv[1:]:\n"
            "    if arg.startswith('--junitxml='):\n"
            "        pathlib.Path(arg.split('=', 1)[1]).write_text(xml, encoding='utf-8')\n",
            encoding="utf-8",
        )
        subprocess.run(["git", "init", "-q"], cwd=str(self.ws), check=True)
        subprocess.run(["git", "config", "user.name", "t"], cwd=str(self.ws), check=True)
        subprocess.run(["git", "config", "user.email", "t@localhost"], cwd=str(self.ws), check=True)
        subprocess.run(["git", "add", "-A"], cwd=str(self.ws), check=True)
        subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=str(self.ws), check=True)

        res_live = score.run_pytest_and_score(
            self.task,
            self.ws,
            self.pre_hashes,
            pytest_cmd=[sys.executable, str(stub_writer)],
            aider_running=False,
        )
        self.assertTrue(res_live["passed"], res_live["reasons"])
        # Staged twin file is cleaned up after scoring
        self.assertFalse((self.ws / "tests" / "test_abmine_fa_twin.py").exists())

        # Missing --junitxml output raises ScoreError
        with self.assertRaises(score.ScoreError):
            score.run_pytest_and_score(
                self.task,
                self.ws,
                self.pre_hashes,
                pytest_cmd=[sys.executable, "-c", "pass"],
                aider_running=False,
            )

        # Deleted test file, added test file, renamed file in git status, xfail mismatch, target failure
        (self.ws / "tests" / "test_abmine_fa.py").unlink()
        (self.ws / "tests" / "test_extra.py").write_text("pass\n", encoding="utf-8")
        res = score.score_task(
            self.task,
            self.ws,
            self.pre_hashes,
            junit_xml=self._canned_xml(xfail=2, target_status="failure", suite_errors=1, suite_failures=1),
            git_status_output="R  mcptoolshop_rnd/abmine.py -> mcptoolshop_rnd/other.py\n M tests/test_abmine_fa.py\n",
        )
        self.assertFalse(res["passed"])
        self.assertTrue(any("deleted test file" in r for r in res["reasons"]))
        self.assertTrue(any("added test file" in r for r in res["reasons"]))
        self.assertTrue(any("target test did not pass" in r for r in res["reasons"]))
        self.assertTrue(any("xfail count" in r for r in res["reasons"]))
        self.assertTrue(any("suite errors" in r for r in res["reasons"]))
        self.assertTrue(any("suite failures" in r for r in res["reasons"]))

        with self.assertRaises(score.ScoreError):
            score.run_pytest_and_score(self.task, self.ws, self.pre_hashes, aider_running=True)
        with self.assertRaises(score.ScoreError):
            score.parse_junitxml("<not-closed")
        with self.assertRaises(score.ScoreError):
            score.parse_junitxml("nonexistent_file.xml")


class WorkspaceTests(unittest.TestCase):
    """Tests for `mcptoolshop_rnd.localbuilders.workspace` against the 2-task fixture bank (F7, F9)."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.tasks = workspace.load_task_bank(BANK_JSON)

        # Build a lightweight mirror git repo with two parent->fix commit pairs plus leaking files
        self.src_repo = self.tmp / "src_repo"
        (self.src_repo / "mcptoolshop_rnd").mkdir(parents=True)
        (self.src_repo / "tests").mkdir(parents=True)
        (self.src_repo / "docs" / "runs").mkdir(parents=True)
        (self.src_repo / "experiments" / "local-builders").mkdir(parents=True)
        (self.src_repo / "docs" / "runs" / "r1.md").write_text("run note\n", encoding="utf-8")
        (self.src_repo / "CHANGELOG.md").write_text("# Changelog\n", encoding="utf-8")
        (self.src_repo / "CHANGELOG.old").write_text("old\n", encoding="utf-8")
        (self.src_repo / "experiments" / "local-builders" / "DESIGN.md").write_text("secret design\n", encoding="utf-8")
        (self.src_repo / "mcptoolshop_rnd" / "abmine.py").write_text("def parse_log(t): return {}\n", encoding="utf-8")
        (self.src_repo / "mcptoolshop_rnd" / "watch.py").write_text("def check(s, st): return {}, {}\n", encoding="utf-8")

        env = workspace.git_env(self.tmp / "git_home")
        subprocess.run(["git", "init", "-q"], cwd=str(self.src_repo), env=env, check=True)
        subprocess.run(["git", "config", "user.name", "t"], cwd=str(self.src_repo), env=env, check=True)
        subprocess.run(["git", "config", "user.email", "t@localhost"], cwd=str(self.src_repo), env=env, check=True)
        subprocess.run(["git", "add", "-A"], cwd=str(self.src_repo), env=env, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "parent 1"], cwd=str(self.src_repo), env=env, check=True)
        self.parent1 = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=str(self.src_repo), env=env, capture_output=True, text=True, check=True
        ).stdout.strip()

        (self.src_repo / "mcptoolshop_rnd" / "abmine.py").write_text("# fixed 1\n", encoding="utf-8")
        subprocess.run(["git", "commit", "-q", "-am", "fix 1"], cwd=str(self.src_repo), env=env, check=True)
        self.fix1 = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=str(self.src_repo), env=env, capture_output=True, text=True, check=True
        ).stdout.strip()

        (self.src_repo / "mcptoolshop_rnd" / "watch.py").write_text("# fixed 2\n", encoding="utf-8")
        subprocess.run(["git", "commit", "-q", "-am", "fix 2"], cwd=str(self.src_repo), env=env, check=True)
        self.fix2 = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=str(self.src_repo), env=env, capture_output=True, text=True, check=True
        ).stdout.strip()

    def test_two_task_fixture_bank_workspaces_have_no_fix_history_and_strip_leakage(self):
        self.assertEqual(len(self.tasks), 2)
        parents = [self.parent1, self.fix1]
        fixes = [self.fix1, self.fix2]

        for idx, base_task in enumerate(self.tasks):
            task = workspace.TaskSpec.from_dict(
                {
                    "id": base_task.id,
                    "parent_commit": parents[idx],
                    "test_file": base_task.test_file,
                    "target_node_id": base_task.target_node_id,
                    "twin_node_id": base_task.twin_nodes[0],
                    "test_cmd": base_task.test_cmd,
                    "allowed_paths": base_task.allowed_paths,
                    "baseline": base_task.baseline,
                    "scrubbed_test_path": base_task.scrubbed_test_path,
                    "twin_test_path": base_task.twin_test_path,
                    "design_notes": base_task.design_notes,
                }
            )
            ws_dir = self.tmp / f"ws-{task.id}"
            prep = workspace.build_workspace(self.src_repo, task, ws_dir)

            # GIT_CONFIG_NOSYSTEM=1 and isolated temporary HOME
            self.assertEqual(prep.env["GIT_CONFIG_NOSYSTEM"], "1")
            self.assertTrue(prep.home_dir.is_dir())

            # CHANGELOG.md, docs/runs/, and design notes are absent
            self.assertFalse((ws_dir / "CHANGELOG.md").exists())
            self.assertFalse((ws_dir / "CHANGELOG.old").exists())
            self.assertFalse((ws_dir / "docs" / "runs").exists())
            self.assertFalse((ws_dir / "experiments" / "local-builders" / "DESIGN.md").exists())

            # Scrubbed test is present and hashed in pre_test_hashes
            self.assertTrue((ws_dir / task.test_file).is_file())
            self.assertIn(task.test_file, prep.pre_test_hashes)

            # Only a single commit ("baseline") exists in git log --all, and the fix commit is unreachable
            log_proc = subprocess.run(
                ["git", "log", "--all", "--oneline"],
                cwd=str(ws_dir),
                env=prep.env,
                capture_output=True,
                text=True,
                check=True,
            )
            commits = [line for line in log_proc.stdout.splitlines() if line.strip()]
            self.assertEqual(len(commits), 1)
            self.assertIn("baseline", commits[0])

            cat_proc = subprocess.run(
                ["git", "cat-file", "-t", fixes[idx]],
                cwd=str(ws_dir),
                env=prep.env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(cat_proc.returncode, 0, "fix commit must not exist in workspace git object store")

    def test_workspace_validation_and_error_branches(self):
        self.assertEqual(workspace.normal_rel_path("./a//b/"), "a/b")
        self.assertFalse(workspace.is_test_path(""))
        self.assertTrue(workspace.is_test_path("pkg/foo_test.py"))

        with self.assertRaises(workspace.WorkspaceError):
            workspace.validate_allowed_paths(["tests/test_abmine.py"])
        with self.assertRaises(workspace.WorkspaceError):
            workspace.validate_allowed_paths(["tests/**"])
        with self.assertRaises(workspace.WorkspaceError):
            workspace.validate_allowed_paths(["conftest.py"])
        with self.assertRaises(workspace.WorkspaceError):
            workspace.validate_allowed_paths([])

        for bad_dict in (
            {},
            {"id": "t"},
            {"id": "t", "parent_commit": "abc", "test_file": "src/main.py"},
            {"id": "t", "parent_commit": "abc", "test_file": "tests/test_x.py"},
            {"id": "t", "parent_commit": "abc", "test_file": "tests/test_x.py", "target_node_id": "tests/test_x.py::t"},
            {
                "id": "t",
                "parent_commit": "abc",
                "test_file": "tests/test_x.py",
                "target_node_id": "tests/test_x.py::t",
                "twin_node_id": "tests/test_t.py::t",
                "allowed_paths": ["src/a.py"],
                "baseline": {"passed": 1},
            },
        ):
            with self.assertRaises(workspace.WorkspaceError):
                workspace.TaskSpec.from_dict(bad_dict)

        spec_inline = workspace.TaskSpec.from_dict(
            {
                "id": "inline",
                "parent_commit": self.parent1,
                "test_file": "tests/test_in.py",
                "target_node_id": "tests/test_in.py::t",
                "twin_node_id": "tests/test_tw.py::t",
                "allowed_paths": ["mcptoolshop_rnd/abmine.py"],
                "baseline": {"passed": 1, "skipped": 0, "xfail": 0},
                "scrubbed_test_content": "def test_in(): pass\n",
                "twin_test_content": "def test_tw(): pass\n",
            }
        )
        self.assertEqual(spec_inline.read_scrubbed_test(), "def test_in(): pass\n")
        self.assertEqual(spec_inline.read_twin_test(), "def test_tw(): pass\n")

        spec_missing = workspace.TaskSpec.from_dict(
            {
                "id": "missing",
                "parent_commit": self.parent1,
                "test_file": "tests/test_in.py",
                "target_node_id": "tests/test_in.py::t",
                "twin_node_id": "tests/test_tw.py::t",
                "allowed_paths": ["mcptoolshop_rnd/abmine.py"],
                "baseline": {"passed": 1, "skipped": 0, "xfail": 0},
            }
        )
        with self.assertRaises(workspace.WorkspaceError):
            spec_missing.read_scrubbed_test()
        with self.assertRaises(workspace.WorkspaceError):
            spec_missing.read_twin_test()

        empty_bank = self.tmp / "empty_bank.json"
        empty_bank.write_text('{"tasks": []}', encoding="utf-8")
        with self.assertRaises(workspace.WorkspaceError):
            workspace.load_task_bank(empty_bank)

        # Non-empty dest_dir and bad commit errors
        non_empty = self.tmp / "non_empty"
        non_empty.mkdir()
        (non_empty / "f").write_text("x", encoding="utf-8")
        with self.assertRaises(workspace.WorkspaceError):
            workspace.build_workspace(self.src_repo, spec_inline, non_empty)

        bad_commit_spec = workspace.TaskSpec.from_dict(
            {
                "id": "badsha",
                "parent_commit": "deadbeef" * 5,
                "test_file": "tests/test_in.py",
                "target_node_id": "tests/test_in.py::t",
                "twin_node_id": "tests/test_tw.py::t",
                "allowed_paths": ["mcptoolshop_rnd/abmine.py"],
                "baseline": {"passed": 1, "skipped": 0, "xfail": 0},
                "scrubbed_test_content": "pass\n",
            }
        )
        with self.assertRaises(workspace.WorkspaceError):
            workspace.build_workspace(self.src_repo, bad_commit_spec, self.tmp / "ws_bad")


class ContainmentAndProbeTests(unittest.TestCase):
    """Tests for `contain.py` and `probe.py` with injected success and failure for every check (F9, section 8)."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.paths = probe.ProbePaths(
            workspace_dir=self.tmp / "ws",
            outside_dir=self.tmp / "outside",
            bank_dir=self.tmp / "bank",
            twins_dir=self.tmp / "twins",
            receipts_dir=self.tmp / "receipts",
            llama_port=18081,
        )
        self.paths.workspace_dir.mkdir(parents=True, exist_ok=True)
        self.paths.outside_dir.mkdir(parents=True, exist_ok=True)
        self.paths.bank_dir.mkdir(parents=True, exist_ok=True)
        self.paths.twins_dir.mkdir(parents=True, exist_ok=True)
        self.paths.receipts_dir.mkdir(parents=True, exist_ok=True)
        (self.paths.bank_dir / "b.json").write_text("{}", encoding="utf-8")

    def test_probe_passes_when_every_check_is_refused(self):
        all_refused = {name: False for name in probe.CHECK_NAMES}
        report = probe.run_probe(self.paths, injected_attempts=all_refused)
        self.assertTrue(report["passed"])
        self.assertEqual(report["breaches"], [])
        for name in probe.CHECK_NAMES:
            self.assertTrue(report["checks"][name]["refused"])

    def test_probe_fails_if_any_single_check_succeeds(self):
        self.assertEqual(len(probe.CHECK_NAMES), 10)
        for breaching_check in probe.CHECK_NAMES:
            with self.subTest(check=breaching_check):
                attempts = {name: False for name in probe.CHECK_NAMES}
                attempts[breaching_check] = True
                report = probe.run_probe(self.paths, injected_attempts=attempts)
                self.assertFalse(report["passed"], f"probe must fail when {breaching_check} succeeds")
                self.assertEqual(report["breaches"], [breaching_check])
                self.assertFalse(report["checks"][breaching_check]["refused"])

    def test_probe_default_attempts_both_refused_and_breached(self):
        # 1. All refused via mocked primitives
        with (
            mock.patch.dict(
                os.environ,
                {"HTTP_PROXY": "http://127.0.0.1:9", "HTTPS_PROXY": "http://127.0.0.1:9", "http_proxy": "x", "https_proxy": "y"},
            ),
            mock.patch.object(
                probe.subprocess,
                "run",
                return_value=subprocess.CompletedProcess(args=[], returncode=1, stdout="", stderr="blocked"),
            ),
            mock.patch.object(probe.socket, "create_connection", side_effect=OSError("network unreachable")),
            mock.patch.object(probe.socket, "getaddrinfo", side_effect=socket.gaierror("DNS blocked")),
            mock.patch.object(probe.os, "listdir", side_effect=PermissionError("0700 denied")),
            mock.patch.object(Path, "write_text", side_effect=PermissionError("read-only outside workspace")),
        ):
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                rc = probe.main(
                    [
                        "--workspace",
                        str(self.paths.workspace_dir),
                        "--outside",
                        str(self.paths.outside_dir),
                        "--bank",
                        str(self.paths.bank_dir),
                        "--twins",
                        str(self.paths.twins_dir),
                        "--receipts",
                        str(self.paths.receipts_dir),
                    ]
                )
            self.assertEqual(rc, 0)

        # 2. All breached via mocked primitives to cover every breach branch
        with (
            mock.patch.object(
                probe.subprocess,
                "run",
                return_value=subprocess.CompletedProcess(args=[], returncode=0, stdout="ok", stderr=""),
            ),
            mock.patch.object(probe.socket, "create_connection", side_effect=lambda *a, **kw: io.BytesIO()),
            mock.patch.object(probe.socket, "getaddrinfo", return_value=[(None, None, None, None, ("93.184.216.34", 443))]),
        ):
            rep_breach = probe.run_probe(self.paths)
            self.assertFalse(rep_breach["passed"])
            self.assertEqual(len(rep_breach["breaches"]), 10)

        # Callable variations in _evaluate_attempt and unknown check error
        self.assertEqual(probe._evaluate_attempt(lambda p: (_ for _ in ()).throw(OSError("no")), self.paths)[0], True)
        self.assertEqual(probe._evaluate_attempt(lambda p: False, self.paths)[0], True)
        self.assertEqual(probe._evaluate_attempt(lambda p: None, self.paths)[0], False)
        with self.assertRaises(ValueError):
            probe.run_probe(self.paths, injected_attempts={"not_a_check": False})

    def test_contain_iptables_rules_env_and_drive_mount_check(self):
        rules = contain.iptables_commands(builder_user="builder", proxy_port=18080, llama_port=18081)
        flat = [" ".join(r) for r in rules]
        self.assertTrue(any("--dport 18080 -m owner --uid-owner builder -j ACCEPT" in r for r in flat))
        self.assertTrue(any("--dport 18081 -m owner --uid-owner builder -j REJECT" in r for r in flat))
        self.assertTrue(any("--dport 53 -m owner --uid-owner builder -j REJECT" in r for r in flat))
        self.assertTrue(any("ip6tables -A OUTPUT -m owner --uid-owner builder -j REJECT" in r for r in flat))
        self.assertEqual(contain.wrap_as_builder(["echo"], use_sudo=False), ["echo"])

        with self.assertRaises(contain.ContainmentError):
            contain.iptables_commands(proxy_port=18080, llama_port=18080)

        env = contain.builder_env(proxy_port=18080, home_dir=self.tmp / "home")
        self.assertEqual(env["OPENAI_API_BASE"], "http://127.0.0.1:18080/v1")
        self.assertEqual(env["OPENAI_API_KEY"], "local")
        self.assertEqual(env["LITELLM_LOCAL_MODEL_COST_MAP"], "True")
        self.assertEqual(env["PIP_NO_INDEX"], "1")
        self.assertEqual(env["NPM_CONFIG_OFFLINE"], "true")
        self.assertEqual(env["GIT_CONFIG_NOSYSTEM"], "1")

        # Drive mount checks (both /proc/mounts and non-empty directory)
        ok, _ = contain.check_no_drive_mount(mounts_text=None, drive_paths=())
        self.assertTrue(ok)
        fake_drive = self.tmp / "drive"
        fake_drive.mkdir()
        (fake_drive / "file.txt").write_text("x", encoding="utf-8")
        ok_dir, why_dir = contain.check_no_drive_mount(mounts_text="", drive_paths=(fake_drive,))
        self.assertFalse(ok_dir)
        self.assertIn("non-empty", why_dir)

        cfg = contain.ContainmentConfig(
            bank_dir=self.paths.bank_dir,
            twins_dir=self.paths.twins_dir,
            receipts_dir=self.paths.receipts_dir,
        )
        with self.assertRaises(contain.ContainmentError):
            contain.apply_vm_containment(cfg, mounts_text="drive /content/drive fuse.drive rw 0 0\n")

        # Useradd path when `id -u` returns non-zero
        def run_need_useradd(c):
            if c[0] == "id":
                return subprocess.CompletedProcess(c, 1, "", "no user")
            return subprocess.CompletedProcess(c, 0, "", "")

        applied = contain.apply_vm_containment(cfg, run_cmd=run_need_useradd, mounts_text="", drive_paths=())
        self.assertEqual(applied["iptables_rules_applied"], 6)

        with self.assertRaises(contain.ContainmentError):
            contain.apply_vm_containment(
                cfg,
                run_cmd=lambda c: subprocess.CompletedProcess(c, 1, "", "fail"),
                mounts_text="",
                drive_paths=(),
            )
        with self.assertRaises(contain.ContainmentError):
            contain.apply_vm_containment(
                cfg,
                run_cmd=lambda c: subprocess.CompletedProcess(c, 0 if c[0] == "id" else 1, "", "iptables err"),
                mounts_text="",
                drive_paths=(),
            )


class PreflightTests(unittest.TestCase):
    """Tests for `mcptoolshop_rnd.localbuilders.preflight` (F5, F6, F13, amendment B item 4)."""

    def test_f13_context_computation_from_30_call_validation_run(self):
        self.assertEqual(preflight.next_power_of_two(0), 1)
        with self.assertRaises(preflight.PreflightError):
            preflight.compute_j2_context([{"kind": "result", "prompt_tokens": 1000, "output_tokens": 500}] * 10)
        with self.assertRaises(preflight.PreflightError):
            preflight.compute_j2_context([], require_full_cap=False)
        with self.assertRaises(preflight.PreflightError):
            preflight.compute_j2_context([{"kind": "result", "prompt_eval_count": 0, "eval_count": 0}], require_full_cap=False)

        calls_small = [{"kind": "result", "prompt_eval_count": 8000, "eval_count": 2000}] * 30
        self.assertEqual(preflight.compute_j2_context(calls_small), 32768)

        calls_large = list(calls_small)
        calls_large[-1] = {"kind": "result", "prompt_tokens": 24000, "output_tokens": 4000}
        self.assertEqual(preflight.compute_j2_context(calls_large), 65536)

    def test_f5_top_5_logprobs_assertion_from_index_1_on(self):
        resp = _canned_llama_response(steps=5)
        self.assertEqual(preflight.assert_top_logprobs(resp), 4)
        self.assertEqual(
            preflight.assert_top_logprobs({"top": [[["a", -0.1]] * 5, [{"token": "b", "logprob": -0.2}] * 5]}),
            1,
        )
        self.assertEqual(
            preflight.assert_top_logprobs([[["a", -0.1]] * 5, [["b", -0.2]] * 5]),
            1,
        )

        with self.assertRaises(preflight.PreflightError):
            preflight.assert_top_logprobs("not-a-list")
        with self.assertRaises(preflight.PreflightError):
            preflight.assert_top_logprobs([[["a", -0.1]] * 5])
        with self.assertRaises(preflight.PreflightError):
            preflight.assert_top_logprobs([[["a", -0.1]] * 5, ["bad-cand"] * 5])
        with self.assertRaises(preflight.PreflightError):
            preflight.assert_top_logprobs([[["a", -0.1]] * 5, [["b", float("inf")]] * 5])

        bad_resp = _canned_llama_response(steps=4)
        bad_resp["choices"][0]["logprobs"]["content"][2]["top_logprobs"] = _make_five_top("x", 2)[:3]
        with self.assertRaises(preflight.PreflightError):
            preflight.assert_top_logprobs(bad_resp)

    def test_f6_and_amendment_b_fit_report_and_cli(self):
        log_pair_only = "llama_kv_cache_init: K (f16): 1600.00 MiB, V (f16): 1600.00 MiB\n"

        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            gguf_file = tmp / "model.gguf"
            gguf_file.write_bytes(b"0" * 1024)

            rep = preflight.evaluate_candidate_fit(
                arm="nemotron-3.5-lightning-30b-a3b",
                quant="Q8_0",
                context_length=32768,
                top_or_response=_canned_llama_response(steps=3),
                gguf_path=gguf_file,
                server_log=log_pair_only,
                peak_vram_mib=42500.0,
            )
            self.assertFalse(rep["fits_a100"])
            self.assertTrue(rep["flagged_for_q6_k"])
            self.assertEqual(rep["arm_label"], "[Q6_K: A100 fit]")

            # CLI main test (never exits non-zero on fit)
            in_json = tmp / "in.json"
            out_json = tmp / "out.json"
            in_json.write_text(
                json.dumps(
                    {
                        "arm": "qwen3.8-27b",
                        "quant": "Q8_0",
                        "validation_calls": [{"kind": "result", "prompt_tokens": 5000, "output_tokens": 1000}] * 30,
                        "probe_response": _canned_llama_response(steps=3),
                        "gguf_size_mib": 27200.0,
                        "kv_cache_mib": 3200.0,
                        "peak_vram_mib": 31000.0,
                    }
                ),
                encoding="utf-8",
            )
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = preflight.main(["--input", str(in_json), "--output", str(out_json)])
            self.assertEqual(rc, 0)
            self.assertTrue(out_json.is_file())

            # Validation error branches
            with self.assertRaises(preflight.PreflightError):
                preflight.evaluate_candidate_fit(
                    arm="m", quant="Q8_0", context_length=16384, top_or_response=_canned_llama_response(steps=3)
                )
            with self.assertRaises(preflight.PreflightError):
                preflight.evaluate_candidate_fit(
                    arm="m",
                    quant="Q8_0",
                    context_length=32768,
                    top_or_response=_canned_llama_response(steps=3),
                    gguf_path=tmp / "missing.gguf",
                )
            with self.assertRaises(preflight.PreflightError):
                preflight.evaluate_candidate_fit(
                    arm="m", quant="Q8_0", context_length=32768, top_or_response=_canned_llama_response(steps=3)
                )
            with self.assertRaises(preflight.PreflightError):
                preflight.evaluate_candidate_fit(
                    arm="m",
                    quant="Q8_0",
                    context_length=32768,
                    top_or_response=_canned_llama_response(steps=3),
                    gguf_size_mib=100.0,
                )
            with self.assertRaises(preflight.PreflightError):
                preflight.evaluate_candidate_fit(
                    arm="m",
                    quant="Q8_0",
                    context_length=32768,
                    top_or_response=_canned_llama_response(steps=3),
                    gguf_size_mib=100.0,
                    kv_cache_mib=50.0,
                )


class RunnerAndReceiptTests(unittest.TestCase):
    """Tests for `mcptoolshop_rnd.localbuilders.runner` (NB1, F2, F4, F7, F9, F10, section 7)."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.task = workspace.load_task_bank(BANK_JSON)[0]

    def test_builds_exact_aider_command_line_and_refuses_editable_test_files(self):
        with self.assertRaises(runner.RunnerError):
            runner.format_task_prompt("  ")
        with self.assertRaises(runner.RunnerError):
            runner.build_aider_argv(
                served_as="m",
                model_settings_file="s",
                test_cmd="pytest",
                test_file="mcptoolshop_rnd/abmine.py",
                node_id="n",
                llm_history_file="h",
                analytics_log="a",
            )

        argv = runner.build_aider_argv(
            served_as="qwen3.8-27b",
            model_settings_file="/pins/aider-settings.yml",
            test_cmd=self.task.test_cmd,
            test_file=self.task.test_file,
            node_id=self.task.target_node_id,
            llm_history_file="/work/llm-history.md",
            analytics_log="/work/analytics.jsonl",
            editable_files=["", "mcptoolshop_rnd/abmine.py"],
        )
        for flag in (
            "--no-stream",
            "--auto-test",
            "--no-auto-commits",
            "--yes-always",
            "--no-check-update",
            "--analytics-disable",
            "--no-suggest-shell-commands",
        ):
            self.assertIn(flag, argv)

        def flag_value(flag: str) -> str:
            idx = argv.index(flag)
            return argv[idx + 1]

        self.assertEqual(flag_value("--model"), "openai/qwen3.8-27b")
        self.assertEqual(flag_value("--edit-format"), "diff")
        self.assertEqual(flag_value("--model-settings-file"), "/pins/aider-settings.yml")
        self.assertEqual(flag_value("--test-cmd"), self.task.test_cmd)
        self.assertEqual(flag_value("--llm-history-file"), "/work/llm-history.md")
        self.assertEqual(flag_value("--analytics-log"), "/work/analytics.jsonl")
        self.assertEqual(flag_value("--read"), "tests/test_abmine_fa.py")
        self.assertEqual(
            flag_value("--message"),
            f"The test {self.task.target_node_id} fails. Make it pass. Don't change any test file.",
        )
        self.assertEqual(argv[-1], "mcptoolshop_rnd/abmine.py")

        with self.assertRaises(runner.RunnerError):
            runner.build_aider_argv(
                served_as="qwen3.8-27b",
                model_settings_file="/pins/aider-settings.yml",
                test_cmd=self.task.test_cmd,
                test_file=self.task.test_file,
                node_id=self.task.target_node_id,
                llm_history_file="/work/llm-history.md",
                analytics_log="/work/analytics.jsonl",
                editable_files=["tests/test_abmine_fa.py"],
            )

        full_cmd = runner.build_aider_command(
            served_as="qwen3.8-27b",
            model_settings_file="/pins/aider-settings.yml",
            test_cmd=self.task.test_cmd,
            test_file=self.task.test_file,
            node_id=self.task.target_node_id,
            llm_history_file="/work/llm-history.md",
            analytics_log="/work/analytics.jsonl",
            editable_files=["mcptoolshop_rnd/abmine.py"],
            use_sudo=True,
        )
        self.assertEqual(full_cmd[:4], ["sudo", "-u", "builder", "-n"])
        self.assertIn("--aider-entrypoint", full_cmd)
        idx_mr = full_cmd.index("--max-reflections")
        self.assertEqual(full_cmd[idx_mr + 1], "29")

    def test_nb1_coder_create_wrapper_and_main_entrypoint(self):
        created_coders = []

        class FakeCoder:
            max_reflections = 3

            @classmethod
            def create(cls, *args, **kwargs):
                inst = cls()
                created_coders.append(inst)
                return inst

        def fake_aider_main(argv):
            coder = FakeCoder.create(argv=argv)
            self.assertEqual(coder.max_reflections, 29)
            return 0

        rc = runner.run_aider_entrypoint(
            ["--model", "openai/m", "--no-stream"],
            max_reflections=29,
            coder_cls=FakeCoder,
            aider_main=fake_aider_main,
        )
        self.assertEqual(rc, 0)
        self.assertEqual(len(created_coders), 1)
        self.assertEqual(created_coders[0].max_reflections, 29)

        with mock.patch.object(runner, "run_aider_entrypoint", return_value=0) as mocked_ep:
            self.assertEqual(
                runner.main(["--aider-entrypoint", "--max-reflections", "29", "--ignored", "--", "--model", "openai/m"]),
                0,
            )
            mocked_ep.assert_called_once_with(["--model", "openai/m"], max_reflections=29)

        with self.assertRaises(runner.RunnerError):
            runner.main([])

    def test_analytics_log_and_end_to_end_single_task_receipt(self):
        # Build a small local git repo so run_single_task is fast
        mini_repo = self.tmp / "mini_repo"
        (mini_repo / "mcptoolshop_rnd").mkdir(parents=True)
        (mini_repo / "mcptoolshop_rnd" / "abmine.py").write_text("x = 1\n", encoding="utf-8")
        env = workspace.git_env(self.tmp / "ghome")
        subprocess.run(["git", "init", "-q"], cwd=str(mini_repo), env=env, check=True)
        subprocess.run(["git", "config", "user.name", "t"], cwd=str(mini_repo), env=env, check=True)
        subprocess.run(["git", "config", "user.email", "t@localhost"], cwd=str(mini_repo), env=env, check=True)
        subprocess.run(["git", "add", "-A"], cwd=str(mini_repo), env=env, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "p"], cwd=str(mini_repo), env=env, check=True)
        parent_sha = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=str(mini_repo), env=env, capture_output=True, text=True, check=True
        ).stdout.strip()

        task = workspace.TaskSpec.from_dict(
            {
                "id": "mini-task",
                "parent_commit": parent_sha,
                "test_file": self.task.test_file,
                "target_node_id": self.task.target_node_id,
                "twin_node_id": self.task.twin_nodes[0],
                "test_cmd": self.task.test_cmd,
                "allowed_paths": ["mcptoolshop_rnd/abmine.py"],
                "baseline": self.task.baseline,
                "scrubbed_test_path": self.task.scrubbed_test_path,
                "twin_test_path": self.task.twin_test_path,
            }
        )

        with _StubLlamaServer() as stub:
            receipt_path = self.tmp / "receipts" / "r1.json"
            settings_file = self.tmp / "model-settings.yml"
            settings_file.write_text("- name: openai/fixture-candidate-q8_0\n  streaming: false\n", encoding="utf-8")

            run_cfg = runner.RunTaskConfig(
                source_repo=mini_repo,
                task=task,
                candidate_config_path=CANDIDATE_CONFIG_JSON,
                model_settings_file=settings_file,
                served_as="fixture-candidate-q8_0",
                model_tag="qwen3.8:27b-q8_0",
                model_digest="sha256:aaee06c39dcf",
                aider_version="0.82.0",
                upstream_url=stub.url,
                work_root=self.tmp / "work",
                receipt_path=receipt_path,
                machine_line={"gpu": "NVIDIA A100-SXM4-40GB"},
            )

            def fake_aider_runner(cmd: list[str], ws_dir: Path, run_env: dict[str, str]) -> int:
                api_base = run_env["OPENAI_API_BASE"]
                _post_json(f"{api_base}/chat/completions", {"messages": [{"role": "user", "content": "turn 1"}]})
                _post_json(f"{api_base}/chat/completions", {"messages": [{"role": "user", "content": "turn 2"}]})
                # Write analytics events to cover parse_analytics_log
                alog = run_cfg.work_root / f"analytics-{task.id}.jsonl"
                alog.write_text(
                    "\n".join(
                        [
                            "",
                            "{bad",
                            "[]",
                            json.dumps({"event": "message_send", "properties": {"num_malformed_responses": 1}}),
                            json.dumps({"event": "edit_failed", "properties": {"failed": True}}),
                            json.dumps({"event": "auto_test_reflection", "properties": {}}),
                        ]
                    )
                    + "\n",
                    encoding="utf-8",
                )
                return 0

            receipt = runner.run_single_task(
                run_cfg,
                aider_runner=fake_aider_runner,
                scorer_fn=lambda t, p: {"task_id": t.id, "passed": True, "correct": True, "reasons": []},
            )

        self.assertEqual(receipt["tool_calls"], {"total": 2, "malformed": 1, "failed": 1})
        self.assertEqual(receipt["retries"], 1)

        # Receipt validation errors
        for bad_mod in (
            lambda r: r.pop("task_id"),
            lambda r: r.update({"generations_sha256": "short"}),
            lambda r: r.update({"injected": "not-dict"}),
            lambda r: r.update({"injected": {"sampling": {}}} ),
            lambda r: r.update({"cap_hits": "not-dict"}),
        ):
            copy_r = json.loads(json.dumps(receipt))
            bad_mod(copy_r)
            with self.assertRaises(runner.RunnerError):
                runner.validate_receipt(copy_r)


if __name__ == "__main__":
    unittest.main()
