"""The CUDA-backend diagnosis harness's own tests, run with the suite.

They live beside the frozen harness in experiments/ollama-cuda-backend/diag/. They include an offline dry run of the
harness's main() through every arm to the verdict, so a bug on that path fails here, not under a GPU grant.
"""

import os
import sys
import unittest

DIAG = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "experiments", "ollama-cuda-backend", "diag")


def load_tests(loader, tests, pattern):
    if DIAG not in sys.path:
        sys.path.insert(0, DIAG)
    import test_diag_test

    tests.addTests(loader.loadTestsFromModule(test_diag_test))
    return tests


if __name__ == "__main__":
    unittest.main()
