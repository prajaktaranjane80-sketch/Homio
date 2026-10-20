from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Mapping

from ..contract_primitives import fingerprint
from .commission_allocation import CommissionAllocation
from .commission_reconciliation import (
    CommissionExternalSettlementEvidence,
    CommissionReconciliation,
    CommissionReconciliationState,
)
from .commission_reconciliation_history import (
    CommissionReconciliationHistory,
)
from .commission_reconciliation_integrity import (
    assert_integrity as assert_reconciliation_integrity,
)
from .commission_reconciliation_snapshot import (
    CommissionReconciliationSnapshot,
)
from .commission_reconciliation_validation import (
    validate_reconciliation,
)
from .commission_security import (
    FinancialAuthorizationAction,
    FinancialAuthorizationRequest,
    FinancialSecurityBoundary,
)
from .commission_settlement import (
    CommissionSettlement,
    CommissionSettlementState,
)
from .commission_settlement_history import (
    CommissionSettlementHistory,
)
from .commission_settlement_integrity import (
    assert_integrity as assert_settlement_integrity,
)
from .commission_settlement_snapshot import (
    CommissionSettlementSnapshot,
)
from .commission_settlement_validation import (
    validate_settlement,
)
from .financial_domain import (
    FinancialTenantScopeError,
    MonetaryAmount,
)


class CommissionSettlementLifecycleError(RuntimeError):
    """Base error for lifecycle orchestration."""


class CommissionSettlementLifecycleValidationError(
    CommissionSettlementLifecycleError
):
    """Lifecycle input or domain validation failed."""


class CommissionSettlementTransitionError(
    CommissionSettlementLifecycleError
):
    """Requested settlement state transition is not allowed."""


class CommissionSettlementConcurrencyError(
    CommissionSettlementLifecycleError
):
    """Caller supplied a stale settlement version or fingerprint."""


class CommissionSettlementIntegrityError(
    CommissionSettlementLifecycleError
):
    """Settlement snapshot, history, or event-chain integrity failed."""


class CommissionSettlementEvidenceError(
    CommissionSettlementLifecycleError
):
    """External settlement evidence could not be independently verified."""


def _required_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CommissionSettlementLifecycleValidationError(
            f"{field_name} must be non-empty text."
        )
    return value.strip()


def _aware_utc(value: datetime, field_name: str) -> datetime:
    if (
        not isinstance(value, datetime)
        or value.tzinfo is None
        or value.utcoffset() is None
    ):
        raise CommissionSettlementLifecycleValidationError(
            f"{field_name} must be timezone-aware."
        )
    return value.astimezone(timezone.utc)


@dataclass(frozen=True, slots=True)
class CommissionSettlementLifecycleEvent:
    """Immutable, hash-linked audit event for a settlement lifecycle step."""

    sequence: int
    event_type: str
    tenant_id: str
    settlement_id: str
    commission_id: str
    from_state: str | None
    to_state: str
    occurred_at: datetime
    settlement_fingerprint: str
    actor_reference: str
    authorization_reference: str | None = None
    evidence_fingerprint: str | None = None
    previous_event_fingerprint: str | None = None
    event_fingerprint: str = ""
    reconciliation_id: str | None = None
    reconciliation_fingerprint: str | None = None

    def __post_init__(self) -> None:
        if (
            isinstance(self.sequence, bool)
            or not isinstance(self.sequence, int)
            or self.sequence < 1
        ):
            raise CommissionSettlementLifecycleValidationError(
                "Event sequence must be a positive integer."
            )

        for field_name in (
            "event_type",
            "tenant_id",
            "settlement_id",
            "commission_id",
            "to_state",
            "settlement_fingerprint",
            "actor_reference",
        ):
            object.__setattr__(
                self,
                field_name,
                _required_text(
                    getattr(self, field_name),
                    field_name,
                ),
            )

        if self.from_state is not None:
            object.__setattr__(
                self,
                "from_state",
                _required_text(
                    self.from_state,
                    "from_state",
                ),
            )

        for field_name in (
            "authorization_reference",
            "evidence_fingerprint",
            "previous_event_fingerprint",
            "reconciliation_id",
            "reconciliation_fingerprint",
        ):
            value = getattr(self, field_name)
            if value is not None:
                object.__setattr__(
                    self,
                    field_name,
                    _required_text(value, field_name),
                )

        object.__setattr__(
            self,
            "occurred_at",
            _aware_utc(
                self.occurred_at,
                "occurred_at",
            ),
        )

        expected = fingerprint(self._payload())

        if self.event_fingerprint:
            if self.event_fingerprint != expected:
                raise CommissionSettlementIntegrityError(
                    "Lifecycle event fingerprint does not match "
                    "its payload."
                )
        else:
            object.__setattr__(
                self,
                "event_fingerprint",
                expected,
            )

    def _payload(self) -> dict[str, Any]:
        return {
            "sequence": self.sequence,
            "event_type": self.event_type,
            "tenant_id": self.tenant_id,
            "settlement_id": self.settlement_id,
            "commission_id": self.commission_id,
            "from_state": self.from_state,
            "to_state": self.to_state,
            "occurred_at": self.occurred_at.isoformat(),
            "settlement_fingerprint": (
                self.settlement_fingerprint
            ),
            "actor_reference": self.actor_reference,
            "authorization_reference": (
                self.authorization_reference
            ),
            "evidence_fingerprint": (
                self.evidence_fingerprint
            ),
            "previous_event_fingerprint": (
                self.previous_event_fingerprint
            ),
            "reconciliation_id": self.reconciliation_id,
            "reconciliation_fingerprint": (
                self.reconciliation_fingerprint
            ),
        }

    def verify(self) -> bool:
        return (
            self.event_fingerprint
            == fingerprint(self._payload())
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            **self._payload(),
            "event_fingerprint": self.event_fingerprint,
        }


@dataclass(frozen=True, slots=True)
class SettlementLifecycleRecord:
    """Immutable result bundle; persistence remains upstream-owned."""

    allocation: CommissionAllocation
    settlement: CommissionSettlement
    settlement_history: CommissionSettlementHistory
    snapshot: CommissionSettlementSnapshot
    lifecycle_events: tuple[
        CommissionSettlementLifecycleEvent,
        ...,
    ]
    reconciliation_history: CommissionReconciliationHistory = field(
        default_factory=CommissionReconciliationHistory
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "settlement": self.settlement.to_dict(),
            "settlement_history": self.settlement_history.to_dict(),
            "snapshot": self.snapshot.to_dict(),
            "lifecycle_events": [
                event.to_dict()
                for event in self.lifecycle_events
            ],
            "reconciliation_history": (
                self.reconciliation_history.to_dict()
            ),
        }


@dataclass(frozen=True, slots=True)
class CommissionSettlementReconciliationResult:
    """Settlement state and independent reconciliation evidence."""

    settlement_record: SettlementLifecycleRecord
    evidence: CommissionExternalSettlementEvidence
    reconciliation: CommissionReconciliation
    reconciliation_snapshot: CommissionReconciliationSnapshot

    def to_dict(self) -> dict[str, Any]:
        return {
            "settlement_record": (
                self.settlement_record.to_dict()
            ),
            "evidence": self.evidence.to_dict(),
            "reconciliation": self.reconciliation.to_dict(),
            "reconciliation_snapshot": (
                self.reconciliation_snapshot.to_dict()
            ),
        }


class CommissionSettlementLifecycle:
    """
    Pure lifecycle orchestration around existing CORE-008 domain components.

    This module does not execute payments, post a ledger, create a second
    authorization system, or write project state. Callers must persist
    successful results through the existing authorized financial path.

    A settlement can become CONFIRMED only through independently verified,
    authorized MATCHED reconciliation evidence linked to the event chain.
    """

    _ALLOWED_TRANSITIONS = {
        CommissionSettlementState.READY: frozenset(
            {
                CommissionSettlementState.AUTHORIZATION_PENDING,
                CommissionSettlementState.CANCELLED,
            }
        ),
        CommissionSettlementState.AUTHORIZATION_PENDING: frozenset(
            {
                CommissionSettlementState.AUTHORIZED,
                CommissionSettlementState.FAILED,
                CommissionSettlementState.CANCELLED,
            }
        ),
        CommissionSettlementState.AUTHORIZED: frozenset(
            {
                CommissionSettlementState.SUBMITTED,
                CommissionSettlementState.CANCELLED,
            }
        ),
        CommissionSettlementState.SUBMITTED: frozenset(
            {
                CommissionSettlementState.FAILED,
            }
        ),
        CommissionSettlementState.CONFIRMED: frozenset(),
        CommissionSettlementState.FAILED: frozenset(),
        CommissionSettlementState.CANCELLED: frozenset(),
    }

    _RECONCILIATION_EVENT_TYPES = frozenset(
        {
            "RECONCILIATION_MATCHED",
            "RECONCILIATION_VARIANCE",
        }
    )

    _KNOWN_EVENT_TYPES = frozenset(
        {
            "SETTLEMENT_CREATED",
            "SETTLEMENT_STATE_TRANSITION",
            "RECONCILIATION_MATCHED",
            "RECONCILIATION_VARIANCE",
        }
    )

    def __init__(
        self,
        *,
        security_boundary: FinancialSecurityBoundary,
        evidence_verifier: Callable[
            [
                CommissionExternalSettlementEvidence,
                CommissionSettlement,
            ],
            bool,
        ],
    ) -> None:
        if not isinstance(
            security_boundary,
            FinancialSecurityBoundary,
        ):
            raise TypeError(
                "security_boundary must be the existing "
                "FinancialSecurityBoundary."
            )

        if not callable(evidence_verifier):
            raise TypeError(
                "evidence_verifier must be callable."
            )

        self._security_boundary = security_boundary
        self._evidence_verifier = evidence_verifier

    def _authorize(
        self,
        *,
        settlement: CommissionSettlement,
        action: FinancialAuthorizationAction,
        actor_reference: str,
        authorization_reference: str,
        context: Mapping[str, Any],
    ) -> None:
        request = FinancialAuthorizationRequest(
            tenant_id=settlement.tenant_id,
            resource_tenant_id=settlement.tenant_id,
            actor_reference=_required_text(
                actor_reference,
                "actor_reference",
            ),
            resource_reference=settlement.settlement_id,
            action=action,
            authorization_reference=_required_text(
                authorization_reference,
                "authorization_reference",
            ),
            sensitive=True,
            context=dict(context),
        )
        self._security_boundary.authorize(request)

    @staticmethod
    def _new_event(
        *,
        record: SettlementLifecycleRecord | None,
        settlement: CommissionSettlement,
        event_type: str,
        from_state: str | None,
        to_state: str,
        occurred_at: datetime,
        actor_reference: str,
        authorization_reference: str | None = None,
        evidence_fingerprint: str | None = None,
        reconciliation_id: str | None = None,
        reconciliation_fingerprint: str | None = None,
    ) -> CommissionSettlementLifecycleEvent:
        prior_events = (
            ()
            if record is None
            else record.lifecycle_events
        )

        previous_fingerprint = (
            prior_events[-1].event_fingerprint
            if prior_events
            else None
        )

        return CommissionSettlementLifecycleEvent(
            sequence=len(prior_events) + 1,
            event_type=event_type,
            tenant_id=settlement.tenant_id,
            settlement_id=settlement.settlement_id,
            commission_id=settlement.commission_id,
            from_state=from_state,
            to_state=to_state,
            occurred_at=occurred_at,
            settlement_fingerprint=(
                settlement.immutable_fingerprint
            ),
            actor_reference=actor_reference,
            authorization_reference=authorization_reference,
            evidence_fingerprint=evidence_fingerprint,
            previous_event_fingerprint=previous_fingerprint,
            reconciliation_id=reconciliation_id,
            reconciliation_fingerprint=(
                reconciliation_fingerprint
            ),
        )

    def _validate_record(
        self,
        record: SettlementLifecycleRecord,
        *,
        at: datetime,
    ) -> None:
        if not isinstance(
            record,
            SettlementLifecycleRecord,
        ):
            raise TypeError(
                "record must be SettlementLifecycleRecord."
            )

        validation_time = _aware_utc(at, "at")
        settlement = record.settlement

        assert_settlement_integrity(
            settlement,
            record.snapshot,
        )

        latest_settlement_history = (
            record.settlement_history.latest
        )

        if latest_settlement_history is None:
            raise CommissionSettlementIntegrityError(
                "Settlement history is empty."
            )

        current_fingerprint = settlement.immutable_fingerprint

        if (
            latest_settlement_history.tenant_id
            != settlement.tenant_id
            or latest_settlement_history.settlement_id
            != settlement.settlement_id
            or latest_settlement_history.commission_id
            != settlement.commission_id
            or latest_settlement_history.allocation_set_id
            != settlement.allocation_set_id
            or latest_settlement_history.settlement_version
            != settlement.settlement_version
            or latest_settlement_history.state
            != settlement.state.value
            or latest_settlement_history.settlement_fingerprint
            != current_fingerprint
        ):
            raise CommissionSettlementIntegrityError(
                "Latest settlement history does not match "
                "the current settlement."
            )

        if not isinstance(
            record.reconciliation_history,
            CommissionReconciliationHistory,
        ):
            raise CommissionSettlementIntegrityError(
                "Reconciliation history has an invalid type."
            )

        settlement_history_by_fingerprint = {}

        for history_entry in record.settlement_history.entries:
            if (
                history_entry.settlement_fingerprint
                in settlement_history_by_fingerprint
            ):
                raise CommissionSettlementIntegrityError(
                    "Settlement history contains duplicate fingerprints."
                )

            if (
                history_entry.tenant_id != settlement.tenant_id
                or history_entry.settlement_id
                != settlement.settlement_id
                or history_entry.commission_id
                != settlement.commission_id
                or history_entry.allocation_set_id
                != settlement.allocation_set_id
            ):
                raise CommissionSettlementIntegrityError(
                    "Settlement history contains a mismatched identity."
                )

            settlement_history_by_fingerprint[
                history_entry.settlement_fingerprint
            ] = history_entry

        if not record.lifecycle_events:
            raise CommissionSettlementIntegrityError(
                "Lifecycle event chain is empty."
            )

        reconciliation_entries = (
            record.reconciliation_history.entries
        )

        previous_fingerprint: str | None = None
        previous_event: (
            CommissionSettlementLifecycleEvent | None
        ) = None

        linked_reconciliation_events = []
        ordered_settlement_history_fingerprints: list[str] = []

        for expected_sequence, event in enumerate(
            record.lifecycle_events,
            start=1,
        ):
            if (
                event.sequence != expected_sequence
                or not event.verify()
                or event.previous_event_fingerprint
                != previous_fingerprint
            ):
                raise CommissionSettlementIntegrityError(
                    "Lifecycle event chain is invalid."
                )

            if (
                event.tenant_id != settlement.tenant_id
                or event.settlement_id != settlement.settlement_id
                or event.commission_id != settlement.commission_id
            ):
                raise CommissionSettlementIntegrityError(
                    "Lifecycle event identity mismatch."
                )

            if event.occurred_at > validation_time:
                raise CommissionSettlementIntegrityError(
                    "Lifecycle event occurs after validation time."
                )

            if event.event_type not in self._KNOWN_EVENT_TYPES:
                raise CommissionSettlementIntegrityError(
                    "Lifecycle event type is not recognised."
                )

            if (
                event.event_type == "SETTLEMENT_STATE_TRANSITION"
                and event.to_state
                in {
                    CommissionSettlementState.AUTHORIZED.value,
                    CommissionSettlementState.CANCELLED.value,
                }
            ):
                if not event.authorization_reference:
                    raise CommissionSettlementIntegrityError(
                        "Sensitive settlement transition is missing "
                        "an authorization reference."
                    )

                if (
                    event.authorization_reference
                    != settlement.authorization_reference
                ):
                    raise CommissionSettlementIntegrityError(
                        "Sensitive settlement transition authorization "
                        "reference does not match the settlement."
                    )

            if (
                event.event_type in self._RECONCILIATION_EVENT_TYPES
                and not event.authorization_reference
            ):
                raise CommissionSettlementIntegrityError(
                    "Reconciliation event is missing an authorization "
                    "reference."
                )

            if previous_event is None:
                if (
                    event.event_type != "SETTLEMENT_CREATED"
                    or event.from_state is not None
                    or event.to_state
                    != CommissionSettlementState.READY.value
                ):
                    raise CommissionSettlementIntegrityError(
                        "Lifecycle chain must begin with "
                        "SETTLEMENT_CREATED."
                    )
            else:
                if event.event_type == "SETTLEMENT_CREATED":
                    raise CommissionSettlementIntegrityError(
                        "SETTLEMENT_CREATED may appear only "
                        "as the first event."
                    )

                if event.from_state != previous_event.to_state:
                    raise CommissionSettlementIntegrityError(
                        "Lifecycle event state continuity is broken."
                    )

                if event.occurred_at < previous_event.occurred_at:
                    raise CommissionSettlementIntegrityError(
                        "Lifecycle event timestamps move backwards."
                    )

            settlement_entry = (
                settlement_history_by_fingerprint.get(
                    event.settlement_fingerprint
                )
            )

            if settlement_entry is None:
                raise CommissionSettlementIntegrityError(
                    "Lifecycle event references an unknown "
                    "settlement fingerprint."
                )

            if (
                settlement_entry.tenant_id != event.tenant_id
                or settlement_entry.settlement_id
                != event.settlement_id
                or settlement_entry.commission_id
                != event.commission_id
                or settlement_entry.state != event.to_state
            ):
                raise CommissionSettlementIntegrityError(
                    "Lifecycle event does not match its "
                    "settlement history entry."
                )

            if (
                not ordered_settlement_history_fingerprints
                or ordered_settlement_history_fingerprints[-1]
                != event.settlement_fingerprint
            ):
                ordered_settlement_history_fingerprints.append(
                    event.settlement_fingerprint
                )

            is_reconciliation_event = (
                event.event_type
                in self._RECONCILIATION_EVENT_TYPES
            )

            if not is_reconciliation_event:
                if (
                    event.reconciliation_id is not None
                    or event.reconciliation_fingerprint is not None
                ):
                    raise CommissionSettlementIntegrityError(
                        "Non-reconciliation event contains "
                        "reconciliation linkage fields."
                    )

            if event.event_type == "SETTLEMENT_STATE_TRANSITION":
                try:
                    source_state = CommissionSettlementState(
                        event.from_state
                    )
                    destination_state = CommissionSettlementState(
                        event.to_state
                    )
                except (TypeError, ValueError) as exc:
                    raise CommissionSettlementIntegrityError(
                        "Lifecycle event contains an invalid "
                        "settlement state."
                    ) from exc

                if (
                    destination_state
                    not in self._ALLOWED_TRANSITIONS[source_state]
                ):
                    raise CommissionSettlementIntegrityError(
                        "Lifecycle event records a forbidden "
                        "settlement transition."
                    )

                if (
                    destination_state
                    is CommissionSettlementState.CONFIRMED
                ):
                    raise CommissionSettlementIntegrityError(
                        "CONFIRMED cannot be reached by a generic "
                        "state transition."
                    )

            if is_reconciliation_event:
                if (
                    not event.reconciliation_id
                    or not event.reconciliation_fingerprint
                    or not event.evidence_fingerprint
                ):
                    raise CommissionSettlementIntegrityError(
                        "Reconciliation event is missing required "
                        "evidence linkage."
                    )

                matches = [
                    entry
                    for entry in reconciliation_entries
                    if (
                        entry.reconciliation_id
                        == event.reconciliation_id
                        and entry.reconciliation_fingerprint
                        == event.reconciliation_fingerprint
                    )
                ]

                if len(matches) != 1:
                    raise CommissionSettlementIntegrityError(
                        "Lifecycle event does not reference exactly "
                        "one reconciliation history entry."
                    )

                reconciliation_entry = matches[0]

                if (
                    reconciliation_entry.tenant_id
                    != settlement.tenant_id
                    or reconciliation_entry.commission_id
                    != settlement.commission_id
                    or reconciliation_entry.settlement_id
                    != settlement.settlement_id
                ):
                    raise CommissionSettlementIntegrityError(
                        "Reconciliation history identity mismatch."
                    )

                if (
                    not reconciliation_entry
                    .external_evidence_fingerprint
                    or event.evidence_fingerprint
                    != reconciliation_entry
                    .external_evidence_fingerprint
                ):
                    raise CommissionSettlementIntegrityError(
                        "Lifecycle evidence fingerprint does not "
                        "match reconciliation history."
                    )

                if event.event_type == "RECONCILIATION_MATCHED":
                    if (
                        reconciliation_entry.state
                        != CommissionReconciliationState.MATCHED.value
                        or event.from_state
                        != CommissionSettlementState.SUBMITTED.value
                        or event.to_state
                        != CommissionSettlementState.CONFIRMED.value
                    ):
                        raise CommissionSettlementIntegrityError(
                            "MATCHED reconciliation does not prove "
                            "the CONFIRMED transition."
                        )
                else:
                    if (
                        reconciliation_entry.state
                        == CommissionReconciliationState.MATCHED.value
                        or event.from_state
                        != CommissionSettlementState.SUBMITTED.value
                        or event.to_state
                        != CommissionSettlementState.SUBMITTED.value
                    ):
                        raise CommissionSettlementIntegrityError(
                            "Variance reconciliation has an "
                            "inconsistent lifecycle transition."
                        )

                linked_reconciliation_events.append(
                    (event, reconciliation_entry)
                )

            previous_fingerprint = event.event_fingerprint
            previous_event = event

        history_fingerprints = tuple(
            entry.settlement_fingerprint
            for entry in record.settlement_history.entries
        )
        event_history_fingerprints = tuple(
            ordered_settlement_history_fingerprints
        )

        if history_fingerprints != event_history_fingerprints:
            raise CommissionSettlementIntegrityError(
                "Settlement history order does not match lifecycle "
                "event order."
            )

        last_event = record.lifecycle_events[-1]

        if (
            last_event.settlement_fingerprint != current_fingerprint
            or last_event.to_state != settlement.state.value
        ):
            raise CommissionSettlementIntegrityError(
                "Last lifecycle event does not match "
                "the current settlement."
            )

        if (
            len(linked_reconciliation_events)
            != len(reconciliation_entries)
        ):
            raise CommissionSettlementIntegrityError(
                "Reconciliation history and lifecycle event "
                "counts do not match."
            )

        for (
            event,
            linked_entry,
        ), history_entry in zip(
            linked_reconciliation_events,
            reconciliation_entries,
        ):
            if (
                event.reconciliation_id
                != history_entry.reconciliation_id
                or event.reconciliation_fingerprint
                != history_entry.reconciliation_fingerprint
                or event.evidence_fingerprint
                != history_entry.external_evidence_fingerprint
                or linked_entry != history_entry
            ):
                raise CommissionSettlementIntegrityError(
                    "Reconciliation events do not match the "
                    "ordered reconciliation history."
                )

        matched_entries = [
            entry
            for entry in reconciliation_entries
            if (
                entry.state
                == CommissionReconciliationState.MATCHED.value
            )
        ]

        latest_reconciliation = (
            record.reconciliation_history.latest
        )

        if settlement.state is CommissionSettlementState.CONFIRMED:
            if (
                not matched_entries
                or latest_reconciliation is None
                or latest_reconciliation.state
                != CommissionReconciliationState.MATCHED.value
                or last_event.event_type
                != "RECONCILIATION_MATCHED"
                or last_event.reconciliation_id
                != latest_reconciliation.reconciliation_id
                or last_event.reconciliation_fingerprint
                != latest_reconciliation.reconciliation_fingerprint
                or last_event.evidence_fingerprint
                != latest_reconciliation.external_evidence_fingerprint
            ):
                raise CommissionSettlementIntegrityError(
                    "CONFIRMED settlement lacks a matching, "
                    "event-linked reconciliation record."
                )
        elif matched_entries:
            raise CommissionSettlementIntegrityError(
                "A matched reconciliation exists for a settlement "
                "that is not CONFIRMED."
            )

        errors = validate_settlement(
            settlement,
            record.allocation,
            at=validation_time,
        )

        if errors:
            raise CommissionSettlementLifecycleValidationError(
                "Settlement validation failed: "
                + "; ".join(errors)
            )

    def verify(
        self,
        record: SettlementLifecycleRecord,
        *,
        at: datetime,
    ) -> bool:
        """Verify snapshot, history, domain rules, and linked events."""
        self._validate_record(record, at=at)
        return True

    def _build_record(
        self,
        *,
        settlement: CommissionSettlement,
        allocation: CommissionAllocation,
        settlement_history: CommissionSettlementHistory,
        reconciliation_history: CommissionReconciliationHistory,
        lifecycle_events: tuple[
            CommissionSettlementLifecycleEvent,
            ...,
        ],
        at: datetime,
    ) -> SettlementLifecycleRecord:
        validation_time = _aware_utc(at, "at")

        errors = validate_settlement(
            settlement,
            allocation,
            at=validation_time,
        )

        if errors:
            raise CommissionSettlementLifecycleValidationError(
                "Settlement validation failed: "
                + "; ".join(errors)
            )

        updated_history = settlement_history.append(settlement)

        snapshot = CommissionSettlementSnapshot.from_settlement(
            settlement
        )

        assert_settlement_integrity(
            settlement,
            snapshot,
        )

        record = SettlementLifecycleRecord(
            allocation=allocation,
            settlement=settlement,
            settlement_history=updated_history,
            snapshot=snapshot,
            lifecycle_events=lifecycle_events,
            reconciliation_history=reconciliation_history,
        )

        self._validate_record(
            record,
            at=validation_time,
        )

        return record

    def create_settlement(
        self,
        allocation: CommissionAllocation,
        *,
        settlement_id: str,
        settlement_version: int = 1,
        authorization_reference: str,
        provenance_reference: str,
        actor_reference: str,
        requested_at: datetime,
        amount: MonetaryAmount | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> SettlementLifecycleRecord:
        """Create an immutable READY instruction and its first audit event."""
        requested_time = _aware_utc(
            requested_at,
            "requested_at",
        )

        actor = _required_text(
            actor_reference,
            "actor_reference",
        )

        provenance = _required_text(
            provenance_reference,
            "provenance_reference",
        )

        settlement = CommissionSettlement.from_allocation(
            allocation,
            settlement_id=settlement_id,
            settlement_version=settlement_version,
            amount=amount,
            authorization_reference=authorization_reference,
            provenance_reference=provenance,
            requested_at=requested_time,
            metadata=metadata,
        )

        event = self._new_event(
            record=None,
            settlement=settlement,
            event_type="SETTLEMENT_CREATED",
            from_state=None,
            to_state=settlement.state.value,
            occurred_at=requested_time,
            actor_reference=actor,
            authorization_reference=(
                settlement.authorization_reference
            ),
            evidence_fingerprint=fingerprint(
                {"provenance_reference": provenance}
            ),
        )

        return self._build_record(
            settlement=settlement,
            allocation=allocation,
            settlement_history=CommissionSettlementHistory(),
            reconciliation_history=CommissionReconciliationHistory(),
            lifecycle_events=(event,),
            at=requested_time,
        )

    def transition(
        self,
        record: SettlementLifecycleRecord,
        target_state: CommissionSettlementState,
        *,
        expected_settlement_version: int,
        expected_settlement_fingerprint: str,
        actor_reference: str,
        at: datetime,
        external_reference: str | None = None,
        failure_code: str | None = None,
    ) -> SettlementLifecycleRecord:
        """
        Apply an allowed state transition using optimistic identity checks.

        CONFIRMED is deliberately excluded: only a matched reconciliation
        of independently verified evidence may confirm a settlement.
        """
        now = _aware_utc(at, "at")
        self._validate_record(record, at=now)

        current = record.settlement
        actor = _required_text(
            actor_reference,
            "actor_reference",
        )

        if (
            isinstance(expected_settlement_version, bool)
            or not isinstance(expected_settlement_version, int)
            or expected_settlement_version
            != current.settlement_version
        ):
            raise CommissionSettlementConcurrencyError(
                "Expected settlement version is stale."
            )

        if (
            _required_text(
                expected_settlement_fingerprint,
                "expected_settlement_fingerprint",
            )
            != current.immutable_fingerprint
        ):
            raise CommissionSettlementConcurrencyError(
                "Expected settlement fingerprint is stale."
            )

        try:
            destination = CommissionSettlementState(target_state)
        except (TypeError, ValueError) as exc:
            raise CommissionSettlementTransitionError(
                "Unsupported settlement destination state."
            ) from exc

        if destination is CommissionSettlementState.CONFIRMED:
            raise CommissionSettlementTransitionError(
                "Settlement can be CONFIRMED only by a MATCHED "
                "reconciliation."
            )

        allowed = self._ALLOWED_TRANSITIONS[current.state]

        if destination not in allowed:
            raise CommissionSettlementTransitionError(
                f"Transition {current.state.value} -> "
                f"{destination.value} is not allowed."
            )

        if destination is CommissionSettlementState.SUBMITTED:
            external_reference = _required_text(
                external_reference,
                "external_reference",
            )
        elif external_reference is not None:
            raise CommissionSettlementLifecycleValidationError(
                "external_reference is accepted only when submitting."
            )

        if destination is CommissionSettlementState.FAILED:
            failure_code = _required_text(
                failure_code,
                "failure_code",
            )
        elif failure_code is not None:
            raise CommissionSettlementLifecycleValidationError(
                "failure_code is accepted only for a FAILED transition."
            )

        authorization_reference: str | None = None

        if destination in {
            CommissionSettlementState.AUTHORIZED,
            CommissionSettlementState.CANCELLED,
        }:
            authorization_reference = (
                current.authorization_reference
            )

            self._authorize(
                settlement=current,
                action=FinancialAuthorizationAction.SETTLE,
                actor_reference=actor,
                authorization_reference=authorization_reference,
                context={
                    "operation": destination.value,
                    "settlement_fingerprint": (
                        current.immutable_fingerprint
                    ),
                },
            )

        updated = current.with_state(
            destination,
            external_reference=external_reference,
            failure_code=failure_code,
        )

        event_evidence_fingerprint: str | None = None

        if external_reference is not None:
            event_evidence_fingerprint = fingerprint(
                {"external_reference": external_reference}
            )
        elif failure_code is not None:
            event_evidence_fingerprint = fingerprint(
                {"failure_code": failure_code}
            )

        event = self._new_event(
            record=record,
            settlement=updated,
            event_type="SETTLEMENT_STATE_TRANSITION",
            from_state=current.state.value,
            to_state=updated.state.value,
            occurred_at=now,
            actor_reference=actor,
            authorization_reference=authorization_reference,
            evidence_fingerprint=event_evidence_fingerprint,
        )

        return self._build_record(
            settlement=updated,
            allocation=record.allocation,
            settlement_history=record.settlement_history,
            reconciliation_history=record.reconciliation_history,
            lifecycle_events=(
                record.lifecycle_events + (event,)
            ),
            at=now,
        )

    def reconcile(
        self,
        record: SettlementLifecycleRecord,
        evidence: CommissionExternalSettlementEvidence,
        *,
        reconciliation_id: str,
        reconciliation_version: int = 1,
        reconciliation_reference: str,
        provenance_reference: str,
        actor_reference: str,
        authorization_reference: str,
        reconciled_at: datetime,
        at: datetime,
        variance_tolerance: MonetaryAmount | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> CommissionSettlementReconciliationResult:
        """
        Reconcile a submitted settlement using verified external evidence.

        A variance remains SUBMITTED for follow-up. Only a MATCHED
        reconciliation creates a CONFIRMED settlement.
        """
        now = _aware_utc(at, "at")

        reconciliation_time = _aware_utc(
            reconciled_at,
            "reconciled_at",
        )

        self._validate_record(
            record,
            at=now,
        )

        settlement = record.settlement

        if settlement.state is not CommissionSettlementState.SUBMITTED:
            raise CommissionSettlementTransitionError(
                "Only SUBMITTED settlements may be reconciled."
            )

        if not isinstance(
            evidence,
            CommissionExternalSettlementEvidence,
        ):
            raise CommissionSettlementLifecycleValidationError(
                "evidence must be "
                "CommissionExternalSettlementEvidence."
            )

        if evidence.tenant_id != settlement.tenant_id:
            raise FinancialTenantScopeError(
                "Settlement and external evidence tenant mismatch."
            )

        if (
            not settlement.external_reference
            or evidence.external_reference
            != settlement.external_reference
        ):
            raise CommissionSettlementEvidenceError(
                "External evidence reference does not match "
                "the submitted settlement."
            )

        if evidence.observed_at > now:
            raise CommissionSettlementLifecycleValidationError(
                "External evidence cannot be observed after "
                "validation time."
            )

        if reconciliation_time < evidence.observed_at:
            raise CommissionSettlementLifecycleValidationError(
                "Reconciliation cannot predate the external evidence."
            )

        if reconciliation_time > now:
            raise CommissionSettlementLifecycleValidationError(
                "Reconciliation cannot occur after validation time."
            )

        actor = _required_text(
            actor_reference,
            "actor_reference",
        )

        authorization_ref = _required_text(
            authorization_reference,
            "authorization_reference",
        )

        if (
            isinstance(reconciliation_version, bool)
            or not isinstance(reconciliation_version, int)
            or reconciliation_version < 1
        ):
            raise CommissionSettlementLifecycleValidationError(
                "reconciliation_version must be a positive integer."
            )

        reconciliation_id_value = _required_text(
            reconciliation_id,
            "reconciliation_id",
        )
        reconciliation_reference_value = _required_text(
            reconciliation_reference,
            "reconciliation_reference",
        )
        provenance_reference_value = _required_text(
            provenance_reference,
            "provenance_reference",
        )

        self._authorize(
            settlement=settlement,
            action=FinancialAuthorizationAction.RECONCILE,
            actor_reference=actor,
            authorization_reference=authorization_ref,
            context={
                "operation": "RECONCILE",
                "settlement_fingerprint": (
                    settlement.immutable_fingerprint
                ),
                "external_evidence_fingerprint": (
                    evidence.immutable_fingerprint
                ),
                "reconciliation_id": reconciliation_id_value,
                "reconciliation_version": reconciliation_version,
                "reconciliation_reference": (
                    reconciliation_reference_value
                ),
                "provenance_reference": provenance_reference_value,
            },
        )

        try:
            independently_verified = self._evidence_verifier(
                evidence,
                settlement,
            )
        except Exception as exc:
            raise CommissionSettlementEvidenceError(
                "External evidence verifier failed; "
                "reconciliation blocked."
            ) from exc

        if independently_verified is not True:
            raise CommissionSettlementEvidenceError(
                "External settlement evidence was not "
                "independently verified."
            )

        if metadata is not None and not isinstance(
            metadata,
            Mapping,
        ):
            raise CommissionSettlementLifecycleValidationError(
                "metadata must be a mapping."
            )

        audit_metadata = (
            {}
            if metadata is None
            else dict(metadata)
        )

        reserved_metadata = {
            "authorized_actor_reference": actor,
            "authorization_reference": authorization_ref,
            "settlement_fingerprint": (
                settlement.immutable_fingerprint
            ),
            "external_evidence_fingerprint": (
                evidence.immutable_fingerprint
            ),
        }

        for key, value in reserved_metadata.items():
            if (
                key in audit_metadata
                and audit_metadata[key] != value
            ):
                raise CommissionSettlementLifecycleValidationError(
                    "metadata cannot override reserved audit field: "
                    f"{key}"
                )

            audit_metadata[key] = value

        reconciliation = CommissionReconciliation.reconcile(
            settlement,
            evidence,
            reconciliation_id=reconciliation_id_value,
            reconciliation_version=reconciliation_version,
            variance_tolerance=variance_tolerance,
            reconciled_at=reconciliation_time,
            reconciliation_reference=reconciliation_reference_value,
            provenance_reference=provenance_reference_value,
            metadata=audit_metadata,
        )

        errors = validate_reconciliation(
            reconciliation,
            settlement,
            evidence,
            at=now,
        )

        if errors:
            raise CommissionSettlementLifecycleValidationError(
                "Reconciliation validation failed: "
                + "; ".join(errors)
            )

        reconciliation_snapshot = (
            CommissionReconciliationSnapshot.from_reconciliation(
                reconciliation
            )
        )

        assert_reconciliation_integrity(
            reconciliation,
            reconciliation_snapshot,
        )

        updated_reconciliation_history = (
            record.reconciliation_history.append(reconciliation)
        )

        if (
            reconciliation.state
            is CommissionReconciliationState.MATCHED
        ):
            updated_settlement = settlement.with_state(
                CommissionSettlementState.CONFIRMED,
                external_reference=evidence.external_reference,
            )
            event_type = "RECONCILIATION_MATCHED"
        else:
            updated_settlement = settlement
            event_type = "RECONCILIATION_VARIANCE"

        event = self._new_event(
            record=record,
            settlement=updated_settlement,
            event_type=event_type,
            from_state=settlement.state.value,
            to_state=updated_settlement.state.value,
            occurred_at=reconciliation_time,
            actor_reference=actor,
            authorization_reference=authorization_ref,
            evidence_fingerprint=(
                evidence.immutable_fingerprint
            ),
            reconciliation_id=reconciliation.reconciliation_id,
            reconciliation_fingerprint=(
                reconciliation.immutable_fingerprint
            ),
        )

        updated_record = self._build_record(
            settlement=updated_settlement,
            allocation=record.allocation,
            settlement_history=record.settlement_history,
            reconciliation_history=updated_reconciliation_history,
            lifecycle_events=(
                record.lifecycle_events + (event,)
            ),
            at=now,
        )

        return CommissionSettlementReconciliationResult(
            settlement_record=updated_record,
            evidence=evidence,
            reconciliation=reconciliation,
            reconciliation_snapshot=reconciliation_snapshot,
        )


__all__ = [
    "CommissionSettlementLifecycleError",
    "CommissionSettlementLifecycleValidationError",
    "CommissionSettlementTransitionError",
    "CommissionSettlementConcurrencyError",
    "CommissionSettlementIntegrityError",
    "CommissionSettlementEvidenceError",
    "CommissionSettlementLifecycleEvent",
    "SettlementLifecycleRecord",
    "CommissionSettlementReconciliationResult",
    "CommissionSettlementLifecycle",
]
