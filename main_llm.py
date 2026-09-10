import json
import time
from pathlib import Path
from typing import Any

from config import AppConfig
from llm.clip_loader import ClipLoader
from llm.action_analyzer import ActionAnalyzer


def build_analyzer(config: AppConfig) -> ActionAnalyzer:
    """Create the LLM action analyzer from config.py."""
    return ActionAnalyzer(
        provider=config.llm.provider,
        model_name=config.llm.model_name,
        prompt_path=config.llm.prompt_path,
        action_guide_path=getattr(
            config.llm,
            "action_guide_path",
            None,
        ),
    )


def predict_video(
    video_path: str | Path | None = None,
    config: AppConfig | None = None,
    analyzer: ActionAnalyzer | None = None,
    save_json: bool | None = None,
    output_dir: str | Path | None = None,
    output_json_path: str | Path | None = None,
) -> dict[str, Any]:
    """
    Predict one video.

    - If video_path is None, use config.video.input_video_path.
    - This keeps main_llm.py usable for single-video execution.
    - main_llm_batch.py can also import and reuse this function.

    Timing:
    - preprocessing_sec: ClipLoader / frame sampling time
    - inference_sec: measured inside ActionAnalyzer
    - total_processing_sec: preprocessing + inference + local parsing overhead
    """
    if config is None:
        config = AppConfig()

    if video_path is None:
        video_path = config.video.input_video_path

    video_path = Path(video_path)

    if not video_path.is_file():
        raise FileNotFoundError(
            f"Single-video predict expects a video file: {video_path}"
        )

    if analyzer is None:
        analyzer = build_analyzer(config)

    total_start = time.perf_counter()

    preprocessing_start = time.perf_counter()

    clip_loader = ClipLoader(video_path)
    clip_info = clip_loader.load(
        sample_count=config.llm.sample_count,
        frame_stride=config.llm.frame_stride,
        jpeg_quality=config.llm.jpeg_quality,
    )

    preprocessing_sec = (
        time.perf_counter() - preprocessing_start
    )

    result = analyzer.analyze(clip_info)

    total_processing_sec = (
        time.perf_counter() - total_start
    )

    # Preserve timing measured inside ActionAnalyzer,
    # and add preprocessing / total pipeline timing here.
    timing = result.setdefault("timing", {})
    timing["preprocessing_sec"] = preprocessing_sec
    timing["total_processing_sec"] = total_processing_sec

    should_save = (
        config.llm.save_json
        if save_json is None
        else save_json
    )

    if should_save:
        if output_json_path is None:
            out_dir = (
                Path(output_dir)
                if output_dir is not None
                else config.output_dir_path
            )
            out_dir.mkdir(
                parents=True,
                exist_ok=True,
            )

            output_json_path = (
                out_dir
                / f"{video_path.stem}"
                f"{config.llm.output_json_suffix}"
            )
        else:
            output_json_path = Path(
                output_json_path
            )
            output_json_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

        output_json_path.write_text(
            json.dumps(
                result,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        print(
            f"[LLM] Saved result to: "
            f"{output_json_path}"
        )

    return result


def main():
    config = AppConfig()

    result = predict_video(
        config=config
    )

    print(
        json.dumps(
            result,
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
