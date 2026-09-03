from __future__ import annotations

"""
ACRL Contract Graph

Provides deterministic discovery and validation of ACRL micro-module
contracts.

This is a linkage layer only.

It does NOT:
- own project state
- own architecture authority
- own capability definitions
- mutate state.json
- mutate controller state
- advance gates
- approve gates
- modify ACRL __init__.py
- replace dependency_authority_map.py
- replace capability_registry.py
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import hashlib
import json


class ContractGraphError(RuntimeError):
    """Base error for ACRL contract graph failures."""


class ContractGraphSourceError(ContractGraphError):
    """Raised when contract sources cannot be accessed."""


class ContractGraphValidationError(ContractGraphError):
    """Raised when contract structure or relationships are invalid."""


@dataclass(frozen=True)
class MicroModuleContract:
    """Immutable machine-readable identity for one ACRL micro-module."""

    module_id: str
    module_path: str
    status: str
    owner: str
    layer: str
    derived_from: tuple[str, ...]
    depends_on: tuple[str, ...]
    consumes: tuple[str, ...]
    produces: tuple[str, ...]
    supersedes: tuple[str, ...]
    replaces: tuple[str, ...]

    @staticmethod
    def _required_string(
        payload: dict[str, Any],
        name: str,
    ) -> str:
        value = payload.get(name)

        if not isinstance(value, str) or not value.strip():
            raise ContractGraphValidationError(
                f"'{name}' must be a non-empty string."
            )

        return value.strip()

    @staticmethod
    def _string_list(
        payload: dict[str, Any],
        name: str,
    ) -> tuple[str, ...]:
        value = payload.get(name)

        if not isinstance(value, list):
            raise ContractGraphValidationError(
                f"'{name}' must be a list."
            )

        result: list[str] = []

        for item in value:
            if not isinstance(item, str) or not item.strip():
                raise ContractGraphValidationError(
                    f"'{name}' contains an invalid value."
                )

            result.append(item.strip())

        return tuple(result)

    @classmethod
    def from_dict(
        cls,
        payload: dict[str, Any],
    ) -> "MicroModuleContract":
        return cls(
            module_id=cls._required_string(
                payload,
                "module_id",
            ),
            module_path=cls._required_string(
                payload,
                "module_path",
            ),
            status=cls._required_string(
                payload,
                "status",
            ),
            owner=cls._required_string(
                payload,
                "owner",
            ),
            layer=cls._required_string(
                payload,
                "layer",
            ),
            derived_from=cls._string_list(
                payload,
                "derived_from",
            ),
            depends_on=cls._string_list(
                payload,
                "depends_on",
            ),
            consumes=cls._string_list(
                payload,
                "consumes",
            ),
            produces=cls._string_list(
                payload,
                "produces",
            ),
            supersedes=cls._string_list(
                payload,
                "supersedes",
            ),
            replaces=cls._string_list(
                payload,
                "replaces",
            ),
        )


@dataclass(frozen=True)
class ContractGraph:
    """Immutable graph of discovered ACRL micro-module contracts."""

    contracts: tuple[MicroModuleContract, ...]

    def get(
        self,
        module_id: str,
    ) -> MicroModuleContract | None:
        for contract in self.contracts:
            if contract.module_id == module_id:
                return contract

        return None

    def dependencies_of(
        self,
        module_id: str,
    ) -> tuple[MicroModuleContract, ...]:
        contract = self.get(module_id)

        if contract is None:
            return ()

        return tuple(
            item
            for item in self.contracts
            if item.module_id in contract.depends_on
        )

    def dependents_of(
        self,
        module_id: str,
    ) -> tuple[MicroModuleContract, ...]:
        return tuple(
            item
            for item in self.contracts
            if module_id in item.depends_on
            or module_id in item.derived_from
        )

    def lineage_of(
        self,
        module_id: str,
    ) -> tuple[MicroModuleContract, ...]:
        result: list[MicroModuleContract] = []
        visited: set[str] = set()

        def visit(current_id: str) -> None:
            if current_id in visited:
                return

            visited.add(current_id)

            contract = self.get(current_id)

            if contract is None:
                return

            for parent_id in contract.derived_from:
                parent = self.get(parent_id)

                if parent is not None:
                    result.append(parent)

                visit(parent_id)

        visit(module_id)

        return tuple(
            sorted(
                result,
                key=lambda item: item.module_id,
            )
        )

    def fingerprint(self) -> str:
        payload = [
            {
                "module_id": item.module_id,
                "module_path": item.module_path,
                "status": item.status,
                "owner": item.owner,
                "layer": item.layer,
                "derived_from": item.derived_from,
                "depends_on": item.depends_on,
                "consumes": item.consumes,
                "produces": item.produces,
                "supersedes": item.supersedes,
                "replaces": item.replaces,
            }
            for item in self.contracts
        ]

        canonical = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
        )

        return hashlib.sha256(
            canonical.encode("utf-8")
        ).hexdigest()


class ContractGraphReader:
    """Read-only ACRL micro-module contract reader."""

    CONTRACT_SUFFIX = ".contract.json"

    def __init__(
        self,
        contracts_root: Path | str,
    ) -> None:
        self.contracts_root = Path(
            contracts_root
        ).resolve()

        if not self.contracts_root.exists():
            raise ContractGraphSourceError(
                f"Contracts root does not exist: "
                f"{self.contracts_root}"
            )

        if not self.contracts_root.is_dir():
            raise ContractGraphSourceError(
                f"Contracts root is not a directory: "
                f"{self.contracts_root}"
            )

    def discover(self) -> ContractGraph:
        files = tuple(
            sorted(
                (
                    path
                    for path in self.contracts_root.rglob(
                        f"*{self.CONTRACT_SUFFIX}"
                    )
                    if path.is_file()
                ),
                key=lambda path: path.as_posix().lower(),
            )
        )

        contracts: list[MicroModuleContract] = []

        for path in files:
            contracts.append(
                self._read_contract(path)
            )

        self._validate(
            contracts
        )

        ordered = tuple(
            sorted(
                contracts,
                key=lambda item: item.module_id,
            )
        )

        return ContractGraph(
            contracts=ordered
        )

    @staticmethod
    def _read_contract(
        path: Path,
    ) -> MicroModuleContract:
        try:
            payload = json.loads(
                path.read_text(
                    encoding="utf-8"
                )
            )
        except OSError as exc:
            raise ContractGraphSourceError(
                f"Unable to read contract: {path}"
            ) from exc

        except json.JSONDecodeError as exc:
            raise ContractGraphValidationError(
                f"Invalid JSON contract: {path}"
            ) from exc

        if not isinstance(payload, dict):
            raise ContractGraphValidationError(
                f"Contract root must be an object: {path}"
            )

        return MicroModuleContract.from_dict(
            payload
        )

    @staticmethod
    def _validate(
        contracts: list[MicroModuleContract],
    ) -> None:
        ids = [
            item.module_id
            for item in contracts
        ]

        if len(ids) != len(set(ids)):
            raise ContractGraphValidationError(
                "Duplicate module_id detected."
            )

        known = set(ids)

        for contract in contracts:
            if contract.module_id in contract.depends_on:
                raise ContractGraphValidationError(
                    f"Self dependency detected: "
                    f"{contract.module_id}"
                )

            if contract.module_id in contract.derived_from:
                raise ContractGraphValidationError(
                    f"Self lineage detected: "
                    f"{contract.module_id}"
                )

            for reference in (
                *contract.derived_from,
                *contract.depends_on,
                *contract.supersedes,
                *contract.replaces,
            ):
                if reference not in known:
                    raise ContractGraphValidationError(
                        f"Unknown module reference "
                        f"'{reference}' in "
                        f"{contract.module_id}."
                    )


def discover_acrl_contract_graph(
    contracts_root: Path | str,
) -> ContractGraph:
    """Return the validated deterministic ACRL micro-module graph."""

    return ContractGraphReader(
        contracts_root
    ).discover()


__all__ = [
    "ContractGraph",
    "ContractGraphError",
    "ContractGraphReader",
    "ContractGraphSourceError",
    "ContractGraphValidationError",
    "MicroModuleContract",
    "discover_acrl_contract_graph",
]