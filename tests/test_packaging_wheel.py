"""Every package under the source tree ships in the wheel (rnd 1.1.12: localbuilders was left out of the explicit list)."""

import fnmatch
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = (ROOT / "pyproject.toml").read_text(encoding="utf-8")


class Packaging(unittest.TestCase):
    def test_every_subpackage_is_included(self):
        block = re.search(r"(?ms)^\[tool\.setuptools\.packages\.find\]\s*\ninclude = \[([^\]]*)\]", PYPROJECT)
        self.assertIsNotNone(block, "pyproject.toml must find packages by pattern")
        patterns = re.findall(r'"([^"]+)"', block.group(1))
        packages = sorted(".".join(p.parent.relative_to(ROOT).parts) for top in ("mcptoolshop_rnd", "rnd")
                          for p in (ROOT / top).rglob("__init__.py"))
        self.assertIn("mcptoolshop_rnd.localbuilders", packages)
        for pkg in packages:
            self.assertTrue(any(fnmatch.fnmatch(pkg, pat) for pat in patterns), f"{pkg} is not in the wheel")

    def test_the_vm_setup_script_ships(self):
        self.assertRegex(PYPROJECT, r'(?m)^"mcptoolshop_rnd\.localbuilders" = \["\*\.sh"\]$')
        self.assertTrue((ROOT / "mcptoolshop_rnd" / "localbuilders" / "setup_vm.sh").is_file())


if __name__ == "__main__":
    unittest.main()
