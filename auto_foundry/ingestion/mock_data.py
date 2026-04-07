from __future__ import annotations

from auto_foundry.schemas import Discussion


SEED_DISCUSSIONS: list[Discussion] = [
    Discussion(
        id="disc-001",
        source="mock-reddit",
        author="ops_founder_42",
        title="Spending Fridays stitching together customer onboarding spreadsheets",
        body=(
            "Every Friday I manually copy onboarding data from HubSpot, Stripe, "
            "and our product database into a spreadsheet. It is slow, error-prone, "
            "and I would happily pay for something that keeps customer health and "
            "activation status synced without another brittle integration project."
        ),
    ),
    Discussion(
        id="disc-002",
        source="mock-slack",
        author="revops_lead",
        title="Reporting is still a mess across sales and success",
        body=(
            "Our exec team asks for weekly expansion risk reports, but the data lives "
            "in five tools. The dashboards are always stale, and we waste hours "
            "explaining why numbers do not match between systems."
        ),
    ),
    Discussion(
        id="disc-003",
        source="mock-hn",
        author="solo_saas",
        title="SOC2 evidence collection is eating our sprint planning",
        body=(
            "Compliance evidence collection feels like a part-time job. Screenshots, "
            "policy updates, access reviews, and vendor docs all end up in random "
            "folders. Existing tools feel expensive for a tiny team."
        ),
    ),
    Discussion(
        id="disc-004",
        source="mock-forum",
        author="support_mgr",
        title="Support tickets repeat the same root cause",
        body=(
            "We keep answering the same support questions because product feedback "
            "never makes it back to roadmap planning. It is frustrating to tag "
            "tickets manually and still miss the trends that would reduce ticket volume."
        ),
    ),
    Discussion(
        id="disc-005",
        source="mock-reddit",
        author="platform_eng",
        title="Internal developer docs are unreliable",
        body=(
            "Developers lose time because internal docs are out of date and nobody "
            "knows which service owner to ask. Onboarding new engineers takes too long "
            "because tribal knowledge is scattered across Slack, Notion, and repos."
        ),
    ),
]
