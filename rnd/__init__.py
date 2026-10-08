"""Compatibility name for mcptoolshop_rnd.

The code lives in `mcptoolshop_rnd`, the import name that always works. An
unrelated PyPI package also installs a top-level `rnd`; if both are installed in
one environment, that one may replace this shim. The `rnd` command does not
depend on this package: it runs `mcptoolshop_rnd.cli:main`.
"""

import importlib
import sys

import mcptoolshop_rnd as _pkg

__version__ = _pkg.__version__

_SUBMODULES = ("catalog", "cli", "frontmatter", "model", "readouts", "release", "store")

for _name in _SUBMODULES:
    _mod = importlib.import_module(f"mcptoolshop_rnd.{_name}")
    sys.modules[f"{__name__}.{_name}"] = _mod
    globals()[_name] = _mod

__all__ = ["__version__", *_SUBMODULES]
