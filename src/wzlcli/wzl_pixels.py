from __future__ import annotations

import struct

from .bmp_codec import BmpImage
from .models import Frame


def decode_frame_pixels(frame: Frame) -> BmpImage:
    if frame.width <= 0 or frame.height <= 0:
        raise ValueError(f"帧 {frame.index} 的尺寸无效: {frame.width}x{frame.height}")
    stride = ((frame.width * 2 + 3) // 4) * 4
    expected = stride * frame.height
    if len(frame.decoded) != expected:
        raise ValueError(f"帧 {frame.index} 解压长度不匹配：expected={expected}, actual={len(frame.decoded)}")
    pixels: list[int] = []
    for row in range(frame.height):
        # WZL payload uses the same bottom-up row order as the reference BMP.
        source_row = frame.height - 1 - row
        start = source_row * stride
        for x in range(frame.width):
            pixels.append(struct.unpack_from("<H", frame.decoded, start + x * 2)[0])
    return BmpImage(frame.width, frame.height, 16, 3, 0xF800, 0x07E0, 0x001F, tuple(pixels))
