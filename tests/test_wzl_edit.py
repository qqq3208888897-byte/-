import hashlib
import struct
import unittest
from pathlib import Path

from wzlcli.wzl_container import read_wzl, set_placement, write_wzl


SAMPLE = Path(r"C:\Users\admin\Desktop\样本\cbohair.wzl")


@unittest.skipUnless(SAMPLE.exists(), "local sample is not present")
class WzlEditTests(unittest.TestCase):
    def test_set_placement_changes_only_target_header_fields(self):
        target = Path(__file__).parent / "cbohair-placement-edit.wzl"
        try:
            resource = read_wzl(SAMPLE)
            original = SAMPLE.read_bytes()
            frame = resource.frames[2]
            set_placement(resource, 2, 123, -456)
            write_wzl(resource, target)
            edited = target.read_bytes()
            self.assertEqual(len(original), len(edited))
            differences = [i for i, (a, b) in enumerate(zip(original, edited)) if a != b]
            target_range = set(range(frame.record_offset + 8, frame.record_offset + 12))
            self.assertTrue(set(differences).issubset(target_range))
            self.assertGreaterEqual(len(differences), 1)
            self.assertEqual(struct.unpack_from("<h", edited, frame.record_offset + 8)[0], 123)
            self.assertEqual(struct.unpack_from("<h", edited, frame.record_offset + 10)[0], -456)
            self.assertEqual(hashlib.sha256(original[:frame.payload_offset] + original[frame.payload_offset:]).digest() != hashlib.sha256(edited).digest(), True)
        finally:
            target.unlink(missing_ok=True)
