from __future__ import annotations

import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from auto_foundry.config import get_settings
from auto_foundry.db.database import connect, init_db
from auto_foundry.db.repository import (
    list_discussions,
    list_opportunities,
    list_pain_signals,
    list_startup_ideas,
    upsert_discussions,
)
from auto_foundry.ingestion.service import fetch_discussions
from auto_foundry.llm.openai_client import LLMClient
from auto_foundry.pipeline import run_pipeline
from auto_foundry.schemas import LLMHealthStatus


BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
app = FastAPI(title="Auto Foundry", version="0.1.0")
logger = logging.getLogger(__name__)
llm_status_cache = LLMHealthStatus(
    provider="openai",
    model="unknown",
    configured=False,
    reachable=False,
    message="not_checked",
)


@app.on_event("startup")
def startup() -> None:
    settings = get_settings()
    global llm_status_cache
    init_db(settings.db_path)
    with connect(settings.db_path) as connection:
        upsert_discussions(connection, fetch_discussions(settings, include_external=False))
    llm_status_cache = LLMClient(settings).check_connectivity()
    if not llm_status_cache.configured:
        print(_format_llm_startup_message(llm_status_cache))
        logger.info(
            "LLM startup check skipped provider=%s model=%s reason=%s",
            llm_status_cache.provider,
            llm_status_cache.model,
            llm_status_cache.message,
        )
    elif llm_status_cache.reachable:
        print(_format_llm_startup_message(llm_status_cache))
        logger.info(
            "LLM startup check passed provider=%s model=%s",
            llm_status_cache.provider,
            llm_status_cache.model,
        )
    else:
        print(_format_llm_startup_message(llm_status_cache))
        logger.warning(
            "LLM startup check failed provider=%s model=%s message=%s",
            llm_status_cache.provider,
            llm_status_cache.model,
            llm_status_cache.message,
        )


def _format_llm_startup_message(status: LLMHealthStatus) -> str:
    if not status.configured:
        return f"LLM startup check skipped provider={status.provider} model={status.model} reason={status.message}"
    if status.reachable:
        return f"LLM startup check passed provider={status.provider} model={status.model}"
    return f"LLM startup check failed provider={status.provider} model={status.model} message={status.message}"


@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request) -> HTMLResponse:
    settings = get_settings()
    init_db(settings.db_path)
    with connect(settings.db_path) as connection:
        opportunities = list_opportunities(connection)
        ideas = list_startup_ideas(connection)
        discussions = list_discussions(connection)
        pain_signals = list_pain_signals(connection)

    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "opportunities": opportunities,
            "ideas": ideas,
            "discussions": discussions,
            "pain_signals": pain_signals,
            "llm_model": settings.llm_model,
            "has_api_key": bool(settings.openai_api_key),
        },
    )


@app.get("/api/health")
def health() -> dict[str, object]:
    return {
        "status": "ok",
        "llm": llm_status_cache.model_dump(),
    }


@app.post("/api/pipeline/run")
def run_pipeline_endpoint() -> dict[str, object]:
    return run_pipeline().model_dump()


@app.get("/api/discussions")
def discussions() -> list[dict[str, object]]:
    settings = get_settings()
    init_db(settings.db_path)
    with connect(settings.db_path) as connection:
        return [item.model_dump() for item in list_discussions(connection)]


@app.get("/api/pain-signals")
def pain_signals() -> list[dict[str, object]]:
    settings = get_settings()
    init_db(settings.db_path)
    with connect(settings.db_path) as connection:
        return [item.model_dump() for item in list_pain_signals(connection)]


@app.get("/api/opportunities")
def opportunities() -> list[dict[str, object]]:
    settings = get_settings()
    init_db(settings.db_path)
    with connect(settings.db_path) as connection:
        return [item.model_dump() for item in list_opportunities(connection)]


@app.get("/api/startup-ideas")
def startup_ideas() -> list[dict[str, object]]:
    settings = get_settings()
    init_db(settings.db_path)
    with connect(settings.db_path) as connection:
        return [item.model_dump() for item in list_startup_ideas(connection)]
