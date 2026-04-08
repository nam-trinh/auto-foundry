from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

from auto_foundry.config import Settings
from auto_foundry.ingestion.github_issues import GitHubIssuesAdapter
from auto_foundry.ingestion.hacker_news import HackerNewsAdapter
from auto_foundry.ingestion.mock_adapter import MockAdapter
from auto_foundry.ingestion.reddit import RedditAdapter
from auto_foundry.ingestion.service import EXTERNAL_ADAPTERS, fetch_normalized_records
from auto_foundry.ingestion.stack_exchange import StackExchangeAdapter
from auto_foundry.schemas import NormalizedComment, NormalizedDiscussionRecord, SourceHealthCheck


def _settings(db_path: str = "test.sqlite3", **overrides: object) -> Settings:
    values = {
        "openai_api_key": None,
        "llm_provider": "openai",
        "llm_model": "gpt-5-mini",
        "llm_model_dev": "gpt-5-mini",
        "llm_model_prod": "gpt-5",
        "llm_timeout_seconds": 1,
        "llm_max_output_tokens": 200,
        "db_path": db_path,
    }
    values.update(overrides)
    return Settings(**values)


def test_mock_adapter_returns_normalized_records_and_discussions() -> None:
    records = MockAdapter().fetch_seed_posts(limit=2)
    discussion = records[0].to_discussion()

    assert len(records) == 2
    assert records[0].source_id
    assert discussion.id == records[0].stable_discussion_id
    assert discussion.title == records[0].title
    assert discussion.body


def test_normalized_comment_preserves_core_fields() -> None:
    created_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
    comment = NormalizedComment(
        comment_id="comment-1",
        author="alice",
        body="This is painful.",
        created_at=created_at,
        score=12,
        parent_id="parent-1",
    )

    assert comment.comment_id == "comment-1"
    assert comment.author == "alice"
    assert comment.body == "This is painful."
    assert comment.created_at == created_at
    assert comment.score == 12
    assert comment.parent_id == "parent-1"


def test_ingestion_service_deduplicates_external_records(monkeypatch) -> None:
    duplicate = MockAdapter().fetch_seed_posts(limit=1)[0]

    class DuplicateAdapter:
        source_name = "duplicate"

        def __init__(self, settings: Settings) -> None:
            self.settings = settings

        def healthcheck(self) -> SourceHealthCheck:
            return SourceHealthCheck(source=self.source_name, ok=True, message="ok")

        def fetch_seed_posts(self, limit: int) -> list[NormalizedDiscussionRecord]:
            return [duplicate]

    monkeypatch.setitem(EXTERNAL_ADAPTERS, "duplicate", DuplicateAdapter)
    settings = _settings(ingestion_source="duplicate", ingestion_limit=5)

    records = fetch_normalized_records(settings)

    assert [item.stable_discussion_id for item in records].count(duplicate.stable_discussion_id) == 1


def test_reddit_normalization_from_praw_like_objects() -> None:
    settings = _settings(reddit_include_comments=True, reddit_comment_limit=2)
    adapter = RedditAdapter(settings)
    comment = SimpleNamespace(
        id="c1",
        author="commenter",
        body="I have this problem too.",
        created_utc=1_700_000_001,
        score=4,
        parent_id="t3_post",
    )
    comments = SimpleNamespace(replace_more=lambda limit: None, list=lambda: [comment])
    submission = SimpleNamespace(
        id="abc123",
        title="Manual reporting is painful",
        selftext="We waste hours every week.",
        subreddit="startups",
        permalink="/r/startups/comments/abc123/manual_reporting/",
        author="poster",
        created_utc=1_700_000_000,
        score=42,
        num_comments=1,
        upvote_ratio=0.95,
        comments=comments,
    )

    record = adapter.normalize_record(submission)

    assert record is not None
    assert record.source == "reddit"
    assert record.source_id == "abc123"
    assert record.community == "startups"
    assert record.comments[0].comment_id == "c1"
    assert record.engagement == 43


def test_hacker_news_normalization_from_item_dict() -> None:
    settings = _settings()
    adapter = HackerNewsAdapter(settings)

    record = adapter.normalize_record(
        {
            "id": 123,
            "type": "story",
            "title": "Ask HN: What workflows are still manual?",
            "text": "We still copy data by hand.",
            "by": "hn_user",
            "time": 1_700_000_000,
            "score": 15,
            "kids": [1, 2],
        }
    )

    assert record is not None
    assert record.source == "hacker_news"
    assert record.source_id == "123"
    assert record.author == "hn_user"
    assert record.engagement == 17


def test_stack_exchange_normalization_from_question_dict() -> None:
    settings = _settings(stack_exchange_site="stackoverflow")
    adapter = StackExchangeAdapter(settings)

    record = adapter.normalize_record(
        {
            "question_id": 456,
            "link": "https://stackoverflow.com/questions/456/example",
            "title": "How do I automate this?",
            "body": "<p>Manual process question.</p>",
            "owner": {"display_name": "stack_user"},
            "creation_date": 1_700_000_000,
            "score": 3,
            "answer_count": 2,
            "view_count": 100,
            "tags": ["python", "automation"],
            "is_answered": True,
        }
    )

    assert record is not None
    assert record.source == "stack_exchange"
    assert record.source_id == "456"
    assert record.tags == ["python", "automation"]
    assert record.engagement == 105


def test_github_issues_filters_prs_and_normalizes_issues() -> None:
    settings = _settings(github_owner="octo", github_repo="repo")
    adapter = GitHubIssuesAdapter(settings)

    assert adapter.normalize_record({"id": 1, "title": "PR", "pull_request": {}}) is None

    record = adapter.normalize_record(
        {
            "id": 789,
            "number": 12,
            "html_url": "https://github.com/octo/repo/issues/12",
            "title": "Issue templates are not enough",
            "body": "Users repeat the same setup mistake.",
            "user": {"login": "gh_user"},
            "created_at": "2026-01-01T00:00:00Z",
            "comments": 3,
            "labels": [{"name": "bug"}, {"name": "support"}],
            "reactions": {"total_count": 5},
            "state": "open",
        }
    )

    assert record is not None
    assert record.source == "github_issues"
    assert record.source_id == "12"
    assert record.tags == ["bug", "support"]
    assert record.engagement == 8


def test_external_adapter_failure_falls_back_to_mock_records() -> None:
    settings = _settings(
        ingestion_source="github_issues",
        ingestion_limit=5,
        github_owner=None,
        github_repo=None,
    )

    records = fetch_normalized_records(settings)

    assert len(records) == 5
    assert all(record.raw_metadata.get("mock") is True for record in records)
