import json
from pathlib import Path

from config import AppConfig
from llm.clip_loader import ClipLoader
from llm.action_analyzer import ActionAnalyzer


def main():
    config = AppConfig()

    video_path = config.video.input_video_path
    output_dir = config.output_dir_path
    output_dir.mkdir(parents=True, exist_ok=True)

    clip_loader = ClipLoader(video_path)
    clip_info = clip_loader.load(
        sample_count=config.llm.sample_count,
        frame_stride=config.llm.frame_stride,
        jpeg_quality=config.llm.jpeg_quality,
    )

    analyzer = ActionAnalyzer(
        provider=config.llm.provider,
        model_name=config.llm.model_name,
        prompt_path=config.llm.prompt_path,
    )

    result = analyzer.analyze(clip_info)

    print(json.dumps(result, ensure_ascii=False, indent=2))

    if config.llm.save_json:
        output_path = output_dir / f"{Path(video_path).stem}{config.llm.output_json_suffix}"
        output_path.write_text(
            json.dumps(result, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"[LLM V1] Saved result to: {output_path}")


if __name__ == "__main__":
    main()