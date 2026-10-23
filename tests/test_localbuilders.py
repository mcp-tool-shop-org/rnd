"""Unit tests for `mcptoolshop_rnd.localbuilders` (J2 harness and logging proxy, amendments C, D, E).

All tests are `unittest.TestCase` classes with no GPU and no external network:
- ProxyTests: against a local `http.server` stub llama-server returning canned responses
  (F1, F3, F4, F5, D1 every sampling key on every call, D2/E1-E3 `fold_system` and `reattach_thinking`
  transforms, late wall-cap result-before-refusal logging, `thinking_words_estimate`)
- ScorerTests: canned JUnit XML and workspace fixtures for pass and every refusal kind, exact
  `file::name` node matching, `SCORER_IGNORED_PATTERNS`, builder containment in `run_pytest_and_score`,
  and `score_timeout` handling (F9, F10, NB2)
- WorkspaceTests: 2-task fixture bank from repo history; no git history reaches the fix;
  `docs/runs/`, `CHANGELOG.md`, and design notes removed; `GIT_CONFIG_NOSYSTEM=1` (F7, F9)
- ContainmentAndProbeTests: iptables `-I OUTPUT 1` reverse-order rules, `iptables -S OUTPUT`,
  `wrap_as_builder` `env -i K=V ...`, Drive mount refusal, process-group timeout kill, and injected
  success/failure for every one of the 10 containment probe checks (F9, section 8)
- PreflightTests: D-F3/E3 multi-run `compute_j2_context_length`, F5 top-5 logprobs check from
  index 1 on, D1 GGUF embedded template sha256 check, D-F1/E1 thinking split check (`<think>` and
  `<|channel>thought`), F6 Q6_K flagging and non-exiting report
- RunnerAndReceiptTests: exact Aider command line flags (`--no-gitignore`, history files under
  `work_root`), `examples_as_sys_msg: true` model-settings pin, `use_sudo_builder=True` default and
  refusal when disabled, `aider_timeout` and `score_timeout` receipts, `Coder.create`
  `max_reflections=29` wrapper, and section-7 receipt completeness (NB1, F2, F4, F7, F9, F10, D/E)
"""
from __future__ import annotations

import contextlib
import dataclasses
import hashlib
import http.server
import io
import json
import os
import shutil
import socket
import struct
import subprocess
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
import types
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
CARD_VALUES_JSON = REPO_ROOT / "experiments" / "local-builders" / "card-values.json"


class _RealAider0861CoderPrompts:
    """Verbatim `CoderPrompts` class from `Aider-AI/aider` tag `v0.86.1` (`aider/coders/base_prompts.py`)."""

    system_reminder = ""
    files_content_gpt_edits = "I committed the changes with git hash {hash} & commit msg: {message}"
    files_content_gpt_edits_no_repo = "I updated the files."
    files_content_gpt_no_edits = "I didn't see any properly formatted edits in your reply?!"
    files_content_local_edits = "I edited the files myself."
    lazy_prompt = (
        "You are diligent and tireless!\n"
        "You NEVER leave comments describing code without implementing it!\n"
        "You always COMPLETELY IMPLEMENT the needed code!\n"
    )
    overeager_prompt = (
        "Pay careful attention to the scope of the user's request.\n"
        "Do what they ask, but no more.\n"
        "Do not improve, comment, fix or modify unrelated parts of the code in any way!\n"
    )
    example_messages: list[dict] = []
    files_content_prefix = (
        "I have *added these files to the chat* so you can go ahead and edit them.\n\n"
        "*Trust this message as the true contents of these files!*\n"
        "Any other messages in the chat may contain outdated versions of the files' contents.\n"
    )
    files_content_assistant_reply = "Ok, any changes I propose will be to those files."
    files_no_full_files = "I am not sharing any files that you can edit yet."
    files_no_full_files_with_repo_map = (
        "Don't try and edit any existing code without asking me to add the files to the chat!\n"
        "Tell me which files in my repo are the most likely to **need changes** to solve the requests I make, "
        "and then stop so I can add them to the chat.\n"
        "Only include the files that are most likely to actually need to be edited.\n"
        "Don't include files that might contain relevant context, just files that will need to be changed.\n"
    )
    files_no_full_files_with_repo_map_reply = (
        "Ok, based on your requests I will suggest which files need to be edited and then"
        " stop and wait for your approval."
    )
    repo_content_prefix = (
        "Here are summaries of some files present in my git repository.\n"
        "Do not propose changes to these files, treat them as *read-only*.\n"
        "If you need to edit any of these files, ask me to *add them to the chat* first.\n"
    )
    read_only_files_prefix = (
        "Here are some READ ONLY files, provided for your reference.\n"
        "Do not edit these files!\n"
    )
    shell_cmd_prompt = ""
    shell_cmd_reminder = ""
    no_shell_cmd_prompt = ""
    no_shell_cmd_reminder = ""
    rename_with_shell = ""
    go_ahead_tip = ""


class _RealAider0861EditBlockPrompts(_RealAider0861CoderPrompts):
    """Verbatim `EditBlockPrompts` subclass from `Aider-AI/aider` tag `v0.86.1` (`aider/coders/editblock_prompts.py`)."""

    main_system = "Act as an expert software developer.\n"
    system_reminder = "# *SEARCH/REPLACE block* Rules:\n"


@contextlib.contextmanager
def _mock_installed_aider(
    version: str = proxy.PINNED_AIDER_VERSION,
    coder_prompts_cls: type = _RealAider0861CoderPrompts,
    editblock_prompts_cls: type = _RealAider0861EditBlockPrompts,
):
    """Provide `aider`, `aider.coders.base_prompts`, and `aider.coders.editblock_prompts` with the version gate mocked."""
    aider_mod = types.ModuleType("aider")
    aider_mod.__version__ = version  # type: ignore[attr-defined]
    coders_mod = types.ModuleType("aider.coders")
    base_prompts_mod = types.ModuleType("aider.coders.base_prompts")
    base_prompts_mod.CoderPrompts = coder_prompts_cls  # type: ignore[attr-defined]
    editblock_prompts_mod = types.ModuleType("aider.coders.editblock_prompts")
    editblock_prompts_mod.EditBlockPrompts = editblock_prompts_cls  # type: ignore[attr-defined]

    with (
        mock.patch.dict(
            sys.modules,
            {
                "aider": aider_mod,
                "aider.coders": coders_mod,
                "aider.coders.base_prompts": base_prompts_mod,
                "aider.coders.editblock_prompts": editblock_prompts_mod,
            },
        ),
        mock.patch.object(preflight, "get_installed_aider_version", return_value=version),
        mock.patch.object(runner.shutil, "chown", return_value=None),
    ):
        yield


def _make_five_top(prefix: str, step: int) -> list[dict]:
    return [
        {"token": f"{prefix}{step}_c{i}", "logprob": round(-0.1 * (i + 1), 4)}
        for i in range(5)
    ]


def _canned_llama_response(
    *,
    content: str = "Fixed the bug.",
    reasoning_content: str | None = "Let me inspect the function first.",
    finish_reason: str = "stop",
    steps: int = 4,
    prompt_tokens: int = 120,
    completion_tokens: int = 18,
    reasoning_tokens: int | None = 10,
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
    usage: dict = {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": prompt_tokens + completion_tokens,
    }
    if reasoning_tokens is not None:
        usage["completion_tokens_details"] = {"reasoning_tokens": reasoning_tokens}
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
        "usage": usage,
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
    """Tests for `mcptoolshop_rnd.localbuilders.proxy` (F1, F3, F4, F5, D1, D2, E1-E3)."""

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
                        "stream": True,
                        "temperature": 0.0,
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

        self.assertIs(sent_up["stream"], False)
        self.assertEqual(sent_up["temperature"], 0.6)
        self.assertEqual(sent_up["top_p"], 0.95)
        self.assertEqual(sent_up["top_k"], 20)
        self.assertEqual(sent_up["min_p"], 0.0)
        self.assertEqual(sent_up["chat_template_kwargs"], {"enable_thinking": True})
        self.assertIs(sent_up["logprobs"], True)
        self.assertEqual(sent_up["top_logprobs"], 5)

        choice0 = reply["choices"][0]
        self.assertNotIn("logprobs", choice0)
        self.assertNotIn("reasoning_content", choice0)
        self.assertNotIn("reasoning_content", choice0["message"])
        self.assertNotIn("logprobs", choice0["message"])
        self.assertEqual(choice0["message"]["content"], "Fixed the bug.")

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
        self.assertIsNone(rec["thinking_words_estimate"])
        self.assertEqual(rec["output_tokens"], 18)
        self.assertEqual(rec["prompt_tokens"], 120)
        self.assertFalse(rec["truncated"])
        self.assertEqual(rec["transforms"], [])
        self.assertIsNone(rec["reattach_max_turns"])
        self.assertEqual(
            rec["injected"],
            {
                "sampling": {"temperature": 0.6, "top_p": 0.95, "top_k": 20, "min_p": 0.0},
                "chat_template_kwargs": {"enable_thinking": True},
                "transforms": [],
                "reattach_max_turns": None,
            },
        )

        loaded = abmine.load_record_file(self.gen_path)
        self.assertIn("fixture-candidate-q8_0", loaded)
        gen0 = loaded["fixture-candidate-q8_0"][0]
        self.assertEqual(gen0.tokens, ["tok0_c0", "tok1_c0", "tok2_c0", "tok3_c0"])
        self.assertEqual(len(gen0.top[1]), 5)

    def test_d1_every_sampling_key_sent_on_every_call_from_card_values_json(self):
        """D1: Stub upstream receives every key and value from card-values.json on call 1 and later calls."""
        raw_cards = json.loads(CARD_VALUES_JSON.read_text(encoding="utf-8"))
        granite_entry = next(c for c in raw_cards["candidates"] if c["candidate"] == "granite-4.2-30b")
        expected_sampling = granite_entry["sampling"]

        cfg = proxy.load_candidate_config(CARD_VALUES_JSON, candidate="granite-4.2-30b")
        self.assertEqual(cfg.sampling, expected_sampling)

        with _StubLlamaServer() as stub:
            state = proxy.ProxyState(
                upstream_url=stub.url,
                config=cfg,
                generations_path=self.gen_path,
            )
            with proxy.LoggingProxyServer(state) as srv:
                url = f"{srv.openai_base_url}/chat/completions"
                # First call (Aider sends its own temperature)
                c1, _ = _post_json(
                    url,
                    {
                        "model": "granite-4.2-30b",
                        "temperature": 0.0,
                        "top_k": 99,
                        "min_p": 0.2,
                        "repeat_penalty": 1.2,
                        "presence_penalty": 0.5,
                        "messages": [{"role": "user", "content": "call 1"}],
                    },
                )
                # Later call (Aider omits or changes sampling keys)
                c2, _ = _post_json(
                    url,
                    {
                        "model": "granite-4.2-30b",
                        "temperature": 0.3,
                        "messages": [
                            {"role": "user", "content": "call 1"},
                            {"role": "assistant", "content": "Fixed the bug."},
                            {"role": "user", "content": "call 2"},
                        ],
                    },
                )
                self.assertEqual(c1, 200)
                self.assertEqual(c2, 200)

        self.assertEqual(len(stub.received_requests), 2)
        for call_idx in (0, 1):
            sent = stub.received_requests[call_idx]["body"]
            for k, expected_val in expected_sampling.items():
                self.assertIn(k, sent, f"sampling key {k!r} missing on call {call_idx + 1}")
                self.assertEqual(sent[k], expected_val, f"sampling key {k!r} mismatch on call {call_idx + 1}")
                self.assertIs(type(sent[k]), type(expected_val))

    def test_d2_fold_system_transform_and_empty_transforms(self):
        """D2 & D-F2 / E2: fold_system folds leading system msgs to head of first user and later reminders to tail of preceding user."""
        r1_cfg = proxy.load_candidate_config(CARD_VALUES_JSON, candidate="deepseek-r1-distill-qwen-32b")
        self.assertEqual(r1_cfg.transforms, ("fold_system",))

        canned_messages = [
            {"role": "system", "content": "System prompt part 1."},
            {"role": "system", "content": "Few-shot examples as sys msg."},
            {"role": "user", "content": "Here is the repo map."},
            {"role": "assistant", "content": "Ok."},
            {"role": "user", "content": "The test fails. Make it pass."},
            {"role": "system", "content": "Reminder: format edits as SEARCH/REPLACE."},
        ]

        with _StubLlamaServer() as stub:
            state = proxy.ProxyState(
                upstream_url=stub.url,
                config=r1_cfg,
                generations_path=self.gen_path,
            )
            with proxy.LoggingProxyServer(state) as srv:
                code, _ = _post_json(
                    f"{srv.openai_base_url}/chat/completions",
                    {"messages": canned_messages},
                )
                self.assertEqual(code, 200)

        forwarded = stub.received_requests[0]["body"]["messages"]
        self.assertTrue(all(m["role"] != "system" for m in forwarded))
        self.assertEqual(len(forwarded), 3)
        self.assertEqual(
            forwarded[0],
            {
                "role": "user",
                "content": "System prompt part 1.\n\nFew-shot examples as sys msg.\n\nHere is the repo map.",
            },
        )
        self.assertEqual(forwarded[1], {"role": "assistant", "content": "Ok."})
        self.assertEqual(
            forwarded[2],
            {
                "role": "user",
                "content": "The test fails. Make it pass.\n\nReminder: format edits as SEARCH/REPLACE.",
            },
        )

        # Edge cases for fold_system: system-only messages and empty user content
        only_sys = proxy.apply_fold_system([{"role": "system", "content": "Only sys"}])
        self.assertEqual(only_sys, [{"role": "user", "content": "Only sys"}])
        empty_u = proxy.apply_fold_system(
            [
                {"role": "assistant", "content": "pre"},
                {"role": "system", "content": "sys before user"},
                {"role": "user", "content": ""},
                {"role": "system", "content": "tail"},
            ]
        )
        self.assertTrue(all(m["role"] != "system" for m in empty_u))

        # Empty transforms list leaves messages untouched
        granite_cfg = proxy.load_candidate_config(CARD_VALUES_JSON, candidate="granite-4.2-30b")
        self.assertEqual(granite_cfg.transforms, ())
        untouched_out = proxy.transform_request_body({"messages": canned_messages}, granite_cfg)
        self.assertEqual(untouched_out["messages"], canned_messages)

    def test_f3_client_seed_passes_through_and_card_sampling_still_wins(self):
        """F3: a client's seed reaches upstream (it is not a card value); its other sampling keys are still replaced."""
        cfg = proxy.load_candidate_config(CARD_VALUES_JSON, candidate="granite-4.2-30b")
        self.assertNotIn("seed", cfg.sampling)
        msgs = [{"role": "user", "content": "call"}]
        out = proxy.transform_request_body({"messages": msgs, "seed": 2, "temperature": 0.0, "top_k": 99}, cfg)
        self.assertEqual(out["seed"], 2)
        self.assertEqual(out["temperature"], cfg.sampling["temperature"])
        self.assertEqual(out["top_k"], cfg.sampling["top_k"])
        self.assertNotIn("seed", proxy.transform_request_body({"messages": msgs}, cfg))
        seeded = dataclasses.replace(cfg, sampling={**cfg.sampling, "seed": 7})
        self.assertEqual(proxy.transform_request_body({"messages": msgs, "seed": 2}, seeded)["seed"], 7)

    def test_d2_reattach_thinking_fifo_stripped_synthetic_mismatch_and_max_turns(self):
        """D2, D-F1, D-F3, E1, E3: reattach_thinking handles repeated replies FIFO, stripped fallback, synthetic 'Ok.', edited mismatch, and reattach_max_turns."""
        qwen_cfg = proxy.load_candidate_config(CARD_VALUES_JSON, candidate="qwen3.8-27b")
        self.assertEqual(qwen_cfg.transforms, ("reattach_thinking",))
        self.assertIsNone(qwen_cfg.reattach_max_turns)

        replies = [
            _canned_llama_response(content="Reply A", reasoning_content="Thinking 1 for A"),
            _canned_llama_response(content="Reply A", reasoning_content="Thinking 2 for A (repeated)"),
            _canned_llama_response(content="Reply B  \n", reasoning_content="Thinking 3 for B"),
            _canned_llama_response(content="Final answer", reasoning_content="Thinking 4"),
        ]

        with _StubLlamaServer(response_fn=lambda _b, idx: replies[idx]) as stub:
            state = proxy.ProxyState(
                upstream_url=stub.url,
                config=qwen_cfg,
                generations_path=self.gen_path,
            )
            with proxy.LoggingProxyServer(state) as srv:
                url = f"{srv.openai_base_url}/chat/completions"
                # Calls 1, 2, 3 populate the proxy's logged reasoning map
                _post_json(url, {"messages": [{"role": "user", "content": "u1"}]})
                _post_json(url, {"messages": [{"role": "user", "content": "u2"}]})
                _post_json(url, {"messages": [{"role": "user", "content": "u3"}]})

                # Call 4 sends:
                # - a synthetic "Ok." turn (counted as synthetic, no reasoning)
                # - first "Reply A" (gets "Thinking 1 for A")
                # - second "Reply A" (gets "Thinking 2 for A (repeated)" in FIFO order)
                # - stripped "Reply B" without trailing whitespace (matches via sha256(content.strip()))
                # - an edited assistant turn "Reply edited by Aider" (counted as mismatch, no reasoning)
                c4, _ = _post_json(
                    url,
                    {
                        "messages": [
                            {"role": "user", "content": "Repo map"},
                            {"role": "assistant", "content": "Ok."},
                            {"role": "user", "content": "u1"},
                            {"role": "assistant", "content": "Reply A"},
                            {"role": "user", "content": "u2"},
                            {"role": "assistant", "content": "Reply A"},
                            {"role": "user", "content": "u3"},
                            {"role": "assistant", "content": "Reply B"},
                            {"role": "user", "content": "u4"},
                            {"role": "assistant", "content": "Reply edited by Aider"},
                            {"role": "user", "content": "u5"},
                        ]
                    },
                )
                self.assertEqual(c4, 200)

        sent4 = stub.received_requests[3]["body"]["messages"]
        assistant_msgs = [m for m in sent4 if m["role"] == "assistant"]
        self.assertEqual(len(assistant_msgs), 5)
        # 0: synthetic "Ok." -> no reasoning_content
        self.assertNotIn("reasoning_content", assistant_msgs[0])
        # 1 & 2: repeated "Reply A" -> FIFO thinking 1 then thinking 2
        self.assertEqual(assistant_msgs[1]["reasoning_content"], "Thinking 1 for A")
        self.assertEqual(assistant_msgs[2]["reasoning_content"], "Thinking 2 for A (repeated)")
        # 3: stripped match "Reply B" -> thinking 3
        self.assertEqual(assistant_msgs[3]["reasoning_content"], "Thinking 3 for B")
        # 4: edited turn -> no reasoning_content
        self.assertNotIn("reasoning_content", assistant_msgs[4])

        summary = state.summary()
        self.assertEqual(summary["reattach_thinking"]["reattached"], 3)
        self.assertEqual(summary["reattach_thinking"]["synthetic"], 1)
        self.assertEqual(summary["reattach_thinking"]["mismatch"], 1)

        # Now test reattach_max_turns=2: only the last 2 non-synthetic assistant turns get reasoning attached
        logged = list(state._logged_replies)
        capped_msgs, capped_stats = proxy.apply_reattach_thinking(
            [
                {"role": "assistant", "content": "Ok."},
                {"role": "assistant", "content": "Reply A"},
                {"role": "assistant", "content": "Reply A"},
                {"role": "assistant", "content": "Reply B"},
            ],
            logged,
            reattach_max_turns=2,
        )
        self.assertNotIn("reasoning_content", capped_msgs[0])
        self.assertNotIn("reasoning_content", capped_msgs[1])  # dropped by reattach_max_turns=2
        self.assertEqual(capped_msgs[2]["reasoning_content"], "Thinking 2 for A (repeated)")
        self.assertEqual(capped_msgs[3]["reasoning_content"], "Thinking 3 for B")
        self.assertEqual(capped_stats["reattached"], 2)
        self.assertEqual(capped_stats["synthetic"], 1)
        self.assertEqual(capped_stats["mismatch"], 0)
        self.assertEqual(capped_stats["reattach_max_turns"], 2)

    def test_aider_synthetic_strings_verified_against_pinned_version(self):
        self.assertTrue(
            proxy.verify_aider_synthetic_strings(
                (_RealAider0861CoderPrompts, _RealAider0861EditBlockPrompts),
                aider_version=proxy.PINNED_AIDER_VERSION,
            )
        )
        with self.assertRaises(proxy.ProxyConfigError):
            proxy.verify_aider_synthetic_strings((), aider_version=proxy.PINNED_AIDER_VERSION)
        with self.assertRaises(proxy.ProxyConfigError):
            proxy.verify_aider_synthetic_strings(_RealAider0861CoderPrompts, aider_version="0.0.1")

        class DriftedPrompts(_RealAider0861CoderPrompts):
            files_content_assistant_reply = "Brand new unexpected ack."

        with self.assertRaises(proxy.ProxyConfigError):
            proxy.verify_aider_synthetic_strings(DriftedPrompts, aider_version=proxy.PINNED_AIDER_VERSION)

        with self.assertRaises(proxy.ProxyConfigError):
            proxy.verify_aider_synthetic_strings(object(), aider_version=proxy.PINNED_AIDER_VERSION)

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

    def test_f4_late_wall_cap_logs_result_row_before_refusal_row(self):
        """Item 7: When a call returns after the wall, log the result row first, then the refusal."""
        fake_now = [100.0]

        def clock():
            return fake_now[0]

        def resp_fn(body, idx):
            if idx == 0:
                return _canned_llama_response(finish_reason="length")
            fake_now[0] += 905.0
            return _canned_llama_response(content="Late reply tokens", finish_reason="stop")

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
        rows = [json.loads(line) for line in self.gen_path.read_text(encoding="utf-8").splitlines()]
        # Row 0: call 1 result; Row 1: call 2 completed result; Row 2: call 2 late wall_cap refusal; Row 3: call 3 pre-call wall_cap refusal
        self.assertEqual([r["kind"] for r in rows], ["result", "result", "refused", "refused"])
        self.assertEqual(rows[1]["response"], "Late reply tokens")
        self.assertEqual(rows[2]["reason"], "wall_cap")
        self.assertEqual(rows[2]["call_index"], 2)

        summary = state.summary()
        self.assertTrue(summary["truncated"])
        self.assertEqual(summary["truncated_calls"], 1)
        self.assertEqual(summary["wall_cap_hits"], 2)
        self.assertTrue(summary["cap_hits"]["wall_cap"])

    def test_config_validation_unknown_transform_and_thinking_words_estimate(self):
        with self.assertRaises(proxy.ProxyConfigError):
            proxy.load_candidate_config(self.tmp / "missing.json")
        # Multi-candidate file requires candidate id
        with self.assertRaises(proxy.ProxyConfigError):
            proxy.load_candidate_config(CARD_VALUES_JSON)
        with self.assertRaises(proxy.ProxyConfigError):
            proxy.load_candidate_config(CARD_VALUES_JSON, candidate="nonexistent-model")
        # Single-entry config with wrong candidate id
        with self.assertRaises(proxy.ProxyConfigError):
            proxy.load_candidate_config(CANDIDATE_CONFIG_JSON, candidate="wrong-id")

        single_in_list = self.tmp / "single_in_list.json"
        single_in_list.write_text(
            json.dumps(
                {
                    "candidates": [
                        {
                            "candidate": "only-one",
                            "sampling": {"temperature": 0.5},
                            "chat_template_kwargs": {},
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        self.assertEqual(proxy.load_candidate_config(single_in_list).candidate, "only-one")

        for bad_text in (
            "{bad",
            "[]",
            '{"candidates": []}',
            '{"chat_template_kwargs": {}}',
            '{"sampling": {"temperature": null}, "chat_template_kwargs": {}}',
            '{"sampling": {"temperature": 0.2}}',
            '{"sampling": {"temperature": 0.2}, "chat_template_kwargs": {}, "transforms": "not-list"}',
            '{"sampling": {"temperature": 0.2}, "chat_template_kwargs": {}, "transforms": ["unknown_transform"]}',
            '{"sampling": {"temperature": 0.2}, "chat_template_kwargs": {}, "reattach_max_turns": 0}',
        ):
            p = self.tmp / "bad_cfg.json"
            p.write_text(bad_text, encoding="utf-8")
            with self.assertRaises(proxy.ProxyConfigError):
                proxy.load_candidate_config(p)

        # Fallback logprobs and reasoning shapes
        toks, top = proxy.extract_abmine_logprobs(
            {"logprobs": ["skip", {"token": "a", "top_logprobs": [["a", -0.1], ["b", -1.2]]}]}
        )
        self.assertEqual(toks, ["a"])
        self.assertEqual(top, [[["a", -0.1], ["b", -1.2]]])
        self.assertEqual(proxy._extract_reasoning_and_content({"response": "hi", "reasoning_content": "r"}), ("hi", "r"))
        self.assertEqual(
            proxy._extract_reasoning_and_content({"choices": [{"text": "t", "reasoning_content": "r2"}]}),
            ("t", "r2"),
        )
        self.assertEqual(
            proxy._extract_reasoning_and_content({"choices": [{"message": {"content": "c"}}], "reasoning_content": "r3"}),
            ("c", "r3"),
        )

        p_tok, th_tok, th_words, out_tok = proxy._count_tokens(
            {"timings": {"prompt_n": 15}},
            ["<think>", "step", "</think>", "ans"],
            None,
        )
        self.assertEqual((p_tok, th_tok, th_words, out_tok), (15, 3, None, 4))

        # Item 11: When no token count is available for reasoning_content, thinking_tokens is None and thinking_words_estimate is set
        p_tok2, th_tok2, th_words2, out_tok2 = proxy._count_tokens({}, ["ans"], "one two three")
        self.assertEqual((p_tok2, th_tok2, th_words2, out_tok2), (0, None, 3, 1))

        p_tok3, th_tok3, th_words3, out_tok3 = proxy._count_tokens(
            {"usage": {"reasoning_tokens": 7}}, ["ans"], "one two"
        )
        self.assertEqual((p_tok3, th_tok3, th_words3, out_tok3), (0, 7, None, 1))

        p_tok4, th_tok4, th_words4, out_tok4 = proxy._count_tokens(
            {"timings": {"reasoning_n": 9}}, ["ans"], "one two"
        )
        self.assertEqual((p_tok4, th_tok4, th_words4, out_tok4), (0, 9, None, 1))

        p_tok5, th_tok5, th_words5, out_tok5 = proxy._count_tokens({}, ["ans"], None)
        self.assertEqual((p_tok5, th_tok5, th_words5, out_tok5), (0, 0, None, 1))

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
    """Tests for `mcptoolshop_rnd.localbuilders.score` on canned JUnit XML and workspace fixtures (F9, F10, NB2)."""

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
        include_target: bool = True,
        extra_cases: list[str] | None = None,
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
        for extra in extra_cases or []:
            cases.append(extra)

        def render_node(node_id: str, status: str) -> str:
            inner = ""
            if status == "failure":
                inner = '<failure message="failed"/>'
            elif status == "error":
                inner = '<error message="error"/>'
            elif status == "skipped":
                inner = '<skipped type="pytest.skip" message="skipped in prod"/>'
            return f'<testcase nodeid="{node_id}" name="{node_id.split("::")[-1]}">{inner}</testcase>'

        if include_target:
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

    def test_scorer_ignores_fixed_named_cache_list_and_nothing_else(self):
        """R&D Blocking 1: Scorer ignores only __pycache__/, *.pyc, .pytest_cache/, .aider.tags.cache.v4/."""
        # Create pycache inside tests/ to verify snapshot_test_hashes also ignores it
        (self.ws / "tests" / "__pycache__").mkdir(parents=True)
        (self.ws / "tests" / "__pycache__" / "test_abmine_fa.cpython-310.pyc").write_bytes(b"pyc")

        porcelain_with_ignored_caches = "\n".join(
            [
                " M mcptoolshop_rnd/abmine.py",
                "!! __pycache__/abmine.cpython-310.pyc",
                "!! mcptoolshop_rnd/__pycache__/",
                "!! tests/__pycache__/test_abmine_fa.cpython-310.pyc",
                "!! stray.pyc",
                "!! .pytest_cache/v/cache/nodeids",
                "!! .pytest_cache/",
                "!! .aider.tags.cache.v4/cache.db",
                "!! .aider.tags.cache.v4/",
            ]
        )
        res = score.score_task(
            self.task,
            self.ws,
            self.pre_hashes,
            junit_xml=self._canned_xml(),
            git_status_output=porcelain_with_ignored_caches,
        )
        self.assertTrue(res["passed"], res["reasons"])

        # Any other Aider file left in the repo (.aider.chat.history.md, .gitignore) is NOT ignored
        res_unignored = score.score_task(
            self.task,
            self.ws,
            self.pre_hashes,
            junit_xml=self._canned_xml(),
            git_status_output=porcelain_with_ignored_caches + "\n?? .aider.chat.history.md\n M .gitignore\n",
        )
        self.assertFalse(res_unignored["passed"])
        self.assertTrue(
            any("changed path outside allowed_paths: .aider.chat.history.md" in r for r in res_unignored["reasons"])
        )
        self.assertTrue(
            any("changed path outside allowed_paths: .gitignore" in r for r in res_unignored["reasons"])
        )

    def test_exact_node_matching_refuses_same_named_test_in_second_file(self):
        """R&D Blocking 5: A same-named test in another file or class must never count as the target passing."""
        target_fn_name = self.task.target_nodes[0].split("::")[-1]
        same_named_other_file = (
            f'<testcase file="tests/test_other_file.py" classname="tests.test_other_file" name="{target_fn_name}"/>'
        )
        xml_missing_target = self._canned_xml(
            include_target=False,
            extra_cases=[same_named_other_file],
        )
        res = score.score_task(
            self.task,
            self.ws,
            self.pre_hashes,
            junit_xml=xml_missing_target,
            git_status_output=" M mcptoolshop_rnd/abmine.py\n",
        )
        self.assertFalse(res["passed"])
        self.assertTrue(
            any(f"target test did not pass: {self.task.target_nodes[0]}" in r for r in res["reasons"]),
            res["reasons"],
        )

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

    def test_junit_edge_cases_builder_containment_and_score_timeout(self):
        s = score.parse_junitxml(
            '<testsuite>'
            '<testcase classname="tests.test_m.Cls" name="test_one"/>'
            '<testcase file="tests/test_f.py" classname="OtherPkg.Cls2" name="test_two"/>'
            '<testcase file="tests/test_f.py" classname="test_f" name="test_three"/>'
            '<testcase classname="pkg.Mod.SubCls" name="test_four"/>'
            '<testcase classname="pkg.mod" name="test_five"><xfail/></testcase>'
            '</testsuite>'
        )
        self.assertEqual(s.outcome_for("tests/test_m.py::Cls::test_one"), "passed")
        self.assertIsNone(s.outcome_for("other/path.py::Cls::test_one"))
        self.assertIsNone(s.outcome_for("tests/test_m.py::OtherCls::test_one"))
        self.assertEqual(s.outcome_for("tests/test_f.py::Cls2::test_two"), "passed")
        self.assertEqual(s.outcome_for("tests/test_f.py::test_three"), "passed")
        self.assertEqual(s.outcome_for("pkg/Mod.py::SubCls::test_four"), "passed")
        self.assertEqual(s.outcome_for("pkg/mod.py::test_five"), "xfail")
        self.assertIsNone(s.outcome_for("nonexistent_node"))
        self.assertEqual(s.xfail, 1)
        self.assertEqual(score.parse_git_status_porcelain("\nxx\n M a.py\n"), [(" M", "a.py")])
        self.assertFalse(score.path_is_allowed("", ["mcptoolshop_rnd/abmine.py"]))
        self.assertFalse(workspace.is_scorer_ignored(""))
        self.assertEqual(
            score.check_workspace_integrity(self.ws, self.pre_hashes, ["tests/test_x.py"]),
            ["tests/** is never permitted in allowed_paths: 'tests/test_x.py'"],
        )

        g_env = workspace.git_env(self.tmp / "ghome")
        subprocess.run(["git", "init", "-q"], cwd=str(self.ws), env=g_env, check=True)
        subprocess.run(["git", "config", "user.name", "t"], cwd=str(self.ws), env=g_env, check=True)
        subprocess.run(["git", "config", "user.email", "t@localhost"], cwd=str(self.ws), env=g_env, check=True)
        subprocess.run(["git", "add", "-A"], cwd=str(self.ws), env=g_env, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=str(self.ws), env=g_env, check=True)

        # R&D Blocking 4: run_pytest_and_score refuses use_sudo_builder=False unless _test_allow_uncontained=True
        with self.assertRaises(score.ScoreError):
            score.run_pytest_and_score(
                self.task,
                self.ws,
                self.pre_hashes,
                use_sudo_builder=False,
            )

        # Verify that with default use_sudo_builder=True, run_pytest_and_score wraps the command via sudo -u builder -n -- env -i ...
        captured_cmds: list[list[str]] = []
        canned_xml_text = self._canned_xml()

        def fake_bounded_subproc(cmd, *, cwd, env, timeout):
            captured_cmds.append(cmd)
            for arg in cmd:
                if arg.startswith("--junitxml="):
                    Path(arg.split("=", 1)[1]).write_text(canned_xml_text, encoding="utf-8")
            return subprocess.CompletedProcess(cmd, 0, "", "")

        with mock.patch.object(score, "run_bounded_subprocess", side_effect=fake_bounded_subproc):
            res_contained = score.run_pytest_and_score(
                self.task,
                self.ws,
                self.pre_hashes,
                aider_running=False,
            )
        self.assertTrue(res_contained["passed"], res_contained["reasons"])
        self.assertEqual(captured_cmds[0][:6], ["sudo", "-u", "builder", "-n", "--", "env"])
        self.assertEqual(captured_cmds[0][6], "-i")
        self.assertTrue(any(a.startswith("PIP_NO_INDEX=1") for a in captured_cmds[0]))
        self.assertIn("CUDA_VISIBLE_DEVICES=", captured_cmds[0])
        self.assertFalse((self.ws / "tests" / "test_abmine_fa_twin.py").exists())

        # R&D Blocking 6: TimeoutExpired in run_pytest_and_score returns score_timeout and cleans up staged twin
        with mock.patch.object(
            score,
            "run_bounded_subprocess",
            side_effect=subprocess.TimeoutExpired(cmd=["pytest"], timeout=300),
        ):
            res_timeout = score.run_pytest_and_score(
                self.task,
                self.ws,
                self.pre_hashes,
                aider_running=False,
            )
        self.assertFalse(res_timeout["passed"])
        self.assertIn("score_timeout", res_timeout["reasons"])
        self.assertFalse((self.ws / "tests" / "test_abmine_fa_twin.py").exists())

        # Missing --junitxml output raises ScoreError
        with self.assertRaises(score.ScoreError):
            score.run_pytest_and_score(
                self.task,
                self.ws,
                self.pre_hashes,
                pytest_cmd=[sys.executable, "-c", "pass"],
                use_sudo_builder=False,
                _test_allow_uncontained=True,
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

            self.assertEqual(prep.env["GIT_CONFIG_NOSYSTEM"], "1")
            self.assertTrue(prep.home_dir.is_dir())

            self.assertFalse((ws_dir / "CHANGELOG.md").exists())
            self.assertFalse((ws_dir / "CHANGELOG.old").exists())
            self.assertFalse((ws_dir / "docs" / "runs").exists())
            self.assertFalse((ws_dir / "experiments" / "local-builders" / "DESIGN.md").exists())

            self.assertTrue((ws_dir / task.test_file).is_file())
            self.assertIn(task.test_file, prep.pre_test_hashes)

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

    def test_companion_tests_written_before_baseline_commit_and_hashed(self):
        """Item 1: companion_tests in task.json (under companion/) overwrite parent copies before baseline commit and join pre_test_hashes."""
        git_env = workspace.git_env(self.tmp / "git_home")
        base_task = self.tasks[0]

        # Parent commit has an older copy of tests/test_companion_interlock.py
        comp_rel = "tests/test_companion_interlock.py"
        parent_comp_file = self.src_repo / comp_rel
        parent_comp_file.write_text("def test_interlock():\n    assert 1 == 2  # parent copy\n", encoding="utf-8")
        subprocess.run(["git", "add", "-A"], cwd=str(self.src_repo), env=git_env, check=True)
        subprocess.run(
            ["git", "commit", "-q", "-m", "parent with companion test"],
            cwd=str(self.src_repo),
            env=git_env,
            check=True,
        )
        parent_with_comp = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(self.src_repo),
            env=git_env,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()

        # Task dir with companion/tests/test_companion_interlock.py
        task_dir = self.tmp / "task_5488ec7c70"
        companion_content = "def test_interlock():\n    assert 1 == 1  # updated companion test\n"
        companion_file = task_dir / "companion" / comp_rel
        companion_file.parent.mkdir(parents=True, exist_ok=True)
        companion_file.write_text(companion_content, encoding="utf-8", newline="\n")
        expected_comp_sha = hashlib.sha256(companion_content.encode("utf-8")).hexdigest()

        spec_comp = workspace.TaskSpec.from_dict(
            {
                "id": "5488ec7c70",
                "parent_commit": parent_with_comp,
                "test_file": base_task.test_file,
                "target_node_id": base_task.target_node_id,
                "twin_node_id": base_task.twin_nodes[0],
                "test_cmd": base_task.test_cmd,
                "install": "uv sync --frozen",
                "allowed_paths": ["mcptoolshop_rnd/abmine.py"],
                "baseline": base_task.baseline,
                "scrubbed_test_path": base_task.scrubbed_test_path,
                "twin_test_path": base_task.twin_test_path,
                "companion_tests": [comp_rel],
            },
            base_dir=task_dir,
        )
        self.assertEqual(spec_comp.companion_tests, [comp_rel])
        self.assertEqual(spec_comp.install_cmd, "uv sync --frozen")
        self.assertEqual(spec_comp.install, "uv sync --frozen")
        self.assertEqual(spec_comp.read_companion_test(comp_rel), companion_content)

        ws_comp = self.tmp / "ws_companion"
        prepared = workspace.build_workspace(
            self.src_repo,
            spec_comp,
            ws_comp,
            home_dir=self.tmp / "home_comp",
        )

        # 1. Written over parent's copy BEFORE baseline commit (working tree is clean on single baseline commit)
        self.assertEqual((ws_comp / comp_rel).read_text(encoding="utf-8"), companion_content)
        rev_count = subprocess.run(
            ["git", "rev-list", "--count", "HEAD"],
            cwd=str(ws_comp),
            env=git_env,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        self.assertEqual(rev_count, "1")
        status_out = subprocess.run(
            ["git", "status", "--porcelain", "-uall", "--ignored"],
            cwd=str(ws_comp),
            env=git_env,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        self.assertEqual(status_out, "")

        # 2. Companion test sha256 joined pre_test_hashes
        self.assertIn(comp_rel, prepared.pre_test_hashes)
        self.assertEqual(prepared.pre_test_hashes[comp_rel], expected_comp_sha)

        # 3. Scorer integrity check passes untouched and catches any edit to the companion test
        self.assertEqual(
            score.check_workspace_integrity(ws_comp, prepared.pre_test_hashes, spec_comp.allowed_paths, env=git_env),
            [],
        )
        (ws_comp / comp_rel).write_text("def test_interlock(): pass\n", encoding="utf-8")
        reasons = score.check_workspace_integrity(
            ws_comp, prepared.pre_test_hashes, spec_comp.allowed_paths, env=git_env
        )
        self.assertTrue(any(f"edited test file: {comp_rel}" in r for r in reasons), reasons)

        # Dict and list-of-dict companion_tests forms and inline companion_test_contents
        spec_dict_comp = workspace.TaskSpec.from_dict(
            {
                "id": "56e0f9c72d",
                "parent_commit": parent_with_comp,
                "test_file": base_task.test_file,
                "target_node_id": base_task.target_node_id,
                "twin_node_id": base_task.twin_nodes[0],
                "allowed_paths": ["mcptoolshop_rnd/abmine.py"],
                "baseline": base_task.baseline,
                "companion_tests": {comp_rel: f"companion/{comp_rel}"},
            },
            bank_dir=task_dir,
        )
        self.assertEqual(spec_dict_comp.read_companion_test(comp_rel), companion_content)

        spec_list_dict_comp = workspace.TaskSpec.from_dict(
            {
                "id": "56e0f9c72d-b",
                "parent_commit": parent_with_comp,
                "test_file": base_task.test_file,
                "target_node_id": base_task.target_node_id,
                "twin_node_id": base_task.twin_nodes[0],
                "allowed_paths": ["mcptoolshop_rnd/abmine.py"],
                "baseline": base_task.baseline,
                "companion_tests": [{"path": comp_rel, "source": f"companion/{comp_rel}"}],
                "companion_test_contents": {comp_rel: "def test_inline(): pass\n"},
            },
            bank_dir=task_dir,
        )
        self.assertEqual(spec_list_dict_comp.read_companion_test(comp_rel), "def test_inline(): pass\n")

        # Validation of bad companion_tests entries and missing companion files
        for bad_companions in (
            ["mcptoolshop_rnd/abmine.py"],
            {"mcptoolshop_rnd/abmine.py": "companion/abmine.py"},
            "not-a-list-or-dict",
        ):
            with self.assertRaises(workspace.WorkspaceError):
                workspace.TaskSpec.from_dict(
                    {
                        "id": "bad_comp",
                        "parent_commit": parent_with_comp,
                        "test_file": base_task.test_file,
                        "target_node_id": base_task.target_node_id,
                        "twin_node_id": base_task.twin_nodes[0],
                        "allowed_paths": ["mcptoolshop_rnd/abmine.py"],
                        "baseline": base_task.baseline,
                        "companion_tests": bad_companions,
                    }
                )
        spec_missing_comp = workspace.TaskSpec.from_dict(
            {
                "id": "missing_comp",
                "parent_commit": parent_with_comp,
                "test_file": base_task.test_file,
                "target_node_id": base_task.target_node_id,
                "twin_node_id": base_task.twin_nodes[0],
                "allowed_paths": ["mcptoolshop_rnd/abmine.py"],
                "baseline": base_task.baseline,
                "companion_tests": ["tests/test_missing_comp.py"],
            },
            base_dir=self.tmp / "empty_task_dir",
        )
        with self.assertRaises(workspace.WorkspaceError):
            spec_missing_comp.read_companion_test("tests/test_missing_comp.py")


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

        self.assertEqual(probe._evaluate_attempt(lambda p: (_ for _ in ()).throw(OSError("no")), self.paths)[0], True)
        self.assertEqual(probe._evaluate_attempt(lambda p: False, self.paths)[0], True)
        self.assertEqual(probe._evaluate_attempt(lambda p: None, self.paths)[0], False)
        with self.assertRaises(ValueError):
            probe.run_probe(self.paths, injected_attempts={"not_a_check": False})

    def test_probe_allows_only_the_two_task_history_files_and_refuses_all_other_outside_writes(self):
        """Item 2: Probe allows writes to work_root/.../chat-history.md and input-history in an un-listable dir, and refuses every other write outside the workspace."""
        history_dir = self.tmp / "work" / "history-task1"
        chat_hist, input_hist = runner.prepare_task_history_files(history_dir, allow_uncontained=True)

        paths_with_history = probe.ProbePaths(
            workspace_dir=self.paths.workspace_dir,
            outside_dir=self.paths.outside_dir,
            bank_dir=self.paths.bank_dir,
            twins_dir=self.paths.twins_dir,
            receipts_dir=self.paths.receipts_dir,
            chat_history_file=chat_hist,
            input_history_file=input_hist,
            llama_port=18081,
        )

        # Exactly those two paths are allowed outside the workspace
        self.assertTrue(probe.is_allowed_outside_write(paths_with_history, chat_hist))
        self.assertTrue(probe.is_allowed_outside_write(paths_with_history, input_hist))
        self.assertFalse(probe.is_allowed_outside_write(paths_with_history, history_dir / "other.txt"))
        self.assertFalse(probe.is_allowed_outside_write(paths_with_history, self.paths.outside_dir / "breach.txt"))

        # Outcome 1 (Pass): writes to chat-history.md and input-history succeed, listing history_dir is refused,
        # and writing any other file in history_dir or outside_dir is refused -> probe passes.
        with (
            mock.patch.object(probe.os, "listdir", side_effect=PermissionError("0711 dir not listable")),
            mock.patch.object(Path, "write_text", side_effect=PermissionError("outside writes refused")),
        ):
            # Direct target checks on the two allowed history files succeed (refused=True / no breach)
            breach_chat, _ = probe._attempt_write_outside_workspace(paths_with_history, target_path=chat_hist)
            breach_input, _ = probe._attempt_write_outside_workspace(paths_with_history, target_path=input_hist)
            self.assertFalse(breach_chat)
            self.assertFalse(breach_input)

            # Direct target check on another file outside workspace is refused -> no breach
            breach_other, _ = probe._attempt_write_outside_workspace(
                paths_with_history, target_path=history_dir / "other.txt"
            )
            self.assertFalse(breach_other)

            # Full run_probe with write_outside_workspace using real _attempt_write_outside_workspace passes
            other_checks_refused = {name: False for name in probe.CHECK_NAMES if name != "write_outside_workspace"}
            rep_pass = probe.run_probe(paths_with_history, injected_attempts=other_checks_refused)
            self.assertTrue(rep_pass["passed"], rep_pass)
            self.assertEqual(rep_pass["breaches"], [])

        # Outcome 2a (Breach): write to a non-history path outside workspace succeeds -> probe fails
        breach_target, detail_target = probe._attempt_write_outside_workspace(
            paths_with_history, target_path=self.paths.outside_dir / "rogue.txt"
        )
        self.assertTrue(breach_target)
        self.assertIn("wrote outside workspace", detail_target)

        # Outcome 2b (Breach): sibling file write inside history_dir succeeds -> probe fails
        with mock.patch.object(probe.os, "listdir", side_effect=PermissionError("0711 dir not listable")):
            other_checks_refused = {name: False for name in probe.CHECK_NAMES if name != "write_outside_workspace"}
            rep_sibling_breach = probe.run_probe(paths_with_history, injected_attempts=other_checks_refused)
            self.assertFalse(rep_sibling_breach["passed"])
            self.assertEqual(rep_sibling_breach["breaches"], ["write_outside_workspace"])
            self.assertIn("wrote non-history file", rep_sibling_breach["checks"]["write_outside_workspace"]["detail"])

        # Outcome 2c (Breach): history_dir is listable by builder -> probe fails
        other_checks_refused = {name: False for name in probe.CHECK_NAMES if name != "write_outside_workspace"}
        rep_listable_breach = probe.run_probe(paths_with_history, injected_attempts=other_checks_refused)
        self.assertFalse(rep_listable_breach["passed"])
        self.assertEqual(rep_listable_breach["breaches"], ["write_outside_workspace"])
        self.assertIn("listed history directory", rep_listable_breach["checks"]["write_outside_workspace"]["detail"])

        # Outcome 2d (Failure): builder cannot write to chat-history.md -> probe fails
        with mock.patch("builtins.open", side_effect=PermissionError("0600 not owned by builder")):
            rep_unwritable = probe.run_probe(paths_with_history, injected_attempts=other_checks_refused)
            self.assertFalse(rep_unwritable["passed"])
            self.assertEqual(rep_unwritable["breaches"], ["write_outside_workspace"])
            self.assertIn("not writable by builder", rep_unwritable["checks"]["write_outside_workspace"]["detail"])

        # Outcome 2e (Failure): only one history file or wrong filename configured -> probe fails
        incomplete_paths = probe.ProbePaths(
            workspace_dir=self.paths.workspace_dir,
            outside_dir=self.paths.outside_dir,
            bank_dir=self.paths.bank_dir,
            twins_dir=self.paths.twins_dir,
            receipts_dir=self.paths.receipts_dir,
            chat_history_file=chat_hist,
            input_history_file=None,
        )
        rep_incomplete = probe.run_probe(incomplete_paths, injected_attempts=other_checks_refused)
        self.assertFalse(rep_incomplete["passed"])
        self.assertEqual(rep_incomplete["breaches"], ["write_outside_workspace"])

    def test_contain_iptables_insert_order_sudo_env_and_process_group_kill(self):
        """R&D Blocking 2 & Item 9: wrap_as_builder preserves builder_env via env -i, and iptables inserts at -I OUTPUT 1 in reverse order."""
        rules = contain.iptables_commands(builder_user="builder", proxy_port=18080, llama_port=18081)
        flat = [" ".join(r) for r in rules]
        # Inserted in reverse order with -I OUTPUT 1:
        # First inserted is the catch-all IPv4 REJECT, last IPv4 inserted is llama_port REJECT (ending up at rule 1)
        self.assertTrue(all("-I OUTPUT 1" in r for r in flat))
        self.assertIn("-j REJECT", flat[0])
        self.assertIn("--dport 18080 -m owner --uid-owner builder -j ACCEPT", flat[1])
        self.assertIn("--dport 18081 -m owner --uid-owner builder -j REJECT", flat[4])
        self.assertIn("ip6tables -I OUTPUT 1 -m owner --uid-owner builder -j REJECT", flat[5])

        script = contain.render_setup_script()
        self.assertIn("iptables -I OUTPUT 1", script)
        self.assertIn("iptables -S OUTPUT", script)

        self.assertEqual(contain.wrap_as_builder(["echo"], use_sudo=False), ["echo"])
        env = contain.builder_env(proxy_port=18080, home_dir=self.tmp / "home")
        self.assertEqual(env["CUDA_VISIBLE_DEVICES"], "")
        wrapped = contain.wrap_as_builder(["aider", "--no-stream"], env=env, use_sudo=True)
        self.assertEqual(wrapped[:7], ["sudo", "-u", "builder", "-n", "--", "env", "-i"])
        for expected_kv in (
            "OPENAI_API_BASE=http://127.0.0.1:18080/v1",
            "OPENAI_API_KEY=local",
            f"HOME={env['HOME']}",
            "LITELLM_LOCAL_MODEL_COST_MAP=True",
            "PIP_NO_INDEX=1",
            "NPM_CONFIG_OFFLINE=true",
            "GIT_CONFIG_NOSYSTEM=1",
            "HTTP_PROXY=http://127.0.0.1:9",
            "HTTPS_PROXY=http://127.0.0.1:9",
            "NO_PROXY=127.0.0.1,localhost",
            "CUDA_VISIBLE_DEVICES=",
        ):
            self.assertIn(expected_kv, wrapped)
        self.assertEqual(wrapped[-2:], ["aider", "--no-stream"])

        with self.assertRaises(contain.ContainmentError):
            contain.iptables_commands(proxy_port=18080, llama_port=18080)

        # Process-group bounded subprocess timeout and kill
        with self.assertRaises(subprocess.TimeoutExpired):
            contain.run_bounded_subprocess(
                [sys.executable, "-c", "import time; time.sleep(10)"],
                cwd=self.tmp,
                env=os.environ.copy(),
                timeout=0.1,
            )

        # Drive mount checks
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

        def run_need_useradd(c):
            if c[0] == "id":
                return subprocess.CompletedProcess(c, 1, "", "no user")
            if c[:2] == ["iptables", "-S"]:
                return subprocess.CompletedProcess(c, 0, "-P OUTPUT ACCEPT\n", "")
            return subprocess.CompletedProcess(c, 0, "", "")

        applied = contain.apply_vm_containment(cfg, run_cmd=run_need_useradd, mounts_text="", drive_paths=())
        self.assertEqual(applied["iptables_rules_applied"], 6)
        self.assertEqual(applied["iptables_s_output"], "-P OUTPUT ACCEPT")

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
        with self.assertRaises(contain.ContainmentError):
            contain.apply_vm_containment(
                cfg,
                run_cmd=lambda c: subprocess.CompletedProcess(c, 1 if c[:2] == ["iptables", "-S"] else 0, "", "s err"),
                mounts_text="",
                drive_paths=(),
            )


class PreflightTests(unittest.TestCase):
    """Tests for `mcptoolshop_rnd.localbuilders.preflight` (F5, F6, F13, D1, D-F1, D-F3, E1, E3)."""

    def test_f13_and_df3_multi_run_context_length_computation(self):
        self.assertEqual(preflight.next_power_of_two(0), 1)
        with self.assertRaises(preflight.PreflightError):
            preflight.compute_j2_context([{"kind": "result", "prompt_tokens": 1000, "output_tokens": 500}] * 10)
        with self.assertRaises(preflight.PreflightError):
            preflight.compute_j2_context([], require_full_cap=False)
        with self.assertRaises(preflight.PreflightError):
            preflight.compute_j2_context([{"kind": "result", "prompt_eval_count": 0, "eval_count": 0}], require_full_cap=False)

        # D-F3 / E3: compute_j2_context_length requires at least 2 validation runs by default
        run_other = [{"kind": "result", "prompt_eval_count": 8000, "eval_count": 2000}] * 30
        run_qwen_reattach = list(run_other)
        run_qwen_reattach[-1] = {"kind": "result", "prompt_tokens": 24000, "output_tokens": 4000}

        with self.assertRaises(preflight.PreflightError):
            preflight.compute_j2_context_length({"only_one": run_other})

        sizing = preflight.compute_j2_context_length(
            {
                "granite-4.2-30b": run_other,
                "qwen3.8-27b-reattach": run_qwen_reattach,
            }
        )
        self.assertEqual(sizing, 65536)
        self.assertEqual(int(sizing), 65536)
        self.assertEqual(sizing["context_length"], 65536)
        self.assertEqual(sizing["runs_used"], ["granite-4.2-30b", "qwen3.8-27b-reattach"])
        self.assertEqual(sizing["winning_run"], "qwen3.8-27b-reattach")
        self.assertEqual(
            sizing["per_run_max_tokens"],
            {"granite-4.2-30b": 10000, "qwen3.8-27b-reattach": 28000},
        )

        # List-of-run-dicts input form
        sizing_list = preflight.compute_j2_context_length(
            [
                {"run_id": "qwen3.8-27b", "calls": run_qwen_reattach},
                {"run_id": "granite-4.2-30b", "calls": run_other},
            ]
        )
        self.assertEqual(sizing_list["context_length"], 65536)
        self.assertEqual(sizing_list["runs_used"], ["qwen3.8-27b", "granite-4.2-30b"])

        with self.assertRaises(preflight.PreflightError):
            preflight.compute_j2_context_length("bad-type")  # type: ignore[arg-type]
        with self.assertRaises(preflight.PreflightError):
            preflight.compute_j2_context_length({})
        with self.assertRaises(preflight.PreflightError):
            preflight.compute_j2_context_length({"r1": "not-list", "r2": []})  # type: ignore[dict-item]

    def test_d1_gguf_template_check_both_outcomes(self):
        """D1: Read chat template embedded in GGUF and report whether its sha256 equals template_sha256."""
        template_str = "{% for message in messages %}{{ message.content }}{% endfor %}"
        expected_sha = hashlib.sha256(template_str.encode("utf-8")).hexdigest()

        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            gguf_match = tmp / "match.gguf"
            gguf_match.write_bytes(
                preflight.build_minimal_gguf_with_template(
                    template_str,
                    extra_int_key=("general.alignment", 32),
                )
            )

            # Outcome 1: Template sha256 matches
            res_match = preflight.check_gguf_template(
                expected_template_sha256=expected_sha,
                gguf_path=gguf_match,
            )
            self.assertTrue(res_match["matches"])
            self.assertEqual(res_match["status"], "match")
            self.assertEqual(res_match["embedded_sha256"], expected_sha)

            # Outcome 2: Template sha256 mismatches (reports mismatch and never exits)
            res_mismatch = preflight.check_gguf_template(
                expected_template_sha256="0" * 64,
                gguf_path=gguf_match,
            )
            self.assertFalse(res_mismatch["matches"])
            self.assertEqual(res_mismatch["status"], "mismatch")
            self.assertIn("mismatch", res_mismatch["report"])

            # Missing template in GGUF or non-GGUF file
            gguf_no_tpl = tmp / "no_tpl.gguf"
            gguf_no_tpl.write_bytes(preflight.build_minimal_gguf_with_template(None))
            res_none = preflight.check_gguf_template(
                expected_template_sha256=expected_sha,
                gguf_path=gguf_no_tpl,
            )
            self.assertFalse(res_none["matches"])
            self.assertEqual(res_none["status"], "missing_template")

            # Array metadata skipping in GGUF header
            arr_key = b"tokenizer.ggml.tokens"
            elem = b"tok"
            arr_kv = (
                struct.pack("<Q", len(arr_key))
                + arr_key
                + struct.pack("<IIQ", 9, 8, 1)
                + struct.pack("<Q", len(elem))
                + elem
            )
            tpl_key = b"tokenizer.chat_template"
            tpl_b = template_str.encode("utf-8")
            tpl_kv = struct.pack("<Q", len(tpl_key)) + tpl_key + struct.pack("<IQ", 8, len(tpl_b)) + tpl_b
            gguf_arr = tmp / "arr.gguf"
            gguf_arr.write_bytes(b"GGUF" + struct.pack("<IQQ", 3, 0, 2) + arr_kv + tpl_kv)
            self.assertEqual(preflight.read_gguf_chat_template(gguf_arr), template_str)

    def test_df1_thinking_split_check_both_outcomes(self):
        """D-F1 / E1: Thinking reply must have non-empty reasoning_content and no <think> or <|channel>thought tag in content."""
        # Outcome 1: Clean split passes
        clean_resp = _canned_llama_response(
            content="Here is the diff.",
            reasoning_content="Step 1: check the caller.",
        )
        ok_split = preflight.check_thinking_split(clean_resp, thinking_enabled=True)
        self.assertTrue(ok_split["passed"])
        self.assertTrue(ok_split["has_nonempty_reasoning"])
        self.assertEqual(ok_split["leaked_tags"], [])

        # Outcome 2a: Empty reasoning_content fails check
        empty_reasoning = _canned_llama_response(content="Here is the diff.", reasoning_content="")
        fail_empty = preflight.check_thinking_split(empty_reasoning, thinking_enabled=True)
        self.assertFalse(fail_empty["passed"])
        self.assertIn("empty reasoning_content", fail_empty["report"])

        # Outcome 2b: Leaked <think> tag in content fails check
        leaked_think = _canned_llama_response(
            content="<think>still in content</think>\nFixed.",
            reasoning_content="Some reasoning",
        )
        fail_think = preflight.check_thinking_split(leaked_think, thinking_enabled=True)
        self.assertFalse(fail_think["passed"])
        self.assertIn("<think>", fail_think["leaked_tags"])

        # Outcome 2c: Leaked Gemma 4 <|channel>thought tag in content fails check
        leaked_gemma = _canned_llama_response(
            content="<|channel>thought\nGemma internal reasoning\nFixed.",
            reasoning_content="Some reasoning",
        )
        fail_gemma = preflight.check_thinking_split(leaked_gemma, thinking_enabled=True)
        self.assertFalse(fail_gemma["passed"])
        self.assertIn("<|channel>thought", fail_gemma["leaked_tags"])

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

    def test_verify_installed_aider_with_version_gate_mocked_and_real_prompts(self):
        """Item 1: preflight.verify_installed_aider imports Aider, enforces version == 0.86.1, and checks CoderPrompts and EditBlockPrompts."""
        # Missing aider package refuses
        with mock.patch.dict(sys.modules, {"aider": None, "aider.coders.base_prompts": None}):
            with self.assertRaises(preflight.PreflightError):
                preflight.get_installed_aider_version()
            with self.assertRaises(preflight.PreflightError):
                preflight.load_installed_aider_prompts()

        # Version gate mocked to 0.86.1 with real 0.86.1 CoderPrompts and EditBlockPrompts -> passes
        with _mock_installed_aider(version="0.86.1"):
            self.assertEqual(preflight.get_installed_aider_version(), "0.86.1")
            res = preflight.verify_installed_aider()
            self.assertEqual(
                res,
                {
                    "aider_version": "0.86.1",
                    "synthetic_strings_verified": True,
                },
            )

        # Version gate mismatch (e.g. 0.85.0 or 0.86.1+import) refuses the run
        for bad_ver in ("0.85.0", "0.86.1+import", "0.87.0"):
            with _mock_installed_aider(version=bad_ver):
                with self.assertRaises(preflight.PreflightError):
                    preflight.verify_installed_aider()

        # Synthetic string mismatch on EditBlockPrompts refuses the run
        class MismatchedEditBlockPrompts(_RealAider0861EditBlockPrompts):
            files_no_full_files_with_repo_map_reply = "New unrecognised Aider synthetic reply."

        with _mock_installed_aider(version="0.86.1", editblock_prompts_cls=MismatchedEditBlockPrompts):
            with self.assertRaises(preflight.PreflightError):
                preflight.verify_installed_aider()

    def test_f6_and_amendment_b_fit_report_and_cli(self):
        log_pair_only = "llama_kv_cache_init: K (f16): 1600.00 MiB, V (f16): 1600.00 MiB\n"
        tpl = "{{ messages }}"
        tpl_sha = hashlib.sha256(tpl.encode("utf-8")).hexdigest()

        with tempfile.TemporaryDirectory() as d, _mock_installed_aider(version="0.86.1"):
            tmp = Path(d)
            gguf_file = tmp / "model.gguf"
            gguf_file.write_bytes(preflight.build_minimal_gguf_with_template(tpl))

            rep = preflight.evaluate_candidate_fit(
                arm="nemotron-3.5-lightning-30b-a3b",
                quant="Q8_0",
                context_length=32768,
                top_or_response=_canned_llama_response(steps=3),
                gguf_path=gguf_file,
                server_log=log_pair_only,
                peak_vram_mib=42500.0,
                expected_template_sha256=tpl_sha,
                reattach_max_turns=10,
            )
            self.assertEqual(rep["aider_version"], "0.86.1")
            self.assertIs(rep["synthetic_strings_verified"], True)
            self.assertFalse(rep["fits_a100"])
            self.assertTrue(rep["flagged_for_q6_k"])
            self.assertEqual(rep["arm_label"], "[Q6_K: A100 fit]")
            self.assertTrue(rep["template_check"]["matches"])
            self.assertTrue(rep["thinking_split_check"]["passed"])
            self.assertIn("ran with a cap", rep["reattach_cap_report"])

            # CLI main test with multi-run validation_runs (never exits non-zero on fit/template/thinking)
            in_json = tmp / "in.json"
            out_json = tmp / "out.json"
            in_json.write_text(
                json.dumps(
                    {
                        "arm": "qwen3.8-27b",
                        "quant": "Q8_0",
                        "validation_runs": {
                            "qwen3.8-27b": [{"kind": "result", "prompt_tokens": 5000, "output_tokens": 1000}] * 30,
                            "granite-4.2-30b": [{"kind": "result", "prompt_tokens": 4000, "output_tokens": 800}] * 30,
                        },
                        "probe_response": _canned_llama_response(steps=3),
                        "gguf_path": str(gguf_file),
                        "expected_template_sha256": "0" * 64,  # mismatch reported without exiting
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
            written = json.loads(out_json.read_text(encoding="utf-8"))
            self.assertEqual(written["context_runs_used"], ["qwen3.8-27b", "granite-4.2-30b"])
            self.assertEqual(written["aider_version"], "0.86.1")
            self.assertIs(written["synthetic_strings_verified"], True)
            self.assertFalse(written["template_check"]["matches"])

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
    """Tests for `mcptoolshop_rnd.localbuilders.runner` (NB1, F2, F4, F7, F9, F10, D/E, section 7)."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.task = workspace.load_task_bank(BANK_JSON)[0]

    def test_builds_exact_aider_command_line_and_pins_examples_as_sys_msg(self):
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

        # Item 2: prepare_task_history_files creates chat-history.md and input-history owned by builder (0600) in a 0711 directory
        chmod_calls: list[tuple[Path, int]] = []
        chown_calls: list[tuple[Path, str]] = []
        hdir = self.tmp / "work" / "history-t1"
        c_file, i_file = runner.prepare_task_history_files(
            hdir,
            builder_user="builder",
            chmod_fn=lambda p, m: chmod_calls.append((p, m)),
            chown_fn=lambda p, u: chown_calls.append((p, u)),
        )
        self.assertEqual(c_file.name, "chat-history.md")
        self.assertEqual(i_file.name, "input-history")
        self.assertTrue(c_file.is_file())
        self.assertTrue(i_file.is_file())
        self.assertIn((hdir.resolve(), 0o711), chmod_calls)
        self.assertIn((c_file, 0o600), chmod_calls)
        self.assertIn((i_file, 0o600), chmod_calls)
        self.assertEqual(chown_calls, [(c_file, "builder"), (i_file, "builder")])

        # Publisher Item 2 (D-F1, D-F2): model-settings file pins examples_as_sys_msg: true for every candidate
        cards = json.loads(CARD_VALUES_JSON.read_text(encoding="utf-8"))["candidates"]
        for cand in cards:
            cid = cand["candidate"]
            s_path = runner.write_model_settings_file(self.tmp / f"settings-{cid}.yml", cid)
            runner.validate_model_settings_file(s_path)
            self.assertIn("examples_as_sys_msg: true", s_path.read_text(encoding="utf-8"))

        bad_settings = self.tmp / "bad-settings.yml"
        bad_settings.write_text("- name: openai/qwen3.8-27b\n  streaming: false\n", encoding="utf-8")
        with self.assertRaises(runner.RunnerError):
            runner.validate_model_settings_file(bad_settings)
        with self.assertRaises(runner.RunnerError):
            runner.validate_model_settings_file(self.tmp / "nonexistent-settings.yml")
        with self.assertRaises(runner.RunnerError):
            runner.build_aider_argv(
                served_as="qwen3.8-27b",
                model_settings_file=bad_settings,
                test_cmd=self.task.test_cmd,
                test_file=self.task.test_file,
                node_id=self.task.target_node_id,
                llm_history_file="/work/llm-history.md",
                analytics_log="/work/analytics.jsonl",
            )

        good_settings = runner.write_model_settings_file(self.tmp / "good-settings.yml", "qwen3.8-27b")
        argv = runner.build_aider_argv(
            served_as="qwen3.8-27b",
            model_settings_file=good_settings,
            test_cmd=self.task.test_cmd,
            test_file=self.task.test_file,
            node_id=self.task.target_node_id,
            llm_history_file="/work/llm-history.md",
            chat_history_file="/work/chat-history.md",
            input_history_file="/work/input-history",
            analytics_log="/work/analytics.jsonl",
            editable_files=["", "mcptoolshop_rnd/abmine.py"],
        )
        for flag in (
            "--no-stream",
            "--auto-test",
            "--no-auto-commits",
            "--no-gitignore",
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
        self.assertEqual(flag_value("--model-settings-file"), str(good_settings))
        self.assertEqual(flag_value("--test-cmd"), self.task.test_cmd)
        self.assertEqual(Path(flag_value("--chat-history-file")).as_posix(), "/work/chat-history.md")
        self.assertEqual(Path(flag_value("--input-history-file")).as_posix(), "/work/input-history")
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
                model_settings_file=good_settings,
                test_cmd=self.task.test_cmd,
                test_file=self.task.test_file,
                node_id=self.task.target_node_id,
                llm_history_file="/work/llm-history.md",
                analytics_log="/work/analytics.jsonl",
                editable_files=["tests/test_abmine_fa.py"],
            )

        # Default use_sudo=True wraps with sudo -u builder -n -- env -i K=V ...
        env = contain.builder_env(proxy_port=18080, home_dir=self.tmp / "home")
        self.assertEqual(env["CUDA_VISIBLE_DEVICES"], "")
        full_cmd = runner.build_aider_command(
            served_as="qwen3.8-27b",
            model_settings_file=good_settings,
            test_cmd=self.task.test_cmd,
            test_file=self.task.test_file,
            node_id=self.task.target_node_id,
            llm_history_file="/work/llm-history.md",
            analytics_log="/work/analytics.jsonl",
            editable_files=["mcptoolshop_rnd/abmine.py"],
            env=env,
        )
        self.assertEqual(full_cmd[:7], ["sudo", "-u", "builder", "-n", "--", "env", "-i"])
        self.assertIn("OPENAI_API_BASE=http://127.0.0.1:18080/v1", full_cmd)
        self.assertIn("CUDA_VISIBLE_DEVICES=", full_cmd)
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
        self.assertEqual(runner.create_coder_with_reflections(FakeCoder, max_reflections=29).max_reflections, 29)

        with mock.patch.object(runner, "run_aider_entrypoint", return_value=0) as mocked_ep:
            self.assertEqual(
                runner.main(["--aider-entrypoint", "--max-reflections", "29", "--ignored", "--", "--model", "openai/m"]),
                0,
            )
            mocked_ep.assert_called_once_with(["--model", "openai/m"], max_reflections=29)

        with self.assertRaises(runner.RunnerError):
            runner.main([])

    def _make_stub_venv_install_cmd(
        self,
        *,
        python_version: str = "Python 3.12.8",
        assert_not_precreated: bool = True,
        require_bank_freeze: bool = False,
        tag: str = "default",
    ) -> str:
        """Build a stub `install` command that names `{venv}`, verifies `{venv}` was NOT pre-created, and builds `{venv}/bin/python` itself."""
        safe_tag = f"{tag}_{python_version}".replace(" ", "_")
        helper_script = self.tmp / f"make_stub_venv_{safe_tag}.py"
        py_posix = Path(sys.executable).as_posix()
        vpy_code = (
            f"#!{py_posix}\n"
            "import subprocess, sys\n"
            "if sys.argv[1:] in (['--version'], ['-V']):\n"
            f"    sys.stdout.write({python_version!r} + '\\n')\n"
            "    sys.exit(0)\n"
            f"sys.exit(subprocess.call([{py_posix!r}, *sys.argv[1:]]))\n"
        )
        helper_script.write_text(
            "import os, pathlib, sys\n"
            "vdir = pathlib.Path(sys.argv[1])\n"
            f"if {assert_not_precreated!r}:\n"
            "    assert not vdir.exists(), f'venv was pre-created before install: {vdir}'\n"
            "assert str(vdir.resolve()) == os.environ['UV_PROJECT_ENVIRONMENT']\n"
            "assert str(vdir.resolve()) == os.environ['VIRTUAL_ENV']\n"
            "assert 'PIP_NO_INDEX' not in os.environ and 'HTTP_PROXY' not in os.environ\n"
            f"if {require_bank_freeze!r}:\n"
            "    bdir = pathlib.Path(sys.argv[2])\n"
            "    assert (bdir / 'aspire-si-freeze.txt').is_file()\n"
            "vbin = vdir / 'bin'\n"
            "vbin.mkdir(parents=True, exist_ok=True)\n"
            "(vdir / 'stub_installed.txt').write_text('ok', encoding='utf-8')\n"
            "vpy = vbin / 'python'\n"
            f"vpy.write_text({vpy_code!r}, encoding='utf-8', newline='\\n')\n"
            "os.chmod(vpy, 0o755)\n",
            encoding="utf-8",
            newline="\n",
        )
        if require_bank_freeze:
            return f'"{sys.executable}" "{helper_script}" "{{venv}}" "{{bank}}"'
        return f'"{sys.executable}" "{helper_script}" "{{venv}}"'

    def test_default_sudo_builder_refusal_timeouts_and_end_to_end_receipt(self):
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
                "install": self._make_stub_venv_install_cmd(tag="mini"),
                "allowed_paths": ["mcptoolshop_rnd/abmine.py"],
                "baseline": self.task.baseline,
                "scrubbed_test_path": self.task.scrubbed_test_path,
                "twin_test_path": self.task.twin_test_path,
            }
        )

        with _StubLlamaServer() as stub, _mock_installed_aider(version="0.86.1"):
            receipt_path = self.tmp / "receipts" / "r1.json"
            settings_file = self.tmp / "model-settings.yml"

            run_cfg = runner.RunTaskConfig(
                source_repo=mini_repo,
                task=task,
                candidate_config_path=CARD_VALUES_JSON,
                candidate="qwen3.8-27b",
                model_settings_file=settings_file,
                served_as="qwen3.8-27b",
                model_tag="qwen3.8:27b-q8_0",
                model_digest="sha256:aaee06c39dcf",
                aider_version=proxy.PINNED_AIDER_VERSION,
                upstream_url=stub.url,
                work_root=self.tmp / "work",
                receipt_path=receipt_path,
                machine_line={"gpu": "NVIDIA A100-SXM4-40GB"},
            )
            # R&D Blocking 3: use_sudo_builder defaults to True, and non-test run with False is refused
            self.assertTrue(run_cfg.use_sudo_builder)
            uncontained_cfg = runner.RunTaskConfig(
                source_repo=mini_repo,
                task=task,
                candidate_config_path=CARD_VALUES_JSON,
                candidate="qwen3.8-27b",
                model_settings_file=settings_file,
                served_as="qwen3.8-27b",
                model_tag="qwen3.8:27b-q8_0",
                model_digest="sha256:aaee06c39dcf",
                aider_version=proxy.PINNED_AIDER_VERSION,
                upstream_url=stub.url,
                work_root=self.tmp / "work-uncontained",
                receipt_path=self.tmp / "receipts" / "uncontained.json",
                machine_line={"gpu": "NVIDIA A100-SXM4-40GB"},
                use_sudo_builder=False,
            )
            with self.assertRaises(runner.RunnerError):
                runner.run_single_task(uncontained_cfg)

            # Wrong Aider version in config or installed Aider refuses the run
            bad_ver_cfg = runner.RunTaskConfig(
                source_repo=mini_repo,
                task=task,
                candidate_config_path=CARD_VALUES_JSON,
                candidate="qwen3.8-27b",
                model_settings_file=settings_file,
                served_as="qwen3.8-27b",
                model_tag="qwen3.8:27b-q8_0",
                model_digest="sha256:aaee06c39dcf",
                aider_version="0.85.0",
                upstream_url=stub.url,
                work_root=self.tmp / "work-bad-ver",
                receipt_path=self.tmp / "receipts" / "bad_ver.json",
                machine_line={"gpu": "NVIDIA A100-SXM4-40GB"},
            )
            with self.assertRaises(runner.RunnerError):
                runner.run_single_task(bad_ver_cfg)

            with _mock_installed_aider(version="0.85.0"):
                with self.assertRaises(runner.RunnerError):
                    runner.run_single_task(run_cfg)

            def fake_aider_runner(cmd: list[str], ws_dir: Path, run_env: dict[str, str]) -> int:
                self.assertEqual(cmd[:7], ["sudo", "-u", "builder", "-n", "--", "env", "-i"])
                # Item 2: Verify the two history files were created before launching Aider
                expected_hdir = run_cfg.work_root / f"history-{task.id}"
                self.assertTrue((expected_hdir / "chat-history.md").is_file())
                self.assertTrue((expected_hdir / "input-history").is_file())
                api_base = run_env["OPENAI_API_BASE"]
                _post_json(f"{api_base}/chat/completions", {"messages": [{"role": "user", "content": "turn 1"}]})
                _post_json(
                    f"{api_base}/chat/completions",
                    {
                        "messages": [
                            {"role": "user", "content": "repo"},
                            {"role": "assistant", "content": "Ok."},
                            {"role": "user", "content": "turn 1"},
                            {"role": "assistant", "content": "Fixed the bug."},
                            {"role": "user", "content": "turn 2"},
                        ]
                    },
                )
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

            self.assertEqual(receipt["aider_version"], "0.86.1")
            self.assertIs(receipt["synthetic_strings_verified"], True)
            self.assertEqual(receipt["tool_calls"], {"total": 2, "malformed": 1, "failed": 1})
            self.assertEqual(receipt["retries"], 1)
            self.assertEqual(receipt["transforms"], ["reattach_thinking"])
            self.assertEqual(receipt["reattach_thinking"]["reattached"], 1)
            self.assertEqual(receipt["reattach_thinking"]["synthetic"], 1)
            self.assertEqual(receipt["reattach_thinking"]["mismatch"], 0)

            # R&D Blocking 6: Aider timeout writes failed receipt with reason 'aider_timeout'
            timeout_aider_cfg = runner.RunTaskConfig(
                source_repo=mini_repo,
                task=task,
                candidate_config_path=CARD_VALUES_JSON,
                candidate="qwen3.8-27b",
                model_settings_file=settings_file,
                served_as="qwen3.8-27b",
                model_tag="qwen3.8:27b-q8_0",
                model_digest="sha256:aaee06c39dcf",
                aider_version=proxy.PINNED_AIDER_VERSION,
                upstream_url=stub.url,
                work_root=self.tmp / "work-aider-to",
                receipt_path=self.tmp / "receipts" / "r_aider_to.json",
                machine_line={"gpu": "NVIDIA A100-SXM4-40GB"},
            )
            r_aider_to = runner.run_single_task(
                timeout_aider_cfg,
                aider_runner=lambda c, w, e: (_ for _ in ()).throw(
                    subprocess.TimeoutExpired(cmd=c, timeout=930)
                ),
            )
            self.assertFalse(r_aider_to["correct"])
            self.assertEqual(r_aider_to["grade"]["reasons"], ["aider_timeout"])
            self.assertTrue(timeout_aider_cfg.receipt_path.is_file())

            # R&D Blocking 6: Score timeout writes failed receipt with reason 'score_timeout'
            timeout_score_cfg = runner.RunTaskConfig(
                source_repo=mini_repo,
                task=task,
                candidate_config_path=CARD_VALUES_JSON,
                candidate="qwen3.8-27b",
                model_settings_file=settings_file,
                served_as="qwen3.8-27b",
                model_tag="qwen3.8:27b-q8_0",
                model_digest="sha256:aaee06c39dcf",
                aider_version=proxy.PINNED_AIDER_VERSION,
                upstream_url=stub.url,
                work_root=self.tmp / "work-score-to",
                receipt_path=self.tmp / "receipts" / "r_score_to.json",
                machine_line={"gpu": "NVIDIA A100-SXM4-40GB"},
            )
            r_score_to = runner.run_single_task(
                timeout_score_cfg,
                aider_runner=lambda c, w, e: 0,
                scorer_fn=lambda t, p: (_ for _ in ()).throw(
                    subprocess.TimeoutExpired(cmd=["pytest"], timeout=300)
                ),
            )
            self.assertFalse(r_score_to["correct"])
            self.assertEqual(r_score_to["grade"]["reasons"], ["score_timeout"])
            self.assertTrue(timeout_score_cfg.receipt_path.is_file())

        # Receipt validation errors
        for bad_mod in (
            lambda r: r.pop("task_id"),
            lambda r: r.update({"aider_version": "0.85.0"}),
            lambda r: r.update({"synthetic_strings_verified": False}),
            lambda r: r.update({"install_cmd": 123}),
            lambda r: r.update({"install_exit_code": "0"}),
            lambda r: r.update({"pip_freeze_sha256": "short"}),
            lambda r: r.update({"generations_sha256": "short"}),
            lambda r: r.update({"injected": "not-dict"}),
            lambda r: r.update({"injected": {"sampling": {}}}),
            lambda r: r.update({"cap_hits": "not-dict"}),
        ):
            copy_r = json.loads(json.dumps(receipt))
            bad_mod(copy_r)
            with self.assertRaises(runner.RunnerError):
                runner.validate_receipt(copy_r)

    def test_chown_fallback_raises_on_vm_and_proxy_files_are_0600(self):
        """Items 2 & 3: prepare_task_history_files raises on VM when chown fails, and proxy files in work_root are written 0600."""
        # Item 2: On the VM (allow_uncontained=False), any chown failure in prepare_task_history_files raises RunnerError
        for exc in (LookupError("unknown user: builder"), PermissionError("operation not permitted"), OSError("failed")):
            with mock.patch.object(runner.shutil, "chown", side_effect=exc):
                with self.assertRaises(runner.RunnerError):
                    runner.prepare_task_history_files(self.tmp / "vm-history")

        # Item 3: ProxyState writes generations.jsonl with mode 0600 on init and on append
        chmod_records: list[tuple[Path, int]] = []
        orig_chmod = os.chmod

        def tracking_chmod(p, mode, *args, **kwargs):
            chmod_records.append((Path(p).resolve(), mode))
            return orig_chmod(p, mode, *args, **kwargs)

        gen_file = self.tmp / "work" / "generations-t1.jsonl"
        with _StubLlamaServer() as stub, mock.patch.object(proxy.os, "chmod", side_effect=tracking_chmod):
            st = proxy.ProxyState(
                upstream_url=stub.url,
                config=CANDIDATE_CONFIG_JSON,
                generations_path=gen_file,
            )
            self.assertIn((gen_file.resolve(), 0o600), chmod_records)
            chmod_records.clear()
            status, _ = st.handle_completion(
                "/v1/chat/completions",
                {"messages": [{"role": "user", "content": "hi"}]},
            )
            self.assertEqual(status, 200)
            self.assertIn((gen_file.resolve(), 0o600), chmod_records)

    def test_per_task_environment_setup_with_stub_install_command_and_setup_failed(self):
        """Item 4: Per-task venv setup at work_root/venv-<task>, {venv} & {bank} filled, receipt records install & python_version fields, and failed install ends as setup_failed."""
        mini_repo = self.tmp / "mini_repo_venv"
        (mini_repo / "mcptoolshop_rnd").mkdir(parents=True)
        (mini_repo / "mcptoolshop_rnd" / "abmine.py").write_text("x = 1\n", encoding="utf-8")
        env = workspace.git_env(self.tmp / "ghome_venv")
        subprocess.run(["git", "init", "-q"], cwd=str(mini_repo), env=env, check=True)
        subprocess.run(["git", "config", "user.name", "t"], cwd=str(mini_repo), env=env, check=True)
        subprocess.run(["git", "config", "user.email", "t@localhost"], cwd=str(mini_repo), env=env, check=True)
        subprocess.run(["git", "add", "-A"], cwd=str(mini_repo), env=env, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "p"], cwd=str(mini_repo), env=env, check=True)
        parent_sha = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=str(mini_repo), env=env, capture_output=True, text=True, check=True
        ).stdout.strip()

        fake_bank_dir = self.tmp / "locked_bank"
        fake_bank_dir.mkdir(parents=True, exist_ok=True)
        (fake_bank_dir / "aspire-si-freeze.txt").write_text("pytest==8.3.3\n", encoding="utf-8")

        # Stub install command uses both {venv} and {bank} placeholders, verifies {venv} was NOT pre-created,
        # builds {venv}/bin/python (reporting Python 3.12.8), and verifies:
        # 1) UV_PROJECT_ENVIRONMENT and VIRTUAL_ENV point at work_root/venv-<task>
        # 2) network/index restrictions (PIP_NO_INDEX, HTTP_PROXY) are NOT set for root setup
        stub_install_template = self._make_stub_venv_install_cmd(
            python_version="Python 3.12.8",
            assert_not_precreated=True,
            require_bank_freeze=True,
            tag="venv-ok",
        )
        task_ok = workspace.TaskSpec.from_dict(
            {
                "id": "venv-ok",
                "parent_commit": parent_sha,
                "test_file": self.task.test_file,
                "target_node_id": self.task.target_node_id,
                "twin_node_id": self.task.twin_nodes[0],
                "test_cmd": "env PYTHONPATH=src {venv}/bin/python -m pytest -p no:xdist -q -o addopts= tests/test_abmine_fa.py",
                "suite_cmd": "env PYTHONPATH=src {venv}/bin/python -m pytest -p no:xdist -q -o addopts=",
                "install": stub_install_template,
                "allowed_paths": ["mcptoolshop_rnd/abmine.py"],
                "baseline": self.task.baseline,
                "scrubbed_test_path": self.task.scrubbed_test_path,
                "twin_test_path": self.task.twin_test_path,
            },
            bank_dir=fake_bank_dir,
        )

        work_ok = self.tmp / "work-venv-ok"
        receipt_ok_path = self.tmp / "receipts" / "r_venv_ok.json"
        settings_file = self.tmp / "model-settings-venv.yml"

        captured_aider_cmd: list[str] = []
        captured_aider_env: dict[str, str] = {}
        captured_score_venv: list[str] = []

        with _StubLlamaServer() as stub, _mock_installed_aider(version="0.86.1"):
            cfg_ok = runner.RunTaskConfig(
                source_repo=mini_repo,
                task=task_ok,
                candidate_config_path=CARD_VALUES_JSON,
                candidate="qwen3.8-27b",
                model_settings_file=settings_file,
                served_as="qwen3.8-27b",
                model_tag="qwen3.8:27b-q8_0",
                model_digest="sha256:aaee06c39dcf",
                aider_version=proxy.PINNED_AIDER_VERSION,
                upstream_url=stub.url,
                work_root=work_ok,
                receipt_path=receipt_ok_path,
                machine_line={"gpu": "NVIDIA A100-SXM4-40GB"},
            )

            def fake_aider_ok(cmd: list[str], ws_dir: Path, run_env: dict[str, str]) -> int:
                captured_aider_cmd.extend(cmd)
                captured_aider_env.update(run_env)
                # Stub install ran BEFORE Aider and created work_root/venv-venv-ok
                expected_venv = work_ok.resolve() / "venv-venv-ok"
                self.assertTrue((expected_venv / "stub_installed.txt").is_file())
                return 0

            def fake_run_pytest_and_score(task_arg, ws_dir_arg, pre_hashes_arg, **kwargs):
                captured_score_venv.append(str(kwargs.get("venv_dir")))
                # Workspace git status is completely clean (venv is outside workspace)
                reasons = score.check_workspace_integrity(
                    ws_dir_arg,
                    pre_hashes_arg,
                    task_arg.allowed_paths,
                    env=kwargs.get("env"),
                )
                self.assertEqual(reasons, [])
                return {
                    "task_id": task_arg.id,
                    "passed": True,
                    "correct": True,
                    "reasons": [],
                    "reason": "",
                    "counts": {"passed": 10, "failed": 0, "errors": 0, "skipped": 0, "xfail": 0},
                    "baseline": dict(task_arg.baseline),
                    "target_nodes": list(task_arg.target_nodes),
                    "twin_nodes": list(task_arg.twin_nodes),
                }

            chmod_calls: list[tuple[Path, int]] = []
            orig_chmod = os.chmod

            def record_chmod(p, mode, *args, **kwargs):
                chmod_calls.append((Path(p).resolve(), mode))
                return orig_chmod(p, mode, *args, **kwargs)

            with (
                mock.patch.object(runner, "run_pytest_and_score", side_effect=fake_run_pytest_and_score),
                mock.patch.object(runner.os, "chmod", side_effect=record_chmod),
            ):
                receipt_ok = runner.run_single_task(cfg_ok, aider_runner=fake_aider_ok)

            expected_venv_dir = work_ok.resolve() / "venv-venv-ok"
            expected_venv_py = str(runner.venv_python_path(expected_venv_dir))
            self.assertTrue(expected_venv_dir.is_dir())
            self.assertTrue(Path(expected_venv_py).is_file())

            # Venv is outside workspace, readable/executable by builder (0755/0644), and not group/world writable
            self.assertIn((expected_venv_dir, 0o755), chmod_calls)
            self.assertIn(((expected_venv_dir / "stub_installed.txt").resolve(), 0o644), chmod_calls)
            self.assertIn((receipt_ok_path.resolve(), 0o600), chmod_calls)

            # Aider's --test-cmd has {venv} filled and preserves env PYTHONPATH=src ... -o addopts= byte for byte
            idx_tc = captured_aider_cmd.index("--test-cmd")
            self.assertEqual(
                captured_aider_cmd[idx_tc + 1],
                f"env PYTHONPATH=src {expected_venv_dir}/bin/python -m pytest -p no:xdist -q -o addopts= tests/test_abmine_fa.py",
            )
            self.assertEqual(captured_aider_env["VIRTUAL_ENV"], str(expected_venv_dir))
            self.assertTrue(captured_aider_env["PATH"].startswith(str(contain.venv_bin_dir(expected_venv_dir))))
            self.assertEqual(captured_score_venv, [str(expected_venv_dir)])

            # Receipt records filled install_cmd, install_exit_code == 0, 64-char pip_freeze_sha256, and venv_python_version
            expected_filled_install = stub_install_template.replace("{venv}", str(expected_venv_dir)).replace(
                "{bank}", str(fake_bank_dir)
            )
            self.assertEqual(receipt_ok["install_cmd"], expected_filled_install)
            self.assertEqual(receipt_ok["install_exit_code"], 0)
            self.assertIsInstance(receipt_ok["pip_freeze_sha256"], str)
            self.assertEqual(len(receipt_ok["pip_freeze_sha256"]), 64)
            self.assertEqual(receipt_ok["venv_python_version"], "Python 3.12.8")
            self.assertEqual(receipt_ok["python_version"], "Python 3.12.8")
            self.assertEqual(receipt_ok["pins"]["install_cmd"], expected_filled_install)
            self.assertEqual(receipt_ok["pins"]["install_exit_code"], 0)
            self.assertEqual(receipt_ok["pins"]["pip_freeze_sha256"], receipt_ok["pip_freeze_sha256"])
            self.assertEqual(receipt_ok["pins"]["venv_python_version"], "Python 3.12.8")

            # Failing stub install command ends the task as setup_failed, with no Aider run and no score
            stub_install_fail = (
                f'"{sys.executable}" -c "import sys; _ = r\'{{venv}}\'; sys.stderr.write(\'broken lockfile\\n\'); sys.exit(17)"'
            )
            task_fail = workspace.TaskSpec.from_dict(
                {
                    "id": "venv-fail",
                    "parent_commit": parent_sha,
                    "test_file": self.task.test_file,
                    "target_node_id": self.task.target_node_id,
                    "twin_node_id": self.task.twin_nodes[0],
                    "test_cmd": "pytest tests/test_abmine_fa.py",
                    "install": stub_install_fail,
                    "allowed_paths": ["mcptoolshop_rnd/abmine.py"],
                    "baseline": self.task.baseline,
                    "scrubbed_test_path": self.task.scrubbed_test_path,
                    "twin_test_path": self.task.twin_test_path,
                }
            )
            work_fail = self.tmp / "work-venv-fail"
            receipt_fail_path = self.tmp / "receipts" / "r_venv_fail.json"
            cfg_fail = runner.RunTaskConfig(
                source_repo=mini_repo,
                task=task_fail,
                candidate_config_path=CARD_VALUES_JSON,
                candidate="qwen3.8-27b",
                model_settings_file=settings_file,
                served_as="qwen3.8-27b",
                model_tag="qwen3.8:27b-q8_0",
                model_digest="sha256:aaee06c39dcf",
                aider_version=proxy.PINNED_AIDER_VERSION,
                upstream_url=stub.url,
                work_root=work_fail,
                receipt_path=receipt_fail_path,
                machine_line={"gpu": "NVIDIA A100-SXM4-40GB"},
            )

            aider_called = False
            scorer_called = False

            def should_not_run_aider(*args, **kwargs):
                nonlocal aider_called
                aider_called = True
                return 0

            def should_not_run_scorer(*args, **kwargs):
                nonlocal scorer_called
                scorer_called = True
                return {}

            receipt_fail = runner.run_single_task(
                cfg_fail,
                aider_runner=should_not_run_aider,
                scorer_fn=should_not_run_scorer,
            )
            self.assertFalse(aider_called)
            self.assertFalse(scorer_called)
            self.assertFalse(receipt_fail["correct"])
            self.assertEqual(receipt_fail["status"], "setup_failed")
            self.assertEqual(receipt_fail["grade"]["status"], "setup_failed")
            self.assertEqual(receipt_fail["grade"]["reason"], "setup_failed")
            self.assertEqual(receipt_fail["grade"]["reasons"], ["setup_failed"])
            self.assertEqual(receipt_fail["call_count"], 0)
            self.assertEqual(
                receipt_fail["install_cmd"],
                stub_install_fail.replace("{venv}", str(work_fail.resolve() / "venv-venv-fail")),
            )
            self.assertEqual(receipt_fail["install_exit_code"], 17)
            self.assertIsNone(receipt_fail["pip_freeze_sha256"])
            self.assertIsNone(receipt_fail["venv_python_version"])

            with self.assertRaises(runner.RunnerError):
                runner.setup_task_venv(task_ok, work_ok, work_ok)

    def test_bank_command_contract_placeholders_suite_cmd_and_exported_entry_end_to_end(self):
        """Bank command contract: {venv} & {bank} filling with zero rewriting, suite_cmd + --junitxml with stub, and exported bank entry end-to-end."""
        # 1. Placeholder filling for both {venv} and {bank} across aspire-si, interlock, and role-set commands
        venv_str = "/root/j2/work/venv-aspire-si-1294984713"
        bank_str = "/root/j2/bank"

        aspire_install = "python3.12 -m venv {venv} && {venv}/bin/pip install -q -r {bank}/aspire-si-freeze.txt"
        aspire_test = (
            "env OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 {venv}/bin/python -m pytest "
            "-p no:xdist -q -p no:randomly "
            "tests/test_critic_heads.py::TestTraining::test_a_head_does_not_depend_on_the_heads_trained_before_it"
        )
        aspire_suite = "env OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 {venv}/bin/python -m pytest -p no:xdist -q -p no:randomly"

        self.assertEqual(
            runner.resolve_test_cmd_for_venv(aspire_install, venv_str, bank_dir=bank_str),
            f"python3.12 -m venv {venv_str} && {venv_str}/bin/pip install -q -r {bank_str}/aspire-si-freeze.txt",
        )
        self.assertEqual(
            runner.resolve_test_cmd_for_venv(aspire_test, venv_str, bank_dir=bank_str),
            f"env OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 {venv_str}/bin/python -m pytest "
            "-p no:xdist -q -p no:randomly "
            "tests/test_critic_heads.py::TestTraining::test_a_head_does_not_depend_on_the_heads_trained_before_it",
        )
        self.assertEqual(
            runner.resolve_test_cmd_for_venv(aspire_suite, venv_str, bank_dir=bank_str),
            f"env OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 {venv_str}/bin/python -m pytest -p no:xdist -q -p no:randomly",
        )

        interlock_venv = "/root/j2/work/venv-interlock-5488ec7c70"
        interlock_install = "UV_PROJECT_ENVIRONMENT={venv} uv sync --frozen --python 3.12"
        interlock_test = (
            "env PYTHONPATH=src {venv}/bin/python -m pytest -p no:xdist -q -o addopts= "
            "tests/test_target.py::test_the_live_runner_returns_the_child_stdout"
        )
        interlock_suite = "env PYTHONPATH=src {venv}/bin/python -m pytest -p no:xdist -q -o addopts="

        self.assertEqual(
            runner.resolve_test_cmd_for_venv(interlock_install, interlock_venv, bank_dir=bank_str),
            f"UV_PROJECT_ENVIRONMENT={interlock_venv} uv sync --frozen --python 3.12",
        )
        self.assertEqual(
            runner.resolve_test_cmd_for_venv(interlock_test, interlock_venv, bank_dir=bank_str),
            f"env PYTHONPATH=src {interlock_venv}/bin/python -m pytest -p no:xdist -q -o addopts= "
            "tests/test_target.py::test_the_live_runner_returns_the_child_stdout",
        )
        self.assertEqual(
            runner.resolve_test_cmd_for_venv(interlock_suite, interlock_venv, bank_dir=bank_str),
            f"env PYTHONPATH=src {interlock_venv}/bin/python -m pytest -p no:xdist -q -o addopts=",
        )

        # Commands without placeholders are never rewritten (no pytest/python prefix rewriting)
        self.assertEqual(runner.resolve_test_cmd_for_venv("pytest -q", interlock_venv), "pytest -q")
        self.assertEqual(runner.resolve_test_cmd_for_venv("python -m pytest -q", interlock_venv), "python -m pytest -q")
        with self.assertRaises(runner.RunnerError):
            runner.resolve_test_cmd_for_venv("{venv}/bin/python -m pytest", None)
        with self.assertRaises(runner.RunnerError):
            runner.resolve_test_cmd_for_venv("pip install -r {bank}/freeze.txt", interlock_venv, bank_dir=None)

        # 2. End-to-end test loading one task entry in the bank's exact shape (interlock-5488ec7c70, with companion)
        #    and running it through TaskSpec, build_workspace, setup_task_venv, and scorer's suite_cmd + --junitxml
        src_repo = self.tmp / "interlock_repo"
        (src_repo / "src" / "switchyard" / "harness").mkdir(parents=True)
        (src_repo / "tests").mkdir(parents=True)
        (src_repo / "src" / "switchyard" / "harness" / "e4b.py").write_text("x = 1\n", encoding="utf-8")
        (src_repo / "src" / "switchyard" / "harness" / "ollama_serve.py").write_text("y = 2\n", encoding="utf-8")
        (src_repo / "tests" / "test_e4b.py").write_text(
            "def test_old_parent_companion():\n    assert False\n", encoding="utf-8"
        )
        g_env = workspace.git_env(self.tmp / "ghome_bank")
        subprocess.run(["git", "init", "-q"], cwd=str(src_repo), env=g_env, check=True)
        subprocess.run(["git", "config", "user.name", "t"], cwd=str(src_repo), env=g_env, check=True)
        subprocess.run(["git", "config", "user.email", "t@localhost"], cwd=str(src_repo), env=g_env, check=True)
        subprocess.run(["git", "add", "-A"], cwd=str(src_repo), env=g_env, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "parent"], cwd=str(src_repo), env=g_env, check=True)
        parent_sha = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=str(src_repo), env=g_env, capture_output=True, text=True, check=True
        ).stdout.strip()

        export_bank_dir = self.tmp / "j2-bank-export"
        task_subdir = export_bank_dir / "interlock-5488ec7c70"
        (task_subdir / "companion" / "tests").mkdir(parents=True)
        scrubbed_content = (
            "def test_the_live_runner_returns_the_child_stdout():\n    assert True\n\n"
            "def test_read_git_refuses_a_runner_that_captured_nothing():\n    assert True\n"
        )
        twin_content = "def test_capture_run_returns_text_stdout_and_exit_code():\n    assert True\n"
        companion_content = "def test_companion_from_bank():\n    assert 2 + 2 == 4\n"

        (task_subdir / "test_target.py").write_text(scrubbed_content, encoding="utf-8", newline="\n")
        (task_subdir / "test_twin.py").write_text(twin_content, encoding="utf-8", newline="\n")
        (task_subdir / "companion" / "tests" / "test_e4b.py").write_text(
            companion_content, encoding="utf-8", newline="\n"
        )

        # Stub runner script that verifies suite_cmd flags + --junitxml=<path> and writes the JUnit XML
        stub_suite_script = self.tmp / "stub_suite_runner.py"
        stub_argv_record = self.tmp / "stub_suite_argv.json"
        stub_suite_script.write_text(
            "import json, os, pathlib, sys\n"
            f"record_path = pathlib.Path({str(stub_argv_record)!r})\n"
            "xml_arg = next((a for a in sys.argv[1:] if a.startswith('--junitxml=')), None)\n"
            "assert xml_arg is not None, f'missing --junitxml in {sys.argv}'\n"
            "assert sys.argv[-1] == xml_arg, f'--junitxml must be appended last: {sys.argv}'\n"
            "record_path.write_text(json.dumps({\n"
            "    'argv': sys.argv[1:],\n"
            "    'pythonpath': os.environ.get('PYTHONPATH'),\n"
            "}), encoding='utf-8')\n"
            "xml_path = pathlib.Path(xml_arg.split('=', 1)[1])\n"
            "cases = [\n"
            "    f'<testcase file=\"tests/test_suite.py\" classname=\"tests.test_suite\" name=\"test_base_{i}\"/>'\n"
            "    for i in range(543)\n"
            "] + [\n"
            "    f'<testcase file=\"tests/test_suite.py\" classname=\"tests.test_suite\" name=\"test_skip_{i}\"><skipped type=\"pytest.skip\"/></testcase>'\n"
            "    for i in range(6)\n"
            "] + [\n"
            "    '<testcase nodeid=\"tests/test_target.py::test_the_live_runner_returns_the_child_stdout\" name=\"test_the_live_runner_returns_the_child_stdout\"/>',\n"
            "    '<testcase nodeid=\"tests/test_target.py::test_read_git_refuses_a_runner_that_captured_nothing\" name=\"test_read_git_refuses_a_runner_that_captured_nothing\"/>',\n"
            "    '<testcase nodeid=\"tests/test_twin.py::test_capture_run_returns_text_stdout_and_exit_code\" name=\"test_capture_run_returns_text_stdout_and_exit_code\"/>',\n"
            "]\n"
            "xml_path.write_text('<testsuite name=\"pytest\">' + ''.join(cases) + '</testsuite>', encoding='utf-8')\n",
            encoding="utf-8",
        )

        exported_entry = {
            "id": "interlock-5488ec7c70",
            "repo": "interlock",
            "repo_url": "https://github.com/mcp-tool-shop-org/interlock",
            "parent_commit": parent_sha,
            "fix_commit": "5488ec7c70d9ee9ddfb19e95be7397412b07238b",
            "test_file": "tests/test_target.py",
            "target_nodes": [
                "tests/test_target.py::test_the_live_runner_returns_the_child_stdout",
                "tests/test_target.py::test_read_git_refuses_a_runner_that_captured_nothing",
            ],
            "twin_nodes": [
                "tests/test_twin.py::test_capture_run_returns_text_stdout_and_exit_code",
            ],
            "scrubbed_test_path": "interlock-5488ec7c70/test_target.py",
            "twin_test_path": "interlock-5488ec7c70/test_twin.py",
            "companion_tests": [
                {
                    "path": "tests/test_e4b.py",
                    "file": "interlock-5488ec7c70/companion/tests/test_e4b.py",
                }
            ],
            "allowed_paths": [
                "src/switchyard/harness/e4b.py",
                "src/switchyard/harness/ollama_serve.py",
            ],
            "baseline": {
                "passed": 543,
                "skipped": 6,
                "xfail": 0,
            },
            "install": "UV_PROJECT_ENVIRONMENT={venv} uv sync --frozen --python 3.12",
            "test_cmd": (
                "env PYTHONPATH=src {venv}/bin/python -m pytest -p no:xdist -q -o addopts= "
                "tests/test_target.py::test_the_live_runner_returns_the_child_stdout "
                "tests/test_target.py::test_read_git_refuses_a_runner_that_captured_nothing"
            ),
            "suite_cmd": "env PYTHONPATH=src {venv}/bin/python -m pytest -p no:xdist -q -o addopts=",
            "difficulty": "multi_file",
        }
        bank_file = export_bank_dir / "bank.json"
        bank_file.write_text(json.dumps({"tasks": [exported_entry]}, indent=2), encoding="utf-8")

        loaded_tasks = workspace.load_task_bank(bank_file)
        self.assertEqual(len(loaded_tasks), 1)
        spec = loaded_tasks[0]
        self.assertEqual(spec.id, "interlock-5488ec7c70")
        self.assertEqual(spec.repo, "interlock")
        self.assertEqual(spec.repo_url, "https://github.com/mcp-tool-shop-org/interlock")
        self.assertEqual(spec.fix_commit, "5488ec7c70d9ee9ddfb19e95be7397412b07238b")
        self.assertEqual(spec.install_cmd, "UV_PROJECT_ENVIRONMENT={venv} uv sync --frozen --python 3.12")
        self.assertEqual(spec.install, "UV_PROJECT_ENVIRONMENT={venv} uv sync --frozen --python 3.12")
        self.assertEqual(spec.suite_cmd, "env PYTHONPATH=src {venv}/bin/python -m pytest -p no:xdist -q -o addopts=")
        self.assertEqual(spec.companion_tests, ["tests/test_e4b.py"])
        self.assertEqual(
            Path(spec.companion_test_sources["tests/test_e4b.py"]),
            export_bank_dir / "interlock-5488ec7c70" / "companion" / "tests" / "test_e4b.py",
        )
        self.assertEqual(spec.read_companion_test("tests/test_e4b.py"), companion_content)

        # Build workspace from exported bank entry: companion written before baseline commit and hashed
        ws_dir = self.tmp / "ws-interlock-5488ec7c70"
        prepared = workspace.build_workspace(src_repo, spec, ws_dir)
        self.assertEqual((ws_dir / "tests" / "test_target.py").read_text(encoding="utf-8"), scrubbed_content)
        self.assertEqual((ws_dir / "tests" / "test_e4b.py").read_text(encoding="utf-8"), companion_content)
        self.assertEqual(
            prepared.pre_test_hashes["tests/test_e4b.py"],
            hashlib.sha256(companion_content.encode("utf-8")).hexdigest(),
        )

        # Verify TaskSpec render helpers and scorer's build_suite_command
        target_venv = self.tmp / "work" / "venv-interlock-5488ec7c70"
        self.assertEqual(
            spec.render_install_cmd(target_venv),
            f"UV_PROJECT_ENVIRONMENT={target_venv} uv sync --frozen --python 3.12",
        )
        self.assertEqual(
            spec.render_test_cmd(target_venv),
            f"env PYTHONPATH=src {target_venv}/bin/python -m pytest -p no:xdist -q -o addopts= "
            "tests/test_target.py::test_the_live_runner_returns_the_child_stdout "
            "tests/test_target.py::test_read_git_refuses_a_runner_that_captured_nothing",
        )
        self.assertEqual(
            spec.render_suite_cmd(target_venv),
            f"env PYTHONPATH=src {target_venv}/bin/python -m pytest -p no:xdist -q -o addopts=",
        )
        built_suite_argv = score.build_suite_command(spec, "/tmp/junit.xml", venv_dir=target_venv)
        self.assertEqual(
            built_suite_argv,
            [
                "env",
                "PYTHONPATH=src",
                f"{target_venv}/bin/python",
                "-m",
                "pytest",
                "-p",
                "no:xdist",
                "-q",
                "-o",
                "addopts=",
                "--junitxml=/tmp/junit.xml",
            ],
        )

        # 3. Scorer invoking suite_cmd with --junitxml appended using the real stub script
        #    Run setup_task_venv with a stub install that creates {venv}/bin/python (reporting Python 3.12.8)
        setup_res = runner.setup_task_venv(
            workspace.TaskSpec.from_dict(
                {**exported_entry, "install": self._make_stub_venv_install_cmd(tag="e2e")},
                bank_dir=export_bank_dir,
            ),
            ws_dir,
            self.tmp / "work",
        )
        self.assertTrue(setup_res.ok, setup_res.reason)
        self.assertEqual(setup_res.python_version, "Python 3.12.8")

        py_rel = setup_res.python_executable.relative_to(setup_res.venv_dir).as_posix()
        stub_suite_cmd = (
            f'env PYTHONPATH=src "{{venv}}/{py_rel}" "{stub_suite_script}" -p no:xdist -q -o addopts='
        )
        spec_with_stub_suite = workspace.TaskSpec.from_dict(
            {**exported_entry, "suite_cmd": stub_suite_cmd},
            bank_dir=export_bank_dir,
        )
        score_res = score.run_pytest_and_score(
            spec_with_stub_suite,
            ws_dir,
            prepared.pre_test_hashes,
            venv_dir=setup_res.venv_dir,
            use_sudo_builder=False,
            _test_allow_uncontained=True,
        )
        self.assertTrue(score_res["passed"], score_res["reasons"])
        self.assertTrue(stub_argv_record.is_file())
        recorded_stub = json.loads(stub_argv_record.read_text(encoding="utf-8"))
        self.assertEqual(recorded_stub["pythonpath"], "src")
        self.assertEqual(recorded_stub["argv"][:-1], ["-p", "no:xdist", "-q", "-o", "addopts="])
        self.assertTrue(recorded_stub["argv"][-1].startswith("--junitxml="))

        # Edge cases for placeholder filling, suite command building, and venv_python_version
        self.assertEqual(workspace.fill_command_placeholders("", venv_dir="/v"), "")
        self.assertEqual(
            score.build_suite_command(["{venv}/bin/python", "-m", "pytest", "-q"], "/tmp/x.xml", venv_dir="/v"),
            ["/v/bin/python", "-m", "pytest", "-q", "--junitxml=/tmp/x.xml"],
        )
        with self.assertRaises(score.ScoreError):
            score.build_suite_command("", "/tmp/x.xml")
        with self.assertRaises(score.ScoreError):
            score.build_suite_command([], "/tmp/x.xml")
        with self.assertRaises(score.ScoreError):
            score.build_suite_command("{venv}/bin/python -m pytest", "/tmp/x.xml", venv_dir=None)
        with self.assertRaises(score.ScoreError):
            score.build_suite_command(["{venv}/bin/python"], "/tmp/x.xml", venv_dir=None)
        with self.assertRaises(runner.RunnerError):
            runner.venv_python_version(
                self.tmp,
                run_cmd=lambda cmd, **kw: subprocess.CompletedProcess(cmd, 1, "", "err"),
            )
        self.assertTrue(
            runner.venv_python_version(
                self.tmp,
                run_cmd=lambda cmd, **kw: subprocess.CompletedProcess(cmd, 0, "", ""),
            ).startswith("Python ")
        )

    def test_round5_no_precreated_venv_python312_check_and_unusable_install_refused(self):
        """Round 5: (1) install naming {venv} runs without pre-created venv and requires Python 3.12; (2) empty or non-{venv} install ends as setup_failed before Aider runs."""
        mini_repo = self.tmp / "mini_repo_r5"
        (mini_repo / "mcptoolshop_rnd").mkdir(parents=True)
        (mini_repo / "mcptoolshop_rnd" / "abmine.py").write_text("x = 1\n", encoding="utf-8")
        env = workspace.git_env(self.tmp / "ghome_r5")
        subprocess.run(["git", "init", "-q"], cwd=str(mini_repo), env=env, check=True)
        subprocess.run(["git", "config", "user.name", "t"], cwd=str(mini_repo), env=env, check=True)
        subprocess.run(["git", "config", "user.email", "t@localhost"], cwd=str(mini_repo), env=env, check=True)
        subprocess.run(["git", "add", "-A"], cwd=str(mini_repo), env=env, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "p"], cwd=str(mini_repo), env=env, check=True)
        parent_sha = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=str(mini_repo), env=env, capture_output=True, text=True, check=True
        ).stdout.strip()

        def make_task(tid: str, install_str: str) -> workspace.TaskSpec:
            return workspace.TaskSpec.from_dict(
                {
                    "id": tid,
                    "parent_commit": parent_sha,
                    "test_file": self.task.test_file,
                    "target_node_id": self.task.target_node_id,
                    "twin_node_id": self.task.twin_nodes[0],
                    "test_cmd": "{venv}/bin/python -m pytest -q tests/test_abmine_fa.py",
                    "suite_cmd": "{venv}/bin/python -m pytest -q",
                    "install": install_str,
                    "allowed_paths": ["mcptoolshop_rnd/abmine.py"],
                    "baseline": self.task.baseline,
                    "scrubbed_test_path": self.task.scrubbed_test_path,
                    "twin_test_path": self.task.twin_test_path,
                }
            )

        # Unit check on is_python_312
        self.assertTrue(runner.is_python_312("Python 3.12.8"))
        self.assertTrue(runner.is_python_312("Python 3.12"))
        self.assertFalse(runner.is_python_312("Python 3.10.11"))
        self.assertFalse(runner.is_python_312("Python 3.11.9"))
        self.assertFalse(runner.is_python_312("Python 3.13.1"))
        self.assertFalse(runner.is_python_312("Python 3.120.0"))
        self.assertFalse(runner.is_python_312(""))
        self.assertFalse(runner.is_python_312(None))

        # 1. An install that names {venv} runs without a pre-created venv (stub asserts not vdir.exists() and builds venv itself)
        task_self_venv = make_task(
            "r5-self-venv",
            self._make_stub_venv_install_cmd(
                python_version="Python 3.12.8",
                assert_not_precreated=True,
                tag="r5-self",
            ),
        )
        ws_self = self.tmp / "ws-r5-self"
        ws_self.mkdir(parents=True, exist_ok=True)
        work_self = self.tmp / "work-r5-self"
        res_self = runner.setup_task_venv(task_self_venv, ws_self, work_self)
        self.assertTrue(res_self.ok, res_self.reason)
        self.assertEqual(res_self.venv_python_version, "Python 3.12.8")
        self.assertEqual(res_self.reason, "")
        self.assertTrue((work_self / "venv-r5-self-venv" / "bin" / "python").is_file())

        settings_file = self.tmp / "model-settings-r5.yml"
        with _StubLlamaServer() as stub, _mock_installed_aider(version="0.86.1"):
            # 2. A venv that reports another Python version ends the task as setup_failed, with the version on the receipt
            task_wrong_py = make_task(
                "r5-wrong-py",
                self._make_stub_venv_install_cmd(
                    python_version="Python 3.11.9",
                    assert_not_precreated=True,
                    tag="r5-wrong-py",
                ),
            )
            aider_called = False
            scorer_called = False

            def forbid_aider(*args, **kwargs):
                nonlocal aider_called
                aider_called = True
                return 0

            def forbid_scorer(*args, **kwargs):
                nonlocal scorer_called
                scorer_called = True
                return {}

            cfg_wrong_py = runner.RunTaskConfig(
                source_repo=mini_repo,
                task=task_wrong_py,
                candidate_config_path=CARD_VALUES_JSON,
                candidate="qwen3.8-27b",
                model_settings_file=settings_file,
                served_as="qwen3.8-27b",
                model_tag="qwen3.8:27b-q8_0",
                model_digest="sha256:aaee06c39dcf",
                aider_version=proxy.PINNED_AIDER_VERSION,
                upstream_url=stub.url,
                work_root=self.tmp / "work-r5-wrong-py",
                receipt_path=self.tmp / "receipts" / "r5_wrong_py.json",
                machine_line={"gpu": "NVIDIA A100-SXM4-40GB"},
            )
            receipt_wrong_py = runner.run_single_task(
                cfg_wrong_py,
                aider_runner=forbid_aider,
                scorer_fn=forbid_scorer,
            )
            self.assertFalse(aider_called)
            self.assertFalse(scorer_called)
            self.assertFalse(receipt_wrong_py["correct"])
            self.assertEqual(receipt_wrong_py["status"], "setup_failed")
            self.assertEqual(receipt_wrong_py["grade"]["status"], "setup_failed")
            self.assertEqual(receipt_wrong_py["venv_python_version"], "Python 3.11.9")
            self.assertEqual(receipt_wrong_py["python_version"], "Python 3.11.9")
            self.assertEqual(receipt_wrong_py["pins"]["venv_python_version"], "Python 3.11.9")
            self.assertIn("Python 3.12", receipt_wrong_py["reason"])
            self.assertIn("Python 3.11.9", receipt_wrong_py["reason"])
            self.assertEqual(receipt_wrong_py["grade"]["reason"], receipt_wrong_py["reason"])
            self.assertIn(receipt_wrong_py["reason"], receipt_wrong_py["grade"]["reasons"])

            # 3. An empty install ends the task as setup_failed with reason 'install is empty', no Aider call, and no score
            task_empty = make_task("r5-empty-install", "")
            cfg_empty = runner.RunTaskConfig(
                source_repo=mini_repo,
                task=task_empty,
                candidate_config_path=CARD_VALUES_JSON,
                candidate="qwen3.8-27b",
                model_settings_file=settings_file,
                served_as="qwen3.8-27b",
                model_tag="qwen3.8:27b-q8_0",
                model_digest="sha256:aaee06c39dcf",
                aider_version=proxy.PINNED_AIDER_VERSION,
                upstream_url=stub.url,
                work_root=self.tmp / "work-r5-empty",
                receipt_path=self.tmp / "receipts" / "r5_empty.json",
                machine_line={"gpu": "NVIDIA A100-SXM4-40GB"},
            )
            receipt_empty = runner.run_single_task(
                cfg_empty,
                aider_runner=forbid_aider,
                scorer_fn=forbid_scorer,
            )
            self.assertFalse(aider_called)
            self.assertFalse(scorer_called)
            self.assertFalse(receipt_empty["correct"])
            self.assertEqual(receipt_empty["status"], "setup_failed")
            self.assertEqual(receipt_empty["grade"]["status"], "setup_failed")
            self.assertEqual(receipt_empty["reason"], "install is empty")
            self.assertEqual(receipt_empty["grade"]["reason"], "install is empty")
            self.assertIn("install is empty", receipt_empty["grade"]["reasons"])
            self.assertIsNone(receipt_empty["venv_python_version"])
            self.assertFalse((self.tmp / "work-r5-empty" / "venv-r5-empty-install").exists())

            # 4. An install without {venv} ends the task as setup_failed with reason 'install does not name {venv}', no Aider call, and no score
            task_no_venv = make_task("r5-no-venv-install", "uv sync --frozen --python 3.12")
            cfg_no_venv = runner.RunTaskConfig(
                source_repo=mini_repo,
                task=task_no_venv,
                candidate_config_path=CARD_VALUES_JSON,
                candidate="qwen3.8-27b",
                model_settings_file=settings_file,
                served_as="qwen3.8-27b",
                model_tag="qwen3.8:27b-q8_0",
                model_digest="sha256:aaee06c39dcf",
                aider_version=proxy.PINNED_AIDER_VERSION,
                upstream_url=stub.url,
                work_root=self.tmp / "work-r5-no-venv",
                receipt_path=self.tmp / "receipts" / "r5_no_venv.json",
                machine_line={"gpu": "NVIDIA A100-SXM4-40GB"},
            )
            receipt_no_venv = runner.run_single_task(
                cfg_no_venv,
                aider_runner=forbid_aider,
                scorer_fn=forbid_scorer,
            )
            self.assertFalse(aider_called)
            self.assertFalse(scorer_called)
            self.assertFalse(receipt_no_venv["correct"])
            self.assertEqual(receipt_no_venv["status"], "setup_failed")
            self.assertEqual(receipt_no_venv["grade"]["status"], "setup_failed")
            self.assertEqual(receipt_no_venv["reason"], "install does not name {venv}")
            self.assertEqual(receipt_no_venv["grade"]["reason"], "install does not name {venv}")
            self.assertIn("install does not name {venv}", receipt_no_venv["grade"]["reasons"])
            self.assertIsNone(receipt_no_venv["venv_python_version"])
            self.assertFalse((self.tmp / "work-r5-no-venv" / "venv-r5-no-venv-install").exists())

        # Edge cases: install exits 0 without creating {venv}/bin/python, and install timeout
        task_no_py = make_task("r5-no-py", 'echo "{venv}"')
        res_no_py = runner.setup_task_venv(
            task_no_py,
            ws_self,
            self.tmp / "work-r5-no-py",
            run_cmd=lambda cmd, **kw: subprocess.CompletedProcess(cmd, 0 if kw.get("shell") else 1, "", "missing py"),
        )
        self.assertFalse(res_no_py.ok)
        self.assertIn("venv python check failed", res_no_py.reason)

        res_to = runner.setup_task_venv(
            task_no_py,
            ws_self,
            self.tmp / "work-r5-to",
            run_cmd=lambda cmd, **kw: (_ for _ in ()).throw(subprocess.TimeoutExpired(cmd=cmd, timeout=1)),
        )
        self.assertFalse(res_to.ok)
        self.assertEqual(res_to.install_exit_code, -1)
        self.assertEqual(res_to.reason, "install_timeout")


if __name__ == "__main__":
    unittest.main()


