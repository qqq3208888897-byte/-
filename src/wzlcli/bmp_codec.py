from __future__ import annotations

import struct
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class BmpImage:
    width: int
    height: int
    bits_per_pixel: int
    compression: int
    red_mask: int
    green_mask: int
    blue_mask: int
    pixels_rgb565: tuple[int, ...]


def read_rgb565_bmp(path: Path) -> BmpImage:
    data = path.read_bytes()
    if len(data) < 54 or data[:2] != b"BM":
        raise ValueError(f"不是 BMP 文件: {path}")
    pixel_offset = struct.unpack_from("<I", data, 10)[0]
    header_size = struct.unpack_from("<I", data, 14)[0]
    if header_size < 40:
        raise ValueError("不支持的 BMP 头")
    width, raw_height = struct.unpack_from("<ii", data, 18)
    planes, bpp, compression = struct.unpack_from("<HHI", data, 26)
    if planes != 1 or bpp != 16 or compression != 3:
        raise ValueError(f"只支持 16 位 BI_BITFIELDS BMP，实际 bpp={bpp}, compression={compression}")
    height = abs(raw_height)
    mask_offset = 14 + header_size
    if header_size >= 52:
        red_mask, green_mask, blue_mask = struct.unpack_from("<III", data, mask_offset - 12)
    else:
        red_mask, green_mask, blue_mask = struct.unpack_from("<III", data, mask_offset)
    stride = ((width * 2 + 3) // 4) * 4
    pixels: list[int] = []
    for row in range(height):
        source_row = row if raw_height < 0 else height - 1 - row
        start = pixel_offset + source_row * stride
        for x in range(width):
            pixels.append(struct.unpack_from("<H", data, start + x * 2)[0])
    return BmpImage(width, height, bpp, compression, red_mask, green_mask, blue_mask, tuple(pixels))


def write_rgb565_bmp(path: Path, image: BmpImage) -> None:
    if image.bits_per_pixel != 16 or image.compression != 3:
        raise ValueError("只支持写出 16 位 BI_BITFIELDS BMP")
    if len(image.pixels_rgb565) != image.width * image.height:
        raise ValueError("像素数量与宽高不一致")
    width, height = image.width, image.height
    stride = ((width * 2 + 3) // 4) * 4
    pixel_bytes = bytearray(stride * height)
    for row in range(height):
        source_row = height - 1 - row
        base = row * stride
        for x in range(width):
            struct.pack_into("<H", pixel_bytes, base + x * 2, image.pixels_rgb565[source_row * width + x])
    pixel_offset = 66
    file_size = pixel_offset + len(pixel_bytes)
    header = bytearray()
    header += b"BM"
    header += struct.pack("<IHHI", file_size, 0, 0, pixel_offset)
    header += struct.pack("<IiiHHIIiiII", 40, width, height, 1, 16, 3, len(pixel_bytes), 0, 0, 0, 0)
    header += struct.pack("<III", image.red_mask, image.green_mask, image.blue_mask)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(bytes(header) + pixel_bytes)
