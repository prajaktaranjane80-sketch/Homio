from __future__ import annotations

from pathlib import Path
from typing import Iterable

from ..T16_Repository_Intelligence_File_Discovery.repository_intelligence import (
    RepositoryPathGuard,
    RepositoryPathSecurityError,
    normalize_repository_path,
)

from .impact_errors import (
    ChangeImpactSecurityError,
)


class T17PathSecurity:
    """T17 path boundary backed by the T16 repository guard."""

    def __init__(
        self,
        repository_root: Path | str,
    ) -> None:
        self.repository_root = Path(
            repository_root
        ).resolve()

        self._guard = RepositoryPathGuard(
            self.repository_root
        )

    def normalize_changed_paths(
        self,
        paths: Iterable[str],
    ) -> tuple[str, ...]:
        values: list[str] = []

        for raw in paths:
            if not isinstance(raw, str) or not raw.strip():
                raise ValueError(
                    "Changed paths must be non-empty strings."
                )

            try:
                resolved = self._guard.resolve(
                    Path(raw)
                )

                relative = resolved.relative_to(
                    self.repository_root
                )

            except RepositoryPathSecurityError as exc:
                raise ChangeImpactSecurityError(
                    "Changed path escapes repository boundary."
                ) from exc

            except (OSError, ValueError) as exc:
                raise ChangeImpactSecurityError(
                    "Changed path cannot be resolved safely."
                ) from exc

            normalized = normalize_repository_path(
                relative.as_posix()
            )

            if (
                normalized == ".."
                or normalized.startswith("../")
                or "/../" in normalized
            ):
                raise ChangeImpactSecurityError(
                    "Changed path escapes repository boundary."
                )

            values.append(normalized)

        return tuple(
            sorted(set(values))
        )


def validate_read_only(report) -> None:
    if report.state_mutated or report.execution_authorized:
        raise ChangeImpactSecurityError(
            "T17 must remain read-only."
        )


__all__ = [
    "ChangeImpactSecurityError",
    "T17PathSecurity",
    "validate_read_only",
]
