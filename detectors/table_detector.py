from typing import List, Dict, Any
import cv2


class TableDetector:
    def __init__(self):
        self.fixed_bbox = None
        self.initialized = False

    def detect(self, frame) -> List[Dict[str, Any]]:
        # 第一次執行 → 手動框
        if not self.initialized:
            self.fixed_bbox = self._select_roi(frame)
            self.initialized = True

        return [
            {
                "label": "table",
                "confidence": 1.0,
                "bbox": self.fixed_bbox,
                "source": "manual_roi",
            }
        ]

    def _select_roi(self, frame):
        print("\n[TableDetector] 請用滑鼠框選桌子，按 ENTER 確認\n")

        # OpenCV ROI
        x, y, w, h = cv2.selectROI(
            "Select Table ROI",
            frame,
            fromCenter=False,
            showCrosshair=True
        )

        cv2.destroyWindow("Select Table ROI")

        if w == 0 or h == 0:
            raise RuntimeError("ROI selection cancelled or invalid")

        x1 = int(x)
        y1 = int(y)
        x2 = int(x + w)
        y2 = int(y + h)

        print(f"[TableDetector] ROI selected: {[x1, y1, x2, y2]}")

        return [x1, y1, x2, y2]