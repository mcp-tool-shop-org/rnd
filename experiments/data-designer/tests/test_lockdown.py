"""Phase 0 lockdown: telemetry, providers, and no egress. No GPU."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import textwrap
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
PYTHON = HERE / ".venv" / "Scripts" / "python.exe"
if not PYTHON.exists():
    PYTHON = Path(sys.executable)


def run_python(code: str, env: dict) -> subprocess.CompletedProcess:
    return subprocess.run(
        [str(PYTHON), "-c", code],
        cwd=HERE,
        env=env,
        text=True,
        capture_output=True,
        timeout=180,
    )


class TelemetryTests(unittest.TestCase):
    def test_import_fails_when_telemetry_env_is_unset(self):
        env = os.environ.copy()
        env.pop("NEMO_TELEMETRY_ENABLED", None)
        env["DATA_DESIGNER_HOME"] = str(HERE / "home")
        result = run_python(
            textwrap.dedent(
                """
                import studio_lock
                try:
                    studio_lock.import_data_designer()
                except RuntimeError as exc:
                    if "unset" not in str(exc):
                        raise SystemExit(f"wrong error: {exc}")
                else:
                    raise SystemExit("import was allowed with telemetry unset")
                """
            ),
            env,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_telemetry_is_off_when_armed_before_import(self):
        env = os.environ.copy()
        env.pop("NEMO_TELEMETRY_ENABLED", None)
        result = run_python(
            textwrap.dedent(
                """
                import studio_lock
                studio_lock.arm()
                studio_lock.import_data_designer()
                from data_designer.engine.models.telemetry import TELEMETRY_ENABLED
                if TELEMETRY_ENABLED:
                    raise SystemExit("telemetry stayed on")
                if __import__("os").environ["NEMO_TELEMETRY_ENABLED"] != "false":
                    raise SystemExit("env was not false")
                print("telemetry-off")
                """
            ),
            env,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("telemetry-off", result.stdout)

    def test_provider_file_and_resolved_list_are_ollama_local_only(self):
        env = os.environ.copy()
        env.pop("NEMO_TELEMETRY_ENABLED", None)
        result = run_python(
            textwrap.dedent(
                """
                import json
                import studio_lock
                studio_lock.arm()
                studio_lock.require_locked_files()
                studio_lock.import_data_designer()
                from data_designer.interface import DataDesigner
                designer = DataDesigner()
                rows = studio_lock.assert_provider_list(designer.get_default_model_providers())
                rows = studio_lock.assert_provider_list(designer.model_provider_registry.providers)
                print(json.dumps(rows))
                """
            ),
            env,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        rows = json.loads(result.stdout.strip().splitlines()[-1])
        self.assertEqual([row["name"] for row in rows], ["ollama-local"])
        self.assertEqual(rows[0]["endpoint"], "http://127.0.0.1:11434/v1")

    def test_cloud_model_name_is_refused(self):
        import studio_lock

        with self.assertRaises(SystemExit):
            studio_lock.refuse_cloud("gemma4:31b-cloud")


class EgressTests(unittest.TestCase):
    def test_stub_job_stays_on_localhost(self):
        body = json.dumps(
            {
                "id": "stub",
                "choices": [
                    {
                        "index": 0,
                        "finish_reason": "stop",
                        "message": {
                            "role": "assistant",
                            "content": "Ice is less dense than liquid water, so it floats.",
                        },
                    }
                ],
                "usage": {"prompt_tokens": 20, "completion_tokens": 12, "total_tokens": 32},
            }
        ).encode()

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                length = int(self.headers.get("Content-Length", "0"))
                self.rfile.read(length)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, fmt, *args):
                return

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        port = server.server_address[1]
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        env = os.environ.copy()
        env.pop("NEMO_TELEMETRY_ENABLED", None)
        env["STUB_ENDPOINT"] = f"http://127.0.0.1:{port}/v1"
        try:
            result = subprocess.run(
                [str(PYTHON), "one_row.py", "stub"],
                cwd=HERE,
                env=env,
                text=True,
                capture_output=True,
                timeout=180,
            )
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        row = json.loads(result.stdout.strip().splitlines()[-1])
        self.assertEqual(row["providers"], ["ollama-local"])
        self.assertEqual(row["file_providers"], ["ollama-local"])
        self.assertIs(row["telemetry_enabled"], False)
        self.assertEqual(row["blocked_hosts"], [])
        self.assertTrue(row["seen_hosts"])
        self.assertTrue(all(host == "127.0.0.1" for host in row["seen_hosts"]))
        self.assertIn("floats", row["answer"])
        self.assertTrue(row["finish_reasons"])
        self.assertTrue(all(reason == "stop" for reason in row["finish_reasons"]))
        self.assertNotIn("length", row["finish_reasons"])

    def test_connect_ex_to_a_public_address_does_not_connect(self):
        import socket

        from egress import BLOCKED_ERRNO, EgressGuard

        public = ("203.0.113.5", 443)
        orig_connect_ex = socket.socket.connect_ex
        with EgressGuard() as guard:
            self.assertIsNot(socket.socket.connect_ex, orig_connect_ex)
            blocked_sock = socket.socket()
            try:
                err = blocked_sock.connect_ex(public)
            finally:
                blocked_sock.close()
            self.assertEqual(err, BLOCKED_ERRNO)
            raised = socket.socket()
            try:
                with self.assertRaises(OSError):
                    raised.connect(public)
            finally:
                raised.close()
            listener = socket.socket()
            listener.bind(("127.0.0.1", 0))
            listener.listen(1)
            local = socket.socket()
            try:
                allowed = local.connect_ex(("127.0.0.1", listener.getsockname()[1]))
            finally:
                local.close()
                listener.close()
            self.assertEqual(allowed, 0)
        self.assertEqual(guard.blocked, ["203.0.113.5", "203.0.113.5"])
        self.assertEqual(guard.seen, ["127.0.0.1"])
        self.assertIs(socket.socket.connect_ex, orig_connect_ex)


if __name__ == "__main__":
    unittest.main()
