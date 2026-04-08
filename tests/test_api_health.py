from __future__ import annotations

from fastapi.testclient import TestClient

from auto_foundry.api import app as app_module


def test_health_includes_llm_status(monkeypatch) -> None:
    monkeypatch.setattr(
        app_module,
        "llm_status_cache",
        app_module.LLMHealthStatus(
            provider="openai",
            model="gpt-5-mini",
            configured=False,
            reachable=False,
            message="no_api_key",
        ),
    )

    client = TestClient(app_module.app)
    response = client.get("/api/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["llm"]["provider"] == "openai"
    assert payload["llm"]["model"] == "gpt-5-mini"
    assert payload["llm"]["configured"] is False
    assert payload["llm"]["reachable"] is False
    assert payload["llm"]["message"] == "no_api_key"
