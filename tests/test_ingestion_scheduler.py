from __future__ import annotations

from datetime import datetime, timedelta, timezone

from auto_foundry.config import Settings
from auto_foundry.db.database import connect, init_db
from auto_foundry.db.ingestion_repository import (
    ensure_source_config,
    get_or_create_ingestion_state,
    is_thread_refresh_due,
    mark_discovery_success,
)
from auto_foundry.ingestion.scheduler import ADAPTERS, run_post_discovery_job, run_reconciliation_job, run_scheduler_tick
from auto_foundry.schemas import NormalizedDiscussionRecord, SourceHealthCheck, TrackedThread


def _settings(db_path: str, **overrides: object) -> Settings:
    values = {
        "openai_api_key": None,
        "llm_provider": "openai",
        "llm_model": "gpt-5-mini",
        "llm_model_dev": "gpt-5-mini",
        "llm_model_prod": "gpt-5",
        "llm_timeout_seconds": 1,
        "llm_max_output_tokens": 200,
        "db_path": db_path,
        "ingestion_source": "mock",
        "ingestion_sources": None,
        "ingestion_limit": 25,
    }
    values.update(overrides)
    return Settings(**values)


def test_post_discovery_checkpoint_updates_only_on_success(tmp_path, monkeypatch) -> None:
    db_path = str(tmp_path / "scheduler.sqlite3")
    settings = _settings(db_path)
    now = datetime(2026, 4, 8, tzinfo=timezone.utc)
    init_db(db_path)

    with connect(db_path) as connection:
        config = ensure_source_config(connection, "mock", "local-seed")
        result = run_post_discovery_job(connection, settings, config, now)
        state = get_or_create_ingestion_state(connection, config.id)

    assert result.status == "success"
    assert result.fetched_count > 0
    assert state.last_successful_discovery_at == now
    assert state.last_attempted_discovery_at == now

    class FailingAdapter:
        def __init__(self, settings: Settings) -> None:
            self.settings = settings

        def fetch_seed_posts(self, limit: int) -> list[NormalizedDiscussionRecord]:
            raise RuntimeError("boom")

    monkeypatch.setitem(ADAPTERS, "failing", FailingAdapter)
    later = now + timedelta(hours=4)
    with connect(db_path) as connection:
        config = ensure_source_config(connection, "failing", "query")
        result = run_post_discovery_job(connection, settings, config, later)
        state = get_or_create_ingestion_state(connection, config.id)

    assert result.status == "failed"
    assert state.last_successful_discovery_at is None
    assert state.last_attempted_discovery_at == later


def test_post_discovery_uses_overlap_window_and_upserts(tmp_path, monkeypatch) -> None:
    db_path = str(tmp_path / "overlap.sqlite3")
    settings = _settings(db_path, ingestion_limit=10)
    now = datetime(2026, 4, 8, 12, tzinfo=timezone.utc)
    init_db(db_path)

    class FakeAdapter:
        def __init__(self, settings: Settings) -> None:
            self.settings = settings

        def fetch_seed_posts(self, limit: int) -> list[NormalizedDiscussionRecord]:
            return [
                NormalizedDiscussionRecord(
                    source="fake",
                    source_id="old",
                    title="Old thread",
                    body="Too old for overlap.",
                    created_at=now - timedelta(hours=13),
                ),
                NormalizedDiscussionRecord(
                    source="fake",
                    source_id="recent",
                    title="Recent thread",
                    body="Inside overlap.",
                    created_at=now - timedelta(hours=1),
                ),
            ]

    monkeypatch.setitem(ADAPTERS, "fake", FakeAdapter)
    with connect(db_path) as connection:
        config = ensure_source_config(connection, "fake", "query", overlap_window_minutes=720)
        mark_discovery_success(connection, config.id, now, None)
        result = run_post_discovery_job(connection, settings, config, now)
        discussions_count = connection.execute("SELECT COUNT(*) FROM discussions").fetchone()[0]
        threads_count = connection.execute("SELECT COUNT(*) FROM tracked_threads").fetchone()[0]
        rerun = run_post_discovery_job(connection, settings, config, now)
        rerun_discussions_count = connection.execute("SELECT COUNT(*) FROM discussions").fetchone()[0]

    assert result.fetched_count == 1
    assert discussions_count == 1
    assert threads_count == 1
    assert rerun.status == "success"
    assert rerun_discussions_count == 1


def test_thread_refresh_decay_policy() -> None:
    now = datetime(2026, 4, 8, 12, tzinfo=timezone.utc)
    base = {
        "internal_id": "thread-1",
        "source_config_id": "source-1",
        "source_type": "mock",
        "external_thread_id": "external-1",
        "first_seen_at": now,
        "last_seen_at": now,
    }

    hot = TrackedThread(
        **base,
        source_created_at=now - timedelta(hours=2),
        last_comment_refresh_at=now - timedelta(minutes=61),
    )
    warm = TrackedThread(
        **base,
        source_created_at=now - timedelta(days=2),
        last_comment_refresh_at=now - timedelta(hours=5),
    )
    archived = TrackedThread(
        **base,
        source_created_at=now - timedelta(days=8),
        last_comment_refresh_at=now - timedelta(days=2),
    )

    assert is_thread_refresh_due(hot, now) is True
    assert is_thread_refresh_due(warm, now) is False
    assert is_thread_refresh_due(archived, now) is False


def test_scheduler_tick_creates_config_and_runs_jobs(tmp_path) -> None:
    db_path = str(tmp_path / "tick.sqlite3")
    settings = _settings(db_path, ingestion_source="mock")
    now = datetime(2026, 4, 8, 12, tzinfo=timezone.utc)

    results = run_scheduler_tick(db_path, settings=settings, now=now)

    assert {result.job_type for result in results} >= {"post_discovery", "reconciliation"}
    with connect(db_path) as connection:
        assert connection.execute("SELECT COUNT(*) FROM source_configs").fetchone()[0] == 1
        assert connection.execute("SELECT COUNT(*) FROM ingestion_runs").fetchone()[0] >= 2
        assert connection.execute("SELECT COUNT(*) FROM tracked_threads").fetchone()[0] > 0


def test_scheduler_tick_registers_multiple_source_configs(tmp_path) -> None:
    db_path = str(tmp_path / "multi.sqlite3")
    settings = _settings(db_path, ingestion_sources=["mock", "hacker_news"], ingestion_source="mock")
    now = datetime(2026, 4, 8, 12, tzinfo=timezone.utc)

    run_scheduler_tick(db_path, settings=settings, now=now)

    with connect(db_path) as connection:
        rows = connection.execute("SELECT source_type, query FROM source_configs ORDER BY source_type").fetchall()

    assert [tuple(row) for row in rows] == [("hacker_news", "askstories"), ("mock", "local-seed")]


def test_reconciliation_updates_only_reconciliation_checkpoint(tmp_path) -> None:
    db_path = str(tmp_path / "reconcile.sqlite3")
    settings = _settings(db_path)
    now = datetime(2026, 4, 8, 12, tzinfo=timezone.utc)
    init_db(db_path)

    with connect(db_path) as connection:
        config = ensure_source_config(connection, "mock", "local-seed")
        result = run_reconciliation_job(connection, settings, config, now)
        state = get_or_create_ingestion_state(connection, config.id)

    assert result.status == "success"
    assert state.last_reconciliation_at == now
    assert state.last_successful_discovery_at is None
