# Auto Foundry

Auto Foundry is a local Python MVP that turns discussion data into ranked startup opportunities.

It ingests normalized discussion posts, extracts pain signals, clusters them, scores the opportunities transparently, and generates startup ideas. The app can call OpenAI for extraction and idea generation, but it always falls back to deterministic local rules if no API key is configured or an LLM call fails.

## Setup

```bash
uv sync
cp .env.example .env
```

Edit `.env`:

```bash
OPENAI_API_KEY=your_key_here
LLM_MODEL=gpt-5-mini
INGESTION_SOURCES=mock
```

Use `gpt-5-mini` for cheaper development runs. Switch to `gpt-5`, `o1`, or another supported OpenAI model by changing `LLM_MODEL`.

## Source Ingestion

Auto Foundry supports single-source and multi-source ingestion.

- Preferred: `INGESTION_SOURCES=mock,hacker_news,reddit`
- Backward-compatible: `INGESTION_SOURCE=hacker_news`

If `mock` is included, deterministic local seed data is always loaded. Any configured external source is appended and deduplicated. If an external adapter is not configured or fails, the rest of the configured sources still run.

Legacy behavior is preserved:

- `INGESTION_SOURCE=hacker_news` means mock plus Hacker News.
- `INGESTION_SOURCES=hacker_news,reddit` means only Hacker News and Reddit.
- `INGESTION_SOURCES=mock,hacker_news,reddit` means mock plus both external sources.

Supported source adapters:

- `mock`: deterministic local seed discussions.
- `reddit`: Reddit API via PRAW.
- `hacker_news` or `hn`: official Hacker News Firebase API.
- `stack_exchange` or `stackexchange`: Stack Exchange API.
- `github_issues` or `github`: GitHub REST API issues endpoint, excluding pull requests.

Reddit requires API credentials:

```bash
INGESTION_SOURCES=mock,reddit
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_USER_AGENT=auto-foundry-local/0.1
REDDIT_SUBREDDITS=startups,SaaS,Entrepreneur
REDDIT_LISTING_MODE=hot
REDDIT_INCLUDE_COMMENTS=false
```

Other source examples:

```bash
INGESTION_SOURCES=mock,hacker_news
HN_LISTING=askstories

INGESTION_SOURCES=mock,stack_exchange
STACK_EXCHANGE_SITE=stackoverflow
STACK_EXCHANGE_TAGS=python;fastapi

INGESTION_SOURCES=mock,github_issues
GITHUB_OWNER=owner
GITHUB_REPO=repo
GITHUB_TOKEN=
```

## Ingestion Scheduling

The scheduler is local-first and intentionally simple. It uses scheduled polling rather than continuous scraping:

```python
from auto_foundry.ingestion.scheduler import scheduler_loop

scheduler_loop()
```

For app-controlled execution, call one tick at a time:

```python
from auto_foundry.ingestion.scheduler import run_scheduler_tick

results = run_scheduler_tick("auto_foundry.sqlite3")
```

Manual refresh functions reuse the same ingestion jobs:

```python
from auto_foundry.ingestion.scheduler import (
    refresh_source_config_now,
    refresh_tracked_thread_now,
    run_reconciliation_now,
)

refresh_source_config_now("auto_foundry.sqlite3", "src-...")
refresh_tracked_thread_now("auto_foundry.sqlite3", "thread-...")
run_reconciliation_now("auto_foundry.sqlite3", "src-...")
```

Scheduler defaults:

- Global tick: 1 hour.
- Post discovery: every 3 hours.
- Discovery overlap window: 12 hours.
- Hot thread refresh: every 1 hour.
- Warm thread refresh: every 6 hours.
- Cold thread refresh: every 12 hours.
- Archived threads older than 7 days: not refreshed automatically.
- Reconciliation: every 24 hours over the last 7 days.

Scheduler tables are created automatically by `init_db`:

- `source_configs`: source type, query/target, enabled flag, post polling interval, overlap window, timestamps.
- `ingestion_states`: last successful discovery, last attempted discovery, last reconciliation, optional last seen external item ID.
- `ingestion_runs`: run ID, source config, job type, status, timestamps, fetched/inserted/updated/skipped counts, error message.
- `tracked_threads`: source thread identity, first/last seen timestamps, comment refresh timestamp, observed comment count, activity status, active polling flag.
- `ingested_comments`: source/comment unique identity and normalized comment payload.
- `analysis_dirty_markers`: dirty markers emitted after successful thread/comment upserts so analysis can run separately.

Design decisions:

- Overlap windows are used because forum APIs and listings can be delayed, reordered, or retried. Re-reading a recent window is safer than trusting a strict timestamp checkpoint.
- Post discovery and comment refresh are separate because new-thread discovery and active-thread comment polling have different schedules and cost profiles.
- Idempotency is guaranteed with stable keys like `source:source_id` for discussions, `source_type + external_thread_id` for tracked threads, and `source_type + external_comment_id` for comments. Jobs use upserts, so overlapping windows and retries do not duplicate data.
- Active thread decay is based on source creation age: under 24h is hot, 1-3 days is warm, 3-7 days is cold, and older than 7 days is archived.
- Checkpoints for successful discovery and reconciliation are updated only after successful jobs. Failed jobs record an ingestion run error without advancing the success checkpoint.

To add a new source adapter:

- Implement the `SourceAdapter` protocol in `auto_foundry/ingestion/base.py`.
- Return `NormalizedDiscussionRecord` and `NormalizedComment` models.
- Add the adapter to the scheduler adapter map.
- Make fetch methods bounded by `limit` and safe to retry.
- Keep source-specific API details inside the adapter; scheduler and persistence should not know the API shape.

## Run

```bash
uv run uvicorn auto_foundry.api.app:app --reload
```

Open `http://127.0.0.1:8000`.

Run the pipeline:

```bash
curl -X POST http://127.0.0.1:8000/api/pipeline/run
```

## Test

```bash
uv run pytest
uv run python -m compileall auto_foundry
```

## API

- `GET /api/health`
- `POST /api/pipeline/run`
- `GET /api/discussions`
- `GET /api/pain-signals`
- `GET /api/opportunities`
- `GET /api/startup-ideas`

## What Is Mocked Vs Real

- Mocked: local seed discussion ingestion uses deterministic data in `auto_foundry/ingestion/mock_data.py`.
- Real: normalized source adapters, SQLite persistence, FastAPI API, dashboard rendering, deterministic extraction/clustering/scoring/idea generation.
- Optional external ingestion: Reddit, Hacker News, Stack Exchange, and GitHub Issues adapters can append source records when configured.
- Optional real LLM: OpenAI calls are attempted when `OPENAI_API_KEY` is set. The app uses `LLM_MODEL` from `.env`.
- Fallback: if no source credentials exist, an external source fails, no LLM key exists, or an LLM call fails, local deterministic logic keeps the app runnable.

## Next Improvements

- Add richer JSON schemas for LLM structured outputs.
- Add deeper pagination, rate-limit handling, and saved ingestion run metadata.
- Add opportunity detail pages with evidence drill-down.
- Track pipeline run history and model usage.
- Add better clustering using embeddings once the MVP shape is stable.
