import struct
import unittest
from pathlib import Path

from wzlcli.wzl_container import read_wzl, set_placement, write_wzl


SAMPLE = Path(r"C:\Users\admin\Desktop\样本\cbohair.wzl")


@unittest.skipUnless(SAMPLE.exists(), "local sample is not present")
class WzlBatchEditTests(unittest.TestCase):
    def test_multiple_placements_can_be_written(self):
        target = Path(__file__).parent / "cbohair-batch-placement.wzl"
        try:
            resource = read_wzl(SAMPLE)
            changes = {0: (1, -2), 2: (123, -456), 84: (-17, 22)}
            for index, (x, y) in changes.items():
                set_placement(resource, index, x, y)
            write_wzl(resource, target)
            restored = read_wzl(target)
            raw = target.read_bytes()
            for index, (x, y) in changes.items():
                self.assertEqual(restored.frames[index].placement.x, x)
                self.assertEqual(restored.frames[index].placement.y, y)
                offset = restored.frames[index].record_offset
                self.assertEqual(struct.unpack_from("<h", raw, offset + 8)[0], x)
                self.assertEqual(struct.unpack_from("<h", raw, offset + 10)[0], y)
        finally:
            target.unlink(missing_ok=True)
