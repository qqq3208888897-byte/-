from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Placement:
    x: int
    y: int
    source_fields: tuple[int, ...] = ()


@dataclass
class Frame:
    index: int
    action_slot: int
    direction_slot: int
    placement: Placement | None
    width: int
    height: int
    record_offset: int
    payload_offset: int
    payload_length: int
    decoded_length: int | None
    decoded: bytes = field(repr=False, default=b"")
    header: bytes = field(repr=False, default=b"")
    payload: bytes = field(repr=False, default=b"")


@dataclass
class Resource:
    path: Path
    format: str
    encrypted: bool = False
    frames: list[Frame] = field(default_factory=list)
    metadata: dict[str, object] = field(default_factory=dict)
    prefix: bytes = field(repr=False, default=b"")
    suffix: bytes = field(repr=False, default=b"")
