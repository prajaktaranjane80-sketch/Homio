from __future__ import annotations

import pytest

from .git_models import (
    GitPolicy,
)
from .git_policy import (
    validate_policy,
)
from .git_scope import (
    is_safe_repository_path,
)


def test_safe_path():
    assert is_safe_repository_path(
        "src/app.py"
    )


def test_absolute_path_rejected():
    assert not is_safe_repository_path(
        "/etc/passwd"
    )


def test_parent_path_rejected():
    assert not is_safe_repository_path(
        "../secret.py"
    )


def test_force_push_policy_rejected():
    policy = GitPolicy(
        allow_force_push=True
    )

    with pytest.raises(ValueError):
        validate_policy(policy)
