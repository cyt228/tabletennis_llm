import cv2

from schemas.state import FrameState


class VideoWriter:
    def __init__(self, save_path: str, fps: float, frame_size: tuple[int, int]):
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        self.writer = cv2.VideoWriter(save_path, fourcc, fps, frame_size)

        # COCO 17-keypoint skeleton
        self.skeleton_edges = [
            (0, 1), (0, 2),
            (1, 3), (2, 4),
            (5, 6),
            (5, 7), (7, 9),
            (6, 8), (8, 10),
            (5, 11), (6, 12),
            (11, 12),
            (11, 13), (13, 15),
            (12, 14), (14, 16),
        ]

    def close(self):
        self.writer.release()

    def draw_and_write(self, frame, frame_state: FrameState):
        vis = frame.copy()

        self._draw_table(vis, frame_state)
        self._draw_persons(vis, frame_state)
        self._draw_header(vis, frame_state)

        self.writer.write(vis)

    def _draw_table(self, frame, frame_state: FrameState):
        table = frame_state.table
        if not table.detected:
            return

        x1, y1, x2, y2 = table.bbox
        cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
        cv2.putText(
            frame,
            "table",
            (x1, max(20, y1 - 8)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 0, 0),
            2,
        )

    def _draw_persons(self, frame, frame_state: FrameState):
        for p in frame_state.persons:
            color = self._role_color(p.role)
            x1, y1, x2, y2 = p.bbox
            cx, cy = p.center
            fx, fy = p.foot_point

            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.circle(frame, (cx, cy), 4, color, -1)
            cv2.circle(frame, (fx, fy), 5, color, -1)

            label = p.role
            if p.track_id is not None:
                label += f"#{p.track_id}"

            cv2.putText(
                frame,
                label,
                (x1, max(20, y1 - 8)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                color,
                2,
            )

            self._draw_keypoints(frame, p.keypoints, color)

    def _draw_keypoints(self, frame, keypoints, color):
        if not keypoints:
            return

        pts = []
        for kp in keypoints:
            if len(kp) >= 2:
                x, y = int(kp[0]), int(kp[1])
                conf = kp[2] if len(kp) > 2 else 1.0
                if conf > 0.2:
                    pts.append((x, y))
                else:
                    pts.append(None)
            else:
                pts.append(None)

        for pt in pts:
            if pt is not None:
                cv2.circle(frame, pt, 3, color, -1)

        for a, b in self.skeleton_edges:
            if a < len(pts) and b < len(pts):
                if pts[a] is not None and pts[b] is not None:
                    cv2.line(frame, pts[a], pts[b], color, 2)

    def _draw_header(self, frame, frame_state: FrameState):
        players = sum(1 for p in frame_state.persons if p.role == "player")
        umpires = sum(1 for p in frame_state.persons if p.role == "umpire")
        others = sum(1 for p in frame_state.persons if p.role == "other")

        text = (
            f"frame: {frame_state.frame_idx} | "
            f"players: {players} | "
            f"umpires: {umpires} | "
            f"others: {others}"
        )

        cv2.putText(
            frame,
            text,
            (20, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2,
        )

    def _role_color(self, role: str):
        if role == "player":
            return (0, 255, 0)
        if role == "umpire":
            return (0, 0, 255)
        return (180, 180, 180)