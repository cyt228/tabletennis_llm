from schemas.state import FrameState
from schemas.records import TableRecord, PersonRecord


class SceneFuser:
    def fuse(
        self,
        frame_idx: int,
        table: TableRecord,
        persons: list[PersonRecord],
    ) -> FrameState:
        return FrameState(
            frame_idx=frame_idx,
            table=table,
            persons=persons,
        )