from typing import List, Dict, Any

from ultralytics import YOLO


class PersonDetector:
    def __init__(
        self,
        model_path: str = "yolo11n-pose.pt",
        confidence_threshold: float = 0.3,
        person_class_id: int = 0,
    ):
        self.model = YOLO(model_path)
        self.confidence_threshold = confidence_threshold
        self.person_class_id = person_class_id

    def detect(self, frame) -> List[Dict[str, Any]]:
        results = self.model.predict(
            source=frame,
            conf=self.confidence_threshold,
            verbose=False,
        )

        detections: List[Dict[str, Any]] = []

        for result in results:
            boxes = result.boxes
            keypoints = result.keypoints

            if boxes is None:
                continue

            num_boxes = len(boxes)

            for i in range(num_boxes):
                box = boxes[i]
                cls_id = int(box.cls[0].item())
                conf = float(box.conf[0].item())

                if cls_id != self.person_class_id:
                    continue

                xyxy = box.xyxy[0].tolist()
                bbox = [int(v) for v in xyxy]

                kpts_out = None
                if keypoints is not None and keypoints.data is not None:
                    kp = keypoints.data[i].tolist()   # shape ~ [17, 3]
                    kpts_out = [[float(a), float(b), float(c)] for a, b, c in kp]

                detections.append(
                    {
                        "label": "person",
                        "confidence": conf,
                        "bbox": bbox,
                        "keypoints": kpts_out,
                        "source": "yolo_pose",
                    }
                )

        return detections