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
import os
import re
import shutil
import stat
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from .contain import BUILDER_USER, builder_env, run_bounded_subprocess, venv_bin_dir, wrap_as_builder
from .preflight import PreflightError, verify_installed_aider
from .proxy import (
    DEFAULT_MAX_CALLS,
    DEFAULT_WALL_LIMIT_S,
    PINNED_AIDER_VERSION,
    PROXY_FILE_MODE,
    LoggingProxyServer,
    ProxyState,
    load_candidate_config,
)
from .score import DEFAULT_SCORE_TIMEOUT_S, run_pytest_and_score
from .workspace import (
    PreparedWorkspace,
    TaskSpec,
    WorkspaceError,
    build_workspace,
    fill_command_placeholders,
    is_test_path,
    normal_rel_path,
)

MAX_REFLECTIONS = 29
EDIT_FORMAT = "diff"
TASK_PROMPT_TEMPLATE = "The test {node_id} fails. Make it pass. Don't change any test file."
DEFAULT_PARTITION = "trial:j2-wave1"

HISTORY_DIR_MODE = 0o711
HISTORY_FILE_MODE = 0o600
VENV_DIR_MODE = 0o755
VENV_EXEC_MODE = 0o755
VENV_FILE_MODE = 0o644
DEFAULT_SETUP_TIMEOUT_S = 600.0
CHAT_HISTORY_FILENAME = "chat-history.md"
INPUT_HISTORY_FILENAME = "input-history"

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
    "aider_version",
    "synthetic_strings_verified",
    "install_cmd",
    "install_exit_code",
    "pip_freeze_sha256",
    "venv_python_version",
    "python_version",
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


def _default_chown_builder(
    path: Path,
    builder_user: str,
    *,
    allow_uncontained: bool = False,
) -> None:
    """Chown `path` to `builder_user`, raising `RunnerError` on the VM if `chown` fails."""
    try:
        shutil.chown(path, user=builder_user)
    except (LookupError, PermissionError, AttributeError, NotImplementedError, OSError) as exc:
        if not allow_uncontained:
            raise RunnerError(
                f"failed to chown {path} to {builder_user!r} on VM: {exc}"
            ) from exc


def prepare_task_history_files(
    history_dir: str | Path,
    *,
    builder_user: str = BUILDER_USER,
    allow_uncontained: bool = False,
    chown_fn: Callable[[Path, str], None] | None = None,
    chmod_fn: Callable[[Path, int], None] | None = None,
) -> tuple[Path, Path]:
    """Create per-task `chat-history.md` and `input-history` owned by `builder` (`0600`) in an un-listable directory (`0711`).

    The parent directory is set to mode `0711` (`rwx--x--x`) so `builder` can traverse into it to open
    the two known filenames (`chat-history.md` and `input-history`, mode `0600`, owned by `builder`),
    while `os.listdir(history_dir)` and creating any other file in `history_dir` are refused.
    """
    hdir = Path(history_dir).resolve()
    hdir.mkdir(parents=True, exist_ok=True)
    do_chmod = chmod_fn or os.chmod
    do_chown = chown_fn or (
        lambda p, u: _default_chown_builder(p, u, allow_uncontained=allow_uncontained)
    )

    if hdir.parent.exists():
        do_chmod(hdir.parent, HISTORY_DIR_MODE)
    do_chmod(hdir, HISTORY_DIR_MODE)

    chat_history = hdir / CHAT_HISTORY_FILENAME
    input_history = hdir / INPUT_HISTORY_FILENAME
    for fpath in (chat_history, input_history):
        if not fpath.exists():
            fpath.write_text("", encoding="utf-8")
        do_chmod(fpath, HISTORY_FILE_MODE)
        do_chown(fpath, builder_user)

    return chat_history, input_history


def prepare_builder_log_files(
    *paths: str | Path,
    builder_user: str = BUILDER_USER,
    allow_uncontained: bool = False,
    chown_fn: Callable[[Path, str], None] | None = None,
    chmod_fn: Callable[[Path, int], None] | None = None,
) -> list[Path]:
    """Pre-create Aider log files in `work_root` with mode `0600` owned by `builder_user`."""
    do_chmod = chmod_fn or os.chmod
    do_chown = chown_fn or (
        lambda p, u: _default_chown_builder(p, u, allow_uncontained=allow_uncontained)
    )
    out: list[Path] = []
    for raw_p in paths:
        fpath = Path(raw_p).resolve()
        fpath.parent.mkdir(parents=True, exist_ok=True)
        if not fpath.exists():
            fpath.write_text("", encoding="utf-8")
        do_chmod(fpath, PROXY_FILE_MODE)
        do_chown(fpath, builder_user)
        out.append(fpath)
    return out


@dataclass(frozen=True)
class TaskEnvSetupResult:
    """Result of per-task environment setup (`work_root/venv-<task>`) run as `root` before Aider."""

    ok: bool
    venv_dir: Path
    python_executable: Path
    install_cmd: str
    install_exit_code: int
    pip_freeze_sha256: str | None
    venv_python_version: str | None = None
    stdout: str = ""
    stderr: str = ""

    @property
    def python_version(self) -> str | None:
        return self.venv_python_version


def venv_python_path(venv_dir: str | Path) -> Path:
    """Return the path to the `python` interpreter inside `venv_dir`."""
    vbin = venv_bin_dir(venv_dir)
    if (vbin / "python").is_file():
        return vbin / "python"
    if (vbin / "python.exe").is_file():
        return vbin / "python.exe"
    return vbin / ("python.exe" if os.name == "nt" else "python")


def resolve_test_cmd_for_venv(
    test_cmd: str,
    venv_dir: str | Path | None = None,
    *,
    bank_dir: str | Path | None = None,
) -> str:
    """Fill `{venv}` and `{bank}` placeholders in a command without rewriting any command prefix."""
    try:
        return fill_command_placeholders(test_cmd, venv_dir=venv_dir, bank_dir=bank_dir)
    except WorkspaceError as exc:
        raise RunnerError(str(exc)) from exc


def root_install_env(
    venv_dir: str | Path,
    *,
    base_env: dict[str, str] | None = None,
) -> dict[str, str]:
    """Build the environment for `root` task setup with network allowed and `UV_PROJECT_ENVIRONMENT` pointed at `venv_dir`."""
    vdir = Path(venv_dir).resolve()
    vbin = str(venv_bin_dir(vdir))
    env = dict(base_env if base_env is not None else os.environ)
    for blocked_key in (
        "PIP_NO_INDEX",
        "NPM_CONFIG_OFFLINE",
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "http_proxy",
        "https_proxy",
    ):
        env.pop(blocked_key, None)
    existing_path = env.get("PATH", "")
    env["PATH"] = f"{vbin}{os.pathsep}{existing_path}" if existing_path else vbin
    env["VIRTUAL_ENV"] = str(vdir)
    env["UV_PROJECT_ENVIRONMENT"] = str(vdir)
    return env


def lock_venv_for_builder(venv_dir: str | Path) -> None:
    """Ensure `venv_dir` (`work_root/venv-<task>`) is readable and executable by `builder` (`0755`/`0644`), never writable."""
    vdir = Path(venv_dir).resolve()
    if not vdir.exists():
        return
    os.chmod(vdir, VENV_DIR_MODE)
    for root_str, dirnames, filenames in os.walk(vdir):
        root_p = Path(root_str)
        for dname in dirnames:
            dp = root_p / dname
            if not dp.is_symlink():
                os.chmod(dp, VENV_DIR_MODE)
        in_bin = root_p.name in ("bin", "Scripts")
        for fname in filenames:
            fp = root_p / fname
            if fp.is_symlink():
                continue
            cur_mode = stat.S_IMODE(fp.stat().st_mode)
            if in_bin or (cur_mode & stat.S_IXUSR):
                os.chmod(fp, VENV_EXEC_MODE)
            else:
                os.chmod(fp, VENV_FILE_MODE)


def freeze_venv_sha256(
    venv_dir: str | Path,
    venv_python: str | Path | None = None,
    *,
    env: dict[str, str] | None = None,
    run_cmd: Callable[..., subprocess.CompletedProcess] | None = None,
) -> str:
    """Return the sha256 hex digest of `pip freeze` for `venv_dir`."""
    vdir = Path(venv_dir).resolve()
    vpy = Path(venv_python) if venv_python is not None else venv_python_path(vdir)
    run_env = env if env is not None else root_install_env(vdir)
    runner_fn = run_cmd or (
        lambda cmd, **kw: subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            timeout=60,
            **kw,
        )
    )

    vbin = venv_bin_dir(vdir)
    has_pip = (vbin / "pip").is_file() or (vbin / "pip.exe").is_file()
    if has_pip or run_cmd is not None:
        res = runner_fn([str(vpy), "-m", "pip", "freeze"], cwd=str(vdir), env=run_env)
        if res.returncode == 0:
            norm = (res.stdout or "").replace("\r\n", "\n")
            return hashlib.sha256(norm.encode("utf-8")).hexdigest()

    # Fallback when `uv sync --frozen` or `--without-pip` produced a venv without `pip` installed inside it
    metadata_code = (
        "import importlib.metadata as m, sys; "
        "dists = sorted({f'{d.metadata[\"Name\"]}=={d.version}' for d in m.distributions() if d.metadata.get('Name')}, key=str.lower); "
        "sys.stdout.write('\\n'.join(dists) + ('\\n' if dists else ''))"
    )
    res_meta = runner_fn([str(vpy), "-c", metadata_code], cwd=str(vdir), env=run_env)
    if res_meta.returncode != 0:
        raise RunnerError(f"failed to freeze venv {vdir}: {res_meta.stderr.strip()}")
    norm = (res_meta.stdout or "").replace("\r\n", "\n")
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()


def venv_python_version(
    venv_dir: str | Path,
    venv_python: str | Path | None = None,
    *,
    env: dict[str, str] | None = None,
    run_cmd: Callable[..., subprocess.CompletedProcess] | None = None,
) -> str:
    """Return the `<venv python> --version` string (e.g. `'Python 3.12.8'`) for `venv_dir`."""
    vdir = Path(venv_dir).resolve()
    vpy = Path(venv_python) if venv_python is not None else venv_python_path(vdir)
    run_env = env if env is not None else root_install_env(vdir)
    runner_fn = run_cmd or (
        lambda cmd, **kw: subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
            **kw,
        )
    )
    res = runner_fn([str(vpy), "--version"], cwd=str(vdir), env=run_env)
    if res.returncode != 0:
        raise RunnerError(f"failed to read python --version for venv {vdir}: {(res.stderr or '').strip()}")
    raw_ver = (res.stdout or "").strip() or (res.stderr or "").strip()
    if raw_ver:
        return raw_ver.splitlines()[0].strip()
    return f"Python {sys.version.split()[0]}"


def setup_task_venv(
    task: TaskSpec | dict,
    workspace_dir: str | Path,
    work_root: str | Path,
    *,
    bank_dir: str | Path | None = None,
    base_python: str | Path = sys.executable,
    base_env: dict[str, str] | None = None,
    timeout: float = DEFAULT_SETUP_TIMEOUT_S,
    with_pip: bool | None = None,
    run_cmd: Callable[..., subprocess.CompletedProcess] | None = None,
) -> TaskEnvSetupResult:
    """Create `work_root/venv-<task>`, fill `{venv}`/`{bank}` and run `install` as `root` with network allowed, and lock permissions."""
    spec = task if isinstance(task, TaskSpec) else TaskSpec.from_dict(task, bank_dir=bank_dir)
    wroot = Path(work_root).resolve()
    ws_dir = Path(workspace_dir).resolve()
    venv_dir = wroot / f"venv-{spec.id}"
    try:
        venv_dir.relative_to(ws_dir)
        raise RunnerError(f"per-task venv {venv_dir} must be outside workspace {ws_dir}")
    except ValueError:
        pass

    eff_bank_dir = bank_dir if bank_dir is not None else spec.bank_dir
    filled_install_cmd = (
        resolve_test_cmd_for_venv(spec.install_cmd, venv_dir, bank_dir=eff_bank_dir)
        if spec.install_cmd.strip()
        else ""
    )

    wroot.mkdir(parents=True, exist_ok=True)
    need_pip = bool(with_pip) if with_pip is not None else ("pip" in filled_install_cmd)

    vpy = venv_python_path(venv_dir)
    if not vpy.is_file():
        venv_args = [str(base_python), "-m", "venv", *([] if need_pip else ["--without-pip"]), str(venv_dir)]
        venv_res = subprocess.run(
            venv_args,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout,
        )
        if venv_res.returncode != 0 and need_pip:
            venv_res = subprocess.run(
                [str(base_python), "-m", "venv", "--without-pip", str(venv_dir)],
                capture_output=True,
                text=True,
                check=False,
                timeout=timeout,
            )
        if venv_res.returncode != 0:
            return TaskEnvSetupResult(
                ok=False,
                venv_dir=venv_dir,
                python_executable=vpy,
                install_cmd=filled_install_cmd,
                install_exit_code=int(venv_res.returncode or 1),
                pip_freeze_sha256=None,
                venv_python_version=None,
                stdout=venv_res.stdout or "",
                stderr=venv_res.stderr or "",
            )
        vpy = venv_python_path(venv_dir)

    install_env = root_install_env(venv_dir, base_env=base_env)
    out_str = ""
    err_str = ""
    install_rc = 0

    if filled_install_cmd:
        try:
            if run_cmd is not None:
                res = run_cmd(filled_install_cmd, cwd=str(ws_dir), env=install_env, shell=True)
            else:
                res = subprocess.run(
                    filled_install_cmd,
                    shell=True,
                    cwd=str(ws_dir),
                    env=install_env,
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=timeout,
                )
            install_rc = int(res.returncode)
            out_str = res.stdout or ""
            err_str = res.stderr or ""
        except subprocess.TimeoutExpired:
            lock_venv_for_builder(venv_dir)
            return TaskEnvSetupResult(
                ok=False,
                venv_dir=venv_dir,
                python_executable=vpy,
                install_cmd=filled_install_cmd,
                install_exit_code=-1,
                pip_freeze_sha256=None,
                venv_python_version=None,
                stdout="",
                stderr="install_timeout",
            )

    if install_rc != 0:
        lock_venv_for_builder(venv_dir)
        return TaskEnvSetupResult(
            ok=False,
            venv_dir=venv_dir,
            python_executable=vpy,
            install_cmd=filled_install_cmd,
            install_exit_code=install_rc,
            pip_freeze_sha256=None,
            venv_python_version=None,
            stdout=out_str,
            stderr=err_str,
        )

    vpy = venv_python_path(venv_dir)
    freeze_sha = freeze_venv_sha256(venv_dir, vpy, env=install_env, run_cmd=run_cmd)
    py_ver = venv_python_version(venv_dir, vpy, env=install_env, run_cmd=run_cmd)
    lock_venv_for_builder(venv_dir)
    return TaskEnvSetupResult(
        ok=True,
        venv_dir=venv_dir,
        python_executable=vpy,
        install_cmd=filled_install_cmd,
        install_exit_code=0,
        pip_freeze_sha256=freeze_sha,
        venv_python_version=py_ver,
        stdout=out_str,
        stderr=err_str,
    )


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
    """Build a failed grade_result dictionary when setup fails or Aider/scoring times out."""
    return {
        "task_id": task.id,
        "status": reason,
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
    synthetic_strings_verified: bool = True,
    install_cmd: str | None = None,
    install_exit_code: int = 0,
    pip_freeze_sha256: str | None = None,
    venv_python_version: str | None = None,
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

    effective_install_cmd = task.install_cmd if install_cmd is None else str(install_cmd)
    effective_install_rc = int(install_exit_code)
    effective_freeze_sha = str(pip_freeze_sha256) if pip_freeze_sha256 is not None else None
    effective_py_ver = str(venv_python_version).strip() if venv_python_version is not None else None

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
        "aider_version": aider_version,
        "synthetic_strings_verified": bool(synthetic_strings_verified),
        "install_cmd": effective_install_cmd,
        "install_exit_code": effective_install_rc,
        "pip_freeze_sha256": effective_freeze_sha,
        "venv_python_version": effective_py_ver,
        "python_version": effective_py_ver,
        "edit_format": EDIT_FORMAT,
        "examples_as_sys_msg": True,
        "max_reflections": MAX_REFLECTIONS,
        "max_calls": proxy_summary.get("max_calls", DEFAULT_MAX_CALLS),
        "transforms": transforms,
        "reattach_max_turns": reattach_max_turns,
        **pins,
    }

    grade_reason = str(grade_result.get("reason") or "")
    status_str = (
        "setup_failed"
        if grade_reason == "setup_failed"
        else ("passed" if grade_result.get("correct") else "failed")
    )

    receipt: dict[str, Any] = {
        "partition": partition,
        "task_id": task.id,
        "slot_id": task.id,
        "difficulty": task.difficulty,
        "status": status_str,
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
            "synthetic_strings_verified": bool(synthetic_strings_verified),
            "edit_format": EDIT_FORMAT,
            "examples_as_sys_msg": True,
            "max_reflections": MAX_REFLECTIONS,
        },
        "harness_version": aider_version,
        "aider_version": aider_version,
        "synthetic_strings_verified": bool(synthetic_strings_verified),
        "install_cmd": effective_install_cmd,
        "install_exit_code": effective_install_rc,
        "pip_freeze_sha256": effective_freeze_sha,
        "venv_python_version": effective_py_ver,
        "python_version": effective_py_ver,
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
    if str(receipt.get("aider_version", "")).strip() != PINNED_AIDER_VERSION:
        raise RunnerError(
            f"receipt aider_version must be {PINNED_AIDER_VERSION!r}; got {receipt.get('aider_version')!r}"
        )
    if receipt.get("synthetic_strings_verified") is not True:
        raise RunnerError("receipt synthetic_strings_verified must be True")
    if not isinstance(receipt.get("install_cmd"), str):
        raise RunnerError("receipt install_cmd must be a string")
    if not isinstance(receipt.get("install_exit_code"), int) or isinstance(receipt.get("install_exit_code"), bool):
        raise RunnerError("receipt install_exit_code must be an integer")
    freeze_sha = receipt.get("pip_freeze_sha256")
    if freeze_sha is not None and (not isinstance(freeze_sha, str) or len(freeze_sha) != 64):
        raise RunnerError("receipt pip_freeze_sha256 must be None or a 64-character sha256 hex digest")
    py_ver = receipt.get("venv_python_version")
    if py_ver is not None and (not isinstance(py_ver, str) or not py_ver.strip()):
        raise RunnerError("receipt venv_python_version must be None or a non-empty string")
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
    bank_dir: Path | str | None = None
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
    setup_runner: Callable[[TaskSpec, Path, Path], TaskEnvSetupResult] | None = None,
    aider_runner: Callable[[list[str], Path, dict[str, str]], int] | None = None,
    scorer_fn: Callable[[TaskSpec, PreparedWorkspace], dict] | None = None,
) -> dict[str, Any]:
    """Run one J2 task end-to-end: workspace -> setup_task_venv -> proxy -> Aider -> score -> receipt.

    - Refuses non-test runs when `cfg.use_sudo_builder` is False (F9).
    - Verifies the installed Aider version (`0.86.1`) and synthetic reply strings on `CoderPrompts`
      and `EditBlockPrompts` before launching Aider.
    - Creates the two per-task history files (`work_root/history-<task>/chat-history.md` and
      `input-history`) owned by `builder` (`0600`) inside a `0711` directory `builder` cannot list.
    - Runs per-task environment setup as `root` with network allowed into `work_root/venv-<task>`
      (`0755`/`0644`, readable and executable by `builder`, not writable). If the install fails,
      ends the task as `setup_failed` with no Aider run and no score.
    - Validates that `cfg.model_settings_file` pins `examples_as_sys_msg: true` (D-F1, D-F2).
    - Catches `subprocess.TimeoutExpired` from Aider (`aider_timeout`) or scoring (`score_timeout`),
      killing the process group and always writing a failed receipt.
    """
    if not cfg.use_sudo_builder and not cfg._test_allow_uncontained:
        raise RunnerError("refusing non-test run with use_sudo_builder=False (F9 containment required)")
    if str(cfg.aider_version).strip() != PINNED_AIDER_VERSION:
        raise RunnerError(
            f"cfg.aider_version {cfg.aider_version!r} does not match pinned {PINNED_AIDER_VERSION!r}"
        )
    try:
        aider_check = verify_installed_aider()
    except PreflightError as exc:
        raise RunnerError(str(exc)) from exc

    cfg.work_root.mkdir(parents=True, exist_ok=True)
    if not cfg.model_settings_file.exists():
        write_model_settings_file(cfg.model_settings_file, cfg.served_as)
    validate_model_settings_file(cfg.model_settings_file)

    ws_dir = cfg.work_root / f"ws-{cfg.task.id}"
    home_dir = cfg.work_root / f"home-{cfg.task.id}"
    history_dir = cfg.work_root / f"history-{cfg.task.id}"
    chat_history, input_history = prepare_task_history_files(
        history_dir,
        allow_uncontained=cfg._test_allow_uncontained,
    )
    gen_path = cfg.work_root / f"generations-{cfg.task.id}.jsonl"
    llm_history = cfg.work_root / f"llm-history-{cfg.task.id}.md"
    analytics_log = cfg.work_root / f"analytics-{cfg.task.id}.jsonl"
    prepare_builder_log_files(
        llm_history,
        analytics_log,
        allow_uncontained=cfg._test_allow_uncontained,
    )

    eff_bank_dir = cfg.bank_dir if cfg.bank_dir is not None else cfg.task.bank_dir
    prepared = build_workspace(
        cfg.source_repo,
        cfg.task,
        ws_dir,
        home_dir=home_dir,
        bank_dir=eff_bank_dir,
    )

    setup_res = (
        setup_runner(cfg.task, prepared.workspace_dir, cfg.work_root)
        if setup_runner is not None
        else setup_task_venv(cfg.task, prepared.workspace_dir, cfg.work_root, bank_dir=eff_bank_dir)
    )

    cand_cfg = load_candidate_config(cfg.candidate_config_path, candidate=cfg.candidate or cfg.served_as)
    state = ProxyState(
        upstream_url=cfg.upstream_url,
        config=cand_cfg,
        generations_path=gen_path,
        max_calls=cfg.max_calls,
        wall_limit_s=cfg.wall_limit_s,
    )

    if not setup_res.ok or setup_res.install_exit_code != 0:
        grade_res = _failed_grade_for_reason(cfg.task, "setup_failed")
        wall_s = 0.0
    else:
        aider_timed_out = False
        resolved_test_cmd = resolve_test_cmd_for_venv(
            cfg.task.test_cmd,
            setup_res.venv_dir,
            bank_dir=eff_bank_dir,
        )
        t0 = time.monotonic()
        with LoggingProxyServer(state) as proxy_srv:
            env = builder_env(
                proxy_port=proxy_srv.port,
                home_dir=prepared.home_dir,
                venv_dir=setup_res.venv_dir,
            )
            edit_files = cfg.editable_files if cfg.editable_files is not None else cfg.task.allowed_paths
            cmd = build_aider_command(
                served_as=cfg.served_as,
                model_settings_file=cfg.model_settings_file,
                test_cmd=resolved_test_cmd,
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
                        venv_dir=setup_res.venv_dir,
                        bank_dir=eff_bank_dir,
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
        aider_version=aider_check["aider_version"],
        synthetic_strings_verified=bool(aider_check["synthetic_strings_verified"]),
        install_cmd=setup_res.install_cmd,
        install_exit_code=setup_res.install_exit_code,
        pip_freeze_sha256=setup_res.pip_freeze_sha256,
        venv_python_version=setup_res.venv_python_version,
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
    os.chmod(cfg.receipt_path, PROXY_FILE_MODE)
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
