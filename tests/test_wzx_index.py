import hashlib
import unittest
from pathlib import Path

from wzlcli.wzx_index import read_wzx, sync_wzx


WZX = Path(r"D:\热血传奇17周年客户端\data\cbohum4.wzx")
WZL = Path(r"D:\热血传奇17周年客户端\data\cbohum4.wzl")


@unittest.skipUnless(WZX.exists() and WZL.exists(), "large WZL/WZX pair is not present")
class WzxTests(unittest.TestCase):
    def test_index_shape(self):
        index = read_wzx(WZX)
        self.assertEqual(len(index.offsets), 33408)
        self.assertEqual(sum(offset == 0 for offset in index.offsets), 10384)
        self.assertEqual(len(set(index.offsets)), 23025)

    def test_unchanged_wzl_sync_is_byte_identical(self):
        target = Path(__file__).parent / "cbohum4-sync.wzx"
        try:
            sync_wzx(WZX, WZL, target)
            self.assertEqual(hashlib.sha256(WZX.read_bytes()).digest(), hashlib.sha256(target.read_bytes()).digest())
        finally:
            target.unlink(missing_ok=True)
