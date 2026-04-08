from __future__ import annotations

from auto_foundry.config import Settings
from auto_foundry.idea_generation.generator import generate_startup_ideas
from auto_foundry.llm.openai_client import LLMClient
from auto_foundry.schemas import Opportunity, ScoreBreakdown


def _settings(**overrides: object) -> Settings:
    values = {
        "openai_api_key": None,
        "llm_provider": "openai",
        "llm_model": "gpt-5-mini",
        "llm_model_dev": "gpt-5-mini",
        "llm_model_prod": "gpt-5",
        "llm_timeout_seconds": 1,
        "llm_max_output_tokens": 50,
        "db_path": "test.sqlite3",
        "ingestion_source": "mock",
        "ingestion_sources": None,
        "ingestion_limit": 5,
    }
    values.update(overrides)
    return Settings(**values)


def test_check_connectivity_returns_skip_when_no_api_key() -> None:
    status = LLMClient(_settings(openai_api_key=None)).check_connectivity()

    assert status.configured is False
    assert status.reachable is False
    assert status.message == "no_api_key"


def test_check_connectivity_returns_success_when_probe_works(monkeypatch) -> None:
    client = LLMClient(_settings(openai_api_key="test-key"))
    captured: dict[str, object] = {}

    class FakeResponses:
        def create(self, **kwargs):
            captured.update(kwargs)

            class Response:
                output_text = "ok"

            return Response()

    class FakeClient:
        responses = FakeResponses()

    monkeypatch.setattr(client, "_client", lambda: FakeClient())

    status = client.check_connectivity()

    assert status.configured is True
    assert status.reachable is True
    assert status.message == "ok"
    assert captured["max_output_tokens"] == 16


def test_generate_json_uses_override_max_output_tokens(monkeypatch) -> None:
    client = LLMClient(_settings(openai_api_key="test-key"))
    captured: dict[str, object] = {}

    class FakeResponses:
        def create(self, **kwargs):
            captured.update(kwargs)

            class Response:
                output_text = "{\"pain_signals\": []}"

            return Response()

    class FakeClient:
        responses = FakeResponses()

    monkeypatch.setattr(client, "_client", lambda: FakeClient())

    payload = client.generate_json("prompt", max_output_tokens=2048)

    assert payload == {"pain_signals": []}
    assert captured["max_output_tokens"] == 2048


def test_check_connectivity_treats_empty_response_as_reachable(monkeypatch) -> None:
    client = LLMClient(_settings(openai_api_key="test-key"))

    class FakeResponses:
        def create(self, **kwargs):
            class Response:
                output_text = ""

            return Response()

    class FakeClient:
        responses = FakeResponses()

    monkeypatch.setattr(client, "_client", lambda: FakeClient())

    status = client.check_connectivity()

    assert status.configured is True
    assert status.reachable is True
    assert status.message == "ok"


def test_check_connectivity_returns_sanitized_failure(monkeypatch) -> None:
    client = LLMClient(_settings(openai_api_key="bad-key"))

    class FakeResponses:
        def create(self, **kwargs):
            raise RuntimeError("Authentication failed for provided API key")

    class FakeClient:
        responses = FakeResponses()

    monkeypatch.setattr(client, "_client", lambda: FakeClient())

    status = client.check_connectivity()

    assert status.configured is True
    assert status.reachable is False
    assert status.message == "authentication_failed"


def test_generate_startup_ideas_calls_llm_once_per_opportunity(monkeypatch) -> None:
    client = LLMClient(_settings(openai_api_key="test-key"))
    prompts: list[str] = []

    def fake_generate_json_with_schema(
        prompt: str,
        max_output_tokens: int | None = None,
        json_schema: dict | None = None,
    ):
        prompts.append(prompt)
        index = len(prompts)
        return {
            "startup_idea": {
                "name": f"Idea {index}",
                "target_customer": "Ops teams",
                "problem": "Manual work",
                "solution": "Automation",
                "mvp": "Basic workflow",
                "why_now": "AI adoption",
                "key_risk": "Distribution",
            }
        }

    monkeypatch.setattr(client, "generate_json_with_schema", fake_generate_json_with_schema)

    opportunities = [
        Opportunity(
            id="opp-1",
            theme="workflow automation",
            title="Opportunity 1",
            summary="Summary 1",
            evidence_count=1,
            source_pain_ids=["pain-1"],
            score=ScoreBreakdown(
                frequency=4.0,
                severity=4.0,
                willingness_to_pay=4.0,
                urgency=4.0,
                final_score=4.0,
                formula="formula",
            ),
        ),
        Opportunity(
            id="opp-2",
            theme="reporting and analytics",
            title="Opportunity 2",
            summary="Summary 2",
            evidence_count=1,
            source_pain_ids=["pain-2"],
            score=ScoreBreakdown(
                frequency=4.0,
                severity=4.0,
                willingness_to_pay=4.0,
                urgency=4.0,
                final_score=4.0,
                formula="formula",
            ),
        ),
    ]

    ideas, source = generate_startup_ideas(opportunities, client)

    assert source == "llm"
    assert len(ideas) == 2
    assert len(prompts) == 2
