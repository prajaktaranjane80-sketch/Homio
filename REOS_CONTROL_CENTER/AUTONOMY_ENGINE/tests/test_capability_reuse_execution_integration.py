from __future__ import annotations

import sys
from pathlib import Path


AUTONOMY_ENGINE_ROOT = Path(__file__).resolve().parents[1]

if str(AUTONOMY_ENGINE_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(AUTONOMY_ENGINE_ROOT),
    )


from orchestration.capability_reuse_guard import (
    CapabilityRecord,
)
from orchestration.execution_coordinator import (
    ExecutionContext,
    ExecutionCoordinator,
    CoordinationStatus,
)
from protocols.action_protocol import (
    ActionProposal,
)


def _context() -> ExecutionContext:
    return ExecutionContext(
        authorized=True,
        capability_available=True,
        policy_allowed=True,
        risk_allowed=True,
        guard_allowed=True,
        idempotency_clear=True,
        tripwires_clear=True,
        architecture_locked=True,
        evidence={
            "test": True,
        },
    )


def _proposal(
    *,
    capability_id: str,
    name: str,
    responsibility: str,
) -> ActionProposal:
    return ActionProposal.create(
        action="create_module",
        target="AUTONOMY_ENGINE/example.py",
        parameters={
            "creates_capability": True,
            "capability_operation": "CREATE",
            "capability_reuse": {
                "capability_id": capability_id,
                "name": name,
                "description": responsibility,
                "responsibility": responsibility,
                "architecture_ids": [
                    "CORE-006",
                ],
                "source_of_truth": (
                    "AUTONOMY_ENGINE/example.py"
                ),
                "inputs": [],
                "outputs": [],
                "owner": "REOS_CONTROL_CENTER",
                "allow_create_new": True,
            },
        },
        requester="TEST",
        reason="capability reuse integration test",
    )


def test_duplicate_capability_is_blocked_before_mutation() -> None:
    existing = CapabilityRecord(
        capability_id="CAP-DEAL-OWNERSHIP",
        name="Deal Ownership",
        description="Existing deal ownership protection.",
        responsibility=(
            "Protect immutable ownership of a deal"
        ),
        architecture_ids=(
            "CORE-006",
        ),
        source_of_truth="AUTONOMY_ENGINE/core/deal.py",
    )

    calls: list[str] = []

    def executor(_proposal):
        calls.append("EXECUTED")
        return "MUTATED"

    coordinator = ExecutionCoordinator(
        capability_catalog_provider=lambda: (
            existing,
        ),
    )

    proposal = _proposal(
        capability_id="CAP-NEW",
        name="Transaction Ownership",
        responsibility=(
            "Protect immutable ownership of a deal"
        ),
    )

    result = coordinator.execute(
        proposal,
        _context(),
        executor=executor,
        postflight={
            "evidence_complete": True,
            "provenance_valid": True,
            "state_consistent": True,
        },
    )

    assert result.status is CoordinationStatus.BLOCKED
    assert result.allowed is False
    assert calls == []

    reuse = result.evidence["capability_reuse"]

    assert reuse["required"] is True
    assert (
        reuse["first_check"]["selected_capability_id"]
        == "CAP-DEAL-OWNERSHIP"
    )


def test_unique_capability_reaches_mutation_boundary() -> None:
    calls: list[str] = []

    def executor(_proposal):
        calls.append("EXECUTED")
        return "MUTATED"

    coordinator = ExecutionCoordinator(
        capability_catalog_provider=lambda: (),
    )

    proposal = _proposal(
        capability_id="CAP-GEO-SEARCH",
        name="Geospatial Search",
        responsibility=(
            "Search inventory using verified geographic radius"
        ),
    )

    result = coordinator.execute(
        proposal,
        _context(),
        executor=executor,
        postflight={
            "evidence_complete": True,
            "provenance_valid": True,
            "state_consistent": True,
        },
    )

    assert result.status is CoordinationStatus.EXECUTED
    assert result.allowed is True
    assert calls == ["EXECUTED"]


def test_catalog_change_between_checks_blocks_mutation() -> None:
    existing = CapabilityRecord(
        capability_id="CAP-LATE",
        name="Late Duplicate",
        description="Created by another agent between checks.",
        responsibility=(
            "Protect immutable ownership of a deal"
        ),
        architecture_ids=(
            "CORE-006",
        ),
        source_of_truth="AUTONOMY_ENGINE/core/deal.py",
    )

    catalog_calls = 0
    executions: list[str] = []

    def catalog_provider():
        nonlocal catalog_calls

        catalog_calls += 1

        if catalog_calls == 1:
            return ()

        return (
            existing,
        )

    def executor(_proposal):
        executions.append("EXECUTED")
        return "MUTATED"

    coordinator = ExecutionCoordinator(
        capability_catalog_provider=catalog_provider,
    )

    proposal = _proposal(
        capability_id="CAP-NEW",
        name="Late Duplicate Candidate",
        responsibility=(
            "Protect immutable ownership of a deal"
        ),
    )

    result = coordinator.execute(
        proposal,
        _context(),
        executor=executor,
        postflight={
            "evidence_complete": True,
            "provenance_valid": True,
            "state_consistent": True,
        },
    )

    assert result.status is CoordinationStatus.BLOCKED
    assert result.allowed is False
    assert catalog_calls >= 2
    assert executions == []

    reuse = result.evidence["capability_reuse"]

    assert (
        reuse["second_check"]["selected_capability_id"]
        == "CAP-LATE"
    )


def test_normal_non_capability_execution_is_unchanged() -> None:
    calls: list[str] = []

    def executor(_proposal):
        calls.append("EXECUTED")
        return "OK"

    coordinator = ExecutionCoordinator(
        capability_catalog_provider=lambda: (),
    )

    proposal = ActionProposal.create(
        action="checkpoint",
        target="REOS_CONTROL_CENTER",
        parameters={
            "note": "normal checkpoint",
        },
        requester="TEST",
        reason="non capability action",
    )

    result = coordinator.execute(
        proposal,
        _context(),
        executor=executor,
        postflight={
            "evidence_complete": True,
            "provenance_valid": True,
            "state_consistent": True,
        },
    )

    assert result.status is CoordinationStatus.EXECUTED
    assert calls == ["EXECUTED"]
