"""What a Colab VM is: GPU, driver, CUDA, host CPU and RAM, disk, Python.

Run on the VM with `colab exec -s <session> -f probe.py`. It prints one JSON object.
It reads no secrets and writes nothing. (google.colab.ai is not probed: its key is
UI-only, and the call hangs from the CLI's kernel.)
"""

import json
import os
import platform
import subprocess


def sh(cmd: str) -> str:
    try:
        return subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60, check=False).stdout.strip()
    except Exception as e:  # noqa: BLE001 (a probe line must never stop the probe)
        return f"ERR {e}"


print(
    json.dumps(
        {
            "gpu": sh("nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader"),
            "cuda": sh("nvidia-smi | grep -o 'CUDA Version: [0-9.]*'"),
            "cpu": sh("nproc") + " cores," + sh("grep -m1 'model name' /proc/cpuinfo | cut -d: -f2"),
            "ram_gb": round(os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") / 2**30, 1),
            "disk": sh("df -h / | tail -1"),
            "python": platform.python_version(),
        },
        indent=1,
    )
)
