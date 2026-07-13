import unittest
from pathlib import Path

from wzlcli.converter import ConversionError, ConversionRequest, convert


class ConverterTests(unittest.TestCase):
    def test_default_policy_is_attached(self):
        request = ConversionRequest(Path("a.wzl"), Path("b.pak"))
        self.assertTrue(request.policy.decrypt_input)
        self.assertTrue(request.policy.encrypt_output)

    def test_unimplemented_container_conversion_is_explicit(self):
        with self.assertRaises(ConversionError):
            convert(ConversionRequest(Path("a.wzl"), Path("b.pak")))
