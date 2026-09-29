from dataclasses import fields

import pytest
from uuid import UUID

from AUTONOMY_ENGINE.core.identity_tenant.identity import (
    ACCOUNT_STATUS_TRANSITIONS,
    FORBIDDEN_IDENTITY_FIELDS,
    IDENTITY_STATUS_TRANSITIONS,
    AccountStatus,
    ExternalIdentityReference,
    ExternalIdentityStatus,
    Identity,
    IdentityAccount,
    IdentityRegistry,
    IdentityResolutionStatus,
    IdentityStatus,
    IdentityType,
    PrivacyClass,
    identity_model_field_names,
)


def test_identity_creation_is_authoritative_and_typed():
    identity = Identity.create(
        identity_type=IdentityType.HUMAN,
        display_name="HOMIO Admin",
        handle="homio.admin",
    )

    assert isinstance(identity.identity_id, UUID)
    assert identity.identity_type is IdentityType.HUMAN
    assert identity.status is IdentityStatus.ACTIVE
    assert identity.revision == 1
    assert identity.handle == "homio.admin"


@pytest.mark.parametrize(
    "identity_type",
    list(IdentityType),
)
def test_all_supported_identity_types_are_first_class(identity_type):
    identity = Identity.create(
        identity_type=identity_type,
        display_name="Actor",
        handle=f"{identity_type.value.lower()}-actor",
    )

    assert identity.identity_type is identity_type


def test_handle_is_normalized():
    identity = Identity.create(
        identity_type=IdentityType.SERVICE,
        display_name="Search Service",
        handle="  SEARCH.Service  ",
    )

    assert identity.handle == "search.service"


@pytest.mark.parametrize(
    "handle",
    ["x", "bad handle", "bad/name", ""],
)
def test_invalid_handle_is_rejected(handle):
    with pytest.raises((ValueError, TypeError)):
        Identity.create(
            identity_type=IdentityType.HUMAN,
            display_name="Actor",
            handle=handle,
        )


def test_identity_id_is_immutable():
    identity = Identity.create(
        identity_type=IdentityType.HUMAN,
        display_name="Actor",
        handle="actor.immutable",
    )

    with pytest.raises((AttributeError, TypeError)):
        identity.identity_id = UUID(int=1)


def test_identity_state_transition_is_immutable():
    original = Identity.create(
        identity_type=IdentityType.HUMAN,
        display_name="Actor",
        handle="actor.one",
    )

    suspended = original.with_status(IdentityStatus.SUSPENDED)

    assert original.status is IdentityStatus.ACTIVE
    assert suspended.status is IdentityStatus.SUSPENDED
    assert suspended.revision == original.revision + 1
    assert suspended.identity_id == original.identity_id
    assert suspended.created_at == original.created_at


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (IdentityStatus.ACTIVE, IdentityStatus.SUSPENDED),
        (IdentityStatus.ACTIVE, IdentityStatus.DEACTIVATED),
        (IdentityStatus.SUSPENDED, IdentityStatus.ACTIVE),
        (IdentityStatus.SUSPENDED, IdentityStatus.DEACTIVATED),
    ],
)
def test_identity_valid_lifecycle_transitions(current, target):
    identity = Identity.create(
        identity_type=IdentityType.HUMAN,
        display_name="Actor",
        handle=f"{current.value.lower()}-{target.value.lower()}",
    )

    if current is not IdentityStatus.ACTIVE:
        identity = identity.with_status(current)

    transitioned = identity.with_status(target)

    assert transitioned.status is target
    assert transitioned.identity_id == identity.identity_id
    assert transitioned.revision == identity.revision + 1


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (IdentityStatus.DEACTIVATED, IdentityStatus.ACTIVE),
        (IdentityStatus.DEACTIVATED, IdentityStatus.SUSPENDED),
    ],
)
def test_deactivated_identity_is_terminal(current, target):
    identity = Identity.create(
        identity_type=IdentityType.HUMAN,
        display_name="Actor",
        handle=f"terminal-{target.value.lower()}",
    ).with_status(IdentityStatus.DEACTIVATED)

    with pytest.raises(ValueError):
        identity.with_status(target)


def test_identity_same_status_is_noop():
    identity = Identity.create(
        identity_type=IdentityType.HUMAN,
        display_name="Actor",
        handle="actor.noop",
    )

    result = identity.with_status(IdentityStatus.ACTIVE)

    assert result is identity
    assert result.revision == 1


def test_identity_rename_is_immutable():
    original = Identity.create(
        identity_type=IdentityType.HUMAN,
        display_name="Original",
        handle="original.actor",
    )

    renamed = original.renamed("Updated")

    assert original.display_name == "Original"
    assert renamed.display_name == "Updated"
    assert renamed.revision == original.revision + 1
    assert renamed.identity_id == original.identity_id
    assert renamed.created_at == original.created_at


def test_identity_rename_same_value_is_noop():
    identity = Identity.create(
        identity_type=IdentityType.HUMAN,
        display_name="Original",
        handle="original.noop",
    )

    result = identity.renamed(" Original ")

    assert result is identity
    assert result.revision == identity.revision


def test_revision_and_timestamp_invariants():
    identity = Identity.create(
        identity_type=IdentityType.HUMAN,
        display_name="Actor",
        handle="actor.revision",
    )

    renamed = identity.renamed("Updated")

    assert identity.revision == 1
    assert renamed.revision == 2
    assert renamed.identity_id == identity.identity_id
    assert renamed.created_at == identity.created_at
    assert renamed.updated_at >= identity.updated_at
    assert renamed.updated_at >= renamed.created_at


def test_restricted_privacy_class_is_supported():
    identity = Identity.create(
        identity_type=IdentityType.AI,
        display_name="Risk Agent",
        handle="risk-agent",
        privacy_class=PrivacyClass.RESTRICTED,
    )

    assert identity.privacy_class is PrivacyClass.RESTRICTED


def test_account_is_separate_from_identity():
    identity = Identity.create(
        identity_type=IdentityType.HUMAN,
        display_name="Broker",
        handle="broker.one",
    )

    account = IdentityAccount.create(identity.identity_id)

    assert account.identity_id == identity.identity_id
    assert account.account_id != identity.identity_id
    assert account.status is AccountStatus.ENABLED
    assert account.authentication_epoch == 1


def test_account_requires_uuid_identity_reference():
    with pytest.raises(TypeError):
        IdentityAccount.create("not-a-uuid")


def test_account_requires_registered_canonical_identity():
    registry = IdentityRegistry()

    account = IdentityAccount.create(
        UUID(int=999),
    )

    with pytest.raises(ValueError):
        registry.register_account(account)


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (AccountStatus.ENABLED, AccountStatus.LOCKED),
        (AccountStatus.ENABLED, AccountStatus.DISABLED),
        (AccountStatus.LOCKED, AccountStatus.ENABLED),
        (AccountStatus.LOCKED, AccountStatus.DISABLED),
    ],
)
def test_account_valid_lifecycle_transitions(current, target):
    identity = Identity.create(
        identity_type=IdentityType.HUMAN,
        display_name="Account Actor",
        handle=f"account-{current.value.lower()}-{target.value.lower()}",
    )

    account = IdentityAccount.create(identity.identity_id)

    if current is AccountStatus.LOCKED:
        account = account.with_status(AccountStatus.LOCKED)
    elif current is AccountStatus.DISABLED:
        account = account.with_status(AccountStatus.DISABLED)

    transitioned = account.with_status(target)

    assert transitioned.status is target
    assert transitioned.account_id == account.account_id
    assert transitioned.identity_id == identity.identity_id


def test_disabled_account_is_terminal():
    identity = Identity.create(
        identity_type=IdentityType.HUMAN,
        display_name="Disabled Actor",
        handle="disabled.actor",
    )

    account = IdentityAccount.create(identity.identity_id)
    disabled = account.with_status(AccountStatus.DISABLED)

    with pytest.raises(ValueError):
        disabled.with_status(AccountStatus.ENABLED)

    with pytest.raises(ValueError):
        disabled.with_status(AccountStatus.LOCKED)


def test_account_same_status_is_noop():
    identity = Identity.create(
        identity_type=IdentityType.HUMAN,
        display_name="Actor",
        handle="account.noop",
    )

    account = IdentityAccount.create(identity.identity_id)

    result = account.with_status(AccountStatus.ENABLED)

    assert result is account


def test_authentication_epoch_rotation_is_immutable():
    identity = Identity.create(
        identity_type=IdentityType.SERVICE,
        display_name="API Service",
        handle="api-service",
    )

    account = IdentityAccount.create(identity.identity_id)
    rotated = account.rotate_authentication_epoch()

    assert account.authentication_epoch == 1
    assert rotated.authentication_epoch == 2
    assert rotated.account_id == account.account_id
    assert rotated.identity_id == account.identity_id
    assert rotated.created_at == account.created_at
    assert rotated.updated_at >= account.updated_at


def test_authentication_epoch_is_monotonic():
    identity = Identity.create(
        identity_type=IdentityType.SERVICE,
        display_name="API Service",
        handle="api-service-epoch",
    )

    account = IdentityAccount.create(identity.identity_id)
    first = account.rotate_authentication_epoch()
    second = first.rotate_authentication_epoch()

    assert account.authentication_epoch < first.authentication_epoch
    assert first.authentication_epoch < second.authentication_epoch


def test_identity_and_account_timestamps_are_timezone_aware():
    identity = Identity.create(
        identity_type=IdentityType.HUMAN,
        display_name="Broker",
        handle="broker.two",
    )

    account = IdentityAccount.create(identity.identity_id)

    assert identity.created_at.tzinfo is not None
    assert identity.created_at.utcoffset() is not None
    assert identity.updated_at.tzinfo is not None
    assert identity.updated_at.utcoffset() is not None

    assert account.created_at.tzinfo is not None
    assert account.created_at.utcoffset() is not None
    assert account.updated_at.tzinfo is not None
    assert account.updated_at.utcoffset() is not None


def test_mixed_case_handle_normalizes_to_canonical_lowercase():
    identity = Identity.create(
        identity_type=IdentityType.SERVICE,
        display_name="Search Service",
        handle="BadName",
    )

    assert identity.handle == "badname"


def test_system_identity_is_first_class():
    identity = Identity.create(
        identity_type=IdentityType.SYSTEM,
        display_name="REOS Control System",
        handle="reos.system",
    )

    assert identity.identity_type is IdentityType.SYSTEM
    assert identity.handle == "reos.system"
    assert identity.status is IdentityStatus.ACTIVE


def test_registry_enforces_canonical_handle_uniqueness():
    first = Identity.create(
        identity_type=IdentityType.HUMAN,
        display_name="Broker One",
        handle="unique.handle",
    )

    second = Identity.create(
        identity_type=IdentityType.HUMAN,
        display_name="Broker Two",
        handle="different.handle",
    )

    registry = IdentityRegistry()
    registry.register_identity(first)

    collision = Identity(
        identity_id=second.identity_id,
        identity_type=second.identity_type,
        display_name=second.display_name,
        handle=" UNIQUE.HANDLE ",
        status=second.status,
        privacy_class=second.privacy_class,
        revision=second.revision,
        created_at=second.created_at,
        updated_at=second.updated_at,
    )

    with pytest.raises(ValueError):
        registry.register_identity(collision)


def test_registry_handle_lookup_is_case_insensitive():
    identity = Identity.create(
        identity_type=IdentityType.HUMAN,
        display_name="Broker",
        handle="Broker.Handle",
    )

    registry = IdentityRegistry()
    registry.register_identity(identity)

    assert registry.get_identity_by_handle("broker.handle") == identity
    assert registry.get_identity_by_handle(" BROKER.HANDLE ") == identity


def test_registry_cannot_rebind_identity_to_new_handle():
    identity = Identity.create(
        identity_type=IdentityType.HUMAN,
        display_name="Broker",
        handle="canonical.handle",
    )

    registry = IdentityRegistry()
    registry.register_identity(identity)

    changed = Identity(
        identity_id=identity.identity_id,
        identity_type=identity.identity_type,
        display_name=identity.display_name,
        handle="new.handle",
        status=identity.status,
        privacy_class=identity.privacy_class,
        revision=identity.revision + 1,
        created_at=identity.created_at,
        updated_at=identity.updated_at,
    )

    with pytest.raises(ValueError):
        registry.register_identity(changed)


def test_registry_identity_lookup_is_authoritative():
    identity = Identity.create(
        identity_type=IdentityType.HUMAN,
        display_name="Broker",
        handle="authoritative.lookup",
    )

    registry = IdentityRegistry()
    registry.register_identity(identity)

    assert registry.get_identity(identity.identity_id) == identity
    assert registry.get_identity(UUID(int=0)) is None


def test_external_identity_reference_is_first_class():
    identity_id = UUID(int=100)

    ref = ExternalIdentityReference.create(
        identity_id=identity_id,
        provider="  Microsoft  ",
        subject="AbC-123",
    )

    assert ref.identity_id == identity_id
    assert ref.provider == "microsoft"
    assert ref.subject == "AbC-123"
    assert ref.status is ExternalIdentityStatus.ACTIVE


def test_external_identity_subject_is_case_preserving():
    ref = ExternalIdentityReference.create(
        identity_id=UUID(int=101),
        provider="Google",
        subject="CaseSensitiveSubject",
    )

    assert ref.subject == "CaseSensitiveSubject"


def test_external_identity_key_is_deterministic():
    ref = ExternalIdentityReference.create(
        identity_id=UUID(int=102),
        provider="Google",
        subject="Subject-001",
    )

    assert ref.external_key() == ("google", "Subject-001")


def test_external_identity_revocation_is_immutable():
    ref = ExternalIdentityReference.create(
        identity_id=UUID(int=103),
        provider="oidc",
        subject="subject-001",
    )

    revoked = ref.revoked()

    assert ref.status is ExternalIdentityStatus.ACTIVE
    assert revoked.status is ExternalIdentityStatus.REVOKED
    assert revoked.revision == ref.revision + 1
    assert revoked.reference_id == ref.reference_id
    assert revoked.identity_id == ref.identity_id


def test_external_identity_revocation_is_terminal():
    ref = ExternalIdentityReference.create(
        identity_id=UUID(int=104),
        provider="oidc",
        subject="terminal-subject",
    ).revoked()

    with pytest.raises(ValueError):
        ref.with_status(ExternalIdentityStatus.ACTIVE)


def test_external_identity_same_status_is_noop():
    ref = ExternalIdentityReference.create(
        identity_id=UUID(int=105),
        provider="oidc",
        subject="noop-subject",
    )

    assert ref.with_status(ExternalIdentityStatus.ACTIVE) is ref


def test_external_identity_invalid_provider_is_rejected():
    for provider in ["", "bad provider", "bad\nprovider"]:
        with pytest.raises((ValueError, TypeError)):
            ExternalIdentityReference.create(
                identity_id=UUID(int=106),
                provider=provider,
                subject="subject",
            )


def test_external_identity_timestamps_are_timezone_aware():
    ref = ExternalIdentityReference.create(
        identity_id=UUID(int=107),
        provider="oidc",
        subject="subject-001",
    )

    assert ref.linked_at.tzinfo is not None
    assert ref.linked_at.utcoffset() is not None


def test_external_identity_resolution_is_deterministic():
    identity = Identity.create(
        identity_type=IdentityType.HUMAN,
        display_name="Broker",
        handle="broker.resolver",
    )

    registry = IdentityRegistry()
    registry.register_identity(identity)

    reference = ExternalIdentityReference.create(
        identity_id=identity.identity_id,
        provider="Google",
        subject="subject-001",
    )

    registry.register_external_reference(reference)

    first = registry.resolve_external("google", "subject-001")
    second = registry.resolve_external("Google", "subject-001")

    assert first.status is IdentityResolutionStatus.RESOLVED
    assert second.status is IdentityResolutionStatus.RESOLVED
    assert first.identity_id == identity.identity_id
    assert second.identity_id == identity.identity_id


def test_external_identity_unknown_reference_fails_closed():
    result = IdentityRegistry().resolve_external(
        "google",
        "unknown-subject",
    )

    assert result.status is IdentityResolutionStatus.NOT_FOUND
    assert result.resolved is False


def test_external_identity_duplicate_key_cannot_rebind():
    first_identity = Identity.create(
        identity_type=IdentityType.HUMAN,
        display_name="Broker One",
        handle="broker.one.resolver",
    )

    second_identity = Identity.create(
        identity_type=IdentityType.HUMAN,
        display_name="Broker Two",
        handle="broker.two.resolver",
    )

    registry = IdentityRegistry()
    registry.register_identity(first_identity)
    registry.register_identity(second_identity)

    first_reference = ExternalIdentityReference.create(
        identity_id=first_identity.identity_id,
        provider="google",
        subject="same-subject",
    )

    second_reference = ExternalIdentityReference.create(
        identity_id=second_identity.identity_id,
        provider="google",
        subject="same-subject",
    )

    registry.register_external_reference(first_reference)

    with pytest.raises(ValueError):
        registry.register_external_reference(second_reference)


def test_external_identity_same_reference_is_idempotent():
    identity = Identity.create(
        identity_type=IdentityType.HUMAN,
        display_name="Broker",
        handle="broker.external.idempotent",
    )

    registry = IdentityRegistry()
    registry.register_identity(identity)

    reference = ExternalIdentityReference.create(
        identity_id=identity.identity_id,
        provider="google",
        subject="same-reference",
    )

    registry.register_external_reference(reference)
    registry.register_external_reference(reference)

    result = registry.resolve_external(
        "google",
        "same-reference",
    )

    assert result.status is IdentityResolutionStatus.RESOLVED


def test_external_identity_revoked_reference_does_not_resolve():
    identity = Identity.create(
        identity_type=IdentityType.SERVICE,
        display_name="Search Service",
        handle="search.service.resolver",
    )

    registry = IdentityRegistry()
    registry.register_identity(identity)

    reference = ExternalIdentityReference.create(
        identity_id=identity.identity_id,
        provider="oidc",
        subject="subject-revoked",
    ).revoked()

    registry.register_external_reference(reference)

    result = registry.resolve_external(
        "oidc",
        "subject-revoked",
    )

    assert result.status is IdentityResolutionStatus.REVOKED
    assert result.resolved is False


def test_inactive_canonical_identity_does_not_resolve():
    identity = Identity.create(
        identity_type=IdentityType.HUMAN,
        display_name="Suspended Broker",
        handle="suspended.broker",
    ).with_status(IdentityStatus.SUSPENDED)

    registry = IdentityRegistry()
    registry.register_identity(identity)

    reference = ExternalIdentityReference.create(
        identity_id=identity.identity_id,
        provider="oidc",
        subject="subject-inactive",
    )

    registry.register_external_reference(reference)

    result = registry.resolve_external(
        "oidc",
        "subject-inactive",
    )

    assert result.status is IdentityResolutionStatus.REVOKED
    assert result.resolved is False


def test_external_identity_reference_requires_canonical_identity():
    registry = IdentityRegistry()

    reference = ExternalIdentityReference.create(
        identity_id=UUID(int=9999),
        provider="oidc",
        subject="orphan-subject",
    )

    with pytest.raises(ValueError):
        registry.register_external_reference(reference)


def test_external_reference_cannot_cross_rebind():
    first = Identity.create(
        identity_type=IdentityType.HUMAN,
        display_name="First",
        handle="external.first",
    )

    second = Identity.create(
        identity_type=IdentityType.HUMAN,
        display_name="Second",
        handle="external.second",
    )

    registry = IdentityRegistry()
    registry.register_identity(first)
    registry.register_identity(second)

    original = ExternalIdentityReference.create(
        identity_id=first.identity_id,
        provider="oidc",
        subject="cross-rebind",
    )

    registry.register_external_reference(original)

    replacement = ExternalIdentityReference(
        reference_id=original.reference_id,
        identity_id=second.identity_id,
        provider="oidc",
        subject="cross-rebind",
        status=ExternalIdentityStatus.ACTIVE,
        revision=2,
        linked_at=original.linked_at,
    )

    with pytest.raises(ValueError):
        registry.register_external_reference(replacement)


def test_forbidden_sensitive_fields_are_not_present():
    model_fields = identity_model_field_names()

    assert model_fields.isdisjoint(FORBIDDEN_IDENTITY_FIELDS)


def test_identity_model_field_names_match_expected_domain_models():
    assert set(identity_model_field_names()) == {
        field.name
        for model in (
            Identity,
            IdentityAccount,
            ExternalIdentityReference,
        )
        for field in fields(model)
    }


def test_lifecycle_runtime_maps_are_explicit():
    assert IDENTITY_STATUS_TRANSITIONS[IdentityStatus.DEACTIVATED] == frozenset()
    assert ACCOUNT_STATUS_TRANSITIONS[AccountStatus.DISABLED] == frozenset()
