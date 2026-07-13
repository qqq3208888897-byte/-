import tempfile
import unittest
from pathlib import Path

from wzlcli.bmp_codec import BmpImage, write_rgb565_bmp
from wzlcli.wzl_builder import build_wzl, write_wzx_for_offsets
from wzlcli.wzl_container import read_wzl
from wzlcli.wzx_index import read_wzx


class WzlBuilderTests(unittest.TestCase):
    def test_build_bmp_to_wzl_and_wzx(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            image_dir = root / "images"
            image_dir.mkdir()
            image = BmpImage(2, 2, 16, 3, 0xF800, 0x07E0, 0x001F, (0xF800, 0x07E0, 0x001F, 0xFFFF))
            write_rgb565_bmp(image_dir / "00000.BMP", image)
            wzl = root / "out.wzl"
            wzx = root / "out.wzx"
            offsets = build_wzl([image_dir / "00000.BMP"], wzl, placements={0: (3, -4)})
            write_wzx_for_offsets(offsets, wzx)
            resource = read_wzl(wzl)
            self.assertEqual(len(resource.frames), 1)
            self.assertEqual((resource.frames[0].width, resource.frames[0].height), (2, 2))
            self.assertEqual((resource.frames[0].placement.x, resource.frames[0].placement.y), (3, -4))
            self.assertEqual(read_wzx(wzx).offsets, offsets)
