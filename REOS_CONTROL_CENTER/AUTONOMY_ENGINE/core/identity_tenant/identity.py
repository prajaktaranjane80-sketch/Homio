from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from enum import StrEnum
from re import fullmatch
from uuid import UUID, uuid4


_HANDLE_PATTERN = r"^[a-z0-9][a-z0-9._-]{2,63}$"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _required_text(value: str, field_name: str, max_length: int) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")

    value = value.strip()

    if not value:
        raise ValueError(f"{field_name} cannot be empty")

    if len(value) > max_length:
        raise ValueError(
            f"{field_name} exceeds maximum length {max_length}"
        )

    return value


def _normalize_handle(value: str) -> str:
    value = _required_text(value, "handle", 64).lower()

    if not fullmatch(_HANDLE_PATTERN, value):
        raise ValueError(
            "handle must contain only lowercase letters, numbers, "
            "dot, underscore or hyphen and must start with a letter/number"
        )

    return value


class IdentityType(StrEnum):
    HUMAN = "HUMAN"
    SERVICE = "SERVICE"
    AI = "AI"



    SYSTEM = "SYSTEM"

class IdentityStatus(StrEnum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    DEACTIVATED = "DEACTIVATED"


class PrivacyClass(StrEnum):
    INTERNAL = "INTERNAL"
    CONFIDENTIAL = "CONFIDENTIAL"
    RESTRICTED = "RESTRICTED"


class AccountStatus(StrEnum):
    ENABLED = "ENABLED"
    LOCKED = "LOCKED"
    DISABLED = "DISABLED"


@dataclass(frozen=True, slots=True)
class Identity:
    """Immutable authoritative identity record.

    Authentication secrets, sessions, tenant memberships and permissions are
    deliberately not stored here. They belong to later CORE-001 boundaries.
    """

    identity_id: UUID
    identity_type: IdentityType
    display_name: str
    handle: str
    status: IdentityStatus = IdentityStatus.ACTIVE
    privacy_class: PrivacyClass = PrivacyClass.INTERNAL
    revision: int = 1
    created_at: datetime = field(default_factory=_utc_now)
    updated_at: datetime = field(default_factory=_utc_now)

    def __post_init__(self) -> None:
        if not isinstance(self.identity_id, UUID):
            raise TypeError("identity_id must be UUID")

        if not isinstance(self.identity_type, IdentityType):
            raise TypeError("identity_type must be IdentityType")

        if not isinstance(self.status, IdentityStatus):
            raise TypeError("status must be IdentityStatus")

        if not isinstance(self.privacy_class, PrivacyClass):
            raise TypeError("privacy_class must be PrivacyClass")

        if self.revision < 1:
            raise ValueError("revision must be >= 1")

        object.__setattr__(
            self,
            "display_name",
            _required_text(self.display_name, "display_name", 120),
        )
        object.__setattr__(
            self,
            "handle",
            _normalize_handle(self.handle),
        )

        if self.created_at.tzinfo is None or self.updated_at.tzinfo is None:
            raise ValueError("identity timestamps must be timezone-aware")

    @classmethod
    def create(
        cls,
        *,
        identity_type: IdentityType,
        display_name: str,
        handle: str,
        privacy_class: PrivacyClass = PrivacyClass.INTERNAL,
    ) -> "Identity":
        now = _utc_now()

        return cls(
            identity_id=uuid4(),
            identity_type=identity_type,
            display_name=display_name,
            handle=handle,
            privacy_class=privacy_class,
            created_at=now,
            updated_at=now,
        )

    def with_status(self, status: IdentityStatus) -> "Identity":
        if status == self.status:
            return self

        return replace(
            self,
            status=status,
            revision=self.revision + 1,
            updated_at=_utc_now(),
        )

    def renamed(self, display_name: str) -> "Identity":
        normalized = _required_text(
            display_name,
            "display_name",
            120,
        )

        if normalized == self.display_name:
            return self

        return replace(
            self,
            display_name=normalized,
            revision=self.revision + 1,
            updated_at=_utc_now(),
        )


@dataclass(frozen=True, slots=True)
class IdentityAccount:
    """Authentication-independent account boundary.

    Credentials/tokens are intentionally absent. The account only owns
    lifecycle and authentication epoch state.
    """

    account_id: UUID
    identity_id: UUID
    status: AccountStatus = AccountStatus.ENABLED
    authentication_epoch: int = 1
    created_at: datetime = field(default_factory=_utc_now)
    updated_at: datetime = field(default_factory=_utc_now)

    def __post_init__(self) -> None:
        if not isinstance(self.account_id, UUID):
            raise TypeError("account_id must be UUID")

        if not isinstance(self.identity_id, UUID):
            raise TypeError("identity_id must be UUID")

        if not isinstance(self.status, AccountStatus):
            raise TypeError("status must be AccountStatus")

        if self.authentication_epoch < 1:
            raise ValueError("authentication_epoch must be >= 1")

        if self.created_at.tzinfo is None or self.updated_at.tzinfo is None:
            raise ValueError("account timestamps must be timezone-aware")

    @classmethod
    def create(cls, identity_id: UUID) -> "IdentityAccount":
        return cls(
            account_id=uuid4(),
            identity_id=identity_id,
        )

    def rotate_authentication_epoch(self) -> "IdentityAccount":
        return replace(
            self,
            authentication_epoch=self.authentication_epoch + 1,
            updated_at=_utc_now(),
        )

def _validate_external_provider(provider: str) -> str:
    if not isinstance(provider, str):
        raise TypeError("provider must be a string")

    candidate = provider.strip().lower()

    if not candidate:
        raise ValueError("provider cannot be empty")

    if len(candidate) > 255:
        raise ValueError("provider is too long")

    if any(ord(ch) < 32 or ch.isspace() for ch in candidate):
        raise ValueError("provider must not contain whitespace or control characters")

    return candidate


def _validate_external_subject(subject: str) -> str:
    if not isinstance(subject, str):
        raise TypeError("subject must be a string")

    if not subject:
        raise ValueError("subject cannot be empty")

    if len(subject) > 255:
        raise ValueError("subject is too long")

    if any(ord(ch) < 32 for ch in subject):
        raise ValueError("subject must not contain control characters")

    return subject


class ExternalIdentityStatus(StrEnum):
    ACTIVE = "ACTIVE"
    REVOKED = "REVOKED"


@dataclass(frozen=True, slots=True)
class ExternalIdentityReference:
    reference_id: UUID
    identity_id: UUID
    provider: str
    subject: str
    status: ExternalIdentityStatus = ExternalIdentityStatus.ACTIVE
    revision: int = 1
    linked_at: datetime = field(default_factory=_utc_now)

    def __post_init__(self) -> None:
        if not isinstance(self.reference_id, UUID):
            raise TypeError("reference_id must be a UUID")

        if not isinstance(self.identity_id, UUID):
            raise TypeError("identity_id must be a UUID")

        if not isinstance(self.status, ExternalIdentityStatus):
            raise TypeError("status must be ExternalIdentityStatus")

        if self.revision < 1:
            raise ValueError("revision must be >= 1")

        if self.linked_at.tzinfo is None or self.linked_at.utcoffset() is None:
            raise ValueError("linked_at must be timezone-aware")

        object.__setattr__(
            self,
            "provider",
            _validate_external_provider(self.provider),
        )
        object.__setattr__(
            self,
            "subject",
            _validate_external_subject(self.subject),
        )

    @classmethod
    def create(
        cls,
        identity_id: UUID,
        provider: str,
        subject: str,
    ) -> "ExternalIdentityReference":
        return cls(
            reference_id=uuid4(),
            identity_id=identity_id,
            provider=provider,
            subject=subject,
        )

    def external_key(self) -> tuple[str, str]:
        return (self.provider, self.subject)

    def with_status(
        self,
        status: ExternalIdentityStatus,
    ) -> "ExternalIdentityReference":
        if not isinstance(status, ExternalIdentityStatus):
            raise TypeError("status must be ExternalIdentityStatus")

        return replace(
            self,
            status=status,
            revision=self.revision + 1,
        )

    def revoked(self) -> "ExternalIdentityReference":
        return self.with_status(ExternalIdentityStatus.REVOKED)

class IdentityResolutionStatus(StrEnum):
    RESOLVED = "RESOLVED"
    NOT_FOUND = "NOT_FOUND"
    REVOKED = "REVOKED"


@dataclass(frozen=True, slots=True)
class IdentityResolutionResult:
    status: IdentityResolutionStatus
    identity_id: UUID | None = None
    reference_id: UUID | None = None
    provider: str = ""
    subject: str = ""
    reason: str = ""

    @property
    def resolved(self) -> bool:
        return self.status is IdentityResolutionStatus.RESOLVED


class IdentityRegistry:
    """
    Deterministic in-memory identity registry for the T01 domain boundary.

    Persistence belongs to the later platform/data layers. This registry
    defines the authoritative resolution contract used by those layers.
    """

    def __init__(self) -> None:
        self._identities: dict[UUID, Identity] = {}
        self._external: dict[tuple[str, str], ExternalIdentityReference] = {}

    def register_identity(self, identity: Identity) -> None:
        if not isinstance(identity, Identity):
            raise TypeError("identity must be an Identity")

        existing = self._identities.get(identity.identity_id)

        if existing is not None and existing != identity:
            raise ValueError("identity_id already belongs to a different identity")

        self._identities[identity.identity_id] = identity

    def register_external_reference(
        self,
        reference: ExternalIdentityReference,
    ) -> None:
        if not isinstance(reference, ExternalIdentityReference):
            raise TypeError(
                "reference must be an ExternalIdentityReference"
            )

        if reference.identity_id not in self._identities:
            raise ValueError(
                "external reference requires a registered canonical identity"
            )

        key = reference.external_key()
        existing = self._external.get(key)

        if existing is not None:
            if existing.identity_id != reference.identity_id:
                raise ValueError(
                    "external identity key is already linked to another identity"
                )

            if existing.reference_id != reference.reference_id:
                raise ValueError(
                    "external identity key already has a different reference"
                )

        self._external[key] = reference

    def resolve_external(
        self,
        provider: str,
        subject: str,
    ) -> IdentityResolutionResult:
        provider_value = _validate_external_provider(provider)
        subject_value = _validate_external_subject(subject)

        key = (provider_value, subject_value)
        reference = self._external.get(key)

        if reference is None:
            return IdentityResolutionResult(
                status=IdentityResolutionStatus.NOT_FOUND,
                provider=provider_value,
                subject=subject_value,
                reason="external identity reference not found",
            )

        if reference.status is ExternalIdentityStatus.REVOKED:
            return IdentityResolutionResult(
                status=IdentityResolutionStatus.REVOKED,
                reference_id=reference.reference_id,
                provider=provider_value,
                subject=subject_value,
                reason="external identity reference is revoked",
            )

        identity = self._identities.get(reference.identity_id)

        if identity is None:
            return IdentityResolutionResult(
                status=IdentityResolutionStatus.NOT_FOUND,
                reference_id=reference.reference_id,
                provider=provider_value,
                subject=subject_value,
                reason="canonical identity is missing",
            )

        if identity.status is not IdentityStatus.ACTIVE:
            return IdentityResolutionResult(
                status=IdentityResolutionStatus.REVOKED,
                identity_id=identity.identity_id,
                reference_id=reference.reference_id,
                provider=provider_value,
                subject=subject_value,
                reason="canonical identity is not active",
            )

        return IdentityResolutionResult(
            status=IdentityResolutionStatus.RESOLVED,
            identity_id=identity.identity_id,
            reference_id=reference.reference_id,
            provider=provider_value,
            subject=subject_value,
            reason="canonical identity resolved",
        )

    def get_identity(self, identity_id: UUID) -> Identity | None:
        return self._identities.get(identity_id)

