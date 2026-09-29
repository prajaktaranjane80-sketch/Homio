from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from enum import StrEnum
from re import fullmatch
from uuid import UUID, uuid4


_SLUG_PATTERN = r"^[a-z0-9][a-z0-9._-]{1,62}[a-z0-9]$"
_KEY_PATTERN = r"^[a-z0-9][a-z0-9._:-]{0,127}$"
_ATTRIBUTE_KEY_PATTERN = r"^[a-z0-9][a-z0-9._:-]{0,127}$"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _required_text(value: str, field_name: str, max_length: int) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    value = value.strip()
    if not value:
        raise ValueError(f"{field_name} cannot be empty")
    if len(value) > max_length:
        raise ValueError(f"{field_name} exceeds {max_length} characters")
    return value


def _normalize_slug(value: str, field_name: str = "slug") -> str:
    candidate = _required_text(value, field_name, 64).lower()
    if not fullmatch(_SLUG_PATTERN, candidate):
        raise ValueError(
            f"{field_name} must be 3-64 characters, lowercase, and contain "
            "only letters, digits, '.', '_' or '-'"
        )
    return candidate


def _normalize_key(value: str, field_name: str = "key") -> str:
    candidate = _required_text(value, field_name, 128).lower()
    if not fullmatch(_KEY_PATTERN, candidate):
        raise ValueError(
            f"{field_name} must contain only letters, digits, "
            "dot, underscore, colon or hyphen"
        )
    return candidate


def _normalize_attribute_key(value: str) -> str:
    candidate = _required_text(value, "attribute_key", 128).lower()
    if not fullmatch(_ATTRIBUTE_KEY_PATTERN, candidate):
        raise ValueError(
            "attribute_key must contain only letters, digits, "
            "dot, underscore, colon or hyphen"
        )
    return candidate


def _validate_uuid(value: UUID, field_name: str) -> UUID:
    if not isinstance(value, UUID):
        raise TypeError(f"{field_name} must be UUID")
    return value


def _validate_optional_uuid(value: UUID | None, field_name: str) -> UUID | None:
    if value is None:
        return None
    return _validate_uuid(value, field_name)


def _validate_aware(value: datetime, field_name: str) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError(f"{field_name} must be datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value


def _validate_time_window(
    valid_from: datetime | None,
    valid_until: datetime | None,
) -> tuple[datetime | None, datetime | None]:
    if valid_from is not None:
        valid_from = _validate_aware(valid_from, "valid_from")
    if valid_until is not None:
        valid_until = _validate_aware(valid_until, "valid_until")
    if (
        valid_from is not None
        and valid_until is not None
        and valid_until <= valid_from
    ):
        raise ValueError("valid_until must be later than valid_from")
    return valid_from, valid_until


def _validate_unique_uuids(values: tuple[UUID, ...], field_name: str) -> tuple[UUID, ...]:
    normalized = tuple(_validate_uuid(value, field_name) for value in values)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} cannot contain duplicate UUIDs")
    return normalized


class OrganizationStatus(StrEnum):
    ACTIVE = "ACTIVE"
    RESTRICTED = "RESTRICTED"
    SUSPENDED = "SUSPENDED"
    DEACTIVATED = "DEACTIVATED"


class MembershipStatus(StrEnum):
    INVITED = "INVITED"
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    RESTRICTED = "RESTRICTED"
    SUSPENDED = "SUSPENDED"
    REVOKED = "REVOKED"
    EXPIRED = "EXPIRED"


class RoleKind(StrEnum):
    SYSTEM = "SYSTEM"
    TENANT = "TENANT"
    ORGANIZATION = "ORGANIZATION"


class PermissionSensitivity(StrEnum):
    NORMAL = "NORMAL"
    SENSITIVE = "SENSITIVE"
    CRITICAL = "CRITICAL"


class ScopeKind(StrEnum):
    TENANT = "TENANT"
    ORGANIZATION = "ORGANIZATION"
    RESOURCE = "RESOURCE"
    RESOURCE_SET = "RESOURCE_SET"


class RelationshipStatus(StrEnum):
    ACTIVE = "ACTIVE"
    REVOKED = "REVOKED"


class RelationType(StrEnum):
    OWNER = "OWNER"
    MEMBER_OF = "MEMBER_OF"
    MANAGES = "MANAGES"
    ASSIGNED_TO = "ASSIGNED_TO"
    BROKER_OF = "BROKER_OF"
    BUILDER_OF = "BUILDER_OF"
    PARTNER_OF = "PARTNER_OF"
    DELEGATED_TO = "DELEGATED_TO"


class ConstraintOperator(StrEnum):
    EQUALS = "EQUALS"
    NOT_EQUALS = "NOT_EQUALS"
    IN = "IN"
    NOT_IN = "NOT_IN"
    EXISTS = "EXISTS"
    NOT_EXISTS = "NOT_EXISTS"


class AssuranceLevel(StrEnum):
    BASIC = "BASIC"
    STANDARD = "STANDARD"
    STRONG = "STRONG"
    HIGH = "HIGH"


class EntitlementStatus(StrEnum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    REVOKED = "REVOKED"


class MembershipResolutionStatus(StrEnum):
    RESOLVED = "RESOLVED"
    NOT_FOUND = "NOT_FOUND"
    INACTIVE = "INACTIVE"
    EXPIRED = "EXPIRED"


class MembershipContextDeniedError(RuntimeError):
    """Raised when no currently valid membership can be established."""


@dataclass(frozen=True, slots=True)
class AttributeConstraint:
    """Declarative ABAC/context constraint.

    This class stores conditions; it does not evaluate or authorize them.
    """

    attribute_key: str
    operator: ConstraintOperator
    expected_values: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "attribute_key",
            _normalize_attribute_key(self.attribute_key),
        )

        if not isinstance(self.operator, ConstraintOperator):
            raise TypeError("operator must be ConstraintOperator")

        if not isinstance(self.expected_values, tuple):
            raise TypeError("expected_values must be tuple")

        values = tuple(
            _required_text(value, "expected_value", 256)
            for value in self.expected_values
        )

        if self.operator in (
            ConstraintOperator.EQUALS,
            ConstraintOperator.NOT_EQUALS,
        ) and len(values) != 1:
            raise ValueError(
                "EQUALS and NOT_EQUALS require exactly one expected value"
            )

        if self.operator in (
            ConstraintOperator.IN,
            ConstraintOperator.NOT_IN,
        ) and not values:
            raise ValueError(
                "IN and NOT_IN require at least one expected value"
            )

        if self.operator in (
            ConstraintOperator.EXISTS,
            ConstraintOperator.NOT_EXISTS,
        ) and values:
            raise ValueError(
                "EXISTS and NOT_EXISTS cannot have expected values"
            )

        if len(set(values)) != len(values):
            raise ValueError("expected_values cannot contain duplicates")

        object.__setattr__(self, "expected_values", values)

    @classmethod
    def equals(cls, attribute_key: str, value: str) -> "AttributeConstraint":
        return cls(
            attribute_key=attribute_key,
            operator=ConstraintOperator.EQUALS,
            expected_values=(value,),
        )

    @classmethod
    def in_values(
        cls,
        attribute_key: str,
        values: tuple[str, ...],
    ) -> "AttributeConstraint":
        return cls(
            attribute_key=attribute_key,
            operator=ConstraintOperator.IN,
            expected_values=values,
        )


@dataclass(frozen=True, slots=True)
class RelationshipRequirement:
    """Declarative relationship prerequisite.

    T03 models the relationship requirement; it does not resolve it.
    """

    relation_type: RelationType
    target_type: str
    target_id: UUID | None = None
    required: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.relation_type, RelationType):
            raise TypeError("relation_type must be RelationType")
        object.__setattr__(
            self,
            "target_type",
            _normalize_key(self.target_type, "target_type"),
        )
        _validate_optional_uuid(self.target_id, "target_id")
        if not isinstance(self.required, bool):
            raise TypeError("required must be bool")


@dataclass(frozen=True, slots=True)
class Organization:
    organization_id: UUID
    tenant_id: UUID
    display_name: str
    slug: str
    status: OrganizationStatus = OrganizationStatus.ACTIVE
    parent_organization_id: UUID | None = None
    revision: int = 1
    created_at: datetime = field(default_factory=_utc_now)
    updated_at: datetime = field(default_factory=_utc_now)

    def __post_init__(self) -> None:
        _validate_uuid(self.organization_id, "organization_id")
        _validate_uuid(self.tenant_id, "tenant_id")
        _validate_optional_uuid(
            self.parent_organization_id,
            "parent_organization_id",
        )

        if self.parent_organization_id == self.organization_id:
            raise ValueError("organization cannot be its own parent")

        if not isinstance(self.status, OrganizationStatus):
            raise TypeError("status must be OrganizationStatus")

        if not isinstance(self.revision, int) or self.revision < 1:
            raise ValueError("revision must be >= 1")

        created_at = _validate_aware(self.created_at, "created_at")
        updated_at = _validate_aware(self.updated_at, "updated_at")
        if updated_at < created_at:
            raise ValueError("updated_at cannot be earlier than created_at")

        object.__setattr__(
            self,
            "display_name",
            _required_text(self.display_name, "display_name", 200),
        )
        object.__setattr__(
            self,
            "slug",
            _normalize_slug(self.slug),
        )
        object.__setattr__(self, "created_at", created_at)
        object.__setattr__(self, "updated_at", updated_at)

    @classmethod
    def create(
        cls,
        *,
        tenant_id: UUID,
        display_name: str,
        slug: str,
        parent_organization_id: UUID | None = None,
    ) -> "Organization":
        now = _utc_now()
        return cls(
            organization_id=uuid4(),
            tenant_id=tenant_id,
            display_name=display_name,
            slug=slug,
            parent_organization_id=parent_organization_id,
            created_at=now,
            updated_at=now,
        )

    @property
    def is_active(self) -> bool:
        return self.status is OrganizationStatus.ACTIVE


@dataclass(frozen=True, slots=True)
class Permission:
    permission_id: UUID
    key: str
    display_name: str
    description: str
    resource: str
    action: str
    business_capability: str
    sensitivity: PermissionSensitivity = PermissionSensitivity.NORMAL
    required_assurance: AssuranceLevel = AssuranceLevel.STANDARD
    revision: int = 1

    def __post_init__(self) -> None:
        _validate_uuid(self.permission_id, "permission_id")

        object.__setattr__(self, "key", _normalize_key(self.key, "key"))
        object.__setattr__(
            self,
            "display_name",
            _required_text(self.display_name, "display_name", 160),
        )
        object.__setattr__(
            self,
            "description",
            _required_text(self.description, "description", 500),
        )
        object.__setattr__(
            self,
            "resource",
            _normalize_key(self.resource, "resource"),
        )
        object.__setattr__(
            self,
            "action",
            _normalize_key(self.action, "action"),
        )
        object.__setattr__(
            self,
            "business_capability",
            _required_text(
                self.business_capability,
                "business_capability",
                200,
            ),
        )

        if not isinstance(self.sensitivity, PermissionSensitivity):
            raise TypeError(
                "sensitivity must be PermissionSensitivity"
            )

        if not isinstance(self.required_assurance, AssuranceLevel):
            raise TypeError(
                "required_assurance must be AssuranceLevel"
            )

        if not isinstance(self.revision, int) or self.revision < 1:
            raise ValueError("revision must be >= 1")

    @classmethod
    def create(
        cls,
        *,
        key: str,
        display_name: str,
        description: str,
        resource: str,
        action: str,
        business_capability: str,
        sensitivity: PermissionSensitivity = PermissionSensitivity.NORMAL,
        required_assurance: AssuranceLevel = AssuranceLevel.STANDARD,
    ) -> "Permission":
        return cls(
            permission_id=uuid4(),
            key=key,
            display_name=display_name,
            description=description,
            resource=resource,
            action=action,
            business_capability=business_capability,
            sensitivity=sensitivity,
            required_assurance=required_assurance,
        )


@dataclass(frozen=True, slots=True)
class Scope:
    scope_id: UUID
    tenant_id: UUID
    scope_kind: ScopeKind
    organization_id: UUID | None = None
    resource_type: str | None = None
    resource_ids: tuple[UUID, ...] = ()
    constraints: tuple[AttributeConstraint, ...] = ()
    revision: int = 1

    def __post_init__(self) -> None:
        _validate_uuid(self.scope_id, "scope_id")
        _validate_uuid(self.tenant_id, "tenant_id")

        if not isinstance(self.scope_kind, ScopeKind):
            raise TypeError("scope_kind must be ScopeKind")

        _validate_optional_uuid(
            self.organization_id,
            "organization_id",
        )

        if self.resource_type is not None:
            object.__setattr__(
                self,
                "resource_type",
                _normalize_key(self.resource_type, "resource_type"),
            )

        resource_ids = _validate_unique_uuids(
            self.resource_ids,
            "resource_ids",
        )
        object.__setattr__(self, "resource_ids", resource_ids)

        if not isinstance(self.constraints, tuple):
            raise TypeError("constraints must be tuple")

        if not all(
            isinstance(constraint, AttributeConstraint)
            for constraint in self.constraints
        ):
            raise TypeError(
                "constraints must contain AttributeConstraint values"
            )

        if self.scope_kind is ScopeKind.ORGANIZATION:
            if self.organization_id is None:
                raise ValueError(
                    "ORGANIZATION scope requires organization_id"
                )

        if self.scope_kind in (
            ScopeKind.RESOURCE,
            ScopeKind.RESOURCE_SET,
        ):
            if self.resource_type is None:
                raise ValueError(
                    "resource scope requires resource_type"
                )

        if self.scope_kind is ScopeKind.RESOURCE and len(resource_ids) != 1:
            raise ValueError(
                "RESOURCE scope requires exactly one resource_id"
            )

        if self.scope_kind is ScopeKind.RESOURCE_SET and not resource_ids:
            raise ValueError(
                "RESOURCE_SET scope requires at least one resource_id"
            )

        if not isinstance(self.revision, int) or self.revision < 1:
            raise ValueError("revision must be >= 1")

        if self.scope_kind is ScopeKind.TENANT:
            if self.organization_id is not None or self.resource_ids:
                raise ValueError(
                    "TENANT scope cannot bind organization or resource IDs"
                )

    @classmethod
    def tenant(cls, tenant_id: UUID) -> "Scope":
        return cls(
            scope_id=uuid4(),
            tenant_id=tenant_id,
            scope_kind=ScopeKind.TENANT,
        )

    @classmethod
    def organization(
        cls,
        tenant_id: UUID,
        organization_id: UUID,
    ) -> "Scope":
        return cls(
            scope_id=uuid4(),
            tenant_id=tenant_id,
            scope_kind=ScopeKind.ORGANIZATION,
            organization_id=organization_id,
        )

    @classmethod
    def resource(
        cls,
        tenant_id: UUID,
        resource_type: str,
        resource_id: UUID,
    ) -> "Scope":
        return cls(
            scope_id=uuid4(),
            tenant_id=tenant_id,
            scope_kind=ScopeKind.RESOURCE,
            resource_type=resource_type,
            resource_ids=(resource_id,),
        )

    @property
    def is_tenant_wide(self) -> bool:
        return self.scope_kind is ScopeKind.TENANT


@dataclass(frozen=True, slots=True)
class Relationship:
    relationship_id: UUID
    tenant_id: UUID
    subject_identity_id: UUID
    relation_type: RelationType
    target_type: str
    target_id: UUID
    status: RelationshipStatus = RelationshipStatus.ACTIVE
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    revision: int = 1

    def __post_init__(self) -> None:
        _validate_uuid(self.relationship_id, "relationship_id")
        _validate_uuid(self.tenant_id, "tenant_id")
        _validate_uuid(self.subject_identity_id, "subject_identity_id")
        _validate_uuid(self.target_id, "target_id")

        if not isinstance(self.relation_type, RelationType):
            raise TypeError("relation_type must be RelationType")
        if not isinstance(self.status, RelationshipStatus):
            raise TypeError("status must be RelationshipStatus")

        object.__setattr__(
            self,
            "target_type",
            _normalize_key(self.target_type, "target_type"),
        )

        valid_from, valid_until = _validate_time_window(
            self.valid_from,
            self.valid_until,
        )
        object.__setattr__(self, "valid_from", valid_from)
        object.__setattr__(self, "valid_until", valid_until)

        if not isinstance(self.revision, int) or self.revision < 1:
            raise ValueError("revision must be >= 1")

    @classmethod
    def create(
        cls,
        *,
        tenant_id: UUID,
        subject_identity_id: UUID,
        relation_type: RelationType,
        target_type: str,
        target_id: UUID,
        valid_from: datetime | None = None,
        valid_until: datetime | None = None,
    ) -> "Relationship":
        return cls(
            relationship_id=uuid4(),
            tenant_id=tenant_id,
            subject_identity_id=subject_identity_id,
            relation_type=relation_type,
            target_type=target_type,
            target_id=target_id,
            valid_from=valid_from,
            valid_until=valid_until,
        )

    def is_active_at(self, at: datetime | None = None) -> bool:
        if self.status is not RelationshipStatus.ACTIVE:
            return False

        timestamp = at or _utc_now()
        timestamp = _validate_aware(timestamp, "at")

        if self.valid_from is not None and timestamp < self.valid_from:
            return False
        if self.valid_until is not None and timestamp >= self.valid_until:
            return False
        return True


@dataclass(frozen=True, slots=True)
class Entitlement:
    entitlement_id: UUID
    tenant_id: UUID | None
    key: str
    display_name: str
    description: str
    permission_ids: tuple[UUID, ...]
    scope_ids: tuple[UUID, ...] = ()
    relationship_requirements: tuple[
        RelationshipRequirement, ...
    ] = ()
    attribute_constraints: tuple[AttributeConstraint, ...] = ()
    required_assurance: AssuranceLevel = AssuranceLevel.STANDARD
    status: EntitlementStatus = EntitlementStatus.ACTIVE
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    revision: int = 1

    def __post_init__(self) -> None:
        _validate_optional_uuid(self.tenant_id, "tenant_id")
        _validate_uuid(self.entitlement_id, "entitlement_id")
        object.__setattr__(self, "key", _normalize_key(self.key, "key"))
        object.__setattr__(
            self,
            "display_name",
            _required_text(self.display_name, "display_name", 200),
        )
        object.__setattr__(
            self,
            "description",
            _required_text(self.description, "description", 500),
        )

        object.__setattr__(
            self,
            "permission_ids",
            _validate_unique_uuids(
                self.permission_ids,
                "permission_ids",
            ),
        )
        object.__setattr__(
            self,
            "scope_ids",
            _validate_unique_uuids(
                self.scope_ids,
                "scope_ids",
            ),
        )

        if not isinstance(
            self.relationship_requirements,
            tuple,
        ):
            raise TypeError(
                "relationship_requirements must be tuple"
            )

        if not all(
            isinstance(requirement, RelationshipRequirement)
            for requirement in self.relationship_requirements
        ):
            raise TypeError(
                "relationship_requirements must contain "
                "RelationshipRequirement values"
            )

        if not isinstance(
            self.attribute_constraints,
            tuple,
        ):
            raise TypeError(
                "attribute_constraints must be tuple"
            )

        if not all(
            isinstance(constraint, AttributeConstraint)
            for constraint in self.attribute_constraints
        ):
            raise TypeError(
                "attribute_constraints must contain "
                "AttributeConstraint values"
            )

        if not isinstance(
            self.required_assurance,
            AssuranceLevel,
        ):
            raise TypeError(
                "required_assurance must be AssuranceLevel"
            )

        if not isinstance(self.status, EntitlementStatus):
            raise TypeError("status must be EntitlementStatus")

        valid_from, valid_until = _validate_time_window(
            self.valid_from,
            self.valid_until,
        )
        object.__setattr__(self, "valid_from", valid_from)
        object.__setattr__(self, "valid_until", valid_until)

        if not isinstance(self.revision, int) or self.revision < 1:
            raise ValueError("revision must be >= 1")

    @classmethod
    def create(
        cls,
        *,
        key: str,
        display_name: str,
        description: str,
        permission_ids: tuple[UUID, ...],
        tenant_id: UUID | None = None,
        scope_ids: tuple[UUID, ...] = (),
        relationship_requirements: tuple[
            RelationshipRequirement, ...
        ] = (),
        attribute_constraints: tuple[AttributeConstraint, ...] = (),
        required_assurance: AssuranceLevel = AssuranceLevel.STANDARD,
        valid_from: datetime | None = None,
        valid_until: datetime | None = None,
    ) -> "Entitlement":
        return cls(
            entitlement_id=uuid4(),
            tenant_id=tenant_id,
            key=key,
            display_name=display_name,
            description=description,
            permission_ids=permission_ids,
            scope_ids=scope_ids,
            relationship_requirements=relationship_requirements,
            attribute_constraints=attribute_constraints,
            required_assurance=required_assurance,
            valid_from=valid_from,
            valid_until=valid_until,
        )

    @property
    def is_active(self) -> bool:
        return self.status is EntitlementStatus.ACTIVE


@dataclass(frozen=True, slots=True)
class Role:
    role_id: UUID
    tenant_id: UUID | None
    organization_id: UUID | None
    role_kind: RoleKind
    key: str
    display_name: str
    description: str
    permission_ids: tuple[UUID, ...]
    entitlement_ids: tuple[UUID, ...] = ()
    scope_ids: tuple[UUID, ...] = ()
    relationship_requirements: tuple[
        RelationshipRequirement, ...
    ] = ()
    attribute_constraints: tuple[AttributeConstraint, ...] = ()
    required_assurance: AssuranceLevel = AssuranceLevel.STANDARD
    revision: int = 1
    active: bool = True

    def __post_init__(self) -> None:
        _validate_uuid(self.role_id, "role_id")
        _validate_optional_uuid(self.tenant_id, "tenant_id")
        _validate_optional_uuid(
            self.organization_id,
            "organization_id",
        )

        if not isinstance(self.role_kind, RoleKind):
            raise TypeError("role_kind must be RoleKind")

        object.__setattr__(self, "key", _normalize_key(self.key, "key"))
        object.__setattr__(
            self,
            "display_name",
            _required_text(self.display_name, "display_name", 160),
        )
        object.__setattr__(
            self,
            "description",
            _required_text(self.description, "description", 500),
        )

        object.__setattr__(
            self,
            "permission_ids",
            _validate_unique_uuids(
                self.permission_ids,
                "permission_ids",
            ),
        )
        object.__setattr__(
            self,
            "entitlement_ids",
            _validate_unique_uuids(
                self.entitlement_ids,
                "entitlement_ids",
            ),
        )
        object.__setattr__(
            self,
            "scope_ids",
            _validate_unique_uuids(
                self.scope_ids,
                "scope_ids",
            ),
        )

        if not isinstance(self.relationship_requirements, tuple):
            raise TypeError(
                "relationship_requirements must be tuple"
            )
        if not all(
            isinstance(requirement, RelationshipRequirement)
            for requirement in self.relationship_requirements
        ):
            raise TypeError(
                "relationship_requirements must contain "
                "RelationshipRequirement values"
            )

        if not isinstance(self.attribute_constraints, tuple):
            raise TypeError(
                "attribute_constraints must be tuple"
            )
        if not all(
            isinstance(constraint, AttributeConstraint)
            for constraint in self.attribute_constraints
        ):
            raise TypeError(
                "attribute_constraints must contain "
                "AttributeConstraint values"
            )

        if not isinstance(
            self.required_assurance,
            AssuranceLevel,
        ):
            raise TypeError(
                "required_assurance must be AssuranceLevel"
            )

        if not isinstance(self.active, bool):
            raise TypeError("active must be bool")

        if not isinstance(self.revision, int) or self.revision < 1:
            raise ValueError("revision must be >= 1")

        if self.role_kind is RoleKind.SYSTEM:
            if self.tenant_id is not None:
                raise ValueError(
                    "SYSTEM role cannot be tenant-scoped"
                )
            if self.organization_id is not None:
                raise ValueError(
                    "SYSTEM role cannot be organization-scoped"
                )
        elif self.tenant_id is None:
            raise ValueError(
                "TENANT and ORGANIZATION roles require tenant_id"
            )

        if (
            self.role_kind is RoleKind.ORGANIZATION
            and self.organization_id is None
        ):
            raise ValueError(
                "ORGANIZATION role requires organization_id"
            )

        if (
            self.role_kind is RoleKind.TENANT
            and self.organization_id is not None
        ):
            raise ValueError(
                "TENANT role cannot carry organization_id"
            )

    @classmethod
    def create(
        cls,
        *,
        key: str,
        display_name: str,
        description: str,
        permission_ids: tuple[UUID, ...],
        role_kind: RoleKind = RoleKind.TENANT,
        tenant_id: UUID | None = None,
        organization_id: UUID | None = None,
        entitlement_ids: tuple[UUID, ...] = (),
        scope_ids: tuple[UUID, ...] = (),
        relationship_requirements: tuple[
            RelationshipRequirement, ...
        ] = (),
        attribute_constraints: tuple[AttributeConstraint, ...] = (),
        required_assurance: AssuranceLevel = AssuranceLevel.STANDARD,
    ) -> "Role":
        return cls(
            role_id=uuid4(),
            tenant_id=tenant_id,
            organization_id=organization_id,
            role_kind=role_kind,
            key=key,
            display_name=display_name,
            description=description,
            permission_ids=permission_ids,
            entitlement_ids=entitlement_ids,
            scope_ids=scope_ids,
            relationship_requirements=relationship_requirements,
            attribute_constraints=attribute_constraints,
            required_assurance=required_assurance,
        )


@dataclass(frozen=True, slots=True)
class Membership:
    membership_id: UUID
    tenant_id: UUID
    organization_id: UUID
    identity_id: UUID
    status: MembershipStatus = MembershipStatus.INVITED
    role_ids: tuple[UUID, ...] = ()
    entitlement_ids: tuple[UUID, ...] = ()
    scope_ids: tuple[UUID, ...] = ()
    relationship_ids: tuple[UUID, ...] = ()
    attribute_constraints: tuple[AttributeConstraint, ...] = ()
    required_assurance: AssuranceLevel = AssuranceLevel.STANDARD
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    invited_at: datetime | None = None
    joined_at: datetime | None = None
    revision: int = 1
    created_at: datetime = field(default_factory=_utc_now)
    updated_at: datetime = field(default_factory=_utc_now)

    def __post_init__(self) -> None:
        _validate_uuid(self.membership_id, "membership_id")
        _validate_uuid(self.tenant_id, "tenant_id")
        _validate_uuid(self.organization_id, "organization_id")
        _validate_uuid(self.identity_id, "identity_id")

        if not isinstance(self.status, MembershipStatus):
            raise TypeError("status must be MembershipStatus")

        object.__setattr__(
            self,
            "role_ids",
            _validate_unique_uuids(self.role_ids, "role_ids"),
        )
        object.__setattr__(
            self,
            "entitlement_ids",
            _validate_unique_uuids(
                self.entitlement_ids,
                "entitlement_ids",
            ),
        )
        object.__setattr__(
            self,
            "scope_ids",
            _validate_unique_uuids(
                self.scope_ids,
                "scope_ids",
            ),
        )
        object.__setattr__(
            self,
            "relationship_ids",
            _validate_unique_uuids(
                self.relationship_ids,
                "relationship_ids",
            ),
        )

        if not isinstance(self.attribute_constraints, tuple):
            raise TypeError("attribute_constraints must be tuple")
        if not all(
            isinstance(constraint, AttributeConstraint)
            for constraint in self.attribute_constraints
        ):
            raise TypeError(
                "attribute_constraints must contain "
                "AttributeConstraint values"
            )

        if not isinstance(
            self.required_assurance,
            AssuranceLevel,
        ):
            raise TypeError(
                "required_assurance must be AssuranceLevel"
            )

        valid_from, valid_until = _validate_time_window(
            self.valid_from,
            self.valid_until,
        )
        object.__setattr__(self, "valid_from", valid_from)
        object.__setattr__(self, "valid_until", valid_until)

        for timestamp, field_name in (
            (self.invited_at, "invited_at"),
            (self.joined_at, "joined_at"),
        ):
            if timestamp is not None:
                _validate_aware(timestamp, field_name)

        if self.joined_at is not None and self.invited_at is not None:
            if self.joined_at < self.invited_at:
                raise ValueError(
                    "joined_at cannot be earlier than invited_at"
                )

        if not isinstance(self.revision, int) or self.revision < 1:
            raise ValueError("revision must be >= 1")

        created_at = _validate_aware(
            self.created_at,
            "created_at",
        )
        updated_at = _validate_aware(
            self.updated_at,
            "updated_at",
        )
        if updated_at < created_at:
            raise ValueError(
                "updated_at cannot be earlier than created_at"
            )

        object.__setattr__(self, "created_at", created_at)
        object.__setattr__(self, "updated_at", updated_at)

    @classmethod
    def create(
        cls,
        *,
        tenant_id: UUID,
        organization_id: UUID,
        identity_id: UUID,
        status: MembershipStatus = MembershipStatus.INVITED,
        role_ids: tuple[UUID, ...] = (),
        entitlement_ids: tuple[UUID, ...] = (),
        scope_ids: tuple[UUID, ...] = (),
        relationship_ids: tuple[UUID, ...] = (),
        attribute_constraints: tuple[AttributeConstraint, ...] = (),
        required_assurance: AssuranceLevel = AssuranceLevel.STANDARD,
        valid_from: datetime | None = None,
        valid_until: datetime | None = None,
    ) -> "Membership":
        now = _utc_now()
        return cls(
            membership_id=uuid4(),
            tenant_id=tenant_id,
            organization_id=organization_id,
            identity_id=identity_id,
            status=status,
            role_ids=role_ids,
            entitlement_ids=entitlement_ids,
            scope_ids=scope_ids,
            relationship_ids=relationship_ids,
            attribute_constraints=attribute_constraints,
            required_assurance=required_assurance,
            valid_from=valid_from,
            valid_until=valid_until,
            invited_at=now,
            created_at=now,
            updated_at=now,
        )

    def transition_to(self, status: MembershipStatus) -> "Membership":
        if not isinstance(status, MembershipStatus):
            raise TypeError("status must be MembershipStatus")
        if status is self.status:
            return self

        allowed = {
            MembershipStatus.INVITED: {
                MembershipStatus.PENDING,
                MembershipStatus.REVOKED,
            },
            MembershipStatus.PENDING: {
                MembershipStatus.ACTIVE,
                MembershipStatus.REVOKED,
            },
            MembershipStatus.ACTIVE: {
                MembershipStatus.RESTRICTED,
                MembershipStatus.SUSPENDED,
                MembershipStatus.REVOKED,
                MembershipStatus.EXPIRED,
            },
            MembershipStatus.RESTRICTED: {
                MembershipStatus.ACTIVE,
                MembershipStatus.SUSPENDED,
                MembershipStatus.REVOKED,
                MembershipStatus.EXPIRED,
            },
            MembershipStatus.SUSPENDED: {
                MembershipStatus.ACTIVE,
                MembershipStatus.RESTRICTED,
                MembershipStatus.REVOKED,
                MembershipStatus.EXPIRED,
            },
            MembershipStatus.REVOKED: set(),
            MembershipStatus.EXPIRED: set(),
        }[self.status]

        if status not in allowed:
            raise ValueError(
                "invalid membership lifecycle transition: "
                f"{self.status.value} -> {status.value}"
            )

        joined_at = self.joined_at
        if status is MembershipStatus.ACTIVE and joined_at is None:
            joined_at = _utc_now()

        return replace(
            self,
            status=status,
            joined_at=joined_at,
            revision=self.revision + 1,
            updated_at=_utc_now(),
        )

    def add_role(self, role_id: UUID) -> "Membership":
        _validate_uuid(role_id, "role_id")
        if role_id in self.role_ids:
            return self
        return replace(
            self,
            role_ids=self.role_ids + (role_id,),
            revision=self.revision + 1,
            updated_at=_utc_now(),
        )

    def remove_role(self, role_id: UUID) -> "Membership":
        _validate_uuid(role_id, "role_id")
        if role_id not in self.role_ids:
            return self
        return replace(
            self,
            role_ids=tuple(
                value
                for value in self.role_ids
                if value != role_id
            ),
            revision=self.revision + 1,
            updated_at=_utc_now(),
        )

    def add_entitlement(self, entitlement_id: UUID) -> "Membership":
        _validate_uuid(entitlement_id, "entitlement_id")
        if entitlement_id in self.entitlement_ids:
            return self
        return replace(
            self,
            entitlement_ids=self.entitlement_ids + (entitlement_id,),
            revision=self.revision + 1,
            updated_at=_utc_now(),
        )

    def add_scope(self, scope_id: UUID) -> "Membership":
        _validate_uuid(scope_id, "scope_id")
        if scope_id in self.scope_ids:
            return self
        return replace(
            self,
            scope_ids=self.scope_ids + (scope_id,),
            revision=self.revision + 1,
            updated_at=_utc_now(),
        )

    def bind_relationship(self, relationship_id: UUID) -> "Membership":
        _validate_uuid(relationship_id, "relationship_id")
        if relationship_id in self.relationship_ids:
            return self
        return replace(
            self,
            relationship_ids=self.relationship_ids + (relationship_id,),
            revision=self.revision + 1,
            updated_at=_utc_now(),
        )

    def with_constraints(
        self,
        constraints: tuple[AttributeConstraint, ...],
    ) -> "Membership":
        if not isinstance(constraints, tuple):
            raise TypeError("constraints must be tuple")
        if not all(
            isinstance(constraint, AttributeConstraint)
            for constraint in constraints
        ):
            raise TypeError(
                "constraints must contain AttributeConstraint values"
            )
        return replace(
            self,
            attribute_constraints=constraints,
            revision=self.revision + 1,
            updated_at=_utc_now(),
        )

    def is_valid_at(self, at: datetime | None = None) -> bool:
        if self.status not in {
            MembershipStatus.ACTIVE,
            MembershipStatus.RESTRICTED,
        }:
            return False

        timestamp = at or _utc_now()
        timestamp = _validate_aware(timestamp, "at")

        if self.valid_from is not None and timestamp < self.valid_from:
            return False
        if self.valid_until is not None and timestamp >= self.valid_until:
            return False
        return True

    @property
    def is_active(self) -> bool:
        return self.status is MembershipStatus.ACTIVE


@dataclass(frozen=True, slots=True)
class MembershipResolutionResult:
    status: MembershipResolutionStatus
    membership_id: UUID | None = None
    tenant_id: UUID | None = None
    organization_id: UUID | None = None
    identity_id: UUID | None = None
    membership_revision: int | None = None
    membership: Membership | None = None
    reason: str = ""

    def __post_init__(self) -> None:
        _validate_optional_uuid(self.membership_id, "membership_id")
        _validate_optional_uuid(self.tenant_id, "tenant_id")
        _validate_optional_uuid(
            self.organization_id,
            "organization_id",
        )
        _validate_optional_uuid(
            self.identity_id,
            "identity_id",
        )

        if not isinstance(
            self.status,
            MembershipResolutionStatus,
        ):
            raise TypeError(
                "status must be MembershipResolutionStatus"
            )

        if self.membership_revision is not None:
            if (
                not isinstance(self.membership_revision, int)
                or self.membership_revision < 1
            ):
                raise ValueError(
                    "membership_revision must be >= 1"
                )

        if self.membership is not None and not isinstance(
            self.membership,
            Membership,
        ):
            raise TypeError(
                "membership must be Membership or None"
            )

        if not isinstance(self.reason, str):
            raise TypeError("reason must be string")

        if self.status is MembershipResolutionStatus.RESOLVED:
            if self.membership is None:
                raise ValueError(
                    "RESOLVED result requires membership"
                )
        elif self.membership is not None:
            raise ValueError(
                "non-resolved result cannot carry membership"
            )

    @property
    def resolved(self) -> bool:
        return self.status is MembershipResolutionStatus.RESOLVED


class MembershipDirectory:
    """Deterministic T03 directory for organization and membership references.

    This directory validates structural references only.
    It does not evaluate authorization and does not own authentication,
    session, tenant isolation, audit, event persistence, or policy engines.
    """

    def __init__(self) -> None:
        self._organizations: dict[UUID, Organization] = {}
        self._organization_slugs: dict[tuple[UUID, str], UUID] = {}
        self._permissions: dict[UUID, Permission] = {}
        self._permission_keys: dict[str, UUID] = {}
        self._entitlements: dict[UUID, Entitlement] = {}
        self._entitlement_keys: dict[tuple[UUID | None, str], UUID] = {}
        self._roles: dict[UUID, Role] = {}
        self._role_keys: dict[tuple[UUID | None, str], UUID] = {}
        self._scopes: dict[UUID, Scope] = {}
        self._relationships: dict[UUID, Relationship] = {}
        self._memberships: dict[UUID, Membership] = {}

    def register_organization(self, organization: Organization) -> None:
        if not isinstance(organization, Organization):
            raise TypeError("organization must be Organization")

        existing = self._organizations.get(organization.organization_id)
        key = (organization.tenant_id, organization.slug)
        existing_slug_owner = self._organization_slugs.get(key)

        if (
            existing_slug_owner is not None
            and existing_slug_owner != organization.organization_id
        ):
            raise ValueError(
                "organization slug is already assigned in tenant"
            )

        if (
            organization.parent_organization_id is not None
            and organization.parent_organization_id not in self._organizations
        ):
            raise ValueError(
                "parent organization must be registered first"
            )

        if existing is None:
            self._organizations[organization.organization_id] = organization
            self._organization_slugs[key] = organization.organization_id
            return

        if existing.tenant_id != organization.tenant_id:
            raise ValueError("organization tenant cannot change")
        if existing.slug != organization.slug:
            raise ValueError("organization slug is immutable")
        if organization.revision < existing.revision:
            raise ValueError("organization revision cannot move backwards")
        if organization.revision == existing.revision and organization != existing:
            raise ValueError(
                "same organization revision cannot represent different state"
            )

        self._organizations[organization.organization_id] = organization
        self._organization_slugs[key] = organization.organization_id

    def register_permission(self, permission: Permission) -> None:
        if not isinstance(permission, Permission):
            raise TypeError("permission must be Permission")

        existing = self._permissions.get(permission.permission_id)
        existing_key_owner = self._permission_keys.get(permission.key)

        if (
            existing_key_owner is not None
            and existing_key_owner != permission.permission_id
        ):
            raise ValueError("permission key is already assigned")

        if existing is not None:
            if permission.key != existing.key:
                raise ValueError("permission key is immutable")
            if permission.revision < existing.revision:
                raise ValueError("permission revision cannot move backwards")
            if (
                permission.revision == existing.revision
                and permission != existing
            ):
                raise ValueError(
                    "same permission revision cannot represent different state"
                )

        self._permissions[permission.permission_id] = permission
        self._permission_keys[permission.key] = permission.permission_id

    def register_scope(self, scope: Scope) -> None:
        if not isinstance(scope, Scope):
            raise TypeError("scope must be Scope")
        existing = self._scopes.get(scope.scope_id)
        if existing is not None and existing != scope:
            raise ValueError("scope_id is immutable")
        self._scopes[scope.scope_id] = scope

    def register_relationship(self, relationship: Relationship) -> None:
        if not isinstance(relationship, Relationship):
            raise TypeError("relationship must be Relationship")
        existing = self._relationships.get(relationship.relationship_id)
        if existing is not None:
            if relationship.tenant_id != existing.tenant_id:
                raise ValueError("relationship tenant cannot change")
            if relationship.revision < existing.revision:
                raise ValueError(
                    "relationship revision cannot move backwards"
                )
            if (
                relationship.revision == existing.revision
                and relationship != existing
            ):
                raise ValueError(
                    "same relationship revision cannot represent different state"
                )
        self._relationships[relationship.relationship_id] = relationship

    def register_entitlement(self, entitlement: Entitlement) -> None:
        if not isinstance(entitlement, Entitlement):
            raise TypeError("entitlement must be Entitlement")

        self._validate_permission_references(entitlement.permission_ids)
        self._validate_scope_references(
            entitlement.scope_ids,
            entitlement.tenant_id,
        )

        key = (entitlement.tenant_id, entitlement.key)
        existing_key_owner = self._entitlement_keys.get(key)
        if (
            existing_key_owner is not None
            and existing_key_owner != entitlement.entitlement_id
        ):
            raise ValueError(
                "entitlement key is already assigned in scope"
            )

        existing = self._entitlements.get(entitlement.entitlement_id)
        if existing is not None:
            if existing.tenant_id != entitlement.tenant_id:
                raise ValueError("entitlement tenant cannot change")
            if existing.key != entitlement.key:
                raise ValueError("entitlement key is immutable")
            if entitlement.revision < existing.revision:
                raise ValueError(
                    "entitlement revision cannot move backwards"
                )
            if (
                entitlement.revision == existing.revision
                and entitlement != existing
            ):
                raise ValueError(
                    "same entitlement revision cannot represent different state"
                )

        self._entitlements[entitlement.entitlement_id] = entitlement
        self._entitlement_keys[key] = entitlement.entitlement_id

    def register_role(self, role: Role) -> None:
        if not isinstance(role, Role):
            raise TypeError("role must be Role")

        if role.organization_id is not None:
            organization = self._organizations.get(role.organization_id)
            if organization is None:
                raise ValueError("role organization must be registered")
            if organization.tenant_id != role.tenant_id:
                raise ValueError(
                    "role organization belongs to another tenant"
                )

        self._validate_permission_references(role.permission_ids)
        self._validate_entitlement_references(
            role.entitlement_ids,
            role.tenant_id,
        )
        self._validate_scope_references(
            role.scope_ids,
            role.tenant_id,
        )

        key = (role.tenant_id, role.key)
        existing_key_owner = self._role_keys.get(key)
        if (
            existing_key_owner is not None
            and existing_key_owner != role.role_id
        ):
            raise ValueError(
                "role key is already assigned in scope"
            )

        existing = self._roles.get(role.role_id)
        if existing is not None:
            if existing.tenant_id != role.tenant_id:
                raise ValueError("role tenant cannot change")
            if existing.key != role.key:
                raise ValueError("role key is immutable")
            if role.revision < existing.revision:
                raise ValueError("role revision cannot move backwards")
            if (
                role.revision == existing.revision
                and role != existing
            ):
                raise ValueError(
                    "same role revision cannot represent different state"
                )

        self._roles[role.role_id] = role
        self._role_keys[key] = role.role_id

    def register_membership(self, membership: Membership) -> None:
        if not isinstance(membership, Membership):
            raise TypeError("membership must be Membership")

        organization = self._organizations.get(membership.organization_id)
        if organization is None:
            raise ValueError("membership organization must be registered")

        if organization.tenant_id != membership.tenant_id:
            raise ValueError(
                "membership cannot reference organization from another tenant"
            )

        self._validate_role_references(
            membership.role_ids,
            membership.tenant_id,
            membership.organization_id,
        )
        self._validate_entitlement_references(
            membership.entitlement_ids,
            membership.tenant_id,
        )
        self._validate_scope_references(
            membership.scope_ids,
            membership.tenant_id,
        )
        self._validate_relationship_references(
            membership.relationship_ids,
            membership.tenant_id,
        )

        existing = self._memberships.get(membership.membership_id)
        if existing is not None:
            if existing.tenant_id != membership.tenant_id:
                raise ValueError("membership tenant cannot change")
            if existing.identity_id != membership.identity_id:
                raise ValueError("membership identity cannot change")
            if (
                membership.revision < existing.revision
            ):
                raise ValueError(
                    "membership revision cannot move backwards"
                )
            if (
                membership.revision == existing.revision
                and membership != existing
            ):
                raise ValueError(
                    "same membership revision cannot represent different state"
                )

        self._memberships[membership.membership_id] = membership

    def resolve_membership(
        self,
        *,
        tenant_id: UUID,
        organization_id: UUID,
        identity_id: UUID,
        at: datetime | None = None,
    ) -> MembershipResolutionResult:
        _validate_uuid(tenant_id, "tenant_id")
        _validate_uuid(organization_id, "organization_id")
        _validate_uuid(identity_id, "identity_id")

        candidates = tuple(
            membership
            for membership in self._memberships.values()
            if (
                membership.tenant_id == tenant_id
                and membership.organization_id == organization_id
                and membership.identity_id == identity_id
            )
        )

        if not candidates:
            return MembershipResolutionResult(
                status=MembershipResolutionStatus.NOT_FOUND,
                tenant_id=tenant_id,
                organization_id=organization_id,
                identity_id=identity_id,
                reason="membership not found",
            )

        current = max(candidates, key=lambda item: item.revision)

        timestamp = at or _utc_now()
        if not isinstance(timestamp, datetime):
            raise TypeError("at must be datetime or None")
        timestamp = _validate_aware(timestamp, "at")

        if current.status in {
            MembershipStatus.REVOKED,
            MembershipStatus.EXPIRED,
        }:
            status = (
                MembershipResolutionStatus.EXPIRED
                if current.status is MembershipStatus.EXPIRED
                else MembershipResolutionStatus.INACTIVE
            )
            return MembershipResolutionResult(
                status=status,
                membership_id=current.membership_id,
                tenant_id=tenant_id,
                organization_id=organization_id,
                identity_id=identity_id,
                membership_revision=current.revision,
                reason="membership is not active",
            )

        if not current.is_valid_at(timestamp):
            return MembershipResolutionResult(
                status=MembershipResolutionStatus.INACTIVE,
                membership_id=current.membership_id,
                tenant_id=tenant_id,
                organization_id=organization_id,
                identity_id=identity_id,
                membership_revision=current.revision,
                reason="membership is outside its validity window",
            )

        return MembershipResolutionResult(
            status=MembershipResolutionStatus.RESOLVED,
            membership_id=current.membership_id,
            tenant_id=tenant_id,
            organization_id=organization_id,
            identity_id=identity_id,
            membership_revision=current.revision,
            membership=current,
            reason="membership resolved",
        )

    def require_membership(
        self,
        *,
        tenant_id: UUID,
        organization_id: UUID,
        identity_id: UUID,
        at: datetime | None = None,
    ) -> Membership:
        result = self.resolve_membership(
            tenant_id=tenant_id,
            organization_id=organization_id,
            identity_id=identity_id,
            at=at,
        )
        if not result.resolved:
            raise MembershipContextDeniedError(
                "NO_VALID_MEMBERSHIP: "
                f"{result.reason}"
            )
        assert result.membership is not None
        return result.membership

    def get_organization(self, organization_id: UUID) -> Organization | None:
        _validate_uuid(organization_id, "organization_id")
        return self._organizations.get(organization_id)

    def get_permission(self, permission_id: UUID) -> Permission | None:
        _validate_uuid(permission_id, "permission_id")
        return self._permissions.get(permission_id)

    def get_role(self, role_id: UUID) -> Role | None:
        _validate_uuid(role_id, "role_id")
        return self._roles.get(role_id)

    def get_entitlement(self, entitlement_id: UUID) -> Entitlement | None:
        _validate_uuid(entitlement_id, "entitlement_id")
        return self._entitlements.get(entitlement_id)

    def get_scope(self, scope_id: UUID) -> Scope | None:
        _validate_uuid(scope_id, "scope_id")
        return self._scopes.get(scope_id)

    def get_relationship(self, relationship_id: UUID) -> Relationship | None:
        _validate_uuid(relationship_id, "relationship_id")
        return self._relationships.get(relationship_id)

    def get_membership(self, membership_id: UUID) -> Membership | None:
        _validate_uuid(membership_id, "membership_id")
        return self._memberships.get(membership_id)

    def _validate_permission_references(
        self,
        permission_ids: tuple[UUID, ...],
    ) -> None:
        for permission_id in permission_ids:
            if permission_id not in self._permissions:
                raise ValueError(
                    f"unknown permission reference: {permission_id}"
                )

    def _validate_scope_references(
        self,
        scope_ids: tuple[UUID, ...],
        tenant_id: UUID | None,
    ) -> None:
        for scope_id in scope_ids:
            scope = self._scopes.get(scope_id)
            if scope is None:
                raise ValueError(
                    f"unknown scope reference: {scope_id}"
                )
            if tenant_id is None:
                continue
            if scope.tenant_id != tenant_id:
                raise ValueError(
                    "scope reference belongs to another tenant"
                )

    def _validate_entitlement_references(
        self,
        entitlement_ids: tuple[UUID, ...],
        tenant_id: UUID | None,
    ) -> None:
        for entitlement_id in entitlement_ids:
            entitlement = self._entitlements.get(entitlement_id)
            if entitlement is None:
                raise ValueError(
                    f"unknown entitlement reference: {entitlement_id}"
                )
            if (
                tenant_id is not None
                and entitlement.tenant_id is not None
                and entitlement.tenant_id != tenant_id
            ):
                raise ValueError(
                    "entitlement reference belongs to another tenant"
                )

    def _validate_role_references(
        self,
        role_ids: tuple[UUID, ...],
        tenant_id: UUID,
        organization_id: UUID,
    ) -> None:
        for role_id in role_ids:
            role = self._roles.get(role_id)
            if role is None:
                raise ValueError(
                    f"unknown role reference: {role_id}"
                )

            if role.tenant_id is not None and role.tenant_id != tenant_id:
                raise ValueError(
                    "role reference belongs to another tenant"
                )

            if (
                role.role_kind is RoleKind.ORGANIZATION
                and role.organization_id != organization_id
            ):
                raise ValueError(
                    "organization role does not match membership organization"
                )

    def _validate_relationship_references(
        self,
        relationship_ids: tuple[UUID, ...],
        tenant_id: UUID,
    ) -> None:
        for relationship_id in relationship_ids:
            relationship = self._relationships.get(relationship_id)
            if relationship is None:
                raise ValueError(
                    f"unknown relationship reference: {relationship_id}"
                )
            if relationship.tenant_id != tenant_id:
                raise ValueError(
                    "relationship reference belongs to another tenant"
                )
