from __future__ import annotations

import os
from typing import List

from dotenv import load_dotenv
from openai import OpenAI

from llm.clip_loader import SampledFrame

load_dotenv()


class VAAdapter:
    """
    v1 的 Vision-Agents 相容層。

    目前先保留 Vision Agents 風格的 adapter 分層，
    實際 inference 走 OpenAI Responses API。
    後面若要改成真正的 Vision Agents realtime / VLM 流程，
    只需要改這一層。
    """

    def __init__(self, provider: str = "openai_responses", model_name: str = "gpt-4.1-mini"):
        self.provider = provider
        self.model_name = model_name

        if self.provider != "openai_responses":
            raise ValueError(f"Unsupported provider for v1: {self.provider}")

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise EnvironmentError("OPENAI_API_KEY is not set in .env or environment.")

        self.client = OpenAI(api_key=api_key)

    def analyze_clip_frames(self, prompt_text: str, frames: List[SampledFrame]) -> str:
        if not frames:
            raise ValueError("frames is empty")

        content = [{"type": "input_text", "text": prompt_text}]

        for frame in frames:
            content.append(
                {
                    "type": "input_image",
                    "image_url": f"data:image/jpeg;base64,{frame.jpeg_base64}",
                }
            )

        response = self.client.responses.create(
            model=self.model_name,
            input=[
                {
                    "role": "user",
                    "content": content,
                }
            ],
        )

        return response.output_text