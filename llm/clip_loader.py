from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List
import base64
import cv2


@dataclass
class SampledFrame:
    frame_idx: int
    jpeg_base64: str


@dataclass
class ClipInfo:
    video_path: Path
    fps: float
    frame_count: int
    width: int
    height: int
    duration_sec: float
    sampled_frames: List[SampledFrame]


class ClipLoader:
    def __init__(self, video_path: str | Path):
        self.video_path = Path(video_path)

    def load(
        self,
        sample_count: int | None = 12,
        frame_stride: int = 4,
        jpeg_quality: int = 85,
    ) -> ClipInfo:
        if not self.video_path.exists():
            raise FileNotFoundError(f"Video file not found: {self.video_path}")

        cap = cv2.VideoCapture(str(self.video_path))
        if not cap.isOpened():
            raise RuntimeError(f"Cannot open video: {self.video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0:
            fps = 30.0

        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration_sec = frame_count / fps if fps > 0 else 0.0

        if frame_count <= 0:
            cap.release()
            raise RuntimeError("Video has no frames.")

        if sample_count is None:
            frame_stride = max(1, frame_stride)
            indices = list(range(0, frame_count, frame_stride))
        else:
            sample_count = max(1, min(sample_count, frame_count))

            if sample_count == 1:
                indices = [0]
            else:
                indices = []
                for i in range(sample_count):
                    ratio = i / (sample_count - 1)
                    idx = int(round(ratio * (frame_count - 1)))
                    indices.append(idx)

        sampled_frames: list[SampledFrame] = []

        for idx in indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ok, frame = cap.read()
            if not ok:
                continue

            ok, buf = cv2.imencode(
                ".jpg",
                frame,
                [int(cv2.IMWRITE_JPEG_QUALITY), jpeg_quality],
            )
            if not ok:
                continue

            sampled_frames.append(
                SampledFrame(
                    frame_idx=idx,
                    jpeg_base64=base64.b64encode(buf.tobytes()).decode("utf-8"),
                )
            )

        cap.release()

        if not sampled_frames:
            raise RuntimeError("Failed to sample any frames from video.")

        return ClipInfo(
            video_path=self.video_path,
            fps=fps,
            frame_count=frame_count,
            width=width,
            height=height,
            duration_sec=duration_sec,
            sampled_frames=sampled_frames,
        )