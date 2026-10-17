"""J2 harness and logging proxy for the local-builders study (amendment C).

Implements:
- proxy.py: loopback logging proxy between Aider and llama-server (F1, F3, F4, F5)
- runner.py: single-task Aider runner with max_reflections=29 and section-7 receipts (NB1, F2, F4, F7, F9, F10)
- workspace.py: clean git-archive task workspace builder (F7, F9)
- score.py: mergeability scorer with test sha256, git status, junitxml parity and held-out twin (F10, NB2)
- contain.py: unprivileged builder user, iptables owner rules and VM setup (F9)
- probe.py: section-8 containment probe verifying every refusal as builder (F9)
- preflight.py: J2 context sizing, top-5 logprobs check and non-exiting VRAM fit report (F5, F6, F13)
"""
from __future__ import annotations

from . import contain, preflight, probe, proxy, runner, score, workspace

__all__ = [
    "contain",
    "preflight",
    "probe",
    "proxy",
    "runner",
    "score",
    "workspace",
]
