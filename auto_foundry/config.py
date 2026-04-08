from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    openai_api_key: str | None
    llm_provider: str
    llm_model: str
    llm_model_dev: str
    llm_model_prod: str
    llm_timeout_seconds: float
    llm_max_output_tokens: int
    db_path: str
    ingestion_source: str = "mock"
    ingestion_sources: list[str] | None = None
    ingestion_limit: int = 25
    reddit_client_id: str | None = None
    reddit_client_secret: str | None = None
    reddit_user_agent: str = "auto-foundry-local/0.1"
    reddit_subreddits: list[str] | None = None
    reddit_listing_mode: str = "hot"
    reddit_include_comments: bool = False
    reddit_comment_limit: int = 25
    hn_base_url: str = "https://hacker-news.firebaseio.com/v0"
    hn_listing: str = "askstories"
    hn_include_comments: bool = False
    hn_comment_limit: int = 25
    stack_exchange_site: str = "stackoverflow"
    stack_exchange_tags: list[str] | None = None
    stack_exchange_sort: str = "activity"
    stack_exchange_order: str = "desc"
    stack_exchange_key: str | None = None
    github_token: str | None = None
    github_owner: str | None = None
    github_repo: str | None = None
    github_state: str = "open"
    github_include_comments: bool = False
    github_comment_limit: int = 25


def get_settings() -> Settings:
    api_key = os.getenv("OPENAI_API_KEY") or None
    return Settings(
        openai_api_key=api_key,
        llm_provider=os.getenv("LLM_PROVIDER", "openai"),
        llm_model=os.getenv("LLM_MODEL", "gpt-5-mini"),
        llm_model_dev=os.getenv("LLM_MODEL_DEV", "gpt-5-mini"),
        llm_model_prod=os.getenv("LLM_MODEL_PROD", "gpt-5"),
        llm_timeout_seconds=float(os.getenv("LLM_TIMEOUT_SECONDS", "20")),
        llm_max_output_tokens=int(os.getenv("LLM_MAX_OUTPUT_TOKENS", "1200")),
        db_path=os.getenv("AUTO_FOUNDRY_DB_PATH", "auto_foundry.sqlite3"),
        ingestion_source=os.getenv("INGESTION_SOURCE", "mock"),
        ingestion_sources=_split_csv(os.getenv("INGESTION_SOURCES", "").strip()),
        ingestion_limit=int(os.getenv("INGESTION_LIMIT", "25")),
        reddit_client_id=os.getenv("REDDIT_CLIENT_ID") or None,
        reddit_client_secret=os.getenv("REDDIT_CLIENT_SECRET") or None,
        reddit_user_agent=os.getenv("REDDIT_USER_AGENT", "auto-foundry-local/0.1"),
        reddit_subreddits=_split_csv(os.getenv("REDDIT_SUBREDDITS", "startups,SaaS,Entrepreneur")),
        reddit_listing_mode=os.getenv("REDDIT_LISTING_MODE", "hot"),
        reddit_include_comments=_parse_bool(os.getenv("REDDIT_INCLUDE_COMMENTS", "false")),
        reddit_comment_limit=int(os.getenv("REDDIT_COMMENT_LIMIT", "25")),
        hn_base_url=os.getenv("HN_BASE_URL", "https://hacker-news.firebaseio.com/v0"),
        hn_listing=os.getenv("HN_LISTING", "askstories"),
        hn_include_comments=_parse_bool(os.getenv("HN_INCLUDE_COMMENTS", "false")),
        hn_comment_limit=int(os.getenv("HN_COMMENT_LIMIT", "25")),
        stack_exchange_site=os.getenv("STACK_EXCHANGE_SITE", "stackoverflow"),
        stack_exchange_tags=_split_semicolon(os.getenv("STACK_EXCHANGE_TAGS", "python;fastapi")),
        stack_exchange_sort=os.getenv("STACK_EXCHANGE_SORT", "activity"),
        stack_exchange_order=os.getenv("STACK_EXCHANGE_ORDER", "desc"),
        stack_exchange_key=os.getenv("STACK_EXCHANGE_KEY") or None,
        github_token=os.getenv("GITHUB_TOKEN") or None,
        github_owner=os.getenv("GITHUB_OWNER") or None,
        github_repo=os.getenv("GITHUB_REPO") or None,
        github_state=os.getenv("GITHUB_STATE", "open"),
        github_include_comments=_parse_bool(os.getenv("GITHUB_INCLUDE_COMMENTS", "false")),
        github_comment_limit=int(os.getenv("GITHUB_COMMENT_LIMIT", "25")),
    )


def _parse_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _split_semicolon(value: str) -> list[str]:
    return [item.strip() for item in value.split(";") if item.strip()]


def configured_ingestion_sources(settings: Settings) -> list[str]:
    sources = settings.ingestion_sources or []
    if sources:
        return _normalize_sources(sources)
    return _normalize_sources([settings.ingestion_source])


def should_include_mock_source(settings: Settings) -> bool:
    if settings.ingestion_sources:
        return "mock" in configured_ingestion_sources(settings)
    return True


def _normalize_sources(values: list[str]) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for value in values:
        item = value.strip()
        if not item:
            continue
        if item in seen:
            continue
        seen.add(item)
        normalized.append(item)
    return normalized or ["mock"]
