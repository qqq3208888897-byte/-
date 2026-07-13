from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .formats import ResourceFormat, detect_format
from .passwords import EncryptionPolicy


class ConversionError(RuntimeError):
    pass


@dataclass(frozen=True)
class ConversionRequest:
    source: Path
    destination: Path
    source_format: ResourceFormat | None = None
    destination_format: ResourceFormat | None = None
    policy: EncryptionPolicy = EncryptionPolicy.default()

    def resolved_source_format(self) -> ResourceFormat:
        return self.source_format or detect_format(self.source)

    def resolved_destination_format(self) -> ResourceFormat:
        return self.destination_format or detect_format(self.destination)


def convert(request: ConversionRequest) -> None:
    source_format = request.resolved_source_format()
    destination_format = request.resolved_destination_format()
    if source_format == ResourceFormat.WZL and destination_format == ResourceFormat.WZL:
        raise ConversionError("WZL→WZL 应使用编辑/优化流程，不应作为格式转换")
    raise ConversionError(
        f"转换器尚未接入 {source_format.value.upper()}→{destination_format.value.upper()} 的具体容器编码；"
        "需要参考编辑器生成的目标文件样本后实现。"
    )
