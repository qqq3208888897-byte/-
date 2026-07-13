import unittest
from pathlib import Path

from wzlcli.formats import ResourceFormat, detect_format


class FormatTests(unittest.TestCase):
    def test_detects_supported_formats(self):
        for suffix, expected in ((".wil", ResourceFormat.WIL), (".wis", ResourceFormat.WIS), (".wzl", ResourceFormat.WZL), (".pak", ResourceFormat.PAK)):
            self.assertEqual(detect_format(Path("resource" + suffix)), expected)

    def test_rejects_unknown_format(self):
        with self.assertRaises(ValueError):
            detect_format(Path("resource.bin"))
