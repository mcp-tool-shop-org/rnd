"""Lock Data Designer to local Ollama before it is imported.

The library reads NEMO_TELEMETRY_ENABLED and DATA_DESIGNER_HOME at import time.
Call arm() first. import_data_designer() refuses to load the library if the
telemetry switch is unset or any value other than the string "false".
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
HOME = HERE / "home"
PROVIDERS_FILE = HOME / "model_providers.yaml"
CONFIGS_FILE = HOME / "model_configs.yaml"
PYTHON_PIN = (HERE / "python-pin.txt").read_text(encoding="utf-8").strip()
DATA_DESIGNER_PIN = "0.9.4"
LOCAL_PROVIDER = "ollama-local"
LOCAL_ENDPOINT = "http://127.0.0.1:11434/v1"
LOCAL_MODEL = "mistral-small:24b"
# First 12 hex digits, same pin as experiments/natural-errors/build.py.
LOCAL_DIGEST = "8039dd90c113"
DUMMY_KEY_ENV = "OLLAMA_LOCAL_API_KEY"
FORBIDDEN_TEXT = (
    "integrate.api.nvidia.com",
    "api.openai.com",
    "openrouter.ai",
    "events.telemetry.data.nvidia.com",
    "cloud",
)


def refuse_cloud(model: str) -> None:
    if "cloud" in model.lower():
        raise SystemExit(f"refusing {model!r}: local Ollama only")


def arm(home: Path | None = None) -> Path:
    """Set the lockdown environment. Does not import data_designer."""
    home = Path(home) if home is not None else HOME
    os.environ["NEMO_TELEMETRY_ENABLED"] = "false"
    os.environ["DATA_DESIGNER_HOME"] = str(home)
    os.environ[DUMMY_KEY_ENV] = "ollama-local"
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
    return home


def assert_telemetry_env() -> None:
    value = os.environ.get("NEMO_TELEMETRY_ENABLED")
    if value is None:
        raise RuntimeError("NEMO_TELEMETRY_ENABLED is unset at import time")
    if value != "false":
        raise RuntimeError(f"NEMO_TELEMETRY_ENABLED must be 'false' before import, got {value!r}")


def require_locked_files(home: Path | None = None) -> None:
    home = Path(home) if home is not None else HOME
    for path in (home / "model_providers.yaml", home / "model_configs.yaml"):
        if not path.exists():
            raise RuntimeError(f"{path.name} is missing; refusing to let Data Designer write its defaults")
        text = path.read_text(encoding="utf-8").lower()
        for needle in FORBIDDEN_TEXT:
            if needle in text:
                raise RuntimeError(f"{path.name} contains {needle!r}")


def assert_python_pin() -> None:
    running = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    if running != PYTHON_PIN:
        raise RuntimeError(f"Python {running} != pin {PYTHON_PIN}")


def import_data_designer():
    """Import data_designer only after the telemetry switch is false."""
    assert_telemetry_env()
    assert_python_pin()
    import data_designer
    from data_designer.config.version import get_library_version
    from data_designer.engine.models.telemetry import TELEMETRY_ENABLED

    version = get_library_version()
    if version != DATA_DESIGNER_PIN:
        raise RuntimeError(f"data-designer {version} != pin {DATA_DESIGNER_PIN}")
    if TELEMETRY_ENABLED:
        raise RuntimeError("telemetry is on after import; NEMO_TELEMETRY_ENABLED was not false first")
    return data_designer


def provider_rows(providers) -> list[dict]:
    rows = []
    for provider in providers:
        rows.append(
            {
                "name": provider.name,
                "endpoint": provider.endpoint.rstrip("/"),
                "provider_type": provider.provider_type,
                "api_key": provider.api_key,
            }
        )
    return rows


def assert_provider_list(providers) -> list[dict]:
    rows = provider_rows(providers)
    if [row["name"] for row in rows] != [LOCAL_PROVIDER]:
        raise RuntimeError(f"provider list must be [{LOCAL_PROVIDER!r}], got {rows}")
    row = rows[0]
    if row["endpoint"] != LOCAL_ENDPOINT:
        raise RuntimeError(f"endpoint {row['endpoint']!r} is not {LOCAL_ENDPOINT}")
    if row["provider_type"] != "openai":
        raise RuntimeError(f"provider_type {row['provider_type']!r} is not openai")
    if row["api_key"] != DUMMY_KEY_ENV:
        raise RuntimeError("api_key must be the dummy env var name, not a pasted key")
    return rows
