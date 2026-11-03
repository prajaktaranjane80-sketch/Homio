from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Final


OWNER: Final = "prajaktaranjane80-sketch"
REPOSITORY: Final = "prajaktaranjane80-sketch/Homio"

OWNER_ID: Final = "320960487"
REPOSITORY_ID: Final = "1346051793"

BRANCH: Final = "reos-development"
BRANCH_REF: Final = f"refs/heads/{BRANCH}"

OIDC_ISSUER: Final = "https://token.actions.githubusercontent.com"

EXPECTED_OIDC_SUBJECT: Final = (
    f"repo:{OWNER}@{OWNER_ID}/Homio@{REPOSITORY_ID}:"
    f"ref:{BRANCH_REF}"
)

EXPECTED_GITHUB_ACTIONS_CLAIMS: Final = (
    ("iss", OIDC_ISSUER),
    ("sub", EXPECTED_OIDC_SUBJECT),
    ("repository", REPOSITORY),
    ("repository_owner", OWNER),
    ("repository_id", REPOSITORY_ID),
    ("repository_owner_id", OWNER_ID),
    ("actor", OWNER),
    ("actor_id", OWNER_ID),
    ("ref", BRANCH_REF),
    ("ref_type", "branch"),
    ("event_name", "push"),
)


class GitHubActionsIdentityError(ValueError):
    """Raised when a GitHub Actions identity is outside HOMIO's trust scope."""


def validate_github_actions_identity_claims(
    claims: Mapping[str, object],
    *,
    expected_sha: str,
) -> None:
    """
    Validate the exact immutable GitHub Actions identity for HOMIO.

    This is a pure validation function. It performs no network access,
    token issuance, state mutation, or authorization of its own.

    Signature, issuer, audience and expiry validation remain the
    responsibility of the existing HOMIO OIDCVerifier.
    """
    if not isinstance(claims, Mapping):
        raise GitHubActionsIdentityError(
            "GitHub Actions identity claims are not a mapping."
        )

    if (
        not isinstance(expected_sha, str)
        or re.fullmatch(r"[0-9a-f]{40}", expected_sha) is None
    ):
        raise GitHubActionsIdentityError(
            "Expected source commit SHA is invalid."
        )

    expected_claims = (
        *EXPECTED_GITHUB_ACTIONS_CLAIMS,
        ("sha", expected_sha),
    )

    for claim_name, expected_value in expected_claims:
        actual_value = claims.get(claim_name)

        if (
            not isinstance(actual_value, str)
            or actual_value != expected_value
        ):
            raise GitHubActionsIdentityError(
                "GitHub Actions identity claim "
                f"{claim_name!r} does not match the pinned HOMIO identity."
            )
