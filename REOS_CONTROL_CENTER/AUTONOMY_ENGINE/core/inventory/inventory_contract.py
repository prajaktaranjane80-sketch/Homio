"""CORE-004 Inventory Contract & Schema.

Part 02 of CORE-004.

This module is the canonical contract boundary for inventory-domain
serialization and validation.

Responsibilities
----------------
- Project contract validation
- Property contract validation
- Unit contract validation
- Strict schema validation
- Contract schema versioning
- Contract compatibility checks
- Deterministic serialization
- Contract fingerprinting
- Unknown/invalid state rejection

Non-responsibilities
--------------------
- No persistence
- No state.json mutation
- No repository mutation
- No acquisition engine
- No search engine
- No lifecycle engine
- No availability engine
- No evidence/audit store
- No event bus implementation
- No authorization engine

The module validates already-owned domain objects/payloads. It does not
become a second source of domain truth.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import hashlib
import json
import math
from typing import Any, Mapping, Sequence

from .inventory import AvailabilityState, InventoryType, LifecycleState
from .project import ProjectLifecycle, ProjectOperatingMode


# ---------------------------------------------------------------------------
# Contract constants
# ---------------------------------------------------------------------------

CURRENT_SCHEMA_VERSION = "1.0"
SUPPORTED_SCHEMA_VERSIONS = frozenset({CURRENT_SCHEMA_VERSION})

PROJECT_CONTRACT_NAME = "CORE-004.PROJECT"
PROPERTY_CONTRACT_NAME = "CORE-004.PROPERTY"
UNIT_CONTRACT_NAME = "CORE-004.UNIT"

SUPPORTED_CONTRACTS = frozenset(
    {
        PROJECT_CONTRACT_NAME,
        PROPERTY_CONTRACT_NAME,
        UNIT_CONTRACT_NAME,
    }
)


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class InventoryContractError(ValueError):
    """Base exception for CORE-004 contract violations."""


class ContractSchemaError(InventoryContractError):
    """Raised when a payload violates the declared schema."""


class UnknownContractFieldError(ContractSchemaError):
    """Raised when an unknown field is present in a strict contract."""

    def __init__(self, path: str, field: str) -> None:
        self.path = path
        self.field = field
        super().__init__(
            f"Unknown contract field at {path}: {field!r}"
        )


class MissingContractFieldError(ContractSchemaError):
    """Raised when a required field is missing."""

    def __init__(self, path: str, field: str) -> None:
        self.path = path
        self.field = field
        super().__init__(
            f"Missing required contract field at {path}: {field!r}"
        )


class InvalidContractValueError(ContractSchemaError):
    """Raised when a contract field contains an invalid value."""

    def __init__(
        self,
        path: str,
        expected: str,
        actual: Any,
    ) -> None:
        self.path = path
        self.expected = expected
        self.actual = actual
        super().__init__(
            f"Invalid contract value at {path}: "
            f"expected {expected}, got {actual!r}"
        )


class UnsupportedSchemaVersionError(InventoryContractError):
    """Raised when a schema version is not supported."""

    def __init__(self, version: str) -> None:
        self.version = version
        super().__init__(
            f"Unsupported CORE-004 schema version: {version!r}"
        )


class ContractCompatibilityError(InventoryContractError):
    """Raised when two schema versions are incompatible."""


class ContractSerializationError(InventoryContractError):
    """Raised when deterministic contract serialization fails."""


class ContractFingerprintMismatchError(InventoryContractError):
    """Raised when a contract fingerprint does not match."""


# ---------------------------------------------------------------------------
# Validation result
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ContractValidationResult:
    """Immutable result of a successful contract validation."""

    contract_name: str
    schema_version: str
    contract_fingerprint: str
    payload_fingerprint: str

    @property
    def valid(self) -> bool:
        """Successful validation is represented explicitly."""
        return True

    def to_dict(self) -> dict[str, str | bool]:
        """Return deterministic result data."""
        return {
            "contract_name": self.contract_name,
            "schema_version": self.schema_version,
            "contract_fingerprint": self.contract_fingerprint,
            "payload_fingerprint": self.payload_fingerprint,
            "valid": self.valid,
        }


# ---------------------------------------------------------------------------
# Contract specification
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ContractSpec:
    """Immutable schema specification."""

    name: str
    version: str
    required_fields: frozenset[str]
    optional_fields: frozenset[str]
    field_types: Mapping[str, str]

    @property
    def allowed_fields(self) -> frozenset[str]:
        return self.required_fields | self.optional_fields

    @property
    def fingerprint(self) -> str:
        """Fingerprint the schema definition, not a runtime payload."""
        canonical = _canonical_json(
            {
                "name": self.name,
                "version": self.version,
                "required_fields": sorted(self.required_fields),
                "optional_fields": sorted(self.optional_fields),
                "field_types": dict(sorted(self.field_types.items())),
            }
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Canonical schema definitions
# ---------------------------------------------------------------------------


_PROJECT_SPEC = ContractSpec(
    name=PROJECT_CONTRACT_NAME,
    version=CURRENT_SCHEMA_VERSION,
    required_fields=frozenset(
        {
            "project_id",
            "tenant_id",
            "developer_id",
            "project_code",
            "name",
            "lifecycle",
            "location",
            "operating_mode",
            "created_at",
            "updated_at",
            "version",
            "metadata",
            "source_of_truth",
        }
    ),
    optional_fields=frozenset(),
    field_types={
        "project_id": "string",
        "tenant_id": "string",
        "developer_id": "string",
        "project_code": "string",
        "name": "string",
        "lifecycle": "ProjectLifecycle",
        "location": "ProjectLocation",
        "operating_mode": "ProjectOperatingMode",
        "created_at": "datetime",
        "updated_at": "datetime",
        "version": "positive_integer",
        "metadata": "json_object",
        "source_of_truth": "literal:project",
    },
)


_IDENTITY_SPEC = ContractSpec(
    name="CORE-004.INVENTORY_IDENTITY",
    version=CURRENT_SCHEMA_VERSION,
    required_fields=frozenset(
        {
            "inventory_id",
            "tenant_id",
            "inventory_type",
            "developer_id",
            "project_id",
            "identity_key",
            "fingerprint",
        }
    ),
    optional_fields=frozenset(
        {
            "property_id",
            "unit_id",
        }
    ),
    field_types={
        "inventory_id": "string",
        "tenant_id": "string",
        "inventory_type": "InventoryType",
        "developer_id": "string",
        "project_id": "string",
        "property_id": "nullable_string",
        "unit_id": "nullable_string",
        "identity_key": "string",
        "fingerprint": "sha256",
    },
)


_INVENTORY_SPEC = ContractSpec(
    name="CORE-004.INVENTORY",
    version=CURRENT_SCHEMA_VERSION,
    required_fields=frozenset(
        {
            "identity",
            "name",
            "lifecycle",
            "availability",
            "created_at",
            "updated_at",
            "version",
            "metadata",
        }
    ),
    optional_fields=frozenset(),
    field_types={
        "identity": "mapping",
        "name": "string",
        "lifecycle": "LifecycleState",
        "availability": "AvailabilityState",
        "created_at": "datetime",
        "updated_at": "datetime",
        "version": "positive_integer",
        "metadata": "json_object",
    },
)


# ---------------------------------------------------------------------------
# Generic low-level helpers
# ---------------------------------------------------------------------------


def _canonical_json(value: Any) -> str:
    """Serialize JSON-compatible data deterministically."""
    try:
        _assert_json_safe(value, "$")
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise ContractSerializationError(
            f"Value cannot be deterministically serialized: {exc}"
        ) from exc


def _assert_json_safe(value: Any, path: str) -> None:
    """Reject non-contract-safe runtime values."""
    if value is None or isinstance(value, (str, bool, int)):
        return

    if isinstance(value, float):
        if not math.isfinite(value):
            raise InvalidContractValueError(
                path,
                "finite JSON number",
                value,
            )
        return

    if isinstance(value, Mapping):
        for key, child in value.items():
            if not isinstance(key, str):
                raise InvalidContractValueError(
                    path,
                    "string object keys",
                    key,
                )
            _assert_json_safe(child, f"{path}.{key}")
        return

    if isinstance(value, Sequence) and not isinstance(
        value,
        (str, bytes, bytearray),
    ):
        for index, child in enumerate(value):
            _assert_json_safe(child, f"{path}[{index}]")
        return

    raise InvalidContractValueError(
        path,
        "JSON-compatible value",
        type(value).__name__,
    )


def _require_mapping(value: Any, path: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise InvalidContractValueError(
            path,
            "mapping/object",
            value,
        )
    return value


def _require_string(value: Any, path: str) -> None:
    if not isinstance(value, str):
        raise InvalidContractValueError(
            path,
            "string",
            value,
        )

    if not value.strip():
        raise InvalidContractValueError(
            path,
            "non-empty string",
            value,
        )


def _require_nullable_string(value: Any, path: str) -> None:
    if value is None:
        return
    _require_string(value, path)


def _require_positive_integer(value: Any, path: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise InvalidContractValueError(
            path,
            "positive integer",
            value,
        )

    if value <= 0:
        raise InvalidContractValueError(
            path,
            "positive integer",
            value,
        )


def _require_datetime(value: Any, path: str) -> None:
    if isinstance(value, datetime):
        return

    if not isinstance(value, str):
        raise InvalidContractValueError(
            path,
            "ISO-8601 datetime string or datetime",
            value,
        )

    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise InvalidContractValueError(
            path,
            "valid ISO-8601 datetime",
            value,
        ) from exc


def _require_enum_value(
    value: Any,
    enum_type: type[Enum],
    path: str,
) -> None:
    values = {member.value for member in enum_type}

    if isinstance(value, enum_type):
        return

    if value not in values:
        raise InvalidContractValueError(
            path,
            f"one of {sorted(values)}",
            value,
        )


def _require_sha256(value: Any, path: str) -> None:
    _require_string(value, path)

    if len(value) != 64:
        raise InvalidContractValueError(
            path,
            "64-character SHA-256 hexadecimal digest",
            value,
        )

    try:
        int(value, 16)
    except ValueError as exc:
        raise InvalidContractValueError(
            path,
            "64-character SHA-256 hexadecimal digest",
            value,
        ) from exc


def _require_json_object(value: Any, path: str) -> None:
    if not isinstance(value, Mapping):
        raise InvalidContractValueError(
            path,
            "JSON object",
            value,
        )

    _assert_json_safe(value, path)


def _datetime_to_wire(value: Any, path: str) -> str:
    _require_datetime(value, path)

    if isinstance(value, datetime):
        return value.isoformat()

    return value


def _enum_to_wire(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    return value


def _normalize_wire_value(value: Any) -> Any:
    """Normalize known Python domain values into wire-safe JSON values."""
    if isinstance(value, Enum):
        return value.value

    if isinstance(value, datetime):
        return value.isoformat()

    if isinstance(value, Mapping):
        return {
            str(key): _normalize_wire_value(child)
            for key, child in value.items()
        }

    if isinstance(value, Sequence) and not isinstance(
        value,
        (str, bytes, bytearray),
    ):
        return [
            _normalize_wire_value(child)
            for child in value
        ]

    return value


def _validate_exact_fields(
    payload: Mapping[str, Any],
    spec: ContractSpec,
    path: str,
) -> None:
    actual_fields = set(payload.keys())

    unknown = actual_fields - spec.allowed_fields
    if unknown:
        field = sorted(unknown)[0]
        raise UnknownContractFieldError(
            path,
            field,
        )

    missing = spec.required_fields - actual_fields
    if missing:
        field = sorted(missing)[0]
        raise MissingContractFieldError(
            path,
            field,
        )


def _fingerprint_payload(payload: Mapping[str, Any]) -> str:
    canonical = _canonical_json(
        _normalize_wire_value(payload)
    )
    return hashlib.sha256(
        canonical.encode("utf-8")
    ).hexdigest()


# ---------------------------------------------------------------------------
# Schema version
# ---------------------------------------------------------------------------


def validate_schema_version(version: Any) -> str:
    """Validate and return a supported schema version."""
    if not isinstance(version, str):
        raise InvalidContractValueError(
            "$.schema_version",
            "string schema version",
            version,
        )

    if version not in SUPPORTED_SCHEMA_VERSIONS:
        raise UnsupportedSchemaVersionError(version)

    return version


def schema_major(version: str) -> int:
    """Return the major version component."""
    validate_schema_version(version)

    try:
        return int(version.split(".", 1)[0])
    except (IndexError, ValueError) as exc:
        raise UnsupportedSchemaVersionError(version) from exc


def schema_minor(version: str) -> int:
    """Return the minor version component."""
    validate_schema_version(version)

    try:
        return int(version.split(".", 1)[1])
    except (IndexError, ValueError) as exc:
        raise UnsupportedSchemaVersionError(version) from exc


# ---------------------------------------------------------------------------
# Compatibility
# ---------------------------------------------------------------------------


def contracts_compatible(
    source_version: str,
    target_version: str,
) -> bool:
    """Return whether two CORE-004 schema versions are compatible.

    Compatibility is intentionally conservative:
    - versions must be supported
    - major versions must match
    - a newer target minor version may consume an older source version
    """

    validate_schema_version(source_version)
    validate_schema_version(target_version)

    if schema_major(source_version) != schema_major(target_version):
        return False

    return schema_minor(source_version) <= schema_minor(
        target_version
    )


def require_contract_compatibility(
    source_version: str,
    target_version: str,
) -> None:
    """Fail closed when contract versions are incompatible."""
    if not contracts_compatible(
        source_version,
        target_version,
    ):
        raise ContractCompatibilityError(
            "CORE-004 contract versions are incompatible: "
            f"source={source_version!r}, "
            f"target={target_version!r}"
        )


# ---------------------------------------------------------------------------
# Project contract validation
# ---------------------------------------------------------------------------


def validate_project_contract(
    payload: Mapping[str, Any],
    *,
    expected_schema_version: str = CURRENT_SCHEMA_VERSION,
) -> ContractValidationResult:
    """Validate the canonical CORE-004 Project wire contract."""
    validate_schema_version(expected_schema_version)

    payload = _require_mapping(payload, "$")

    _validate_exact_fields(
        payload,
        _PROJECT_SPEC,
        "$.project",
    )

    _require_string(payload["project_id"], "$.project_id")
    _require_string(payload["tenant_id"], "$.tenant_id")
    _require_string(payload["developer_id"], "$.developer_id")
    _require_string(payload["project_code"], "$.project_code")
    _require_string(payload["name"], "$.name")

    _require_enum_value(
        payload["lifecycle"],
        ProjectLifecycle,
        "$.lifecycle",
    )

    location = _require_mapping(
        payload["location"],
        "$.location",
    )

    _validate_project_location(location)

    _require_enum_value(
        payload["operating_mode"],
        ProjectOperatingMode,
        "$.operating_mode",
    )

    _require_datetime(
        payload["created_at"],
        "$.created_at",
    )

    _require_datetime(
        payload["updated_at"],
        "$.updated_at",
    )

    _require_positive_integer(
        payload["version"],
        "$.version",
    )

    _require_json_object(
        payload["metadata"],
        "$.metadata",
    )

    if payload["source_of_truth"] != "project":
        raise InvalidContractValueError(
            "$.source_of_truth",
            "literal 'project'",
            payload["source_of_truth"],
        )

    _assert_timestamp_order(
        payload["created_at"],
        payload["updated_at"],
        "$.project",
    )

    normalized = _normalize_wire_value(payload)

    return ContractValidationResult(
        contract_name=PROJECT_CONTRACT_NAME,
        schema_version=expected_schema_version,
        contract_fingerprint=_PROJECT_SPEC.fingerprint,
        payload_fingerprint=_fingerprint_payload(normalized),
    )


def _validate_project_location(
    location: Mapping[str, Any],
) -> None:
    allowed = {
        "country_code",
        "state_code",
        "city",
        "postal_code",
        "address_line",
    }

    unknown = set(location) - allowed
    if unknown:
        field = sorted(unknown)[0]
        raise UnknownContractFieldError(
            "$.location",
            field,
        )

    required = {
        "country_code",
        "city",
    }

    missing = required - set(location)
    if missing:
        field = sorted(missing)[0]
        raise MissingContractFieldError(
            "$.location",
            field,
        )

    _require_string(
        location["country_code"],
        "$.location.country_code",
    )

    country_code = location["country_code"].upper()
    if len(country_code) != 2 or not country_code.isalpha():
        raise InvalidContractValueError(
            "$.location.country_code",
            "ISO-3166 alpha-2 country code",
            location["country_code"],
        )

    _require_string(
        location["city"],
        "$.location.city",
    )

    for field in (
        "state_code",
        "postal_code",
        "address_line",
    ):
        if field in location:
            _require_nullable_string(
                location[field],
                f"$.location.{field}",
            )


# ---------------------------------------------------------------------------
# Inventory identity contract
# ---------------------------------------------------------------------------


def validate_inventory_identity_contract(
    payload: Mapping[str, Any],
) -> None:
    """Validate canonical inventory identity."""
    payload = _require_mapping(payload, "$.identity")

    _validate_exact_fields(
        payload,
        _IDENTITY_SPEC,
        "$.identity",
    )

    _require_string(
        payload["inventory_id"],
        "$.identity.inventory_id",
    )

    _require_string(
        payload["tenant_id"],
        "$.identity.tenant_id",
    )

    _require_enum_value(
        payload["inventory_type"],
        InventoryType,
        "$.identity.inventory_type",
    )

    _require_string(
        payload["developer_id"],
        "$.identity.developer_id",
    )

    _require_string(
        payload["project_id"],
        "$.identity.project_id",
    )

    if "property_id" in payload:
        _require_nullable_string(
            payload["property_id"],
            "$.identity.property_id",
        )

    if "unit_id" in payload:
        _require_nullable_string(
            payload["unit_id"],
            "$.identity.unit_id",
        )

    _require_string(
        payload["identity_key"],
        "$.identity.identity_key",
    )

    _require_sha256(
        payload["fingerprint"],
        "$.identity.fingerprint",
    )

    inventory_type = _enum_wire_value(
        payload["inventory_type"]
    )

    property_id = payload.get("property_id")
    unit_id = payload.get("unit_id")

    if inventory_type == InventoryType.DEVELOPMENT.value:
        if property_id is not None or unit_id is not None:
            raise InvalidContractValueError(
                "$.identity",
                "development identity without property_id/unit_id",
                payload,
            )

    elif inventory_type == InventoryType.PROPERTY.value:
        if property_id is None:
            raise InvalidContractValueError(
                "$.identity.property_id",
                "property identity requires property_id",
                property_id,
            )

        if unit_id is not None:
            raise InvalidContractValueError(
                "$.identity.unit_id",
                "property identity must not contain unit_id",
                unit_id,
            )

    elif inventory_type == InventoryType.UNIT.value:
        if property_id is None:
            raise InvalidContractValueError(
                "$.identity.property_id",
                "unit identity requires property_id",
                property_id,
            )

        if unit_id is None:
            raise InvalidContractValueError(
                "$.identity.unit_id",
                "unit identity requires unit_id",
                unit_id,
            )

    else:
        raise InvalidContractValueError(
            "$.identity.inventory_type",
            "known InventoryType",
            inventory_type,
        )


# ---------------------------------------------------------------------------
# Inventory contract validation
# ---------------------------------------------------------------------------


def validate_inventory_contract(
    payload: Mapping[str, Any],
    *,
    expected_inventory_type: InventoryType | str | None = None,
) -> ContractValidationResult:
    """Validate canonical inventory serialization data."""
    payload = _require_mapping(payload, "$")

    _validate_exact_fields(
        payload,
        _INVENTORY_SPEC,
        "$.inventory",
    )

    validate_inventory_identity_contract(
        payload["identity"]
    )

    _require_string(
        payload["name"],
        "$.name",
    )

    _require_enum_value(
        payload["lifecycle"],
        LifecycleState,
        "$.lifecycle",
    )

    _require_enum_value(
        payload["availability"],
        AvailabilityState,
        "$.availability",
    )

    _require_datetime(
        payload["created_at"],
        "$.created_at",
    )

    _require_datetime(
        payload["updated_at"],
        "$.updated_at",
    )

    _require_positive_integer(
        payload["version"],
        "$.version",
    )

    _require_json_object(
        payload["metadata"],
        "$.metadata",
    )

    _assert_timestamp_order(
        payload["created_at"],
        payload["updated_at"],
        "$.inventory",
    )

    actual_inventory_type = _enum_wire_value(
        payload["identity"]["inventory_type"]
    )

    if expected_inventory_type is not None:
        expected = _enum_wire_value(expected_inventory_type)

        if actual_inventory_type != expected:
            raise InvalidContractValueError(
                "$.identity.inventory_type",
                f"inventory type {expected!r}",
                actual_inventory_type,
            )

    _validate_state_combination(
        lifecycle=_enum_wire_value(payload["lifecycle"]),
        availability=_enum_wire_value(payload["availability"]),
    )

    normalized = _normalize_wire_value(payload)

    contract_name = {
        InventoryType.PROPERTY.value: PROPERTY_CONTRACT_NAME,
        InventoryType.UNIT.value: UNIT_CONTRACT_NAME,
    }.get(
        actual_inventory_type,
        "CORE-004.INVENTORY",
    )

    contract_fingerprint = _inventory_contract_fingerprint(
        actual_inventory_type
    )

    return ContractValidationResult(
        contract_name=contract_name,
        schema_version=CURRENT_SCHEMA_VERSION,
        contract_fingerprint=contract_fingerprint,
        payload_fingerprint=_fingerprint_payload(normalized),
    )


def validate_property_contract(
    payload: Mapping[str, Any],
) -> ContractValidationResult:
    """Validate a property inventory contract."""
    return validate_inventory_contract(
        payload,
        expected_inventory_type=InventoryType.PROPERTY,
    )


def validate_unit_contract(
    payload: Mapping[str, Any],
) -> ContractValidationResult:
    """Validate a unit inventory contract."""
    return validate_inventory_contract(
        payload,
        expected_inventory_type=InventoryType.UNIT,
    )


def _inventory_contract_fingerprint(
    inventory_type: str,
) -> str:
    """Return a type-aware contract fingerprint."""
    if inventory_type == InventoryType.PROPERTY.value:
        contract = {
            "contract": PROPERTY_CONTRACT_NAME,
            "version": CURRENT_SCHEMA_VERSION,
            "identity": _IDENTITY_SPEC.fingerprint,
            "inventory": _INVENTORY_SPEC.fingerprint,
            "required_type": InventoryType.PROPERTY.value,
        }
    elif inventory_type == InventoryType.UNIT.value:
        contract = {
            "contract": UNIT_CONTRACT_NAME,
            "version": CURRENT_SCHEMA_VERSION,
            "identity": _IDENTITY_SPEC.fingerprint,
            "inventory": _INVENTORY_SPEC.fingerprint,
            "required_type": InventoryType.UNIT.value,
        }
    else:
        contract = {
            "contract": "CORE-004.INVENTORY",
            "version": CURRENT_SCHEMA_VERSION,
            "identity": _IDENTITY_SPEC.fingerprint,
            "inventory": _INVENTORY_SPEC.fingerprint,
            "required_type": inventory_type,
        }

    canonical = _canonical_json(contract)

    return hashlib.sha256(
        canonical.encode("utf-8")
    ).hexdigest()


# ---------------------------------------------------------------------------
# Cross-field state safety
# ---------------------------------------------------------------------------


def _validate_state_combination(
    *,
    lifecycle: str,
    availability: str,
) -> None:
    """Reject impossible lifecycle/availability combinations."""

    valid_pairs = {
        (
            LifecycleState.DRAFT.value,
            AvailabilityState.UNAVAILABLE.value,
        ),
        (
            LifecycleState.ACTIVE.value,
            AvailabilityState.AVAILABLE.value,
        ),
        (
            LifecycleState.ACTIVE.value,
            AvailabilityState.RESERVED.value,
        ),
        (
            LifecycleState.ACTIVE.value,
            AvailabilityState.BLOCKED.value,
        ),
        (
            LifecycleState.ACTIVE.value,
            AvailabilityState.ALLOCATED.value,
        ),
        (
            LifecycleState.ACTIVE.value,
            AvailabilityState.SOLD.value,
        ),
        (
            LifecycleState.ACTIVE.value,
            AvailabilityState.UNAVAILABLE.value,
        ),
        (
            LifecycleState.RESERVED.value,
            AvailabilityState.RESERVED.value,
        ),
        (
            LifecycleState.BLOCKED.value,
            AvailabilityState.BLOCKED.value,
        ),
        (
            LifecycleState.SOLD.value,
            AvailabilityState.SOLD.value,
        ),
        (
            LifecycleState.UNAVAILABLE.value,
            AvailabilityState.UNAVAILABLE.value,
        ),
        (
            LifecycleState.ARCHIVED.value,
            AvailabilityState.UNAVAILABLE.value,
        ),
    }

    if (lifecycle, availability) not in valid_pairs:
        raise InvalidContractValueError(
            "$",
            "valid lifecycle/availability state combination",
            {
                "lifecycle": lifecycle,
                "availability": availability,
            },
        )


# ---------------------------------------------------------------------------
# Serialization contract
# ---------------------------------------------------------------------------


def serialize_contract(
    *,
    contract_name: str,
    payload: Mapping[str, Any],
    schema_version: str = CURRENT_SCHEMA_VERSION,
) -> str:
    """Serialize a validated contract into a deterministic envelope."""
    if contract_name not in SUPPORTED_CONTRACTS:
        raise InventoryContractError(
            f"Unsupported CORE-004 contract: {contract_name!r}"
        )

    validate_schema_version(schema_version)

    payload = _require_mapping(payload, "$.payload")

    envelope = {
        "schema_version": schema_version,
        "contract_name": contract_name,
        "contract_fingerprint": contract_fingerprint(
            contract_name
        ),
        "payload": _normalize_wire_value(payload),
    }

    try:
        return _canonical_json(envelope)
    except ContractSerializationError:
        raise


def deserialize_contract(
    serialized: str,
) -> dict[str, Any]:
    """Deserialize a contract envelope and fail closed on ambiguity."""
    if not isinstance(serialized, str):
        raise ContractSerializationError(
            "Serialized contract must be a string."
        )

    try:
        decoded = json.loads(serialized)
    except json.JSONDecodeError as exc:
        raise ContractSerializationError(
            f"Invalid contract JSON: {exc}"
        ) from exc

    envelope = _require_mapping(decoded, "$")

    required = {
        "schema_version",
        "contract_name",
        "contract_fingerprint",
        "payload",
    }

    actual = set(envelope)
    unknown = actual - required
    if unknown:
        field = sorted(unknown)[0]
        raise UnknownContractFieldError(
            "$",
            field,
        )

    missing = required - actual
    if missing:
        field = sorted(missing)[0]
        raise MissingContractFieldError(
            "$",
            field,
        )

    version = validate_schema_version(
        envelope["schema_version"]
    )

    contract_name = envelope["contract_name"]
    if contract_name not in SUPPORTED_CONTRACTS:
        raise InventoryContractError(
            f"Unsupported CORE-004 contract: {contract_name!r}"
        )

    expected_fingerprint = contract_fingerprint(
        contract_name
    )

    if envelope["contract_fingerprint"] != expected_fingerprint:
        raise ContractFingerprintMismatchError(
            "Contract fingerprint mismatch: "
            f"expected {expected_fingerprint!r}, "
            f"received {envelope['contract_fingerprint']!r}"
        )

    payload = _require_mapping(
        envelope["payload"],
        "$.payload",
    )

    return {
        "schema_version": version,
        "contract_name": contract_name,
        "contract_fingerprint": expected_fingerprint,
        "payload": dict(payload),
    }


# ---------------------------------------------------------------------------
# Contract fingerprint API
# ---------------------------------------------------------------------------


def contract_fingerprint(
    contract_name: str,
) -> str:
    """Return deterministic fingerprint of the named contract."""
    if contract_name == PROJECT_CONTRACT_NAME:
        return _PROJECT_SPEC.fingerprint

    if contract_name == PROPERTY_CONTRACT_NAME:
        return _inventory_contract_fingerprint(
            InventoryType.PROPERTY.value
        )

    if contract_name == UNIT_CONTRACT_NAME:
        return _inventory_contract_fingerprint(
            InventoryType.UNIT.value
        )

    raise InventoryContractError(
        f"Unsupported CORE-004 contract: {contract_name!r}"
    )


# ---------------------------------------------------------------------------
# Domain-object adapters
# ---------------------------------------------------------------------------


def project_to_contract_payload(project: Any) -> dict[str, Any]:
    """Convert the canonical Project domain object to contract payload."""
    to_dict = getattr(project, "to_dict", None)

    if not callable(to_dict):
        raise InvalidContractValueError(
            "$.project",
            "canonical Project object with to_dict()",
            type(project).__name__,
        )

    payload = to_dict()

    validate_project_contract(payload)

    return _normalize_wire_value(payload)


def inventory_to_contract_payload(inventory: Any) -> dict[str, Any]:
    """Convert the canonical Inventory domain object to contract payload."""
    to_dict = getattr(inventory, "to_dict", None)

    if not callable(to_dict):
        raise InvalidContractValueError(
            "$.inventory",
            "canonical Inventory object with to_dict()",
            type(inventory).__name__,
        )

    payload = to_dict()

    validate_inventory_contract(payload)

    return _normalize_wire_value(payload)


# ---------------------------------------------------------------------------
# Contract verification API
# ---------------------------------------------------------------------------


def verify_serialized_contract(
    serialized: str,
) -> ContractValidationResult:
    """Deserialize and validate a serialized CORE-004 contract."""

    envelope = deserialize_contract(serialized)

    contract_name = envelope["contract_name"]
    payload = envelope["payload"]

    if contract_name == PROJECT_CONTRACT_NAME:
        result = validate_project_contract(
            payload,
            expected_schema_version=envelope["schema_version"],
        )

    elif contract_name == PROPERTY_CONTRACT_NAME:
        result = validate_property_contract(payload)

    elif contract_name == UNIT_CONTRACT_NAME:
        result = validate_unit_contract(payload)

    else:
        raise InventoryContractError(
            f"Unsupported CORE-004 contract: {contract_name!r}"
        )

    if (
        result.contract_fingerprint
        != envelope["contract_fingerprint"]
    ):
        raise ContractFingerprintMismatchError(
            "Serialized contract fingerprint does not match "
            "the validated contract."
        )

    return result


# ---------------------------------------------------------------------------
# Timestamp consistency
# ---------------------------------------------------------------------------


def _assert_timestamp_order(
    created_at: Any,
    updated_at: Any,
    path: str,
) -> None:
    """Ensure updated_at never precedes created_at."""
    created = _parse_datetime(created_at, f"{path}.created_at")
    updated = _parse_datetime(updated_at, f"{path}.updated_at")

    if updated < created:
        raise InvalidContractValueError(
            path,
            "updated_at >= created_at",
            {
                "created_at": created_at,
                "updated_at": updated_at,
            },
        )


def _parse_datetime(
    value: Any,
    path: str,
) -> datetime:
    if isinstance(value, datetime):
        return value

    _require_string(value, path)

    try:
        return datetime.fromisoformat(
            value.replace("Z", "+00:00")
        )
    except ValueError as exc:
        raise InvalidContractValueError(
            path,
            "valid ISO-8601 datetime",
            value,
        ) from exc


# ---------------------------------------------------------------------------
# Enum wire helpers
# ---------------------------------------------------------------------------


def _enum_wire_value(value: Any) -> Any:
    """Return enum values in canonical wire representation."""
    if isinstance(value, Enum):
        return value.value
    return value


# ---------------------------------------------------------------------------
# Public contract metadata
# ---------------------------------------------------------------------------


def supported_contracts() -> tuple[str, ...]:
    """Return supported contract names deterministically."""
    return tuple(sorted(SUPPORTED_CONTRACTS))


def supported_schema_versions() -> tuple[str, ...]:
    """Return supported schema versions deterministically."""
    return tuple(sorted(SUPPORTED_SCHEMA_VERSIONS))


def contract_metadata(
    contract_name: str,
) -> dict[str, Any]:
    """Return immutable-style metadata for a contract."""
    if contract_name not in SUPPORTED_CONTRACTS:
        raise InventoryContractError(
            f"Unsupported CORE-004 contract: {contract_name!r}"
        )

    return {
        "contract_name": contract_name,
        "schema_version": CURRENT_SCHEMA_VERSION,
        "contract_fingerprint": contract_fingerprint(
            contract_name
        ),
    }


__all__ = [
    "CURRENT_SCHEMA_VERSION",
    "SUPPORTED_SCHEMA_VERSIONS",
    "PROJECT_CONTRACT_NAME",
    "PROPERTY_CONTRACT_NAME",
    "UNIT_CONTRACT_NAME",
    "SUPPORTED_CONTRACTS",
    "InventoryContractError",
    "ContractSchemaError",
    "UnknownContractFieldError",
    "MissingContractFieldError",
    "InvalidContractValueError",
    "UnsupportedSchemaVersionError",
    "ContractCompatibilityError",
    "ContractSerializationError",
    "ContractFingerprintMismatchError",
    "ContractValidationResult",
    "ContractSpec",
    "validate_schema_version",
    "schema_major",
    "schema_minor",
    "contracts_compatible",
    "require_contract_compatibility",
    "validate_project_contract",
    "validate_inventory_identity_contract",
    "validate_inventory_contract",
    "validate_property_contract",
    "validate_unit_contract",
    "serialize_contract",
    "deserialize_contract",
    "contract_fingerprint",
    "project_to_contract_payload",
    "inventory_to_contract_payload",
    "verify_serialized_contract",
    "supported_contracts",
    "supported_schema_versions",
    "contract_metadata",
]
