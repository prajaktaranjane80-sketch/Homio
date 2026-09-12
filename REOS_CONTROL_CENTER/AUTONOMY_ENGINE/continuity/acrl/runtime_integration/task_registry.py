from __future__ import annotations

import re
from pathlib import Path

from .integration_models import ACRLTaskDescriptor


TASK_PATTERN = re.compile(r"^T(\d{2})_(.+)$")


class ACRLTaskRegistry:
    """Discovers and validates the existing T01–T30 ACRL spine."""

    def __init__(self, acrl_root: Path) -> None:
        self.acrl_root = Path(acrl_root)

    def discover(self) -> tuple[ACRLTaskDescriptor, ...]:
        descriptors: list[ACRLTaskDescriptor] = []

        for number in range(1, 31):
            prefix = f"T{number:02d}_"
            matches = sorted(
                path
                for path in self.acrl_root.iterdir()
                if path.is_dir() and path.name.startswith(prefix)
            )

            if len(matches) > 1:
                raise ValueError(
                    f"Multiple ACRL directories found for {prefix}: "
                    f"{[item.name for item in matches]}"
                )

            if not matches:
                descriptors.append(
                    ACRLTaskDescriptor(
                        task_id=f"T{number:02d}",
                        directory_name="",
                        path=str(self.acrl_root / f"{prefix}<MISSING>"),
                        exists=False,
                        has_init=False,
                        contract_files=(),
                        test_files=(),
                    )
                )
                continue

            directory = matches[0]

            if not TASK_PATTERN.match(directory.name):
                raise ValueError(
                    f"Invalid ACRL directory naming: {directory.name}"
                )

            contract_files = tuple(
                sorted(
                    file.name
                    for file in directory.rglob("*")
                    if file.is_file()
                    and (
                        file.name.endswith(".contract.json")
                        or "contract" in file.name.lower()
                    )
                )
            )

            test_files = tuple(
                sorted(
                    file.name
                    for file in directory.rglob("test_*.py")
                    if file.is_file()
                )
            )

            descriptors.append(
                ACRLTaskDescriptor(
                    task_id=f"T{number:02d}",
                    directory_name=directory.name,
                    path=str(directory),
                    exists=True,
                    has_init=(directory / "__init__.py").is_file(),
                    contract_files=contract_files,
                    test_files=test_files,
                )
            )

        return tuple(descriptors)

    def validate(self) -> tuple[ACRLTaskDescriptor, ...]:
        tasks = self.discover()

        missing = [task.task_id for task in tasks if not task.exists]
        if missing:
            raise ValueError(
                f"ACRL integration cannot start; missing tasks: {missing}"
            )

        unhealthy = [
            task.task_id
            for task in tasks
            if not task.healthy
        ]
        if unhealthy:
            raise ValueError(
                f"ACRL integration cannot start; unhealthy tasks: {unhealthy}"
            )

        return tasks
