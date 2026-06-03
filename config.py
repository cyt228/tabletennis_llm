from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class VideoConfig:
    input_video_path: str = "data/video/double_test1.mp4"
    output_dir: str = "outputs"
    output_video_suffix: str = "_annotated.mp4"
    output_json_suffix: str = ".json"
    save_video: bool = True
    save_json: bool = True
    display_scale: float = 1.0


@dataclass
class TableConfig:
    smooth_alpha: float = 0.7


@dataclass
class PersonConfig:
    model_path: str = "yolo26n-pose.pt"
    confidence_threshold: float = 0.2
    person_class_id: int = 0


@dataclass
class FilterConfig:
    max_players_per_side: int = 2
    umpire_zone_ratio_top: float = 0.35
    min_person_area_ratio: float = 0.003
    outside_margin_x_ratio: float = 0.75


@dataclass
class LLMConfig:
    enabled: bool = True
    provider: str = "openai_responses"
    model_name: str = "gpt-4.1-mini"
    prompt_path: Path = Path("prompts/action_analysis_v5.md")
    sample_count: int | None = None
    frame_stride: int = 1
    jpeg_quality: int = 85
    save_json: bool = True
    output_json_suffix: str = "_llm_v5.json"


@dataclass
class AppConfig:
    video: VideoConfig = field(default_factory=VideoConfig)
    table: TableConfig = field(default_factory=TableConfig)
    person: PersonConfig = field(default_factory=PersonConfig)
    filter: FilterConfig = field(default_factory=FilterConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)

    @property
    def output_dir_path(self) -> Path:
        return Path(self.video.output_dir)