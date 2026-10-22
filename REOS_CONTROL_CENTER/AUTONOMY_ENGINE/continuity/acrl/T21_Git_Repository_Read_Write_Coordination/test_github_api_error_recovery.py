from __future__ import annotations

import pytest

from .git_models import GitReason
from .git_push import classify_git_push_error
from .git_registry import GitRegistry
from .github_api_error_recovery import (
    GitHubAPIErrorKind,
    classify_github_api_failure,
)


def test_403_rate_limit_is_distinct_from_permission_failure() -> None:
    result = classify_github_api_failure(
        403,
        headers={
            "X-RateLimit-Remaining": "0",
            "X-RateLimit-Reset": "1700000120",
        },
        message="API rate limit exceeded",
        now_epoch=1700000000,
    )

    assert result.kind is GitHubAPIErrorKind.RATE_LIMITED
    assert result.retryable is True
    assert result.retry_after_seconds == 120
    assert result.max_retries == 1


def test_403_permission_failure_is_not_retried() -> None:
    result = classify_github_api_failure(
        403,
        message="Resource access is forbidden",
    )

    assert result.kind is GitHubAPIErrorKind.PERMISSION_DENIED
    assert result.retryable is False
    assert result.max_retries == 0


def test_404_requires_exact_path_and_ref_check() -> None:
    result = classify_github_api_failure(404)

    assert result.kind is GitHubAPIErrorKind.NOT_FOUND
    assert result.retryable is False
    assert "silently switch branches" in result.action


@pytest.mark.parametrize(
    ("status_code", "expected_kind"),
    (
        (409, GitHubAPIErrorKind.CONFLICT),
        (422, GitHubAPIErrorKind.VALIDATION_OR_STALE_SHA),
    ),
)
def test_stale_or_conflicting_write_requires_readback(
    status_code: int,
    expected_kind: GitHubAPIErrorKind,
) -> None:
    result = classify_github_api_failure(
        status_code,
        operation_is_write=True,
    )

    assert result.kind is expected_kind
    assert result.requires_readback is True
    assert result.retryable is False
    assert result.max_retries == 0


def test_write_timeout_is_ambiguous_and_not_auto_retried() -> None:
    result = classify_github_api_failure(
        None,
        operation_is_write=True,
        transport_error="request timed out",
    )

    assert result.kind is GitHubAPIErrorKind.TIMEOUT
    assert result.requires_readback is True
    assert result.retryable is False


def test_safe_read_timeout_has_a_bounded_retry() -> None:
    result = classify_github_api_failure(
        None,
        operation_is_write=False,
        transport_error="timeout",
    )

    assert result.kind is GitHubAPIErrorKind.TIMEOUT
    assert result.retryable is True
    assert result.max_retries == 1


def test_write_server_error_requires_readback() -> None:
    result = classify_github_api_failure(
        503,
        operation_is_write=True,
    )

    assert result.kind is GitHubAPIErrorKind.SERVER_ERROR
    assert result.requires_readback is True
    assert result.retryable is False


def test_tls_failure_is_never_retried_or_bypassed() -> None:
    result = classify_github_api_failure(
        None,
        transport_error="TLS certificate validation failure",
    )

    assert result.kind is GitHubAPIErrorKind.TLS_FAILURE
    assert result.retryable is False
    assert "Do not disable certificate verification" in result.action


def test_unknown_failure_fails_closed() -> None:
    result = classify_github_api_failure(
        418,
        operation_is_write=True,
    )

    assert result.kind is GitHubAPIErrorKind.UNKNOWN
    assert result.retryable is False
    assert result.requires_readback is True


def test_invalid_status_code_is_rejected() -> None:
    with pytest.raises(ValueError):
        classify_github_api_failure(99)


def test_registry_declares_api_error_recovery_component() -> None:
    registry = GitRegistry()
    registry.validate()

    assert registry.api_error_recovery == "github_api_error_recovery"


def test_existing_push_adapter_uses_rate_limit_classification() -> None:
    reason, explanation = classify_git_push_error(
        RuntimeError(
            "fatal: HTTP 403: API rate limit exceeded"
        )
    )

    assert reason is GitReason.RATE_LIMITED
    assert "bounded retry" in explanation.lower()


def test_existing_push_adapter_keeps_permission_denial_distinct() -> None:
    reason, explanation = classify_git_push_error(
        RuntimeError("fatal: HTTP 403 permission denied")
    )

    assert reason is GitReason.AUTHORIZATION_DENIED
    assert "permission" in explanation.lower()


def test_existing_push_adapter_maps_conflict_to_reconciliation() -> None:
    reason, explanation = classify_git_push_error(
        RuntimeError("remote: HTTP 409 stale reference")
    )

    assert reason is GitReason.NON_FAST_FORWARD
    assert "reconcile" in explanation.lower() or "reread" in explanation.lower()
