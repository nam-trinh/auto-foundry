from __future__ import annotations

import hashlib

from pydantic import ValidationError

from auto_foundry.llm.openai_client import LLMClient
from auto_foundry.schemas import Discussion, PainSignal


THEME_KEYWORDS: dict[str, list[str]] = {
    "workflow automation": ["manual", "copy", "spreadsheet", "slow", "workflow", "brittle"],
    "reporting and analytics": ["report", "dashboard", "numbers", "stale", "trends", "data"],
    "integrations": ["integration", "synced", "systems", "tools", "hubspot", "stripe"],
    "customer support": ["support", "tickets", "feedback", "questions", "roadmap"],
    "compliance operations": ["compliance", "soc2", "evidence", "policy", "access", "vendor"],
    "developer tooling": ["developer", "docs", "onboarding", "repos", "service", "engineers"],
}

PAIN_MARKERS = [
    "manually",
    "manual",
    "slow",
    "error-prone",
    "waste",
    "wasted",
    "expensive",
    "frustrating",
    "unreliable",
    "out of date",
    "too long",
    "brittle",
    "stale",
    "miss",
    "scattered",
]


def extract_pain_signals(discussions: list[Discussion], llm_client: LLMClient) -> tuple[list[PainSignal], str]:
    print(f"[EXTRACT] start discussions={len(discussions)} llm_configured={llm_client.is_configured}")
    llm_signals = _extract_with_llm(discussions, llm_client)
    if llm_signals:
        print(f"[EXTRACT] completed source=llm count={len(llm_signals)}")
        return llm_signals, "llm"
    fallback_signals = _extract_with_rules(discussions)
    print(f"[EXTRACT] completed source=fallback count={len(fallback_signals)}")
    return fallback_signals, "fallback"


def _extract_with_llm(discussions: list[Discussion], llm_client: LLMClient) -> list[PainSignal]:
    prompt = _build_extraction_prompt(discussions)
    payload = llm_client.generate_json(prompt, max_output_tokens=2048)
    if not payload:
        print("[EXTRACT] llm_result missing_or_invalid")
        return []
    if "pain_signals" not in payload:
        print(f"[EXTRACT] llm_result missing pain_signals keys={list(payload.keys())}")
        return []

    signals: list[PainSignal] = []
    try:
        for index, item in enumerate(payload["pain_signals"], start=1):
            discussion_id = str(item["discussion_id"])
            signal_id = str(item.get("id") or f"pain-llm-{index:03d}")
            signals.append(
                PainSignal(
                    id=signal_id,
                    discussion_id=discussion_id,
                    summary=str(item["summary"]),
                    quote=str(item.get("quote", "")),
                    severity=int(item.get("severity", 3)),
                    theme_hint=str(item.get("theme_hint", "workflow automation")),
                    source="llm",
                )
            )
    except (KeyError, TypeError, ValueError, ValidationError) as exc:
        print(
            f"[EXTRACT] llm_result validation_failed index={index} "
            f"error_type={type(exc).__name__} message={str(exc)[:240]}"
        )
        return []
    print(f"[EXTRACT] llm_result accepted count={len(signals)}")
    return signals


def _build_extraction_prompt(discussions: list[Discussion]) -> str:
    serialized = "\n\n".join(
        f"ID: {item.id}\nTitle: {item.title}\nBody: {item.body}" for item in discussions
    )
    return (
        "Extract startup opportunity pain signals from these discussions. "
        "Return strict JSON with key pain_signals containing objects with "
        "id, discussion_id, summary, quote, severity 1-5, and theme_hint. "
        "Return at most one pain signal per discussion. Keep summaries concise and "
        "theme_hint short, using 2-5 words. Keep quotes brief. \n\n"
        f"{serialized}"
    )


def _extract_with_rules(discussions: list[Discussion]) -> list[PainSignal]:
    signals: list[PainSignal] = []
    for discussion in discussions:
        text = f"{discussion.title} {discussion.body}".lower()
        if not any(marker in text for marker in PAIN_MARKERS):
            continue
        theme = _infer_theme(text)
        signals.append(
            PainSignal(
                id=_stable_id("pain", discussion.id),
                discussion_id=discussion.id,
                summary=_summarize_pain(discussion, theme),
                quote=_first_sentence(discussion.body),
                severity=_infer_severity(text),
                theme_hint=theme,
                source="fallback",
            )
        )
    return signals


def _infer_theme(text: str) -> str:
    scores = {
        theme: sum(1 for keyword in keywords if keyword in text)
        for theme, keywords in THEME_KEYWORDS.items()
    }
    return max(scores, key=scores.get)


def _infer_severity(text: str) -> int:
    severity = 2
    for marker in ["waste", "wasted", "expensive", "error-prone", "brittle", "part-time job"]:
        if marker in text:
            severity += 1
    return min(severity, 5)


def _summarize_pain(discussion: Discussion, theme: str) -> str:
    return f"{discussion.author} is struggling with {theme}: {discussion.title.lower()}."


def _first_sentence(text: str) -> str:
    return text.split(".")[0].strip() + "."


def _stable_id(prefix: str, value: str) -> str:
    digest = hashlib.sha1(value.encode("utf-8")).hexdigest()[:10]
    return f"{prefix}-{digest}"
