import pytest

from .evidence_policy import (
    EvidencePolicy,
    authority_weight,
    validate_policy,
)
from .evidence_models import (
    EvidenceAuthority,
)


def test_authority_order():
    policy = EvidencePolicy()

    assert (
        authority_weight(
            EvidenceAuthority.CANONICAL_STATE,
            policy,
        )
        > authority_weight(
            EvidenceAuthority.GENERAL_EVIDENCE,
            policy,
        )
    )


def test_stale_selection_is_forbidden():
    policy = EvidencePolicy(
        allow_stale_selection=True
    )

    with pytest.raises(ValueError):
        validate_policy(policy)


def test_policy_is_safe_by_default():
    policy = EvidencePolicy()

    assert not policy.allow_stale_selection
    assert not policy.allow_non_canonical_override
