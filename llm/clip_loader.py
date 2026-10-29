from __future__ import annotations

from dataclasses import dataclass, field
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
    # Native video mode does not create sampled JPEG frames.
    sampled_frames: List[SampledFrame] = field(default_factory=list)


class ClipLoader:
    def __init__(self, video_path: str | Path):
        self.video_path = Path(video_path)

    def _read_metadata(self) -> tuple[cv2.VideoCapture, float, int, int, int, float]:
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

        if frame_count <= 0:
            cap.release()
            raise RuntimeError("Video has no frames.")

        duration_sec = frame_count / fps if fps > 0 else 0.0
        return cap, fps, frame_count, width, height, duration_sec

    def load_metadata(self) -> ClipInfo:
        """Read only video metadata for native-video VLM input."""
        cap, fps, frame_count, width, height, duration_sec = self._read_metadata()
        cap.release()

        return ClipInfo(
            video_path=self.video_path,
            fps=fps,
            frame_count=frame_count,
            width=width,
            height=height,
            duration_sec=duration_sec,
            sampled_frames=[],
        )

    def load(
        self,
        sample_count: int | None = 12,
        frame_stride: int = 4,
        jpeg_quality: int = 85,
    ) -> ClipInfo:
        """Load JPEG frames for the existing multi-frame VLM input path."""
        cap, fps, frame_count, width, height, duration_sec = self._read_metadata()

        sampled_frames: list[SampledFrame] = []

        # ============================================================
        # Mode 1: Read the whole video sequentially
        # ============================================================
        if sample_count is None:
            frame_stride = max(1, frame_stride)

            frame_idx = 0

            while True:
                ok, frame = cap.read()

                if not ok:
                    break

                # stride = 1 -> every frame
                # stride = 2 -> 0, 2, 4, 6...
                if frame_idx % frame_stride == 0:
                    ok_encode, buf = cv2.imencode(
                        ".jpg",
                        frame,
                        [int(cv2.IMWRITE_JPEG_QUALITY), jpeg_quality],
                    )

                    if ok_encode:
                        sampled_frames.append(
                            SampledFrame(
                                frame_idx=frame_idx,
                                jpeg_base64=base64.b64encode(
                                    buf.tobytes()
                                ).decode("utf-8"),
                            )
                        )

                frame_idx += 1

        # ============================================================
        # Mode 2: Uniformly sample a fixed number of frames
        # ============================================================
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

            for idx in indices:
                cap.set(cv2.CAP_PROP_POS_FRAMES, idx)

                ok, frame = cap.read()

                if not ok:
                    print(
                        f"[WARNING] Failed to read frame {idx} "
                        f"from {self.video_path.name}"
                    )
                    continue

                ok_encode, buf = cv2.imencode(
                    ".jpg",
                    frame,
                    [int(cv2.IMWRITE_JPEG_QUALITY), jpeg_quality],
                )

                if not ok_encode:
                    print(
                        f"[WARNING] Failed to encode frame {idx} "
                        f"from {self.video_path.name}"
                    )
                    continue

                sampled_frames.append(
                    SampledFrame(
                        frame_idx=idx,
                        jpeg_base64=base64.b64encode(
                            buf.tobytes()
                        ).decode("utf-8"),
                    )
                )

        cap.release()

        if not sampled_frames:
            raise RuntimeError("Failed to sample any frames from video.")

        # ============================================================
        # Sanity check
        # ============================================================
        if sample_count is None:
            expected_count = (frame_count + frame_stride - 1) // frame_stride

            if len(sampled_frames) != expected_count:
                print(
                    f"[WARNING] Frame count mismatch: "
                    f"video={self.video_path.name}, "
                    f"metadata_frames={frame_count}, "
                    f"expected={expected_count}, "
                    f"loaded={len(sampled_frames)}, "
                    f"last_loaded_frame={sampled_frames[-1].frame_idx}"
                )

        return ClipInfo(
            video_path=self.video_path,
            fps=fps,
            frame_count=frame_count,
            width=width,
            height=height,
            duration_sec=duration_sec,
            sampled_frames=sampled_frames,
        )