from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from html import unescape
from urllib.parse import urlencode
from urllib.request import urlopen

from auto_foundry.config import Settings
from auto_foundry.ingestion.base import configured_stack_exchange_tags
from auto_foundry.schemas import NormalizedComment, NormalizedDiscussionRecord, SourceHealthCheck, TrackedThread


class StackExchangeAdapter:
    source_name = "stack_exchange"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def healthcheck(self) -> SourceHealthCheck:
        if not self.settings.stack_exchange_site:
            return SourceHealthCheck(source=self.source_name, ok=False, message="STACK_EXCHANGE_SITE is required.")
        return SourceHealthCheck(source=self.source_name, ok=True, message="Stack Exchange config is present.")

    def fetch_seed_posts(self, limit: int) -> list[NormalizedDiscussionRecord]:
        params = {
            "site": self.settings.stack_exchange_site,
            "pagesize": min(limit, 100),
            "order": self.settings.stack_exchange_order,
            "sort": self.settings.stack_exchange_sort,
            "filter": "withbody",
        }
        tags = configured_stack_exchange_tags(self.settings)
        if tags:
            params["tagged"] = ";".join(tags)
        if self.settings.stack_exchange_key:
            params["key"] = self.settings.stack_exchange_key

        payload = self._get_json(f"https://api.stackexchange.com/2.3/questions?{urlencode(params)}")
        records: list[NormalizedDiscussionRecord] = []
        for item in payload.get("items", [])[:limit]:
            normalized = self.normalize_record(item)
            if normalized is not None:
                records.append(normalized)
        return records

    def fetch_comments(self, record: object, limit: int) -> list[object]:
        return []

    def fetch_thread_comments(self, thread: TrackedThread, limit: int) -> list[NormalizedComment]:
        return []

    def normalize_record(self, record: dict[str, object]) -> NormalizedDiscussionRecord | None:
        title = _clean_html(str(record.get("title") or ""))
        body = _clean_html(str(record.get("body") or ""))
        if not title and not body:
            return None
        owner = record.get("owner") if isinstance(record.get("owner"), dict) else {}
        tags = [str(tag) for tag in record.get("tags", [])]
        engagement = int(record.get("score") or 0) + int(record.get("answer_count") or 0) + int(record.get("view_count") or 0)
        return NormalizedDiscussionRecord(
            source=self.source_name,
            source_id=str(record.get("question_id")),
            url=str(record.get("link") or ""),
            community=self.settings.stack_exchange_site,
            title=title,
            body=body,
            comments=[],
            created_at=_datetime_from_stack_exchange(record.get("creation_date")),
            author=str(owner.get("display_name") or "unknown"),
            engagement=engagement,
            tags=tags,
            raw_metadata={
                "score": record.get("score"),
                "answer_count": record.get("answer_count"),
                "view_count": record.get("view_count"),
                "is_answered": record.get("is_answered"),
            },
        )

    def _get_json(self, url: str) -> dict[str, object]:
        with urlopen(url, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))


def _clean_html(value: str) -> str:
    return re.sub(r"<[^>]+>", "", unescape(value)).strip()


def _datetime_from_stack_exchange(value: object) -> datetime | None:
    if not isinstance(value, (int, float)):
        return None
    return datetime.fromtimestamp(value, tz=timezone.utc)
