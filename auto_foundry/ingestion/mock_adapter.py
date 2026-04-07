from __future__ import annotations

from auto_foundry.ingestion.mock_data import SEED_DISCUSSIONS
from auto_foundry.schemas import NormalizedDiscussionRecord, SourceHealthCheck


class MockAdapter:
    source_name = "mock"

    def healthcheck(self) -> SourceHealthCheck:
        return SourceHealthCheck(source=self.source_name, ok=True, message="Mock seed data is available.")

    def fetch_seed_posts(self, limit: int) -> list[NormalizedDiscussionRecord]:
        return [self.normalize_record(item) for item in SEED_DISCUSSIONS[:limit]]

    def fetch_comments(self, record: object, limit: int) -> list[object]:
        return []

    def normalize_record(self, record: object) -> NormalizedDiscussionRecord:
        discussion = record
        return NormalizedDiscussionRecord(
            source=discussion.source,
            source_id=discussion.id,
            url=None,
            community=discussion.source,
            title=discussion.title,
            body=discussion.body,
            comments=[],
            author=discussion.author,
            engagement=None,
            tags=["mock"],
            raw_metadata={"mock": True},
        )
