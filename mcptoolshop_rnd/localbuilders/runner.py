"""Single-task J2 runner and section-7 receipt writer (NB1, F2, F4, F7, F9, F10, D1, D2, E1-E3).

Responsibilities:
- NB1: Runs Aider with `--no-stream`, `--model openai/<served_as>`, `OPENAI_API_BASE` pointing at the
  loopback logging proxy, and `OPENAI_API_KEY=local`. Wraps Aider's `Coder.create` so
  `coder.max_reflections = 29`, lifting Aider's default `max_reflections=3` so the proxy's 30-call
  cap is the real limit. Records Aider's pinned version.
- F2 & D-F1/D-F2: Enforces `--edit-format diff` for every model with no exceptions, and a pinned
  `--model-settings-file` with `examples_as_sys_msg: true`.
- F4: Passes `--auto-test --test-cmd "<target test command>" --no-auto-commits`.
- F7: Uses the fixed prompt template:
  `The test <node id> fails. Make it pass. Don't change any test file.`
- F9: Passes `--yes-always --no-check-update --analytics-disable --no-suggest-shell-commands --no-gitignore`,
  plus `--llm-history-file`, `--chat-history-file`, `--input-history-file`, and `--analytics-log`
  under `work_root` (outside the workspace). Executes Aider and scoring pytest as the unprivileged
  `builder` user by default (`use_sudo_builder=True`), refusing non-test runs without it.
- F10: Passes the target test file via `--read <test file>`, never as an editable file.
- Section 7 & Amendment E: Writes one receipt per run (including on `aider_timeout` or `score_timeout`),
  recording `generations_sha256`, injected sampling/kwargs, `transforms`, `reattach_thinking`
  (`synthetic` and `mismatch` counts, `reattach_max_turns`), `call_count`, and `cap_hits`.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from .contain import BUILDER_USER, builder_env, run_bounded_subprocess, wrap_as_builder
from .proxy import (
    DEFAULT_MAX_CALLS,
    DEFAULT_WALL_LIMIT_S,
    PINNED_AIDER_VERSION,
    LoggingProxyServer,
    ProxyState,
    load_candidate_config,
)
from .score import DEFAULT_SCORE_TIMEOUT_S, run_pytest_and_score
from .workspace import PreparedWorkspace, TaskSpec, build_workspace, is_test_path, normal_rel_path

MAX_REFLECTIONS = 29
EDIT_FORMAT = "diff"
TASK_PROMPT_TEMPLATE = "The test {node_id} fails. Make it pass. Don't change any test file."
DEFAULT_PARTITION = "trial:j2-wave1"

REQUIRED_RECEIPT_FIELDS = (
    "partition",
    "task_id",
    "slot_id",
    "difficulty",
    "model",
    "model_tag",
    "model_digest",
    "harness",
    "harness_version",
    "prompt_hash",
    "pins",
    "injected",
    "injected_sampling",
    "injected_kwargs",
    "transforms",
    "reattach_max_turns",
    "reattach_thinking",
    "effort",
    "thinking_tokens",
    "thinking_words_estimate",
    "output_tokens",
    "prompt_tokens",
    "truncation",
    "turns",
    "call_count",
    "cap_hits",
    "tool_calls",
    "retries",
    "wall_time_s",
    "peak_vram_mib",
    "energy_joules",
    "governor_tier_events",
    "preempted",
    "grade",
    "correct",
    "machine_line",
    "generations_sha256",
)

_EXAMPLES_SYS_MSG_TRUE_RE = re.compile(r"^\s*examples_as_sys_msg\s*:\s*true\s*(?:#.*)?$", re.IGNORECASE | re.MULTILINE)


class RunnerError(Exception):
    """Raised when runner inputs, editable files, model settings, or receipt fields are invalid."""


def format_task_prompt(node_id: str) -> str:
    """Render the fixed F7 task prompt template for `node_id`."""
    nid = str(node_id).strip()
    if not nid:
        raise RunnerError("node_id must not be empty")
    return TASK_PROMPT_TEMPLATE.format(node_id=nid)


def prompt_sha256(prompt_text: str) -> str:
    """Compute the sha256 hex digest of a task prompt string."""
    return hashlib.sha256(prompt_text.encode("utf-8")).hexdigest()


def render_model_settings_yaml(served_as: str) -> str:
    """Render the pinned Aider model-settings YAML for `served_as` (F2, NB1, D-F1, D-F2).

    Pins `examples_as_sys_msg: true` so Aider's few-shot examples arrive as system text rather
    than fake user/assistant turns across every candidate arm.
    """
    model_name = served_as.strip()
    if not model_name.startswith("openai/"):
        model_name = f"openai/{model_name}"
    return (
        f"- name: {model_name}\n"
        f"  edit_format: {EDIT_FORMAT}\n"
        f"  streaming: false\n"
        f"  examples_as_sys_msg: true\n"
    )


def write_model_settings_file(path: str | Path, served_as: str) -> Path:
    """Write the pinned Aider model-settings file with `examples_as_sys_msg: true` and return its Path."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(render_model_settings_yaml(served_as), encoding="utf-8", newline="\n")
    return p


def validate_model_settings_file(path: str | Path) -> None:
    """Assert that Aider's model-settings file pins `examples_as_sys_msg: true` (D-F1, D-F2)."""
    p = Path(path)
    if not p.is_file():
        raise RunnerError(f"model_settings_file not found: {p}")
    text = p.read_text(encoding="utf-8")
    if not _EXAMPLES_SYS_MSG_TRUE_RE.search(text):
        raise RunnerError(
            f"model_settings_file {p} must pin 'examples_as_sys_msg: true' for every candidate (D-F1, D-F2)"
        )


def build_aider_argv(
    *,
    served_as: str,
    model_settings_file: str | Path,
    test_cmd: str,
    test_file: str | Path,
    node_id: str,
    llm_history_file: str | Path,
    analytics_log: str | Path,
    chat_history_file: str | Path | None = None,
    input_history_file: str | Path | None = None,
    editable_files: list[str | Path] | None = None,
) -> list[str]:
    """Build the exact Aider CLI argument list (NB1, F2, F4, F7, F9, F10, D-F1, D-F2).

    - Never passes any test file as an editable file; the target test file is always passed
      via `--read <test_file>`.
    - Passes `--no-gitignore` and places `--chat-history-file` and `--input-history-file`
      outside the workspace (under `work_root`) so Aider's own files never dirty the workspace.
    - If `model_settings_file` exists on disk, validates that it pins `examples_as_sys_msg: true`.
    """
    settings_path = Path(model_settings_file)
    if settings_path.is_file():
        validate_model_settings_file(settings_path)

    norm_test = normal_rel_path(test_file)
    if not norm_test or not is_test_path(norm_test):
        raise RunnerError(f"target test_file must be a test path: {test_file!r}")

    edit_list: list[str] = []
    for fpath in editable_files or []:
        norm_f = normal_rel_path(fpath)
        if not norm_f:
            continue
        if norm_f == norm_test or is_test_path(norm_f):
            raise RunnerError(
                f"test file {norm_f!r} must never be passed to Aider as an editable file (F10)"
            )
        edit_list.append(norm_f)

    llm_hist_path = Path(llm_history_file)
    chat_hist = Path(chat_history_file) if chat_history_file is not None else llm_hist_path.parent / "chat-history.md"
    input_hist = Path(input_history_file) if input_history_file is not None else llm_hist_path.parent / "input-history"

    prompt = format_task_prompt(node_id)
    argv = [
        "--model",
        f"openai/{served_as.strip()}",
        "--no-stream",
        "--edit-format",
        EDIT_FORMAT,
        "--model-settings-file",
        str(model_settings_file),
        "--auto-test",
        "--test-cmd",
        str(test_cmd),
        "--no-auto-commits",
        "--no-gitignore",
        "--yes-always",
        "--no-check-update",
        "--analytics-disable",
        "--no-suggest-shell-commands",
        "--chat-history-file",
        str(chat_hist),
        "--input-history-file",
        str(input_hist),
        "--llm-history-file",
        str(llm_history_file),
        "--analytics-log",
        str(analytics_log),
        "--read",
        norm_test,
        "--message",
        prompt,
        *edit_list,
    ]
    return argv


def build_aider_command(
    *,
    python_executable: str = sys.executable,
    max_reflections: int = MAX_REFLECTIONS,
    builder_user: str | None = BUILDER_USER,
    use_sudo: bool = True,
    env: dict[str, str] | None = None,
    **aider_kwargs: Any,
) -> list[str]:
    """Build the full subprocess command invoking our `Coder.create` wrapper with `max_reflections=29`."""
    aider_argv = build_aider_argv(**aider_kwargs)
    cmd = [
        python_executable,
        "-m",
        "mcptoolshop_rnd.localbuilders.runner",
        "--aider-entrypoint",
        "--max-reflections",
        str(int(max_reflections)),
        "--",
        *aider_argv,
    ]
    if use_sudo and builder_user:
        return wrap_as_builder(cmd, env=env, builder_user=builder_user, use_sudo=True)
    return cmd


def create_coder_with_reflections(
    coder_cls: Any,
    *args: Any,
    max_reflections: int = MAX_REFLECTIONS,
    **kwargs: Any,
) -> Any:
    """Wrap `Coder.create(*args, **kwargs)` and set `coder.max_reflections = max_reflections` (NB1)."""
    coder = coder_cls.create(*args, **kwargs)
    coder.max_reflections = int(max_reflections)
    return coder


def run_aider_entrypoint(
    aider_argv: list[str],
    *,
    max_reflections: int = MAX_REFLECTIONS,
    coder_cls: Any = None,
    aider_main: Callable[[list[str]], int | None] | None = None,
) -> int:
    """Execute Aider's main entry point with `Coder.create` patched so `max_reflections=29` (NB1).

    Aider is an external program on the VM and is never imported at module load time; tests inject
    `coder_cls` and `aider_main` directly.
    """
    if coder_cls is None or aider_main is None:  # pragma: no cover (external VM program)
        from aider.coders.base_coder import Coder as _Coder  # type: ignore[import-not-found]
        from aider.main import main as _aider_main  # type: ignore[import-not-found]

        coder_cls = coder_cls or _Coder
        aider_main = aider_main or _aider_main

    orig_create = coder_cls.create

    def _wrapped_create(*args: Any, **kwargs: Any) -> Any:
        coder = orig_create(*args, **kwargs)
        coder.max_reflections = int(max_reflections)
        return coder

    coder_cls.create = _wrapped_create
    coder_cls.max_reflections = int(max_reflections)
    try:
        rc = aider_main(list(aider_argv))
        return int(rc or 0)
    finally:
        coder_cls.create = orig_create


def parse_analytics_log(analytics_path: str | Path) -> dict[str, int]:
    """Read Aider's `--analytics-log` JSONL file for malformed/failed edit and tool counts.

    Note on Aider's `aider/analytics.py`: `Analytics.event()` writes the JSONL entry to
    `self.logfile` (`--analytics-log`) unconditionally before checking `if not self.ph: return`
    (which `--analytics-disable` sets to `None`), so local JSONL event logging works even when
    PostHog telemetry is disabled.
    """
    p = Path(analytics_path)
    total = malformed = failed = retries = 0
    if not p.is_file():
        return {"total": 0, "malformed": 0, "failed": 0, "retries": 0}
    for raw in p.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line:
            continue
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(ev, dict):
            continue
        event_name = str(ev.get("event") or "")
        props = ev.get("properties") if isinstance(ev.get("properties"), dict) else {}
        if "message_send" in event_name or "litellm" in event_name or "edit" in event_name:
            total += 1
        if props.get("num_malformed_responses") or "malformed" in event_name:
            malformed += int(props.get("num_malformed_responses") or 1)
        if props.get("failed") or "error" in event_name or "failed" in event_name:
            failed += 1
        if "reflection" in event_name or "auto_test" in event_name:
            retries += 1
    return {
        "total": total,
        "malformed": malformed,
        "failed": failed,
        "retries": retries,
    }


def _failed_grade_for_reason(task: TaskSpec, reason: str) -> dict[str, Any]:
    """Build a failed grade_result dictionary when Aider or scoring times out."""
    return {
        "task_id": task.id,
        "passed": False,
        "correct": False,
        "reasons": [reason],
        "reason": reason,
        "counts": {"passed": 0, "failed": 0, "errors": 0, "skipped": 0, "xfail": 0},
        "baseline": dict(task.baseline),
        "target_nodes": list(task.target_nodes),
        "twin_nodes": list(task.twin_nodes),
    }


def build_receipt(
    *,
    task: TaskSpec,
    model_tag: str,
    model_digest: str,
    aider_version: str,
    pins: dict[str, Any],
    proxy_summary: dict[str, Any],
    grade_result: dict[str, Any],
    wall_time_s: float,
    machine_line: dict[str, Any],
    effort_raw: Any = None,
    effort_graded: str = "unsupported",
    peak_vram_mib: float | None = None,
    energy_joules: float | None = None,
    governor_tier_events: list[dict] | None = None,
    preempted: bool = False,
    tool_calls: dict[str, int] | None = None,
    retries: int | None = None,
    partition: str = DEFAULT_PARTITION,
) -> dict[str, Any]:
    """Construct a section-7 receipt and validate that every required field is present."""
    prompt_text = format_task_prompt(task.target_node_id)
    p_hash = prompt_sha256(prompt_text)

    injected = proxy_summary["injected"]
    call_count = int(proxy_summary["call_count"])
    calc_retries = retries if retries is not None else max(0, call_count - 1)
    tc = tool_calls or {"total": call_count, "malformed": 0, "failed": 0}

    transforms = list(proxy_summary.get("transforms") or injected.get("transforms") or [])
    reattach_max_turns = proxy_summary.get("reattach_max_turns", injected.get("reattach_max_turns"))
    raw_reattach = proxy_summary.get("reattach_thinking") or {}
    reattach_thinking = {
        "reattached": int(raw_reattach.get("reattached", 0)),
        "synthetic": int(raw_reattach.get("synthetic", 0)),
        "mismatch": int(raw_reattach.get("mismatch", 0)),
        "reattach_max_turns": reattach_max_turns,
    }

    thinking_tokens_raw = proxy_summary.get("thinking_tokens")
    thinking_tokens: int | None = int(thinking_tokens_raw) if thinking_tokens_raw is not None else None
    thinking_words_raw = proxy_summary.get("thinking_words_estimate")
    thinking_words_estimate: int | None = int(thinking_words_raw) if thinking_words_raw is not None else None

    full_pins = {
        "parent_commit": task.parent_commit,
        "model_digest": model_digest,
        "candidate_config_sha256": proxy_summary.get("config_sha256", ""),
        "edit_format": EDIT_FORMAT,
        "examples_as_sys_msg": True,
        "max_reflections": MAX_REFLECTIONS,
        "max_calls": proxy_summary.get("max_calls", DEFAULT_MAX_CALLS),
        "transforms": transforms,
        "reattach_max_turns": reattach_max_turns,
        **pins,
    }

    receipt: dict[str, Any] = {
        "partition": partition,
        "task_id": task.id,
        "slot_id": task.id,
        "difficulty": task.difficulty,
        "model": {
            "tag": model_tag,
            "digest": model_digest,
            "arm": proxy_summary.get("arm", model_tag),
        },
        "model_tag": model_tag,
        "model_digest": model_digest,
        "harness": {
            "name": "aider",
            "version": aider_version,
            "edit_format": EDIT_FORMAT,
            "examples_as_sys_msg": True,
            "max_reflections": MAX_REFLECTIONS,
        },
        "harness_version": aider_version,
        "prompt_hash": p_hash,
        "pins": full_pins,
        "injected": injected,
        "injected_sampling": injected["sampling"],
        "injected_kwargs": injected["chat_template_kwargs"],
        "transforms": transforms,
        "reattach_max_turns": reattach_max_turns,
        "reattach_thinking": reattach_thinking,
        "synthetic_turns": reattach_thinking["synthetic"],
        "mismatch_turns": reattach_thinking["mismatch"],
        "effort": {
            "raw_parameter": effort_raw if effort_raw is not None else injected["chat_template_kwargs"],
            "graded": effort_graded,
        },
        "thinking_tokens": thinking_tokens,
        "thinking_words_estimate": thinking_words_estimate,
        "output_tokens": int(proxy_summary["output_tokens"]),
        "prompt_tokens": int(proxy_summary["prompt_tokens"]),
        "truncation": {
            "truncated": bool(proxy_summary["truncated"]),
            "truncated_calls": int(proxy_summary["truncated_calls"]),
        },
        "turns": call_count,
        "call_count": call_count,
        "cap_hits": dict(proxy_summary["cap_hits"]),
        "tool_calls": {
            "total": int(tc.get("total", call_count)),
            "malformed": int(tc.get("malformed", 0)),
            "failed": int(tc.get("failed", 0)),
        },
        "retries": int(calc_retries),
        "wall_time_s": round(float(wall_time_s), 4),
        "peak_vram_mib": peak_vram_mib,
        "energy_joules": energy_joules,
        "governor_tier_events": list(governor_tier_events or []),
        "preempted": bool(preempted),
        "grade": grade_result,
        "correct": bool(grade_result.get("correct", False)),
        "machine_line": dict(machine_line),
        "generations_sha256": str(proxy_summary["generations_sha256"]),
    }
    validate_receipt(receipt)
    return receipt


def validate_receipt(receipt: dict[str, Any]) -> None:
    """Verify every required section-7 field is present and non-empty where mandatory."""
    missing = [field for field in REQUIRED_RECEIPT_FIELDS if field not in receipt]
    if missing:
        raise RunnerError(f"receipt missing required section-7 field(s): {missing}")
    if not receipt.get("generations_sha256") or len(str(receipt["generations_sha256"])) != 64:
        raise RunnerError("receipt generations_sha256 must be a 64-character sha256 hex digest")
    if not isinstance(receipt.get("injected"), dict):
        raise RunnerError("receipt injected must be a dict")
    if "sampling" not in receipt["injected"] or "chat_template_kwargs" not in receipt["injected"]:
        raise RunnerError("receipt injected must record both sampling and chat_template_kwargs")
    if not isinstance(receipt.get("cap_hits"), dict):
        raise RunnerError("receipt cap_hits must be a dict")


@dataclass
class RunTaskConfig:
    """Configuration for running a single J2 task through the proxy, Aider, and scorer."""

    source_repo: Path
    task: TaskSpec
    candidate_config_path: Path
    model_settings_file: Path
    served_as: str
    model_tag: str
    model_digest: str
    aider_version: str
    upstream_url: str
    work_root: Path
    receipt_path: Path
    machine_line: dict[str, Any]
    candidate: str | None = None
    pins: dict[str, Any] = field(default_factory=dict)
    editable_files: list[str] | None = None
    max_calls: int = DEFAULT_MAX_CALLS
    wall_limit_s: float = DEFAULT_WALL_LIMIT_S
    score_timeout_s: float = DEFAULT_SCORE_TIMEOUT_S
    use_sudo_builder: bool = True
    _test_allow_uncontained: bool = False
    peak_vram_mib: float | None = None
    energy_joules: float | None = None


def run_single_task(
    cfg: RunTaskConfig,
    *,
    aider_runner: Callable[[list[str], Path, dict[str, str]], int] | None = None,
    scorer_fn: Callable[[TaskSpec, PreparedWorkspace], dict] | None = None,
) -> dict[str, Any]:
    """Run one J2 task end-to-end: workspace -> proxy -> Aider -> score -> receipt.

    - Refuses non-test runs when `cfg.use_sudo_builder` is False (F9).
    - Validates that `cfg.model_settings_file` pins `examples_as_sys_msg: true` (D-F1, D-F2).
    - Catches `subprocess.TimeoutExpired` from Aider (`aider_timeout`) or scoring (`score_timeout`),
      killing the process group and always writing a failed receipt.
    """
    if not cfg.use_sudo_builder and not cfg._test_allow_uncontained:
        raise RunnerError("refusing non-test run with use_sudo_builder=False (F9 containment required)")

    cfg.work_root.mkdir(parents=True, exist_ok=True)
    if not cfg.model_settings_file.exists():
        write_model_settings_file(cfg.model_settings_file, cfg.served_as)
    validate_model_settings_file(cfg.model_settings_file)

    ws_dir = cfg.work_root / f"ws-{cfg.task.id}"
    home_dir = cfg.work_root / f"home-{cfg.task.id}"
    gen_path = cfg.work_root / f"generations-{cfg.task.id}.jsonl"
    llm_history = cfg.work_root / f"llm-history-{cfg.task.id}.md"
    chat_history = cfg.work_root / f"chat-history-{cfg.task.id}.md"
    input_history = cfg.work_root / f"input-history-{cfg.task.id}"
    analytics_log = cfg.work_root / f"analytics-{cfg.task.id}.jsonl"

    prepared = build_workspace(
        cfg.source_repo,
        cfg.task,
        ws_dir,
        home_dir=home_dir,
    )

    cand_cfg = load_candidate_config(cfg.candidate_config_path, candidate=cfg.candidate or cfg.served_as)
    state = ProxyState(
        upstream_url=cfg.upstream_url,
        config=cand_cfg,
        generations_path=gen_path,
        max_calls=cfg.max_calls,
        wall_limit_s=cfg.wall_limit_s,
    )

    aider_timed_out = False
    t0 = time.monotonic()
    with LoggingProxyServer(state) as proxy_srv:
        env = builder_env(proxy_port=proxy_srv.port, home_dir=prepared.home_dir)
        edit_files = cfg.editable_files if cfg.editable_files is not None else cfg.task.allowed_paths
        cmd = build_aider_command(
            served_as=cfg.served_as,
            model_settings_file=cfg.model_settings_file,
            test_cmd=cfg.task.test_cmd,
            test_file=cfg.task.test_file,
            node_id=cfg.task.target_node_id,
            llm_history_file=llm_history,
            chat_history_file=chat_history,
            input_history_file=input_history,
            analytics_log=analytics_log,
            editable_files=edit_files,
            use_sudo=cfg.use_sudo_builder,
            env=env,
        )
        try:
            if aider_runner is not None:
                aider_runner(cmd, prepared.workspace_dir, env)
            else:
                run_bounded_subprocess(
                    cmd,
                    cwd=prepared.workspace_dir,
                    env=env,
                    timeout=float(cfg.wall_limit_s) + 30.0,
                )
        except subprocess.TimeoutExpired:
            aider_timed_out = True
    wall_s = time.monotonic() - t0

    # Score ONLY after Aider has exited and the proxy has closed.
    if aider_timed_out:
        grade_res = _failed_grade_for_reason(cfg.task, "aider_timeout")
    else:
        try:
            if scorer_fn is not None:
                grade_res = scorer_fn(cfg.task, prepared)
            else:
                grade_res = run_pytest_and_score(
                    cfg.task,
                    prepared.workspace_dir,
                    prepared.pre_test_hashes,
                    env=env,
                    aider_running=False,
                    use_sudo_builder=cfg.use_sudo_builder,
                    proxy_port=proxy_srv.port,
                    timeout=cfg.score_timeout_s,
                    _test_allow_uncontained=cfg._test_allow_uncontained,
                )
        except subprocess.TimeoutExpired:
            grade_res = _failed_grade_for_reason(cfg.task, "score_timeout")

    analytics = parse_analytics_log(analytics_log)
    summary = state.summary()
    receipt = build_receipt(
        task=cfg.task,
        model_tag=cfg.model_tag,
        model_digest=cfg.model_digest,
        aider_version=cfg.aider_version,
        pins=cfg.pins,
        proxy_summary=summary,
        grade_result=grade_res,
        wall_time_s=wall_s,
        machine_line=cfg.machine_line,
        peak_vram_mib=cfg.peak_vram_mib,
        energy_joules=cfg.energy_joules,
        tool_calls=analytics if analytics["total"] > 0 else None,
        retries=analytics["retries"] if analytics["retries"] > 0 else None,
    )
    cfg.receipt_path.parent.mkdir(parents=True, exist_ok=True)
    cfg.receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return receipt


def main(argv: list[str] | None = None) -> int:
    """Entry point supporting `--aider-entrypoint --max-reflections 29 -- <aider args...>`."""
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] == "--aider-entrypoint":
        max_refl = MAX_REFLECTIONS
        idx = 1
        while idx < len(args):
            if args[idx] == "--":
                idx += 1
                break
            if args[idx] == "--max-reflections" and idx + 1 < len(args):
                max_refl = int(args[idx + 1])
                idx += 2
            else:
                idx += 1
        aider_args = args[idx:]
        return run_aider_entrypoint(aider_args, max_reflections=max_refl)
    raise RunnerError(
        "usage: python -m mcptoolshop_rnd.localbuilders.runner --aider-entrypoint [--max-reflections 29] -- <aider args>"
    )


if __name__ == "__main__":
    sys.exit(main())
