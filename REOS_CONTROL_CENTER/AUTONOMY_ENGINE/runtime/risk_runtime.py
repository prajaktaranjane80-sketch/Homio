from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RiskDecision:
    level: str
    mutation_allowed: bool
    approval_required: bool
    blockers: tuple[str, ...]
    reasons: tuple[str, ...]


class RiskRuntime:
    """Conservative risk classification."""

    CRITICAL_TERMS = frozenset(
        {
            "delete",
            "destroy",
            "payment",
            "financial",
            "commission",
            "credential",
            "privacy",
            "security",
            "production",
            "legal",
            "irreversible",
            "tenant",
        }
    )

    MEDIUM_TERMS = frozenset(
        {
            "database",
            "schema",
            "migration",
            "authentication",
            "authorization",
            "lead",
            "deal",
            "inventory",
        }
    )

    def classify(
        self,
        description: str,
        *,
        mutation: bool = False,
    ) -> RiskDecision:
        text = description.lower()

        critical = sorted(
            term
            for term in self.CRITICAL_TERMS
            if term in text
        )

        medium = sorted(
            term
            for term in self.MEDIUM_TERMS
            if term in text
        )

        if critical:
            return RiskDecision(
                "CRITICAL",
                False,
                True,
                ("HUMAN_APPROVAL_REQUIRED",),
                tuple(critical),
            )

        if medium or mutation:
            return RiskDecision(
                "MEDIUM",
                False,
                False,
                (),
                tuple(medium)
                or ("MUTATION_REQUIRES_GUARDED_EXECUTION",),
            )

        return RiskDecision(
            "LOW",
            False,
            False,
            (),
            ("READ_ONLY_INSPECTION",),
        )
