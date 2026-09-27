"""
CORE-004 T06 — Inventory Source & Provenance

Owns:
- source identity
- builder/developer reference
- acquisition reference
- source evidence references
- provenance metadata
- source history
- provenance integrity

Does NOT own:
- acquisition engine
- evidence storage
- inventory identity
- lifecycle
- availability
- commercial state
- concurrency
- authorization
- event transport
- REOS state
- ACRL execution

The acquisition reference is an external provenance reference.
CORE-004 does not acquire inventory and does not create a second
acquisition engine.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
from typing import Any, Mapping


class InventoryProvenanceError(ValueError):
    """Base provenance error."""


class ProvenanceIntegrityError(
    InventoryProvenanceError
):
    """Raised when provenance integrity is violated."""


class ProvenanceTenantViolation(
    InventoryProvenanceError
):
    """Raised when provenance crosses tenant boundaries."""


class SourceHistoryConflict(
    InventoryProvenanceError
):
    """Raised when provenance history is not contiguous."""


class InventorySourceType(str, Enum):
    BUILDER = "BUILDER"
    DEVELOPER = "DEVELOPER"
    BROKER = "BROKER"
    PARTNER = "PARTNER"
    DIRECT = "DIRECT"
    IMPORT = "IMPORT"
    API = "API"
    PLATFORM = "PLATFORM"


def _text(
    value: str,
    field_name: str,
) -> str:
    if not isinstance(value, str):
        raise InventoryProvenanceError(
            f"{field_name} must be string."
        )

    value = value.strip()

    if not value:
        raise InventoryProvenanceError(
            f"{field_name} cannot be empty."
        )

    return value


def _time(
    value: datetime,
    field_name: str,
) -> datetime:
    if not isinstance(value, datetime):
        raise InventoryProvenanceError(
            f"{field_name} must be datetime."
        )

    if value.tzinfo is None or value.utcoffset() is None:
        raise InventoryProvenanceError(
            f"{field_name} must be timezone-aware."
        )

    return value.astimezone(timezone.utc)


def _canonicalize(
    value: Any,
) -> Any:
    if isinstance(value, Enum):
        return value.value

    if isinstance(value, datetime):
        return _time(
            value,
            "datetime",
        ).isoformat()

    if isinstance(value, Mapping):
        return {
            str(key): _canonicalize(item)
            for key, item in sorted(
                value.items(),
                key=lambda pair: str(pair[0]),
            )
        }

    if isinstance(value, (list, tuple)):
        return [
            _canonicalize(item)
            for item in value
        ]

    if (
        value is None
        or isinstance(
            value,
            (str, int, float, bool),
        )
    ):
        return value

    raise InventoryProvenanceError(
        "Unsupported provenance value type: "
        f"{type(value).__name__}"
    )


def _fingerprint(
    payload: Mapping[str, Any],
) -> str:
    canonical = json.dumps(
        _canonicalize(payload),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )

    return hashlib.sha256(
        canonical.encode("utf-8")
    ).hexdigest()


@dataclass(frozen=True, slots=True)
class InventorySource:
    """
    Canonical source identity.

    `acquisition_reference` identifies an external acquisition process or
    source record. It is intentionally a reference, not an acquisition
    workflow implementation.
    """

    source_id: str
    tenant_id: str
    source_type: InventorySourceType
    source_reference: str
    builder_developer_id: str
    acquisition_reference: str | None = None
    channel_reference: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "source_id",
            _text(
                self.source_id,
                "source_id",
            ),
        )

        object.__setattr__(
            self,
            "tenant_id",
            _text(
                self.tenant_id,
                "tenant_id",
            ),
        )

        try:
            normalized_type = InventorySourceType(
                self.source_type
            )
        except (TypeError, ValueError) as exc:
            raise InventoryProvenanceError(
                "source_type is invalid."
            ) from exc

        object.__setattr__(
            self,
            "source_type",
            normalized_type,
        )

        object.__setattr__(
            self,
            "source_reference",
            _text(
                self.source_reference,
                "source_reference",
            ),
        )

        object.__setattr__(
            self,
            "builder_developer_id",
            _text(
                self.builder_developer_id,
                "builder_developer_id",
            ),
        )

        if self.acquisition_reference is not None:
            object.__setattr__(
                self,
                "acquisition_reference",
                _text(
                    self.acquisition_reference,
                    "acquisition_reference",
                ),
            )

        if self.channel_reference is not None:
            object.__setattr__(
                self,
                "channel_reference",
                _text(
                    self.channel_reference,
                    "channel_reference",
                ),
            )

        if not isinstance(
            self.metadata,
            Mapping,
        ):
            raise InventoryProvenanceError(
                "metadata must be mapping."
            )

        object.__setattr__(
            self,
            "metadata",
            {
                str(key): _canonicalize(item)
                for key, item in self.metadata.items()
            },
        )

    @property
    def identity_key(self) -> tuple[str, str, str]:
        return (
            self.tenant_id,
            self.source_id,
            self.source_reference,
        )

    @property
    def fingerprint(self) -> str:
        return _fingerprint(
            {
                "source_id": self.source_id,
                "tenant_id": self.tenant_id,
                "source_type": self.source_type.value,
                "source_reference": self.source_reference,
                "builder_developer_id": (
                    self.builder_developer_id
                ),
                "acquisition_reference": (
                    self.acquisition_reference
                ),
                "channel_reference": (
                    self.channel_reference
                ),
            }
        )

    def assert_tenant(
        self,
        tenant_id: str,
    ) -> None:
        if _text(tenant_id, "tenant_id") != self.tenant_id:
            raise ProvenanceTenantViolation(
                "Provenance belongs to another tenant."
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "tenant_id": self.tenant_id,
            "source_type": self.source_type.value,
            "source_reference": self.source_reference,
            "builder_developer_id": (
                self.builder_developer_id
            ),
            "acquisition_reference": (
                self.acquisition_reference
            ),
            "channel_reference": (
                self.channel_reference
            ),
            "metadata": dict(self.metadata),
            "fingerprint": self.fingerprint,
        }


@dataclass(frozen=True, slots=True)
class ProvenanceEvidenceReference:
    """
    Reference to evidence owned by another subsystem.

    CORE-004 stores the reference and integrity metadata only.
    """

    evidence_reference: str
    tenant_id: str
    evidence_type: str
    evidence_fingerprint: str
    recorded_at: datetime
    source_reference: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "evidence_reference",
            _text(
                self.evidence_reference,
                "evidence_reference",
            ),
        )

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
            "evidence_type",
            _text(
                self.evidence_type,
                "evidence_type",
            ),
        )

        object.__setattr__(
            self,
            "evidence_fingerprint",
            _text(
                self.evidence_fingerprint,
                "evidence_fingerprint",
            ),
        )

        if len(self.evidence_fingerprint) != 64:
            raise ProvenanceIntegrityError(
                "evidence_fingerprint must be SHA-256."
            )

        try:
            int(
                self.evidence_fingerprint,
                16,
            )
        except ValueError as exc:
            raise ProvenanceIntegrityError(
                "evidence_fingerprint must be hexadecimal."
            ) from exc

        object.__setattr__(
            self,
            "recorded_at",
            _time(
                self.recorded_at,
                "recorded_at",
            ),
        )

        object.__setattr__(
            self,
            "source_reference",
            _text(
                self.source_reference,
                "source_reference",
            ),
        )

    def assert_tenant(
        self,
        tenant_id: str,
    ) -> None:
        if _text(tenant_id, "tenant_id") != self.tenant_id:
            raise ProvenanceTenantViolation(
                "Evidence reference belongs to another tenant."
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "evidence_reference": self.evidence_reference,
            "tenant_id": self.tenant_id,
            "evidence_type": self.evidence_type,
            "evidence_fingerprint": self.evidence_fingerprint,
            "recorded_at": self.recorded_at.isoformat(),
            "source_reference": self.source_reference,
        }


@dataclass(frozen=True, slots=True)
class InventoryProvenance:
    """
    Immutable provenance snapshot for one inventory identity.
    """

    inventory_id: str
    tenant_id: str
    source: InventorySource
    evidence: tuple[
        ProvenanceEvidenceReference,
        ...
    ] = ()
    provenance_version: int = 1

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "inventory_id",
            _text(
                self.inventory_id,
                "inventory_id",
            ),
        )

        object.__setattr__(
            self,
            "tenant_id",
            _text(
                self.tenant_id,
                "tenant_id",
            ),
        )

        if not isinstance(
            self.source,
            InventorySource,
        ):
            raise InventoryProvenanceError(
                "source must be InventorySource."
            )

        if self.source.tenant_id != self.tenant_id:
            raise ProvenanceTenantViolation(
                "Inventory and source tenant mismatch."
            )

        if (
            not isinstance(
                self.provenance_version,
                int,
            )
            or self.provenance_version < 1
        ):
            raise InventoryProvenanceError(
                "provenance_version must be >= 1."
            )

        normalized = tuple(
            self.evidence
        )

        for item in normalized:
            if not isinstance(
                item,
                ProvenanceEvidenceReference,
            ):
                raise ProvenanceIntegrityError(
                    "Invalid provenance evidence reference."
                )

            if item.tenant_id != self.tenant_id:
                raise ProvenanceTenantViolation(
                    "Provenance evidence crosses tenant boundary."
                )

            if (
                item.source_reference
                != self.source.source_reference
            ):
                raise ProvenanceIntegrityError(
                    "Evidence source reference does not match "
                    "canonical source."
                )

        object.__setattr__(
            self,
            "evidence",
            normalized,
        )

    @property
    def fingerprint(self) -> str:
        return _fingerprint(
            {
                "inventory_id": self.inventory_id,
                "tenant_id": self.tenant_id,
                "source": self.source.to_dict(),
                "evidence": [
                    item.to_dict()
                    for item in self.evidence
                ],
                "provenance_version": (
                    self.provenance_version
                ),
            }
        )

    def assert_integrity(self) -> None:
        for evidence in self.evidence:
            if (
                evidence.tenant_id
                != self.tenant_id
            ):
                raise ProvenanceTenantViolation(
                    "Provenance evidence tenant mismatch."
                )

            if (
                evidence.source_reference
                != self.source.source_reference
            ):
                raise ProvenanceIntegrityError(
                    "Provenance evidence references "
                    "a different source."
                )

    def to_dict(self) -> dict[str, Any]:
        return {
            "inventory_id": self.inventory_id,
            "tenant_id": self.tenant_id,
            "source": self.source.to_dict(),
            "evidence": [
                item.to_dict()
                for item in self.evidence
            ],
            "provenance_version": (
                self.provenance_version
            ),
            "fingerprint": self.fingerprint,
        }


@dataclass(frozen=True, slots=True)
class ProvenanceHistoryEntry:
    """
    Immutable provenance history record.
    """

    inventory_id: str
    tenant_id: str
    version: int
    provenance_fingerprint: str
    occurred_at: datetime
    change_reference: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "inventory_id",
            _text(
                self.inventory_id,
                "inventory_id",
            ),
        )

        object.__setattr__(
            self,
            "tenant_id",
            _text(
                self.tenant_id,
                "tenant_id",
            ),
        )

        if (
            not isinstance(
                self.version,
                int,
            )
            or self.version < 1
        ):
            raise SourceHistoryConflict(
                "Provenance history version must be >= 1."
            )

        object.__setattr__(
            self,
            "provenance_fingerprint",
            _text(
                self.provenance_fingerprint,
                "provenance_fingerprint",
            ),
        )

        if len(self.provenance_fingerprint) != 64:
            raise SourceHistoryConflict(
                "provenance_fingerprint must be SHA-256."
            )

        object.__setattr__(
            self,
            "occurred_at",
            _time(
                self.occurred_at,
                "occurred_at",
            ),
        )

        object.__setattr__(
            self,
            "change_reference",
            _text(
                self.change_reference,
                "change_reference",
            ),
        )


def validate_provenance_history(
    history: tuple[
        ProvenanceHistoryEntry,
        ...
    ],
) -> None:
    previous_version: int | None = None
    previous_time: datetime | None = None
    inventory_id: str | None = None
    tenant_id: str | None = None

    for entry in history:
        if inventory_id is None:
            inventory_id = entry.inventory_id
        elif inventory_id != entry.inventory_id:
            raise SourceHistoryConflict(
                "Provenance history mixes inventories."
            )

        if tenant_id is None:
            tenant_id = entry.tenant_id
        elif tenant_id != entry.tenant_id:
            raise SourceHistoryConflict(
                "Provenance history crosses tenants."
            )

        if previous_version is not None:
            if entry.version != previous_version + 1:
                raise SourceHistoryConflict(
                    "Provenance history version gap."
                )

            if (
                previous_time is not None
                and entry.occurred_at < previous_time
            ):
                raise SourceHistoryConflict(
                    "Provenance history moved backward in time."
                )

        previous_version = entry.version
        previous_time = entry.occurred_at


__all__ = [
    "InventoryProvenanceError",
    "ProvenanceIntegrityError",
    "ProvenanceTenantViolation",
    "SourceHistoryConflict",
    "InventorySourceType",
    "InventorySource",
    "ProvenanceEvidenceReference",
    "InventoryProvenance",
    "ProvenanceHistoryEntry",
    "validate_provenance_history",
]
