"""The package survives the clash with the unrelated PyPI `rnd`.

The code lives in mcptoolshop_rnd; rnd/ is a compatibility shim. Another package
that installs a top-level rnd/ can replace the shim, so the real package, its
`python -m` entry and the `rnd` console script must not depend on rnd/.
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import mcptoolshop_rnd

REPO = Path(__file__).resolve().parent.parent
PYPROJECT = (REPO / "pyproject.toml").read_text(encoding="utf-8")


def run_py(cwd, *args):
    env = {k: v for k, v in os.environ.items() if k not in ("PYTHONPATH", "RND_ROOT")}
    return subprocess.run([sys.executable, *args], cwd=cwd, env=env, capture_output=True, text=True, timeout=60)


class ShimTests(unittest.TestCase):
    def test_rnd_is_an_alias(self):
        import rnd
        import rnd.cli
        import rnd.store
        self.assertIs(rnd.store, mcptoolshop_rnd.store)
        self.assertIs(rnd.cli, mcptoolshop_rnd.cli)
        self.assertIs(sys.modules["rnd.release"], mcptoolshop_rnd.release)
        self.assertEqual(rnd.__version__, mcptoolshop_rnd.__version__)
        from rnd import catalog, frontmatter, model, readouts
        self.assertIs(catalog, mcptoolshop_rnd.catalog)
        self.assertEqual({frontmatter, model, readouts},
                         {mcptoolshop_rnd.frontmatter, mcptoolshop_rnd.model, mcptoolshop_rnd.readouts})


class WithoutTheShimTests(unittest.TestCase):
    """A copy of mcptoolshop_rnd alone, then with an unrelated rnd/ beside it."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        shutil.copytree(REPO / "mcptoolshop_rnd", self.tmp / "mcptoolshop_rnd",
                        ignore=shutil.ignore_patterns("__pycache__"))

    def check_works(self):
        r = run_py(self.tmp, "-c", "import mcptoolshop_rnd, mcptoolshop_rnd.store, mcptoolshop_rnd.cli; "
                                   "print(mcptoolshop_rnd.__version__)")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.strip(), mcptoolshop_rnd.__version__)
        r = run_py(self.tmp, "-m", "mcptoolshop_rnd", "--version")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn(mcptoolshop_rnd.__version__, r.stdout)
        target = re.search(r'^rnd = "([\w.]+):(\w+)"', PYPROJECT, re.M)
        r = run_py(self.tmp, "-c", f"import importlib, sys; m = importlib.import_module({target.group(1)!r}); "
                                   f"sys.exit(getattr(m, {target.group(2)!r})(['--version']))")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn(mcptoolshop_rnd.__version__, r.stdout)

    def test_no_rnd_package(self):
        self.check_works()

    def test_clashing_rnd_package(self):
        clash = self.tmp / "rnd"
        clash.mkdir()
        (clash / "__init__.py").write_text("raise ImportError('the unrelated rnd package')\n", encoding="utf-8")
        self.check_works()


class ManifestTests(unittest.TestCase):
    def test_manifest_points_at_the_real_package(self):
        self.assertIn('packages = ["mcptoolshop_rnd", "rnd"]', PYPROJECT)
        self.assertIn('version = { attr = "mcptoolshop_rnd.__version__" }', PYPROJECT)
        self.assertRegex(PYPROJECT, r'(?m)^rnd = "mcptoolshop_rnd\.cli:main"$')

    def test_version_matches_the_tag(self):
        try:
            r = subprocess.run(["git", "describe", "--exact-match", "--tags", "HEAD"], cwd=REPO,
                               capture_output=True, text=True, timeout=30)
        except OSError:
            self.skipTest("git not available")
        if r.returncode != 0:
            self.skipTest("HEAD carries no tag")
        dirty = subprocess.run(["git", "diff", "--quiet", "HEAD", "--", "mcptoolshop_rnd/__init__.py"],
                               cwd=REPO, timeout=30)
        if dirty.returncode != 0:
            self.skipTest("the version is bumped but not committed yet")
        self.assertEqual(r.stdout.strip(), f"v{mcptoolshop_rnd.__version__}")


if __name__ == "__main__":
    unittest.main()
