"""CORE-007 Point 12 — Governance Event Integration Contract.

CORE-002 is the canonical event authority.

This module defines:
- trust-signal event,
- fraud-signal event,
- risk-assessment event,
- governance-review event,
- escalation event,
- override event.

This module does NOT:
- publish events,
- implement Kafka,
- implement an outbox,
- implement replay,
- implement transport,
- own event persistence,
- mutate Control Center state.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping
from uuid import UUID, uuid4

from ..contract_primitives import (
    canonicalize,
    deep_freeze,
    fingerprint,
)
from ..event_platform.event_domain import (
    EventEnvelope,
    EventTraceContext,
)


GOVERNANCE_EVENT_SCHEMA_NAME = (
    "REOS.CORE007.GovernanceEvent"
)
GOVERNANCE_EVENT_SCHEMA_VERSION = 1


class GovernanceEventError(ValueError):
    """Base CORE-007 event contract error."""


class GovernanceEventScopeError(
    GovernanceEventError
):
    """Tenant scope violation inside an event."""


class GovernanceEventType(str, Enum):
    TRUST_SIGNAL = (
        "CORE007.TRUST_SIGNAL"
    )

    FRAUD_SIGNAL = (
        "CORE007.FRAUD_SIGNAL"
    )

    RISK_ASSESSMENT = (
        "CORE007.RISK_ASSESSMENT"
    )

    GOVERNANCE_REVIEW = (
        "CORE007.GOVERNANCE_REVIEW"
    )

    ESCALATION = (
        "CORE007.ESCALATION"
    )

    OVERRIDE = (
        "CORE007.OVERRIDE"
    )


_REQUIRED_FIELDS: dict[
    GovernanceEventType,
    tuple[str, ...],
] = {
    GovernanceEventType.TRUST_SIGNAL: (
        "signal_id",
        "subject_id",
        "signal_type",
        "signal_source",
        "signal_version",
        "provenance",
        "evidence_reference",
    ),
    GovernanceEventType.FRAUD_SIGNAL: (
        "fraud_signal_id",
        "subject_id",
        "detection_rule_reference",
        "detection_input_provenance",
        "detection_state",
        "confidence",
    ),
    GovernanceEventType.RISK_ASSESSMENT: (
        "assessment_id",
        "subject_id",
        "assessment_version",
        "risk_factors",
        "assessment_evidence",
        "reproducibility",
    ),
    GovernanceEventType.GOVERNANCE_REVIEW: (
        "review_id",
        "subject_id",
        "review_state",
        "decision_evidence",
        "policy_id",
        "policy_version",
    ),
    GovernanceEventType.ESCALATION: (
        "escalation_id",
        "subject_id",
        "escalation_state",
        "reason",
        "evidence_references",
    ),
    GovernanceEventType.OVERRIDE: (
        "override_id",
        "subject_id",
        "override_reference",
        "override_authorization",
        "review_reference",
        "evidence_references",
    ),
}


@dataclass(frozen=True, slots=True)
class GovernanceEventContract:
    """Immutable CORE-007 event contract."""

    event_type: GovernanceEventType
    tenant_id: UUID
    producer_id: UUID
    correlation_id: UUID
    payload: Mapping[str, Any]

    causation_id: UUID | None = None
    occurred_at: datetime | None = None
    observed_at: datetime | None = None
    trace_context: EventTraceContext | None = None
    idempotency_key: str | None = None
    event_version: int = 1

    def __post_init__(self) -> None:
        for name in (
            "tenant_id",
            "producer_id",
            "correlation_id",
        ):
            if not isinstance(
                getattr(self, name),
                UUID,
            ):
                raise GovernanceEventError(
                    f"{name} must be UUID."
                )

        if (
            self.causation_id is not None
            and not isinstance(
                self.causation_id,
                UUID,
            )
        ):
            raise GovernanceEventError(
                "causation_id must be UUID."
            )

        if (
            isinstance(self.event_version, bool)
            or not isinstance(
                self.event_version,
                int,
            )
            or self.event_version < 1
        ):
            raise GovernanceEventError(
                "event_version must be >= 1."
            )

        if not isinstance(
            self.payload,
            Mapping,
        ):
            raise GovernanceEventError(
                "payload must be a mapping."
            )

        normalized = dict(
            canonicalize(self.payload)
        )

        required = _REQUIRED_FIELDS[
            self.event_type
        ]

        missing = [
            field
            for field in required
            if field not in normalized
        ]

        if missing:
            raise GovernanceEventError(
                "Missing required payload fields: "
                + ", ".join(missing)
            )

        payload_tenant = normalized.get(
            "tenant_id"
        )

        if (
            payload_tenant is not None
            and str(payload_tenant)
            != str(self.tenant_id)
        ):
            raise GovernanceEventScopeError(
                "payload tenant_id does not "
                "match event tenant_id."
            )

        object.__setattr__(
            self,
            "payload",
            deep_freeze(
                normalized,
                field_name="payload",
            ),
        )

        if self.idempotency_key is not None:
            if (
                not isinstance(
                    self.idempotency_key,
                    str,
                )
                or not self.idempotency_key.strip()
            ):
                raise GovernanceEventError(
                    "idempotency_key cannot be empty."
                )

            object.__setattr__(
                self,
                "idempotency_key",
                self.idempotency_key.strip(),
            )

    @property
    def contract_key(self) -> str:
        return (
            f"{GOVERNANCE_EVENT_SCHEMA_NAME}:"
            f"{GOVERNANCE_EVENT_SCHEMA_VERSION}:"
            f"{self.event_type.value}"
        )

    @property
    def payload_fingerprint(self) -> str:
        return fingerprint(
            canonicalize(self.payload)
        )

    @property
    def idempotency_identity(
        self,
    ) -> tuple[UUID, str, str]:
        return (
            self.tenant_id,
            self.event_type.value,
            (
                self.idempotency_key
                or self.payload_fingerprint
            ),
        )

    def to_event_envelope(
        self,
    ) -> EventEnvelope:
        occurred = (
            self.occurred_at
            or datetime.now(timezone.utc)
        )

        observed = (
            self.observed_at
            or occurred
        )

        if (
            observed.tzinfo is None
            or observed.utcoffset() is None
        ):
            raise GovernanceEventError(
                "observed_at must be timezone-aware."
            )

        if (
            occurred.tzinfo is None
            or occurred.utcoffset() is None
        ):
            raise GovernanceEventError(
                "occurred_at must be timezone-aware."
            )

        occurred = occurred.astimezone(
            timezone.utc
        )
        observed = observed.astimezone(
            timezone.utc
        )

        return EventEnvelope(
            event_id=uuid4(),
            event_type=self.event_type.value,
            schema_name=(
                GOVERNANCE_EVENT_SCHEMA_NAME
            ),
            schema_version=(
                GOVERNANCE_EVENT_SCHEMA_VERSION
            ),
            event_version=self.event_version,
            tenant_id=self.tenant_id,
            producer_id=self.producer_id,
            correlation_id=self.correlation_id,
            causation_id=self.causation_id,
            occurred_at=occurred,
            observed_at=observed,
            payload=self.payload,
            trace_context=self.trace_context,
            idempotency_key=(
                self.idempotency_key
                or self.payload_fingerprint
            ),
            metadata={
                "core": "CORE-007",
                "contract_key": self.contract_key,
                "payload_fingerprint": (
                    self.payload_fingerprint
                ),
            },
        )

    def to_dict(
        self,
    ) -> dict[str, Any]:
        return {
            "event_type": (
                self.event_type.value
            ),
            "schema_name": (
                GOVERNANCE_EVENT_SCHEMA_NAME
            ),
            "schema_version": (
                GOVERNANCE_EVENT_SCHEMA_VERSION
            ),
            "event_version": self.event_version,
            "tenant_id": str(
                self.tenant_id
            ),
            "producer_id": str(
                self.producer_id
            ),
            "correlation_id": str(
                self.correlation_id
            ),
            "causation_id": (
                str(self.causation_id)
                if self.causation_id is not None
                else None
            ),
            "payload": canonicalize(
                self.payload
            ),
            "payload_fingerprint": (
                self.payload_fingerprint
            ),
            "contract_key": self.contract_key,
            "idempotency_identity": [
                str(self.idempotency_identity[0]),
                self.idempotency_identity[1],
                self.idempotency_identity[2],
            ],
        }


def build_governance_event(
    *,
    event_type: GovernanceEventType,
    tenant_id: UUID,
    producer_id: UUID,
    correlation_id: UUID,
    payload: Mapping[str, Any],
    causation_id: UUID | None = None,
    occurred_at: datetime | None = None,
    observed_at: datetime | None = None,
    trace_context: EventTraceContext | None = None,
    idempotency_key: str | None = None,
    event_version: int = 1,
) -> GovernanceEventContract:
    return GovernanceEventContract(
        event_type=event_type,
        tenant_id=tenant_id,
        producer_id=producer_id,
        correlation_id=correlation_id,
        payload=payload,
        causation_id=causation_id,
        occurred_at=occurred_at,
        observed_at=observed_at,
        trace_context=trace_context,
        idempotency_key=idempotency_key,
        event_version=event_version,
    )


def build_trust_signal_event(
    **kwargs: Any,
) -> GovernanceEventContract:
    return build_governance_event(
        event_type=(
            GovernanceEventType.TRUST_SIGNAL
        ),
        **kwargs,
    )


def build_fraud_signal_event(
    **kwargs: Any,
) -> GovernanceEventContract:
    return build_governance_event(
        event_type=(
            GovernanceEventType.FRAUD_SIGNAL
        ),
        **kwargs,
    )


def build_risk_assessment_event(
    **kwargs: Any,
) -> GovernanceEventContract:
    return build_governance_event(
        event_type=(
            GovernanceEventType.RISK_ASSESSMENT
        ),
        **kwargs,
    )


def build_governance_review_event(
    **kwargs: Any,
) -> GovernanceEventContract:
    return build_governance_event(
        event_type=(
            GovernanceEventType.GOVERNANCE_REVIEW
        ),
        **kwargs,
    )


def build_escalation_event(
    **kwargs: Any,
) -> GovernanceEventContract:
    return build_governance_event(
        event_type=(
            GovernanceEventType.ESCALATION
        ),
        **kwargs,
    )


def build_override_event(
    **kwargs: Any,
) -> GovernanceEventContract:
    return build_governance_event(
        event_type=(
            GovernanceEventType.OVERRIDE
        ),
        **kwargs,
    )


__all__ = [
    "GOVERNANCE_EVENT_SCHEMA_NAME",
    "GOVERNANCE_EVENT_SCHEMA_VERSION",
    "GovernanceEventError",
    "GovernanceEventScopeError",
    "GovernanceEventType",
    "GovernanceEventContract",
    "build_governance_event",
    "build_trust_signal_event",
    "build_fraud_signal_event",
    "build_risk_assessment_event",
    "build_governance_review_event",
    "build_escalation_event",
    "build_override_event",
]
