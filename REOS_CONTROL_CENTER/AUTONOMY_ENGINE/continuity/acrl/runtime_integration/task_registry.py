from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .integration_models import ACRLTaskDescriptor


TASK_PATTERN = re.compile(r"^T(\d{2})_(.+)$")
LAYER_ID_PATTERN = re.compile(r"\bT\d{2}\b")

CONTRACT_IDENTITY_KEYS = (
    "contract_id",
    "layer",
    "contract_version",
    "schema_version",
    "system_id",
    "system_name",
    "name",
)

FORBIDDEN_AUTHORITY_FLAGS = frozenset(
    {
        "execution_authorized",
        "write_authorized",
        "approval_authorized",
        "may_modify_state_json",
        "may_modify_architecture",
        "may_advance_gate",
        "may_approve_gate",
        "may_freeze_gate",
        "may_execute_controller_transition",
    }
)

CANONICAL_DIRECTORY_OVERRIDES: dict[int, str] = {
    14: "T14_Repository_Intelligence_Context",
}

COMPATIBILITY_DIRECTORIES: dict[int, frozenset[str]] = {
    14: frozenset({"T14_Full_Regression"}),
}


def _reject_nonstandard_json_constant(value: str) -> None:
    raise ValueError(
        f"Non-standard JSON constant is not allowed: {value}"
    )


def _walk_mapping(value: Any):
    """Yield nested mapping entries without executing contract code."""
    if isinstance(value, dict):
        for key, item in value.items():
            yield str(key), item
            yield from _walk_mapping(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk_mapping(item)


def _validate_json_contract(
    *,
    contract_path: Path,
    expected_task_id: str,
) -> None:
    """Validate machine-readable contract shape and authority boundaries."""
    try:
        # utf-8-sig accepts ordinary UTF-8 and removes an optional UTF-8 BOM.
        # It does not relax JSON syntax or the authority checks below.
        raw_text = contract_path.read_text(encoding="utf-8-sig")
        document = json.loads(
            raw_text,
            parse_constant=_reject_nonstandard_json_constant,
        )
    except (
        OSError,
        UnicodeError,
        json.JSONDecodeError,
        ValueError,
    ) as exc:
        raise ValueError(
            f"Invalid JSON contract for {expected_task_id}: "
            f"{contract_path.name}: {exc}"
        ) from exc

    if not isinstance(document, dict):
        raise ValueError(
            f"Invalid JSON contract for {expected_task_id}: "
            f"{contract_path.name} must contain a JSON object"
        )

    if not any(
        key in document
        for key in CONTRACT_IDENTITY_KEYS
    ):
        raise ValueError(
            f"Invalid JSON contract for {expected_task_id}: "
            f"{contract_path.name} has no recognized identity metadata"
        )

    declared_layer = document.get("layer")
    if declared_layer is not None:
        if not isinstance(declared_layer, str):
            raise ValueError(
                f"Invalid layer value in contract: {contract_path.name}"
            )

        if declared_layer.strip().upper() != expected_task_id:
            raise ValueError(
                f"Contract layer mismatch for {expected_task_id}: "
                f"{contract_path.name} declares {declared_layer!r}"
            )

    contract_id = document.get("contract_id")
    if isinstance(contract_id, str):
        declared_ids = {
            match.upper()
            for match in LAYER_ID_PATTERN.findall(contract_id)
        }

        if declared_ids and declared_ids != {expected_task_id}:
            raise ValueError(
                f"Contract identity mismatch for {expected_task_id}: "
                f"{contract_path.name} declares {sorted(declared_ids)}"
            )

    # A contract describes boundaries; it cannot grant itself privileges.
    for key, value in _walk_mapping(document):
        if key in FORBIDDEN_AUTHORITY_FLAGS and value is True:
            raise ValueError(
                f"Unsafe authority flag {key}=true in "
                f"{expected_task_id}/{contract_path.name}"
            )


class ACRLTaskRegistry:
    """Discovers and validates the canonical T01-T30 ACRL runtime spine."""

    def __init__(self, acrl_root: Path) -> None:
        self.acrl_root = Path(acrl_root)

    def _resolve_directory(
        self,
        *,
        number: int,
        matches: list[Path],
    ) -> Path | None:
        """Resolve exactly one canonical directory for a numbered layer."""
        prefix = f"T{number:02d}_"

        if not matches:
            return None

        canonical_name = CANONICAL_DIRECTORY_OVERRIDES.get(number)

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
                    f"Unexpected duplicate ACRL directories for {prefix}: "
                    f"{unexpected_duplicates}"
                )

            if len(canonical_matches) != 1:
                raise ValueError(
                    f"Canonical ACRL directory missing or ambiguous for "
                    f"{prefix}: {canonical_name}; found "
                    f"{[item.name for item in matches]}"
                )

            return canonical_matches[0]

        if len(matches) > 1:
            raise ValueError(
                f"Multiple ACRL directories found for {prefix}: "
                f"{[item.name for item in matches]}"
            )

        return matches[0]

    def discover(self) -> tuple[ACRLTaskDescriptor, ...]:
        """Discover layers without treating discovery as proof of health."""
        if not self.acrl_root.is_dir():
            raise ValueError(
                f"Canonical ACRL root is missing: {self.acrl_root}"
            )

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
                            self.acrl_root / f"{prefix}<MISSING>"
                        ),
                        exists=False,
                        has_init=False,
                        contract_files=(),
                        test_files=(),
                    )
                )
                continue

            if not TASK_PATTERN.match(directory.name):
                raise ValueError(
                    f"Invalid ACRL directory naming: {directory.name}"
                )

            files = tuple(
                path
                for path in directory.rglob("*")
                if path.is_file()
            )

            contract_files = tuple(
                sorted(
                    path.relative_to(directory).as_posix()
                    for path in files
                    if "contract" in path.name.lower()
                )
            )

            test_files = tuple(
                sorted(
                    path.relative_to(directory).as_posix()
                    for path in files
                    if path.name.startswith("test_")
                    and path.suffix.lower() == ".py"
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

    @staticmethod
    def _validate_contracts(
        descriptor: ACRLTaskDescriptor,
    ) -> None:
        directory = Path(descriptor.path)

        json_contracts = sorted(
            path
            for path in directory.rglob("*")
            if path.is_file()
            and "contract" in path.name.lower()
            and path.suffix.lower() == ".json"
        )

        for contract_path in json_contracts:
            _validate_json_contract(
                contract_path=contract_path,
                expected_task_id=descriptor.task_id,
            )

    def validate(self) -> tuple[ACRLTaskDescriptor, ...]:
        """Fail closed on missing tasks, packages, tests or contracts."""
        tasks = self.discover()

        expected_ids = tuple(
            f"T{number:02d}"
            for number in range(1, 31)
        )
        actual_ids = tuple(
            task.task_id
            for task in tasks
        )

        if actual_ids != expected_ids:
            raise ValueError(
                "ACRL registry returned an invalid T01-T30 sequence: "
                f"{actual_ids}"
            )

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
                "ACRL integration cannot start; unhealthy tasks "
                "(package __init__.py, contract and tests are required): "
                f"{unhealthy}"
            )

        # File presence alone is not sufficient: validate the JSON content.
        for task in tasks:
            self._validate_contracts(task)

        return tasks
