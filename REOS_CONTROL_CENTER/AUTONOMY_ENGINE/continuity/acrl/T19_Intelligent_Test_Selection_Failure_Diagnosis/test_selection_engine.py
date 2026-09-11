from __future__ import annotations

import hashlib
import json
from pathlib import Path

from AUTONOMY_ENGINE.continuity.acrl.T03_State_Reconstruction.state_reconstruction import (
    ExecutionStateSnapshot,
)
from AUTONOMY_ENGINE.continuity.acrl.T12_Resume_Safety_Validation.resume_safety_validation import (
    ResumeDecision,
    ResumeSafetyReason,
    ResumeSafetyReport,
)
from AUTONOMY_ENGINE.continuity.acrl.T17_Change_Impact_Dependency_Analysis.impact_models import (
    ChangeImpactReport,
)
from AUTONOMY_ENGINE.continuity.acrl.T17_Change_Impact_Dependency_Analysis.impact_registry import (
    T17Decision,
)

from .selection_engine import (
    discover_tests,
    select_tests,
)
from .t19_models import (
    T19Decision,
)


def _impact_fingerprint(report):
    payload = report.to_dict()
    payload["fingerprint"] = ""

    return hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
    ).hexdigest()


def build_state():
    return ExecutionStateSnapshot(
        phase="PRE-CODING ARCHITECTURE",
        gate_id="CORE-005",
        gate_name="Search",
        gate_status="CURRENT",
        current_task="Structured search",
        current_subtask="CORE-005-T01",
        current_subtask_status="IN_PROGRESS",
        completed_subtasks=(),
        pending_subtasks=("CORE-005-T01",),
        future_gates=("CORE-006",),
        state_schema_version=3,
        controller_version="7.0",
        canonical_source="data/state.json",
        source_state_sha256="a" * 64,
    )


def build_resume():
    return ResumeSafetyReport(
        schema_version="1.0",
        authority="REOS_CONTROL_CENTER",
        decision=ResumeDecision.SAFE_TO_RESUME,
        reason=ResumeSafetyReason.VALID,
        request_fingerprint="b" * 64,
        validated=True,
        fail_closed=False,
        explanation="safe",
    )


def build_impact(changed):
    provisional = ChangeImpactReport(
        schema_version="1.0",
        decision=T17Decision.ANALYZE,
        changed_paths=tuple(changed),
        impacts=(),
        dependency_impacts=(),
        protected_paths=(),
        unknown_paths=(),
        graph_nodes=1,
        graph_edges=0,
        fingerprint="",
        policy_schema="1.0",
        provenance_source="T17",
        state_mutated=False,
        execution_authorized=False,
    )

    return ChangeImpactReport(
        **{
            **provisional.__dict__,
            "fingerprint": _impact_fingerprint(provisional),
        }
    )


def test_discovers_tests(tmp_path: Path):
    (tmp_path / "test_project.py").write_text(
        "def test_x(): pass\n",
        encoding="utf-8",
    )

    discovered = discover_tests(tmp_path)

    assert len(discovered) == 1
    assert discovered[0].path == "test_project.py"


def test_selects_direct_name_match(tmp_path: Path):
    (tmp_path / "project.py").write_text(
        "VALUE = 1\n",
        encoding="utf-8",
    )
    (tmp_path / "test_project.py").write_text(
        "def test_project(): pass\n",
        encoding="utf-8",
    )

    plan = select_tests(
        repository_root=tmp_path,
        state_snapshot=build_state(),
        resume_report=build_resume(),
        impact_report=build_impact(("project.py",)),
    )

    assert plan.decision is T19Decision.SELECT
    assert plan.selected_tests[0].path == "test_project.py"


def test_selection_is_deterministic(tmp_path: Path):
    (tmp_path / "a.py").write_text(
        "VALUE = 1\n",
        encoding="utf-8",
    )
    (tmp_path / "test_a.py").write_text(
        "def test_a(): pass\n",
        encoding="utf-8",
    )

    first = select_tests(
        repository_root=tmp_path,
        state_snapshot=build_state(),
        resume_report=build_resume(),
        impact_report=build_impact(("a.py",)),
    )

    second = select_tests(
        repository_root=tmp_path,
        state_snapshot=build_state(),
        resume_report=build_resume(),
        impact_report=build_impact(("a.py",)),
    )

    assert first == second


def test_selection_is_read_only(tmp_path: Path):
    (tmp_path / "a.py").write_text(
        "VALUE = 1\n",
        encoding="utf-8",
    )
    (tmp_path / "test_a.py").write_text(
        "def test_a(): pass\n",
        encoding="utf-8",
    )

    before = sorted(
        item.name
        for item in tmp_path.iterdir()
    )

    select_tests(
        repository_root=tmp_path,
        state_snapshot=build_state(),
        resume_report=build_resume(),
        impact_report=build_impact(("a.py",)),
    )

    after = sorted(
        item.name
        for item in tmp_path.iterdir()
    )

    assert before == after


def test_blocks_unsafe_resume(tmp_path: Path):
    resume = ResumeSafetyReport(
        schema_version="1.0",
        authority="REOS_CONTROL_CENTER",
        decision=ResumeDecision.BLOCK_RESUME,
        reason=ResumeSafetyReason.STALE_STATE,
        request_fingerprint="c" * 64,
        validated=True,
        fail_closed=False,
        explanation="stale",
    )

    (tmp_path / "test_a.py").write_text(
        "def test_a(): pass\n",
        encoding="utf-8",
    )

    try:
        select_tests(
            repository_root=tmp_path,
            state_snapshot=build_state(),
            resume_report=resume,
            impact_report=build_impact(("a.py",)),
        )
    except Exception as exc:
        assert "unsafe" in str(exc).lower()
    else:
        raise AssertionError(
            "T19 must reject unsafe resume state."
        )
