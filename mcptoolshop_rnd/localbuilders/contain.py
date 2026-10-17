"""Containment configuration and Colab VM lockdown for J2 (F9).

Responsibilities:
- Executes Aider and task test runs as an unprivileged `builder` user.
- Generates and applies `iptables -m owner --uid-owner builder` (and `ip6tables`) rules allowing
  TCP only to the logging proxy's loopback port: blocking `llama-server`'s port, DNS (UDP/TCP 53),
  and all internet/external traffic.
- Verifies no Google Drive mount is present on the Colab VM.
- Locks the task bank, held-out twins, and receipts directories to `0700` (`root:root`) so
  `builder` cannot read or traverse them.
- Sets offline environment pins (`LITELLM_LOCAL_MODEL_COST_MAP=True`, `PIP_NO_INDEX=1`,
  `NPM_CONFIG_OFFLINE=true`, `GIT_CONFIG_NOSYSTEM=1`).
"""
from __future__ import annotations

import os
import stat
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

BUILDER_USER = "builder"
DEAD_PROXY = "http://127.0.0.1:9"
SETUP_SCRIPT_PATH = Path(__file__).resolve().parent / "setup_vm.sh"


class ContainmentError(Exception):
    """Raised when containment setup or pre-checks fail."""


@dataclass(frozen=True)
class ContainmentConfig:
    """Configuration for VM and process containment (F9)."""

    builder_user: str = BUILDER_USER
    proxy_port: int = 18080
    llama_port: int = 18081
    bank_dir: Path = Path("/root/j2/bank")
    twins_dir: Path = Path("/root/j2/twins")
    receipts_dir: Path = Path("/root/j2/receipts")


def builder_env(
    *,
    proxy_port: int,
    home_dir: str | Path,
    base_env: dict[str, str] | None = None,
) -> dict[str, str]:
    """Return the locked-down environment dictionary for `builder` processes (F2, F9, NB1)."""
    source = base_env if base_env is not None else os.environ
    home = str(Path(home_dir).resolve())
    env: dict[str, str] = {}
    for k in ("PATH", "SystemRoot", "SYSTEMROOT", "COMSPEC", "WINDIR", "TMP", "TEMP", "TMPDIR", "LANG"):
        if k in source:
            env[k] = source[k]
    env.update(
        {
            "HOME": home,
            "USERPROFILE": home,
            "USER": BUILDER_USER,
            "LOGNAME": BUILDER_USER,
            "OPENAI_API_BASE": f"http://127.0.0.1:{int(proxy_port)}/v1",
            "OPENAI_API_KEY": "local",
            "LITELLM_LOCAL_MODEL_COST_MAP": "True",
            "PIP_NO_INDEX": "1",
            "NPM_CONFIG_OFFLINE": "true",
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": str(Path(home) / ".gitconfig"),
            "GIT_TERMINAL_PROMPT": "0",
            "HTTP_PROXY": DEAD_PROXY,
            "HTTPS_PROXY": DEAD_PROXY,
            "NO_PROXY": "127.0.0.1,localhost",
        }
    )
    return env


def iptables_commands(
    *,
    builder_user: str = BUILDER_USER,
    proxy_port: int = 18080,
    llama_port: int = 18081,
) -> list[list[str]]:
    """Return the exact `iptables` and `ip6tables` owner rules for `builder` (F9).

    Order of OUTPUT rules for `--uid-owner builder`:
    1. Reject TCP to `127.0.0.1:<llama_port>` explicitly so `builder` never reaches `llama-server`.
    2. Reject UDP and TCP port 53 (DNS) so `builder` cannot resolve names.
    3. Allow TCP only to `127.0.0.1:<proxy_port>` (the loopback logging proxy).
    4. Reject all other IPv4 and IPv6 traffic from `builder`.
    """
    if int(proxy_port) == int(llama_port):
        raise ContainmentError("proxy_port and llama_port must differ")
    p_port = str(int(proxy_port))
    l_port = str(int(llama_port))
    return [
        [
            "iptables",
            "-A",
            "OUTPUT",
            "-p",
            "tcp",
            "-d",
            "127.0.0.1",
            "--dport",
            l_port,
            "-m",
            "owner",
            "--uid-owner",
            builder_user,
            "-j",
            "REJECT",
            "--reject-with",
            "tcp-reset",
        ],
        [
            "iptables",
            "-A",
            "OUTPUT",
            "-p",
            "udp",
            "--dport",
            "53",
            "-m",
            "owner",
            "--uid-owner",
            builder_user,
            "-j",
            "REJECT",
        ],
        [
            "iptables",
            "-A",
            "OUTPUT",
            "-p",
            "tcp",
            "--dport",
            "53",
            "-m",
            "owner",
            "--uid-owner",
            builder_user,
            "-j",
            "REJECT",
            "--reject-with",
            "tcp-reset",
        ],
        [
            "iptables",
            "-A",
            "OUTPUT",
            "-p",
            "tcp",
            "-d",
            "127.0.0.1",
            "--dport",
            p_port,
            "-m",
            "owner",
            "--uid-owner",
            builder_user,
            "-j",
            "ACCEPT",
        ],
        [
            "iptables",
            "-A",
            "OUTPUT",
            "-m",
            "owner",
            "--uid-owner",
            builder_user,
            "-j",
            "REJECT",
        ],
        [
            "ip6tables",
            "-A",
            "OUTPUT",
            "-m",
            "owner",
            "--uid-owner",
            builder_user,
            "-j",
            "REJECT",
        ],
    ]


def check_no_drive_mount(
    *,
    mounts_text: str | None = None,
    drive_paths: tuple[str | Path, ...] = ("/content/drive", "/content/gdrive"),
) -> tuple[bool, str]:
    """Verify no Google Drive mount is present on the Colab VM (F9)."""
    if mounts_text is None:
        mounts_file = Path("/proc/mounts")
        mounts_text = mounts_file.read_text(encoding="utf-8") if mounts_file.is_file() else ""
    for line in mounts_text.splitlines():
        lower = line.lower()
        if "/content/drive" in lower or "/content/gdrive" in lower or "drive.google" in lower or "fuse.drive" in lower:
            return False, f"Google Drive mount found in /proc/mounts: {line.strip()}"
    for dp in drive_paths:
        p = Path(dp)
        if p.exists() and any(p.iterdir()):
            return False, f"Google Drive mount directory is non-empty: {p}"
    return True, ""


def lock_secret_directories(*dirs: str | Path) -> list[Path]:
    """Ensure bank, twins, and receipts directories exist with mode `0700` (unreadable by `builder`)."""
    locked: list[Path] = []
    for d in dirs:
        p = Path(d).resolve()
        p.mkdir(parents=True, exist_ok=True)
        os.chmod(p, stat.S_IRWXU)
        locked.append(p)
    return locked


def wrap_as_builder(
    cmd: list[str],
    *,
    builder_user: str = BUILDER_USER,
    use_sudo: bool = True,
) -> list[str]:
    """Wrap `cmd` so it executes as the unprivileged `builder` user on the VM."""
    if not use_sudo:
        return list(cmd)
    return ["sudo", "-u", builder_user, "-n", "--", *cmd]


def apply_vm_containment(
    config: ContainmentConfig,
    *,
    run_cmd: Callable[[list[str]], subprocess.CompletedProcess] | None = None,
    mounts_text: str | None = None,
    drive_paths: tuple[str | Path, ...] = ("/content/drive", "/content/gdrive"),
) -> dict:
    """Apply full F9 VM containment: check no Drive mount, create `builder`, lock dirs, add iptables."""
    ok_drive, why = check_no_drive_mount(mounts_text=mounts_text, drive_paths=drive_paths)
    if not ok_drive:
        raise ContainmentError(why)

    runner = run_cmd or (
        lambda c: subprocess.run(c, capture_output=True, text=True, check=False, timeout=30)
    )

    # Create unprivileged builder user if not already present
    id_res = runner(["id", "-u", config.builder_user])
    if id_res.returncode != 0:
        add_res = runner(["useradd", "--system", "--no-create-home", "--shell", "/bin/sh", config.builder_user])
        if add_res.returncode != 0:
            raise ContainmentError(f"useradd {config.builder_user} failed: {add_res.stderr.strip()}")

    locked = lock_secret_directories(config.bank_dir, config.twins_dir, config.receipts_dir)

    rules = iptables_commands(
        builder_user=config.builder_user,
        proxy_port=config.proxy_port,
        llama_port=config.llama_port,
    )
    for rule in rules:
        res = runner(rule)
        if res.returncode != 0:
            raise ContainmentError(f"command {' '.join(rule)} failed: {res.stderr.strip()}")

    return {
        "builder_user": config.builder_user,
        "proxy_port": config.proxy_port,
        "llama_port": config.llama_port,
        "locked_dirs": [str(p) for p in locked],
        "iptables_rules_applied": len(rules),
    }


def render_setup_script(config: ContainmentConfig | None = None) -> str:
    """Return the shell script text for locking down a Colab VM for J2 runs."""
    cfg = config or ContainmentConfig()
    rules = "\n".join(" ".join(r) for r in iptables_commands(
        builder_user=cfg.builder_user,
        proxy_port=cfg.proxy_port,
        llama_port=cfg.llama_port,
    ))
    return f"""#!/usr/bin/env bash
# Colab VM containment setup for local-builders J2 (amendment C, F9).
set -euo pipefail

BUILDER_USER="${{BUILDER_USER:-{cfg.builder_user}}}"
PROXY_PORT="${{PROXY_PORT:-{cfg.proxy_port}}}"
LLAMA_PORT="${{LLAMA_PORT:-{cfg.llama_port}}}"
BANK_DIR="${{BANK_DIR:-{cfg.bank_dir.as_posix()}}}"
TWINS_DIR="${{TWINS_DIR:-{cfg.twins_dir.as_posix()}}}"
RECEIPTS_DIR="${{RECEIPTS_DIR:-{cfg.receipts_dir.as_posix()}}}"

# 1. Refuse if Google Drive is mounted on the VM.
if grep -qiE '/content/drive|/content/gdrive|fuse\\.drive' /proc/mounts 2>/dev/null; then
  echo "FATAL: Google Drive is mounted on this VM; refusing to proceed." >&2
  exit 1
fi
if [ -d /content/drive ] && [ -n "$(ls -A /content/drive 2>/dev/null)" ]; then
  echo "FATAL: /content/drive is non-empty; refusing to proceed." >&2
  exit 1
fi

# 2. Create the unprivileged builder user if missing.
if ! id -u "$BUILDER_USER" >/dev/null 2>&1; then
  useradd --system --no-create-home --shell /bin/sh "$BUILDER_USER"
fi

# 3. Lock task bank, held-out twins, and receipts directories to root:root 0700.
mkdir -p "$BANK_DIR" "$TWINS_DIR" "$RECEIPTS_DIR"
chown root:root "$BANK_DIR" "$TWINS_DIR" "$RECEIPTS_DIR"
chmod 0700 "$BANK_DIR" "$TWINS_DIR" "$RECEIPTS_DIR"

# 4. Apply iptables and ip6tables owner rules for builder.
{rules}

# 5. Export offline environment defaults for builder subshells.
export LITELLM_LOCAL_MODEL_COST_MAP=True
export PIP_NO_INDEX=1
export NPM_CONFIG_OFFLINE=true
export GIT_CONFIG_NOSYSTEM=1
"""
