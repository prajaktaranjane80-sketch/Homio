from __future__ import annotations

from dataclasses import dataclass

from ..event_platform.event_domain import EventEnvelope

from .commission_event_validation import (
    CommissionFinancialEventValidationError,
    validate_financial_event,
)


@dataclass(frozen=True, slots=True)
class CommissionFinancialEventIntegrityReport:
    valid: bool
    event_id: str
    tenant_id: str
    event_type: str
    fingerprint: str
    reason: str = ""

    def to_dict(self) -> dict[str, str | bool]:
        return {
            "valid": self.valid,
            "event_id": self.event_id,
            "tenant_id": self.tenant_id,
            "event_type": self.event_type,
            "fingerprint": self.fingerprint,
            "reason": self.reason,
        }


def inspect_financial_event_integrity(
    event: EventEnvelope,
) -> CommissionFinancialEventIntegrityReport:
    try:
        validate_financial_event(event)

        return CommissionFinancialEventIntegrityReport(
            valid=True,
            event_id=str(event.event_id),
            tenant_id=str(event.tenant_id),
            event_type=event.event_type,
            fingerprint=event.immutable_fingerprint,
        )
    except (
        Exception
    ) as exc:
        if isinstance(event, EventEnvelope):
            return CommissionFinancialEventIntegrityReport(
                valid=False,
                event_id=str(event.event_id),
                tenant_id=str(event.tenant_id),
                event_type=event.event_type,
                fingerprint=event.immutable_fingerprint,
                reason=str(exc),
            )

        return CommissionFinancialEventIntegrityReport(
            valid=False,
            event_id="",
            tenant_id="",
            event_type="",
            fingerprint="",
            reason=str(exc),
        )


def assert_financial_event_integrity(
    event: EventEnvelope,
) -> None:
    report = inspect_financial_event_integrity(
        event
    )

    if not report.valid:
        raise CommissionFinancialEventValidationError(
            report.reason
        )


__all__ = [
    "CommissionFinancialEventIntegrityReport",
    "inspect_financial_event_integrity",
    "assert_financial_event_integrity",
]
