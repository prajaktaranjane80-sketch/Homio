from __future__ import annotations

import json
from pathlib import Path

import pytest

from .integration_models import ACRLTaskDescriptor
from .task_registry import ACRLTaskRegistry


def make_acrl_tree(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)

    for number in range(1, 31):
        name = (
            "T14_Repository_Intelligence_Context"
            if number == 14
            else f"T{number:02d}_Test_Layer"
        )
        layer = root / name
        layer.mkdir(parents=True)

        (layer / "__init__.py").write_text(
            '"""Test ACRL layer."""\n',
            encoding="utf-8",
        )
        (layer / "test_smoke.py").write_text(
            "def test_smoke():\n    assert True\n",
            encoding="utf-8",
        )

        contract = {
            "contract_id": f"ACRL-T{number:02d}-TEST",
            "contract_version": "1.0",
            "layer": f"T{number:02d}",
            "mode": "READ_ONLY",
            "authority": {
                "execution_authorized": False,
                "write_authorized": False,
                "approval_authorized": False,
            },
        }
        (layer / f"t{number:02d}.contract.json").write_text(
            json.dumps(contract),
            encoding="utf-8",
        )

    compatibility = root / "T14_Full_Regression"
    compatibility.mkdir()
    (compatibility / "__init__.py").write_text(
        '"""T14 compatibility package."""\n',
        encoding="utf-8",
    )
    (compatibility / "test_compatibility.py").write_text(
        "def test_compatibility():\n    assert True\n",
        encoding="utf-8",
    )

    return root


def test_descriptor_health_requires_all_core_artifacts() -> None:
    base = {
        "task_id": "T01",
        "directory_name": "T01_Test_Layer",
        "path": "/virtual/T01_Test_Layer",
        "exists": True,
    }

    assert ACRLTaskDescriptor(
        **base,
        has_init=True,
        contract_files=("t01.contract.json",),
        test_files=("test_smoke.py",),
    ).healthy

    assert not ACRLTaskDescriptor(
        **base,
        has_init=False,
        contract_files=("t01.contract.json",),
        test_files=("test_smoke.py",),
    ).healthy

    assert not ACRLTaskDescriptor(
        **base,
        has_init=True,
        contract_files=(),
        test_files=("test_smoke.py",),
    ).healthy

    assert not ACRLTaskDescriptor(
        **base,
        has_init=True,
        contract_files=("t01.contract.json",),
        test_files=(),
    ).healthy


def test_missing_package_init_fails_closed(tmp_path: Path) -> None:
    root = make_acrl_tree(tmp_path / "acrl")
    (root / "T10_Test_Layer" / "__init__.py").unlink()

    with pytest.raises(ValueError, match="unhealthy tasks"):
        ACRLTaskRegistry(root).validate()


def test_missing_contract_fails_closed(tmp_path: Path) -> None:
    root = make_acrl_tree(tmp_path / "acrl")
    (root / "T08_Test_Layer" / "t08.contract.json").unlink()

    with pytest.raises(ValueError, match="unhealthy tasks"):
        ACRLTaskRegistry(root).validate()


def test_invalid_json_contract_fails_closed(tmp_path: Path) -> None:
    root = make_acrl_tree(tmp_path / "acrl")
    contract = root / "T04_Test_Layer" / "t04.contract.json"
    contract.write_text("{invalid-json", encoding="utf-8")

    with pytest.raises(
        ValueError,
        match="Invalid JSON contract for T04",
    ):
        ACRLTaskRegistry(root).validate()


def test_utf8_bom_in_valid_json_contract_is_accepted(
    tmp_path: Path,
) -> None:
    root = make_acrl_tree(tmp_path / "acrl")
    contract = root / "T03_Test_Layer" / "t03.contract.json"

    valid_json = json.dumps(
        {
            "contract_id": "ACRL-T03-BOM-REGRESSION",
            "contract_version": "1.0",
            "layer": "T03",
            "mode": "READ_ONLY",
            "authority": {
                "execution_authorized": False,
                "write_authorized": False,
                "approval_authorized": False,
            },
        }
    ).encode("utf-8")

    # Reproduce the exact leading bytes causing the live CI failure.
    contract.write_bytes(b"\xef\xbb\xbf" + valid_json)

    tasks = ACRLTaskRegistry(root).validate()

    assert len(tasks) == 30


def test_contract_cannot_self_authorize_writes(
    tmp_path: Path,
) -> None:
    root = make_acrl_tree(tmp_path / "acrl")
    contract = root / "T04_Test_Layer" / "t04.contract.json"

    data = json.loads(contract.read_text(encoding="utf-8"))
    data["authority"]["write_authorized"] = True
    contract.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(ValueError, match="Unsafe authority flag"):
        ACRLTaskRegistry(root).validate()


def test_contract_layer_mismatch_fails_closed(
    tmp_path: Path,
) -> None:
    root = make_acrl_tree(tmp_path / "acrl")
    contract = root / "T04_Test_Layer" / "t04.contract.json"

    data = json.loads(contract.read_text(encoding="utf-8"))
    data["layer"] = "T05"
    contract.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(ValueError, match="Contract layer mismatch"):
        ACRLTaskRegistry(root).validate()


def test_compatibility_t14_is_not_a_second_task(
    tmp_path: Path,
) -> None:
    root = make_acrl_tree(tmp_path / "acrl")

    tasks = ACRLTaskRegistry(root).validate()

    assert len(tasks) == 30
    t14 = next(task for task in tasks if task.task_id == "T14")
    assert t14.directory_name == "T14_Repository_Intelligence_Context"
