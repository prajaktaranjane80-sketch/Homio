from __future__ import annotations

import json
from pathlib import Path

import pytest

from AUTONOMY_ENGINE.continuity.acrl.contract_graph import (
    ContractGraphReader,
    ContractGraphSourceError,
    ContractGraphValidationError,
)


def contract(
    module_id: str,
    *,
    derived_from: list[str] | None = None,
    depends_on: list[str] | None = None,
) -> dict:
    return {
        "contract_version": "1.0",
        "module_id": module_id,
        "module_path": (
            f"REOS_CONTROL_CENTER/"
            f"AUTONOMY_ENGINE/continuity/acrl/"
            f"{module_id.lower().replace('-', '_')}.py"
        ),
        "status": "ACTIVE",
        "owner": "ACRL",
        "layer": "ACRL",
        "derived_from": derived_from or [],
        "depends_on": depends_on or [],
        "consumes": [],
        "produces": [],
        "supersedes": [],
        "replaces": [],
    }


def write_contract(
    root: Path,
    filename: str,
    payload: dict,
) -> None:
    (root / filename).write_text(
        json.dumps(
            payload,
            indent=2,
        ),
        encoding="utf-8",
    )


def test_empty_graph_is_valid(
    tmp_path: Path,
) -> None:
    graph = ContractGraphReader(
        tmp_path
    ).discover()

    assert graph.contracts == ()


def test_contract_discovery(
    tmp_path: Path,
) -> None:
    write_contract(
        tmp_path,
        "acrl_core.contract.json",
        contract("ACRL-CORE"),
    )

    graph = ContractGraphReader(
        tmp_path
    ).discover()

    assert len(graph.contracts) == 1
    assert graph.get("ACRL-CORE") is not None


def test_dependency_link(
    tmp_path: Path,
) -> None:
    write_contract(
        tmp_path,
        "core.contract.json",
        contract("ACRL-CORE"),
    )

    write_contract(
        tmp_path,
        "child.contract.json",
        contract(
            "ACRL-CHILD",
            depends_on=["ACRL-CORE"],
        ),
    )

    graph = ContractGraphReader(
        tmp_path
    ).discover()

    dependencies = graph.dependencies_of(
        "ACRL-CHILD"
    )

    assert len(dependencies) == 1
    assert dependencies[0].module_id == "ACRL-CORE"


def test_dependent_link(
    tmp_path: Path,
) -> None:
    write_contract(
        tmp_path,
        "core.contract.json",
        contract("ACRL-CORE"),
    )

    write_contract(
        tmp_path,
        "child.contract.json",
        contract(
            "ACRL-CHILD",
            depends_on=["ACRL-CORE"],
        ),
    )

    graph = ContractGraphReader(
        tmp_path
    ).discover()

    dependents = graph.dependents_of(
        "ACRL-CORE"
    )

    assert len(dependents) == 1
    assert dependents[0].module_id == "ACRL-CHILD"


def test_lineage_link(
    tmp_path: Path,
) -> None:
    write_contract(
        tmp_path,
        "base.contract.json",
        contract("ACRL-BASE"),
    )

    write_contract(
        tmp_path,
        "middle.contract.json",
        contract(
            "ACRL-MIDDLE",
            derived_from=["ACRL-BASE"],
        ),
    )

    write_contract(
        tmp_path,
        "leaf.contract.json",
        contract(
            "ACRL-LEAF",
            derived_from=["ACRL-MIDDLE"],
        ),
    )

    graph = ContractGraphReader(
        tmp_path
    ).discover()

    lineage = graph.lineage_of(
        "ACRL-LEAF"
    )

    assert [item.module_id for item in lineage] == [
        "ACRL-BASE",
        "ACRL-MIDDLE",
    ]


def test_duplicate_ids_fail(
    tmp_path: Path,
) -> None:
    write_contract(
        tmp_path,
        "one.contract.json",
        contract("ACRL-SAME"),
    )

    write_contract(
        tmp_path,
        "two.contract.json",
        contract("ACRL-SAME"),
    )

    with pytest.raises(
        ContractGraphValidationError
    ):
        ContractGraphReader(
            tmp_path
        ).discover()


def test_unknown_reference_fails(
    tmp_path: Path,
) -> None:
    write_contract(
        tmp_path,
        "broken.contract.json",
        contract(
            "ACRL-BROKEN",
            depends_on=["ACRL-NOT-FOUND"],
        ),
    )

    with pytest.raises(
        ContractGraphValidationError
    ):
        ContractGraphReader(
            tmp_path
        ).discover()


def test_self_dependency_fails(
    tmp_path: Path,
) -> None:
    write_contract(
        tmp_path,
        "self.contract.json",
        contract(
            "ACRL-SELF",
            depends_on=["ACRL-SELF"],
        ),
    )

    with pytest.raises(
        ContractGraphValidationError
    ):
        ContractGraphReader(
            tmp_path
        ).discover()


def test_missing_root_fails(
    tmp_path: Path,
) -> None:
    missing = tmp_path / "missing"

    with pytest.raises(
        ContractGraphSourceError
    ):
        ContractGraphReader(missing)


def test_fingerprint_is_deterministic(
    tmp_path: Path,
) -> None:
    write_contract(
        tmp_path,
        "core.contract.json",
        contract("ACRL-CORE"),
    )

    reader = ContractGraphReader(
        tmp_path
    )

    first = reader.discover().fingerprint()
    second = reader.discover().fingerprint()

    assert first == second
    assert len(first) == 64