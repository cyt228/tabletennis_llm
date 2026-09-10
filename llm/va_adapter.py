from __future__ import annotations

import os
from typing import Any, List

from dotenv import load_dotenv
from openai import OpenAI

from llm.clip_loader import SampledFrame


load_dotenv()


class VAAdapter:
    """
    OpenRouter 相容層。

    影片由 ClipLoader 抽取影格，再將多張 JPEG 圖片透過 OpenRouter
    傳給視覺模型。

    回傳內容包含：
    - 模型文字輸出
    - token usage
    - OpenRouter 回傳成本（若有）
    - response id
    """

    def __init__(
        self,
        provider: str = "openrouter",
        model_name: str = "openai/gpt-4.1-mini",
    ):
        self.provider = provider
        self.model_name = model_name

        if self.provider != "openrouter":
            raise ValueError(f"Unsupported provider: {self.provider}")

        api_key = os.getenv("OPENROUTER_API_KEY")

        if not api_key:
            raise EnvironmentError(
                "OPENROUTER_API_KEY is not set in .env or environment."
            )

        self.client = OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
        )

    def analyze_clip_frames(
        self,
        prompt_text: str,
        frames: List[SampledFrame],
    ) -> dict[str, Any]:
        if not frames:
            raise ValueError("frames is empty")

        content: list[dict[str, Any]] = [
            {
                "type": "text",
                "text": prompt_text,
            }
        ]

        for frame in frames:
            content.append(
                {
                    "type": "image_url",
                    "image_url": {
                        "url": (
                            "data:image/jpeg;base64,"
                            f"{frame.jpeg_base64}"
                        )
                    },
                }
            )

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {
                    "role": "user",
                    "content": content,
                }
            ],
            temperature=0,
            max_tokens=1000,
            # 要求 OpenRouter 在 response 中附上 usage / cost 資訊。
            extra_body={
                "usage": {
                    "include": True,
                }
            },
        )

        result_text = response.choices[0].message.content

        if not result_text:
            raise RuntimeError("OpenRouter returned an empty response.")

        usage_dict: dict[str, Any] = {}

        if response.usage is not None:
            # OpenAI SDK 的 response model 可轉成 dict；
            # OpenRouter 額外欄位（如 cost）若有回傳也會盡量保留。
            if hasattr(response.usage, "model_dump"):
                usage_dict = response.usage.model_dump()
            else:
                usage_dict = {
                    "prompt_tokens": getattr(
                        response.usage, "prompt_tokens", None
                    ),
                    "completion_tokens": getattr(
                        response.usage, "completion_tokens", None
                    ),
                    "total_tokens": getattr(
                        response.usage, "total_tokens", None
                    ),
                }

        prompt_tokens = usage_dict.get("prompt_tokens")
        completion_tokens = usage_dict.get("completion_tokens")
        total_tokens = usage_dict.get("total_tokens")
        cost = usage_dict.get("cost")

        # 保留細節，之後若要分析 cached / reasoning token 可直接使用。
        prompt_details = usage_dict.get("prompt_tokens_details")
        completion_details = usage_dict.get("completion_tokens_details")

        return {
            "text": result_text,
            "response_id": getattr(response, "id", None),
            "usage": {
                "input_tokens": prompt_tokens,
                "output_tokens": completion_tokens,
                "total_tokens": total_tokens,
                "cost_usd": cost,
                "prompt_tokens_details": prompt_details,
                "completion_tokens_details": completion_details,
                "raw_usage": usage_dict,
            },
        }