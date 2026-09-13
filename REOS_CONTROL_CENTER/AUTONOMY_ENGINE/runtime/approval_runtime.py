from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ApprovalDecision:
    status: str
    required: bool
    approved: bool
    reasons: tuple[str, ...]


class ApprovalRuntime:
    """Explicit human approval boundary."""

    def evaluate(
        self,
        *,
        risk_level: str,
        irreversible: bool = False,
        explicit_approval: bool = False,
        reasons: tuple[str, ...] = (),
    ) -> ApprovalDecision:
        required = (
            irreversible
            or risk_level in {"HIGH", "CRITICAL"}
        )

        if required and not explicit_approval:
            return ApprovalDecision(
                "BLOCKED",
                True,
                False,
                reasons
                or ("EXPLICIT_HUMAN_APPROVAL_REQUIRED",),
            )

        if required:
            return ApprovalDecision(
                "APPROVED",
                True,
                True,
                reasons,
            )

        return ApprovalDecision(
            "NOT_REQUIRED",
            False,
            True,
            reasons,
        )
