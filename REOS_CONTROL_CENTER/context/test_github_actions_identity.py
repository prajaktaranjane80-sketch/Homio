from __future__ import annotations

import copy

import pytest

from .github_actions_identity import (
    EXPECTED_GITHUB_ACTIONS_CLAIMS,
    EXPECTED_OIDC_SUBJECT,
    GitHubActionsIdentityError,
    validate_github_actions_identity_claims,
)


VALID_SHA = "a" * 40


def valid_claims() -> dict[str, str]:
    claims = dict(EXPECTED_GITHUB_ACTIONS_CLAIMS)
    claims["sha"] = VALID_SHA
    return claims


def test_expected_subject_uses_immutable_repository_identity():
    assert EXPECTED_OIDC_SUBJECT == (
        "repo:prajaktaranjane80-sketch@320960487/"
        "Homio@1346051793:"
        "ref:refs/heads/reos-development"
    )


def test_valid_owner_push_identity_is_accepted():
    validate_github_actions_identity_claims(
        valid_claims(),
        expected_sha=VALID_SHA,
    )


@pytest.mark.parametrize(
    ("claim_name", "wrong_value"),
    [
        ("iss", "https://untrusted.example"),
        (
            "sub",
            "repo:prajaktaranjane80-sketch/Homio:"
            "ref:refs/heads/reos-development",
        ),
        ("repository", "another-owner/Homio"),
        ("repository_owner", "another-owner"),
        ("repository_id", "999999999"),
        ("repository_owner_id", "999999999"),
        ("actor", "another-user"),
        ("actor_id", "999999999"),
        ("ref", "refs/heads/main"),
        ("ref_type", "tag"),
        ("event_name", "pull_request"),
        ("sha", "b" * 40),
    ],
)
def test_wrong_identity_claim_is_rejected(
    claim_name: str,
    wrong_value: str,
):
    claims = valid_claims()
    claims[claim_name] = wrong_value

    with pytest.raises(
        GitHubActionsIdentityError,
        match=claim_name,
    ):
        validate_github_actions_identity_claims(
            claims,
            expected_sha=VALID_SHA,
        )


@pytest.mark.parametrize(
    "claim_name",
    [name for name, _ in EXPECTED_GITHUB_ACTIONS_CLAIMS],
)
def test_missing_identity_claim_is_rejected(claim_name: str):
    claims = valid_claims()
    claims.pop(claim_name)

    with pytest.raises(
        GitHubActionsIdentityError,
        match=claim_name,
    ):
        validate_github_actions_identity_claims(
            claims,
            expected_sha=VALID_SHA,
        )


def test_invalid_expected_sha_is_rejected():
    with pytest.raises(GitHubActionsIdentityError):
        validate_github_actions_identity_claims(
            valid_claims(),
            expected_sha="not-a-commit-sha",
        )


def test_identity_validation_does_not_mutate_claims():
    claims = valid_claims()
    before = copy.deepcopy(claims)

    validate_github_actions_identity_claims(
        claims,
        expected_sha=VALID_SHA,
    )

    assert claims == before


def test_legacy_subject_is_never_accepted():
    claims = valid_claims()
    claims["sub"] = (
        "repo:prajaktaranjane80-sketch/Homio:"
        "ref:refs/heads/reos-development"
    )

    with pytest.raises(
        GitHubActionsIdentityError,
        match="sub",
    ):
        validate_github_actions_identity_claims(
            claims,
            expected_sha=VALID_SHA,
        )
