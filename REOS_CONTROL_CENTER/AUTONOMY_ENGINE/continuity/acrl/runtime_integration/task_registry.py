from __future__ import annotations

import re
from pathlib import Path

from .integration_models import ACRLTaskDescriptor


TASK_PATTERN = re.compile(r"^T(\d{2})_(.+)$")


# Canonical runtime directory for a task when historical/compatibility
# directories share the same numeric task prefix.
CANONICAL_DIRECTORY_OVERRIDES: dict[int, str] = {
    14: "T14_Repository_Intelligence_Context",
}


# Existing compatibility/support directories that must remain in the
# repository but must not be selected as the canonical runtime task.
COMPATIBILITY_DIRECTORIES: dict[int, frozenset[str]] = {
    14: frozenset(
        {
            "T14_Full_Regression",
        }
    ),
}


class ACRLTaskRegistry:
    """Discovers and validates the existing T01-T30 ACRL spine."""

    def __init__(self, acrl_root: Path) -> None:
        self.acrl_root = Path(acrl_root)

    def _resolve_directory(
        self,
        *,
        number: int,
        matches: list[Path],
    ) -> Path | None:
        """Resolve one canonical runtime directory for a task."""

        prefix = f"T{number:02d}_"

        if not matches:
            return None

        canonical_name = CANONICAL_DIRECTORY_OVERRIDES.get(
            number
        )

        if canonical_name is not None:
            canonical_matches = [
                path
                for path in matches
                if path.name == canonical_name
            ]

            unexpected_duplicates = [
                path.name
                for path in matches
                if path.name != canonical_name
                and path.name
                not in COMPATIBILITY_DIRECTORIES.get(
                    number,
                    frozenset(),
                )
            ]

            if unexpected_duplicates:
                raise ValueError(
                    f"Unexpected duplicate ACRL directories "
                    f"for {prefix}: "
                    f"{unexpected_duplicates}"
                )

            if len(canonical_matches) != 1:
                raise ValueError(
                    f"Canonical ACRL directory missing or "
                    f"ambiguous for {prefix}: "
                    f"{canonical_name}; "
                    f"found {[item.name for item in matches]}"
                )

            return canonical_matches[0]

        # For all normal T01-T30 tasks, multiple matching
        # directories remain a fail-closed condition.
        if len(matches) > 1:
            raise ValueError(
                f"Multiple ACRL directories found for {prefix}: "
                f"{[item.name for item in matches]}"
            )

        return matches[0]

    def discover(
        self,
    ) -> tuple[ACRLTaskDescriptor, ...]:
        """Discover the canonical T01-T30 runtime spine."""

        descriptors: list[ACRLTaskDescriptor] = []

        for number in range(1, 31):
            prefix = f"T{number:02d}_"

            matches = sorted(
                (
                    path
                    for path in self.acrl_root.iterdir()
                    if path.is_dir()
                    and path.name.startswith(prefix)
                ),
                key=lambda path: path.name.lower(),
            )

            directory = self._resolve_directory(
                number=number,
                matches=matches,
            )

            if directory is None:
                descriptors.append(
                    ACRLTaskDescriptor(
                        task_id=f"T{number:02d}",
                        directory_name="",
                        path=str(
                            self.acrl_root
                            / f"{prefix}<MISSING>"
                        ),
                        exists=False,
                        has_init=False,
                        contract_files=(),
                        test_files=(),
                    )
                )
                continue

            if not TASK_PATTERN.match(
                directory.name
            ):
                raise ValueError(
                    f"Invalid ACRL directory naming: "
                    f"{directory.name}"
                )

            contract_files = tuple(
                sorted(
                    file.name
                    for file in directory.rglob("*")
                    if file.is_file()
                    and (
                        file.name.endswith(
                            ".contract.json"
                        )
                        or "contract" in file.name.lower()
                    )
                )
            )

            test_files = tuple(
                sorted(
                    file.name
                    for file in directory.rglob(
                        "test_*.py"
                    )
                    if file.is_file()
                )
            )

            descriptors.append(
                ACRLTaskDescriptor(
                    task_id=f"T{number:02d}",
                    directory_name=directory.name,
                    path=str(directory),
                    exists=True,
                    has_init=(
                        directory / "__init__.py"
                    ).is_file(),
                    contract_files=contract_files,
                    test_files=test_files,
                )
            )

        return tuple(descriptors)

    def validate(
        self,
    ) -> tuple[ACRLTaskDescriptor, ...]:
        """Validate that the canonical T01-T30 spine is healthy."""

        tasks = self.discover()

        missing = [
            task.task_id
            for task in tasks
            if not task.exists
        ]

        if missing:
            raise ValueError(
                "ACRL integration cannot start; "
                f"missing tasks: {missing}"
            )

        unhealthy = [
            task.task_id
            for task in tasks
            if not task.healthy
        ]

        if unhealthy:
            raise ValueError(
                "ACRL integration cannot start; "
                f"unhealthy tasks: {unhealthy}"
            )

        return tasks
