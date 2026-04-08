from __future__ import annotations

import hashlib

from pydantic import ValidationError

from auto_foundry.llm.openai_client import LLMClient
from auto_foundry.schemas import Opportunity, StartupIdea

IDEA_RESPONSE_SCHEMA: dict[str, object] = {
    "type": "object",
    "properties": {
        "startup_idea": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "target_customer": {"type": "string"},
                "problem": {"type": "string"},
                "solution": {"type": "string"},
                "mvp": {"type": "string"},
                "why_now": {"type": "string"},
                "key_risk": {"type": "string"},
            },
            "required": [
                "name",
                "target_customer",
                "problem",
                "solution",
                "mvp",
                "why_now",
                "key_risk",
            ],
            "additionalProperties": False,
        }
    },
    "required": ["startup_idea"],
    "additionalProperties": False,
}

IDEA_MAX_OUTPUT_TOKENS = 2048


def generate_startup_ideas(
    opportunities: list[Opportunity],
    llm_client: LLMClient,
) -> tuple[list[StartupIdea], str]:
    print(f"[IDEAS] start opportunities={len(opportunities)} llm_configured={llm_client.is_configured}")
    llm_ideas = _generate_with_llm(opportunities, llm_client)
    if len(llm_ideas) == len(opportunities) and llm_ideas:
        print(f"[IDEAS] completed source=llm count={len(llm_ideas)}")
        return llm_ideas, "llm"
    fallback_ideas = _generate_with_templates(opportunities)
    if llm_ideas:
        llm_by_opportunity = {idea.opportunity_id: idea for idea in llm_ideas}
        merged_ideas = [llm_by_opportunity.get(opportunity.id) or fallback_idea for opportunity, fallback_idea in zip(opportunities, fallback_ideas)]
        print(
            f"[IDEAS] completed source=fallback count={len(merged_ideas)} "
            f"llm_count={len(llm_ideas)} fallback_count={len(merged_ideas) - len(llm_ideas)}"
        )
        return merged_ideas, "fallback"
    print(f"[IDEAS] completed source=fallback count={len(fallback_ideas)}")
    return fallback_ideas, "fallback"


def _generate_with_llm(opportunities: list[Opportunity], llm_client: LLMClient) -> list[StartupIdea]:
    ideas: list[StartupIdea] = []
    output_limit = min(llm_client.settings.llm_max_output_tokens, IDEA_MAX_OUTPUT_TOKENS)
    for index, opportunity in enumerate(opportunities, start=1):
        prompt = _build_single_idea_prompt(opportunity)
        print(f"[IDEAS] opportunity start id={opportunity.id} rank={index}")
        payload = llm_client.generate_json_with_schema(
            prompt,
            max_output_tokens=output_limit,
            json_schema=IDEA_RESPONSE_SCHEMA,
        )
        if not payload:
            print(f"[IDEAS] opportunity fallback id={opportunity.id} reason=missing_or_invalid_payload")
            continue
        if "startup_idea" not in payload:
            print(
                f"[IDEAS] opportunity fallback id={opportunity.id} reason=missing_startup_idea "
                f"keys={list(payload.keys())}"
            )
            continue
        try:
            item = payload["startup_idea"]
            ideas.append(
                StartupIdea(
                    id=f"idea-llm-{opportunity.id}",
                    opportunity_id=opportunity.id,
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
            print(f"[IDEAS] opportunity success id={opportunity.id}")
        except (KeyError, TypeError, ValidationError) as exc:
            print(
                f"[IDEAS] opportunity fallback id={opportunity.id} reason=validation_failed "
                f"error_type={type(exc).__name__} message={str(exc)[:240]}"
            )
            continue
    print(f"[IDEAS] llm_result accepted count={len(ideas)}")
    return ideas


def _build_single_idea_prompt(opportunity: Opportunity) -> str:
    return (
        "Generate exactly one startup idea for this opportunity. "
        "Keep each field concise, plain language, and focused on a realistic B2B MVP.\n\n"
        f"ID: {opportunity.id}\n"
        f"Theme: {opportunity.theme}\n"
        f"Summary: {opportunity.summary}\n"
        f"Score: {opportunity.score.final_score}"
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
