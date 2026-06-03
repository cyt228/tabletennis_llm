from dataclasses import dataclass, field
from typing import Any

from schemas.records import TableRecord, PersonRecord


@dataclass
class FrameState:
    frame_idx: int
    table: TableRecord
    persons: list[PersonRecord] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "frame_idx": self.frame_idx,
            "table": self.table.to_dict(),
            "persons": [p.to_dict() for p in self.persons],
        }


@dataclass
class SessionState:
    frames: list[FrameState] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "frames": [frame.to_dict() for frame in self.frames]
        }