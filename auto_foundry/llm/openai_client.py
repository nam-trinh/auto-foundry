from __future__ import annotations

import json
import logging
from typing import Any

from openai import OpenAI

from auto_foundry.config import Settings
from auto_foundry.schemas import LLMHealthStatus

logger = logging.getLogger(__name__)


class LLMClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    @property
    def is_configured(self) -> bool:
        return self.settings.llm_provider == "openai" and bool(self.settings.openai_api_key)

    def check_connectivity(self) -> LLMHealthStatus:
        if self.settings.llm_provider != "openai":
            return LLMHealthStatus(
                provider=self.settings.llm_provider,
                model=self.settings.llm_model,
                configured=False,
                reachable=False,
                message="unsupported_provider",
            )
        if not self.settings.openai_api_key:
            return LLMHealthStatus(
                provider=self.settings.llm_provider,
                model=self.settings.llm_model,
                configured=False,
                reachable=False,
                message="no_api_key",
            )

        try:
            self._client().responses.create(
                model=self.settings.llm_model,
                input="Respond with the word ok.",
                max_output_tokens=16,
            )
            return LLMHealthStatus(
                provider=self.settings.llm_provider,
                model=self.settings.llm_model,
                configured=True,
                reachable=True,
                message="ok",
            )
        except Exception as exc:
            return LLMHealthStatus(
                provider=self.settings.llm_provider,
                model=self.settings.llm_model,
                configured=True,
                reachable=False,
                message=_sanitize_error_message(exc),
            )

    def generate_json(self, prompt: str, max_output_tokens: int | None = None) -> dict[str, Any] | None:
        return self.generate_json_with_schema(prompt=prompt, max_output_tokens=max_output_tokens, json_schema=None)

    def generate_json_with_schema(
        self,
        prompt: str,
        max_output_tokens: int | None = None,
        json_schema: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        if not self.is_configured:
            print(f"[LLM] skipped model={self.settings.llm_model} reason=not_configured")
            return None

        output_limit = max_output_tokens or self.settings.llm_max_output_tokens
        print(
            f"[LLM] request model={self.settings.llm_model} prompt_chars={len(prompt)} "
            f"max_output_tokens={output_limit} strict_schema={bool(json_schema)}"
        )
        response_format: dict[str, Any]
        if json_schema:
            response_format = {
                "format": {
                    "type": "json_schema",
                    "name": "auto_foundry_payload",
                    "schema": json_schema,
                    "strict": True,
                }
            }
        else:
            response_format = {"format": {"type": "json_object"}}
        try:
            response = self._client().responses.create(
                model=self.settings.llm_model,
                input=prompt,
                max_output_tokens=output_limit,
                text=response_format,
            )
            output_text = _extract_response_text(response)
            if not output_text.strip():
                status = getattr(response, "status", None)
                incomplete_details = getattr(response, "incomplete_details", None)
                print(
                    f"[LLM] warning model={self.settings.llm_model} payload is empty "
                    f"status={status} incomplete_details={_safe_repr(incomplete_details)}"
                )
                return None
            payload = _loads_json_payload(output_text)
            payload_keys = list(payload.keys()) if isinstance(payload, dict) else []
            print(
                f"[LLM] success model={self.settings.llm_model} "
                f"output_chars={len(output_text)} payload_type={type(payload).__name__} keys={payload_keys}"
            )
            return payload
        except Exception as exc:
            sanitized = _sanitize_error_message(exc)
            print(f"[LLM] failed model={self.settings.llm_model} error_type={type(exc).__name__} message={sanitized}")
            return None

    def _client(self) -> OpenAI:
        return OpenAI(api_key=self.settings.openai_api_key, timeout=self.settings.llm_timeout_seconds)


def _sanitize_error_message(exc: Exception) -> str:
    message = str(exc).strip() or exc.__class__.__name__
    lowered = message.lower()
    if "api key" in lowered or "authentication" in lowered or "unauthorized" in lowered:
        return "authentication_failed"
    if "model" in lowered and ("not found" in lowered or "permission" in lowered or "access" in lowered):
        return "model_unavailable"
    if "timeout" in lowered:
        return "request_timeout"
    if "ssl" in lowered or "connection" in lowered or "network" in lowered:
        return "network_error"
    return message[:160]


def _extract_response_text(response: Any) -> str:
    direct = getattr(response, "output_text", None)
    if isinstance(direct, str) and direct.strip():
        return direct

    output_items = getattr(response, "output", None) or []
    text_chunks: list[str] = []
    for item in output_items:
        item_type = _read_field(item, "type")
        if item_type != "message":
            continue
        content_items = _read_field(item, "content") or []
        for content in content_items:
            content_type = _read_field(content, "type")
            if content_type != "output_text":
                continue
            text_value = _read_field(content, "text")
            if isinstance(text_value, str) and text_value.strip():
                text_chunks.append(text_value)
    return "\n".join(text_chunks)


def _loads_json_payload(output_text: str) -> dict[str, Any]:
    try:
        parsed = json.loads(output_text)
        if isinstance(parsed, dict):
            return parsed
        raise ValueError("json_payload_not_object")
    except json.JSONDecodeError:
        candidate = _extract_json_object_slice(output_text)
        if candidate:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
        raise


def _extract_json_object_slice(text: str) -> str | None:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    return text[start : end + 1]


def _read_field(obj: Any, key: str) -> Any:
    if isinstance(obj, dict):
        return obj.get(key)
    return getattr(obj, key, None)


def _safe_repr(value: Any) -> str:
    text = repr(value)
    if len(text) > 240:
        return text[:237] + "..."
    return text
