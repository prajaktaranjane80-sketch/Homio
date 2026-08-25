"""
Deterministic execution audit boundary for AUTONOMY_ENGINE.

Observational only:
- Never authorizes execution.
- Never executes mutations.
- Never discovers executors.
- Never mutates controller state.
- Preserves execution evidence.
- Fail-closed validation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Mapping


class AuditStatus(str, Enum):
    """Lifecycle status of an audit record."""

    RECORDED = "RECORDED"
    REJECTED = "REJECTED"
    FAILED = "FAILED"


class AuditReason(str, Enum):
    """Machine-readable audit outcomes."""

    RECORDED = "RECORDED"
    INVALID_ACTION_ID = "INVALID_ACTION_ID"
    INVALID_EVENT_TYPE = "INVALID_EVENT_TYPE"
    INVALID_STATUS = "INVALID_STATUS"
    INVALID_SEQUENCE = "INVALID_SEQUENCE"
    SINK_INVALID = "SINK_INVALID"
    SINK_FAILED = "SINK_FAILED"


@dataclass(frozen=True)
class AuditRecord:
    """Immutable observational execution record."""

    sequence: int
    action_id: str
    event_type: str
    status: AuditStatus
    execution_attempted: bool
    execution_succeeded: bool
    evidence: Mapping[str, Any] = field(default_factory=dict)

    @property
    def successful(self) -> bool:
        """Return whether this record represents successful execution."""

        return (
            self.status is AuditStatus.RECORDED
            and self.execution_attempted is True
            and self.execution_succeeded is True
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible representation."""

        return {
            "sequence": self.sequence,
            "action_id": self.action_id,
            "event_type": self.event_type,
            "status": self.status.value,
            "execution_attempted": self.execution_attempted,
            "execution_succeeded": self.execution_succeeded,
            "successful": self.successful,
            "evidence": dict(self.evidence),
        }


@dataclass(frozen=True)
class AuditDecision:
    """Immutable result of audit validation/recording."""

    accepted: bool
    status: AuditStatus
    reason: AuditReason
    failures: tuple[str, ...] = ()
    record: AuditRecord | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible representation."""

        return {
            "accepted": self.accepted,
            "status": self.status.value,
            "reason": self.reason.value,
            "failures": list(self.failures),
            "record": (
                self.record.to_dict()
                if self.record is not None
                else None
            ),
        }


AuditSink = Callable[[AuditRecord], Any]


class ExecutionAudit:
    """
    Passive deterministic execution audit recorder.

    This component records evidence only. It has no authority over execution.
    """

    def __init__(self) -> None:
        self._next_sequence = 1
        self._records: list[AuditRecord] = []

    def create_record(
        self,
        *,
        action_id: str,
        event_type: str,
        status: AuditStatus,
        execution_attempted: bool,
        execution_succeeded: bool,
        evidence: Mapping[str, Any] | None = None,
    ) -> AuditRecord:
        """Create an immutable audit record without storing it."""

        return AuditRecord(
            sequence=self._next_sequence,
            action_id=action_id if isinstance(action_id, str) else "",
            event_type=event_type if isinstance(event_type, str) else "",
            status=(
                status
                if isinstance(status, AuditStatus)
                else AuditStatus.REJECTED
            ),
            execution_attempted=execution_attempted is True,
            execution_succeeded=execution_succeeded is True,
            evidence=dict(evidence or {}),
        )

    def record(
        self,
        *,
        action_id: str,
        event_type: str,
        status: AuditStatus,
        execution_attempted: bool,
        execution_succeeded: bool,
        evidence: Mapping[str, Any] | None = None,
        sink: AuditSink | None = None,
    ) -> AuditDecision:
        """
        Validate and commit one audit record.

        A supplied sink is invoked only after validation.
        The sink is never discovered or invented.
        """

        record = self.create_record(
            action_id=action_id,
            event_type=event_type,
            status=status,
            execution_attempted=execution_attempted,
            execution_succeeded=execution_succeeded,
            evidence=evidence,
        )

        validation = self.validate(record)

        if not validation.accepted:
            return validation

        if sink is not None and not callable(sink):
            return AuditDecision(
                accepted=False,
                status=AuditStatus.REJECTED,
                reason=AuditReason.SINK_INVALID,
                failures=("sink_not_callable",),
                record=record,
            )

        if sink is not None:
            try:
                sink(record)
            except Exception as exc:
                return AuditDecision(
                    accepted=False,
                    status=AuditStatus.FAILED,
                    reason=AuditReason.SINK_FAILED,
                    failures=(
                        f"sink_exception:{type(exc).__name__}",
                    ),
                    record=record,
                )

        self._records.append(record)
        self._next_sequence += 1

        return AuditDecision(
            accepted=True,
            status=AuditStatus.RECORDED,
            reason=AuditReason.RECORDED,
            record=record,
        )

    @staticmethod
    def validate(record: AuditRecord) -> AuditDecision:
        """Validate an audit record without storing or executing anything."""

        if not isinstance(record, AuditRecord):
            return AuditDecision(
                accepted=False,
                status=AuditStatus.REJECTED,
                reason=AuditReason.INVALID_ACTION_ID,
                failures=("record_type",),
            )

        failures: list[str] = []

        if not isinstance(record.action_id, str) or not record.action_id.strip():
            failures.append("action_id")

        if not isinstance(record.event_type, str) or not record.event_type.strip():
            failures.append("event_type")

        if not isinstance(record.status, AuditStatus):
            failures.append("status")

        if not isinstance(record.sequence, int) or record.sequence < 1:
            failures.append("sequence")

        if record.execution_succeeded is True and (
            record.execution_attempted is not True
        ):
            failures.append("success_without_attempt")

        if record.status is AuditStatus.RECORDED:
            if record.execution_succeeded is not True:
                failures.append("recorded_without_success")

        if record.status is AuditStatus.FAILED:
            if record.execution_succeeded is True:
                failures.append("failed_with_success")

        if record.status is AuditStatus.REJECTED:
            if record.execution_succeeded is True:
                failures.append("rejected_with_success")

        if failures:
            reason = AuditReason.INVALID_ACTION_ID

            if "event_type" in failures:
                reason = AuditReason.INVALID_EVENT_TYPE
            elif "status" in failures:
                reason = AuditReason.INVALID_STATUS
            elif "sequence" in failures:
                reason = AuditReason.INVALID_SEQUENCE

            return AuditDecision(
                accepted=False,
                status=AuditStatus.REJECTED,
                reason=reason,
                failures=tuple(failures),
                record=record,
            )

        return AuditDecision(
            accepted=True,
            status=AuditStatus.RECORDED,
            reason=AuditReason.RECORDED,
            record=record,
        )

    def records(self) -> tuple[AuditRecord, ...]:
        """Return an immutable snapshot of local audit records."""

        return tuple(self._records)

    def last_sequence(self) -> int:
        """Return the last committed sequence number."""

        if not self._records:
            return 0

        return self._records[-1].sequence

    def count(self) -> int:
        """Return the number of committed records."""

        return len(self._records)

    def reset(self) -> None:
        """
        Clear only local audit memory.

        This does not clear controller or persistent audit state.
        """

        self._records.clear()
        self._next_sequence = 1


def create_audit_record(
    *,
    action_id: str,
    event_type: str,
    status: AuditStatus,
    execution_attempted: bool,
    execution_succeeded: bool,
    evidence: Mapping[str, Any] | None = None,
) -> AuditRecord:
    """Create a standalone immutable audit record."""

    return AuditRecord(
        sequence=1,
        action_id=action_id if isinstance(action_id, str) else "",
        event_type=event_type if isinstance(event_type, str) else "",
        status=(
            status
            if isinstance(status, AuditStatus)
            else AuditStatus.REJECTED
        ),
        execution_attempted=execution_attempted is True,
        execution_succeeded=execution_succeeded is True,
        evidence=dict(evidence or {}),
    )


def validate_audit_record(record: AuditRecord) -> AuditDecision:
    """Stateless audit validation helper."""

    return ExecutionAudit.validate(record)
