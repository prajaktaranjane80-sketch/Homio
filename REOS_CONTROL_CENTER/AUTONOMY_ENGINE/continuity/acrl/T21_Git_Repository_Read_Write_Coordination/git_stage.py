from __future__ import annotations

from .git_models import GitPolicy
from .git_policy import normalize_path
from .git_repository import GitRepository


def stage_exact_paths(
    repository: GitRepository,
    paths: tuple[str, ...],
    policy: GitPolicy,
) -> tuple[str, ...]:
    if not policy.allow_staging:
        raise ValueError(
            "Git staging is disabled by policy."
        )

    normalized = tuple(
        sorted(
            {
                normalize_path(path)
                for path in paths
            }
        )
    )

    if not normalized:
        raise ValueError(
            "No paths supplied for staging."
        )

    repository.run(
        "add",
        "--",
        *normalized,
    )

    return normalized


def staged_paths(
    repository: GitRepository,
) -> tuple[str, ...]:
    output = repository.run(
        "diff",
        "--cached",
        "--name-only",
        "--no-renames",
    ).stdout

    return tuple(
        sorted(
            normalize_path(line)
            for line in output.splitlines()
            if line.strip()
        )
    )
