from __future__ import annotations

from auto_foundry.clustering.clusterer import cluster_pain_signals
from auto_foundry.db.database import connect, init_db
from auto_foundry.db.repository import list_discussions, upsert_discussions
from auto_foundry.extraction.pain_extractor import extract_pain_signals
from auto_foundry.idea_generation.generator import generate_startup_ideas
from auto_foundry.ingestion.mock_data import SEED_DISCUSSIONS
from auto_foundry.llm.openai_client import LLMClient
from auto_foundry.config import Settings
from auto_foundry.pipeline import run_pipeline
from auto_foundry.scoring.scorer import score_opportunities


def _settings(db_path: str) -> Settings:
    return Settings(
        openai_api_key=None,
        llm_provider="openai",
        llm_model="gpt-5-mini",
        llm_model_dev="gpt-5-mini",
        llm_model_prod="gpt-5",
        llm_timeout_seconds=1,
        llm_max_output_tokens=200,
        db_path=db_path,
    )


def test_seed_discussions_are_idempotent(tmp_path) -> None:
    db_path = str(tmp_path / "test.sqlite3")
    init_db(db_path)

    with connect(db_path) as connection:
        upsert_discussions(connection, SEED_DISCUSSIONS)
        upsert_discussions(connection, SEED_DISCUSSIONS)
        discussions = list_discussions(connection)

    assert len(discussions) == len(SEED_DISCUSSIONS)


def test_fallback_pipeline_steps_generate_ranked_ideas(tmp_path) -> None:
    settings = _settings(str(tmp_path / "test.sqlite3"))
    llm_client = LLMClient(settings)

    signals, extraction_source = extract_pain_signals(SEED_DISCUSSIONS, llm_client)
    opportunities = cluster_pain_signals(signals)
    scored = score_opportunities(opportunities, signals)
    ideas, idea_source = generate_startup_ideas(scored, llm_client)

    assert extraction_source == "fallback"
    assert idea_source == "fallback"
    assert len(signals) > 0
    assert len(scored) > 0
    assert len(ideas) == len(scored)
    assert scored[0].score.final_score > 0
    assert "frequency" in scored[0].score.model_dump()


def test_run_pipeline_reports_fallback_without_api_key(tmp_path, monkeypatch) -> None:
    db_path = str(tmp_path / "pipeline.sqlite3")
    monkeypatch.setenv("AUTO_FOUNDRY_DB_PATH", db_path)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    result = run_pipeline()

    assert result.discussions_count == len(SEED_DISCUSSIONS)
    assert result.pain_signals_count > 0
    assert result.opportunities_count > 0
    assert result.startup_ideas_count == result.opportunities_count
    assert result.extraction_source == "fallback"
    assert result.idea_generation_source == "fallback"
