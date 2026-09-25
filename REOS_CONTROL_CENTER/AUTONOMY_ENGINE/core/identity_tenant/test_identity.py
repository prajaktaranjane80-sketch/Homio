from uuid import UUID

import pytest

from AUTONOMY_ENGINE.core.identity_tenant.identity import (
    AccountStatus,
    Identity,
    IdentityAccount,
    IdentityStatus,
    IdentityType,
    PrivacyClass,
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
    [
        IdentityType.HUMAN,
        IdentityType.SERVICE,
        IdentityType.AI,
    ],
)
def test_supported_identity_types(identity_type):
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
    assert account.status is AccountStatus.ENABLED
    assert account.authentication_epoch == 1


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


def test_identity_and_account_timestamps_are_timezone_aware():
    identity = Identity.create(
        identity_type=IdentityType.HUMAN,
        display_name="Broker",
        handle="broker.two",
    )

    account = IdentityAccount.create(identity.identity_id)

    assert identity.created_at.tzinfo is not None
    assert identity.updated_at.tzinfo is not None
    assert account.created_at.tzinfo is not None
    assert account.updated_at.tzinfo is not None

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


def test_external_identity_reference_is_first_class():
    from uuid import uuid4
    from AUTONOMY_ENGINE.core.identity_tenant.identity import (
        ExternalIdentityReference,
        ExternalIdentityStatus,
    )

    identity_id = uuid4()

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
    from uuid import uuid4
    from AUTONOMY_ENGINE.core.identity_tenant.identity import ExternalIdentityReference

    ref = ExternalIdentityReference.create(
        identity_id=uuid4(),
        provider="Google",
        subject="CaseSensitiveSubject",
    )

    assert ref.subject == "CaseSensitiveSubject"


def test_external_identity_key_is_deterministic():
    from uuid import uuid4
    from AUTONOMY_ENGINE.core.identity_tenant.identity import ExternalIdentityReference

    ref = ExternalIdentityReference.create(
        identity_id=uuid4(),
        provider="Google",
        subject="Subject-001",
    )

    assert ref.external_key() == ("google", "Subject-001")


def test_external_identity_revocation_is_immutable():
    from uuid import uuid4
    from AUTONOMY_ENGINE.core.identity_tenant.identity import (
        ExternalIdentityReference,
        ExternalIdentityStatus,
    )

    ref = ExternalIdentityReference.create(
        identity_id=uuid4(),
        provider="oidc",
        subject="subject-001",
    )

    revoked = ref.revoked()

    assert ref.status is ExternalIdentityStatus.ACTIVE
    assert revoked.status is ExternalIdentityStatus.REVOKED
    assert revoked.revision == ref.revision + 1


def test_external_identity_invalid_provider_is_rejected():
    from uuid import uuid4
    from AUTONOMY_ENGINE.core.identity_tenant.identity import ExternalIdentityReference

    for provider in ["", "bad provider", "bad\nprovider"]:
        try:
            ExternalIdentityReference.create(
                identity_id=uuid4(),
                provider=provider,
                subject="subject",
            )
        except (ValueError, TypeError):
            pass
        else:
            raise AssertionError(f"invalid provider accepted: {provider!r}")


def test_external_identity_timestamps_are_timezone_aware():
    from uuid import uuid4
    from AUTONOMY_ENGINE.core.identity_tenant.identity import ExternalIdentityReference

    ref = ExternalIdentityReference.create(
        identity_id=uuid4(),
        provider="oidc",
        subject="subject-001",
    )

    assert ref.linked_at.tzinfo is not None
    assert ref.linked_at.utcoffset() is not None

def test_external_identity_resolution_is_deterministic():
    from AUTONOMY_ENGINE.core.identity_tenant.identity import (
        ExternalIdentityReference,
        IdentityRegistry,
        IdentityResolutionStatus,
    )

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
    from AUTONOMY_ENGINE.core.identity_tenant.identity import (
        IdentityRegistry,
        IdentityResolutionStatus,
    )

    result = IdentityRegistry().resolve_external(
        "google",
        "unknown-subject",
    )

    assert result.status is IdentityResolutionStatus.NOT_FOUND
    assert result.resolved is False


def test_external_identity_duplicate_key_cannot_rebind():
    from AUTONOMY_ENGINE.core.identity_tenant.identity import (
        ExternalIdentityReference,
        IdentityRegistry,
    )

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

    try:
        registry.register_external_reference(second_reference)
    except ValueError:
        pass
    else:
        raise AssertionError(
            "duplicate external identity key was allowed to rebind"
        )


def test_external_identity_revoked_reference_does_not_resolve():
    from AUTONOMY_ENGINE.core.identity_tenant.identity import (
        ExternalIdentityReference,
        IdentityRegistry,
        IdentityResolutionStatus,
    )

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
    from AUTONOMY_ENGINE.core.identity_tenant.identity import (
        ExternalIdentityReference,
        IdentityRegistry,
        IdentityResolutionStatus,
    )

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
    from uuid import uuid4
    from AUTONOMY_ENGINE.core.identity_tenant.identity import (
        ExternalIdentityReference,
        IdentityRegistry,
    )

    registry = IdentityRegistry()

    reference = ExternalIdentityReference.create(
        identity_id=uuid4(),
        provider="oidc",
        subject="orphan-subject",
    )

    try:
        registry.register_external_reference(reference)
    except ValueError:
        pass
    else:
        raise AssertionError(
            "orphan external identity reference was accepted"
        )

