from __future__ import annotations

import json
import re
from html import unescape
from urllib.request import urlopen

from auto_foundry.config import Settings
from auto_foundry.schemas import NormalizedComment, NormalizedDiscussionRecord, SourceHealthCheck, datetime_from_unix


class HackerNewsAdapter:
    source_name = "hacker_news"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def healthcheck(self) -> SourceHealthCheck:
        if not self.settings.hn_base_url:
            return SourceHealthCheck(source=self.source_name, ok=False, message="HN_BASE_URL is required.")
        return SourceHealthCheck(source=self.source_name, ok=True, message="Hacker News config is present.")

    def fetch_seed_posts(self, limit: int) -> list[NormalizedDiscussionRecord]:
        story_ids = self._get_json(f"{self.settings.hn_base_url}/{self.settings.hn_listing}.json") or []
        records: list[NormalizedDiscussionRecord] = []
        for story_id in story_ids[:limit]:
            item = self._get_json(f"{self.settings.hn_base_url}/item/{story_id}.json")
            if not item:
                continue
            normalized = self.normalize_record(item)
            if normalized is not None:
                records.append(normalized)
        return records

    def fetch_comments(self, record: dict[str, object], limit: int) -> list[NormalizedComment]:
        if not self.settings.hn_include_comments:
            return []
        comments: list[NormalizedComment] = []
        for comment_id in list(record.get("kids", []))[:limit]:
            item = self._get_json(f"{self.settings.hn_base_url}/item/{comment_id}.json")
            if not item or item.get("deleted") or item.get("dead"):
                continue
            body = _clean_html(str(item.get("text", "")))
            if not body:
                continue
            comments.append(
                NormalizedComment(
                    comment_id=str(item.get("id")),
                    author=str(item.get("by") or "unknown"),
                    body=body,
                    created_at=datetime_from_unix(item.get("time")),
                    score=None,
                    parent_id=str(item.get("parent")) if item.get("parent") is not None else None,
                )
            )
        return comments

    def normalize_record(self, record: dict[str, object]) -> NormalizedDiscussionRecord | None:
        if record.get("deleted") or record.get("dead"):
            return None
        title = str(record.get("title") or "")
        body = _clean_html(str(record.get("text") or ""))
        if not title and not body:
            return None
        source_id = str(record.get("id"))
        return NormalizedDiscussionRecord(
            source=self.source_name,
            source_id=source_id,
            url=str(record.get("url") or f"https://news.ycombinator.com/item?id={source_id}"),
            community=str(record.get("type") or "story"),
            title=title or "Untitled Hacker News item",
            body=body,
            comments=self.fetch_comments(record, self.settings.hn_comment_limit),
            created_at=datetime_from_unix(record.get("time")),
            author=str(record.get("by") or "unknown"),
            engagement=int(record.get("score") or 0) + len(record.get("kids", []) or []),
            tags=["hacker-news", str(record.get("type") or "story")],
            raw_metadata={"score": record.get("score"), "descendants": record.get("descendants")},
        )

    def _get_json(self, url: str) -> object | None:
        with urlopen(url, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))


def _clean_html(value: str) -> str:
    return re.sub(r"<[^>]+>", "", unescape(value)).strip()
