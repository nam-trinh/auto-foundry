# AGENTS.md

## Project
auto-foundry is a Python startup-opportunity discovery system.
It ingests discussion data, extracts pain signals, clusters them into opportunities, scores them, and generates startup concepts.

## Priorities
1. Keep the app runnable locally at all times.
2. Prefer simple, explicit code over clever abstractions.
3. Preserve clear module boundaries:
   - ingestion
   - extraction
   - clustering
   - scoring
   - idea generation
   - db
   - api/ui
   - shared schemas
4. Always keep deterministic fallbacks for AI-dependent steps.

## Stack
- Python 3.11+
- FastAPI
- Pydantic
- SQLite

## Conventions
- Use strong typing.
- Keep files reasonably small.
- Prefer readable functions and explicit data flow.
- Keep scoring formulas interpretable.
- Seed data must always exist so demos work without external APIs.
- Add tests for core pipeline behavior when touching core logic.

## Non-goals for now
- auth
- billing
- background jobs
- cloud infra
- production-grade scraping
- full multi-agent orchestration

## Done means
- app runs locally
- seed data loads
- pain signals are extracted
- clusters are generated
- opportunities are scored
- startup ideas are displayed in the local UI/API