from pathlib import Path
import cv2

from config import AppConfig
from detectors.table_detector import TableDetector
from detectors.person_detector import PersonDetector
from processors.table_processor import TableProcessor
from processors.person_processor import PersonProcessor
from processors.player_filter import PlayerFilter
from processors.scene_fuser import SceneFuser
from schemas.state import SessionState
from utils.json_writer import JsonWriter
from utils.video_writer import VideoWriter


def main():
    config = AppConfig()
    config.output_dir_path.mkdir(parents=True, exist_ok=True)

    input_path = Path(config.video.input_video_path)
    stem = input_path.stem

    output_video_path = config.output_dir_path / f"{stem}_annotated.mp4"
    output_json_path = config.output_dir_path / f"{stem}.json"

    cap = cv2.VideoCapture(str(input_path))
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {config.video.input_video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0:
        fps = 30.0

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    table_detector = TableDetector()

    person_detector = PersonDetector(
        model_path=config.person.model_path,
        confidence_threshold=config.person.confidence_threshold,
        person_class_id=config.person.person_class_id,
    )

    table_processor = TableProcessor(
        smooth_alpha=config.table.smooth_alpha,
    )
    person_processor = PersonProcessor(
        min_area_ratio=config.filter.min_person_area_ratio,
    )
    player_filter = PlayerFilter(
        max_players_per_side=config.filter.max_players_per_side,
        umpire_zone_ratio_top=config.filter.umpire_zone_ratio_top,
        outside_margin_x_ratio=config.filter.outside_margin_x_ratio,
    )
    scene_fuser = SceneFuser()

    session_state = SessionState()

    json_writer = JsonWriter(str(output_json_path))

    video_writer = None
    if config.video.save_video:
        video_writer = VideoWriter(
            save_path=str(output_video_path),
            fps=fps,
            frame_size=(width, height),
        )

    frame_idx = 0

    while True:
        ok, frame = cap.read()
        if not ok:
            break

        raw_tables = table_detector.detect(frame)
        raw_persons = person_detector.detect(frame)

        table = table_processor.process(raw_tables)
        persons = person_processor.process(raw_persons, frame.shape)
        persons = player_filter.filter(persons, table, frame.shape)

        frame_state = scene_fuser.fuse(
            frame_idx=frame_idx,
            table=table,
            persons=persons,
        )

        session_state.frames.append(frame_state)

        if video_writer is not None:
            video_writer.draw_and_write(frame, frame_state)

        frame_idx += 1

        if frame_idx % 30 == 0:
            print(f"[Agent] processed frame={frame_idx}")

    cap.release()

    if video_writer is not None:
        video_writer.close()

    if config.video.save_json:
        json_writer.write(session_state)

    print("[Agent] Done.")
    print(f"[Agent] Total frames: {frame_idx}")
    print(f"[Agent] JSON saved to: {output_json_path}")
    if config.video.save_video:
        print(f"[Agent] Video saved to: {output_video_path}")


if __name__ == "__main__":
    main()