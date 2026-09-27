"""
CORE-004 T01 — Project / Development Identity

Owns:
- canonical project/development identity
- tenant-scoped project identity
- developer reference
- project code
- immutable identity semantics
- project identity fingerprint

Does NOT own:
- inventory hierarchy
- property identity
- unit identity
- lifecycle transitions
- availability
- provenance
- commercial state
- concurrency
- authorization
- event transport
- REOS state
- ACRL reconstruction
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
import re
from types import MappingProxyType
from typing import Any, Mapping


class ProjectDomainError(ValueError):
    """Base CORE-004 project identity error."""


class ProjectTenantViolation(ProjectDomainError):
    """Raised when a project is accessed through another tenant."""


_PROJECT_CODE_PATTERN = re.compile(
    r"^[A-Z0-9][A-Z0-9_-]{1,63}$"
)


def _require_text(
    value: str,
    field_name: str,
) -> str:
    if not isinstance(value, str):
        raise ProjectDomainError(
            f"{field_name} must be a string."
        )

    normalized = value.strip()

    if not normalized:
        raise ProjectDomainError(
            f"{field_name} cannot be empty."
        )

    return normalized


def _validate_project_code(
    value: str,
) -> str:
    value = _require_text(
        value,
        "project_code",
    ).upper()

    if not _PROJECT_CODE_PATTERN.fullmatch(value):
        raise ProjectDomainError(
            "project_code must contain 2-64 uppercase "
            "letters, digits, '_' or '-'."
        )

    return value


def _freeze_json_mapping(
    value: Mapping[str, Any] | None,
) -> MappingProxyType:
    if value is None:
        return MappingProxyType({})

    if not isinstance(value, Mapping):
        raise ProjectDomainError(
            "metadata must be a mapping."
        )

    normalized: dict[str, Any] = {}

    for key, item in value.items():
        if not isinstance(key, str):
            raise ProjectDomainError(
                "metadata keys must be strings."
            )

        normalized[key] = _canonicalize(item)

    return MappingProxyType(normalized)


def _canonicalize(
    value: Any,
) -> Any:
    if value is None:
        return None

    if isinstance(value, (str, int, float, bool)):
        return value

    if isinstance(value, Mapping):
        result: dict[str, Any] = {}

        for key, item in sorted(
            value.items(),
            key=lambda pair: str(pair[0]),
        ):
            if not isinstance(key, str):
                raise ProjectDomainError(
                    "Nested metadata keys must be strings."
                )

            result[key] = _canonicalize(item)

        return result

    if isinstance(value, (list, tuple)):
        return [
            _canonicalize(item)
            for item in value
        ]

    raise ProjectDomainError(
        "Unsupported metadata value type: "
        f"{type(value).__name__}"
    )


def _canonical_json(
    value: Mapping[str, Any],
) -> bytes:
    try:
        return json.dumps(
            _canonicalize(value),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ProjectDomainError(
            "Project identity cannot be canonicalized."
        ) from exc


@dataclass(frozen=True, slots=True)
class ProjectIdentity:
    """
    Immutable canonical identity of one real-estate project/development.

    `project_id` is the technical identity.

    `project_code` is the tenant-scoped business identity.

    The pair:
        tenant_id + project_code

    is the stable business identity boundary.

    This class deliberately does not own project lifecycle or inventory
    relationships. Those belong to later CORE-004 contracts.
    """

    project_id: str
    tenant_id: str
    developer_id: str
    project_code: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "project_id",
            _require_text(
                self.project_id,
                "project_id",
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

        object.__setattr__(
            self,
            "developer_id",
            _require_text(
                self.developer_id,
                "developer_id",
            ),
        )

        object.__setattr__(
            self,
            "project_code",
            _validate_project_code(
                self.project_code,
            ),
        )

    @property
    def identity_key(self) -> str:
        """
        Tenant-scoped immutable business identity.
        """
        return (
            f"{self.tenant_id}:"
            f"{self.project_code}"
        )

    @property
    def fingerprint(self) -> str:
        """
        Deterministic identity fingerprint.

        Only immutable identity fields participate.
        """
        payload = {
            "project_id": self.project_id,
            "tenant_id": self.tenant_id,
            "developer_id": self.developer_id,
            "project_code": self.project_code,
        }

        return hashlib.sha256(
            _canonical_json(payload)
        ).hexdigest()

    def assert_tenant(
        self,
        tenant_id: str,
    ) -> None:
        tenant_id = _require_text(
            tenant_id,
            "tenant_id",
        )

        if tenant_id != self.tenant_id:
            raise ProjectTenantViolation(
                "Project belongs to another tenant."
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_id": self.project_id,
            "tenant_id": self.tenant_id,
            "developer_id": self.developer_id,
            "project_code": self.project_code,
        }


@dataclass(frozen=True, slots=True)
class Project:
    """
    Canonical CORE-004 project/development identity holder.

    This object is intentionally narrow.

    Lifecycle, hierarchy, commercial state and source provenance are
    implemented by their dedicated CORE-004 layers.
    """

    identity: ProjectIdentity
    name: str
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(
            self.identity,
            ProjectIdentity,
        ):
            raise ProjectDomainError(
                "identity must be ProjectIdentity."
            )

        object.__setattr__(
            self,
            "name",
            _require_text(
                self.name,
                "name",
            ),
        )

        object.__setattr__(
            self,
            "metadata",
            _freeze_json_mapping(
                self.metadata,
            ),
        )

    @property
    def project_id(self) -> str:
        return self.identity.project_id

    @property
    def tenant_id(self) -> str:
        return self.identity.tenant_id

    @property
    def developer_id(self) -> str:
        return self.identity.developer_id

    @property
    def project_code(self) -> str:
        return self.identity.project_code

    @property
    def identity_key(self) -> str:
        return self.identity.identity_key

    @property
    def identity_fingerprint(self) -> str:
        return self.identity.fingerprint

    def assert_tenant(
        self,
        tenant_id: str,
    ) -> None:
        self.identity.assert_tenant(
            tenant_id
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_id": self.project_id,
            "tenant_id": self.tenant_id,
            "developer_id": self.developer_id,
            "project_code": self.project_code,
            "name": self.name,
            "metadata": dict(self.metadata),
            "identity_fingerprint": (
                self.identity_fingerprint
            ),
        }


__all__ = [
    "Project",
    "ProjectDomainError",
    "ProjectIdentity",
    "ProjectTenantViolation",
]
