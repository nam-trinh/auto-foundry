from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone

from auto_foundry.schemas import (
    IngestionRun,
    IngestionState,
    NormalizedComment,
    NormalizedDiscussionRecord,
    SourceConfig,
    TrackedThread,
)


def utc_now() -> datetime:
    return datetime.now(tz=timezone.utc)


def iso(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def parse_dt(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None


def make_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


def ensure_source_config(
    connection: sqlite3.Connection,
    source_type: str,
    query: str,
    polling_interval_minutes: int = 180,
    overlap_window_minutes: int = 720,
    enabled: bool = True,
) -> SourceConfig:
    existing = connection.execute(
        "SELECT * FROM source_configs WHERE source_type = ? AND query = ?",
        (source_type, query),
    ).fetchone()
    now = utc_now()
    if existing:
        return _source_config_from_row(existing)

    config = SourceConfig(
        id=make_id("src"),
        source_type=source_type,
        query=query,
        enabled=enabled,
        polling_interval_minutes=polling_interval_minutes,
        overlap_window_minutes=overlap_window_minutes,
        created_at=now,
        updated_at=now,
    )
    upsert_source_config(connection, config)
    return config


def upsert_source_config(connection: sqlite3.Connection, config: SourceConfig) -> None:
    connection.execute(
        """
        INSERT INTO source_configs (
            id, source_type, query, enabled, polling_interval_minutes,
            overlap_window_minutes, created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            source_type = excluded.source_type,
            query = excluded.query,
            enabled = excluded.enabled,
            polling_interval_minutes = excluded.polling_interval_minutes,
            overlap_window_minutes = excluded.overlap_window_minutes,
            updated_at = excluded.updated_at
        """,
        (
            config.id,
            config.source_type,
            config.query,
            int(config.enabled),
            config.polling_interval_minutes,
            config.overlap_window_minutes,
            iso(config.created_at),
            iso(config.updated_at),
        ),
    )
    get_or_create_ingestion_state(connection, config.id)


def list_enabled_source_configs(connection: sqlite3.Connection) -> list[SourceConfig]:
    rows = connection.execute("SELECT * FROM source_configs WHERE enabled = 1 ORDER BY created_at").fetchall()
    return [_source_config_from_row(row) for row in rows]


def get_source_config(connection: sqlite3.Connection, source_config_id: str) -> SourceConfig | None:
    row = connection.execute("SELECT * FROM source_configs WHERE id = ?", (source_config_id,)).fetchone()
    return _source_config_from_row(row) if row else None


def get_or_create_ingestion_state(connection: sqlite3.Connection, source_config_id: str) -> IngestionState:
    row = connection.execute("SELECT * FROM ingestion_states WHERE source_config_id = ?", (source_config_id,)).fetchone()
    if row:
        return _ingestion_state_from_row(row)
    state = IngestionState(source_config_id=source_config_id, updated_at=utc_now())
    connection.execute(
        """
        INSERT INTO ingestion_states (
            source_config_id, last_successful_discovery_at, last_attempted_discovery_at,
            last_reconciliation_at, last_seen_external_item_id, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            state.source_config_id,
            iso(state.last_successful_discovery_at),
            iso(state.last_attempted_discovery_at),
            iso(state.last_reconciliation_at),
            state.last_seen_external_item_id,
            iso(state.updated_at),
        ),
    )
    return state


def mark_discovery_attempt(connection: sqlite3.Connection, source_config_id: str, attempted_at: datetime) -> None:
    get_or_create_ingestion_state(connection, source_config_id)
    connection.execute(
        """
        UPDATE ingestion_states
        SET last_attempted_discovery_at = ?, updated_at = ?
        WHERE source_config_id = ?
        """,
        (iso(attempted_at), iso(attempted_at), source_config_id),
    )


def mark_discovery_success(
    connection: sqlite3.Connection,
    source_config_id: str,
    successful_at: datetime,
    last_seen_external_item_id: str | None,
) -> None:
    get_or_create_ingestion_state(connection, source_config_id)
    connection.execute(
        """
        UPDATE ingestion_states
        SET last_successful_discovery_at = ?,
            last_seen_external_item_id = COALESCE(?, last_seen_external_item_id),
            updated_at = ?
        WHERE source_config_id = ?
        """,
        (iso(successful_at), last_seen_external_item_id, iso(successful_at), source_config_id),
    )


def mark_reconciliation_success(connection: sqlite3.Connection, source_config_id: str, successful_at: datetime) -> None:
    get_or_create_ingestion_state(connection, source_config_id)
    connection.execute(
        """
        UPDATE ingestion_states
        SET last_reconciliation_at = ?, updated_at = ?
        WHERE source_config_id = ?
        """,
        (iso(successful_at), iso(successful_at), source_config_id),
    )


def start_ingestion_run(
    connection: sqlite3.Connection,
    source_config_id: str,
    job_type: str,
    started_at: datetime,
) -> IngestionRun:
    run = IngestionRun(
        id=make_id("run"),
        source_config_id=source_config_id,
        job_type=job_type,
        started_at=started_at,
        status="running",
    )
    connection.execute(
        """
        INSERT INTO ingestion_runs (
            id, source_config_id, job_type, started_at, finished_at, status,
            fetched_count, inserted_count, updated_count, skipped_count, error_message
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run.id,
            run.source_config_id,
            run.job_type,
            iso(run.started_at),
            iso(run.finished_at),
            run.status,
            run.fetched_count,
            run.inserted_count,
            run.updated_count,
            run.skipped_count,
            run.error_message,
        ),
    )
    return run


def finish_ingestion_run(
    connection: sqlite3.Connection,
    run_id: str,
    finished_at: datetime,
    status: str,
    fetched_count: int = 0,
    inserted_count: int = 0,
    updated_count: int = 0,
    skipped_count: int = 0,
    error_message: str | None = None,
) -> None:
    connection.execute(
        """
        UPDATE ingestion_runs
        SET finished_at = ?, status = ?, fetched_count = ?, inserted_count = ?,
            updated_count = ?, skipped_count = ?, error_message = ?
        WHERE id = ?
        """,
        (
            iso(finished_at),
            status,
            fetched_count,
            inserted_count,
            updated_count,
            skipped_count,
            error_message,
            run_id,
        ),
    )


def upsert_normalized_record(
    connection: sqlite3.Connection,
    source_config: SourceConfig,
    record: NormalizedDiscussionRecord,
) -> tuple[str, TrackedThread]:
    discussion_id = record.stable_discussion_id
    existed = connection.execute("SELECT 1 FROM discussions WHERE id = ?", (discussion_id,)).fetchone() is not None
    discussion = record.to_discussion()
    connection.execute(
        """
        INSERT INTO discussions (id, source, author, title, body)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            source = excluded.source,
            author = excluded.author,
            title = excluded.title,
            body = excluded.body
        """,
        (discussion.id, discussion.source, discussion.author, discussion.title, discussion.body),
    )
    thread = upsert_tracked_thread(connection, source_config, record)
    mark_analysis_dirty(connection, record.source, record.source_id, "thread", "ingestion_upsert")
    return ("updated" if existed else "inserted", thread)


def upsert_tracked_thread(
    connection: sqlite3.Connection,
    source_config: SourceConfig,
    record: NormalizedDiscussionRecord,
) -> TrackedThread:
    now = utc_now()
    existing = connection.execute(
        "SELECT * FROM tracked_threads WHERE source_type = ? AND external_thread_id = ?",
        (record.source, record.source_id),
    ).fetchone()
    comment_count = len(record.comments)
    raw_metadata = json.dumps(record.raw_metadata)
    if existing:
        internal_id = existing["internal_id"]
        first_seen_at = existing["first_seen_at"]
        connection.execute(
            """
            UPDATE tracked_threads
            SET source_config_id = ?, external_url = ?, source_created_at = ?,
                last_seen_at = ?, last_observed_comment_count = ?,
                activity_status = ?, raw_metadata = ?
            WHERE internal_id = ?
            """,
            (
                source_config.id,
                record.url,
                iso(record.created_at),
                iso(now),
                comment_count,
                determine_activity_status(record.created_at, now),
                raw_metadata,
                internal_id,
            ),
        )
    else:
        internal_id = make_id("thread")
        first_seen_at = iso(now)
        connection.execute(
            """
            INSERT INTO tracked_threads (
                internal_id, source_config_id, source_type, external_thread_id,
                external_url, source_created_at, first_seen_at, last_seen_at,
                last_comment_refresh_at, last_observed_comment_count, activity_status,
                active_polling_enabled, raw_metadata
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                internal_id,
                source_config.id,
                record.source,
                record.source_id,
                record.url,
                iso(record.created_at),
                first_seen_at,
                iso(now),
                None,
                comment_count,
                determine_activity_status(record.created_at, now),
                1,
                raw_metadata,
            ),
        )
    refreshed = connection.execute("SELECT * FROM tracked_threads WHERE internal_id = ?", (internal_id,)).fetchone()
    return _tracked_thread_from_row(refreshed)


def upsert_comments(
    connection: sqlite3.Connection,
    source_config: SourceConfig,
    thread: TrackedThread,
    comments: list[NormalizedComment],
) -> tuple[int, int, int]:
    inserted = 0
    updated = 0
    skipped = 0
    for comment in comments:
        if not comment.comment_id or not comment.body:
            skipped += 1
            continue
        existed = connection.execute(
            "SELECT 1 FROM ingested_comments WHERE source_type = ? AND external_comment_id = ?",
            (thread.source_type, comment.comment_id),
        ).fetchone() is not None
        connection.execute(
            """
            INSERT INTO ingested_comments (
                id, source_type, external_comment_id, external_thread_id, source_config_id,
                author, body, source_created_at, score, parent_id, raw_metadata
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(source_type, external_comment_id) DO UPDATE SET
                body = excluded.body,
                score = excluded.score,
                parent_id = excluded.parent_id,
                raw_metadata = excluded.raw_metadata
            """,
            (
                f"{thread.source_type}:{comment.comment_id}",
                thread.source_type,
                comment.comment_id,
                thread.external_thread_id,
                source_config.id,
                comment.author,
                comment.body,
                iso(comment.created_at),
                comment.score,
                comment.parent_id,
                "{}",
            ),
        )
        mark_analysis_dirty(connection, thread.source_type, comment.comment_id, "comment", "comment_refresh")
        if existed:
            updated += 1
        else:
            inserted += 1
    return inserted, updated, skipped


def list_refresh_due_threads(connection: sqlite3.Connection, now: datetime) -> list[TrackedThread]:
    rows = connection.execute(
        "SELECT * FROM tracked_threads WHERE active_polling_enabled = 1 ORDER BY last_seen_at DESC"
    ).fetchall()
    return [thread for thread in (_tracked_thread_from_row(row) for row in rows) if is_thread_refresh_due(thread, now)]


def get_tracked_thread(connection: sqlite3.Connection, internal_id: str) -> TrackedThread | None:
    row = connection.execute("SELECT * FROM tracked_threads WHERE internal_id = ?", (internal_id,)).fetchone()
    return _tracked_thread_from_row(row) if row else None


def mark_thread_comment_refresh(
    connection: sqlite3.Connection,
    thread: TrackedThread,
    refreshed_at: datetime,
    observed_comment_count: int,
) -> None:
    status = determine_activity_status(thread.source_created_at, refreshed_at)
    active = 0 if status == "archived" else int(thread.active_polling_enabled)
    connection.execute(
        """
        UPDATE tracked_threads
        SET last_comment_refresh_at = ?, last_observed_comment_count = ?,
            activity_status = ?, active_polling_enabled = ?
        WHERE internal_id = ?
        """,
        (iso(refreshed_at), observed_comment_count, status, active, thread.internal_id),
    )


def mark_analysis_dirty(
    connection: sqlite3.Connection,
    source_type: str,
    external_id: str,
    entity_type: str,
    reason: str,
) -> None:
    connection.execute(
        """
        INSERT INTO analysis_dirty_markers (id, source_type, external_id, entity_type, reason, created_at, processed_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(source_type, external_id, entity_type) DO UPDATE SET
            reason = excluded.reason,
            created_at = excluded.created_at,
            processed_at = NULL
        """,
        (
            make_id("dirty"),
            source_type,
            external_id,
            entity_type,
            reason,
            iso(utc_now()),
            None,
        ),
    )


def determine_activity_status(source_created_at: datetime | None, now: datetime) -> str:
    if source_created_at is None:
        return "warm"
    age_hours = (now - source_created_at).total_seconds() / 3600
    if age_hours <= 24:
        return "hot"
    if age_hours <= 72:
        return "warm"
    if age_hours <= 168:
        return "cold"
    return "archived"


def is_thread_refresh_due(thread: TrackedThread, now: datetime) -> bool:
    status = determine_activity_status(thread.source_created_at, now)
    if status == "archived":
        return False
    if thread.last_comment_refresh_at is None:
        return True
    age_minutes = (now - thread.last_comment_refresh_at).total_seconds() / 60
    if status == "hot":
        return age_minutes >= 60
    if status == "warm":
        return age_minutes >= 360
    return age_minutes >= 720


def _source_config_from_row(row: sqlite3.Row) -> SourceConfig:
    return SourceConfig(
        id=row["id"],
        source_type=row["source_type"],
        query=row["query"],
        enabled=bool(row["enabled"]),
        polling_interval_minutes=row["polling_interval_minutes"],
        overlap_window_minutes=row["overlap_window_minutes"],
        created_at=parse_dt(row["created_at"]) or utc_now(),
        updated_at=parse_dt(row["updated_at"]) or utc_now(),
    )


def _ingestion_state_from_row(row: sqlite3.Row) -> IngestionState:
    return IngestionState(
        source_config_id=row["source_config_id"],
        last_successful_discovery_at=parse_dt(row["last_successful_discovery_at"]),
        last_attempted_discovery_at=parse_dt(row["last_attempted_discovery_at"]),
        last_reconciliation_at=parse_dt(row["last_reconciliation_at"]),
        last_seen_external_item_id=row["last_seen_external_item_id"],
        updated_at=parse_dt(row["updated_at"]) or utc_now(),
    )


def _tracked_thread_from_row(row: sqlite3.Row) -> TrackedThread:
    return TrackedThread(
        internal_id=row["internal_id"],
        source_config_id=row["source_config_id"],
        source_type=row["source_type"],
        external_thread_id=row["external_thread_id"],
        external_url=row["external_url"],
        source_created_at=parse_dt(row["source_created_at"]),
        first_seen_at=parse_dt(row["first_seen_at"]) or utc_now(),
        last_seen_at=parse_dt(row["last_seen_at"]) or utc_now(),
        last_comment_refresh_at=parse_dt(row["last_comment_refresh_at"]),
        last_observed_comment_count=row["last_observed_comment_count"],
        activity_status=row["activity_status"],
        active_polling_enabled=bool(row["active_polling_enabled"]),
        raw_metadata=json.loads(row["raw_metadata"] or "{}"),
    )
