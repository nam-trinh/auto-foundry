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
