from __future__ import annotations

from dataclasses import dataclass, field, fields, replace
from datetime import datetime, timezone
from enum import StrEnum
from re import fullmatch
from uuid import UUID, uuid4


_HANDLE_PATTERN = r"^[a-z0-9][a-z0-9._-]{2,63}$"

FORBIDDEN_IDENTITY_FIELDS = frozenset(
    {
        "password",
        "password_hash",
        "secret",
        "access_token",
        "refresh_token",
        "private_key",
        "credential",
        "session_token",
    }
)


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


class ExternalIdentityStatus(StrEnum):
    ACTIVE = "ACTIVE"
    REVOKED = "REVOKED"


class IdentityResolutionStatus(StrEnum):
    RESOLVED = "RESOLVED"
    NOT_FOUND = "NOT_FOUND"
    REVOKED = "REVOKED"


IDENTITY_STATUS_TRANSITIONS: dict[
    IdentityStatus,
    frozenset[IdentityStatus],
] = {
    IdentityStatus.ACTIVE: frozenset(
        {
            IdentityStatus.SUSPENDED,
            IdentityStatus.DEACTIVATED,
        }
    ),
    IdentityStatus.SUSPENDED: frozenset(
        {
            IdentityStatus.ACTIVE,
            IdentityStatus.DEACTIVATED,
        }
    ),
    IdentityStatus.DEACTIVATED: frozenset(),
}


ACCOUNT_STATUS_TRANSITIONS: dict[
    AccountStatus,
    frozenset[AccountStatus],
] = {
    AccountStatus.ENABLED: frozenset(
        {
            AccountStatus.LOCKED,
            AccountStatus.DISABLED,
        }
    ),
    AccountStatus.LOCKED: frozenset(
        {
            AccountStatus.ENABLED,
            AccountStatus.DISABLED,
        }
    ),
    AccountStatus.DISABLED: frozenset(),
}


def _validate_identity_transition(
    current: IdentityStatus,
    target: IdentityStatus,
) -> None:
    if not isinstance(target, IdentityStatus):
        raise TypeError("status must be IdentityStatus")

    if target == current:
        return

    allowed = IDENTITY_STATUS_TRANSITIONS[current]

    if target not in allowed:
        raise ValueError(
            f"invalid identity status transition: "
            f"{current.value} -> {target.value}"
        )


def _validate_account_transition(
    current: AccountStatus,
    target: AccountStatus,
) -> None:
    if not isinstance(target, AccountStatus):
        raise TypeError("status must be AccountStatus")

    if target == current:
        return

    allowed = ACCOUNT_STATUS_TRANSITIONS[current]

    if target not in allowed:
        raise ValueError(
            f"invalid account status transition: "
            f"{current.value} -> {target.value}"
        )


@dataclass(frozen=True, slots=True)
class Identity:
    """Immutable authoritative identity record.

    T01 owns canonical identity data only.

    Deliberately outside this model:
    - authentication credentials
    - sessions
    - authorization permissions
    - tenant membership
    - persistence
    - event bus
    - audit engine
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

        if not isinstance(self.revision, int):
            raise TypeError("revision must be int")

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

        if not isinstance(self.created_at, datetime):
            raise TypeError("created_at must be datetime")

        if not isinstance(self.updated_at, datetime):
            raise TypeError("updated_at must be datetime")

        if self.created_at.tzinfo is None or self.created_at.utcoffset() is None:
            raise ValueError("created_at must be timezone-aware")

        if self.updated_at.tzinfo is None or self.updated_at.utcoffset() is None:
            raise ValueError("updated_at must be timezone-aware")

        if self.updated_at < self.created_at:
            raise ValueError("updated_at cannot be earlier than created_at")

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
            revision=1,
            created_at=now,
            updated_at=now,
        )

    def with_status(self, status: IdentityStatus) -> "Identity":
        _validate_identity_transition(self.status, status)

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

    Credentials, tokens and sessions are deliberately absent.

    The canonical Identity relationship is enforced by IdentityRegistry when
    an account is registered into the T01 domain boundary.
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

        if not isinstance(self.authentication_epoch, int):
            raise TypeError("authentication_epoch must be int")

        if self.authentication_epoch < 1:
            raise ValueError("authentication_epoch must be >= 1")

        if not isinstance(self.created_at, datetime):
            raise TypeError("created_at must be datetime")

        if not isinstance(self.updated_at, datetime):
            raise TypeError("updated_at must be datetime")

        if self.created_at.tzinfo is None or self.created_at.utcoffset() is None:
            raise ValueError("created_at must be timezone-aware")

        if self.updated_at.tzinfo is None or self.updated_at.utcoffset() is None:
            raise ValueError("updated_at must be timezone-aware")

        if self.updated_at < self.created_at:
            raise ValueError("updated_at cannot be earlier than created_at")

    @classmethod
    def create(cls, identity_id: UUID) -> "IdentityAccount":
        if not isinstance(identity_id, UUID):
            raise TypeError("identity_id must be UUID")

        return cls(
            account_id=uuid4(),
            identity_id=identity_id,
        )

    def with_status(self, status: AccountStatus) -> "IdentityAccount":
        _validate_account_transition(self.status, status)

        if status == self.status:
            return self

        return replace(
            self,
            status=status,
            updated_at=_utc_now(),
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
        raise ValueError(
            "provider must not contain whitespace or control characters"
        )

    return candidate


def _validate_external_subject(subject: str) -> str:
    if not isinstance(subject, str):
        raise TypeError("subject must be a string")

    if not subject:
        raise ValueError("subject cannot be empty")

    if len(subject) > 255:
        raise ValueError("subject is too long")

    if any(ord(ch) < 32 for ch in subject):
        raise ValueError(
            "subject must not contain control characters"
        )

    return subject


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
            raise TypeError(
                "status must be ExternalIdentityStatus"
            )

        if not isinstance(self.revision, int):
            raise TypeError("revision must be int")

        if self.revision < 1:
            raise ValueError("revision must be >= 1")

        if not isinstance(self.linked_at, datetime):
            raise TypeError("linked_at must be datetime")

        if (
            self.linked_at.tzinfo is None
            or self.linked_at.utcoffset() is None
        ):
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
        if not isinstance(identity_id, UUID):
            raise TypeError("identity_id must be UUID")

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
            raise TypeError(
                "status must be ExternalIdentityStatus"
            )

        if status == self.status:
            return self

        if (
            self.status is ExternalIdentityStatus.REVOKED
            and status is ExternalIdentityStatus.ACTIVE
        ):
            raise ValueError(
                "revoked external identity reference is terminal"
            )

        return replace(
            self,
            status=status,
            revision=self.revision + 1,
        )

    def revoked(self) -> "ExternalIdentityReference":
        return self.with_status(ExternalIdentityStatus.REVOKED)


@dataclass(frozen=True, slots=True)
class IdentityResolutionResult:
    status: IdentityResolutionStatus
    identity_id: UUID | None = None
    reference_id: UUID | None = None
    provider: str = ""
    subject: str = ""
    reason: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.status, IdentityResolutionStatus):
            raise TypeError(
                "status must be IdentityResolutionStatus"
            )

        if self.identity_id is not None and not isinstance(
            self.identity_id,
            UUID,
        ):
            raise TypeError("identity_id must be UUID or None")

        if self.reference_id is not None and not isinstance(
            self.reference_id,
            UUID,
        ):
            raise TypeError("reference_id must be UUID or None")

        if not isinstance(self.provider, str):
            raise TypeError("provider must be string")

        if not isinstance(self.subject, str):
            raise TypeError("subject must be string")

        if not isinstance(self.reason, str):
            raise TypeError("reason must be string")

    @property
    def resolved(self) -> bool:
        return self.status is IdentityResolutionStatus.RESOLVED


class IdentityRegistry:
    """Deterministic in-memory T01 identity resolution boundary.

    This registry is deliberately NOT:
    - a database repository
    - an authentication engine
    - an authorization engine
    - a session engine
    - a tenant-membership engine
    - an event bus
    - an audit engine
    """

    def __init__(self) -> None:
        self._identities: dict[UUID, Identity] = {}
        self._handles: dict[str, UUID] = {}
        self._external: dict[
            tuple[str, str],
            ExternalIdentityReference,
        ] = {}
        self._accounts: dict[UUID, IdentityAccount] = {}

    def register_identity(self, identity: Identity) -> None:
        if not isinstance(identity, Identity):
            raise TypeError("identity must be an Identity")

        existing = self._identities.get(identity.identity_id)

        if existing is not None and existing != identity:
            raise ValueError(
                "identity_id already belongs to a different identity"
            )

        existing_handle_identity = self._handles.get(identity.handle)

        if (
            existing_handle_identity is not None
            and existing_handle_identity != identity.identity_id
        ):
            raise ValueError(
                "handle is already assigned to another identity"
            )

        if existing is not None:
            if existing.handle != identity.handle:
                raise ValueError(
                    "registered identity cannot change its canonical handle"
                )

            self._identities[identity.identity_id] = identity
            self._handles[identity.handle] = identity.identity_id
            return

        self._identities[identity.identity_id] = identity
        self._handles[identity.handle] = identity.identity_id

    def get_identity(self, identity_id: UUID) -> Identity | None:
        if not isinstance(identity_id, UUID):
            raise TypeError("identity_id must be UUID")

        return self._identities.get(identity_id)

    def get_identity_by_handle(self, handle: str) -> Identity | None:
        normalized = _normalize_handle(handle)
        identity_id = self._handles.get(normalized)

        if identity_id is None:
            return None

        return self._identities.get(identity_id)

    def register_account(self, account: IdentityAccount) -> None:
        if not isinstance(account, IdentityAccount):
            raise TypeError(
                "account must be an IdentityAccount"
            )

        if account.identity_id not in self._identities:
            raise ValueError(
                "account requires a registered canonical identity"
            )

        existing = self._accounts.get(account.account_id)

        if existing is not None and existing != account:
            raise ValueError(
                "account_id already belongs to a different account"
            )

        self._accounts[account.account_id] = account

    def get_account(self, account_id: UUID) -> IdentityAccount | None:
        if not isinstance(account_id, UUID):
            raise TypeError("account_id must be UUID")

        return self._accounts.get(account_id)

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
                    "external identity key is already linked "
                    "to another identity"
                )

            if existing.reference_id != reference.reference_id:
                raise ValueError(
                    "external identity key already has "
                    "a different reference"
                )

            if existing != reference:
                raise ValueError(
                    "external identity reference replacement "
                    "must preserve the canonical reference"
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


def identity_model_field_names() -> frozenset[str]:
    """Return all fields owned by the T01 identity domain models."""

    model_types = (
        Identity,
        IdentityAccount,
        ExternalIdentityReference,
        IdentityResolutionResult,
    )

    return frozenset(
        field.name
        for model_type in model_types
        for field in fields(model_type)
    )
