from __future__ import annotations

from .git_models import GitPolicy
from .git_repository import GitRepository


def create_commit(
    repository: GitRepository,
    commit_message: str,
    policy: GitPolicy,
) -> str:
    if not policy.allow_commit:
        raise ValueError(
            "Git commit is disabled by policy."
        )

    message = commit_message.strip()

    if not message:
        raise ValueError(
            "Commit message is required."
        )

    staged = repository.run(
        "diff",
        "--cached",
        "--name-only",
    ).stdout.strip()

    if not staged:
        raise ValueError(
            "Cannot create empty commit."
        )

    repository.run(
        "commit",
        "-m",
        message,
    )

    return repository.head()


def verify_commit(
    repository: GitRepository,
    commit_sha: str,
) -> bool:
    return (
        repository.commit_exists(
            commit_sha
        )
        and repository.head()
        == commit_sha
    )
