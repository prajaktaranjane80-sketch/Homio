from __future__ import annotations

from .git_models import GitPolicy
from .git_repository import GitRepository


def push_branch(
    repository: GitRepository,
    *,
    remote: str,
    branch: str,
    policy: GitPolicy,
) -> None:
    if not policy.allow_push:
        raise ValueError(
            "Git push is disabled by policy."
        )

    if policy.allow_force_push:
        raise ValueError(
            "Force push is forbidden in T21 V1."
        )

    if "--force" in {
        remote,
        branch,
    }:
        raise ValueError(
            "Force push arguments are forbidden."
        )

    if remote not in repository.remote_names():
        raise ValueError(
            f"Unknown Git remote: {remote}"
        )

    repository.run(
        "push",
        remote,
        f"HEAD:{branch}",
    )


def verify_remote_branch(
    repository: GitRepository,
    *,
    remote: str,
    branch: str,
) -> str:
    output = repository.run(
        "ls-remote",
        remote,
        f"refs/heads/{branch}",
    ).stdout.strip()

    if not output:
        raise ValueError(
            "Remote branch could not be verified."
        )

    return output.split(
        "\t",
        1,
    )[0]
