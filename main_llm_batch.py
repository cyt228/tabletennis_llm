import csv
import json
from pathlib import Path

from config import AppConfig
from llm.clip_loader import ClipLoader
from llm.action_analyzer import ActionAnalyzer


VIDEO_EXTS = {".mp4", ".avi", ".mov", ".mkv"}


def find_videos(input_path: Path) -> list[Path]:
    if input_path.is_file():
        return [input_path]

    if not input_path.is_dir():
        raise FileNotFoundError(f"Input path not found: {input_path}")

    videos = []
    for path in sorted(input_path.iterdir()):
        if path.is_file() and path.suffix.lower() in VIDEO_EXTS:
            videos.append(path)

    return videos


def main():
    config = AppConfig()

    input_path = Path(config.video.input_video_path)
    output_dir = config.output_dir_path
    output_dir.mkdir(parents=True, exist_ok=True)

    analyzer = ActionAnalyzer(
        provider=config.llm.provider,
        model_name=config.llm.model_name,
        prompt_path=config.llm.prompt_path,
    )

    video_paths = find_videos(input_path)
    if not video_paths:
        raise RuntimeError(f"No video files found in: {input_path}")

    results = []

    for idx, video_path in enumerate(video_paths, start=1):
        print(f"[{idx}/{len(video_paths)}] Processing: {video_path.name}")

        try:
            clip_loader = ClipLoader(video_path)
            clip_info = clip_loader.load(
                sample_count=config.llm.sample_count,
                jpeg_quality=config.llm.jpeg_quality,
            )

            result = analyzer.analyze(clip_info)
            prediction = result["prediction"]

            results.append({
                "video_name": prediction["video_name"],
                "predicted_label": prediction["predicted_label"],
            })

            per_video_json = output_dir / f"{video_path.stem}{config.llm.output_json_suffix}"
            per_video_json.write_text(
                json.dumps(result, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

        except Exception as e:
            print(f"[ERROR] {video_path.name}: {e}")
            results.append({
                "video_name": video_path.name,
                "predicted_label": -1,
            })

    csv_path = output_dir / "predictions.csv"
    with csv_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["video_name", "predicted_label"])
        writer.writeheader()
        writer.writerows(results)

    print(f"[DONE] Saved batch predictions to: {csv_path}")


if __name__ == "__main__":
    main()