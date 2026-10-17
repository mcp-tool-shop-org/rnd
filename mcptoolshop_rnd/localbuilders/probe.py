"""Section-8 containment probe for J2 (F9).

Run as the unprivileged `builder` user before any counted run.
Must prove that EVERY ONE of the following ten actions is refused, and exit non-zero if ANY succeeds:
1. `curl https://example.com`
2. A raw `socket.create_connection` to an external IP (`93.184.216.34:443`)
3. DNS resolution (`socket.getaddrinfo("example.com", 443)`)
4. `pip install`
5. `git push`
6. A direct connection to `llama-server`'s loopback port, with `HTTP_PROXY` / `HTTPS_PROXY` unset
7. Reading the task bank directory
8. Reading the held-out twins directory
9. Reading the receipts directory
10. A write outside the task workspace
"""
from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

CHECK_NAMES = (
    "curl_https",
    "raw_socket_external",
    "dns_resolution",
    "pip_install",
    "git_push",
    "direct_llama_server",
    "read_task_bank",
    "read_twins",
    "read_receipts",
    "write_outside_workspace",
)


@dataclass(frozen=True)
class ProbePaths:
    """Paths and ports probed by `run_probe`."""

    workspace_dir: Path
    outside_dir: Path
    bank_dir: Path
    twins_dir: Path
    receipts_dir: Path
    llama_port: int = 18081
    external_ip: str = "93.184.216.34"
    external_port: int = 443
    dns_host: str = "example.com"


def _attempt_curl_https(paths: ProbePaths) -> tuple[bool, str]:
    """Attempt `curl https://example.com`. Returns `(action_succeeded, detail)`."""
    proc = subprocess.run(
        ["curl", "-sS", "--max-time", "5", "https://example.com"],
        cwd=str(paths.workspace_dir),
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    if proc.returncode == 0:
        return True, "curl https://example.com succeeded (exit 0)"
    return False, f"refused (exit {proc.returncode})"


def _attempt_raw_socket_external(paths: ProbePaths) -> tuple[bool, str]:
    """Attempt raw TCP connection to an external IP. Returns `(action_succeeded, detail)`."""
    try:
        with socket.create_connection((paths.external_ip, paths.external_port), timeout=3.0):
            return True, f"connected to {paths.external_ip}:{paths.external_port}"
    except OSError as exc:
        return False, f"refused ({exc})"


def _attempt_dns_resolution(paths: ProbePaths) -> tuple[bool, str]:
    """Attempt DNS resolution of an external hostname. Returns `(action_succeeded, detail)`."""
    try:
        res = socket.getaddrinfo(paths.dns_host, 443)
        return True, f"resolved {paths.dns_host} -> {res[0][4] if res else 'addrs'}"
    except OSError as exc:
        return False, f"refused ({exc})"


def _attempt_pip_install(paths: ProbePaths) -> tuple[bool, str]:
    """Attempt `pip install`. Returns `(action_succeeded, detail)`."""
    env = dict(os.environ)
    env["PIP_NO_INDEX"] = "1"
    proc = subprocess.run(
        [sys.executable, "-m", "pip", "install", "--dry-run", "nonexistent-j2-containment-probe-pkg"],
        cwd=str(paths.workspace_dir),
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=15,
    )
    if proc.returncode == 0:
        return True, "pip install succeeded (exit 0)"
    return False, f"refused (exit {proc.returncode})"


def _attempt_git_push(paths: ProbePaths) -> tuple[bool, str]:
    """Attempt `git push` from the workspace. Returns `(action_succeeded, detail)`."""
    proc = subprocess.run(
        ["git", "push", "https://example.com/repo.git", "HEAD"],
        cwd=str(paths.workspace_dir),
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    if proc.returncode == 0:
        return True, "git push succeeded (exit 0)"
    return False, f"refused (exit {proc.returncode})"


def _attempt_direct_llama_server(paths: ProbePaths) -> tuple[bool, str]:
    """Attempt direct connection to `llama-server`'s port with `HTTP_PROXY` unset."""
    saved_http = os.environ.pop("HTTP_PROXY", None)
    saved_https = os.environ.pop("HTTPS_PROXY", None)
    saved_http_l = os.environ.pop("http_proxy", None)
    saved_https_l = os.environ.pop("https_proxy", None)
    try:
        with socket.create_connection(("127.0.0.1", int(paths.llama_port)), timeout=3.0):
            return True, f"connected directly to llama-server port {paths.llama_port} with HTTP_PROXY unset"
    except OSError as exc:
        return False, f"refused ({exc})"
    finally:
        if saved_http is not None:
            os.environ["HTTP_PROXY"] = saved_http
        if saved_https is not None:
            os.environ["HTTPS_PROXY"] = saved_https
        if saved_http_l is not None:
            os.environ["http_proxy"] = saved_http_l
        if saved_https_l is not None:
            os.environ["https_proxy"] = saved_https_l


def _attempt_read_dir(target: Path, label: str) -> tuple[bool, str]:
    """Attempt to list or read files in a protected directory (`bank`, `twins`, `receipts`)."""
    try:
        entries = list(os.listdir(target))
        for name in entries:
            child = target / name
            if child.is_file():
                _ = child.read_bytes()
        return True, f"read {label} at {target} ({len(entries)} entries)"
    except OSError as exc:
        return False, f"refused ({exc})"


def _attempt_write_outside_workspace(paths: ProbePaths) -> tuple[bool, str]:
    """Attempt to write a file outside the task workspace."""
    probe_file = Path(paths.outside_dir) / ".j2-containment-probe-write"
    try:
        probe_file.write_text("breach\n", encoding="utf-8")
        try:
            probe_file.unlink()
        except OSError:  # pragma: no cover
            pass
        return True, f"wrote outside workspace at {probe_file}"
    except OSError as exc:
        return False, f"refused ({exc})"


DEFAULT_ATTEMPTS: dict[str, Callable[[ProbePaths], tuple[bool, str]]] = {
    "curl_https": _attempt_curl_https,
    "raw_socket_external": _attempt_raw_socket_external,
    "dns_resolution": _attempt_dns_resolution,
    "pip_install": _attempt_pip_install,
    "git_push": _attempt_git_push,
    "direct_llama_server": _attempt_direct_llama_server,
    "read_task_bank": lambda p: _attempt_read_dir(p.bank_dir, "task_bank"),
    "read_twins": lambda p: _attempt_read_dir(p.twins_dir, "twins"),
    "read_receipts": lambda p: _attempt_read_dir(p.receipts_dir, "receipts"),
    "write_outside_workspace": _attempt_write_outside_workspace,
}


def _evaluate_attempt(
    fn_or_flag: bool | Callable[[ProbePaths], tuple[bool, str] | bool | None],
    paths: ProbePaths,
) -> tuple[bool, str]:
    """Normalize an attempt callable or injected flag into `(refused: bool, detail: str)`.

    Remember: in a containment probe, an action that *succeeds* means containment FAILED
    (`refused = False`). An action that fails/raises means containment HELD (`refused = True`).
    """
    if isinstance(fn_or_flag, bool):
        action_succeeded = fn_or_flag
        return (not action_succeeded), ("action succeeded (BREACH)" if action_succeeded else "refused (injected)")
    try:
        res = fn_or_flag(paths)
    except Exception as exc:  # noqa: BLE001
        return True, f"refused ({exc})"
    if isinstance(res, tuple) and len(res) == 2:
        action_succeeded, detail = bool(res[0]), str(res[1])
        return (not action_succeeded), detail
    if isinstance(res, bool):
        action_succeeded = res
        return (not action_succeeded), ("action succeeded (BREACH)" if action_succeeded else "refused")
    return False, "action returned without error (BREACH)"


def run_probe(
    paths: ProbePaths,
    *,
    injected_attempts: dict[str, bool | Callable] | None = None,
) -> dict:
    """Run all ten section-8 containment checks and return the probe report.

    `passed` is True ONLY if all ten checks were refused (`refused == True`).
    If any forbidden check succeeds (`refused == False`), `passed` is False and
    `breaches` lists the checks that succeeded.
    """
    overrides = injected_attempts or {}
    unknown = set(overrides) - set(CHECK_NAMES)
    if unknown:
        raise ValueError(f"unknown probe check(s): {sorted(unknown)}")

    results: dict[str, dict] = {}
    breaches: list[str] = []

    for name in CHECK_NAMES:
        attempt = overrides.get(name, DEFAULT_ATTEMPTS[name])
        refused, detail = _evaluate_attempt(attempt, paths)
        results[name] = {
            "refused": refused,
            "action_succeeded": not refused,
            "detail": detail,
        }
        if not refused:
            breaches.append(name)

    return {
        "passed": len(breaches) == 0,
        "breaches": breaches,
        "checks": results,
    }


def main(argv: list[str] | None = None) -> int:
    """CLI entry point for running the containment probe as `builder` on the VM."""
    parser = argparse.ArgumentParser(description="Run the J2 section-8 containment probe.")
    parser.add_argument("--workspace", required=True, help="Task workspace directory")
    parser.add_argument("--outside", default="/root", help="Directory outside the task workspace")
    parser.add_argument("--bank", default="/root/j2/bank", help="Protected task bank directory")
    parser.add_argument("--twins", default="/root/j2/twins", help="Protected held-out twins directory")
    parser.add_argument("--receipts", default="/root/j2/receipts", help="Protected receipts directory")
    parser.add_argument("--llama-port", type=int, default=18081, help="llama-server loopback port")
    args = parser.parse_args(argv)

    paths = ProbePaths(
        workspace_dir=Path(args.workspace),
        outside_dir=Path(args.outside),
        bank_dir=Path(args.bank),
        twins_dir=Path(args.twins),
        receipts_dir=Path(args.receipts),
        llama_port=args.llama_port,
    )
    report = run_probe(paths)
    print(json.dumps(report, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
