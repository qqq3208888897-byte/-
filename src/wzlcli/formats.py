from __future__ import annotations

from enum import Enum
from pathlib import Path


class ResourceFormat(str, Enum):
    WIL = "wil"
    WIS = "wis"
    WZL = "wzl"
    PAK = "pak"


def detect_format(path: Path) -> ResourceFormat:
    suffix = path.suffix.lower().lstrip(".")
    try:
        return ResourceFormat(suffix)
    except ValueError as exc:
        raise ValueError(f"不支持的资源扩展名: {path.suffix}") from exc
