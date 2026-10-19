from __future__ import annotations

import json
from pathlib import Path

import pytest

from . import operational_runtime as runtime_module
from .task_registry import ACRLTaskRegistry


PROJECT_ROOT = Path(__file__).resolve().parents[4]
ACRL_ROOT = (
    PROJECT_ROOT
    / "AUTONOMY_ENGINE"
    / "continuity"
    / "acrl"
)


def _make_acrl_tree(root: Path, *, include_compatibility_t14: bool = True) -> Path:
    root.mkdir(parents=True, exist_ok=True)

    for number in range(1, 31):
        if number == 14:
            directory_name = "T14_Repository_Intelligence_Context"
        else:
            directory_name = f"T{number:02d}_Test_Layer"

        layer = root / directory_name
        layer.mkdir(parents=True, exist_ok=True)

        (layer / "__init__.py").write_text(
            '"""Test layer package."""\n',
            encoding="utf-8",
        )
        (layer / "test_smoke.py").write_text(
            "def test_smoke():\n"
            "    assert True\n",
            encoding="utf-8",
        )
        (layer / f"t{number:02d}.contract.json").write_text(
            json.dumps(
                {
                    "layer": f"T{number:02d}",
                    "name": f"Test layer {number:02d}",
                    "schema_version": "1.0",
                    "mode": "read-only",
                },
                sort_keys=True,
            ),
            encoding="utf-8",
        )

    if include_compatibility_t14:
        compatibility = root / "T14_Full_Regression"
        compatibility.mkdir(parents=True, exist_ok=True)
        (compatibility / "__init__.py").write_text(
            '"""T14 compatibility/support package."""\n',
            encoding="utf-8",
        )
        (compatibility / "test_compatibility.py").write_text(
            "def test_compatibility_directory_is_retained():\n"
            "    assert True\n",
            encoding="utf-8",
        )

    return root


def _write_valid_state(path: Path) -> bytes:
    path.parent.mkdir(parents=True, exist_ok=True)

    state = {
        "constitution": {
            "canonical_source": "REOS_CONTROL_CENTER/data/state.json",
        },
        "integrity": {
            "sha256": None,
        },
    }
    state["integrity"]["sha256"] = runtime_module._state_hash(state)

    raw = (
        json.dumps(
            state,
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")

    path.write_bytes(raw)
    return raw


def test_live_repository_uses_one_canonical_t14() -> None:
    registry = ACRLTaskRegistry(ACRL_ROOT)
    descriptors = registry.discover()

    assert tuple(item.task_id for item in descriptors) == tuple(
        f"T{number:02d}" for number in range(1, 31)
    )

    t14 = next(item for item in descriptors if item.task_id == "T14")
    assert t14.directory_name == "T14_Repository_Intelligence_Context"


def test_duplicate_t14_compatibility_directory_is_not_a_second_task(
    tmp_path: Path,
) -> None:
    acrl_root = _make_acrl_tree(tmp_path / "acrl")

    descriptors = ACRLTaskRegistry(acrl_root).validate()

    assert len(descriptors) == 30
    t14 = next(item for item in descriptors if item.task_id == "T14")
    assert t14.directory_name == "T14_Repository_Intelligence_Context"


def test_missing_canonical_t14_fails_closed(tmp_path: Path) -> None:
    acrl_root = _make_acrl_tree(
        tmp_path / "acrl",
        include_compatibility_t14=True,
    )
    canonical_t14 = acrl_root / "T14_Repository_Intelligence_Context"

    for child in canonical_t14.iterdir():
        if child.is_file():
            child.unlink()
        elif child.is_dir():
            import shutil

            shutil.rmtree(child)
    canonical_t14.rmdir()

    with pytest.raises(ValueError, match="Canonical ACRL directory"):
        ACRLTaskRegistry(acrl_root).discover()


def test_read_only_preflight_does_not_change_state_json(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    control_center_root = tmp_path / "REOS_CONTROL_CENTER"
    state_path = control_center_root / "data" / "state.json"
    acrl_root = _make_acrl_tree(
        control_center_root / "AUTONOMY_ENGINE" / "continuity" / "acrl"
    )

    before_bytes = _write_valid_state(state_path)

    monkeypatch.setattr(runtime_module, "CONTROL_CENTER_ROOT", control_center_root)
    monkeypatch.setattr(runtime_module, "STATE_PATH", state_path)
    monkeypatch.setattr(runtime_module, "ACRL_ROOT", acrl_root)

    commands = {
        ("branch", "--show-current"): "reos-development",
        ("rev-parse", "HEAD"): "a" * 40,
        ("status", "--porcelain"): "",
    }

    def fake_git(*args: str) -> str:
        try:
            return commands[tuple(args)]
        except KeyError as exc:
            raise AssertionError(f"Unexpected Git command: {args}") from exc

    monkeypatch.setattr(runtime_module, "_git", fake_git)

    result = runtime_module.run_final_operational_proof(
        mission_id="ACRL-READ-ONLY-TEST",
        note="Prove the default operational entry point is read-only",
    )

    assert result.status == "READ_ONLY_PREFLIGHT_PASS"
    assert result.controller_command == ()
    assert result.state_integrity is True
    assert result.state_changed is False
    assert result.evidence["mutation_attempted"] is False
    assert result.evidence["self_authorized_execution"] is False
    assert result.evidence["state_bytes_unchanged"] is True
    assert state_path.read_bytes() == before_bytes


def test_invalid_state_integrity_fails_closed_without_writing_state(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    control_center_root = tmp_path / "REOS_CONTROL_CENTER"
    state_path = control_center_root / "data" / "state.json"
    acrl_root = _make_acrl_tree(
        control_center_root / "AUTONOMY_ENGINE" / "continuity" / "acrl"
    )

    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(
        json.dumps(
            {
                "constitution": {},
                "integrity": {"sha256": "0" * 64},
            }
        ),
        encoding="utf-8",
    )
    before_bytes = state_path.read_bytes()

    monkeypatch.setattr(runtime_module, "CONTROL_CENTER_ROOT", control_center_root)
    monkeypatch.setattr(runtime_module, "STATE_PATH", state_path)
    monkeypatch.setattr(runtime_module, "ACRL_ROOT", acrl_root)

    with pytest.raises(RuntimeError, match="integrity"):
        runtime_module.run_final_operational_proof(
            mission_id="ACRL-INVALID-STATE-TEST",
            note="Invalid state must fail closed",
        )

    assert state_path.read_bytes() == before_bytes
