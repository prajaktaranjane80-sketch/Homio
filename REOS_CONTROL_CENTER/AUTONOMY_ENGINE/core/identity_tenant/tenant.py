from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from enum import StrEnum
from re import fullmatch
from uuid import UUID, uuid4


_TENANT_SLUG_PATTERN = r"^[a-z0-9][a-z0-9._-]{1,62}[a-z0-9]$"


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


def _normalize_slug(slug: str) -> str:
    value = _required_text(slug, "slug", 64).lower()

    if not fullmatch(_TENANT_SLUG_PATTERN, value):
        raise ValueError(
            "slug must be 3-64 characters, lowercase, and contain "
            "only letters, digits, '.', '_' or '-'"
        )

    return value


def _validate_uuid(value: UUID, field_name: str) -> UUID:
    if not isinstance(value, UUID):
        raise TypeError(f"{field_name} must be a UUID")
    return value


def _validate_aware(value: datetime, field_name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value


class TenantKind(StrEnum):
    BROKERAGE = "BROKERAGE"
    BUILDER = "BUILDER"
    ENTERPRISE = "ENTERPRISE"
    PARTNER = "PARTNER"
    PLATFORM = "PLATFORM"


class OperatingMode(StrEnum):
    OWNED_INTERNATIONAL_BROKERAGE = "OWNED_INTERNATIONAL_BROKERAGE"
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


_ALLOWED_TRANSITIONS: dict[
    TenantStatus,
    frozenset[TenantStatus],
] = {
    TenantStatus.PROVISIONING: frozenset({
        TenantStatus.PENDING_ACTIVATION,
        TenantStatus.RESTRICTED,
        TenantStatus.DEACTIVATING,
    }),
    TenantStatus.PENDING_ACTIVATION: frozenset({
        TenantStatus.ACTIVE,
        TenantStatus.RESTRICTED,
        TenantStatus.SUSPENDED,
        TenantStatus.DEACTIVATING,
    }),
    TenantStatus.ACTIVE: frozenset({
        TenantStatus.RESTRICTED,
        TenantStatus.SUSPENDED,
        TenantStatus.DEACTIVATING,
    }),
    TenantStatus.RESTRICTED: frozenset({
        TenantStatus.ACTIVE,
        TenantStatus.SUSPENDED,
        TenantStatus.DEACTIVATING,
    }),
    TenantStatus.SUSPENDED: frozenset({
        TenantStatus.ACTIVE,
        TenantStatus.RESTRICTED,
        TenantStatus.DEACTIVATING,
    }),
    TenantStatus.DEACTIVATING: frozenset({
        TenantStatus.DEACTIVATED,
    }),
    TenantStatus.DEACTIVATED: frozenset({
        TenantStatus.ARCHIVED,
    }),
    TenantStatus.ARCHIVED: frozenset(),
}


@dataclass(frozen=True, slots=True)
class Tenant:
    tenant_id: UUID
    tenant_kind: TenantKind
    operating_mode: OperatingMode
    display_name: str
    slug: str
    status: TenantStatus = TenantStatus.PROVISIONING
    isolation_profile: IsolationProfile = IsolationProfile.SHARED_LOGICAL
    residency_mode: DataResidencyMode = DataResidencyMode.GLOBAL_ALLOWED
    residency_region: str | None = None
    jurisdiction: str | None = None
    quota_profile: str = "default"
    owner_identity_id: UUID | None = None
    primary_admin_identity_id: UUID | None = None
    revision: int = 1
    created_at: datetime = field(default_factory=_utc_now)
    updated_at: datetime = field(default_factory=_utc_now)

    def __post_init__(self) -> None:
        _validate_uuid(self.tenant_id, "tenant_id")

        if not isinstance(self.tenant_kind, TenantKind):
            raise TypeError("tenant_kind must be TenantKind")

        if not isinstance(self.operating_mode, OperatingMode):
            raise TypeError("operating_mode must be OperatingMode")

        if not isinstance(self.status, TenantStatus):
            raise TypeError("status must be TenantStatus")

        if not isinstance(self.isolation_profile, IsolationProfile):
            raise TypeError("isolation_profile must be IsolationProfile")

        if not isinstance(self.residency_mode, DataResidencyMode):
            raise TypeError("residency_mode must be DataResidencyMode")

        if self.owner_identity_id is not None:
            _validate_uuid(self.owner_identity_id, "owner_identity_id")

        if self.primary_admin_identity_id is not None:
            _validate_uuid(
                self.primary_admin_identity_id,
                "primary_admin_identity_id",
            )

        if self.revision < 1:
            raise ValueError("revision must be >= 1")

        _validate_aware(self.created_at, "created_at")
        _validate_aware(self.updated_at, "updated_at")

        object.__setattr__(
            self,
            "display_name",
            _required_text(self.display_name, "display_name", 200),
        )
        object.__setattr__(self, "slug", _normalize_slug(self.slug))
        object.__setattr__(
            self,
            "quota_profile",
            _required_text(self.quota_profile, "quota_profile", 128),
        )

        if self.residency_region is not None:
            object.__setattr__(
                self,
                "residency_region",
                _required_text(
                    self.residency_region,
                    "residency_region",
                    128,
                ),
            )

        if self.jurisdiction is not None:
            object.__setattr__(
                self,
                "jurisdiction",
                _required_text(
                    self.jurisdiction,
                    "jurisdiction",
                    128,
                ),
            )

        if self.residency_mode in (
            DataResidencyMode.REGION_BOUND,
            DataResidencyMode.COUNTRY_BOUND,
            DataResidencyMode.CUSTOM_POLICY,
        ):
            if not self.residency_region and not self.jurisdiction:
                raise ValueError(
                    "restricted residency mode requires residency_region "
                    "or jurisdiction"
                )

    @classmethod
    def create(
        cls,
        *,
        tenant_kind: TenantKind,
        operating_mode: OperatingMode,
        display_name: str,
        slug: str,
        isolation_profile: IsolationProfile = IsolationProfile.SHARED_LOGICAL,
        residency_mode: DataResidencyMode = DataResidencyMode.GLOBAL_ALLOWED,
        residency_region: str | None = None,
        jurisdiction: str | None = None,
        quota_profile: str = "default",
        owner_identity_id: UUID | None = None,
        primary_admin_identity_id: UUID | None = None,
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

    def transition_to(self, status: TenantStatus) -> "Tenant":
        if not isinstance(status, TenantStatus):
            raise TypeError("status must be TenantStatus")

        if status is self.status:
            return self

        allowed = _ALLOWED_TRANSITIONS[self.status]

        if status not in allowed:
            raise ValueError(
                f"invalid tenant lifecycle transition: "
                f"{self.status.value} -> {status.value}"
            )

        if status is TenantStatus.ACTIVE:
            if self.owner_identity_id is None:
                raise ValueError(
                    "tenant cannot become ACTIVE without an owner"
                )

            if self.primary_admin_identity_id is None:
                raise ValueError(
                    "tenant cannot become ACTIVE without a primary admin"
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
    def accepts_new_activity(self) -> bool:
        return self.status is TenantStatus.ACTIVE


@dataclass(frozen=True, slots=True)
class TenantProvisioningIntent:
    intent_id: UUID
    tenant_id: UUID
    idempotency_key: str
    status: ProvisioningIntentStatus = ProvisioningIntentStatus.REQUESTED
    revision: int = 1
    requested_at: datetime = field(default_factory=_utc_now)
    updated_at: datetime = field(default_factory=_utc_now)

    def __post_init__(self) -> None:
        _validate_uuid(self.intent_id, "intent_id")
        _validate_uuid(self.tenant_id, "tenant_id")

        if not isinstance(self.status, ProvisioningIntentStatus):
            raise TypeError(
                "status must be ProvisioningIntentStatus"
            )

        key = _required_text(
            self.idempotency_key,
            "idempotency_key",
            200,
        )

        if self.revision < 1:
            raise ValueError("revision must be >= 1")

        _validate_aware(self.requested_at, "requested_at")
        _validate_aware(self.updated_at, "updated_at")

        object.__setattr__(self, "idempotency_key", key)

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
        if not isinstance(status, ProvisioningIntentStatus):
            raise TypeError(
                "status must be ProvisioningIntentStatus"
            )

        return replace(
            self,
            status=status,
            revision=self.revision + 1,
            updated_at=_utc_now(),
        )

    def key(self) -> tuple[UUID, str]:
        return (self.tenant_id, self.idempotency_key)
