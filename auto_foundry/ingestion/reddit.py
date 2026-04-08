from __future__ import annotations

from typing import Any

import praw

from auto_foundry.config import Settings
from auto_foundry.ingestion.base import configured_subreddits
from auto_foundry.schemas import NormalizedComment, NormalizedDiscussionRecord, SourceHealthCheck, TrackedThread, datetime_from_unix


class RedditAdapter:
    source_name = "reddit"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def healthcheck(self) -> SourceHealthCheck:
        if not self.settings.reddit_client_id or not self.settings.reddit_client_secret:
            return SourceHealthCheck(
                source=self.source_name,
                ok=False,
                message="REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET are required for Reddit ingestion.",
            )
        return SourceHealthCheck(source=self.source_name, ok=True, message="Reddit config is present.")

    def fetch_seed_posts(self, limit: int) -> list[NormalizedDiscussionRecord]:
        health = self.healthcheck()
        if not health.ok:
            return []

        reddit = self._client()
        records: list[NormalizedDiscussionRecord] = []
        subreddits = configured_subreddits(self.settings)
        per_subreddit_limit = max(1, limit // max(len(subreddits), 1))

        for subreddit_name in subreddits:
            subreddit = reddit.subreddit(subreddit_name)
            submissions = self._listing(subreddit, per_subreddit_limit)
            for submission in submissions:
                normalized = self.normalize_record(submission)
                if normalized is not None:
                    records.append(normalized)
                if len(records) >= limit:
                    return records
        return records

    def fetch_thread_comments(self, thread: TrackedThread, limit: int) -> list[NormalizedComment]:
        health = self.healthcheck()
        if not health.ok:
            return []
        submission = self._client().submission(id=thread.external_thread_id)
        return self.fetch_comments(submission, limit)

    def fetch_comments(self, record: Any, limit: int) -> list[NormalizedComment]:
        record.comments.replace_more(limit=0)
        comments: list[NormalizedComment] = []
        for comment in record.comments.list()[:limit]:
            body = getattr(comment, "body", "") or ""
            if not body:
                continue
            comments.append(
                NormalizedComment(
                    comment_id=str(getattr(comment, "id", "")),
                    author=str(getattr(comment, "author", None) or "unknown"),
                    body=body,
                    created_at=datetime_from_unix(getattr(comment, "created_utc", None)),
                    score=getattr(comment, "score", None),
                    parent_id=getattr(comment, "parent_id", None),
                )
            )
        return comments

    def normalize_record(self, record: Any) -> NormalizedDiscussionRecord | None:
        title = getattr(record, "title", "") or ""
        body = getattr(record, "selftext", "") or ""
        if not title and not body:
            return None

        subreddit = getattr(record, "subreddit", None)
        permalink = getattr(record, "permalink", None)
        url = f"https://www.reddit.com{permalink}" if permalink else getattr(record, "url", None)
        comments = self.fetch_comments(record, self.settings.reddit_comment_limit) if self.settings.reddit_include_comments else []
        return NormalizedDiscussionRecord(
            source=self.source_name,
            source_id=str(getattr(record, "id", "")),
            url=url,
            community=str(subreddit) if subreddit is not None else None,
            title=title,
            body=body,
            comments=comments,
            created_at=datetime_from_unix(getattr(record, "created_utc", None)),
            author=str(getattr(record, "author", None) or "unknown"),
            engagement=int(getattr(record, "score", 0) or 0) + int(getattr(record, "num_comments", 0) or 0),
            tags=[str(subreddit)] if subreddit is not None else [],
            raw_metadata={
                "score": getattr(record, "score", None),
                "num_comments": getattr(record, "num_comments", None),
                "upvote_ratio": getattr(record, "upvote_ratio", None),
            },
        )

    def _listing(self, subreddit: Any, limit: int) -> Any:
        mode = self.settings.reddit_listing_mode.lower()
        if mode == "new":
            return subreddit.new(limit=limit)
        if mode == "top":
            return subreddit.top(limit=limit)
        return subreddit.hot(limit=limit)

    def _client(self) -> praw.Reddit:
        return praw.Reddit(
            client_id=self.settings.reddit_client_id,
            client_secret=self.settings.reddit_client_secret,
            user_agent=self.settings.reddit_user_agent,
            check_for_async=False,
        )
