from __future__ import annotations

from auto_foundry.config import Settings, configured_ingestion_sources, should_include_mock_source
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
    requested_sources = configured_ingestion_sources(settings)
    records: list[NormalizedDiscussionRecord] = []

    if should_include_mock_source(settings) or not include_external:
        records.extend(MockAdapter().fetch_seed_posts(settings.ingestion_limit))

    if not include_external:
        return _dedupe_records(records)

    for source_name in requested_sources:
        if source_name == "mock":
            continue
        adapter_class = EXTERNAL_ADAPTERS.get(source_name)
        if adapter_class is None:
            continue
        try:
            adapter = adapter_class(settings)
            health = adapter.healthcheck()
            if not health.ok:
                continue
            records.extend(adapter.fetch_seed_posts(settings.ingestion_limit))
        except Exception:
            continue

    return _dedupe_records(records)


def fetch_discussions(settings: Settings, include_external: bool = True) -> list[Discussion]:
    return [record.to_discussion() for record in fetch_normalized_records(settings, include_external=include_external)]


def healthcheck_sources(settings: Settings) -> list[SourceHealthCheck]:
    checks: list[SourceHealthCheck] = []
    for source_name in configured_ingestion_sources(settings):
        if source_name == "mock":
            checks.append(MockAdapter().healthcheck())
            continue
        adapter_class = EXTERNAL_ADAPTERS.get(source_name)
        if adapter_class is None:
            checks.append(SourceHealthCheck(source=source_name, ok=False, message="Unknown ingestion source."))
            continue
        try:
            checks.append(adapter_class(settings).healthcheck())
        except Exception as exc:
            checks.append(SourceHealthCheck(source=source_name, ok=False, message=str(exc)))
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
