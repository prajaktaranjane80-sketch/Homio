"""Canonical ACRL T01-T14 registry and filesystem discovery."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Tuple


@dataclass(frozen=True)
class CanonicalLayerSpec:
    layer_number: int
    name: str
    directory: str
    core_file: str
    test_glob: str = "test_*.py"

    @property
    def package_name(self) -> str:
        return f"AUTONOMY_ENGINE.continuity.acrl.{self.directory}"

    @property
    def core_module_name(self) -> str:
        return f"{self.package_name}.{Path(self.core_file).stem}"


class RegressionRegistry:
    """Authoritative T14 canonical topology description."""

    SPECS: Tuple[CanonicalLayerSpec, ...] = (
        CanonicalLayerSpec(1, "Project DNA", "T01_Project_DNA", "project_dna.py"),
        CanonicalLayerSpec(2, "Architecture Lock", "T02_Architecture_Lock", "architecture_lock.py"),
        CanonicalLayerSpec(3, "State Reconstruction", "T03_State_Reconstruction", "state_reconstruction.py"),
        CanonicalLayerSpec(4, "Gate/Subtask Continuity", "T04_Gate_Subtask_Continuity", "gate_subtask_continuity.py"),
        CanonicalLayerSpec(5, "Dependency & Authority Map", "T05_Dependency_Authority_Map", "dependency_authority_map.py"),
        CanonicalLayerSpec(6, "Checkpoint Engine", "T06_Checkpoint_Engine", "checkpoint_engine.py"),
        CanonicalLayerSpec(7, "New-Chat Bootstrap", "T07_New_Chat_Bootstrap", "new_chat_bootstrap.py"),
        CanonicalLayerSpec(8, "Context Compression", "T08_Context_Compression", "context_compression.py"),
        CanonicalLayerSpec(9, "State Fingerprint", "T09_State_Fingerprint", "state_integrity.py"),
        CanonicalLayerSpec(10, "Drift Detection", "T10_Drift_Detection", "drift_detection.py"),
        CanonicalLayerSpec(11, "Recovery / Fail-Closed", "T11_Recovery_Fail_Closed", "recovery_guard.py"),
        CanonicalLayerSpec(12, "Resume-Safety Validation", "T12_Resume_Safety_Validation", "resume_safety_validation.py"),
        CanonicalLayerSpec(13, "Controller Integration", "T13_Controller_Integration", "controller_integration.py"),
        CanonicalLayerSpec(14, "Full Regression", "T14_Full_Regression", "regression_layer.py"),
    )

    @classmethod
    def validate(cls) -> None:
        numbers = tuple(spec.layer_number for spec in cls.SPECS)
        if numbers != tuple(range(1, 15)):
            raise ValueError("T14 registry layer numbering is inconsistent.")
        dirs = tuple(spec.directory for spec in cls.SPECS)
        if len(dirs) != len(set(dirs)):
            raise ValueError("T14 registry contains duplicate directories.")

    @classmethod
    def discover(cls, acrl_root: Path) -> dict[CanonicalLayerSpec, tuple[Path, Path, tuple[Path, ...]]]:
        cls.validate()
        if not acrl_root.is_dir():
            raise FileNotFoundError(f"ACRL root not found: {acrl_root}")
        found = {}
        for spec in cls.SPECS:
            directory = acrl_root / spec.directory
            core = directory / spec.core_file
            tests = tuple(sorted(directory.glob(spec.test_glob))) if directory.is_dir() else tuple()
            found[spec] = (directory, core, tests)
        return found
