from __future__ import annotations

from auto_foundry.config import Settings
from auto_foundry.ingestion.github_issues import GitHubIssuesAdapter
from auto_foundry.ingestion.hacker_news import HackerNewsAdapter
from auto_foundry.ingestion.mock_adapter import MockAdapter
from auto_foundry.ingestion.reddit import RedditAdapter
from auto_foundry.ingestion.stack_exchange import StackExchangeAdapter
from auto_foundry.schemas import Discussion, NormalizedDiscussionRecord, SourceHealthCheck


EXTERNAL_ADAPTERS = {
    "reddit": RedditAdapter,
    "hacker_news": HackerNewsAdapter,
    "hn": HackerNewsAdapter,
    "stack_exchange": StackExchangeAdapter,
    "stackexchange": StackExchangeAdapter,
    "github_issues": GitHubIssuesAdapter,
    "github": GitHubIssuesAdapter,
}


def fetch_normalized_records(settings: Settings, include_external: bool = True) -> list[NormalizedDiscussionRecord]:
    mock_records = MockAdapter().fetch_seed_posts(settings.ingestion_limit)
    if not include_external or settings.ingestion_source == "mock":
        return _dedupe_records(mock_records)

    adapter_class = EXTERNAL_ADAPTERS.get(settings.ingestion_source)
    if adapter_class is None:
        return _dedupe_records(mock_records)

    try:
        adapter = adapter_class(settings)
        health = adapter.healthcheck()
        if not health.ok:
            return _dedupe_records(mock_records)
        external_records = adapter.fetch_seed_posts(settings.ingestion_limit)
    except Exception:
        external_records = []

    return _dedupe_records([*mock_records, *external_records])


def fetch_discussions(settings: Settings, include_external: bool = True) -> list[Discussion]:
    return [record.to_discussion() for record in fetch_normalized_records(settings, include_external=include_external)]


def healthcheck_sources(settings: Settings) -> list[SourceHealthCheck]:
    checks = [MockAdapter().healthcheck()]
    adapter_class = EXTERNAL_ADAPTERS.get(settings.ingestion_source)
    if adapter_class is not None:
        try:
            checks.append(adapter_class(settings).healthcheck())
        except Exception as exc:
            checks.append(SourceHealthCheck(source=settings.ingestion_source, ok=False, message=str(exc)))
    return checks


def _dedupe_records(records: list[NormalizedDiscussionRecord]) -> list[NormalizedDiscussionRecord]:
    seen: set[str] = set()
    deduped: list[NormalizedDiscussionRecord] = []
    for record in records:
        key = record.stable_discussion_id
        if key in seen:
            continue
        seen.add(key)
        deduped.append(record)
    return deduped
