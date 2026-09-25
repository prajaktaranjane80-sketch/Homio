from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from enum import StrEnum
from re import fullmatch
from uuid import UUID, uuid4


_TENANT_SLUG_PATTERN = r"^[a-z0-9][a-z0-9._-]{1,62}[a-z0-9]$"
_REFERENCE_KEY_PATTERN = r"^[a-z0-9][a-z0-9._-]{0,127}$"
_REGION_PATTERN = r"^[A-Za-z0-9][A-Za-z0-9._-]{0,31}$"
_JURISDICTION_PATTERN = r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _required_text(
    value: str,
    field_name: str,
    max_length: int,
) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")

    value = value.strip()

    if not value:
        raise ValueError(f"{field_name} cannot be empty")

    if len(value) > max_length:
        raise ValueError(
            f"{field_name} exceeds {max_length} characters"
        )

    return value


def _normalize_slug(slug: str) -> str:
    value = _required_text(slug, "slug", 64).lower()

    if not fullmatch(_TENANT_SLUG_PATTERN, value):
        raise ValueError(
            "slug must be 3-64 characters, lowercase, and contain "
            "only letters, digits, '.', '_' or '-'"
        )

    return value


def _normalize_reference_key(
    value: str,
    field_name: str,
) -> str:
    candidate = _required_text(
        value,
        field_name,
        128,
    ).lower()

    if not fullmatch(_REFERENCE_KEY_PATTERN, candidate):
        raise ValueError(
            f"{field_name} must contain only letters, digits, "
            "dot, underscore or hyphen"
        )

    return candidate


def _validate_uuid(
    value: UUID,
    field_name: str,
) -> UUID:
    if not isinstance(value, UUID):
        raise TypeError(f"{field_name} must be a UUID")

    return value


def _validate_optional_uuid(
    value: UUID | None,
    field_name: str,
) -> UUID | None:
    if value is None:
        return None

    return _validate_uuid(value, field_name)


def _validate_aware(
    value: datetime,
    field_name: str,
) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError(f"{field_name} must be datetime")

    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(
            f"{field_name} must be timezone-aware"
        )

    return value


def _normalize_region(
    value: str | None,
) -> str | None:
    if value is None:
        return None

    candidate = _required_text(
        value,
        "region",
        32,
    )

    if not fullmatch(_REGION_PATTERN, candidate):
        raise ValueError(
            "region must contain only letters, digits, "
            "dot, underscore or hyphen"
        )

    return candidate


def _normalize_jurisdiction(
    value: str | None,
) -> str | None:
    if value is None:
        return None

    candidate = _required_text(
        value,
        "jurisdiction",
        64,
    )

    if not fullmatch(_JURISDICTION_PATTERN, candidate):
        raise ValueError(
            "jurisdiction must contain only letters, digits, "
            "dot, underscore or hyphen"
        )

    return candidate


class TenantKind(StrEnum):
    BROKERAGE = "BROKERAGE"
    BUILDER = "BUILDER"
    ENTERPRISE = "ENTERPRISE"
    PARTNER = "PARTNER"
    PLATFORM = "PLATFORM"


class OperatingMode(StrEnum):
    OWNED_INTERNATIONAL_BROKERAGE = (
        "OWNED_INTERNATIONAL_BROKERAGE"
    )
    BROKER_SAAS = "BROKER_SAAS"
    BUILDER_SAAS = "BUILDER_SAAS"
    ENTERPRISE_WHITE_LABEL = "ENTERPRISE_WHITE_LABEL"
    PLATFORM_API_PARTNER = "PLATFORM_API_PARTNER"


class TenantStatus(StrEnum):
    PROVISIONING = "PROVISIONING"
    PENDING_ACTIVATION = "PENDING_ACTIVATION"
    ACTIVE = "ACTIVE"
    RESTRICTED = "RESTRICTED"
    SUSPENDED = "SUSPENDED"
    DEACTIVATING = "DEACTIVATING"
    DEACTIVATED = "DEACTIVATED"
    ARCHIVED = "ARCHIVED"


class IsolationProfile(StrEnum):
    SHARED_LOGICAL = "SHARED_LOGICAL"
    TENANT_DEDICATED = "TENANT_DEDICATED"


class DataResidencyMode(StrEnum):
    GLOBAL_ALLOWED = "GLOBAL_ALLOWED"
    REGION_BOUND = "REGION_BOUND"
    COUNTRY_BOUND = "COUNTRY_BOUND"
    CUSTOM_POLICY = "CUSTOM_POLICY"


class ProvisioningIntentStatus(StrEnum):
    REQUESTED = "REQUESTED"
    ACCEPTED = "ACCEPTED"
    APPLIED = "APPLIED"
    REJECTED = "REJECTED"


class TenantResolutionStatus(StrEnum):
    RESOLVED = "RESOLVED"
    NOT_FOUND = "NOT_FOUND"
    INACTIVE = "INACTIVE"
    ARCHIVED = "ARCHIVED"


class TenantContextDeniedError(RuntimeError):
    """Raised when a usable tenant context cannot be established."""


@dataclass(frozen=True, slots=True)
class TenantConfigurationReference:
    """Immutable reference to tenant-owned configuration.

    T02 owns the reference, not the configuration store itself.
    """

    reference_id: UUID
    configuration_key: str
    version: int = 1

    def __post_init__(self) -> None:
        _validate_uuid(
            self.reference_id,
            "reference_id",
        )

        normalized = _normalize_reference_key(
            self.configuration_key,
            "configuration_key",
        )

        if not isinstance(self.version, int):
            raise TypeError("version must be int")

        if self.version < 1:
            raise ValueError("version must be >= 1")

        object.__setattr__(
            self,
            "configuration_key",
            normalized,
        )

    @classmethod
    def create(
        cls,
        configuration_key: str,
        version: int = 1,
    ) -> "TenantConfigurationReference":
        return cls(
            reference_id=uuid4(),
            configuration_key=configuration_key,
            version=version,
        )


@dataclass(frozen=True, slots=True)
class TenantSecurityProfileReference:
    """Immutable reference to tenant security policy.

    The policy implementation remains outside T02.
    """

    reference_id: UUID
    profile_key: str
    version: int = 1
    fail_closed: bool = True
    require_valid_tenant_context: bool = True

    def __post_init__(self) -> None:
        _validate_uuid(
            self.reference_id,
            "reference_id",
        )

        normalized = _normalize_reference_key(
            self.profile_key,
            "profile_key",
        )

        if not isinstance(self.version, int):
            raise TypeError("version must be int")

        if self.version < 1:
            raise ValueError("version must be >= 1")

        if not isinstance(self.fail_closed, bool):
            raise TypeError("fail_closed must be bool")

        if not isinstance(
            self.require_valid_tenant_context,
            bool,
        ):
            raise TypeError(
                "require_valid_tenant_context must be bool"
            )

        if not self.fail_closed:
            raise ValueError(
                "tenant security profile must be fail-closed"
            )

        if not self.require_valid_tenant_context:
            raise ValueError(
                "tenant security profile must require valid "
                "tenant context"
            )

        object.__setattr__(
            self,
            "profile_key",
            normalized,
        )

    @classmethod
    def create(
        cls,
        profile_key: str,
        version: int = 1,
    ) -> "TenantSecurityProfileReference":
        return cls(
            reference_id=uuid4(),
            profile_key=profile_key,
            version=version,
        )


@dataclass(frozen=True, slots=True)
class TenantRegionJurisdictionReference:
    """Immutable geographical and jurisdiction reference."""

    reference_id: UUID
    region: str | None = None
    jurisdiction: str | None = None

    def __post_init__(self) -> None:
        _validate_uuid(
            self.reference_id,
            "reference_id",
        )

        normalized_region = _normalize_region(
            self.region
        )
        normalized_jurisdiction = _normalize_jurisdiction(
            self.jurisdiction
        )

        if (
            normalized_region is None
            and normalized_jurisdiction is None
        ):
            raise ValueError(
                "region or jurisdiction is required"
            )

        object.__setattr__(
            self,
            "region",
            normalized_region,
        )

        object.__setattr__(
            self,
            "jurisdiction",
            normalized_jurisdiction,
        )

    @classmethod
    def create(
        cls,
        *,
        region: str | None = None,
        jurisdiction: str | None = None,
    ) -> "TenantRegionJurisdictionReference":
        return cls(
            reference_id=uuid4(),
            region=region,
            jurisdiction=jurisdiction,
        )


_ALLOWED_TRANSITIONS: dict[
    TenantStatus,
    frozenset[TenantStatus],
] = {
    TenantStatus.PROVISIONING: frozenset(
        {
            TenantStatus.PENDING_ACTIVATION,
            TenantStatus.RESTRICTED,
            TenantStatus.DEACTIVATING,
        }
    ),
    TenantStatus.PENDING_ACTIVATION: frozenset(
        {
            TenantStatus.ACTIVE,
            TenantStatus.RESTRICTED,
            TenantStatus.SUSPENDED,
            TenantStatus.DEACTIVATING,
        }
    ),
    TenantStatus.ACTIVE: frozenset(
        {
            TenantStatus.RESTRICTED,
            TenantStatus.SUSPENDED,
            TenantStatus.DEACTIVATING,
        }
    ),
    TenantStatus.RESTRICTED: frozenset(
        {
            TenantStatus.ACTIVE,
            TenantStatus.SUSPENDED,
            TenantStatus.DEACTIVATING,
        }
    ),
    TenantStatus.SUSPENDED: frozenset(
        {
            TenantStatus.ACTIVE,
            TenantStatus.RESTRICTED,
            TenantStatus.DEACTIVATING,
        }
    ),
    TenantStatus.DEACTIVATING: frozenset(
        {
            TenantStatus.DEACTIVATED,
        }
    ),
    TenantStatus.DEACTIVATED: frozenset(
        {
            TenantStatus.ARCHIVED,
        }
    ),
    TenantStatus.ARCHIVED: frozenset(),
}


@dataclass(frozen=True, slots=True)
class Tenant:
    """Canonical T02 tenant record.

    T02 owns:
    - tenant identity and lifecycle
    - operating-mode binding
    - configuration/security/profile references
    - regional/jurisdictional reference
    - deterministic tenant metadata
    - immutable tenant ID / slug boundary

    T02 does not own:
    - memberships
    - roles or permissions
    - authorization decisions
    - cross-tenant enforcement
    - credentials
    - sessions
    - audit storage
    - event persistence
    """

    tenant_id: UUID
    tenant_kind: TenantKind
    operating_mode: OperatingMode
    display_name: str
    slug: str
    status: TenantStatus = TenantStatus.PROVISIONING
    isolation_profile: IsolationProfile = (
        IsolationProfile.SHARED_LOGICAL
    )
    residency_mode: DataResidencyMode = (
        DataResidencyMode.GLOBAL_ALLOWED
    )
    residency_region: str | None = None
    jurisdiction: str | None = None
    quota_profile: str = "default"
    owner_identity_id: UUID | None = None
    primary_admin_identity_id: UUID | None = None
    configuration_ref: TenantConfigurationReference = field(
        default_factory=lambda: TenantConfigurationReference.create(
            "default"
        )
    )
    security_profile_ref: TenantSecurityProfileReference = field(
        default_factory=lambda: (
            TenantSecurityProfileReference.create(
                "default"
            )
        )
    )
    region_jurisdiction_ref: (
        TenantRegionJurisdictionReference | None
    ) = None
    revision: int = 1
    created_at: datetime = field(
        default_factory=_utc_now
    )
    updated_at: datetime = field(
        default_factory=_utc_now
    )

    def __post_init__(self) -> None:
        _validate_uuid(self.tenant_id, "tenant_id")

        if not isinstance(
            self.tenant_kind,
            TenantKind,
        ):
            raise TypeError(
                "tenant_kind must be TenantKind"
            )

        if not isinstance(
            self.operating_mode,
            OperatingMode,
        ):
            raise TypeError(
                "operating_mode must be OperatingMode"
            )

        if not isinstance(
            self.status,
            TenantStatus,
        ):
            raise TypeError(
                "status must be TenantStatus"
            )

        if not isinstance(
            self.isolation_profile,
            IsolationProfile,
        ):
            raise TypeError(
                "isolation_profile must be IsolationProfile"
            )

        if not isinstance(
            self.residency_mode,
            DataResidencyMode,
        ):
            raise TypeError(
                "residency_mode must be DataResidencyMode"
            )

        _validate_optional_uuid(
            self.owner_identity_id,
            "owner_identity_id",
        )

        _validate_optional_uuid(
            self.primary_admin_identity_id,
            "primary_admin_identity_id",
        )

        if not isinstance(
            self.configuration_ref,
            TenantConfigurationReference,
        ):
            raise TypeError(
                "configuration_ref must be "
                "TenantConfigurationReference"
            )

        if not isinstance(
            self.security_profile_ref,
            TenantSecurityProfileReference,
        ):
            raise TypeError(
                "security_profile_ref must be "
                "TenantSecurityProfileReference"
            )

        if self.region_jurisdiction_ref is not None and not isinstance(
            self.region_jurisdiction_ref,
            TenantRegionJurisdictionReference,
        ):
            raise TypeError(
                "region_jurisdiction_ref must be "
                "TenantRegionJurisdictionReference or None"
            )

        if not isinstance(self.revision, int):
            raise TypeError("revision must be int")

        if self.revision < 1:
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

        object.__setattr__(
            self,
            "created_at",
            created_at,
        )
        object.__setattr__(
            self,
            "updated_at",
            updated_at,
        )

        object.__setattr__(
            self,
            "display_name",
            _required_text(
                self.display_name,
                "display_name",
                200,
            ),
        )

        object.__setattr__(
            self,
            "slug",
            _normalize_slug(self.slug),
        )

        object.__setattr__(
            self,
            "quota_profile",
            _required_text(
                self.quota_profile,
                "quota_profile",
                128,
            ),
        )

        normalized_region = _normalize_region(
            self.residency_region
        )
        normalized_jurisdiction = _normalize_jurisdiction(
            self.jurisdiction
        )

        object.__setattr__(
            self,
            "residency_region",
            normalized_region,
        )
        object.__setattr__(
            self,
            "jurisdiction",
            normalized_jurisdiction,
        )

        if self.residency_mode in (
            DataResidencyMode.REGION_BOUND,
            DataResidencyMode.COUNTRY_BOUND,
            DataResidencyMode.CUSTOM_POLICY,
        ):
            if (
                normalized_region is None
                and normalized_jurisdiction is None
                and self.region_jurisdiction_ref is None
            ):
                raise ValueError(
                    "restricted residency mode requires "
                    "region or jurisdiction"
                )

        if self.region_jurisdiction_ref is None:
            if (
                normalized_region is not None
                or normalized_jurisdiction is not None
            ):
                object.__setattr__(
                    self,
                    "region_jurisdiction_ref",
                    TenantRegionJurisdictionReference.create(
                        region=normalized_region,
                        jurisdiction=normalized_jurisdiction,
                    ),
                )

    @classmethod
    def create(
        cls,
        *,
        tenant_kind: TenantKind,
        operating_mode: OperatingMode,
        display_name: str,
        slug: str,
        isolation_profile: IsolationProfile = (
            IsolationProfile.SHARED_LOGICAL
        ),
        residency_mode: DataResidencyMode = (
            DataResidencyMode.GLOBAL_ALLOWED
        ),
        residency_region: str | None = None,
        jurisdiction: str | None = None,
        quota_profile: str = "default",
        owner_identity_id: UUID | None = None,
        primary_admin_identity_id: UUID | None = None,
        configuration_ref: (
            TenantConfigurationReference | None
        ) = None,
        security_profile_ref: (
            TenantSecurityProfileReference | None
        ) = None,
        region_jurisdiction_ref: (
            TenantRegionJurisdictionReference | None
        ) = None,
    ) -> "Tenant":
        now = _utc_now()

        return cls(
            tenant_id=uuid4(),
            tenant_kind=tenant_kind,
            operating_mode=operating_mode,
            display_name=display_name,
            slug=slug,
            isolation_profile=isolation_profile,
            residency_mode=residency_mode,
            residency_region=residency_region,
            jurisdiction=jurisdiction,
            quota_profile=quota_profile,
            owner_identity_id=owner_identity_id,
            primary_admin_identity_id=primary_admin_identity_id,
            configuration_ref=(
                configuration_ref
                or TenantConfigurationReference.create(
                    "default"
                )
            ),
            security_profile_ref=(
                security_profile_ref
                or TenantSecurityProfileReference.create(
                    "default"
                )
            ),
            region_jurisdiction_ref=region_jurisdiction_ref,
            created_at=now,
            updated_at=now,
        )

    def assign_administrators(
        self,
        *,
        owner_identity_id: UUID,
        primary_admin_identity_id: UUID,
    ) -> "Tenant":
        return replace(
            self,
            owner_identity_id=_validate_uuid(
                owner_identity_id,
                "owner_identity_id",
            ),
            primary_admin_identity_id=_validate_uuid(
                primary_admin_identity_id,
                "primary_admin_identity_id",
            ),
            revision=self.revision + 1,
            updated_at=_utc_now(),
        )

    def with_configuration_reference(
        self,
        configuration_ref: TenantConfigurationReference,
    ) -> "Tenant":
        if not isinstance(
            configuration_ref,
            TenantConfigurationReference,
        ):
            raise TypeError(
                "configuration_ref must be "
                "TenantConfigurationReference"
            )

        if configuration_ref == self.configuration_ref:
            return self

        return replace(
            self,
            configuration_ref=configuration_ref,
            revision=self.revision + 1,
            updated_at=_utc_now(),
        )

    def with_security_profile(
        self,
        security_profile_ref: TenantSecurityProfileReference,
    ) -> "Tenant":
        if not isinstance(
            security_profile_ref,
            TenantSecurityProfileReference,
        ):
            raise TypeError(
                "security_profile_ref must be "
                "TenantSecurityProfileReference"
            )

        if (
            security_profile_ref
            == self.security_profile_ref
        ):
            return self

        return replace(
            self,
            security_profile_ref=security_profile_ref,
            revision=self.revision + 1,
            updated_at=_utc_now(),
        )

    def with_region_jurisdiction(
        self,
        reference: TenantRegionJurisdictionReference,
    ) -> "Tenant":
        if not isinstance(
            reference,
            TenantRegionJurisdictionReference,
        ):
            raise TypeError(
                "reference must be "
                "TenantRegionJurisdictionReference"
            )

        return replace(
            self,
            region_jurisdiction_ref=reference,
            residency_region=reference.region,
            jurisdiction=reference.jurisdiction,
            revision=self.revision + 1,
            updated_at=_utc_now(),
        )

    def transition_to(
        self,
        status: TenantStatus,
    ) -> "Tenant":
        if not isinstance(
            status,
            TenantStatus,
        ):
            raise TypeError(
                "status must be TenantStatus"
            )

        if status is self.status:
            return self

        allowed = _ALLOWED_TRANSITIONS[self.status]

        if status not in allowed:
            raise ValueError(
                "invalid tenant lifecycle transition: "
                f"{self.status.value} -> {status.value}"
            )

        if status is TenantStatus.ACTIVE:
            if self.owner_identity_id is None:
                raise ValueError(
                    "tenant cannot become ACTIVE "
                    "without an owner"
                )

            if self.primary_admin_identity_id is None:
                raise ValueError(
                    "tenant cannot become ACTIVE "
                    "without a primary admin"
                )

            if not self.security_profile_ref.fail_closed:
                raise ValueError(
                    "tenant cannot become ACTIVE "
                    "without fail-closed security profile"
                )

            if not (
                self.security_profile_ref
                .require_valid_tenant_context
            ):
                raise ValueError(
                    "tenant cannot become ACTIVE "
                    "without mandatory tenant context"
                )

        return replace(
            self,
            status=status,
            revision=self.revision + 1,
            updated_at=_utc_now(),
        )

    @property
    def is_active(self) -> bool:
        return self.status is TenantStatus.ACTIVE

    @property
    def is_context_valid(self) -> bool:
        return self.status in {
            TenantStatus.ACTIVE,
            TenantStatus.RESTRICTED,
        }

    @property
    def accepts_new_activity(self) -> bool:
        return self.status is TenantStatus.ACTIVE


@dataclass(frozen=True, slots=True)
class TenantContext:
    """Resolved tenant context for downstream layers.

    T02 creates/validates the tenant context.
    T03+ may enrich it with membership and authority.
    """

    tenant_id: UUID
    tenant_revision: int
    tenant_status: TenantStatus
    tenant_kind: TenantKind
    operating_mode: OperatingMode
    configuration_ref: TenantConfigurationReference
    security_profile_ref: TenantSecurityProfileReference
    region_jurisdiction_ref: TenantRegionJurisdictionReference | None
    resolved_at: datetime = field(
        default_factory=_utc_now
    )

    def __post_init__(self) -> None:
        _validate_uuid(
            self.tenant_id,
            "tenant_id",
        )

        if not isinstance(
            self.tenant_revision,
            int,
        ):
            raise TypeError(
                "tenant_revision must be int"
            )

        if self.tenant_revision < 1:
            raise ValueError(
                "tenant_revision must be >= 1"
            )

        if not isinstance(
            self.tenant_status,
            TenantStatus,
        ):
            raise TypeError(
                "tenant_status must be TenantStatus"
            )

        if not isinstance(
            self.tenant_kind,
            TenantKind,
        ):
            raise TypeError(
                "tenant_kind must be TenantKind"
            )

        if not isinstance(
            self.operating_mode,
            OperatingMode,
        ):
            raise TypeError(
                "operating_mode must be OperatingMode"
            )

        if not isinstance(
            self.configuration_ref,
            TenantConfigurationReference,
        ):
            raise TypeError(
                "configuration_ref must be "
                "TenantConfigurationReference"
            )

        if not isinstance(
            self.security_profile_ref,
            TenantSecurityProfileReference,
        ):
            raise TypeError(
                "security_profile_ref must be "
                "TenantSecurityProfileReference"
            )

        if (
            self.region_jurisdiction_ref is not None
            and not isinstance(
                self.region_jurisdiction_ref,
                TenantRegionJurisdictionReference,
            )
        ):
            raise TypeError(
                "region_jurisdiction_ref must be "
                "TenantRegionJurisdictionReference or None"
            )

        _validate_aware(
            self.resolved_at,
            "resolved_at",
        )

    @property
    def is_valid(self) -> bool:
        return self.tenant_status in {
            TenantStatus.ACTIVE,
            TenantStatus.RESTRICTED,
        }

    @property
    def accepts_new_activity(self) -> bool:
        return self.tenant_status is TenantStatus.ACTIVE


@dataclass(frozen=True, slots=True)
class TenantResolutionResult:
    status: TenantResolutionStatus
    tenant_id: UUID | None = None
    tenant_revision: int | None = None
    context: TenantContext | None = None
    reason: str = ""

    def __post_init__(self) -> None:
        if not isinstance(
            self.status,
            TenantResolutionStatus,
        ):
            raise TypeError(
                "status must be TenantResolutionStatus"
            )

        if self.tenant_id is not None:
            _validate_uuid(
                self.tenant_id,
                "tenant_id",
            )

        if self.tenant_revision is not None:
            if not isinstance(
                self.tenant_revision,
                int,
            ):
                raise TypeError(
                    "tenant_revision must be int or None"
                )

            if self.tenant_revision < 1:
                raise ValueError(
                    "tenant_revision must be >= 1"
                )

        if self.context is not None and not isinstance(
            self.context,
            TenantContext,
        ):
            raise TypeError(
                "context must be TenantContext or None"
            )

        if not isinstance(
            self.reason,
            str,
        ):
            raise TypeError(
                "reason must be string"
            )

        if (
            self.status is TenantResolutionStatus.RESOLVED
            and self.context is None
        ):
            raise ValueError(
                "RESOLVED result requires tenant context"
            )

        if (
            self.status is not TenantResolutionStatus.RESOLVED
            and self.context is not None
        ):
            raise ValueError(
                "non-resolved result cannot carry tenant context"
            )

    @property
    def resolved(self) -> bool:
        return (
            self.status is TenantResolutionStatus.RESOLVED
        )


@dataclass(frozen=True, slots=True)
class TenantProvisioningIntent:
    intent_id: UUID
    tenant_id: UUID
    idempotency_key: str
    status: ProvisioningIntentStatus = (
        ProvisioningIntentStatus.REQUESTED
    )
    revision: int = 1
    requested_at: datetime = field(
        default_factory=_utc_now
    )
    updated_at: datetime = field(
        default_factory=_utc_now
    )

    def __post_init__(self) -> None:
        _validate_uuid(
            self.intent_id,
            "intent_id",
        )
        _validate_uuid(
            self.tenant_id,
            "tenant_id",
        )

        if not isinstance(
            self.status,
            ProvisioningIntentStatus,
        ):
            raise TypeError(
                "status must be ProvisioningIntentStatus"
            )

        key = _required_text(
            self.idempotency_key,
            "idempotency_key",
            200,
        )

        if not isinstance(
            self.revision,
            int,
        ):
            raise TypeError(
                "revision must be int"
            )

        if self.revision < 1:
            raise ValueError(
                "revision must be >= 1"
            )

        requested_at = _validate_aware(
            self.requested_at,
            "requested_at",
        )
        updated_at = _validate_aware(
            self.updated_at,
            "updated_at",
        )

        if updated_at < requested_at:
            raise ValueError(
                "updated_at cannot be earlier than requested_at"
            )

        object.__setattr__(
            self,
            "idempotency_key",
            key,
        )

    @classmethod
    def create(
        cls,
        *,
        tenant_id: UUID,
        idempotency_key: str,
    ) -> "TenantProvisioningIntent":
        now = _utc_now()

        return cls(
            intent_id=uuid4(),
            tenant_id=tenant_id,
            idempotency_key=idempotency_key,
            requested_at=now,
            updated_at=now,
        )

    def with_status(
        self,
        status: ProvisioningIntentStatus,
    ) -> "TenantProvisioningIntent":
        if not isinstance(
            status,
            ProvisioningIntentStatus,
        ):
            raise TypeError(
                "status must be ProvisioningIntentStatus"
            )

        if status is self.status:
            return self

        return replace(
            self,
            status=status,
            revision=self.revision + 1,
            updated_at=_utc_now(),
        )

    def key(self) -> tuple[UUID, str]:
        return (
            self.tenant_id,
            self.idempotency_key,
        )


class TenantRegistry:
    """Deterministic in-memory T02 tenant resolution boundary.

    This is the canonical T02 lookup boundary.

    It is deliberately NOT:
    - a membership engine
    - an authorization engine
    - a tenant-isolation enforcement engine
    - a credential/session engine
    - a persistence implementation
    - an audit engine
    """

    def __init__(self) -> None:
        self._tenants: dict[UUID, Tenant] = {}
        self._slugs: dict[str, UUID] = {}

    def register_tenant(
        self,
        tenant: Tenant,
    ) -> None:
        if not isinstance(
            tenant,
            Tenant,
        ):
            raise TypeError(
                "tenant must be Tenant"
            )

        existing = self._tenants.get(
            tenant.tenant_id
        )

        existing_slug_owner = self._slugs.get(
            tenant.slug
        )

        if (
            existing_slug_owner is not None
            and existing_slug_owner
            != tenant.tenant_id
        ):
            raise ValueError(
                "tenant slug is already assigned "
                "to another tenant"
            )

        if existing is None:
            self._tenants[
                tenant.tenant_id
            ] = tenant
            self._slugs[
                tenant.slug
            ] = tenant.tenant_id
            return

        if existing.slug != tenant.slug:
            raise ValueError(
                "registered tenant slug is immutable"
            )

        if tenant.revision < existing.revision:
            raise ValueError(
                "tenant revision cannot move backwards"
            )

        if (
            tenant.revision == existing.revision
            and tenant != existing
        ):
            raise ValueError(
                "same tenant revision cannot represent "
                "different tenant state"
            )

        self._tenants[
            tenant.tenant_id
        ] = tenant
        self._slugs[
            tenant.slug
        ] = tenant.tenant_id

    def get_tenant(
        self,
        tenant_id: UUID,
    ) -> Tenant | None:
        _validate_uuid(
            tenant_id,
            "tenant_id",
        )

        return self._tenants.get(
            tenant_id
        )

    def get_tenant_by_slug(
        self,
        slug: str,
    ) -> Tenant | None:
        normalized = _normalize_slug(slug)

        tenant_id = self._slugs.get(
            normalized
        )

        if tenant_id is None:
            return None

        return self._tenants.get(
            tenant_id
        )

    def resolve_context(
        self,
        tenant_id: UUID,
    ) -> TenantResolutionResult:
        tenant = self.get_tenant(
            tenant_id
        )

        if tenant is None:
            return TenantResolutionResult(
                status=TenantResolutionStatus.NOT_FOUND,
                tenant_id=tenant_id,
                reason="tenant not found",
            )

        if tenant.status is TenantStatus.ARCHIVED:
            return TenantResolutionResult(
                status=TenantResolutionStatus.ARCHIVED,
                tenant_id=tenant.tenant_id,
                tenant_revision=tenant.revision,
                reason="tenant is archived",
            )

        if not tenant.is_context_valid:
            return TenantResolutionResult(
                status=TenantResolutionStatus.INACTIVE,
                tenant_id=tenant.tenant_id,
                tenant_revision=tenant.revision,
                reason=(
                    "tenant does not provide a valid "
                    "execution context"
                ),
            )

        context = TenantContext(
            tenant_id=tenant.tenant_id,
            tenant_revision=tenant.revision,
            tenant_status=tenant.status,
            tenant_kind=tenant.tenant_kind,
            operating_mode=tenant.operating_mode,
            configuration_ref=tenant.configuration_ref,
            security_profile_ref=tenant.security_profile_ref,
            region_jurisdiction_ref=(
                tenant.region_jurisdiction_ref
            ),
        )

        return TenantResolutionResult(
            status=TenantResolutionStatus.RESOLVED,
            tenant_id=tenant.tenant_id,
            tenant_revision=tenant.revision,
            context=context,
            reason="tenant context resolved",
        )

    def require_context(
        self,
        tenant_id: UUID,
    ) -> TenantContext:
        result = self.resolve_context(
            tenant_id
        )

        if not result.resolved:
            raise TenantContextDeniedError(
                "NO_VALID_TENANT_CONTEXT: "
                f"{result.reason}"
            )

        assert result.context is not None

        return result.context
