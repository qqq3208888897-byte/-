from __future__ import annotations

import struct
import zlib
import json
from pathlib import Path

from .bmp_codec import BmpImage, read_rgb565_bmp


MAGIC = b"www.shandagames.com"
HEADER_SIZE = 64


def _raw_bottom_up(image: BmpImage) -> bytes:
    stride = ((image.width * 2 + 3) // 4) * 4
    out = bytearray(stride * image.height)
    for row in range(image.height):
        source_row = image.height - 1 - row
        for x in range(image.width):
            struct.pack_into("<H", out, row * stride + x * 2, image.pixels_rgb565[source_row * image.width + x])
    return bytes(out)


def _prefix(template: Path | None) -> bytes:
    if template is not None:
        data = template.read_bytes()
        if len(data) < HEADER_SIZE:
            raise ValueError("模板 WZL 小于 64 字节")
        return data[:HEADER_SIZE]
    prefix = bytearray(HEADER_SIZE)
    prefix[: len(MAGIC)] = MAGIC
    return bytes(prefix)


def _read_png(path: Path) -> BmpImage:
    try:
        from PIL import Image
    except ImportError as exc:
        raise RuntimeError("PNG 导入需要 Pillow；请安装 Pillow 或先转换为 RGB565 BMP") from exc
    image = Image.open(path).convert("RGBA")
    pixels = []
    for y in range(image.height):
        for x in range(image.width):
            r, g, b, a = image.getpixel((x, y))
            if a == 0 or (r == 0 and g == 0 and b == 0):
                pixels.append(0)
                continue
            pixels.append(((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3))
    return BmpImage(image.width, image.height, 16, 3, 0xF800, 0x07E0, 0x001F, tuple(pixels))


def load_image(path: Path) -> BmpImage:
    if path.suffix.lower() == ".bmp":
        return read_rgb565_bmp(path)
    if path.suffix.lower() == ".png":
        return _read_png(path)
    raise ValueError(f"只支持 BMP/PNG：{path}")


def build_wzl(images: list[Path], output: Path, placements: dict[int, tuple[int, int]] | None = None, template: Path | None = None) -> list[int]:
    if not images:
        raise ValueError("没有输入图片")
    result = bytearray(_prefix(template))
    offsets: list[int] = []
    for index, image_path in enumerate(images):
        image = load_image(image_path)
        raw = _raw_bottom_up(image)
        compressed = zlib.compress(raw)
        x, y = (placements or {}).get(index, (0, 0))
        if not -32768 <= x <= 32767 or not -32768 <= y <= 32767:
            raise ValueError(f"第 {index} 帧 Placement 超出 int16")
        offsets.append(len(result))
        result.extend(struct.pack("<8H", 261, 0, image.width, image.height, x & 0xFFFF, y & 0xFFFF, len(compressed), 0))
        result.extend(compressed)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(bytes(result))
    return offsets


def write_wzx_for_offsets(offsets: list[int], output: Path, empty_prefix: int = 0) -> None:
    count = empty_prefix + len(offsets)
    data = bytearray(48)
    data[: len(MAGIC)] = MAGIC
    struct.pack_into("<I", data, 44, count)
    table = [0] * empty_prefix + offsets
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(bytes(data) + struct.pack(f"<{len(table)}I", *table))


def _build_records(images: list[Path], start_offset: int, start_index: int, placements: dict[int, tuple[int, int]] | None = None, template_header: bytes | None = None) -> tuple[bytes, list[dict]]:
    result = bytearray()
    entries: list[dict] = []
    for local_index, image_path in enumerate(images):
        image = load_image(image_path)
        raw = _raw_bottom_up(image)
        compressed = zlib.compress(raw)
        x, y = (placements or {}).get(start_index + local_index, (0, 0))
        if template_header and len(template_header) >= 2:
            first, second = struct.unpack_from("<HH", template_header, 0)
        else:
            first, second = 261, 0
        record_offset = start_offset + len(result)
        result.extend(struct.pack("<8H", first, second, image.width, image.height, x & 0xFFFF, y & 0xFFFF, len(compressed), 0))
        result.extend(compressed)
        entries.append({"index": start_index + local_index, "source": image_path.name, "record_offset": record_offset, "width": image.width, "height": image.height, "placement_x": x, "placement_y": y})
    return bytes(result), entries


def append_images(existing_wzl: Path, images: list[Path], output_wzl: Path, placements: dict[int, tuple[int, int]] | None = None) -> list[dict]:
    from .wzl_container import read_wzl
    resource = read_wzl(existing_wzl)
    source = existing_wzl.read_bytes()
    last_header = resource.frames[-1].header if resource.frames else None
    start_index = len(resource.frames)
    records, entries = _build_records(images, len(source), start_index, placements, last_header)
    output_wzl.parent.mkdir(parents=True, exist_ok=True)
    output_wzl.write_bytes(source + records)
    return entries


def write_index_manifest(entries: list[dict], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({"new_frames": entries}, ensure_ascii=False, indent=2), encoding="utf-8")
