from __future__ import annotations

import json
from typing import Any

from openai import OpenAI

from auto_foundry.config import Settings


class LLMClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    @property
    def is_configured(self) -> bool:
        return self.settings.llm_provider == "openai" and bool(self.settings.openai_api_key)

    def generate_json(self, prompt: str) -> dict[str, Any] | None:
        if not self.is_configured:
            return None

        try:
            client = OpenAI(api_key=self.settings.openai_api_key, timeout=self.settings.llm_timeout_seconds)
            response = client.responses.create(
                model=self.settings.llm_model,
                input=prompt,
                max_output_tokens=self.settings.llm_max_output_tokens,
                text={"format": {"type": "json_object"}},
            )
            return json.loads(response.output_text)
        except Exception:
            return None
