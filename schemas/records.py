from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass
class TableRecord:
    detected: bool = False
    bbox: list[int] = field(default_factory=lambda: [0, 0, 0, 0])
    confidence: float = 0.0
    stable: bool = False
    source: str = ""
    corners: list[list[int]] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PersonRecord:
    bbox: list[int]
    center: list[int]
    foot_point: list[int]
    area: int
    confidence: float
    track_id: int | None = None
    role: str = "unknown"
    keypoints: list[list[float]] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)