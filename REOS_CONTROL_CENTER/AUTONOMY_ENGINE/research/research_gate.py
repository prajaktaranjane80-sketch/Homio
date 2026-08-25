"""Research gate for V6 AUTONOMY_ENGINE additions.

Provides a small, deterministic gate for deciding whether an autonomous
operation is permitted to proceed based on research requirements and
available evidence.

This module is additive. It does not replace the existing research
policy, cache, or source-policy components.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable


@dataclass(frozen=True)
class ResearchRequirement:
    """Defines the research evidence required before an action proceeds."""

    required: bool = False
    minimum_sources: int = 0
    required_topics: tuple[str, ...] = ()


@dataclass(frozen=True)
class ResearchEvidence:
    """Represents normalized research evidence available to the gate."""

    sources: tuple[str, ...] = ()
    topics: tuple[str, ...] = ()
    verified: bool = False
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class ResearchGateResult:
    """Deterministic result returned by the research gate."""

    allowed: bool
    reason: str
    source_count: int
    missing_topics: tuple[str, ...] = ()


class ResearchGate:
    """Evaluate whether available research satisfies a requirement."""

    def evaluate(
        self,
        requirement: ResearchRequirement,
        evidence: ResearchEvidence | None = None,
    ) -> ResearchGateResult:
        if not requirement.required:
            return ResearchGateResult(
                allowed=True,
                reason="research_not_required",
                source_count=0 if evidence is None else len(evidence.sources),
            )

        if evidence is None:
            return ResearchGateResult(
                allowed=False,
                reason="research_evidence_missing",
                source_count=0,
            )

        if not evidence.verified:
            return ResearchGateResult(
                allowed=False,
                reason="research_evidence_unverified",
                source_count=len(evidence.sources),
            )

        source_count = len(evidence.sources)

        if source_count < requirement.minimum_sources:
            return ResearchGateResult(
                allowed=False,
                reason="minimum_source_requirement_not_met",
                source_count=source_count,
            )

        available_topics = {topic.strip().lower() for topic in evidence.topics}
        missing_topics = tuple(
            topic
            for topic in requirement.required_topics
            if topic.strip().lower() not in available_topics
        )

        if missing_topics:
            return ResearchGateResult(
                allowed=False,
                reason="required_research_topics_missing",
                source_count=source_count,
                missing_topics=missing_topics,
            )

        return ResearchGateResult(
            allowed=True,
            reason="research_requirements_satisfied",
            source_count=source_count,
        )


def normalize_sources(sources: Iterable[str]) -> tuple[str, ...]:
    """Return deterministic, de-duplicated source identifiers."""

    normalized: list[str] = []
    seen: set[str] = set()

    for source in sources:
        value = str(source).strip()
        if not value or value in seen:
            continue
        seen.add(value)
        normalized.append(value)

    return tuple(normalized)