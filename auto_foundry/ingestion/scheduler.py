from __future__ import annotations

import logging
import time
from dataclasses import replace
from datetime import datetime, timedelta, timezone

from auto_foundry.config import Settings, configured_ingestion_sources, get_settings
from auto_foundry.db.database import connect, init_db
from auto_foundry.db.ingestion_repository import (
    ensure_source_config,
    finish_ingestion_run,
    get_or_create_ingestion_state,
    get_source_config,
    get_tracked_thread,
    is_thread_refresh_due,
    list_enabled_source_configs,
    list_refresh_due_threads,
    mark_discovery_attempt,
    mark_discovery_success,
    mark_reconciliation_success,
    mark_thread_comment_refresh,
    start_ingestion_run,
    upsert_comments,
    upsert_normalized_record,
    utc_now,
)
from auto_foundry.ingestion.github_issues import GitHubIssuesAdapter
from auto_foundry.ingestion.hacker_news import HackerNewsAdapter
from auto_foundry.ingestion.mock_adapter import MockAdapter
from auto_foundry.ingestion.reddit import RedditAdapter
from auto_foundry.ingestion.stack_exchange import StackExchangeAdapter
from auto_foundry.schemas import IngestionJobResult, NormalizedDiscussionRecord, SourceConfig, TrackedThread


logger = logging.getLogger(__name__)

GLOBAL_SCHEDULER_TICK_SECONDS = 60 * 60
DEFAULT_DISCOVERY_INTERVAL_MINUTES = 180
DEFAULT_OVERLAP_WINDOW_MINUTES = 720
DEFAULT_RECONCILIATION_INTERVAL_HOURS = 24
DEFAULT_RECONCILIATION_WINDOW_DAYS = 7
DEFAULT_COMMENT_REFRESH_LIMIT = 100

ADAPTERS = {
    "mock": MockAdapter,
    "reddit": RedditAdapter,
    "hacker_news": HackerNewsAdapter,
    "hn": HackerNewsAdapter,
    "stack_exchange": StackExchangeAdapter,
    "stackexchange": StackExchangeAdapter,
    "github_issues": GitHubIssuesAdapter,
    "github": GitHubIssuesAdapter,
}


def scheduler_loop(
    db_path: str | None = None,
    tick_seconds: int = GLOBAL_SCHEDULER_TICK_SECONDS,
) -> None:
    """Simple local scheduler loop. Move this behind cron/APScheduler later if needed."""
    settings = get_settings()
    path = db_path or settings.db_path
    while True:
        run_scheduler_tick(path, settings=settings)
        time.sleep(tick_seconds)


def run_scheduler_tick(
    db_path: str | None = None,
    settings: Settings | None = None,
    now: datetime | None = None,
) -> list[IngestionJobResult]:
    settings = settings or get_settings()
    current_time = now or utc_now()
    path = db_path or settings.db_path
    init_db(path)
    results: list[IngestionJobResult] = []

    with connect(path) as connection:
        ensure_configs_from_settings(connection, settings)
        for config in list_enabled_source_configs(connection):
            if is_post_discovery_due(connection, config, current_time):
                results.append(run_post_discovery_job(connection, settings, config, current_time))
            if is_reconciliation_due(connection, config, current_time):
                results.append(run_reconciliation_job(connection, settings, config, current_time))
        for thread in list_refresh_due_threads(connection, current_time):
            results.append(run_thread_comment_refresh_job(connection, settings, thread, current_time))

    return results


def ensure_configs_from_settings(connection, settings: Settings) -> list[SourceConfig]:
    configs: list[SourceConfig] = []
    for source_type in configured_ingestion_sources(settings):
        configs.append(
            ensure_source_config(
                connection,
                source_type=source_type,
                query=_query_from_settings(settings, source_type),
                polling_interval_minutes=DEFAULT_DISCOVERY_INTERVAL_MINUTES,
                overlap_window_minutes=DEFAULT_OVERLAP_WINDOW_MINUTES,
                enabled=True,
            )
        )
    return configs


def is_post_discovery_due(connection, config: SourceConfig, now: datetime) -> bool:
    state = get_or_create_ingestion_state(connection, config.id)
    if state.last_attempted_discovery_at is None:
        return True
    return now - state.last_attempted_discovery_at >= timedelta(minutes=config.polling_interval_minutes)


def is_reconciliation_due(connection, config: SourceConfig, now: datetime) -> bool:
    state = get_or_create_ingestion_state(connection, config.id)
    if state.last_reconciliation_at is None:
        return True
    return now - state.last_reconciliation_at >= timedelta(hours=DEFAULT_RECONCILIATION_INTERVAL_HOURS)


def run_post_discovery_job(
    connection,
    settings: Settings,
    config: SourceConfig,
    now: datetime | None = None,
) -> IngestionJobResult:
    current_time = now or utc_now()
    state = get_or_create_ingestion_state(connection, config.id)
    cutoff = None
    if state.last_successful_discovery_at is not None:
        cutoff = state.last_successful_discovery_at - timedelta(minutes=config.overlap_window_minutes)
    return _run_record_ingestion_job(
        connection=connection,
        settings=settings,
        config=config,
        job_type="post_discovery",
        current_time=current_time,
        cutoff=cutoff,
        checkpoint_kind="discovery",
    )


def run_reconciliation_job(
    connection,
    settings: Settings,
    config: SourceConfig,
    now: datetime | None = None,
) -> IngestionJobResult:
    current_time = now or utc_now()
    cutoff = current_time - timedelta(days=DEFAULT_RECONCILIATION_WINDOW_DAYS)
    return _run_record_ingestion_job(
        connection=connection,
        settings=settings,
        config=config,
        job_type="reconciliation",
        current_time=current_time,
        cutoff=cutoff,
        checkpoint_kind="reconciliation",
    )


def run_thread_comment_refresh_job(
    connection,
    settings: Settings,
    thread: TrackedThread,
    now: datetime | None = None,
) -> IngestionJobResult:
    current_time = now or utc_now()
    config = get_source_config(connection, thread.source_config_id)
    if config is None:
        return IngestionJobResult(
            run_id="missing-config",
            source_config_id=thread.source_config_id,
            job_type="comment_refresh",
            status="failed",
            error_message="Source config not found.",
        )
    run = start_ingestion_run(connection, config.id, "comment_refresh", current_time)
    try:
        adapter = _adapter_for_config(settings, config)
        comments = adapter.fetch_thread_comments(thread, DEFAULT_COMMENT_REFRESH_LIMIT)
        inserted, updated, skipped = upsert_comments(connection, config, thread, comments)
        mark_thread_comment_refresh(connection, thread, current_time, len(comments))
        finish_ingestion_run(
            connection,
            run.id,
            current_time,
            status="success",
            fetched_count=len(comments),
            inserted_count=inserted,
            updated_count=updated,
            skipped_count=skipped,
        )
        logger.info("comment_refresh success source_config=%s thread=%s fetched=%s", config.id, thread.internal_id, len(comments))
        return IngestionJobResult(
            run_id=run.id,
            source_config_id=config.id,
            job_type="comment_refresh",
            status="success",
            fetched_count=len(comments),
            inserted_count=inserted,
            updated_count=updated,
            skipped_count=skipped,
        )
    except Exception as exc:
        finish_ingestion_run(connection, run.id, current_time, status="failed", error_message=str(exc))
        logger.exception("comment_refresh failed source_config=%s thread=%s", config.id, thread.internal_id)
        return IngestionJobResult(
            run_id=run.id,
            source_config_id=config.id,
            job_type="comment_refresh",
            status="failed",
            error_message=str(exc),
        )


def refresh_source_config_now(db_path: str, source_config_id: str, settings: Settings | None = None) -> IngestionJobResult:
    settings = settings or get_settings()
    init_db(db_path)
    with connect(db_path) as connection:
        config = get_source_config(connection, source_config_id)
        if config is None:
            return IngestionJobResult(
                run_id="missing-config",
                source_config_id=source_config_id,
                job_type="post_discovery",
                status="failed",
                error_message="Source config not found.",
            )
        return run_post_discovery_job(connection, settings, config)


def refresh_tracked_thread_now(db_path: str, tracked_thread_id: str, settings: Settings | None = None) -> IngestionJobResult:
    settings = settings or get_settings()
    init_db(db_path)
    with connect(db_path) as connection:
        thread = get_tracked_thread(connection, tracked_thread_id)
        if thread is None:
            return IngestionJobResult(
                run_id="missing-thread",
                source_config_id="unknown",
                job_type="comment_refresh",
                status="failed",
                error_message="Tracked thread not found.",
            )
        return run_thread_comment_refresh_job(connection, settings, thread)


def run_reconciliation_now(db_path: str, source_config_id: str, settings: Settings | None = None) -> IngestionJobResult:
    settings = settings or get_settings()
    init_db(db_path)
    with connect(db_path) as connection:
        config = get_source_config(connection, source_config_id)
        if config is None:
            return IngestionJobResult(
                run_id="missing-config",
                source_config_id=source_config_id,
                job_type="reconciliation",
                status="failed",
                error_message="Source config not found.",
            )
        return run_reconciliation_job(connection, settings, config)


def _run_record_ingestion_job(
    connection,
    settings: Settings,
    config: SourceConfig,
    job_type: str,
    current_time: datetime,
    cutoff: datetime | None,
    checkpoint_kind: str,
) -> IngestionJobResult:
    run = start_ingestion_run(connection, config.id, job_type, current_time)
    if job_type == "post_discovery":
        mark_discovery_attempt(connection, config.id, current_time)

    try:
        adapter = _adapter_for_config(settings, config)
        records = _filter_records_by_cutoff(adapter.fetch_seed_posts(settings.ingestion_limit), cutoff)
        inserted = 0
        updated = 0
        skipped = 0
        last_seen_external_item_id = None
        for record in records:
            result, _thread = upsert_normalized_record(connection, config, record)
            if result == "inserted":
                inserted += 1
            else:
                updated += 1
            last_seen_external_item_id = record.source_id
            comment_inserted, comment_updated, comment_skipped = upsert_comments(connection, config, _thread, record.comments)
            inserted += comment_inserted
            updated += comment_updated
            skipped += comment_skipped

        if checkpoint_kind == "discovery":
            mark_discovery_success(connection, config.id, current_time, last_seen_external_item_id)
        if checkpoint_kind == "reconciliation":
            mark_reconciliation_success(connection, config.id, current_time)

        finish_ingestion_run(
            connection,
            run.id,
            current_time,
            status="success",
            fetched_count=len(records),
            inserted_count=inserted,
            updated_count=updated,
            skipped_count=skipped,
        )
        logger.info("%s success source_config=%s fetched=%s inserted=%s updated=%s", job_type, config.id, len(records), inserted, updated)
        return IngestionJobResult(
            run_id=run.id,
            source_config_id=config.id,
            job_type=job_type,
            status="success",
            fetched_count=len(records),
            inserted_count=inserted,
            updated_count=updated,
            skipped_count=skipped,
        )
    except Exception as exc:
        finish_ingestion_run(connection, run.id, current_time, status="failed", error_message=str(exc))
        logger.exception("%s failed source_config=%s", job_type, config.id)
        return IngestionJobResult(
            run_id=run.id,
            source_config_id=config.id,
            job_type=job_type,
            status="failed",
            error_message=str(exc),
        )


def _filter_records_by_cutoff(
    records: list[NormalizedDiscussionRecord],
    cutoff: datetime | None,
) -> list[NormalizedDiscussionRecord]:
    if cutoff is None:
        return records
    return [record for record in records if record.created_at is None or record.created_at >= cutoff]


def _adapter_for_config(settings: Settings, config: SourceConfig):
    adapter_class = ADAPTERS.get(config.source_type)
    if adapter_class is None:
        raise ValueError(f"Unsupported source type: {config.source_type}")
    if config.source_type == "mock":
        return MockAdapter()
    return adapter_class(_settings_for_config(settings, config))


def _settings_for_config(settings: Settings, config: SourceConfig) -> Settings:
    if config.source_type == "reddit":
        return replace(settings, reddit_subreddits=[item.strip() for item in config.query.split(",") if item.strip()])
    if config.source_type in {"hacker_news", "hn"}:
        return replace(settings, hn_listing=config.query)
    if config.source_type in {"stack_exchange", "stackexchange"}:
        return replace(settings, stack_exchange_tags=[item.strip() for item in config.query.replace(",", ";").split(";") if item.strip()])
    if config.source_type in {"github_issues", "github"} and "/" in config.query:
        owner, repo = config.query.split("/", 1)
        return replace(settings, github_owner=owner, github_repo=repo)
    return settings


def _query_from_settings(settings: Settings, source_type: str) -> str:
    if source_type == "reddit":
        return ",".join(settings.reddit_subreddits or [])
    if source_type in {"hacker_news", "hn"}:
        return settings.hn_listing
    if source_type in {"stack_exchange", "stackexchange"}:
        return ";".join(settings.stack_exchange_tags or [])
    if source_type in {"github_issues", "github"}:
        if settings.github_owner and settings.github_repo:
            return f"{settings.github_owner}/{settings.github_repo}"
        return ""
    return "local-seed"
