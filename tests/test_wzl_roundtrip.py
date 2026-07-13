import hashlib
import unittest
from pathlib import Path

from wzlcli.wzl_container import read_wzl, write_wzl


SAMPLE = Path(r"C:\Users\admin\Desktop\样本\cbohair.wzl")


@unittest.skipUnless(SAMPLE.exists(), "local sample is not present")
class WzlRoundTripTests(unittest.TestCase):
    def test_lossless_round_trip(self):
        target = Path(__file__).parent / "cbohair-roundtrip.wzl"
        try:
            resource = read_wzl(SAMPLE)
            write_wzl(resource, target)
            self.assertEqual(hashlib.sha256(SAMPLE.read_bytes()).digest(), hashlib.sha256(target.read_bytes()).digest())
        finally:
            target.unlink(missing_ok=True)
