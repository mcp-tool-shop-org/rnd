import unittest
from mcptoolshop_rnd import abmine


class ForcedFlashAttentionTests(unittest.TestCase):
    def test_forced_setting_resolves_itself(self):
        lg = abmine.parse_log("llama_context: flash_attn            = disabled")
        self.assertEqual((lg["flash_attn_setting"], lg["flash_attn_resolved"]), ("disabled", "disabled"))
        lg = abmine.parse_log("llama_context: flash_attn            = enabled")
        self.assertEqual(lg["flash_attn_resolved"], "enabled")
