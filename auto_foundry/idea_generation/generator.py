from __future__ import annotations

import hashlib

from pydantic import ValidationError

from auto_foundry.llm.openai_client import LLMClient
from auto_foundry.schemas import Opportunity, StartupIdea


def generate_startup_ideas(
    opportunities: list[Opportunity],
    llm_client: LLMClient,
) -> tuple[list[StartupIdea], str]:
    llm_ideas = _generate_with_llm(opportunities, llm_client)
    if llm_ideas:
        return llm_ideas, "llm"
    return _generate_with_templates(opportunities), "fallback"


def _generate_with_llm(opportunities: list[Opportunity], llm_client: LLMClient) -> list[StartupIdea]:
    prompt = _build_idea_prompt(opportunities)
    payload = llm_client.generate_json(prompt)
    if not payload or "startup_ideas" not in payload:
        return []

    ideas: list[StartupIdea] = []
    try:
        for index, item in enumerate(payload["startup_ideas"], start=1):
            ideas.append(
                StartupIdea(
                    id=str(item.get("id") or f"idea-llm-{index:03d}"),
                    opportunity_id=str(item["opportunity_id"]),
                    name=str(item["name"]),
                    target_customer=str(item["target_customer"]),
                    problem=str(item["problem"]),
                    solution=str(item["solution"]),
                    mvp=str(item["mvp"]),
                    why_now=str(item["why_now"]),
                    key_risk=str(item["key_risk"]),
                    source="llm",
                )
            )
    except (KeyError, TypeError, ValidationError):
        return []
    return ideas


def _build_idea_prompt(opportunities: list[Opportunity]) -> str:
    serialized = "\n\n".join(
        (
            f"ID: {item.id}\nTheme: {item.theme}\nSummary: {item.summary}\n"
            f"Score: {item.score.final_score}"
        )
        for item in opportunities
    )
    return (
        "Generate one startup idea for each opportunity. Return strict JSON with key "
        "startup_ideas containing objects with id, opportunity_id, name, target_customer, "
        "problem, solution, mvp, why_now, and key_risk.\n\n"
        f"{serialized}"
    )


def _generate_with_templates(opportunities: list[Opportunity]) -> list[StartupIdea]:
    return [
        StartupIdea(
            id=_stable_id("idea", opportunity.id),
            opportunity_id=opportunity.id,
            name=_name_for_theme(opportunity.theme),
            target_customer=_customer_for_theme(opportunity.theme),
            problem=opportunity.summary,
            solution=f"A lightweight assistant that detects and automates recurring {opportunity.theme} work.",
            mvp="Connect two common data sources, surface the top recurring issues, and generate a weekly action plan.",
            why_now="Teams are adopting AI copilots but still need domain-specific workflow glue around fragmented SaaS tools.",
            key_risk="The first version may be too generic unless it focuses on one high-urgency workflow and buyer.",
            source="fallback",
        )
        for opportunity in opportunities
    ]


def _name_for_theme(theme: str) -> str:
    words = "".join(word.title() for word in theme.split())
    return f"{words} Copilot"


def _customer_for_theme(theme: str) -> str:
    if "developer" in theme:
        return "Engineering managers at scaling SaaS teams"
    if "compliance" in theme:
        return "Founders and ops leads preparing for security reviews"
    if "support" in theme:
        return "Customer support and product operations teams"
    if "reporting" in theme:
        return "Revenue operations leaders"
    return "Operations-heavy B2B SaaS teams"


def _stable_id(prefix: str, value: str) -> str:
    digest = hashlib.sha1(value.encode("utf-8")).hexdigest()[:10]
    return f"{prefix}-{digest}"
