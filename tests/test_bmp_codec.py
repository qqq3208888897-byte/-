import unittest
from pathlib import Path

from wzlcli.bmp_codec import read_rgb565_bmp, write_rgb565_bmp


SAMPLE = Path(r"C:\Users\admin\Desktop\样本\cbohum4")


@unittest.skipUnless((SAMPLE / "00001.BMP").exists(), "large BMP sample is not present")
class BmpCodecTests(unittest.TestCase):
    def test_first_sample_is_rgb565(self):
        image = read_rgb565_bmp(SAMPLE / "00001.BMP")
        self.assertEqual((image.width, image.height), (82, 100))
        self.assertEqual(image.bits_per_pixel, 16)
        self.assertEqual(image.compression, 3)
        self.assertEqual((image.red_mask, image.green_mask, image.blue_mask), (0xF800, 0x07E0, 0x001F))
        self.assertEqual(len(image.pixels_rgb565), 82 * 100)

    def test_last_sample_can_be_read(self):
        image = read_rgb565_bmp(SAMPLE / "14204.BMP")
        self.assertEqual((image.width, image.height), (68, 82))
        self.assertEqual(len(image.pixels_rgb565), 68 * 82)

    def test_round_trip_write(self):
        source = SAMPLE / "00001.BMP"
        target = Path(__file__).parent / "roundtrip-00001.BMP"
        try:
            image = read_rgb565_bmp(source)
            write_rgb565_bmp(target, image)
            restored = read_rgb565_bmp(target)
            self.assertEqual((restored.width, restored.height), (image.width, image.height))
            self.assertEqual(restored.pixels_rgb565, image.pixels_rgb565)
        finally:
            target.unlink(missing_ok=True)
