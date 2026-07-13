import unittest
from pathlib import Path

from wzlcli.wzl_container import read_wzl


SAMPLE = Path(r"C:\Users\admin\Desktop\样本\cbohair.wzl")


@unittest.skipUnless(SAMPLE.exists(), "local sample is not present")
class WzlSampleTests(unittest.TestCase):
    def test_sample_has_85_frames(self):
        resource = read_wzl(SAMPLE)
        self.assertEqual(len(resource.frames), 85)
        self.assertEqual(resource.frames[0].action_slot, 0)
        self.assertEqual(resource.frames[0].direction_slot, 0)
        self.assertEqual(resource.frames[5].action_slot, 1)
        self.assertEqual(resource.frames[5].direction_slot, 0)

    def test_all_sample_payloads_decompress(self):
        resource = read_wzl(SAMPLE)
        self.assertTrue(all(frame.decoded for frame in resource.frames))
