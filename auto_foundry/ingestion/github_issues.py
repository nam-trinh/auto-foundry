from __future__ import annotations

import json
from datetime import datetime
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from auto_foundry.config import Settings
from auto_foundry.schemas import NormalizedComment, NormalizedDiscussionRecord, SourceHealthCheck


class GitHubIssuesAdapter:
    source_name = "github_issues"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def healthcheck(self) -> SourceHealthCheck:
        if not self.settings.github_owner or not self.settings.github_repo:
            return SourceHealthCheck(
                source=self.source_name,
                ok=False,
                message="GITHUB_OWNER and GITHUB_REPO are required for GitHub Issues ingestion.",
            )
        return SourceHealthCheck(source=self.source_name, ok=True, message="GitHub Issues config is present.")

    def fetch_seed_posts(self, limit: int) -> list[NormalizedDiscussionRecord]:
        health = self.healthcheck()
        if not health.ok:
            return []
        params = urlencode({"state": self.settings.github_state, "per_page": min(limit, 100)})
        url = f"https://api.github.com/repos/{self.settings.github_owner}/{self.settings.github_repo}/issues?{params}"
        issues = self._get_json(url)
        records: list[NormalizedDiscussionRecord] = []
        for item in issues[:limit]:
            normalized = self.normalize_record(item)
            if normalized is not None:
                records.append(normalized)
        return records

    def fetch_comments(self, record: dict[str, object], limit: int) -> list[NormalizedComment]:
        if not self.settings.github_include_comments:
            return []
        comments_url = record.get("comments_url")
        if not comments_url:
            return []
        comments = self._get_json(str(comments_url))
        normalized_comments: list[NormalizedComment] = []
        for item in comments[:limit]:
            user = item.get("user") if isinstance(item.get("user"), dict) else {}
            normalized_comments.append(
                NormalizedComment(
                    comment_id=str(item.get("id")),
                    author=str(user.get("login") or "unknown"),
                    body=str(item.get("body") or ""),
                    created_at=_datetime_from_github(item.get("created_at")),
                    score=None,
                    parent_id=None,
                )
            )
        return normalized_comments

    def normalize_record(self, record: dict[str, object]) -> NormalizedDiscussionRecord | None:
        if "pull_request" in record:
            return None
        title = str(record.get("title") or "")
        body = str(record.get("body") or "")
        if not title and not body:
            return None
        user = record.get("user") if isinstance(record.get("user"), dict) else {}
        labels = record.get("labels") if isinstance(record.get("labels"), list) else []
        tags = [str(item.get("name")) for item in labels if isinstance(item, dict) and item.get("name")]
        reactions = record.get("reactions") if isinstance(record.get("reactions"), dict) else {}
        engagement = int(record.get("comments") or 0) + int(reactions.get("total_count") or 0)
        return NormalizedDiscussionRecord(
            source=self.source_name,
            source_id=str(record.get("id") or record.get("number")),
            url=str(record.get("html_url") or ""),
            community=f"{self.settings.github_owner}/{self.settings.github_repo}",
            title=title,
            body=body,
            comments=self.fetch_comments(record, self.settings.github_comment_limit),
            created_at=_datetime_from_github(record.get("created_at")),
            author=str(user.get("login") or "unknown"),
            engagement=engagement,
            tags=tags,
            raw_metadata={
                "number": record.get("number"),
                "state": record.get("state"),
                "comments": record.get("comments"),
                "reactions": reactions,
            },
        )

    def _get_json(self, url: str) -> list[dict[str, object]]:
        request = Request(url, headers=self._headers())
        with urlopen(request, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))

    def _headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "auto-foundry-local",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.settings.github_token:
            headers["Authorization"] = f"Bearer {self.settings.github_token}"
        return headers


def _datetime_from_github(value: object) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))
