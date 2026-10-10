"""timed_call: the per-call device bound used by every npu-probe runner."""

import sys
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "experiments" / "npu-probe"))

from call_timeout import CallTimeout, timed_call


class TimedCallTest(unittest.TestCase):
    def test_fast_call_returns(self):
        self.assertEqual(timed_call(5.0, lambda: 41 + 1), 42)

    def test_timeout_raises(self):
        t0 = time.perf_counter()
        with self.assertRaises(CallTimeout):
            timed_call(0.05, time.sleep, 0.4)
        self.assertLess(time.perf_counter() - t0, 0.3)

    def test_exceptions_propagate(self):
        def boom():
            raise ValueError("explode")

        with self.assertRaises(ValueError):
            timed_call(5.0, boom)

    def test_zero_disables(self):
        self.assertEqual(timed_call(0, time.sleep, 0.01) is None, True)
        self.assertIsNone(timed_call(None, time.sleep, 0.01))


if __name__ == "__main__":
    unittest.main()
