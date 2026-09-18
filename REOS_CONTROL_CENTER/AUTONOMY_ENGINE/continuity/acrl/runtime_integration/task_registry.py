from __future__ import annotations

import re
from pathlib import Path

from .integration_models import ACRLTaskDescriptor


TASK_PATTERN = re.compile(r"^T(\d{2})_(.+)$")

# Explicit canonical directory overrides where historical compatibility
# directories share the same numeric prefix.
CANONICAL_DIRECTORY_OVERRIDES: dict[int, str] = {
    14: "T14_Repository_Intelligence_Context",
}

# Known preserved compatibility/support directories that must not be
# treated as the canonical runtime task.
COMPATIBILITY_DIRECTORIES: dict[int, frozenset[str]] = {
    14: frozenset(
        {
            "T14_Full_Regression",
        }
    ),
}


class ACRLTaskRegistry:
    """Discovers and validates the existing T01–T30 ACRL spine."""

    def __init__(self, acrl_root: Path) -> None:
        self.acrl_root = Path(acrl_root)

    def _resolve_directory(
        self,
        *,
        number: int,
        matches: list[Path],
    ) -> Path | None:
        prefix = f"T{number:02d}_"

        if not matches:
            return None

        canonical_name = CANONICAL_DIRECTORY_OVERRIDES.get(
            number
        )

        if canonical_name is not None:
            canonical = [
                path
                for path in matches
                if path.name == canonical_name
            ]

            if len(canonical) != 1:
                raise ValueError(
                    f"Canonical ACRL directory missing or ambiguous "
                    f"for {prefix}: {canonical_name!r}; "
                    f"found {[item.name for item in matches]}"
                )

            allowed_compatibility = (
                COMPATIBILITY_DIRECTORIES.get(
                    number,
                    frozenset(),
                )
            )

            unexpected = [
                path.name
                for path in matches
                if path.name != canonical_name
                and path.name not in allowed_compatibility
            ]

            if unexpected:
                raise ValueError(
                    f"Unexpected duplicate ACRL directories for "
                    f"{prefix}: {unexpected}"
                )

            return canonical[0]

        if len(matches) > 1:
            raise ValueError(
                f"Multiple ACRL directories found for {prefix}: "
                f"{[item.name for item in matches]}"
            )

        return matches[0]

    def discover(self) -> tuple[ACRLTaskDescriptor, ...]:
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
