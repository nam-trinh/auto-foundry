from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class Discussion(BaseModel):
    id: str
    source: str
    author: str
    title: str
    body: str


class NormalizedComment(BaseModel):
    comment_id: str
    author: str | None = None
    body: str
    created_at: datetime | None = None
    score: int | None = None
    parent_id: str | None = None


class NormalizedDiscussionRecord(BaseModel):
    source: str
    source_id: str
    url: str | None = None
    community: str | None = None
    title: str
    body: str
    comments: list[NormalizedComment] = Field(default_factory=list)
    created_at: datetime | None = None
    author: str | None = None
    engagement: int | None = None
    tags: list[str] = Field(default_factory=list)
    raw_metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def stable_discussion_id(self) -> str:
        return f"{self.source}:{self.source_id}"

    def to_discussion(self) -> Discussion:
        comments_text = "\n".join(comment.body for comment in self.comments if comment.body)
        body_parts = [self.body]
        if comments_text:
            body_parts.append(f"Comments:\n{comments_text}")
        return Discussion(
            id=self.stable_discussion_id,
            source=self.source,
            author=self.author or "unknown",
            title=self.title,
            body="\n\n".join(part for part in body_parts if part),
        )


class SourceHealthCheck(BaseModel):
    source: str
    ok: bool
    message: str


class LLMHealthStatus(BaseModel):
    provider: str
    model: str
    configured: bool
    reachable: bool
    message: str


class SourceConfig(BaseModel):
    id: str
    source_type: str
    query: str
    enabled: bool = True
    polling_interval_minutes: int = 180
    overlap_window_minutes: int = 720
    created_at: datetime
    updated_at: datetime


class IngestionState(BaseModel):
    source_config_id: str
    last_successful_discovery_at: datetime | None = None
    last_attempted_discovery_at: datetime | None = None
    last_reconciliation_at: datetime | None = None
    last_seen_external_item_id: str | None = None
    updated_at: datetime


class IngestionRun(BaseModel):
    id: str
    source_config_id: str
    job_type: str
    started_at: datetime
    finished_at: datetime | None = None
    status: str
    fetched_count: int = 0
    inserted_count: int = 0
    updated_count: int = 0
    skipped_count: int = 0
    error_message: str | None = None


class TrackedThread(BaseModel):
    internal_id: str
    source_config_id: str
    source_type: str
    external_thread_id: str
    external_url: str | None = None
    source_created_at: datetime | None = None
    first_seen_at: datetime
    last_seen_at: datetime
    last_comment_refresh_at: datetime | None = None
    last_observed_comment_count: int = 0
    activity_status: str = "hot"
    active_polling_enabled: bool = True
    raw_metadata: dict[str, Any] = Field(default_factory=dict)


class IngestionJobResult(BaseModel):
    run_id: str
    source_config_id: str
    job_type: str
    status: str
    fetched_count: int = 0
    inserted_count: int = 0
    updated_count: int = 0
    skipped_count: int = 0
    error_message: str | None = None


def datetime_from_unix(timestamp: int | float | None) -> datetime | None:
    if timestamp is None:
        return None
    return datetime.fromtimestamp(timestamp, tz=timezone.utc)


class PainSignal(BaseModel):
    id: str
    discussion_id: str
    summary: str
    quote: str
    severity: int = Field(ge=1, le=5)
    theme_hint: str
    source: str = "fallback"


class ScoreBreakdown(BaseModel):
    frequency: float
    severity: float
    willingness_to_pay: float
    urgency: float
    final_score: float
    formula: str


class Opportunity(BaseModel):
    id: str
    theme: str
    title: str
    summary: str
    evidence_count: int
    source_pain_ids: list[str]
    score: ScoreBreakdown


class StartupIdea(BaseModel):
    id: str
    opportunity_id: str
    name: str
    target_customer: str
    problem: str
    solution: str
    mvp: str
    why_now: str
    key_risk: str
    source: str = "fallback"


class PipelineRunResult(BaseModel):
    discussions_count: int
    pain_signals_count: int
    opportunities_count: int
    startup_ideas_count: int
    extraction_source: str
    idea_generation_source: str
    llm_model: str
