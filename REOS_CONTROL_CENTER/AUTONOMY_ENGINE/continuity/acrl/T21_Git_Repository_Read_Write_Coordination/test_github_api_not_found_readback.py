from __future__ import annotations

import pytest

from .github_api_error_recovery import (
    GitHubAPIOutcome,
    GitHubNotFoundReadbackEvidence,
    classify_github_api_failure,
    resolve_github_not_found,
)


OWNER = "test-owner"
REPOSITORY = "test-repository"
REF = "reos-development"
PATH = "REOS_CONTROL_CENTER/example.py"
PRINCIPAL = "verified-test-principal"


def make_evidence(**changes) -> GitHubNotFoundReadbackEvidence:
    values = {
        "original_status_code": 404,
        "original_authenticated_identity": PRINCIPAL,
        "original_identity_verified": True,
        "authenticated_identity": PRINCIPAL,
        "identity_verified": True,
        "owner": OWNER,
        "repository": REPOSITORY,
        "ref": REF,
        "target_path": PATH,
        "repository_status_code": 200,
        "ref_status_code": 200,
        "parent_tree_path": "REOS_CONTROL_CENTER",
        "parent_tree_status_code": 200,
        "parent_tree_entry_names": ("other.py", "README.md"),
    }
    values.update(changes)
    return GitHubNotFoundReadbackEvidence(**values)


def resolve(evidence):
    return resolve_github_not_found(
        evidence,
        expected_owner=OWNER,
        expected_repository=REPOSITORY,
        expected_ref=REF,
        expected_path=PATH,
    )


@pytest.mark.parametrize("operation_is_write", [False, True])
def test_a_single_404_is_ambiguous_and_always_requires_readback(
    operation_is_write: bool,
) -> None:
    result = classify_github_api_failure(
        404,
        operation_is_write=operation_is_write,
    )

    assert result.outcome is GitHubAPIOutcome.AMBIGUOUS_NOT_FOUND
    assert result.retryable is False
    assert result.max_retries == 0
    assert result.requires_readback is True
    assert "never silently switch branches" in result.action.lower()


def test_authorized_exact_readback_confirms_absence_but_not_write_authority():
    result = resolve(make_evidence())

    assert result.outcome is GitHubAPIOutcome.CONFIRMED_NOT_FOUND
    assert result.kind.value == "NOT_FOUND"
    assert result.retryable is False
    assert result.max_retries == 0
    assert result.requires_readback is False
    assert "does not authorize" in result.action.lower()
    assert "t18 authorization" in result.action.lower()


@pytest.mark.parametrize(
    "changes",
    [
        {"original_status_code": 403},
        {"original_identity_verified": False},
        {"identity_verified": False},
        {"original_authenticated_identity": "different-principal"},
        {"authenticated_identity": "different-principal"},
        {"owner": "wrong-owner"},
        {"repository": "wrong-repository"},
        {"ref": "main"},
        {"target_path": "REOS_CONTROL_CENTER/Example.py"},
        {"repository_status_code": 404},
        {"ref_status_code": 404},
        {"parent_tree_path": "wrong-parent"},
        {"parent_tree_status_code": 404},
        {"parent_tree_entry_names": ["other.py"]},
        {"parent_tree_entry_names": ("example.py", "other.py")},
    ],
)
def test_missing_or_mismatched_evidence_never_confirms_absence(changes):
    result = resolve(make_evidence(**changes))

    assert result.outcome is GitHubAPIOutcome.AMBIGUOUS_NOT_FOUND
    assert result.retryable is False
    assert result.requires_readback is True
    assert result.max_retries == 0


def test_path_traversal_is_never_confirmed_as_repository_absence():
    unsafe_path = "../outside.py"
    evidence = make_evidence(
        target_path=unsafe_path,
        parent_tree_path="..",
    )
    result = resolve_github_not_found(
        evidence,
        expected_owner=OWNER,
        expected_repository=REPOSITORY,
        expected_ref=REF,
        expected_path=unsafe_path,
    )

    assert result.outcome is GitHubAPIOutcome.AMBIGUOUS_NOT_FOUND
    assert result.requires_readback is True


def test_missing_evidence_keeps_404_ambiguous():
    result = resolve(None)

    assert result.outcome is GitHubAPIOutcome.AMBIGUOUS_NOT_FOUND
    assert result.retryable is False
    assert result.requires_readback is True
