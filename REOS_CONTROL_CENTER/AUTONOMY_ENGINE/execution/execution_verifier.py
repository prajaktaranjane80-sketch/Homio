"""
Deterministic execution verification boundary for AUTONOMY_ENGINE.

Authority model
---------------
- REOS_CONTROL_CENTER remains authoritative.
- This verifier never executes mutations.
- This verifier never discovers executors.
- This verifier never mutates controller state.
- This verifier only verifies supplied execution evidence/results.
- Missing verification evidence fails closed.

Design principles
-----------------
- Fail closed.
- Default deny.
- No implicit success.
- No implicit provenance.
- No implicit state consistency.
- No retry.
- No mutation.
- Deterministic verification.
- Evidence is preserved.
- Existing architecture remains untouched.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping


class VerificationStatus(str, Enum):
    """Deterministic verification lifecycle states."""

    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"


class VerificationFailure(str, Enum):
    """Machine-readable verification failure reasons."""

    EXECUTION_NOT_CONFIRMED = "EXECUTION_NOT_CONFIRMED"
    EVIDENCE_INCOMPLETE = "EVIDENCE_INCOMPLETE"
    PROVENANCE_INVALID = "PROVENANCE_INVALID"
    STATE_INCONSISTENT = "STATE_INCONSISTENT"
    RECEIPT_INVALID = "RECEIPT_INVALID"
    ACTION_ID_MISMATCH = "ACTION_ID_MISMATCH"
    RESULT_MISSING = "RESULT_MISSING"


@dataclass(frozen=True)
class VerificationInput:
    """
    Explicit verification envelope.

    Nothing is inferred. Every important verification signal must be
    explicitly supplied by the caller.
    """

    action_id: str

    execution_succeeded: bool = False
    evidence_complete: bool = False
    provenance_valid: bool = False
    state_consistent: bool = False

    result_available: bool = False
    receipt_valid: bool = False

    receipt_action_id: str | None = None

    evidence: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class VerificationResult:
    """Immutable result of one execution verification attempt."""

    status: VerificationStatus
    action_id: str
    verified: bool
    reason: str
    failures: tuple[str, ...] = ()
    evidence: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible representation."""

        return {
            "status": self.status.value,
            "action_id": self.action_id,
            "verified": self.verified,
            "reason": self.reason,
            "failures": list(self.failures),
            "evidence": dict(self.evidence),
        }


class ExecutionVerifier:
    """
    Deterministic post-execution verification boundary.

    This class verifies execution evidence only.

    It cannot:
    - execute an action,
    - retry an action,
    - discover an executor,
    - modify controller state,
    - approve an action,
    - bypass governance,
    - manufacture evidence.
    """

    def __init__(self) -> None:
        self._verified_action_ids: set[str] = set()

    def verify(
        self,
        verification: VerificationInput,
    ) -> VerificationResult:
        """
        Verify one execution attempt.

        All required conditions must be explicitly true.
        """

        action_id = self._safe_action_id(verification.action_id)

        failures: list[str] = []

        if not isinstance(verification.action_id, str):
            failures.append(
                VerificationFailure.ACTION_ID_MISMATCH.value
            )
        elif not verification.action_id:
            failures.append(
                VerificationFailure.ACTION_ID_MISMATCH.value
            )

        if verification.execution_succeeded is not True:
            failures.append(
                VerificationFailure.EXECUTION_NOT_CONFIRMED.value
            )

        if verification.evidence_complete is not True:
            failures.append(
                VerificationFailure.EVIDENCE_INCOMPLETE.value
            )

        if verification.provenance_valid is not True:
            failures.append(
                VerificationFailure.PROVENANCE_INVALID.value
            )

        if verification.state_consistent is not True:
            failures.append(
                VerificationFailure.STATE_INCONSISTENT.value
            )

        if verification.result_available is not True:
            failures.append(
                VerificationFailure.RESULT_MISSING.value
            )

        if verification.receipt_valid is not True:
            failures.append(
                VerificationFailure.RECEIPT_INVALID.value
            )

        if verification.receipt_action_id is not None:
            if verification.receipt_action_id != action_id:
                failures.append(
                    VerificationFailure.ACTION_ID_MISMATCH.value
                )

        evidence = {
            **dict(verification.evidence),
            "verification_attempted": True,
            "verification_passed": not failures,
            "verification_failures": tuple(failures),
        }

        if failures:
            return VerificationResult(
                status=VerificationStatus.REJECTED,
                action_id=action_id,
                verified=False,
                reason="Execution verification failed.",
                failures=tuple(failures),
                evidence=evidence,
            )

        self._verified_action_ids.add(action_id)

        return VerificationResult(
            status=VerificationStatus.VERIFIED,
            action_id=action_id,
            verified=True,
            reason="Execution evidence passed all verification checks.",
            failures=(),
            evidence=evidence,
        )

    def verify_flags(
        self,
        *,
        action_id: str,
        execution_succeeded: bool = False,
        evidence_complete: bool = False,
        provenance_valid: bool = False,
        state_consistent: bool = False,
        result_available: bool = False,
        receipt_valid: bool = False,
        receipt_action_id: str | None = None,
        evidence: Mapping[str, Any] | None = None,
    ) -> VerificationResult:
        """
        Convenience API for callers that already have explicit flags.

        This method performs no inference.
        """

        request = VerificationInput(
            action_id=action_id,
            execution_succeeded=execution_succeeded,
            evidence_complete=evidence_complete,
            provenance_valid=provenance_valid,
            state_consistent=state_consistent,
            result_available=result_available,
            receipt_valid=receipt_valid,
            receipt_action_id=receipt_action_id,
            evidence=dict(evidence or {}),
        )

        return self.verify(request)

    def verified(self, action_id: str) -> bool:
        """Return whether this instance verified an action."""

        return action_id in self._verified_action_ids

    def reset(self) -> None:
        """
        Clear only local verification memory.

        This does not alter persistent controller state.
        """

        self._verified_action_ids.clear()

    @staticmethod
    def _safe_action_id(action_id: Any) -> str:
        """Normalize action_id without raising unexpected exceptions."""

        if isinstance(action_id, str) and action_id:
            return action_id

        return "<invalid-action-id>"