"""Single-task J2 runner and section-7 receipt writer (NB1, F2, F4, F7, F9, F10).

Responsibilities:
- NB1: Runs Aider with `--no-stream`, `--model openai/<served_as>`, `OPENAI_API_BASE` pointing at the
  loopback logging proxy, and `OPENAI_API_KEY=local`. Wraps Aider's `Coder.create` so
  `coder.max_reflections = 29`, lifting Aider's default `max_reflections=3` so the proxy's 30-call
  cap is the real limit. Records Aider's pinned version.
- F2: Enforces `--edit-format diff` for every model with no exceptions, and a pinned
  `--model-settings-file`.
- F4: Passes `--auto-test --test-cmd "<target test command>" --no-auto-commits`.
- F7: Uses the fixed prompt template:
  `The test <node id> fails. Make it pass. Don't change any test file.`
- F9: Passes `--yes-always --no-check-update --analytics-disable --no-suggest-shell-commands`, plus
  `--llm-history-file` and `--analytics-log`. Executes Aider as the unprivileged `builder` user.
- F10: Passes the target test file via `--read <test file>`, never as an editable file.
- Section 7: Writes one receipt per run with every required field, including `generations_sha256`,
  the injected sampling and `chat_template_kwargs`, `call_count`, and `cap_hits`.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from .contain import BUILDER_USER, builder_env, wrap_as_builder
from .proxy import DEFAULT_MAX_CALLS, DEFAULT_WALL_LIMIT_S, LoggingProxyServer, ProxyState, load_candidate_config
from .score import run_pytest_and_score, score_task
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
    "effort",
    "thinking_tokens",
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


class RunnerError(Exception):
    """Raised when runner inputs, editable files, or receipt fields are invalid."""


def format_task_prompt(node_id: str) -> str:
    """Render the fixed F7 task prompt template for `node_id`."""
    nid = str(node_id).strip()
    if not nid:
        raise RunnerError("node_id must not be empty")
    return TASK_PROMPT_TEMPLATE.format(node_id=nid)


def prompt_sha256(prompt_text: str) -> str:
    """Compute the sha256 hex digest of a task prompt string."""
    return hashlib.sha256(prompt_text.encode("utf-8")).hexdigest()


def build_aider_argv(
    *,
    served_as: str,
    model_settings_file: str | Path,
    test_cmd: str,
    test_file: str | Path,
    node_id: str,
    llm_history_file: str | Path,
    analytics_log: str | Path,
    editable_files: list[str | Path] | None = None,
) -> list[str]:
    """Build the exact Aider CLI argument list (NB1, F2, F4, F7, F9, F10).

    Never passes any test file as an editable file; the target test file is always passed
    via `--read <test_file>`.
    """
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
        "--yes-always",
        "--no-check-update",
        "--analytics-disable",
        "--no-suggest-shell-commands",
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
    use_sudo: bool = False,
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
        return wrap_as_builder(cmd, builder_user=builder_user, use_sudo=True)
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
    """Read Aider's `--analytics-log` JSONL file for malformed/failed edit and tool counts."""
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

    full_pins = {
        "parent_commit": task.parent_commit,
        "model_digest": model_digest,
        "candidate_config_sha256": proxy_summary.get("config_sha256", ""),
        "edit_format": EDIT_FORMAT,
        "max_reflections": MAX_REFLECTIONS,
        "max_calls": proxy_summary.get("max_calls", DEFAULT_MAX_CALLS),
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
            "max_reflections": MAX_REFLECTIONS,
        },
        "harness_version": aider_version,
        "prompt_hash": p_hash,
        "pins": full_pins,
        "injected": injected,
        "injected_sampling": injected["sampling"],
        "injected_kwargs": injected["chat_template_kwargs"],
        "effort": {
            "raw_parameter": effort_raw if effort_raw is not None else injected["chat_template_kwargs"],
            "graded": effort_graded,
        },
        "thinking_tokens": int(proxy_summary["thinking_tokens"]),
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
    pins: dict[str, Any] = field(default_factory=dict)
    editable_files: list[str] | None = None
    max_calls: int = DEFAULT_MAX_CALLS
    wall_limit_s: float = DEFAULT_WALL_LIMIT_S
    use_sudo_builder: bool = False
    peak_vram_mib: float | None = None
    energy_joules: float | None = None


def run_single_task(
    cfg: RunTaskConfig,
    *,
    aider_runner: Callable[[list[str], Path, dict[str, str]], int] | None = None,
    scorer_fn: Callable[[TaskSpec, PreparedWorkspace], dict] | None = None,
) -> dict[str, Any]:
    """Run one J2 task end-to-end: workspace -> proxy -> Aider -> score -> receipt."""
    cfg.work_root.mkdir(parents=True, exist_ok=True)
    ws_dir = cfg.work_root / f"ws-{cfg.task.id}"
    home_dir = cfg.work_root / f"home-{cfg.task.id}"
    gen_path = cfg.work_root / f"generations-{cfg.task.id}.jsonl"
    llm_history = cfg.work_root / f"llm-history-{cfg.task.id}.md"
    analytics_log = cfg.work_root / f"analytics-{cfg.task.id}.jsonl"

    prepared = build_workspace(
        cfg.source_repo,
        cfg.task,
        ws_dir,
        home_dir=home_dir,
    )

    cand_cfg = load_candidate_config(cfg.candidate_config_path)
    state = ProxyState(
        upstream_url=cfg.upstream_url,
        config=cand_cfg,
        generations_path=gen_path,
        max_calls=cfg.max_calls,
        wall_limit_s=cfg.wall_limit_s,
    )

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
            analytics_log=analytics_log,
            editable_files=edit_files,
            use_sudo=cfg.use_sudo_builder,
        )
        if aider_runner is not None:
            aider_runner(cmd, prepared.workspace_dir, env)
        else:  # pragma: no cover (external VM execution)
            subprocess.run(
                cmd,
                cwd=str(prepared.workspace_dir),
                env=env,
                capture_output=True,
                text=True,
                check=False,
                timeout=int(cfg.wall_limit_s) + 30,
            )
    wall_s = time.monotonic() - t0

    # Score ONLY after Aider has exited and the proxy has closed.
    if scorer_fn is not None:
        grade_res = scorer_fn(cfg.task, prepared)
    else:  # pragma: no cover (VM pytest execution)
        grade_res = run_pytest_and_score(
            cfg.task,
            prepared.workspace_dir,
            prepared.pre_test_hashes,
            env=prepared.env,
            aider_running=False,
        )

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
    raise RunnerError("usage: python -m mcptoolshop_rnd.localbuilders.runner --aider-entrypoint [--max-reflections 29] -- <aider args>")


if __name__ == "__main__":
    sys.exit(main())
