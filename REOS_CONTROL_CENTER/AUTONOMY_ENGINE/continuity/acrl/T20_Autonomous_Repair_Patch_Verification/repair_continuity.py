from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .repair_models import (
    RepairDecision,
    RepairResult,
)
from .repair_identity import fingerprint


class RepairContinuityDecision(str, Enum):
    INVALIDATE_REQUIRED = "INVALIDATE_REQUIRED"
    REFRESH_REQUIRED = "REFRESH_REQUIRED"
    BLOCKED = "BLOCKED"


class RepairContinuityError(RuntimeError):
    """Base T20 repair-continuity error."""


class RepairContinuityValidationError(
    RepairContinuityError
):
    """Raised when repair-continuity input is invalid."""


@dataclass(frozen=True, slots=True)
class RepairContinuitySignal:
    """
    Machine-readable signal emitted after T20 repair.

    T20 does not reconstruct context itself.
    It explicitly tells the continuity layer whether
    previously reconstructed context may still be used.
    """

    schema_version: str
    repair_id: str
    decision: RepairContinuityDecision
    previous_context_fingerprint: str
    repair_result_fingerprint: str
    final_tree_fingerprint: str
    reason: str
    requires_context_refresh: bool
    signal_fingerprint: str

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "repair_id": self.repair_id,
            "decision": self.decision.value,
            "previous_context_fingerprint": (
                self.previous_context_fingerprint
            ),
            "repair_result_fingerprint": (
                self.repair_result_fingerprint
            ),
            "final_tree_fingerprint": (
                self.final_tree_fingerprint
            ),
            "reason": self.reason,
            "requires_context_refresh": (
                self.requires_context_refresh
            ),
            "signal_fingerprint": self.signal_fingerprint,
        }

    def verify_integrity(self) -> bool:
        payload = {
            "schema_version": self.schema_version,
            "repair_id": self.repair_id,
            "decision": self.decision.value,
            "previous_context_fingerprint": (
                self.previous_context_fingerprint
            ),
            "repair_result_fingerprint": (
                self.repair_result_fingerprint
            ),
            "final_tree_fingerprint": (
                self.final_tree_fingerprint
            ),
            "reason": self.reason,
            "requires_context_refresh": (
                self.requires_context_refresh
            ),
        }

        return (
            fingerprint(payload)
            == self.signal_fingerprint
        )


def build_repair_continuity_signal(
    *,
    result: RepairResult,
    previous_context_fingerprint: str,
) -> RepairContinuitySignal:
    """
    Convert a T20 repair result into a continuity decision.

    T20 never silently reuses pre-repair context.
    A verified repair always requires the previous
    reconstructed context to be refreshed.
    """

    if not result.repair_id.strip():
        raise RepairContinuityValidationError(
            "Repair ID is required."
        )

    if (
        len(previous_context_fingerprint) != 64
        or any(
            character
            not in "0123456789abcdef"
            for character
            in previous_context_fingerprint
        )
    ):
        raise RepairContinuityValidationError(
            "Invalid previous context fingerprint."
        )

    if (
        result.decision
        is RepairDecision.VERIFIED
    ):
        decision = (
            RepairContinuityDecision.REFRESH_REQUIRED
        )
        reason = (
            "Verified repair changed the effective "
            "workspace state; previously reconstructed "
            "context must be refreshed before continuation."
        )
        requires_refresh = True

    elif result.decision in {
        RepairDecision.REPAIR_APPLIED,
        RepairDecision.ROLLED_BACK,
        RepairDecision.BLOCKED,
        RepairDecision.FAIL_CLOSED,
        RepairDecision.REJECTED,
    }:
        decision = (
            RepairContinuityDecision.INVALIDATE_REQUIRED
        )
        reason = (
            "Repair did not establish a verified final state; "
            "previous reconstructed context must not be reused."
        )
        requires_refresh = True

    else:
        raise RepairContinuityValidationError(
            "Unsupported repair decision for continuity."
        )

    result_payload = result.to_dict()

    signal_payload = {
        "schema_version": "1.0",
        "repair_id": result.repair_id,
        "decision": decision.value,
        "previous_context_fingerprint": (
            previous_context_fingerprint
        ),
        "repair_result_fingerprint": fingerprint(
            result_payload
        ),
        "final_tree_fingerprint": (
            result.final_tree_fingerprint
        ),
        "reason": reason,
        "requires_context_refresh": requires_refresh,
    }

    return RepairContinuitySignal(
        schema_version="1.0",
        repair_id=result.repair_id,
        decision=decision,
        previous_context_fingerprint=(
            previous_context_fingerprint
        ),
        repair_result_fingerprint=(
            signal_payload[
                "repair_result_fingerprint"
            ]
        ),
        final_tree_fingerprint=(
            result.final_tree_fingerprint
        ),
        reason=reason,
        requires_context_refresh=requires_refresh,
        signal_fingerprint=fingerprint(
            signal_payload
        ),
    )


__all__ = [
    "RepairContinuityDecision",
    "RepairContinuityError",
    "RepairContinuityValidationError",
    "RepairContinuitySignal",
    "build_repair_continuity_signal",
]
