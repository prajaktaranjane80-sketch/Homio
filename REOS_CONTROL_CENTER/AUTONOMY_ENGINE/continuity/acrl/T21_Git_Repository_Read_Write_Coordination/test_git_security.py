from __future__ import annotations

import pytest

from .git_models import GitPolicy, GitReason
from .git_policy import (
    is_protected_path,
    validate_policy,
)
from .git_scope import is_safe_repository_path
from .git_push import classify_git_push_error


def test_safe_path():
    assert is_safe_repository_path("src/app.py")


def test_absolute_path_rejected():
    assert not is_safe_repository_path("/etc/passwd")


def test_parent_path_rejected():
    assert not is_safe_repository_path("../secret.py")


@pytest.mark.parametrize(
    "path",
    [
        "C:/secret.py",
        r"C:\secret.py",
        "//server/share/file.py",
        "src//app.py",
        "src/./app.py",
        "src/../secret.py",
        "src/app.py/",
        " src/app.py",
        "src/app.py ",
        "src/\x00app.py",
        "src/\napp.py",
        "",
    ],
)
def test_unsafe_repository_paths_are_rejected(path: str):
    assert not is_safe_repository_path(path)


@pytest.mark.parametrize(
    "path",
    [
        ".reos_t21_transaction.lock",
        "data/state.json",
        "REOS_CONTROL_CENTER/data/state.json",
        "architecture/system.json",
        "REOS_CONTROL_CENTER/architecture/system.json",
        "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/continuity/acrl/"
        "T18_Safe_Execution_Authorization_Guard/authorization_models.py",
    ],
)
def test_protected_paths_are_rejected(path: str):
    assert is_protected_path(path, GitPolicy())


def test_force_push_policy_rejected():
    policy = GitPolicy(
        allow_force_push=True,
    )

    with pytest.raises(ValueError):
        validate_policy(policy)

@pytest.mark.parametrize(
    ("message", "expected"),
    [
        ("remote returned HTTP 401", GitReason.AUTHENTICATION_FAILED),
        ("remote returned HTTP 403", GitReason.AUTHORIZATION_DENIED),
        ("repository not found; HTTP 404", GitReason.REMOTE_NOT_FOUND),
        ("proxy authentication required; HTTP 407", GitReason.PROXY_AUTH_REQUIRED),
        ("HTTP 429: rate limit exceeded", GitReason.RATE_LIMITED),
        ("connection timed out", GitReason.NETWORK_FAILURE),
        ("SSL certificate verify failed", GitReason.TLS_FAILURE),
        ("non-fast-forward update rejected", GitReason.NON_FAST_FORWARD),
    ],
)
def test_remote_failure_classification_is_specific_and_safe(
    message: str,
    expected: GitReason,
):
    reason, explanation = classify_git_push_error(RuntimeError(message))
    assert reason is expected
    assert message not in explanation


def test_remote_error_does_not_echo_credentials():
    message = (
        "fatal: unable to access "
        "'https://x-access-token:ghp_secret-value-12345678901234567890@"
        "github.com/example/repo': HTTP 403 permission denied"
    )

    reason, explanation = classify_git_push_error(RuntimeError(message))

    assert reason is GitReason.AUTHORIZATION_DENIED
    assert "ghp_secret-value" not in explanation
    assert "x-access-token" not in explanation
