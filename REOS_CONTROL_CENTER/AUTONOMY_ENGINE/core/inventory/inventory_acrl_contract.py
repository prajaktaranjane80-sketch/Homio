"""
CORE-004 T11 — ACRL Integration Contract

Owns:
- inventory reconstruction contract
- hierarchy reconstruction contract
- lifecycle reconstruction contract
- dependency discoverability
- contract discoverability
- evidence-reference discoverability
- checkpoint/recovery compatibility
- drift detection

Does NOT own:
- ACRL engine
- checkpoint storage
- recovery execution
- inventory persistence
- hierarchy persistence
- lifecycle engine
- provenance evidence storage
- REOS Control Center state
- execution authorization

ACRL remains the continuity/recovery authority.

CORE-004 exposes the minimum deterministic information ACRL needs to
reconstruct and verify inventory state.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
from typing import Any, Iterable, Mapping

from .inventory import Inventory
from .inventory_availability import AvailabilityState
from .inventory_hierarchy import (
    InventoryHierarchy,
)
from .inventory_lifecycle import (
    InventoryLifecycleHistory,
)
from .inventory_provenance import (
    InventoryProvenance,
)
from .inventory_contract import (
    CORE_004_SCHEMA_VERSION,
)


class InventoryACRLContractError(
    ValueError
):
    """Base CORE-004 -> ACRL contract error."""


class InventoryACRLValidationError(
    InventoryACRLContractError
):
    """Raised when ACRL contract data is invalid."""


class InventoryACRLDriftError(
    InventoryACRLContractError
):
    """Raised when reconstruction fingerprints drift."""


class InventoryACRLPreconditionConflict(
    InventoryACRLContractError
):
    """Raised when continuity preconditions are stale."""


class InventoryACRLOperation(str, Enum):
    RECONSTRUCT_INVENTORY = (
        "RECONSTRUCT_INVENTORY"
    )
    RECONSTRUCT_HIERARCHY = (
        "RECONSTRUCT_HIERARCHY"
    )
    RECONSTRUCT_LIFECYCLE = (
        "RECONSTRUCT_LIFECYCLE"
    )
    VERIFY_DEPENDENCIES = (
        "VERIFY_DEPENDENCIES"
    )
    VERIFY_CONTRACT = (
        "VERIFY_CONTRACT"
    )
    DETECT_DRIFT = (
        "DETECT_DRIFT"
    )


def _text(
    value: str,
    name: str,
) -> str:
    if not isinstance(value, str):
        raise InventoryACRLValidationError(
            f"{name} must be string."
        )

    value = value.strip()

    if not value:
        raise InventoryACRLValidationError(
            f"{name} cannot be empty."
        )

    return value


def _time(
    value: datetime,
    name: str,
) -> datetime:
    if not isinstance(
        value,
        datetime,
    ):
        raise InventoryACRLValidationError(
            f"{name} must be datetime."
        )

    if (
        value.tzinfo is None
        or value.utcoffset() is None
    ):
        raise InventoryACRLValidationError(
            f"{name} must be timezone-aware."
        )

    return value.astimezone(
        timezone.utc
    )


def _hash(
    payload: Mapping[str, Any],
) -> str:
    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,
    )

    return hashlib.sha256(
        canonical.encode("utf-8")
    ).hexdigest()


@dataclass(frozen=True, slots=True)
class InventoryReconstructionDescriptor:
    """
    Descriptor used by ACRL to identify the exact inventory aggregate
    expected during reconstruction.
    """

    tenant_id: str
    inventory_id: str
    contract_version: int
    inventory_version: int
    identity_fingerprint: str
    hierarchy_fingerprint: str | None
    lifecycle_fingerprint: str | None
    provenance_fingerprint: str | None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "tenant_id",
            _text(
                self.tenant_id,
                "tenant_id",
            ),
        )

        object.__setattr__(
            self,
            "inventory_id",
            _text(
                self.inventory_id,
                "inventory_id",
            ),
        )

        if (
            not isinstance(
                self.contract_version,
                int,
            )
            or self.contract_version < 1
        ):
            raise InventoryACRLValidationError(
                "contract_version must be >= 1."
            )

        if (
            not isinstance(
                self.inventory_version,
                int,
            )
            or self.inventory_version < 1
        ):
            raise InventoryACRLValidationError(
                "inventory_version must be >= 1."
            )

        object.__setattr__(
            self,
            "identity_fingerprint",
            _text(
                self.identity_fingerprint,
                "identity_fingerprint",
            ),
        )

        for name in (
            "hierarchy_fingerprint",
            "lifecycle_fingerprint",
            "provenance_fingerprint",
        ):
            value = getattr(
                self,
                name,
            )

            if value is not None:
                object.__setattr__(
                    self,
                    name,
                    _text(
                        value,
                        name,
                    ),
                )

    @property
    def reconstruction_key(self) -> tuple[
        str,
        str,
        int,
    ]:
        return (
            self.tenant_id,
            self.inventory_id,
            self.inventory_version,
        )

    @property
    def fingerprint(self) -> str:
        return _hash(
            {
                "tenant_id": self.tenant_id,
                "inventory_id": self.inventory_id,
                "contract_version": (
                    self.contract_version
                ),
                "inventory_version": (
                    self.inventory_version
                ),
                "identity_fingerprint": (
                    self.identity_fingerprint
                ),
                "hierarchy_fingerprint": (
                    self.hierarchy_fingerprint
                ),
                "lifecycle_fingerprint": (
                    self.lifecycle_fingerprint
                ),
                "provenance_fingerprint": (
                    self.provenance_fingerprint
                ),
            }
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "tenant_id": self.tenant_id,
            "inventory_id": self.inventory_id,
            "contract_version": self.contract_version,
            "inventory_version": self.inventory_version,
            "identity_fingerprint": (
                self.identity_fingerprint
            ),
            "hierarchy_fingerprint": (
                self.hierarchy_fingerprint
            ),
            "lifecycle_fingerprint": (
                self.lifecycle_fingerprint
            ),
            "provenance_fingerprint": (
                self.provenance_fingerprint
            ),
            "reconstruction_key": (
                self.reconstruction_key
            ),
            "fingerprint": self.fingerprint,
        }


@dataclass(frozen=True, slots=True)
class InventoryCheckpointDescriptor:
    """
    ACRL checkpoint reference.

    The checkpoint itself belongs to ACRL.
    CORE-004 stores only the correlation/verification contract.
    """

    checkpoint_id: str
    tenant_id: str
    inventory_id: str
    sequence: int
    inventory_version: int
    contract_fingerprint: str
    created_at: datetime

    def __post_init__(self) -> None:
        for field_name in (
            "checkpoint_id",
            "tenant_id",
            "inventory_id",
            "contract_fingerprint",
        ):
            object.__setattr__(
                self,
                field_name,
                _text(
                    getattr(self, field_name),
                    field_name,
                ),
            )

        if (
            not isinstance(
                self.sequence,
                int,
            )
            or self.sequence < 0
        ):
            raise InventoryACRLValidationError(
                "sequence must be non-negative integer."
            )

        if (
            not isinstance(
                self.inventory_version,
                int,
            )
            or self.inventory_version < 1
        ):
            raise InventoryACRLValidationError(
                "inventory_version must be >= 1."
            )

        object.__setattr__(
            self,
            "created_at",
            _time(
                self.created_at,
                "created_at",
            ),
        )


@dataclass(frozen=True, slots=True)
class InventoryACRLIntegrationContract:
    """
    Full CORE-004 continuity contract consumed by ACRL.
    """

    operation_id: str
    tenant_id: str
    inventory_id: str
    operation: InventoryACRLOperation
    contract_version: int
    correlation_id: str
    idempotency_key: str
    reconstruction: InventoryReconstructionDescriptor
    dependency_references: tuple[str, ...]
    contract_references: tuple[str, ...]
    evidence_references: tuple[str, ...]
    checkpoint: InventoryCheckpointDescriptor | None
    created_at: datetime

    def __post_init__(self) -> None:
        for field_name in (
            "operation_id",
            "tenant_id",
            "inventory_id",
            "correlation_id",
            "idempotency_key",
        ):
            object.__setattr__(
                self,
                field_name,
                _text(
                    getattr(
                        self,
                        field_name,
                    ),
                    field_name,
                ),
            )

        if not isinstance(
            self.operation,
            InventoryACRLOperation,
        ):
            raise InventoryACRLValidationError(
                "operation must be InventoryACRLOperation."
            )

        if (
            not isinstance(
                self.contract_version,
                int,
            )
            or self.contract_version < 1
        ):
            raise InventoryACRLValidationError(
                "contract_version must be >= 1."
            )

        if not isinstance(
            self.reconstruction,
            InventoryReconstructionDescriptor,
        ):
            raise InventoryACRLValidationError(
                "reconstruction descriptor is invalid."
            )



        for field_name in (
            "dependency_references",
            "contract_references",
            "evidence_references",
        ):
            values = tuple(
                dict.fromkeys(
                    _text(
                        item,
                        field_name,
                    )
                    for item in getattr(
                        self,
                        field_name,
                    )
                )
            )

            object.__setattr__(
                self,
                field_name,
                values,
            )

        if self.checkpoint is not None:
            if (
                self.checkpoint.tenant_id
                != self.tenant_id
                or self.checkpoint.inventory_id
                != self.inventory_id
            ):
                raise InventoryACRLValidationError(
                    "Checkpoint identity does not match "
                    "integration contract."
                )

        object.__setattr__(
            self,
            "created_at",
            _time(
                self.created_at,
                "created_at",
            ),
        )

    @property
    def contract_key(self) -> tuple[str, str, str]:
        return (
            self.tenant_id,
            self.inventory_id,
            self.idempotency_key,
        )

    @property
    def fingerprint(self) -> str:
        return _hash(
            {
                "operation_id": self.operation_id,
                "tenant_id": self.tenant_id,
                "inventory_id": self.inventory_id,
                "operation": self.operation.value,
                "contract_version": (
                    self.contract_version
                ),
                "correlation_id": self.correlation_id,
                "idempotency_key": (
                    self.idempotency_key
                ),
                "reconstruction": (
                    self.reconstruction.to_dict()
                ),
                "dependency_references": (
                    self.dependency_references
                ),
                "contract_references": (
                    self.contract_references
                ),
                "evidence_references": (
                    self.evidence_references
                ),
                "checkpoint": (
                    _checkpoint_to_dict(
                        self.checkpoint
                    )
                    if self.checkpoint is not None
                    else None
                ),
                "created_at": self.created_at.isoformat(),
            }
        )

    def assert_compatible(
        self,
        other: "InventoryACRLIntegrationContract",
    ) -> None:
        if not isinstance(
            other,
            InventoryACRLIntegrationContract,
        ):
            raise InventoryACRLValidationError(
                "other must be InventoryACRLIntegrationContract."
            )

        if self.contract_key != other.contract_key:
            raise InventoryACRLPreconditionConflict(
                "ACRL contract identities differ."
            )

        if self.fingerprint != other.fingerprint:
            raise InventoryACRLPreconditionConflict(
                "Same idempotency identity contains "
                "conflicting ACRL contract data."
            )

    def validate_current_inventory(
        self,
        inventory: Inventory,
    ) -> None:
        if inventory.tenant_id != self.tenant_id:
            raise InventoryACRLPreconditionConflict(
                "Inventory tenant does not match ACRL contract."
            )

        if inventory.inventory_id != self.inventory_id:
            raise InventoryACRLPreconditionConflict(
                "Inventory identity does not match ACRL contract."
            )

        if (
            inventory.version
            != self.reconstruction.inventory_version
        ):
            raise InventoryACRLPreconditionConflict(
                "Inventory version no longer matches "
                "reconstruction precondition."
            )

        if (
            inventory.identity_fingerprint
            != self.reconstruction.identity_fingerprint
        ):
            raise InventoryACRLDriftError(
                "Inventory identity fingerprint drift detected."
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "operation_id": self.operation_id,
            "tenant_id": self.tenant_id,
            "inventory_id": self.inventory_id,
            "operation": self.operation.value,
            "contract_version": self.contract_version,
            "correlation_id": self.correlation_id,
            "idempotency_key": self.idempotency_key,
            "reconstruction": (
                self.reconstruction.to_dict()
            ),
            "dependency_references": list(
                self.dependency_references
            ),
            "contract_references": list(
                self.contract_references
            ),
            "evidence_references": list(
                self.evidence_references
            ),
            "checkpoint": (
                _checkpoint_to_dict(
                    self.checkpoint
                )
                if self.checkpoint is not None
                else None
            ),
            "created_at": self.created_at.isoformat(),
            "fingerprint": self.fingerprint,
        }


def _checkpoint_to_dict(
    checkpoint: InventoryCheckpointDescriptor,
) -> dict[str, Any]:
    return {
        "checkpoint_id": checkpoint.checkpoint_id,
        "tenant_id": checkpoint.tenant_id,
        "inventory_id": checkpoint.inventory_id,
        "sequence": checkpoint.sequence,
        "inventory_version": (
            checkpoint.inventory_version
        ),
        "contract_fingerprint": (
            checkpoint.contract_fingerprint
        ),
        "created_at": checkpoint.created_at.isoformat(),
    }


def hierarchy_fingerprint(
    hierarchy: InventoryHierarchy,
) -> str:
    if not isinstance(
        hierarchy,
        InventoryHierarchy,
    ):
        raise InventoryACRLValidationError(
            "hierarchy must be InventoryHierarchy."
        )

    return _hash(
        hierarchy.to_dict()
    )


def lifecycle_fingerprint(
    history: Iterable[
        InventoryLifecycleHistory
    ],
) -> str:
    payload = [
        item.to_dict()
        for item in history
    ]

    return _hash(
        {
            "lifecycle_history": payload,
        }
    )


def provenance_fingerprint(
    provenance: InventoryProvenance,
) -> str:
    if not isinstance(
        provenance,
        InventoryProvenance,
    ):
        raise InventoryACRLValidationError(
            "provenance must be InventoryProvenance."
        )

    return _hash(
        provenance.to_dict()
    )


def detect_drift(
    *,
    expected_fingerprint: str,
    actual_fingerprint: str,
) -> bool:
    return expected_fingerprint != actual_fingerprint


def validate_checkpoint_compatibility(
    checkpoint: InventoryCheckpointDescriptor,
    inventory: Inventory,
) -> None:
    if checkpoint.tenant_id != inventory.tenant_id:
        raise InventoryACRLPreconditionConflict(
            "Checkpoint tenant does not match inventory."
        )

    if checkpoint.inventory_id != inventory.inventory_id:
        raise InventoryACRLPreconditionConflict(
            "Checkpoint inventory does not match inventory."
        )

    if checkpoint.inventory_version > inventory.version:
        raise InventoryACRLPreconditionConflict(
            "Checkpoint cannot reference a future inventory version."
        )


__all__ = [
    "InventoryACRLContractError",
    "InventoryACRLValidationError",
    "InventoryACRLDriftError",
    "InventoryACRLPreconditionConflict",
    "InventoryACRLOperation",
    "InventoryReconstructionDescriptor",
    "InventoryCheckpointDescriptor",
    "InventoryACRLIntegrationContract",
    "hierarchy_fingerprint",
    "lifecycle_fingerprint",
    "provenance_fingerprint",
    "detect_drift",
    "validate_checkpoint_compatibility",
]
