import unittest
from pathlib import Path

from wzlcli.bmp_codec import read_rgb565_bmp
from wzlcli.wzl_container import read_wzl
from wzlcli.wzl_pixels import decode_frame_pixels


WZL = Path(r"D:\热血传奇17周年客户端\data\cbohum4.wzl")
BMP = Path(r"C:\Users\admin\Desktop\样本\cbohum4\00001.BMP")


@unittest.skipUnless(WZL.exists() and BMP.exists(), "large WZL/BMP pair is not present")
class WzlPixelTests(unittest.TestCase):
    def test_frame_one_matches_reference_bmp(self):
        resource = read_wzl(WZL)
        decoded = decode_frame_pixels(resource.frames[1])
        reference = read_rgb565_bmp(BMP)
        self.assertEqual((decoded.width, decoded.height), (reference.width, reference.height))
        self.assertEqual(decoded.pixels_rgb565, reference.pixels_rgb565)

    def test_first_three_frames_match_reference_bmps(self):
        resource = read_wzl(WZL)
        for index in (1, 2, 3):
            decoded = decode_frame_pixels(resource.frames[index])
            reference = read_rgb565_bmp(BMP.parent / f"{index:05d}.BMP")
            self.assertEqual(decoded.pixels_rgb565, reference.pixels_rgb565)
