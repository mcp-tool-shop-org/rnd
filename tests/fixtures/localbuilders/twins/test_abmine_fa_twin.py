import unittest
from mcptoolshop_rnd import abmine


class ForcedFlashAttentionTwinTests(unittest.TestCase):
    def test_forced_enabled_and_disabled_resolve(self):
        on = abmine.parse_log("llama_context: flash_attn = enabled\nllama_context: n_ctx = 4096")
        off = abmine.parse_log("llama_context: flash_attn = disabled\nllama_context: n_ctx = 4096")
        self.assertEqual(on["flash_attn_resolved"], "enabled")
        self.assertEqual(off["flash_attn_resolved"], "disabled")
