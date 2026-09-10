from __future__ import annotations

import json
import time
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

COARSE_MAP = {
    0: "zero",
    1: "attack",
    2: "attack",
    3: "attack",
    4: "attack",
    5: "attack",
    6: "attack",
    7: "attack",
    8: "control",
    9: "control",
    10: "control",
    11: "control",
    12: "defensive",
    13: "defensive",
    14: "defensive",
    15: "serve",
    16: "serve",
    17: "serve",
    18: "serve",
}

VALID_COARSE_CATEGORIES = {
    "zero",
    "attack",
    "control",
    "defensive",
    "serve",
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
        self.action_guide_path = (
            Path(action_guide_path) if action_guide_path else None
        )

        self.adapter = VAAdapter(
            provider=self.provider,
            model_name=self.model_name,
        )

    def analyze(self, clip_info: ClipInfo) -> dict[str, Any]:
        prompt_text = self._build_prompt()

        inference_start = time.perf_counter()

        adapter_result = self.adapter.analyze_clip_frames(
            prompt_text=prompt_text,
            frames=clip_info.sampled_frames,
        )

        inference_sec = time.perf_counter() - inference_start

        raw_text = adapter_result["text"]
        usage = adapter_result.get("usage", {})

        prediction = self._parse_prediction(
            raw_text=raw_text,
            video_name=clip_info.video_path.name,
        )

        return {
            "video_info": {
                "video_path": str(clip_info.video_path),
                "video_name": clip_info.video_path.name,
                "fps": clip_info.fps,
                "frame_count": clip_info.frame_count,
                "width": clip_info.width,
                "height": clip_info.height,
                "duration_sec": clip_info.duration_sec,
                "sampled_frame_count": len(clip_info.sampled_frames),
                "sampled_frame_indices": [
                    f.frame_idx for f in clip_info.sampled_frames
                ],
            },
            "experiment_info": {
                "provider": self.provider,
                "model_name": self.model_name,
                "prompt_path": str(self.prompt_path),
                "prompt_version": self._infer_prompt_version(),
                "action_guide_path": (
                    str(self.action_guide_path)
                    if self.action_guide_path
                    else None
                ),
            },
            "timing": {
                # 只計算送出 VLM request 到收到 response 的時間，
                # 不包含影片讀取與抽 frame。
                "inference_sec": inference_sec,
            },
            "usage": usage,
            "response_id": adapter_result.get("response_id"),
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

    def _infer_prompt_version(self) -> str | None:
        """
        從 prompt 檔名推測版本，例如：
        action_analysis_v7_unified_full_output.md -> v7
        """
        stem = self.prompt_path.stem.lower()

        for version in range(1, 100):
            token = f"v{version}"
            if token in stem:
                return token

        return None

    def _parse_prediction(
        self,
        raw_text: str,
        video_name: str,
    ) -> dict[str, Any]:
        cleaned = raw_text.strip()

        if cleaned.startswith("```json"):
            cleaned = cleaned[len("```json"):].strip()
        elif cleaned.startswith("```"):
            cleaned = cleaned[len("```"):].strip()

        if cleaned.endswith("```"):
            cleaned = cleaned[:-3].strip()

        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            return self._parse_error_result(
                video_name=video_name,
                error=f"JSONDecodeError: {exc}",
            )

        if not isinstance(parsed, dict):
            return self._parse_error_result(
                video_name=video_name,
                error="Response JSON is not an object.",
            )

        try:
            predicted_label = int(parsed["predicted_label"])
        except (KeyError, ValueError, TypeError):
            return self._parse_error_result(
                video_name=video_name,
                error="predicted_label is missing or invalid.",
            )

        if predicted_label not in LABEL_MAP:
            return self._parse_error_result(
                video_name=video_name,
                error=(
                    "predicted_label is outside valid range 0-18: "
                    f"{predicted_label}"
                ),
            )

        label_info = LABEL_MAP[predicted_label]

        coarse_category_raw = parsed.get("coarse_category")
        coarse_category = (
            str(coarse_category_raw).strip().lower()
            if coarse_category_raw is not None
            else None
        )

        # 保留模型自己輸出的 coarse category；
        # derived_coarse_category 則由 label 計算，方便檢查兩者是否一致。
        if coarse_category not in VALID_COARSE_CATEGORIES:
            coarse_category = None

        main_actor = self._optional_string(parsed.get("main_actor"))

        observed_evidence_raw = parsed.get("observed_evidence", [])
        if isinstance(observed_evidence_raw, list):
            observed_evidence = [
                str(item).strip()
                for item in observed_evidence_raw
                if str(item).strip()
            ]
        else:
            observed_evidence = []

        decision_reason = self._optional_string(
            parsed.get("decision_reason")
        )

        closest_alternative = self._optional_int(
            parsed.get("closest_alternative")
        )
        if closest_alternative not in LABEL_MAP:
            closest_alternative = None

        alternative_reason = self._optional_string(
            parsed.get("alternative_reason")
        )

        confidence = self._optional_float(parsed.get("confidence"))
        if confidence is not None:
            confidence = max(0.0, min(1.0, confidence))

        derived_coarse_category = COARSE_MAP[predicted_label]

        return {
            "video_name": video_name,
            "parse_success": True,
            "parse_error": None,
            "predicted_label": predicted_label,
            "predicted_name_zh": label_info["zh"],
            "predicted_name_en": label_info["en"],
            "predicted_type": label_info["type"],
            "coarse_category": coarse_category,
            "derived_coarse_category": derived_coarse_category,
            "coarse_category_consistent": (
                coarse_category == derived_coarse_category
                if coarse_category is not None
                else None
            ),
            "main_actor": main_actor,
            "observed_evidence": observed_evidence,
            "decision_reason": decision_reason,
            "closest_alternative": closest_alternative,
            "alternative_reason": alternative_reason,
            "confidence": confidence,
            "action_guide_path": (
                str(self.action_guide_path)
                if self.action_guide_path
                else None
            ),
        }

    def _parse_error_result(
        self,
        video_name: str,
        error: str,
    ) -> dict[str, Any]:
        """
        Parse 失敗時不要再自動當作 label 0。
        否則 API/格式錯誤會污染真正的 Zero 類評估。
        """
        return {
            "video_name": video_name,
            "parse_success": False,
            "parse_error": error,
            "predicted_label": None,
            "predicted_name_zh": None,
            "predicted_name_en": None,
            "predicted_type": None,
            "coarse_category": None,
            "derived_coarse_category": None,
            "coarse_category_consistent": None,
            "main_actor": None,
            "observed_evidence": [],
            "decision_reason": None,
            "closest_alternative": None,
            "alternative_reason": None,
            "confidence": None,
            "action_guide_path": (
                str(self.action_guide_path)
                if self.action_guide_path
                else None
            ),
        }

    @staticmethod
    def _optional_string(value: Any) -> str | None:
        if value is None:
            return None

        text = str(value).strip()
        return text if text else None

    @staticmethod
    def _optional_int(value: Any) -> int | None:
        if value is None:
            return None

        try:
            return int(value)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _optional_float(value: Any) -> float | None:
        if value is None:
            return None

        try:
            return float(value)
        except (ValueError, TypeError):
            return None