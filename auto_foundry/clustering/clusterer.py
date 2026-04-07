from __future__ import annotations

import hashlib
from collections import defaultdict

from auto_foundry.schemas import Opportunity, PainSignal, ScoreBreakdown


EMPTY_SCORE = ScoreBreakdown(
    frequency=0.0,
    severity=0.0,
    willingness_to_pay=0.0,
    urgency=0.0,
    final_score=0.0,
    formula="score = frequency * 0.4 + severity * 0.3 + willingness_to_pay * 0.2 + urgency * 0.1",
)


def cluster_pain_signals(signals: list[PainSignal]) -> list[Opportunity]:
    grouped: dict[str, list[PainSignal]] = defaultdict(list)
    for signal in signals:
        grouped[signal.theme_hint].append(signal)

    opportunities: list[Opportunity] = []
    for theme, theme_signals in grouped.items():
        source_ids = [signal.id for signal in theme_signals]
        opportunities.append(
            Opportunity(
                id=_stable_id("opp", theme),
                theme=theme,
                title=f"{theme.title()} Opportunity",
                summary=_summarize_theme(theme, theme_signals),
                evidence_count=len(theme_signals),
                source_pain_ids=source_ids,
                score=EMPTY_SCORE,
            )
        )
    return opportunities


def _summarize_theme(theme: str, signals: list[PainSignal]) -> str:
    summaries = " ".join(signal.summary for signal in signals[:3])
    return f"Repeated pain around {theme}. Evidence: {summaries}"


def _stable_id(prefix: str, value: str) -> str:
    digest = hashlib.sha1(value.encode("utf-8")).hexdigest()[:10]
    return f"{prefix}-{digest}"
