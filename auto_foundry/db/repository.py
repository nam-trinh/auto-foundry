from __future__ import annotations

import json
import sqlite3

from auto_foundry.schemas import Discussion, Opportunity, PainSignal, ScoreBreakdown, StartupIdea


def upsert_discussions(connection: sqlite3.Connection, discussions: list[Discussion]) -> None:
    connection.executemany(
        """
        INSERT INTO discussions (id, source, author, title, body)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            source = excluded.source,
            author = excluded.author,
            title = excluded.title,
            body = excluded.body
        """,
        [(item.id, item.source, item.author, item.title, item.body) for item in discussions],
    )


def clear_derived_records(connection: sqlite3.Connection) -> None:
    connection.execute("DELETE FROM startup_ideas")
    connection.execute("DELETE FROM opportunities")
    connection.execute("DELETE FROM pain_signals")


def insert_pain_signals(connection: sqlite3.Connection, signals: list[PainSignal]) -> None:
    connection.executemany(
        """
        INSERT INTO pain_signals (id, discussion_id, summary, quote, severity, theme_hint, source)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (item.id, item.discussion_id, item.summary, item.quote, item.severity, item.theme_hint, item.source)
            for item in signals
        ],
    )


def insert_opportunities(connection: sqlite3.Connection, opportunities: list[Opportunity]) -> None:
    connection.executemany(
        """
        INSERT INTO opportunities (
            id, theme, title, summary, evidence_count, source_pain_ids,
            frequency, severity, willingness_to_pay, urgency, final_score, formula
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                item.id,
                item.theme,
                item.title,
                item.summary,
                item.evidence_count,
                json.dumps(item.source_pain_ids),
                item.score.frequency,
                item.score.severity,
                item.score.willingness_to_pay,
                item.score.urgency,
                item.score.final_score,
                item.score.formula,
            )
            for item in opportunities
        ],
    )


def insert_startup_ideas(connection: sqlite3.Connection, ideas: list[StartupIdea]) -> None:
    connection.executemany(
        """
        INSERT INTO startup_ideas (
            id, opportunity_id, name, target_customer, problem, solution, mvp, why_now, key_risk, source
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                item.id,
                item.opportunity_id,
                item.name,
                item.target_customer,
                item.problem,
                item.solution,
                item.mvp,
                item.why_now,
                item.key_risk,
                item.source,
            )
            for item in ideas
        ],
    )


def list_discussions(connection: sqlite3.Connection) -> list[Discussion]:
    rows = connection.execute("SELECT * FROM discussions ORDER BY id").fetchall()
    return [Discussion(**dict(row)) for row in rows]


def list_pain_signals(connection: sqlite3.Connection) -> list[PainSignal]:
    rows = connection.execute("SELECT * FROM pain_signals ORDER BY id").fetchall()
    return [PainSignal(**dict(row)) for row in rows]


def list_opportunities(connection: sqlite3.Connection) -> list[Opportunity]:
    rows = connection.execute("SELECT * FROM opportunities ORDER BY final_score DESC, id").fetchall()
    opportunities: list[Opportunity] = []
    for row in rows:
        data = dict(row)
        opportunities.append(
            Opportunity(
                id=data["id"],
                theme=data["theme"],
                title=data["title"],
                summary=data["summary"],
                evidence_count=data["evidence_count"],
                source_pain_ids=json.loads(data["source_pain_ids"]),
                score=ScoreBreakdown(
                    frequency=data["frequency"],
                    severity=data["severity"],
                    willingness_to_pay=data["willingness_to_pay"],
                    urgency=data["urgency"],
                    final_score=data["final_score"],
                    formula=data["formula"],
                ),
            )
        )
    return opportunities


def list_startup_ideas(connection: sqlite3.Connection) -> list[StartupIdea]:
    rows = connection.execute("SELECT * FROM startup_ideas ORDER BY id").fetchall()
    return [StartupIdea(**dict(row)) for row in rows]
