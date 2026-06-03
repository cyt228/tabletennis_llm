from typing import List, Dict, Any, Optional
from schemas.records import TableRecord


class TableProcessor:
    def __init__(self, smooth_alpha: float = 0.7):
        self.smooth_alpha = smooth_alpha
        self.prev_table: Optional[TableRecord] = None

    def process(self, raw_tables: List[Dict[str, Any]]) -> TableRecord:
        if not raw_tables:
            if self.prev_table is not None:
                return TableRecord(
                    detected=False,
                    bbox=self.prev_table.bbox,
                    confidence=self.prev_table.confidence,
                    stable=False,
                    source=self.prev_table.source,
                    corners=self.prev_table.corners,
                )

            return TableRecord(
                detected=False,
                bbox=None,
                confidence=0.0,
                stable=False,
                source="none",
                corners=None,
            )

        best = raw_tables[0]
        bbox = best.get("bbox")

        table = TableRecord(
            detected=True,
            bbox=bbox,
            confidence=float(best.get("confidence", 0.0)),
            stable=True,
            source=best.get("source", ""),
            corners=best.get("corners"),
        )

        self.prev_table = table
        return table