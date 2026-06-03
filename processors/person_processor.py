from schemas.records import PersonRecord


class PersonProcessor:
    def __init__(self, min_area_ratio: float = 0.005, dedup_iou_threshold: float = 0.55):
        self.min_area_ratio = min_area_ratio
        self.dedup_iou_threshold = dedup_iou_threshold

    def process(self, raw_detections: list[dict], frame_shape) -> list[PersonRecord]:
        h, w = frame_shape[:2]
        min_area = int(h * w * self.min_area_ratio)

        candidates = []
        for det in raw_detections:
            bbox = det.get("bbox")
            if not bbox or len(bbox) != 4:
                continue

            x1, y1, x2, y2 = map(int, bbox)
            bw = max(0, x2 - x1)
            bh = max(0, y2 - y1)
            area = bw * bh

            if area < min_area:
                continue

            candidates.append({
                "bbox": [x1, y1, x2, y2],
                "area": area,
                "confidence": float(det.get("confidence", 0.0)),
                "keypoints": det.get("keypoints"),
            })

        deduped = self._deduplicate_candidates(candidates)

        persons = []
        for det in deduped:
            x1, y1, x2, y2 = det["bbox"]
            center = [int((x1 + x2) / 2), int((y1 + y2) / 2)]
            foot_point = [int((x1 + x2) / 2), y2]

            persons.append(
                PersonRecord(
                    bbox=det["bbox"],
                    center=center,
                    foot_point=foot_point,
                    area=det["area"],
                    confidence=det["confidence"],
                    track_id=None,
                    role="unknown",
                    keypoints=det.get("keypoints"),
                )
            )

        return persons

    def _deduplicate_candidates(self, candidates: list[dict]) -> list[dict]:
        # 先留高 confidence 的
        candidates = sorted(candidates, key=lambda x: x["confidence"], reverse=True)

        kept = []
        for cand in candidates:
            is_duplicate = False
            for exist in kept:
                iou = self._bbox_iou(cand["bbox"], exist["bbox"])
                if iou >= self.dedup_iou_threshold:
                    is_duplicate = True
                    break

            if not is_duplicate:
                kept.append(cand)

        return kept

    def _bbox_iou(self, box_a: list[int], box_b: list[int]) -> float:
        ax1, ay1, ax2, ay2 = box_a
        bx1, by1, bx2, by2 = box_b

        inter_x1 = max(ax1, bx1)
        inter_y1 = max(ay1, by1)
        inter_x2 = min(ax2, bx2)
        inter_y2 = min(ay2, by2)

        inter_w = max(0, inter_x2 - inter_x1)
        inter_h = max(0, inter_y2 - inter_y1)
        inter_area = inter_w * inter_h

        area_a = max(0, ax2 - ax1) * max(0, ay2 - ay1)
        area_b = max(0, bx2 - bx1) * max(0, by2 - by1)

        union = area_a + area_b - inter_area
        if union <= 0:
            return 0.0

        return inter_area / union