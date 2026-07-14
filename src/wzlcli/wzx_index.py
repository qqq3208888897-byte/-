from __future__ import annotations

import struct
from dataclasses import dataclass
from pathlib import Path

from .wzl_container import FIRST_RECORD, HEADER_SIZE


@dataclass
class WzxIndex:
    prefix: bytes
    offsets: list[int]


def read_wzx(path: Path) -> WzxIndex:
    data = path.read_bytes()
    if len(data) < 48 or not data[:32].startswith(b"www.shandagames.com"):
        raise ValueError("不是可识别的 WZX 文件")
    count = struct.unpack_from("<I", data, 44)[0]
    expected = 48 + count * 4
    if expected != len(data):
        raise ValueError(f"WZX 索引长度不匹配：expected={expected}, actual={len(data)}")
    offsets = list(struct.unpack_from(f"<{count}I", data, 48))
    return WzxIndex(prefix=data[:48], offsets=offsets)


def _wzl_record_offsets(wzl_path: Path) -> list[int]:
    data = wzl_path.read_bytes()
    offsets: list[int] = []
    cursor = FIRST_RECORD
    while cursor + HEADER_SIZE <= len(data):
        payload_length = struct.unpack_from("<H", data, cursor + 12)[0]
        end = cursor + HEADER_SIZE + payload_length
        if not payload_length or end > len(data):
            break
        offsets.append(cursor)
        cursor = end
    return offsets


def sync_wzx(wzx_path: Path, wzl_path: Path, output: Path) -> None:
    index = read_wzx(wzx_path)
    new_record_offsets = _wzl_record_offsets(wzl_path)
    old_nonzero = [offset for offset in index.offsets if offset]
    if len(old_nonzero) > len(new_record_offsets):
        raise ValueError("新的 WZL 记录数量少于 WZX 有效索引数量")
    mapping = {old: new_record_offsets[i] for i, old in enumerate(old_nonzero)}
    updated = [mapping.get(offset, 0) for offset in index.offsets]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(index.prefix + struct.pack(f"<{len(updated)}I", *updated))


def append_wzx(wzx_path: Path, wzl_path: Path, new_record_offsets: list[int], output: Path) -> None:
    index = read_wzx(wzx_path)
    current_offsets = _wzl_record_offsets(wzl_path)
    if len(current_offsets) < sum(offset != 0 for offset in index.offsets):
        raise ValueError("WZL 有效记录少于 WZX 当前有效索引")
    updated = list(index.offsets) + list(new_record_offsets)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(index.prefix[:44] + struct.pack("<I", len(updated)) + struct.pack(f"<{len(updated)}I", *updated))
