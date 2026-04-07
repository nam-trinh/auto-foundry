from __future__ import annotations

from auto_foundry.schemas import Opportunity, PainSignal, ScoreBreakdown


FORMULA = "score = frequency * 0.4 + severity * 0.3 + willingness_to_pay * 0.2 + urgency * 0.1"
PAY_MARKERS = ["pay", "expensive", "cost", "pricing", "budget"]
URGENCY_MARKERS = ["weekly", "friday", "hours", "every", "always", "part-time job", "too long"]


def score_opportunities(opportunities: list[Opportunity], signals: list[PainSignal]) -> list[Opportunity]:
    signal_by_id = {signal.id: signal for signal in signals}
    max_evidence = max((item.evidence_count for item in opportunities), default=1)
    scored: list[Opportunity] = []

    for opportunity in opportunities:
        evidence = [signal_by_id[pain_id] for pain_id in opportunity.source_pain_ids if pain_id in signal_by_id]
        frequency = round(opportunity.evidence_count / max_evidence * 5, 2)
        severity = round(sum(signal.severity for signal in evidence) / max(len(evidence), 1), 2)
        combined_text = " ".join(signal.summary.lower() + " " + signal.quote.lower() for signal in evidence)
        willingness_to_pay = 4.0 if any(marker in combined_text for marker in PAY_MARKERS) else 2.5
        urgency = 4.0 if any(marker in combined_text for marker in URGENCY_MARKERS) else 3.0
        final_score = round(
            frequency * 0.4 + severity * 0.3 + willingness_to_pay * 0.2 + urgency * 0.1,
            2,
        )
        scored.append(
            opportunity.model_copy(
                update={
                    "score": ScoreBreakdown(
                        frequency=frequency,
                        severity=severity,
                        willingness_to_pay=willingness_to_pay,
                        urgency=urgency,
                        final_score=final_score,
                        formula=FORMULA,
                    )
                }
            )
        )
    return sorted(scored, key=lambda item: item.score.final_score, reverse=True)
