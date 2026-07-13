from __future__ import annotations

import struct
import zlib
from pathlib import Path

from .models import Frame, Placement, Resource


FIRST_RECORD = 0x40
HEADER_SIZE = 16


def _signed16(value: int) -> int:
    return struct.unpack("<h", struct.pack("<H", value))[0]


def read_wzl(path: Path) -> Resource:
    data = path.read_bytes()
    if len(data) < FIRST_RECORD:
        raise ValueError("WZL 文件过小")
    frames: list[Frame] = []
    offset = FIRST_RECORD
    index = 0
    while offset + HEADER_SIZE <= len(data):
        words = struct.unpack("<8H", data[offset : offset + HEADER_SIZE])
        payload_offset = offset + HEADER_SIZE
        payload_length = words[6]
        payload_end = payload_offset + payload_length
        if not payload_length or payload_end > len(data):
            break
        payload = data[payload_offset:payload_end]
        decoded = b""
        try:
            stream = zlib.decompressobj()
            decoded = stream.decompress(payload) + stream.flush()
            if stream.unused_data or stream.unconsumed_tail:
                decoded = b""
        except zlib.error:
            decoded = b""
        frames.append(
            Frame(
                index=index,
                action_slot=index // 5,
                direction_slot=index % 5,
                placement=Placement(_signed16(words[4]), _signed16(words[5]), tuple(words)),
                width=words[2],
                height=words[3],
                record_offset=offset,
                payload_offset=payload_offset,
                payload_length=payload_length,
                decoded_length=len(decoded) if decoded else None,
                decoded=decoded,
                header=bytes(data[offset : offset + HEADER_SIZE]),
                payload=bytes(payload),
            )
        )
        index += 1
        offset = payload_end
    return Resource(
        path=path,
        format="wzl",
        frames=frames,
        metadata={
            "magic": data[:32].rstrip(bytes([0])).decode("ascii", errors="replace"),
            "size": len(data),
            "grouping_candidate": "record_index // 5, record_index % 5",
        },
        prefix=data[:FIRST_RECORD],
        suffix=data[offset:],
    )


def write_wzl(resource: Resource, path: Path) -> None:
    if resource.format.lower() != "wzl":
        raise ValueError("当前写回器只支持 WZL")
    output = bytearray(resource.prefix)
    for frame in resource.frames:
        if len(frame.header) != HEADER_SIZE or len(frame.payload) != frame.payload_length:
            raise ValueError(f"帧 {frame.index} 缺少原始头或压缩数据")
        output.extend(frame.header)
        output.extend(frame.payload)
    output.extend(resource.suffix)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(bytes(output))


def set_placement(resource: Resource, index: int, x: int, y: int) -> None:
    if not -32768 <= x <= 32767 or not -32768 <= y <= 32767:
        raise ValueError("Placement 必须是有符号 16 位整数")
    try:
        frame = resource.frames[index]
    except IndexError as exc:
        raise ValueError(f"帧不存在: {index}") from exc
    header = bytearray(frame.header)
    struct.pack_into("<h", header, 8, x)
    struct.pack_into("<h", header, 10, y)
    frame.header = bytes(header)
    frame.placement = Placement(x, y, frame.placement.source_fields if frame.placement else ())
