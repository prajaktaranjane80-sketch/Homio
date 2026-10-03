from __future__ import annotations

from pathlib import Path

from architecture.governance.architecture_integrity import (
    EXPECTED_ARCHITECTURE_ID,
    validate_master_architecture,
    validate_repository_master_uniqueness,
    validate_state_alignment,
)


def _master() -> dict:
    nodes = [
        {
            "id": f"ARCH-{index:03d}",
            "name": f"Architecture Node {index}",
            "status": (
                "PENDING"
                if index == 39
                else "APPROVED"
            ),
        }
        for index in range(1, 40)
    ]

    return {
        "schema_version": "1.0",
        "architecture_id": "ARCH-039",
        "name": "HOMIO / REOS Master Architecture",
        "version": "1.0",
        "status": "FINAL_ARCHITECTURE_CONTENT",
        "authority": {
            "role": (
                "Single canonical architectural blueprint "
                "for HOMIO / REOS."
            ),
            "architecture_source": "This file",
            "execution_state": (
                "REOS_CONTROL_CENTER/data/state.json"
            ),
            "execution_templates": (
                "REOS_CONTROL_CENTER/GATE_TEMPLATES.json"
            ),
            "code_truth": "Git repository",
            "continuity_truth": (
                "ACRL derived from canonical machine state "
                "and repository evidence"
            ),
            "chat_is_authority": False,
            "parallel_master_architecture_forbidden": True,
        },
        "authority_boundaries": {
            "customer": {
                "owner": "FUTURE_DEDICATED_CUSTOMER_DOMAIN",
                "status": "FUTURE_ARCHITECTURE_BOUNDARY",
            },
            "builder": {
                "owner": "FUTURE_DEDICATED_BUILDER_DOMAIN",
                "status": "FUTURE_ARCHITECTURE_BOUNDARY",
            },
            "communication": {
                "owner": "ARCH-009",
                "status": "APPROVED_ARCHITECTURE_NODE",
            },
            "evidence": {
                "owner": "ARCH-014",
                "status": "APPROVED_ARCHITECTURE_NODE",
            },
            "acrl": {
                "owner": "ACRL",
                "status": "CONTINUITY_RECONSTRUCTION_BOUNDARY",
            },
        },
        "architecture_nodes": nodes,
        "canonical_graphs": [
            {
                "id": f"GRAPH-{index:03d}",
                "name": f"Graph {index}",
                "purpose": f"Purpose {index}",
            }
            for index in range(1, 7)
        ],
        "canonical_truth_rules": {
            "business_truth": [
                "identity",
                "tenant",
                "customer",
                "lead",
                "builder",
                "project",
                "inventory",
                "deal",
                "evidence",
                "commission obligation/reference",
            ],
            "derived_views": [
                "search indexes",
                "vector indexes",
                "analytics",
                "warehouse",
                "AI context",
                "digital twins",
            ],
            "rule": (
                "Derived systems can consume canonical truth and events, "
                "but cannot silently become business source of truth."
            ),
        },
        "global_invariants": [
            "One authoritative source per business responsibility",
            "No duplicate domain logic",
            "Derived views remain rebuildable",
        ],
        "architecture_change_policy": {
            "requires_review": [
                "new top-level business domain",
                "new source of truth",
                "ownership boundary change",
            ],
            "forbidden_without_explicit_approval": [
                "second master architecture",
                "second execution-state authority",
                "duplicate domain engine",
                "AI as final business authority",
            ],
        },
    }


def _state(
    *,
    arch039_plan_status: str = "CURRENT",
    locked: bool = False,
) -> dict:
    return {
        "execution": {
            "current_gate": (
                "CORE-008"
            ),
        },
        "execution_plan": {
            "authoritative_sequence": [
                {
                    "gate": "ARCH-039",
                    "status": arch039_plan_status,
                },
            ],
        },
        "architecture": {
            "approved": [
                {
                    "id": f"ARCH-{index:03d}",
                    "name": f"Architecture Node {index}",
                    "status": "APPROVED",
                }
                for index in range(1, 39)
            ],
            "pending": [
                {
                    "id": EXPECTED_ARCHITECTURE_ID,
                    "name": "Master Blueprint v1.0",
                    "status": "PENDING",
                }
            ],
            "locked": locked,
        },
    }


def test_valid_master_architecture_passes() -> None:
    report = validate_master_architecture(
        _master()
    )

    assert report.ok is True
    assert report.issues == ()


def test_duplicate_node_id_is_rejected() -> None:
    architecture = _master()

    architecture["architecture_nodes"][1]["id"] = (
        architecture["architecture_nodes"][0]["id"]
    )

    report = validate_master_architecture(
        architecture
    )

    assert report.ok is False
    assert any(
        issue.code == "DUPLICATE_NODE_ID"
        for issue in report.issues
    )


def test_missing_mandatory_node_is_rejected() -> None:
    architecture = _master()

    architecture["architecture_nodes"] = [
        node
        for node in architecture[
            "architecture_nodes"
        ]
        if node["id"] != "ARCH-038"
    ]

    report = validate_master_architecture(
        architecture
    )

    assert report.ok is False
    assert any(
        issue.code == "MANDATORY_NODE_MISSING"
        for issue in report.issues
    )


def test_invalid_node_status_is_rejected() -> None:
    architecture = _master()

    architecture["architecture_nodes"][0][
        "status"
    ] = "FROZEN"

    report = validate_master_architecture(
        architecture
    )

    assert report.ok is False
    assert any(
        issue.code == "INVALID_NODE_STATUS"
        for issue in report.issues
    )


def test_canonical_master_location_is_accepted(
    tmp_path: Path,
) -> None:
    master_dir = (
        tmp_path
        / "architecture"
        / "master"
    )

    master_dir.mkdir(
        parents=True
    )

    canonical = (
        master_dir
        / "HOMIO_REOS_MASTER_ARCHITECTURE.json"
    )

    canonical.write_text(
        "{}",
        encoding="utf-8",
    )

    report = (
        validate_repository_master_uniqueness(
            tmp_path
        )
    )

    assert report.ok is True
    assert report.issues == ()


def test_second_master_architecture_is_rejected(
    tmp_path: Path,
) -> None:
    master_dir = (
        tmp_path
        / "architecture"
        / "master"
    )

    master_dir.mkdir(
        parents=True
    )

    canonical = (
        master_dir
        / "HOMIO_REOS_MASTER_ARCHITECTURE.json"
    )

    duplicate = (
        master_dir
        / "SECOND_MASTER_ARCHITECTURE.json"
    )

    canonical.write_text(
        "{}",
        encoding="utf-8",
    )

    duplicate.write_text(
        "{}",
        encoding="utf-8",
    )

    report = (
        validate_repository_master_uniqueness(
            tmp_path
        )
    )

    assert report.ok is False
    assert any(
        issue.code
        == "SECOND_MASTER_ARCHITECTURE"
        for issue in report.issues
    )


def test_locked_state_with_pending_architecture_is_rejected() -> None:
    architecture = _master()
    state = _state(
        locked=True
    )

    report = validate_state_alignment(
        architecture,
        state,
    )

    assert report.ok is False

    codes = {
        issue.code
        for issue in report.issues
    }

    assert (
        "LOCKED_WITH_PENDING_ARCHITECTURE"
        in codes
    )


def test_execution_complete_while_arch039_pending_is_rejected() -> None:
    architecture = _master()
    state = _state(
        arch039_plan_status="COMPLETE"
    )

    report = validate_state_alignment(
        architecture,
        state,
    )

    assert report.ok is False

    assert any(
        issue.code
        == "EXECUTION_COMPLETE_WHILE_ARCH_PENDING"
        for issue in report.issues
    )


def test_clean_preapproval_alignment_passes() -> None:
    architecture = _master()
    state = _state(
        arch039_plan_status="CURRENT"
    )

    report = validate_state_alignment(
        architecture,
        state,
    )

    assert report.ok is True
    assert report.issues == ()


def test_missing_authority_boundary_is_rejected() -> None:
    architecture = _master()

    architecture["authority_boundaries"].pop(
        "customer"
    )

    report = validate_master_architecture(
        architecture
    )

    assert report.ok is False
    assert any(
        issue.code
        == "AUTHORITY_BOUNDARY_MISSING"
        for issue in report.issues
    )


def test_invalid_authority_boundary_is_rejected() -> None:
    architecture = _master()

    architecture["authority_boundaries"][
        "evidence"
    ]["owner"] = "DUPLICATE_EVIDENCE_ENGINE"

    report = validate_master_architecture(
        architecture
    )

    assert report.ok is False
    assert any(
        issue.code
        == "INVALID_AUTHORITY_BOUNDARY"
        for issue in report.issues
    )


def test_invalid_master_authority_fails_closed() -> None:
    architecture = _master()

    architecture["authority"][
        "chat_is_authority"
    ] = True

    report = validate_master_architecture(
        architecture
    )

    assert report.ok is False
    assert any(
        issue.code
        == "INVALID_AUTHORITY_VALUE"
        for issue in report.issues
    )
