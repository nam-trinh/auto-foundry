from __future__ import annotations

import sqlite3
from pathlib import Path


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS discussions (
    id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    author TEXT NOT NULL,
    title TEXT NOT NULL,
    body TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS pain_signals (
    id TEXT PRIMARY KEY,
    discussion_id TEXT NOT NULL,
    summary TEXT NOT NULL,
    quote TEXT NOT NULL,
    severity INTEGER NOT NULL,
    theme_hint TEXT NOT NULL,
    source TEXT NOT NULL,
    FOREIGN KEY (discussion_id) REFERENCES discussions(id)
);

CREATE TABLE IF NOT EXISTS opportunities (
    id TEXT PRIMARY KEY,
    theme TEXT NOT NULL,
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    evidence_count INTEGER NOT NULL,
    source_pain_ids TEXT NOT NULL,
    frequency REAL NOT NULL,
    severity REAL NOT NULL,
    willingness_to_pay REAL NOT NULL,
    urgency REAL NOT NULL,
    final_score REAL NOT NULL,
    formula TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS startup_ideas (
    id TEXT PRIMARY KEY,
    opportunity_id TEXT NOT NULL,
    name TEXT NOT NULL,
    target_customer TEXT NOT NULL,
    problem TEXT NOT NULL,
    solution TEXT NOT NULL,
    mvp TEXT NOT NULL,
    why_now TEXT NOT NULL,
    key_risk TEXT NOT NULL,
    source TEXT NOT NULL,
    FOREIGN KEY (opportunity_id) REFERENCES opportunities(id)
);

CREATE TABLE IF NOT EXISTS source_configs (
    id TEXT PRIMARY KEY,
    source_type TEXT NOT NULL,
    query TEXT NOT NULL,
    enabled INTEGER NOT NULL DEFAULT 1,
    polling_interval_minutes INTEGER NOT NULL DEFAULT 180,
    overlap_window_minutes INTEGER NOT NULL DEFAULT 720,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ingestion_states (
    source_config_id TEXT PRIMARY KEY,
    last_successful_discovery_at TEXT,
    last_attempted_discovery_at TEXT,
    last_reconciliation_at TEXT,
    last_seen_external_item_id TEXT,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (source_config_id) REFERENCES source_configs(id)
);

CREATE TABLE IF NOT EXISTS ingestion_runs (
    id TEXT PRIMARY KEY,
    source_config_id TEXT NOT NULL,
    job_type TEXT NOT NULL,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    status TEXT NOT NULL,
    fetched_count INTEGER NOT NULL DEFAULT 0,
    inserted_count INTEGER NOT NULL DEFAULT 0,
    updated_count INTEGER NOT NULL DEFAULT 0,
    skipped_count INTEGER NOT NULL DEFAULT 0,
    error_message TEXT,
    FOREIGN KEY (source_config_id) REFERENCES source_configs(id)
);

CREATE TABLE IF NOT EXISTS tracked_threads (
    internal_id TEXT PRIMARY KEY,
    source_config_id TEXT NOT NULL,
    source_type TEXT NOT NULL,
    external_thread_id TEXT NOT NULL,
    external_url TEXT,
    source_created_at TEXT,
    first_seen_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL,
    last_comment_refresh_at TEXT,
    last_observed_comment_count INTEGER NOT NULL DEFAULT 0,
    activity_status TEXT NOT NULL DEFAULT 'hot',
    active_polling_enabled INTEGER NOT NULL DEFAULT 1,
    raw_metadata TEXT NOT NULL DEFAULT '{}',
    UNIQUE(source_type, external_thread_id),
    FOREIGN KEY (source_config_id) REFERENCES source_configs(id)
);

CREATE TABLE IF NOT EXISTS ingested_comments (
    id TEXT PRIMARY KEY,
    source_type TEXT NOT NULL,
    external_comment_id TEXT NOT NULL,
    external_thread_id TEXT NOT NULL,
    source_config_id TEXT NOT NULL,
    author TEXT,
    body TEXT NOT NULL,
    source_created_at TEXT,
    score INTEGER,
    parent_id TEXT,
    raw_metadata TEXT NOT NULL DEFAULT '{}',
    UNIQUE(source_type, external_comment_id),
    FOREIGN KEY (source_config_id) REFERENCES source_configs(id)
);

CREATE TABLE IF NOT EXISTS analysis_dirty_markers (
    id TEXT PRIMARY KEY,
    source_type TEXT NOT NULL,
    external_id TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    reason TEXT NOT NULL,
    created_at TEXT NOT NULL,
    processed_at TEXT,
    UNIQUE(source_type, external_id, entity_type)
);
"""


def connect(db_path: str) -> sqlite3.Connection:
    path = Path(db_path)
    if path.parent != Path("."):
        path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    return connection


def init_db(db_path: str) -> None:
    with connect(db_path) as connection:
        connection.executescript(SCHEMA_SQL)
