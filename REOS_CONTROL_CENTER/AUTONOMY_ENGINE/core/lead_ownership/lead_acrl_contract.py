"""
CORE-003 T10 — REOS + ACRL Integration Contract

Purpose:
- Define the machine-readable boundary between CORE-003 and ACRL.
- Preserve idempotency, tenant scope, revision preconditions,
  correlation, checkpoint and evidence references.
- Allow ACRL to reason about continuity/recovery without owning
  Lead or Ownership domain state.

IMPORTANT:
This module does NOT import or implement ACRL internals.

ACRL owns:
- continuity
- checkpoint/recovery
- drift/reconstruction
- execution evidence/operation framework

CORE-003 owns:
- lead/ownership domain truth

Neither layer mutates the other's canonical state.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
from uuid import UUID, uuid4

from .lead import Lead
from .lead_consistency import (
    LeadConsistencySnapshot,
    LeadMutationPrecondition,
)
from .lead_ownership import LeadOwnership


class LeadAcrlContractError(Exception):
    """Base REOS↔ACRL contract error."""


class LeadAcrlValidationError(
    LeadAcrlContractError
):
    """Invalid REOS↔ACRL integration contract."""


class LeadAcrlPreconditionConflict(
    LeadAcrlContractError
):
    """Integration contract precondition mismatch."""


class ReosLeadOperation(str, Enum):
    CREATE_LEAD = "CREATE_LEAD"
    TRANSITION_LEAD = "TRANSITION_LEAD"
    UPDATE_LEAD = "UPDATE_LEAD"
    ASSIGN_OWNER = "ASSIGN_OWNER"
    TRANSFER_OWNER = "TRANSFER_OWNER"
    ATTACH_COMMUNICATION_EVIDENCE = (
        "ATTACH_COMMUNICATION_EVIDENCE"
    )
    CREATE_FRAUD_HANDOFF = "CREATE_FRAUD_HANDOFF"


def _uuid(value: UUID, field_name: str) -> UUID:
    if not isinstance(value, UUID):
        raise LeadAcrlValidationError(
            f"{field_name} must be UUID"
        )
    return value


def _text(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise LeadAcrlValidationError(
            f"{field_name} must be non-empty text"
        )
    return value.strip()


def _time(value: datetime, field_name: str) -> datetime:
    if not isinstance(value, datetime):
        raise LeadAcrlValidationError(
            f"{field_name} must be datetime"
        )

    if value.tzinfo is None or value.utcoffset() is None:
        raise LeadAcrlValidationError(
            f"{field_name} must be timezone-aware"
        )

    return value.astimezone(timezone.utc)


@dataclass(frozen=True, slots=True)
class LeadAcrlIntegrationContract:
    operation_id: UUID
    tenant_id: UUID
    lead_id: UUID
    operation: ReosLeadOperation
    contract_version: int
    correlation_id: UUID
    idempotency_key: str
    precondition: LeadMutationPrecondition
    evidence_references: tuple[str, ...]
    checkpoint_reference: str | None
    expected_post_lead_revision: int | None
    expected_post_ownership_revision: int | None
    created_at: datetime
    handoff_reference: str | None = None

    def __post_init__(self) -> None:
        _uuid(self.operation_id, "operation_id")
        _uuid(self.tenant_id, "tenant_id")
        _uuid(self.lead_id, "lead_id")
        _uuid(self.correlation_id, "correlation_id")

        if not isinstance(
            self.operation,
            ReosLeadOperation,
        ):
            raise LeadAcrlValidationError(
                "operation must be ReosLeadOperation"
            )

        if (
            not isinstance(
                self.contract_version,
                int,
            )
            or self.contract_version < 1
        ):
            raise LeadAcrlValidationError(
                "contract_version must be >= 1"
            )

        object.__setattr__(
            self,
            "idempotency_key",
            _text(
                self.idempotency_key,
                "idempotency_key",
            ),
        )

        if not isinstance(
            self.precondition,
            LeadMutationPrecondition,
        ):
            raise LeadAcrlValidationError(
                "precondition must be LeadMutationPrecondition"
            )

        if self.precondition.tenant_id != self.tenant_id:
            raise LeadAcrlValidationError(
                "Precondition tenant does not match contract"
            )

        if self.precondition.lead_id != self.lead_id:
            raise LeadAcrlValidationError(
                "Precondition lead does not match contract"
            )

        evidence = tuple(
            dict.fromkeys(
                _text(
                    reference,
                    "evidence_reference",
                )
                for reference in self.evidence_references
            )
        )

        object.__setattr__(
            self,
            "evidence_references",
            evidence,
        )

        if self.checkpoint_reference is not None:
            object.__setattr__(
                self,
                "checkpoint_reference",
                _text(
                    self.checkpoint_reference,
                    "checkpoint_reference",
                ),
            )

        if self.handoff_reference is not None:
            object.__setattr__(
                self,
                "handoff_reference",
                _text(
                    self.handoff_reference,
                    "handoff_reference",
                ),
            )

        if (
            self.expected_post_lead_revision
            is not None
        ):
            if (
                not isinstance(
                    self.expected_post_lead_revision,
                    int,
                )
                or self.expected_post_lead_revision < 0
            ):
                raise LeadAcrlValidationError(
                    "expected_post_lead_revision must be non-negative integer"
                )

            if (
                self.expected_post_lead_revision
                < self.precondition.expected_lead_revision
            ):
                raise LeadAcrlValidationError(
                    "expected_post_lead_revision cannot be below precondition revision"
                )

        if (
            self.expected_post_ownership_revision
            is not None
        ):
            if (
                not isinstance(
                    self.expected_post_ownership_revision,
                    int,
                )
                or self.expected_post_ownership_revision < 0
            ):
                raise LeadAcrlValidationError(
                    "expected_post_ownership_revision must be non-negative integer"
                )

            if (
                self.precondition.expected_ownership_revision
                is not None
                and self.expected_post_ownership_revision
                < self.precondition.expected_ownership_revision
            ):
                raise LeadAcrlValidationError(
                    "expected_post_ownership_revision cannot be below precondition revision"
                )

        object.__setattr__(
            self,
            "created_at",
            _time(self.created_at, "created_at"),
        )

    @classmethod
    def create(
        cls,
        *,
        tenant_id: UUID,
        lead_id: UUID,
        operation: ReosLeadOperation,
        correlation_id: UUID,
        idempotency_key: str,
        precondition: LeadMutationPrecondition,
        evidence_references: tuple[str, ...] = (),
        checkpoint_reference: str | None = None,
        expected_post_lead_revision: int | None = None,
        expected_post_ownership_revision: int | None = None,
        handoff_reference: str | None = None,
        operation_id: UUID | None = None,
        contract_version: int = 1,
        created_at: datetime | None = None,
    ) -> "LeadAcrlIntegrationContract":
        return cls(
            operation_id=operation_id or uuid4(),
            tenant_id=tenant_id,
            lead_id=lead_id,
            operation=operation,
            contract_version=contract_version,
            correlation_id=correlation_id,
            idempotency_key=idempotency_key,
            precondition=precondition,
            evidence_references=evidence_references,
            checkpoint_reference=checkpoint_reference,
            expected_post_lead_revision=(
                expected_post_lead_revision
            ),
            expected_post_ownership_revision=(
                expected_post_ownership_revision
            ),
            created_at=(
                created_at
                or datetime.now(timezone.utc)
            ),
            handoff_reference=handoff_reference,
        )

    @property
    def contract_key(self) -> tuple[UUID, UUID, str]:
        return (
            self.tenant_id,
            self.lead_id,
            self.idempotency_key,
        )

    @property
    def fingerprint(self) -> str:
        payload = {
            "operation_id": str(self.operation_id),
            "tenant_id": str(self.tenant_id),
            "lead_id": str(self.lead_id),
            "operation": self.operation.value,
            "contract_version": self.contract_version,
            "correlation_id": str(self.correlation_id),
            "idempotency_key": self.idempotency_key,
            "precondition": self.precondition.to_dict(),
            "evidence_references": self.evidence_references,
            "checkpoint_reference": (
                self.checkpoint_reference
            ),
            "expected_post_lead_revision": (
                self.expected_post_lead_revision
            ),
            "expected_post_ownership_revision": (
                self.expected_post_ownership_revision
            ),
            "created_at": self.created_at.isoformat(),
            "handoff_reference": (
                self.handoff_reference
            ),
        }

        canonical = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
        )

        return hashlib.sha256(
            canonical.encode("utf-8")
        ).hexdigest()

    def validate_snapshot(
        self,
        snapshot: LeadConsistencySnapshot,
    ) -> None:
        try:
            self.precondition.validate_snapshot(
                snapshot
            )
        except Exception as exc:
            raise LeadAcrlPreconditionConflict(
                str(exc)
            ) from exc

    def validate_current_domain(
        self,
        lead: Lead,
        ownership: LeadOwnership | None,
    ) -> None:
        if lead.tenant_id != self.tenant_id:
            raise LeadAcrlPreconditionConflict(
                "Lead tenant does not match ACRL contract"
            )

        if lead.lead_id != self.lead_id:
            raise LeadAcrlPreconditionConflict(
                "Lead identity does not match ACRL contract"
            )

        snapshot = LeadConsistencySnapshot.capture(
            lead,
            ownership,
        )

        self.validate_snapshot(snapshot)

    def assert_compatible(
        self,
        other: "LeadAcrlIntegrationContract",
    ) -> None:
        if not isinstance(
            other,
            LeadAcrlIntegrationContract,
        ):
            raise LeadAcrlValidationError(
                "other must be LeadAcrlIntegrationContract"
            )

        if self.contract_key != other.contract_key:
            raise LeadAcrlPreconditionConflict(
                "ACRL contract identities differ"
            )

        if self.fingerprint != other.fingerprint:
            raise LeadAcrlPreconditionConflict(
                "Same idempotency key has conflicting contract"
            )

    def to_dict(self) -> dict[str, object]:
        return {
            "operation_id": str(self.operation_id),
            "tenant_id": str(self.tenant_id),
            "lead_id": str(self.lead_id),
            "operation": self.operation.value,
            "contract_version": self.contract_version,
            "correlation_id": str(
                self.correlation_id
            ),
            "idempotency_key": self.idempotency_key,
            "precondition": self.precondition.to_dict(),
            "evidence_references": list(
                self.evidence_references
            ),
            "checkpoint_reference": (
                self.checkpoint_reference
            ),
            "expected_post_lead_revision": (
                self.expected_post_lead_revision
            ),
            "expected_post_ownership_revision": (
                self.expected_post_ownership_revision
            ),
            "created_at": self.created_at.isoformat(),
            "handoff_reference": (
                self.handoff_reference
            ),
            "fingerprint": self.fingerprint,
        }
