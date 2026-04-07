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
INGESTION_SOURCE=mock
```

Use `gpt-5-mini` for cheaper development runs. Switch to `gpt-5`, `o1`, or another supported OpenAI model by changing `LLM_MODEL`.

## Source Ingestion

Auto Foundry always keeps local mock seed data available. By default, `INGESTION_SOURCE=mock` means the pipeline uses mock data only. If you set an external source, the pipeline uses mock plus that external source and falls back to mock-only if the external adapter is not configured or fails.

Supported source adapters:

- `mock`: deterministic local seed discussions.
- `reddit`: Reddit API via PRAW.
- `hacker_news` or `hn`: official Hacker News Firebase API.
- `stack_exchange` or `stackexchange`: Stack Exchange API.
- `github_issues` or `github`: GitHub REST API issues endpoint, excluding pull requests.

Reddit requires API credentials:

```bash
INGESTION_SOURCE=reddit
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_USER_AGENT=auto-foundry-local/0.1
REDDIT_SUBREDDITS=startups,SaaS,Entrepreneur
REDDIT_LISTING_MODE=hot
REDDIT_INCLUDE_COMMENTS=false
```

Other source examples:

```bash
INGESTION_SOURCE=hacker_news
HN_LISTING=askstories

INGESTION_SOURCE=stack_exchange
STACK_EXCHANGE_SITE=stackoverflow
STACK_EXCHANGE_TAGS=python;fastapi

INGESTION_SOURCE=github_issues
GITHUB_OWNER=owner
GITHUB_REPO=repo
GITHUB_TOKEN=
```

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
