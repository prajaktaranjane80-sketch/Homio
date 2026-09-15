from pathlib import Path

import pytest

from AUTONOMY_ENGINE.continuity.acrl.T17_Change_Impact_Dependency_Analysis.impact_context import (
    AUTHORITY,
    ChangeImpactContextDecision,
    ChangeImpactContextEngine,
    ChangeImpactContextValidationError,
    ChangeImpactContextRequest,
)


def build_repo(root: Path):
    app = root / "app"
    tests = root / "tests"
    app.mkdir(parents=True)
    tests.mkdir(parents=True)

    (app / "__init__.py").write_text("")
    (app / "base.py").write_text(
        "VALUE = 1\n"
    )
    (app / "service.py").write_text(
        "from app.base import VALUE\n"
        "RESULT = VALUE\n"
    )
    (app / "api.py").write_text(
        "from app.service import RESULT\n"
        "PUBLIC = RESULT\n"
    )

    (tests / "test_service.py").write_text(
        "from app.service import RESULT\n"
        "def test_result():\n"
        "    assert RESULT == 1\n"
    )

    (root / "state.json").write_text("{}\n")

    (root / "app.contract.json").write_text(
        '{\n'
        '  "module_id": "APP-SERVICE",\n'
        '  "module_path": "app/service.py",\n'
        '  "status": "ACTIVE",\n'
        '  "owner": "REOS_CONTROL_CENTER",\n'
        '  "layer": "CORE",\n'
        '  "derived_from": [],\n'
        '  "depends_on": [],\n'
        '  "consumes": ["app.base"],\n'
        '  "produces": ["app.service"],\n'
        '  "supersedes": [],\n'
        '  "replaces": []\n'
        '}\n'
    )

    return root


def test_reconstructs_position_and_blast_radius(tmp_path):
    root = build_repo(
        tmp_path / "repo"
    )

    request = ChangeImpactContextRequest.create(
        repository_root=root,
        current_gate="CORE-004",
        current_task="CORE-004-T02",
        current_subtask="inventory-domain",
        changed_paths=("app/base.py",),
    )

    report = ChangeImpactContextEngine(
        root
    ).reconstruct(request)

    assert (
        report.decision
        == ChangeImpactContextDecision.RESOLVED
    )

    assert (
        report.current_gate
        == "CORE-004"
    )

    assert (
        report.current_task
        == "CORE-004-T02"
    )

    assert (
        "app/base.py"
        in report.affected_modules
    )

    assert (
        "app/service.py"
        in report.dependent_modules
    )

    assert report.blast_radius >= 2


def test_test_impact_detected(tmp_path):
    root = build_repo(
        tmp_path / "repo"
    )

    report = ChangeImpactContextEngine(
        root
    ).reconstruct(
        ChangeImpactContextRequest.create(
            repository_root=root,
            current_gate="CORE-004",
            current_task="CORE-004-T02",
            current_subtask="inventory-domain",
            changed_paths=("app/service.py",),
        )
    )

    assert (
        "tests/test_service.py"
        in report.test_impact
    )


def test_contract_impact_detected(tmp_path):
    root = build_repo(
        tmp_path / "repo"
    )

    report = ChangeImpactContextEngine(
        root
    ).reconstruct(
        ChangeImpactContextRequest.create(
            repository_root=root,
            current_gate="CORE-004",
            current_task="CORE-004-T02",
            current_subtask="inventory-domain",
            changed_paths=("app/service.py",),
        )
    )

    assert (
        "app.contract.json"
        in report.contract_impact
    )


def test_protected_authority_impact(tmp_path):
    root = build_repo(
        tmp_path / "repo"
    )

    report = ChangeImpactContextEngine(
        root
    ).reconstruct(
        ChangeImpactContextRequest.create(
            repository_root=root,
            current_gate="CORE-004",
            current_task="CORE-004-T02",
            current_subtask="inventory-domain",
            changed_paths=("state.json",),
        )
    )

    assert (
        "PROTECTED_FILE"
        in report.authority_impact
    )


def test_unknown_path_blocks(tmp_path):
    root = build_repo(
        tmp_path / "repo"
    )

    report = ChangeImpactContextEngine(
        root
    ).reconstruct(
        ChangeImpactContextRequest.create(
            repository_root=root,
            current_gate="CORE-004",
            current_task="CORE-004-T02",
            current_subtask="inventory-domain",
            changed_paths=("missing.py",),
        )
    )

    assert (
        report.decision
        == ChangeImpactContextDecision.BLOCKED
    )


def test_authority_is_preserved(tmp_path):
    root = build_repo(
        tmp_path / "repo"
    )

    report = ChangeImpactContextEngine(
        root
    ).reconstruct(
        ChangeImpactContextRequest.create(
            repository_root=root,
            current_gate="CORE-004",
            current_task="CORE-004-T02",
            current_subtask="inventory-domain",
            changed_paths=("app/base.py",),
        )
    )

    assert report.authority == AUTHORITY
    assert report.state_mutated is False
    assert report.execution_authorized is False


def test_fingerprint_is_deterministic(tmp_path):
    root = build_repo(
        tmp_path / "repo"
    )

    request = ChangeImpactContextRequest.create(
        repository_root=root,
        current_gate="CORE-004",
        current_task="CORE-004-T02",
        current_subtask="inventory-domain",
        changed_paths=("app/base.py",),
    )

    engine = ChangeImpactContextEngine(root)

    first = engine.reconstruct(request)
    second = engine.reconstruct(request)

    assert (
        first.impact_fingerprint
        == second.impact_fingerprint
    )


def test_wrong_authority_rejected(tmp_path):
    root = build_repo(
        tmp_path / "repo"
    )

    request = ChangeImpactContextRequest.create(
        repository_root=root,
        current_gate="CORE-004",
        current_task="CORE-004-T02",
        current_subtask="inventory-domain",
        changed_paths=("app/base.py",),
        authority="WRONG_AUTHORITY",
    )

    with pytest.raises(
        ChangeImpactContextValidationError
    ):
        ChangeImpactContextEngine(
            root
        ).reconstruct(request)


def test_empty_changed_paths_rejected(tmp_path):
    root = build_repo(
        tmp_path / "repo"
    )

    with pytest.raises(
        ChangeImpactContextValidationError
    ):
        ChangeImpactContextRequest.create(
            repository_root=root,
            current_gate="CORE-004",
            current_task="CORE-004-T02",
            current_subtask="inventory-domain",
            changed_paths=(),
        )
