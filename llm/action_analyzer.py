from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from llm.clip_loader import ClipInfo
from llm.prompt_loader import load_markdown_prompt
from llm.va_adapter import VAAdapter
from llm.action_guide_loader import load_action_guide


LABEL_MAP = {
    0: {"zh": "無", "en": "none", "type": "無"},
    1: {"zh": "拉球", "en": "drive", "type": "攻擊"},
    2: {"zh": "反拉", "en": "counter drive", "type": "攻擊"},
    3: {"zh": "殺球", "en": "smash", "type": "攻擊"},
    4: {"zh": "擰球", "en": "backhand twist", "type": "攻擊"},
    5: {"zh": "快帶", "en": "fast drive", "type": "攻擊"},
    6: {"zh": "推擠", "en": "fast push", "type": "攻擊"},
    7: {"zh": "挑撥", "en": "flip", "type": "攻擊"},
    8: {"zh": "拱球", "en": "pimple’s long push", "type": "控制"},
    9: {"zh": "磕球", "en": "pimple’s fast push", "type": "控制"},
    10: {"zh": "搓球", "en": "long push", "type": "控制"},
    11: {"zh": "擺短", "en": "drop shot", "type": "控制"},
    12: {"zh": "削球", "en": "chop", "type": "防守"},
    13: {"zh": "擋球", "en": "block", "type": "防守"},
    14: {"zh": "放高球", "en": "lob", "type": "防守"},
    15: {"zh": "傳統", "en": "traditional", "type": "發球"},
    16: {"zh": "勾手", "en": "hook", "type": "發球"},
    17: {"zh": "逆旋轉", "en": "reverse", "type": "發球"},
    18: {"zh": "下蹲式", "en": "squat", "type": "發球"},
}


class ActionAnalyzer:
    def __init__(
        self,
        provider: str,
        model_name: str,
        prompt_path: str | Path,
        action_guide_path: str | Path | None = None,
    ):
        self.provider = provider
        self.model_name = model_name
        self.prompt_path = Path(prompt_path)
        self.action_guide_path = Path(action_guide_path) if action_guide_path else None

        self.adapter = VAAdapter(
            provider=self.provider,
            model_name=self.model_name,
        )

    def analyze(self, clip_info: ClipInfo) -> dict[str, Any]:
        prompt_text = self._build_prompt()

        raw_text = self.adapter.analyze_clip_frames(
            prompt_text=prompt_text,
            frames=clip_info.sampled_frames,
        )

        prediction = self._parse_prediction(raw_text, clip_info.video_path.name)

        return {
            "video_info": {
                "video_path": str(clip_info.video_path),
                "video_name": clip_info.video_path.name,
                "fps": clip_info.fps,
                "frame_count": clip_info.frame_count,
                "width": clip_info.width,
                "height": clip_info.height,
                "duration_sec": clip_info.duration_sec,
                "sampled_frame_indices": [f.frame_idx for f in clip_info.sampled_frames],
            },
            "provider": self.provider,
            "model_name": self.model_name,
            "prompt_path": str(self.prompt_path),
            "prediction": prediction,
            "raw_response": raw_text,
        }
    
    def _build_prompt(self) -> str:
        prompt_text = load_markdown_prompt(self.prompt_path)

        if self.action_guide_path is None:
            return prompt_text

        action_guide = load_action_guide(self.action_guide_path)

        if "{{ACTION_GUIDE}}" in prompt_text:
            return prompt_text.replace("{{ACTION_GUIDE}}", action_guide)

        return (
            f"{prompt_text}\n\n"
            f"Action guide:\n"
            f"{action_guide}"
        )

    def _parse_prediction(self, raw_text: str, video_name: str) -> dict[str, Any]:
        cleaned = raw_text.strip()

        if cleaned.startswith("```json"):
            cleaned = cleaned[len("```json"):].strip()
        elif cleaned.startswith("```"):
            cleaned = cleaned[len("```"):].strip()

        if cleaned.endswith("```"):
            cleaned = cleaned[:-3].strip()

        try:
            parsed = json.loads(cleaned)
            predicted_label = int(parsed.get("predicted_label", 0))
        except (json.JSONDecodeError, ValueError, TypeError):
            predicted_label = 0

        if predicted_label not in LABEL_MAP:
            predicted_label = 0

        label_info = LABEL_MAP[predicted_label]

        return {
            "video_name": video_name,
            "predicted_label": predicted_label,
            "predicted_name_zh": label_info["zh"],
            "predicted_name_en": label_info["en"],
            "predicted_type": label_info["type"],
            "action_guide_path": str(self.action_guide_path) if self.action_guide_path else None,
        }

 