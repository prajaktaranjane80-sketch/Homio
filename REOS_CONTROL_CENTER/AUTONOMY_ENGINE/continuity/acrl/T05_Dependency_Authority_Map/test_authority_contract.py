"""ACRL T05 — contract tests."""

from __future__ import annotations

from .authority_contract import (
    contract_dict,
    validate_authority_contract,
)
from .dependency_authority_map import (
    DependencyAuthorityMapBuilder,
)


def test_default_map_satisfies_contract() -> None:
    authority_map = (
        DependencyAuthorityMapBuilder()
        .build()
    )

    validate_authority_contract(
        authority_map
    )


def test_contract_is_non_authorizing() -> None:
    contract = contract_dict()

    permissions = contract["permissions"]

    assert permissions["write_sources"] is False
    assert permissions["modify_authority"] is False
    assert permissions["authorize_execution"] is False
    assert permissions["repair_code"] is False


def test_contract_identity_is_explicit() -> None:
    contract = contract_dict()

    assert contract["layer"] == "T05"
    assert contract["mode"] == "READ_ONLY"
    assert (
        contract["authority"]
        ["primary_execution_authority"]
        == "REOS_STATE"
    )