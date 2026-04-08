from __future__ import annotations

from typing import Any, Protocol

from auto_foundry.config import Settings
from auto_foundry.schemas import NormalizedComment, NormalizedDiscussionRecord, SourceHealthCheck, TrackedThread


class SourceAdapter(Protocol):
    source_name: str

    def healthcheck(self) -> SourceHealthCheck:
        """Validate lightweight config without doing expensive fetch work."""

    def fetch_seed_posts(self, limit: int) -> list[NormalizedDiscussionRecord]:
        """Fetch and normalize discussion posts."""

    def fetch_comments(self, record: Any, limit: int) -> list[Any]:
        """Fetch source-specific comments when supported."""

    def fetch_thread_comments(self, thread: TrackedThread, limit: int) -> list[NormalizedComment]:
        """Refresh comments for a known tracked thread."""

    def normalize_record(self, record: Any) -> NormalizedDiscussionRecord | None:
        """Normalize one source-specific record. Return None to skip it."""


def configured_subreddits(settings: Settings) -> list[str]:
    return settings.reddit_subreddits or ["startups", "SaaS", "Entrepreneur"]


def configured_stack_exchange_tags(settings: Settings) -> list[str]:
    return settings.stack_exchange_tags or ["python", "fastapi"]
