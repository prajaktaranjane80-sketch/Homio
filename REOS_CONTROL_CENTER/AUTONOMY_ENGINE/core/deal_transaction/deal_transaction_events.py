from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from hashlib import sha256
import json
from types import MappingProxyType
from typing import Any, Mapping

from .deal_contract import DealStatus
from .deal_transaction_milestones import (
    DealTransactionMilestone,
)
from .deal_offer_negotiation import (
    DealNegotiation,
    DealNegotiationStatus,
    DealOffer,
    DealOfferStatus,
)
from .deal_ownership_integration import (
    DealOwnershipBinding,
)
from .deal_evidence_audit import (
    DealAuditEntry,
    DealEvidenceReference,
)


CORE002_SCHEMA_NAME = "reos.deal.transaction"
CORE002_SCHEMA_VERSION = 1
CORE002_EVENT_VERSION = 1
CORE006_PRODUCER = "CORE-006"
DEAL_EVENT_SCHEMA_VERSION = "1.0"

TRANSACTION_STATUSES = frozenset(
    {
        DealStatus.BOOKING_PENDING,
        DealStatus.BOOKED,
        DealStatus.AGREEMENT_PENDING,
        DealStatus.AGREED,
        DealStatus.REGISTRATION_PENDING,
        DealStatus.REGISTERED,
        DealStatus.COMPLETION_PENDING,
        DealStatus.COMPLETED,
    }
)


class DealTransactionEventError(ValueError):
    """Base CORE-006 transaction-event error."""


class DealTransactionEventScopeError(
    DealTransactionEventError
):
    """Raised when an event crosses Deal or tenant scope."""


class DealTransactionEventConflictError(
    DealTransactionEventError
):
    """Raised when one event identity carries conflicting data."""


class DealTransactionEventType(str, Enum):
    DEAL_CREATED = "DEAL_CREATED"
    DEAL_STATE_CHANGED = "DEAL_STATE_CHANGED"
    OFFER_CREATED = "OFFER_CREATED"
    OFFER_STATE_CHANGED = "OFFER_STATE_CHANGED"
    NEGOTIATION_STATE_CHANGED = "NEGOTIATION_STATE_CHANGED"
    BOOKING_STATE_CHANGED = "BOOKING_STATE_CHANGED"
    MILESTONE_COMPLETED = "MILESTONE_COMPLETED"
    OWNERSHIP_REFERENCE_CHANGED = (
        "OWNERSHIP_REFERENCE_CHANGED"
    )
    EVIDENCE_ATTACHED = "EVIDENCE_ATTACHED"
    AUDIT_RECORDED = "AUDIT_RECORDED"


def _require_text(
    value: Any,
    field_name: str,
) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DealTransactionEventError(
            f"{field_name} must be non-empty text."
        )

    return value.strip()


def _canonicalize(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value

    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise DealTransactionEventError(
                "datetime payload values must be timezone-aware."
            )

        return value.isoformat()

    if isinstance(value, Mapping):
        return {
            str(key): _canonicalize(value[key])
            for key in sorted(
                value,
                key=lambda item: str(item),
            )
        }

    if isinstance(value, (tuple, list)):
        return [
            _canonicalize(item)
            for item in value
        ]

    if isinstance(
        value,
        (str, int, float, bool),
    ) or value is None:
        return value

    if hasattr(value, "to_dict"):
        return _canonicalize(
            value.to_dict()
        )

    raise DealTransactionEventError(
        "Unsupported event payload type: "
        f"{type(value).__name__}"
    )


def _canonical_json(
    value: Mapping[str, Any],
) -> str:
    return json.dumps(
        _canonicalize(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _event_id(
    *parts: object,
) -> str:
    return ":".join(
        str(part)
        for part in parts
    )


def _state_event_type(
    to_status: DealStatus,
) -> DealTransactionEventType:
    if to_status in TRANSACTION_STATUSES:
        return DealTransactionEventType.BOOKING_STATE_CHANGED

    return DealTransactionEventType.DEAL_STATE_CHANGED


@dataclass(frozen=True)
class DealTransactionEvent:
    """
    Immutable CORE-006 business-event contract.

    CORE-006 owns:
    - which Deal/Transaction business event occurred
    - event payload
    - Deal and tenant identity
    - business idempotency identity

    CORE-002 owns:
    - canonical EventEnvelope
    - event contracts/registry
    - delivery
    - transport
    - retry/replay
    - tenant security boundary
    """

    event_id: str
    event_type: DealTransactionEventType
    deal_id: str
    tenant_id: str
    deal_version: int
    occurred_at: str

    payload: Mapping[str, Any] = field(
        default_factory=dict
    )

    source_of_truth: str = "deal"
    schema_version: str = DEAL_EVENT_SCHEMA_VERSION
    idempotency_key: str = ""

    correlation_id: str = ""
    causation_id: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "event_id",
            _require_text(
                self.event_id,
                "event_id",
            ),
        )

        object.__setattr__(
            self,
            "deal_id",
            _require_text(
                self.deal_id,
                "deal_id",
            ),
        )

        object.__setattr__(
            self,
            "tenant_id",
            _require_text(
                self.tenant_id,
                "tenant_id",
            ),
        )

        if (
            isinstance(
                self.deal_version,
                bool,
            )
            or not isinstance(
                self.deal_version,
                int,
            )
            or self.deal_version < 1
        ):
            raise DealTransactionEventError(
                "deal_version must be an integer >= 1."
            )

        object.__setattr__(
            self,
            "event_type",
            DealTransactionEventType(
                self.event_type
            ),
        )

        object.__setattr__(
            self,
            "occurred_at",
            _require_text(
                self.occurred_at,
                "occurred_at",
            ),
        )

        object.__setattr__(
            self,
            "source_of_truth",
            _require_text(
                self.source_of_truth,
                "source_of_truth",
            ),
        )

        if self.source_of_truth != "deal":
            raise DealTransactionEventError(
                "source_of_truth must remain 'deal'."
            )

        if self.schema_version != (
            DEAL_EVENT_SCHEMA_VERSION
        ):
            raise DealTransactionEventError(
                "Unsupported Deal transaction event schema version."
            )

        if not isinstance(
            self.payload,
            Mapping,
        ):
            raise DealTransactionEventError(
                "payload must be a mapping."
            )

        normalized_payload = MappingProxyType(
            _canonicalize(
                dict(self.payload)
            )
        )

        object.__setattr__(
            self,
            "payload",
            normalized_payload,
        )

        idempotency_key = (
            self.idempotency_key
            or self.event_id
        )

        if idempotency_key != self.event_id:
            raise DealTransactionEventError(
                "idempotency_key must equal event_id."
            )

        object.__setattr__(
            self,
            "idempotency_key",
            idempotency_key,
        )

        correlation_id = (
            self.correlation_id
            or self.event_id
        )

        object.__setattr__(
            self,
            "correlation_id",
            _require_text(
                correlation_id,
                "correlation_id",
            ),
        )

        if self.causation_id is not None:
            object.__setattr__(
                self,
                "causation_id",
                _require_text(
                    self.causation_id,
                    "causation_id",
                ),
            )

    @property
    def identity_key(self) -> tuple[
        str,
        str,
        str,
    ]:
        return (
            self.tenant_id,
            self.deal_id,
            self.idempotency_key,
        )

    @property
    def payload_hash(self) -> str:
        return sha256(
            _canonical_json(
                dict(self.payload)
            ).encode("utf-8")
        ).hexdigest()

    def assert_scope(
        self,
        *,
        deal_id: str,
        tenant_id: str,
    ) -> None:
        if (
            self.deal_id != deal_id
            or self.tenant_id != tenant_id
        ):
            raise DealTransactionEventScopeError(
                "Event crosses Deal or tenant scope."
            )

    def assert_compatible(
        self,
        other: DealTransactionEvent,
    ) -> None:
        if not isinstance(
            other,
            DealTransactionEvent,
        ):
            raise TypeError(
                "other must be DealTransactionEvent."
            )

        if self.identity_key != other.identity_key:
            raise DealTransactionEventConflictError(
                "Event identities differ."
            )

        if self.to_dict() != other.to_dict():
            raise DealTransactionEventConflictError(
                "Same event identity has conflicting data."
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "schema_version": self.schema_version,
            "source_of_truth": self.source_of_truth,
            "deal_id": self.deal_id,
            "tenant_id": self.tenant_id,
            "deal_version": self.deal_version,
            "occurred_at": self.occurred_at,
            "payload": dict(self.payload),
            "payload_hash": self.payload_hash,
            "idempotency_key": self.idempotency_key,
            "correlation_id": self.correlation_id,
            "causation_id": self.causation_id,
        }

    def to_core002_payload(
        self,
    ) -> dict[str, Any]:
        """
        Canonical business-event representation consumed
        by the existing CORE-002 Event Platform boundary.

        This method does not publish, persist, transport,
        retry or replay anything.
        """

        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "schema_name": CORE002_SCHEMA_NAME,
            "schema_version": CORE002_SCHEMA_VERSION,
            "event_version": CORE002_EVENT_VERSION,
            "tenant_id": self.tenant_id,
            "producer": CORE006_PRODUCER,
            "deal_id": self.deal_id,
            "deal_version": self.deal_version,
            "occurred_at": self.occurred_at,
            "correlation_id": self.correlation_id,
            "causation_id": self.causation_id,
            "idempotency_key": self.idempotency_key,
            "payload": dict(self.payload),
            "payload_hash": self.payload_hash,
        }

    @classmethod
    def from_milestone(
        cls,
        milestone: DealTransactionMilestone,
        *,
        event_type: DealTransactionEventType = (
            DealTransactionEventType.MILESTONE_COMPLETED
        ),
        correlation_id: str | None = None,
        causation_id: str | None = None,
    ) -> "DealTransactionEvent":
        if event_type is not (
            DealTransactionEventType.MILESTONE_COMPLETED
        ):
            raise DealTransactionEventError(
                "Milestone events must use MILESTONE_COMPLETED."
            )

        return cls(
            event_id=milestone.milestone_id,
            event_type=event_type,
            deal_id=milestone.deal_id,
            tenant_id=milestone.tenant_id,
            deal_version=milestone.deal_version,
            occurred_at=milestone.occurred_at.isoformat(),
            payload={
                "milestone_id": milestone.milestone_id,
                "from_status": (
                    milestone.from_status.value
                ),
                "to_status": (
                    milestone.to_status.value
                ),
                "sequence": milestone.sequence,
                "reference_id": milestone.reference_id,
                "evidence_required": (
                    milestone.evidence_required
                ),
            },
            correlation_id=(
                correlation_id
                or milestone.milestone_id
            ),
            causation_id=causation_id,
        )


def transaction_event_from_deal_created(
    *,
    deal_id: str,
    tenant_id: str,
    deal_version: int,
    occurred_at: str,
    correlation_id: str | None = None,
    causation_id: str | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> DealTransactionEvent:
    event_id = _event_id(
        "deal",
        deal_id,
        "v",
        deal_version,
        "created",
    )

    return DealTransactionEvent(
        event_id=event_id,
        event_type=(
            DealTransactionEventType.DEAL_CREATED
        ),
        deal_id=deal_id,
        tenant_id=tenant_id,
        deal_version=deal_version,
        occurred_at=occurred_at,
        payload={
            "metadata": dict(metadata or {}),
        },
        correlation_id=(
            correlation_id or event_id
        ),
        causation_id=causation_id,
    )


def transaction_event_from_deal_state(
    *,
    deal_id: str,
    tenant_id: str,
    deal_version: int,
    occurred_at: str,
    from_status: DealStatus,
    to_status: DealStatus,
    correlation_id: str | None = None,
    causation_id: str | None = None,
) -> DealTransactionEvent:
    from_status = DealStatus(from_status)
    to_status = DealStatus(to_status)

    event_type = _state_event_type(
        to_status
    )

    event_id = _event_id(
        "deal",
        deal_id,
        "v",
        deal_version,
        event_type.value,
        to_status.value,
    )

    return DealTransactionEvent(
        event_id=event_id,
        event_type=event_type,
        deal_id=deal_id,
        tenant_id=tenant_id,
        deal_version=deal_version,
        occurred_at=occurred_at,
        payload={
            "from_status": from_status.value,
            "to_status": to_status.value,
        },
        correlation_id=(
            correlation_id or event_id
        ),
        causation_id=causation_id,
    )


def transaction_event_from_offer_created(
    offer: DealOffer,
    *,
    correlation_id: str | None = None,
    causation_id: str | None = None,
) -> DealTransactionEvent:
    if not isinstance(
        offer,
        DealOffer,
    ):
        raise TypeError(
            "offer must be DealOffer."
        )

    event_id = _event_id(
        "offer",
        offer.offer_id,
        "created",
        "v",
        offer.version,
    )

    return DealTransactionEvent(
        event_id=event_id,
        event_type=(
            DealTransactionEventType.OFFER_CREATED
        ),
        deal_id=offer.deal_id,
        tenant_id=offer.tenant_id,
        deal_version=offer.version,
        occurred_at=offer.created_at,
        payload={
            "offer": offer.to_dict(),
        },
        correlation_id=(
            correlation_id or event_id
        ),
        causation_id=causation_id,
    )


def transaction_event_from_offer_state(
    *,
    offer: DealOffer,
    from_status: DealOfferStatus,
    to_status: DealOfferStatus,
    deal_version: int,
    occurred_at: str,
    correlation_id: str | None = None,
    causation_id: str | None = None,
) -> DealTransactionEvent:
    if not isinstance(
        offer,
        DealOffer,
    ):
        raise TypeError(
            "offer must be DealOffer."
        )

    from_status = DealOfferStatus(
        from_status
    )
    to_status = DealOfferStatus(
        to_status
    )

    event_id = _event_id(
        "offer",
        offer.offer_id,
        "v",
        offer.version,
        to_status.value,
    )

    return DealTransactionEvent(
        event_id=event_id,
        event_type=(
            DealTransactionEventType.OFFER_STATE_CHANGED
        ),
        deal_id=offer.deal_id,
        tenant_id=offer.tenant_id,
        deal_version=deal_version,
        occurred_at=occurred_at,
        payload={
            "offer_id": offer.offer_id,
            "from_status": from_status.value,
            "to_status": to_status.value,
            "offer_version": offer.version,
        },
        correlation_id=(
            correlation_id or event_id
        ),
        causation_id=causation_id,
    )


def transaction_event_from_negotiation_state(
    *,
    negotiation: DealNegotiation,
    from_status: DealNegotiationStatus,
    to_status: DealNegotiationStatus,
    deal_version: int,
    occurred_at: str,
    correlation_id: str | None = None,
    causation_id: str | None = None,
) -> DealTransactionEvent:
    if not isinstance(
        negotiation,
        DealNegotiation,
    ):
        raise TypeError(
            "negotiation must be DealNegotiation."
        )

    from_status = DealNegotiationStatus(
        from_status
    )
    to_status = DealNegotiationStatus(
        to_status
    )

    event_id = _event_id(
        "negotiation",
        negotiation.negotiation_id,
        "v",
        negotiation.version,
        to_status.value,
    )

    return DealTransactionEvent(
        event_id=event_id,
        event_type=(
            DealTransactionEventType.NEGOTIATION_STATE_CHANGED
        ),
        deal_id=negotiation.deal_id,
        tenant_id=negotiation.tenant_id,
        deal_version=deal_version,
        occurred_at=occurred_at,
        payload={
            "negotiation_id": (
                negotiation.negotiation_id
            ),
            "from_status": from_status.value,
            "to_status": to_status.value,
            "negotiation_version": negotiation.version,
            "active_offer_id": (
                negotiation.active_offer_id
            ),
        },
        correlation_id=(
            correlation_id or event_id
        ),
        causation_id=causation_id,
    )


def transaction_event_from_milestone(
    milestone: DealTransactionMilestone,
    *,
    correlation_id: str | None = None,
    causation_id: str | None = None,
) -> DealTransactionEvent:
    return DealTransactionEvent.from_milestone(
        milestone,
        correlation_id=correlation_id,
        causation_id=causation_id,
    )


def transaction_event_from_ownership(
    binding: DealOwnershipBinding,
    *,
    deal_version: int,
    occurred_at: str,
    correlation_id: str | None = None,
    causation_id: str | None = None,
) -> DealTransactionEvent:
    if not isinstance(
        binding,
        DealOwnershipBinding,
    ):
        raise TypeError(
            "binding must be DealOwnershipBinding."
        )

    event_id = _event_id(
        "ownership",
        binding.binding_id,
        "v",
        deal_version,
    )

    return DealTransactionEvent(
        event_id=event_id,
        event_type=(
            DealTransactionEventType
            .OWNERSHIP_REFERENCE_CHANGED
        ),
        deal_id=binding.deal_id,
        tenant_id=binding.tenant_id,
        deal_version=deal_version,
        occurred_at=occurred_at,
        payload={
            "binding": binding.to_dict(),
        },
        correlation_id=(
            correlation_id or event_id
        ),
        causation_id=causation_id,
    )


def transaction_event_from_evidence(
    evidence: DealEvidenceReference,
    *,
    deal_version: int,
    correlation_id: str | None = None,
    causation_id: str | None = None,
) -> DealTransactionEvent:
    if not isinstance(
        evidence,
        DealEvidenceReference,
    ):
        raise TypeError(
            "evidence must be DealEvidenceReference."
        )

    event_id = _event_id(
        "evidence",
        evidence.evidence_id,
        "v",
        deal_version,
    )

    return DealTransactionEvent(
        event_id=event_id,
        event_type=(
            DealTransactionEventType.EVIDENCE_ATTACHED
        ),
        deal_id=evidence.deal_id,
        tenant_id=evidence.tenant_id,
        deal_version=deal_version,
        occurred_at=evidence.created_at,
        payload={
            "evidence": evidence.to_dict(),
        },
        correlation_id=(
            correlation_id or event_id
        ),
        causation_id=causation_id,
    )


def transaction_event_from_audit(
    audit: DealAuditEntry,
    *,
    correlation_id: str | None = None,
    causation_id: str | None = None,
) -> DealTransactionEvent:
    if not isinstance(
        audit,
        DealAuditEntry,
    ):
        raise TypeError(
            "audit must be DealAuditEntry."
        )

    event_id = _event_id(
        "audit",
        audit.audit_id,
        "v",
        audit.deal_version,
    )

    return DealTransactionEvent(
        event_id=event_id,
        event_type=(
            DealTransactionEventType.AUDIT_RECORDED
        ),
        deal_id=audit.deal_id,
        tenant_id=audit.tenant_id,
        deal_version=audit.deal_version,
        occurred_at=audit.created_at,
        payload={
            "audit": audit.to_dict(),
        },
        correlation_id=(
            correlation_id or event_id
        ),
        causation_id=causation_id,
    )


def build_core002_event_contracts():
    """
    Return CORE-006 business-event contracts for registration
    in the existing CORE-002 EventContractRegistry.

    CORE-006 does not own or instantiate the registry.
    """

    from ..event_platform.event_contract import (
        EventContract,
    )

    required_fields = (
        "event_id",
        "event_type",
        "schema_name",
        "schema_version",
        "event_version",
        "tenant_id",
        "producer",
        "deal_id",
        "deal_version",
        "occurred_at",
        "correlation_id",
        "idempotency_key",
        "payload",
        "payload_hash",
    )

    field_types = {
        "event_id": "string",
        "event_type": "string",
        "schema_name": "string",
        "schema_version": "integer",
        "event_version": "integer",
        "tenant_id": "string",
        "producer": "string",
        "deal_id": "string",
        "deal_version": "integer",
        "occurred_at": "string",
        "correlation_id": "string",
        "idempotency_key": "string",
        "payload": "object",
        "payload_hash": "string",
    }

    return tuple(
        EventContract(
            schema_name=CORE002_SCHEMA_NAME,
            event_type=event_type.value,
            schema_version=CORE002_SCHEMA_VERSION,
            event_version=CORE002_EVENT_VERSION,
            required_fields=required_fields,
            field_types=field_types,
            allow_additional_fields=True,
        )
        for event_type in DealTransactionEventType
    )


__all__ = [
    "CORE002_SCHEMA_NAME",
    "CORE002_SCHEMA_VERSION",
    "CORE002_EVENT_VERSION",
    "CORE006_PRODUCER",
    "DEAL_EVENT_SCHEMA_VERSION",
    "DealTransactionEventError",
    "DealTransactionEventScopeError",
    "DealTransactionEventConflictError",
    "DealTransactionEventType",
    "DealTransactionEvent",
    "transaction_event_from_deal_created",
    "transaction_event_from_deal_state",
    "transaction_event_from_offer_created",
    "transaction_event_from_offer_state",
    "transaction_event_from_negotiation_state",
    "transaction_event_from_milestone",
    "transaction_event_from_ownership",
    "transaction_event_from_evidence",
    "transaction_event_from_audit",
    "build_core002_event_contracts",
]
