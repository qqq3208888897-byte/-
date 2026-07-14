import tempfile
import unittest
from pathlib import Path

from wzlcli.bmp_codec import BmpImage, write_rgb565_bmp
from wzlcli.wzl_builder import append_images
from wzlcli.wzl_container import read_wzl


class WzlAppendTests(unittest.TestCase):
    def test_append_images_assigns_new_indexes(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            source_dir = root / "source"
            add_dir = root / "add"
            source_dir.mkdir()
            add_dir.mkdir()
            image = BmpImage(2, 2, 16, 3, 0xF800, 0x07E0, 0x001F, (0xF800, 0x07E0, 0x001F, 0xFFFF))
            write_rgb565_bmp(source_dir / "00000.BMP", image)
            write_rgb565_bmp(add_dir / "00001.BMP", image)
            first = root / "first.wzl"
            output = root / "appended.wzl"
            from wzlcli.wzl_builder import build_wzl
            build_wzl([source_dir / "00000.BMP"], first)
            entries = append_images(first, [add_dir / "00001.BMP"], output)
            self.assertEqual(entries[0]["index"], 1)
            self.assertEqual(len(read_wzl(output).frames), 2)
