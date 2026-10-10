"""Per-call timeout for device calls (R&D, 2026-10-09): 60 s default, matching
switchyard's adapter. A call that exceeds the bound raises CallTimeout; the
runners record a "hang" outcome for it and stop that device for the rest of
the run (no silent retry). The worker is a daemon thread: a hung device call
cannot be joined, and ending the process is the hang protocol's answer at
session level. --call-timeout 0 disables the bound.
"""
from __future__ import annotations

import threading

DEFAULT_CALL_TIMEOUT_S = 60.0


class CallTimeout(Exception):
    """A device call exceeded the per-call timeout."""


def timed_call(timeout_s: float, fn, *args, **kwargs):
    """fn(*args, **kwargs), raising CallTimeout after timeout_s seconds.

    timeout_s <= 0 disables the bound. Exceptions from fn propagate unchanged.
    """
    if timeout_s is None or timeout_s <= 0:
        return fn(*args, **kwargs)
    box: dict = {}

    def _run() -> None:
        try:
            box["value"] = fn(*args, **kwargs)
        except BaseException as exc:
            box["error"] = exc

    worker = threading.Thread(target=_run, daemon=True, name="npu-probe-call")
    worker.start()
    worker.join(timeout_s)
    if worker.is_alive():
        raise CallTimeout("call exceeded %gs" % timeout_s)
    if "error" in box:
        raise box["error"]
    return box["value"]
