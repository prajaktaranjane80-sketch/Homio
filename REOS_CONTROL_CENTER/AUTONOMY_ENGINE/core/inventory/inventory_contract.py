"""
CORE-004 T02 — Inventory Contract & Schema

Owns:
- project contract
- property contract
- unit contract
- strict schema validation
- schema versioning
- contract compatibility
- canonical serialization
- contract fingerprinting
- unknown/invalid contract-state rejection

Does NOT own:
- inventory identity
- hierarchy mutation
- lifecycle transitions
- availability transitions
- reservation handling
- allocation handling
- provenance
- commercial state
- concurrency coordination
- authorization
- event transport
- REOS Control Center state
- ACRL reconstruction

This module defines the external contract boundary around the canonical
CORE-004 domain objects. It is not a second domain model.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import hashlib
import json
from typing import Any, Mapping

from .inventory import (
    AvailabilityState,
    Inventory,
    InventoryIdentity,
    InventoryType,
    LifecycleState,
)
from .project import Project


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class InventoryContractError(ValueError):
    """Base CORE-004 contract error."""


class InventorySchemaError(InventoryContractError):
    """Raised when contract shape or field values are invalid."""


class InventorySchemaVersionError(
    InventoryContractError
):
    """Raised when a schema version is unsupported."""


class InventoryContractCompatibilityError(
    InventoryContractError
):
    """Raised when two contract definitions are incompatible."""


class InventorySerializationError(
    InventoryContractError
):
    """Raised when canonical serialization fails."""


class InventoryContractFingerprintError(
    InventoryContractError
):
    """Raised when a contract fingerprint is invalid."""


# ---------------------------------------------------------------------------
# Schema identity
# ---------------------------------------------------------------------------


CORE_004_SCHEMA_VERSION = 1

PROJECT_SCHEMA_NAME = "REOS.CORE-004.PROJECT"
PROPERTY_SCHEMA_NAME = "REOS.CORE-004.PROPERTY"
UNIT_SCHEMA_NAME = "REOS.CORE-004.UNIT"

SUPPORTED_SCHEMA_VERSIONS = frozenset(
    {
        CORE_004_SCHEMA_VERSION,
    }
)


# ---------------------------------------------------------------------------
# Canonical field contracts
# ---------------------------------------------------------------------------


PROJECT_FIELDS = (
    "project_id",
    "tenant_id",
    "developer_id",
    "project_code",
    "name",
    "metadata",
    "identity_fingerprint",
)


INVENTORY_FIELDS = (
    "identity",
    "name",
    "lifecycle",
    "availability",
    "created_at",
    "updated_at",
    "version",
    "metadata",
    "identity_fingerprint",
)


INVENTORY_IDENTITY_FIELDS = (
    "inventory_id",
    "tenant_id",
    "inventory_type",
    "developer_id",
    "project_id",
    "property_id",
    "unit_id",
)


# ---------------------------------------------------------------------------
# Immutable contract definition
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class InventoryContract:
    """
    Immutable description of one CORE-004 external contract.

    A contract is metadata about the accepted representation.
    It does not contain runtime inventory state.
    """

    schema_name: str
    schema_version: int
    required_fields: tuple[str, ...]
    expected_inventory_type: InventoryType | None = None
    allow_additional_fields: bool = False

    def __post_init__(self) -> None:
        if not isinstance(
            self.schema_name,
            str,
        ):
            raise InventorySchemaError(
                "schema_name must be a string."
            )

        if not self.schema_name.strip():
            raise InventorySchemaError(
                "schema_name cannot be empty."
            )

        if not isinstance(
            self.schema_version,
            int,
        ):
            raise InventorySchemaError(
                "schema_version must be an integer."
            )

        if self.schema_version < 1:
            raise InventorySchemaError(
                "schema_version must be >= 1."
            )

        normalized = tuple(
            dict.fromkeys(
                self.required_fields
            )
        )

        if normalized != self.required_fields:
            raise InventorySchemaError(
                "required_fields cannot contain duplicates."
            )

        if self.expected_inventory_type is not None:
            if not isinstance(
                self.expected_inventory_type,
                InventoryType,
            ):
                raise InventorySchemaError(
                    "expected_inventory_type must be "
                    "InventoryType."
                )

    @property
    def fingerprint(self) -> str:
        """
        Deterministic fingerprint of the contract definition.

        The fingerprint changes when:
        - schema name changes
        - schema version changes
        - required fields change
        - expected inventory type changes
        - additional-field policy changes
        """
        payload = {
            "schema_name": self.schema_name,
            "schema_version": self.schema_version,
            "required_fields": list(
                self.required_fields
            ),
            "expected_inventory_type": (
                self.expected_inventory_type.value
                if self.expected_inventory_type
                is not None
                else None
            ),
            "allow_additional_fields": (
                self.allow_additional_fields
            ),
        }

        return hashlib.sha256(
            _canonical_json(
                payload
            ).encode("utf-8")
        ).hexdigest()

    def validate_mapping(
        self,
        payload: Mapping[str, Any],
    ) -> None:
        """
        Validate exact contract shape.

        Missing and unknown fields both fail closed.
        """
        if not isinstance(
            payload,
            Mapping,
        ):
            raise InventorySchemaError(
                f"{self.schema_name} payload "
                "must be a mapping."
            )

        actual = set(
            payload.keys()
        )

        required = set(
            self.required_fields
        )

        missing = required - actual

        if missing:
            raise InventorySchemaError(
                f"{self.schema_name} missing required "
                f"fields: {sorted(missing)}"
            )

        if not self.allow_additional_fields:
            unknown = actual - required

            if unknown:
                raise InventorySchemaError(
                    f"{self.schema_name} contains "
                    f"unknown fields: {sorted(unknown)}"
                )

    def assert_compatible(
        self,
        other: "InventoryContract",
    ) -> None:
        """
        Require exact contract compatibility.

        CORE-004 fails closed instead of silently accepting a different
        schema version or contract family.
        """
        if not isinstance(
            other,
            InventoryContract,
        ):
            raise InventoryContractCompatibilityError(
                "other must be InventoryContract."
            )

        if self.schema_name != other.schema_name:
            raise InventoryContractCompatibilityError(
                "Contract families differ: "
                f"{self.schema_name!r} != "
                f"{other.schema_name!r}"
            )

        if (
            self.schema_version
            != other.schema_version
        ):
            raise InventoryContractCompatibilityError(
                "Contract schema versions differ: "
                f"{self.schema_version} != "
                f"{other.schema_version}"
            )

        if (
            self.required_fields
            != other.required_fields
        ):
            raise InventoryContractCompatibilityError(
                "Contract required-field definitions differ."
            )

        if (
            self.expected_inventory_type
            != other.expected_inventory_type
        ):
            raise InventoryContractCompatibilityError(
                "Contract inventory-type constraints differ."
            )

        if (
            self.allow_additional_fields
            != other.allow_additional_fields
        ):
            raise InventoryContractCompatibilityError(
                "Contract additional-field policy differs."
            )


# ---------------------------------------------------------------------------
# Canonical contract definitions
# ---------------------------------------------------------------------------


PROJECT_CONTRACT = InventoryContract(
    schema_name=PROJECT_SCHEMA_NAME,
    schema_version=CORE_004_SCHEMA_VERSION,
    required_fields=PROJECT_FIELDS,
)


PROPERTY_CONTRACT = InventoryContract(
    schema_name=PROPERTY_SCHEMA_NAME,
    schema_version=CORE_004_SCHEMA_VERSION,
    required_fields=INVENTORY_FIELDS,
    expected_inventory_type=InventoryType.PROPERTY,
)


UNIT_CONTRACT = InventoryContract(
    schema_name=UNIT_SCHEMA_NAME,
    schema_version=CORE_004_SCHEMA_VERSION,
    required_fields=INVENTORY_FIELDS,
    expected_inventory_type=InventoryType.UNIT,
)


# ---------------------------------------------------------------------------
# Primitive validation
# ---------------------------------------------------------------------------


def _require_text(
    value: Any,
    field_name: str,
) -> None:
    if not isinstance(
        value,
        str,
    ):
        raise InventorySchemaError(
            f"{field_name} must be string."
        )

    if not value.strip():
        raise InventorySchemaError(
            f"{field_name} cannot be empty."
        )


def _require_positive_integer(
    value: Any,
    field_name: str,
) -> None:
    if isinstance(
        value,
        bool,
    ):
        raise InventorySchemaError(
            f"{field_name} must be integer."
        )

    if not isinstance(
        value,
        int,
    ):
        raise InventorySchemaError(
            f"{field_name} must be integer."
        )

    if value < 1:
        raise InventorySchemaError(
            f"{field_name} must be >= 1."
        )


def _require_datetime(
    value: Any,
    field_name: str,
) -> None:
    if not isinstance(
        value,
        str,
    ):
        raise InventorySchemaError(
            f"{field_name} must be ISO datetime string."
        )

    try:
        datetime.fromisoformat(
            value.replace(
                "Z",
                "+00:00",
            )
        )
    except ValueError as exc:
        raise InventorySchemaError(
            f"{field_name} is not a valid ISO datetime."
        ) from exc


def _require_mapping(
    value: Any,
    field_name: str,
) -> Mapping[str, Any]:
    if not isinstance(
        value,
        Mapping,
    ):
        raise InventorySchemaError(
            f"{field_name} must be mapping."
        )

    return value


def _require_enum(
    value: Any,
    enum_type: type[Enum],
    field_name: str,
) -> None:
    allowed = {
        member.value
        for member in enum_type
    }

    if isinstance(
        value,
        enum_type,
    ):
        return

    if value not in allowed:
        raise InventorySchemaError(
            f"{field_name} contains invalid value "
            f"{value!r}; allowed={sorted(allowed)}"
        )


def _require_sha256(
    value: Any,
    field_name: str,
) -> None:
    _require_text(
        value,
        field_name,
    )

    if len(value) != 64:
        raise InventorySchemaError(
            f"{field_name} must be SHA-256 hexadecimal."
        )

    try:
        int(
            value,
            16,
        )
    except ValueError as exc:
        raise InventorySchemaError(
            f"{field_name} must be SHA-256 hexadecimal."
        ) from exc


# ---------------------------------------------------------------------------
# Project contract validation
# ---------------------------------------------------------------------------


def validate_project(
    project: Project,
) -> None:
    """
    Validate the canonical Project domain object.
    """
    if not isinstance(
        project,
        Project,
    ):
        raise InventorySchemaError(
            "project must be canonical CORE-004 Project."
        )

    payload = project.to_dict()

    validate_project_mapping(
        payload
    )


def validate_project_mapping(
    payload: Mapping[str, Any],
) -> None:
    """
    Validate serialized Project representation.
    """
    PROJECT_CONTRACT.validate_mapping(
        payload
    )

    _require_text(
        payload["project_id"],
        "project_id",
    )

    _require_text(
        payload["tenant_id"],
        "tenant_id",
    )

    _require_text(
        payload["developer_id"],
        "developer_id",
    )

    _require_text(
        payload["project_code"],
        "project_code",
    )

    _require_text(
        payload["name"],
        "name",
    )

    if not isinstance(
        payload["metadata"],
        Mapping,
    ):
        raise InventorySchemaError(
            "metadata must be mapping."
        )

    _require_sha256(
        payload["identity_fingerprint"],
        "identity_fingerprint",
    )

    expected = _project_identity_fingerprint(
        payload
    )

    if (
        payload["identity_fingerprint"]
        != expected
    ):
        raise InventoryContractFingerprintError(
            "Project identity fingerprint mismatch."
        )


def _project_identity_fingerprint(
    payload: Mapping[str, Any],
) -> str:
    identity = {
        "project_id": payload["project_id"],
        "tenant_id": payload["tenant_id"],
        "developer_id": payload["developer_id"],
        "project_code": payload["project_code"],
    }

    return hashlib.sha256(
        _canonical_json(
            identity
        ).encode("utf-8")
    ).hexdigest()


# ---------------------------------------------------------------------------
# Inventory identity contract
# ---------------------------------------------------------------------------


def validate_inventory_identity(
    identity: InventoryIdentity,
    *,
    expected_inventory_type: InventoryType | None = None,
) -> None:
    """
    Validate the canonical immutable InventoryIdentity.

    Hierarchy shape is checked here because it is part of the contract
    representation, but hierarchy relationships themselves belong to
    Part 03.
    """
    if not isinstance(
        identity,
        InventoryIdentity,
    ):
        raise InventorySchemaError(
            "identity must be InventoryIdentity."
        )

    validate_inventory_identity_mapping(
        identity.to_dict(),
        expected_inventory_type=(
            expected_inventory_type
        ),
        expected_fingerprint=identity.fingerprint,
    )


def validate_inventory_identity_mapping(
    payload: Mapping[str, Any],
    *,
    expected_inventory_type: InventoryType | None = None,
    expected_fingerprint: str | None = None,
) -> None:
    """
    Validate the exact serialized identity contract.
    """
    if not isinstance(
        payload,
        Mapping,
    ):
        raise InventorySchemaError(
            "identity must be mapping."
        )

    actual = set(
        payload.keys()
    )

    required = set(
        INVENTORY_IDENTITY_FIELDS
    )

    missing = required - actual

    if missing:
        raise InventorySchemaError(
            f"identity missing required fields: "
            f"{sorted(missing)}"
        )

    unknown = actual - required

    if unknown:
        raise InventorySchemaError(
            f"identity contains unknown fields: "
            f"{sorted(unknown)}"
        )

    _require_text(
        payload["inventory_id"],
        "identity.inventory_id",
    )

    _require_text(
        payload["tenant_id"],
        "identity.tenant_id",
    )

    _require_enum(
        payload["inventory_type"],
        InventoryType,
        "identity.inventory_type",
    )

    _require_text(
        payload["developer_id"],
        "identity.developer_id",
    )

    _require_text(
        payload["project_id"],
        "identity.project_id",
    )

    property_id = payload["property_id"]
    unit_id = payload["unit_id"]

    if property_id is not None:
        _require_text(
            property_id,
            "identity.property_id",
        )

    if unit_id is not None:
        _require_text(
            unit_id,
            "identity.unit_id",
        )

    inventory_type = InventoryType(
        payload["inventory_type"]
    )

    if expected_inventory_type is not None:
        if (
            inventory_type
            is not expected_inventory_type
        ):
            raise InventorySchemaError(
                "Inventory type does not match "
                "contract: "
                f"expected="
                f"{expected_inventory_type.value}, "
                f"actual="
                f"{inventory_type.value}"
            )

    _validate_identity_hierarchy(
        inventory_type,
        property_id,
        unit_id,
    )

    if expected_fingerprint is not None:
        actual_fingerprint = (
            _inventory_identity_fingerprint(
                payload
            )
        )

        if (
            actual_fingerprint
            != expected_fingerprint
        ):
            raise InventoryContractFingerprintError(
                "Inventory identity fingerprint "
                "does not match canonical identity."
            )


def _validate_identity_hierarchy(
    inventory_type: InventoryType,
    property_id: str | None,
    unit_id: str | None,
) -> None:
    if (
        inventory_type
        is InventoryType.DEVELOPMENT
    ):
        if (
            property_id is not None
            or unit_id is not None
        ):
            raise InventorySchemaError(
                "DEVELOPMENT identity cannot contain "
                "property_id or unit_id."
            )

    elif (
        inventory_type
        is InventoryType.PROPERTY
    ):
        if property_id is None:
            raise InventorySchemaError(
                "PROPERTY identity requires property_id."
            )

        if unit_id is not None:
            raise InventorySchemaError(
                "PROPERTY identity cannot contain unit_id."
            )

    elif (
        inventory_type
        is InventoryType.UNIT
    ):
        if property_id is None:
            raise InventorySchemaError(
                "UNIT identity requires property_id."
            )

        if unit_id is None:
            raise InventorySchemaError(
                "UNIT identity requires unit_id."
            )


def _inventory_identity_fingerprint(
    payload: Mapping[str, Any],
) -> str:
    immutable_identity = {
        "inventory_id": payload["inventory_id"],
        "tenant_id": payload["tenant_id"],
        "inventory_type": (
            payload["inventory_type"]
        ),
        "developer_id": payload["developer_id"],
        "project_id": payload["project_id"],
        "property_id": payload["property_id"],
        "unit_id": payload["unit_id"],
    }

    return hashlib.sha256(
        _canonical_json(
            immutable_identity
        ).encode("utf-8")
    ).hexdigest()


# ---------------------------------------------------------------------------
# Inventory / property / unit contract
# ---------------------------------------------------------------------------


def validate_inventory(
    inventory: Inventory,
) -> None:
    """
    Validate generic canonical Inventory representation.
    """
    if not isinstance(
        inventory,
        Inventory,
    ):
        raise InventorySchemaError(
            "inventory must be canonical CORE-004 Inventory."
        )

    validate_inventory_mapping(
        inventory.to_dict()
    )


def validate_property(
    inventory: Inventory,
) -> None:
    """
    Validate canonical PROPERTY inventory.
    """
    if not isinstance(
        inventory,
        Inventory,
    ):
        raise InventorySchemaError(
            "inventory must be canonical CORE-004 Inventory."
        )

    validate_inventory_mapping(
        inventory.to_dict(),
        expected_inventory_type=(
            InventoryType.PROPERTY
        ),
    )


def validate_unit(
    inventory: Inventory,
) -> None:
    """
    Validate canonical UNIT inventory.
    """
    if not isinstance(
        inventory,
        Inventory,
    ):
        raise InventorySchemaError(
            "inventory must be canonical CORE-004 Inventory."
        )

    validate_inventory_mapping(
        inventory.to_dict(),
        expected_inventory_type=(
            InventoryType.UNIT
        ),
    )


def validate_inventory_mapping(
    payload: Mapping[str, Any],
    *,
    expected_inventory_type: InventoryType | None = None,
) -> None:
    """
    Validate exact serialized Inventory contract.

    This method checks representation and immutable identity integrity.
    Lifecycle transition semantics are intentionally left to Part 04.
    Availability transition semantics are intentionally left to Part 05.
    """
    (
        PROPERTY_CONTRACT
        if expected_inventory_type
        is InventoryType.PROPERTY
        else (
            UNIT_CONTRACT
            if expected_inventory_type
            is InventoryType.UNIT
            else InventoryContract(
                schema_name=(
                    "REOS.CORE-004.INVENTORY"
                ),
                schema_version=(
                    CORE_004_SCHEMA_VERSION
                ),
                required_fields=INVENTORY_FIELDS,
            )
        )
    ).validate_mapping(
        payload
    )

    identity = _require_mapping(
        payload["identity"],
        "identity",
    )

    validate_inventory_identity_mapping(
        identity,
        expected_inventory_type=(
            expected_inventory_type
        ),
    )

    _require_text(
        payload["name"],
        "name",
    )

    _require_enum(
        payload["lifecycle"],
        LifecycleState,
        "lifecycle",
    )

    _require_enum(
        payload["availability"],
        AvailabilityState,
        "availability",
    )

    _require_datetime(
        payload["created_at"],
        "created_at",
    )

    _require_datetime(
        payload["updated_at"],
        "updated_at",
    )

    _require_positive_integer(
        payload["version"],
        "version",
    )

    if not isinstance(
        payload["metadata"],
        Mapping,
    ):
        raise InventorySchemaError(
            "metadata must be mapping."
        )

    _require_sha256(
        payload["identity_fingerprint"],
        "identity_fingerprint",
    )

    expected_fingerprint = (
        _inventory_identity_fingerprint(
            identity
        )
    )

    if (
        payload["identity_fingerprint"]
        != expected_fingerprint
    ):
        raise InventoryContractFingerprintError(
            "Inventory identity fingerprint mismatch."
        )

    created = _parse_datetime(
        payload["created_at"]
    )

    updated = _parse_datetime(
        payload["updated_at"]
    )

    if updated < created:
        raise InventorySchemaError(
            "updated_at cannot be earlier "
            "than created_at."
        )


# ---------------------------------------------------------------------------
# Schema versioning
# ---------------------------------------------------------------------------


def validate_schema_version(
    version: int,
) -> None:
    if not isinstance(
        version,
        int,
    ):
        raise InventorySchemaVersionError(
            "schema_version must be integer."
        )

    if version not in SUPPORTED_SCHEMA_VERSIONS:
        raise InventorySchemaVersionError(
            f"Unsupported CORE-004 schema version: "
            f"{version}"
        )


def schema_compatible(
    left: InventoryContract,
    right: InventoryContract,
) -> bool:
    """
    Conservative compatibility rule.

    The same contract family and exact schema version are compatible.
    Everything else fails closed.
    """
    if not isinstance(
        left,
        InventoryContract,
    ):
        return False

    if not isinstance(
        right,
        InventoryContract,
    ):
        return False

    try:
        validate_schema_version(
            left.schema_version
        )
        validate_schema_version(
            right.schema_version
        )
    except InventorySchemaVersionError:
        return False

    return (
        left.schema_name
        == right.schema_name
        and left.schema_version
        == right.schema_version
        and left.required_fields
        == right.required_fields
        and left.expected_inventory_type
        == right.expected_inventory_type
        and left.allow_additional_fields
        == right.allow_additional_fields
    )


def require_schema_compatibility(
    left: InventoryContract,
    right: InventoryContract,
) -> None:
    if not schema_compatible(
        left,
        right,
    ):
        raise InventoryContractCompatibilityError(
            "CORE-004 contracts are incompatible."
        )


# ---------------------------------------------------------------------------
# Canonical serialization
# ---------------------------------------------------------------------------


def project_payload(
    project: Project,
) -> dict[str, Any]:
    """
    Return the canonical serialized Project representation.
    """
    validate_project(
        project
    )

    return project.to_dict()


def property_payload(
    inventory: Inventory,
) -> dict[str, Any]:
    """
    Return the canonical serialized PROPERTY representation.
    """
    validate_property(
        inventory
    )

    return inventory.to_dict()


def unit_payload(
    inventory: Inventory,
) -> dict[str, Any]:
    """
    Return the canonical serialized UNIT representation.
    """
    validate_unit(
        inventory
    )

    return inventory.to_dict()


def serialize_project(
    project: Project,
) -> str:
    payload = project_payload(
        project
    )

    return _serialize(
        PROJECT_CONTRACT,
        payload,
    )


def serialize_property(
    inventory: Inventory,
) -> str:
    payload = property_payload(
        inventory
    )

    return _serialize(
        PROPERTY_CONTRACT,
        payload,
    )


def serialize_unit(
    inventory: Inventory,
) -> str:
    payload = unit_payload(
        inventory
    )

    return _serialize(
        UNIT_CONTRACT,
        payload,
    )


def _serialize(
    contract: InventoryContract,
    payload: Mapping[str, Any],
) -> str:
    envelope = {
        "schema_name": contract.schema_name,
        "schema_version": contract.schema_version,
        "contract_fingerprint": contract.fingerprint,
        "payload": payload,
    }

    try:
        return _canonical_json(
            envelope
        )
    except (
        TypeError,
        ValueError,
        InventoryContractError,
    ) as exc:
        raise InventorySerializationError(
            "CORE-004 contract serialization failed."
        ) from exc


def deserialize_contract(
    serialized: str,
) -> dict[str, Any]:
    """
    Parse and validate the outer contract envelope.

    This does not reconstruct a domain object.
    Reconstruction belongs to Part 03 / Part 11.
    """
    if not isinstance(
        serialized,
        str,
    ):
        raise InventorySerializationError(
            "serialized contract must be string."
        )

    try:
        payload = json.loads(
            serialized
        )
    except json.JSONDecodeError as exc:
        raise InventorySerializationError(
            "serialized contract is invalid JSON."
        ) from exc

    if not isinstance(
        payload,
        dict,
    ):
        raise InventorySerializationError(
            "serialized contract root must be object."
        )

    required = {
        "schema_name",
        "schema_version",
        "contract_fingerprint",
        "payload",
    }

    actual = set(
        payload.keys()
    )

    missing = required - actual

    if missing:
        raise InventorySerializationError(
            "serialized contract missing fields: "
            f"{sorted(missing)}"
        )

    unknown = actual - required

    if unknown:
        raise InventorySerializationError(
            "serialized contract contains unknown fields: "
            f"{sorted(unknown)}"
        )

    schema_name = payload[
        "schema_name"
    ]

    schema_version = payload[
        "schema_version"
    ]

    validate_schema_version(
        schema_version
    )

    contract = contract_by_name(
        schema_name
    )

    if (
        payload["contract_fingerprint"]
        != contract.fingerprint
    ):
        raise InventoryContractFingerprintError(
            "Contract fingerprint mismatch."
        )

    if not isinstance(
        payload["payload"],
        dict,
    ):
        raise InventorySerializationError(
            "serialized contract payload "
            "must be object."
        )

    return payload


# ---------------------------------------------------------------------------
# Fingerprint API
# ---------------------------------------------------------------------------


def project_contract_fingerprint() -> str:
    return PROJECT_CONTRACT.fingerprint


def property_contract_fingerprint() -> str:
    return PROPERTY_CONTRACT.fingerprint


def unit_contract_fingerprint() -> str:
    return UNIT_CONTRACT.fingerprint


def payload_fingerprint(
    payload: Mapping[str, Any],
) -> str:
    """
    Fingerprint the supplied payload.

    This is intentionally different from the contract fingerprint.
    """
    if not isinstance(
        payload,
        Mapping,
    ):
        raise InventoryContractError(
            "payload must be mapping."
        )

    return hashlib.sha256(
        _canonical_json(
            payload
        ).encode("utf-8")
    ).hexdigest()


# ---------------------------------------------------------------------------
# Contract lookup
# ---------------------------------------------------------------------------


def contract_by_name(
    schema_name: str,
) -> InventoryContract:
    if schema_name == PROJECT_SCHEMA_NAME:
        return PROJECT_CONTRACT

    if schema_name == PROPERTY_SCHEMA_NAME:
        return PROPERTY_CONTRACT

    if schema_name == UNIT_SCHEMA_NAME:
        return UNIT_CONTRACT

    raise InventoryContractError(
        f"Unknown CORE-004 contract: "
        f"{schema_name!r}"
    )


def contract_for_inventory_type(
    inventory_type: InventoryType,
) -> InventoryContract:
    if not isinstance(
        inventory_type,
        InventoryType,
    ):
        raise InventoryContractError(
            "inventory_type must be InventoryType."
        )

    if (
        inventory_type
        is InventoryType.PROPERTY
    ):
        return PROPERTY_CONTRACT

    if (
        inventory_type
        is InventoryType.UNIT
    ):
        return UNIT_CONTRACT

    raise InventoryContractError(
        "DEVELOPMENT inventory uses the Project "
        "contract rather than a PROPERTY/UNIT "
        "contract."
    )


# ---------------------------------------------------------------------------
# Canonical JSON helpers
# ---------------------------------------------------------------------------


def _canonicalize(
    value: Any,
) -> Any:
    if isinstance(
        value,
        Enum,
    ):
        return value.value

    if isinstance(
        value,
        Mapping,
    ):
        result: dict[str, Any] = {}

        for key, item in sorted(
            value.items(),
            key=lambda pair: str(pair[0]),
        ):
            result[str(key)] = _canonicalize(
                item
            )

        return result

    if isinstance(
        value,
        (list, tuple),
    ):
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

    raise InventorySerializationError(
        "Unsupported value type during "
        "canonical serialization: "
        f"{type(value).__name__}"
    )


def _canonical_json(
    value: Any,
) -> str:
    try:
        return json.dumps(
            _canonicalize(value),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
    except (
        TypeError,
        ValueError,
    ) as exc:
        raise InventorySerializationError(
            "Value cannot be canonically serialized."
        ) from exc


def _parse_datetime(
    value: str,
) -> datetime:
    try:
        return datetime.fromisoformat(
            value.replace(
                "Z",
                "+00:00",
            )
        )
    except ValueError as exc:
        raise InventorySchemaError(
            f"Invalid ISO datetime: {value!r}"
        ) from exc


__all__ = [
    "CORE_004_SCHEMA_VERSION",
    "PROJECT_SCHEMA_NAME",
    "PROPERTY_SCHEMA_NAME",
    "UNIT_SCHEMA_NAME",
    "SUPPORTED_SCHEMA_VERSIONS",
    "InventoryContractError",
    "InventorySchemaError",
    "InventorySchemaVersionError",
    "InventoryContractCompatibilityError",
    "InventorySerializationError",
    "InventoryContractFingerprintError",
    "InventoryContract",
    "PROJECT_CONTRACT",
    "PROPERTY_CONTRACT",
    "UNIT_CONTRACT",
    "validate_project",
    "validate_project_mapping",
    "validate_inventory_identity",
    "validate_inventory_identity_mapping",
    "validate_inventory",
    "validate_property",
    "validate_unit",
    "validate_inventory_mapping",
    "validate_schema_version",
    "schema_compatible",
    "require_schema_compatibility",
    "project_payload",
    "property_payload",
    "unit_payload",
    "serialize_project",
    "serialize_property",
    "serialize_unit",
    "deserialize_contract",
    "project_contract_fingerprint",
    "property_contract_fingerprint",
    "unit_contract_fingerprint",
    "payload_fingerprint",
    "contract_by_name",
    "contract_for_inventory_type",
]
