"""Canonical project identity inside the CORE-004 inventory boundary.

This is a domain model, not an acquisition engine, persistence layer or
second project service.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from enum import Enum
import re
from types import MappingProxyType
from typing import Any, Mapping
from uuid import uuid4


class ProjectDomainError(ValueError):
    """Base error for invalid project-domain operations."""


class ProjectTenantViolation(ProjectDomainError):
    """Raised when a caller crosses the project tenant boundary."""


class ProjectTransitionError(ProjectDomainError):
    """Raised when a project lifecycle transition is invalid."""


class ProjectLifecycle(str, Enum):
    DRAFT = "DRAFT"
    ONBOARDING = "ONBOARDING"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    ARCHIVED = "ARCHIVED"


class ProjectOperatingMode(str, Enum):
    OUR_OWNED_INTERNATIONAL_BROKERAGE = (
        "OUR_OWNED_INTERNATIONAL_BROKERAGE"
    )
    BROKER_SAAS = "BROKER_SAAS"
    BUILDER_SAAS = "BUILDER_SAAS"
    ENTERPRISE_WHITE_LABEL = "ENTERPRISE_WHITE_LABEL"
    PLATFORM_API_PARTNER = "PLATFORM_API_PARTNER"


_ALLOWED_TRANSITIONS = {
    ProjectLifecycle.DRAFT: frozenset(
        {
            ProjectLifecycle.ONBOARDING,
            ProjectLifecycle.ARCHIVED,
        }
    ),
    ProjectLifecycle.ONBOARDING: frozenset(
        {
            ProjectLifecycle.ACTIVE,
            ProjectLifecycle.SUSPENDED,
            ProjectLifecycle.ARCHIVED,
        }
    ),
    ProjectLifecycle.ACTIVE: frozenset(
        {
            ProjectLifecycle.SUSPENDED,
            ProjectLifecycle.ARCHIVED,
        }
    ),
    ProjectLifecycle.SUSPENDED: frozenset(
        {
            ProjectLifecycle.ONBOARDING,
            ProjectLifecycle.ACTIVE,
            ProjectLifecycle.ARCHIVED,
        }
    ),
    ProjectLifecycle.ARCHIVED: frozenset(),
}

_PROJECT_CODE = re.compile(r"[A-Z0-9][A-Z0-9_-]{1,63}")
_COUNTRY_CODE = re.compile(r"[A-Z]{2}")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _freeze_metadata(
    value: Mapping[str, Any] | None,
) -> MappingProxyType:
    if value is None:
        return MappingProxyType({})

    if not isinstance(value, Mapping):
        raise ProjectDomainError("metadata must be a mapping.")

    return MappingProxyType(
        {str(key): item for key, item in value.items()}
    )


@dataclass(frozen=True)
class ProjectLocation:
    """Canonical geographic identity of a real-estate project."""

    country_code: str
    region: str
    city: str
    postal_code: str | None = None
    address_line: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.country_code, str):
            raise ProjectDomainError(
                "country_code must be a string."
            )

        country = self.country_code.strip().upper()

        if not _COUNTRY_CODE.fullmatch(country):
            raise ProjectDomainError(
                "country_code must be an ISO-3166 alpha-2 code."
            )

        if not isinstance(self.region, str) or not self.region.strip():
            raise ProjectDomainError("region is required.")

        if not isinstance(self.city, str) or not self.city.strip():
            raise ProjectDomainError("city is required.")

        object.__setattr__(
            self,
            "country_code",
            country,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            key: value
            for key, value in {
                "country_code": self.country_code,
                "region": self.region,
                "city": self.city,
                "postal_code": self.postal_code,
                "address_line": self.address_line,
            }.items()
            if value is not None
        }


@dataclass(frozen=True)
class ProjectEvent:
    """Persistence-neutral event emitted by a project state change."""

    event_id: str
    event_type: str
    project_id: str
    tenant_id: str
    project_version: int
    occurred_at: str
    payload: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.event_id, str) or not self.event_id.strip():
            raise ProjectDomainError("event_id is required.")

        if not isinstance(self.event_type, str) or not self.event_type.strip():
            raise ProjectDomainError("event_type is required.")

        if not isinstance(self.project_id, str) or not self.project_id.strip():
            raise ProjectDomainError("project_id is required.")

        if not isinstance(self.tenant_id, str) or not self.tenant_id.strip():
            raise ProjectDomainError("tenant_id is required.")

        if (
            not isinstance(self.project_version, int)
            or self.project_version < 1
        ):
            raise ProjectDomainError(
                "project_version must be a positive integer."
            )

        object.__setattr__(
            self,
            "payload",
            _freeze_metadata(self.payload),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "project_id": self.project_id,
            "tenant_id": self.tenant_id,
            "project_version": self.project_version,
            "occurred_at": self.occurred_at,
            "payload": dict(self.payload),
        }


@dataclass(frozen=True)
class Project:
    """Authoritative project aggregate for CORE-004."""

    project_id: str
    tenant_id: str
    developer_id: str
    project_code: str
    name: str
    lifecycle: ProjectLifecycle
    location: ProjectLocation
    operating_mode: ProjectOperatingMode
    created_at: str
    updated_at: str
    version: int = 1
    metadata: Mapping[str, Any] = field(default_factory=dict)
    source_of_truth: str = "project"

    def __post_init__(self) -> None:
        for field_name in (
            "project_id",
            "tenant_id",
            "developer_id",
            "project_code",
            "name",
        ):
            value = getattr(self, field_name)

            if not isinstance(value, str) or not value.strip():
                raise ProjectDomainError(
                    f"{field_name} is required."
                )

        if not _PROJECT_CODE.fullmatch(self.project_code):
            raise ProjectDomainError(
                "project_code must be 2-64 characters using uppercase "
                "letters, digits, '_' or '-'."
            )

        if not isinstance(self.location, ProjectLocation):
            raise ProjectDomainError(
                "location must be a ProjectLocation."
            )

        try:
            lifecycle = ProjectLifecycle(self.lifecycle)
            operating_mode = ProjectOperatingMode(self.operating_mode)
        except (TypeError, ValueError) as exc:
            raise ProjectDomainError(
                "Invalid project lifecycle or operating mode."
            ) from exc

        object.__setattr__(
            self,
            "lifecycle",
            lifecycle,
        )

        object.__setattr__(
            self,
            "operating_mode",
            operating_mode,
        )

        if (
            not isinstance(self.version, int)
            or self.version < 1
        ):
            raise ProjectDomainError("version must be >= 1.")

        if self.source_of_truth != "project":
            raise ProjectDomainError(
                "project must remain the authoritative source of truth."
            )

        object.__setattr__(
            self,
            "metadata",
            _freeze_metadata(self.metadata),
        )

    @classmethod
    def create(
        cls,
        *,
        tenant_id: str,
        developer_id: str,
        project_code: str,
        name: str,
        location: ProjectLocation,
        operating_mode: ProjectOperatingMode,
        metadata: Mapping[str, Any] | None = None,
        project_id: str | None = None,
        at: str | None = None,
    ) -> "Project":
        timestamp = at or _utc_now()

        return cls(
            project_id=project_id or str(uuid4()),
            tenant_id=tenant_id,
            developer_id=developer_id,
            project_code=project_code,
            name=name,
            lifecycle=ProjectLifecycle.DRAFT,
            location=location,
            operating_mode=operating_mode,
            created_at=timestamp,
            updated_at=timestamp,
            metadata=metadata or {},
        )

    @property
    def identity_key(self) -> str:
        return f"{self.tenant_id}:{self.project_code}"

    def assert_tenant(self, tenant_id: str) -> None:
        if tenant_id != self.tenant_id:
            raise ProjectTenantViolation(
                "Project belongs to a different tenant."
            )

    def transition(
        self,
        target: ProjectLifecycle,
        *,
        tenant_id: str,
        at: str | None = None,
    ) -> tuple["Project", ProjectEvent]:
        self.assert_tenant(tenant_id)

        try:
            target = ProjectLifecycle(target)
        except (TypeError, ValueError) as exc:
            raise ProjectTransitionError(
                "Invalid target project lifecycle."
            ) from exc

        if target not in _ALLOWED_TRANSITIONS[self.lifecycle]:
            raise ProjectTransitionError(
                "Invalid project lifecycle transition: "
                f"{self.lifecycle.value} -> {target.value}."
            )

        timestamp = at or _utc_now()

        updated = replace(
            self,
            lifecycle=target,
            updated_at=timestamp,
            version=self.version + 1,
        )

        event = ProjectEvent(
            event_id=str(uuid4()),
            event_type="PROJECT_LIFECYCLE_CHANGED",
            project_id=self.project_id,
            tenant_id=self.tenant_id,
            project_version=updated.version,
            occurred_at=timestamp,
            payload={
                "from": self.lifecycle.value,
                "to": target.value,
                "identity_key": self.identity_key,
            },
        )

        return updated, event

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_id": self.project_id,
            "tenant_id": self.tenant_id,
            "developer_id": self.developer_id,
            "project_code": self.project_code,
            "name": self.name,
            "lifecycle": self.lifecycle.value,
            "location": self.location.to_dict(),
            "operating_mode": self.operating_mode.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "version": self.version,
            "metadata": dict(self.metadata),
            "source_of_truth": self.source_of_truth,
        }


__all__ = [
    "Project",
    "ProjectDomainError",
    "ProjectEvent",
    "ProjectLifecycle",
    "ProjectLocation",
    "ProjectOperatingMode",
    "ProjectTenantViolation",
    "ProjectTransitionError",
]
