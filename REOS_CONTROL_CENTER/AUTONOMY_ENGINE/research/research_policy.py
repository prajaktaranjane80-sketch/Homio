
from __future__ import annotations

from dataclasses import dataclass

@dataclass(frozen=True)
class ResearchDecision:
    required: bool
    reasons: tuple[str, ...]

CURRENT_FACT_DOMAINS = {
    "software_version",
    "api_behavior",
    "vendor_capability",
    "cloud_service",
    "pricing",
    "security_guidance",
    "standards",
    "support_window",
    "compliance",
}

def research_requirement(topic: str) -> ResearchDecision:
    lowered = topic.lower()
    reasons = [
        domain for domain in CURRENT_FACT_DOMAINS
        if domain.replace("_", " ") in lowered or domain in lowered
    ]
    return ResearchDecision(bool(reasons), tuple(reasons))
