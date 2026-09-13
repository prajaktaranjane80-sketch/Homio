from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class VerificationDecision:
    status: str
    passed: bool
    blockers: tuple[str, ...]
    evidence: dict[str, bool]


class VerificationRuntime:
    """Mandatory postflight verification."""

    REQUIRED = (
        "evidence_complete",
        "provenance_valid",
        "state_consistent",
    )

    def verify(
        self,
        *,
        postflight: dict[str, bool],
        expected_state_changed: bool | None = None,
        actual_state_changed: bool | None = None,
    ) -> VerificationDecision:
        blockers = []

        for field in self.REQUIRED:
            if postflight.get(field) is not True:
                blockers.append(
                    f"POSTFLIGHT_{field.upper()}_FAILED"
                )

        if (
            expected_state_changed is True
            and actual_state_changed is not True
        ):
            blockers.append(
                "EXPECTED_STATE_CHANGE_MISSING"
            )

        if (
            expected_state_changed is False
            and actual_state_changed is True
        ):
            blockers.append(
                "UNEXPECTED_STATE_CHANGE"
            )

        return VerificationDecision(
            "VERIFIED" if not blockers else "BLOCKED",
            not blockers,
            tuple(blockers),
            dict(postflight),
        )
