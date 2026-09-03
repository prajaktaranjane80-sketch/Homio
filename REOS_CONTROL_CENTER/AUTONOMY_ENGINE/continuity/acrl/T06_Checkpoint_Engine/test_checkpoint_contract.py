"""ACRL T06 — checkpoint contract tests."""

from __future__ import annotations

import pytest

from .checkpoint_contract import (
    contract_dict,
    validate_checkpoint_contract,
)
from .checkpoint_engine import (
    CheckpointEngine,
)


def make_checkpoint():
    return CheckpointEngine.build_checkpoint(
        {
            "phase": "PRE-CODING ARCHITECTURE",
            "current_gate": "CORE-004",
            "current_subtask": "CORE-004-T06",
            "status": "CONTROL_CENTER_DRIVEN",
        },
        checkpoint_id="CP-CONTRACT-001",
        created_at="2026-08-31T00:00:00+00:00",
    )


def test_contract_accepts_valid_checkpoint():
    validate_checkpoint_contract(
        make_checkpoint()
    )


def test_contract_rejects_invalid_checkpoint():
    checkpoint = make_checkpoint()

    object.__setattr__(
        checkpoint,
        "source",
        "CHAT_CONTEXT",
    )

    with pytest.raises(ValueError):
        validate_checkpoint_contract(
            checkpoint
        )


def test_contract_dict_is_non_authorizing():
    contract = contract_dict()

    assert (
        contract["permissions"]
        ["mutate_reos_state"]
        is False
    )

    assert (
        contract["permissions"]
        ["authorize_execution"]
        is False
    )

    assert (
        contract["permissions"]
        ["modify_architecture"]
        is False
    )