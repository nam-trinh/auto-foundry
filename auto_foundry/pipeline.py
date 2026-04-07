from __future__ import annotations

from auto_foundry.clustering.clusterer import cluster_pain_signals
from auto_foundry.config import get_settings
from auto_foundry.db.database import connect, init_db
from auto_foundry.db.repository import (
    clear_derived_records,
    insert_opportunities,
    insert_pain_signals,
    insert_startup_ideas,
    list_discussions,
    upsert_discussions,
)
from auto_foundry.extraction.pain_extractor import extract_pain_signals
from auto_foundry.idea_generation.generator import generate_startup_ideas
from auto_foundry.ingestion.service import fetch_discussions
from auto_foundry.llm.openai_client import LLMClient
from auto_foundry.schemas import PipelineRunResult
from auto_foundry.scoring.scorer import score_opportunities


def run_pipeline() -> PipelineRunResult:
    settings = get_settings()
    init_db(settings.db_path)
    llm_client = LLMClient(settings)

    with connect(settings.db_path) as connection:
        upsert_discussions(connection, fetch_discussions(settings, include_external=True))
        discussions = list_discussions(connection)
        clear_derived_records(connection)

        pain_signals, extraction_source = extract_pain_signals(discussions, llm_client)
        opportunities = cluster_pain_signals(pain_signals)
        scored_opportunities = score_opportunities(opportunities, pain_signals)
        startup_ideas, idea_generation_source = generate_startup_ideas(scored_opportunities, llm_client)

        insert_pain_signals(connection, pain_signals)
        insert_opportunities(connection, scored_opportunities)
        insert_startup_ideas(connection, startup_ideas)

    return PipelineRunResult(
        discussions_count=len(discussions),
        pain_signals_count=len(pain_signals),
        opportunities_count=len(scored_opportunities),
        startup_ideas_count=len(startup_ideas),
        extraction_source=extraction_source,
        idea_generation_source=idea_generation_source,
        llm_model=settings.llm_model,
    )
