from __future__ import annotations

from datetime import datetime, timezone
import hashlib
from pathlib import Path
import sys

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
GATE_SCRIPT_DIRECTORY = (
    REPOSITORY_ROOT
    / ".github"
    / "actions"
    / "homio-backend-ci"
    / "verification"
    / "scripts"
)
sys.path.insert(0, str(GATE_SCRIPT_DIRECTORY))

from production_readiness_gate import (
    REQUIRED_OPERATIONAL_CONTROLS,
    REQUIRED_QUALITY_METRICS,
    evaluate_production_readiness,
)

NOW = datetime(2026, 10, 30, 7, 0, tzinfo=timezone.utc)
COMMIT = "a" * 40


def _evidence_file(root: Path, name: str) -> tuple[str, str]:
    path = root / "evidence" / f"{name}.txt"
    path.parent.mkdir(parents=True, exist_ok=True)
    content = f"synthetic evidence for {name}\n".encode()
    path.write_bytes(content)
    return (
        path.relative_to(root).as_posix(),
        hashlib.sha256(content).hexdigest(),
    )


def _quality_report(*, q10_complete: bool = True) -> dict:
    criteria = {
        "bedroom_count": 2,
        "budget_min_minor": 8_000_000,
        "budget_max_minor": 10_000_000,
        "currency": "INR",
        "city_id": "IN-MH-PUNE",
        "transit_radius_m": 1_000,
    }

    request = {
        "tenant_id": "tenant-synthetic",
        "identity_sha256": "b" * 64,
        "filters_present": q10_complete,
        "structured_criteria": criteria if q10_complete else None,
        "unsupported_criteria": (
            []
            if q10_complete
            else ["bedroom_count", "budget", "locality", "transit"]
        ),
        "criteria_contract_version": "CORE-005-SEARCH-CRITERIA-v2",
    }

    return {
        "schema_version": 1,
        "run_metadata": {
            "repository": "prajaktaranjane80-sketch/Homio",
            "branch": "reos-development",
            "commit_sha": COMMIT,
        },
        "summary": {
            "executable_cases": 10,
            "passed_cases": 10,
            "failed_cases": 0,
            "blocked_cases": 0,
            "quality_thresholds_approved": True,
        },
        "cases": [
            *[
                {"case_id": f"S14-Q{number:02d}", "outcome": "PASS"}
                for number in range(1, 10)
            ],
            {
                "case_id": "S14-Q10",
                "outcome": "PASS",
                "invariant_results": {
                    "typed_criteria": True,
                    "tenant_scope": True,
                },
                "observed_result": {
                    "canonical_search_request": request
                },
            },
        ],
    }


def _valid_operational_evidence(root: Path) -> dict:
    quality_path, quality_hash = _evidence_file(
        root,
        "quality-evaluation",
    )
    slo_path, slo_hash = _evidence_file(
        root,
        "availability-slo",
    )

    controls = []
    for control_id in sorted(REQUIRED_OPERATIONAL_CONTROLS):
        path, digest = _evidence_file(root, control_id)
        record = {
            "control_id": control_id,
            "status": "VERIFIED",
            "verified_by": "synthetic-release-owner",
            "verified_at_utc": NOW.isoformat(),
            "evidence_path": path,
            "evidence_sha256": digest,
        }

        if control_id in {
            "provider_data_residency",
            "data_retention_and_deletion",
        }:
            record["approval_reference"] = (
                f"SYNTHETIC-APPROVAL-{control_id}"
            )

        controls.append(record)

    return {
        "schema_version": 1,
        "environment": "production",
        "tested_commit_sha": COMMIT,
        "verified_by": "synthetic-release-owner",
        "verified_at_utc": NOW.isoformat(),
        "quality_thresholds": {
            "status": "APPROVED",
            "approval_reference": "SYNTHETIC-QUALITY-APPROVAL",
            "approved_by": "synthetic-release-owner",
            "approved_at_utc": NOW.isoformat(),
            "thresholds": {
                metric: 0.99
                for metric in REQUIRED_QUALITY_METRICS
            },
            "measured_metrics": {
                metric: 1.0
                for metric in REQUIRED_QUALITY_METRICS
            },
            "evidence_path": quality_path,
            "evidence_sha256": quality_hash,
        },
        "availability_slo": {
            "status": "APPROVED",
            "approval_reference": "SYNTHETIC-AVAILABILITY-APPROVAL",
            "approved_by": "synthetic-release-owner",
            "approved_at_utc": NOW.isoformat(),
            "target_percent": 99.9,
            "measured_percent": 100.0,
            "measurement_window_days": 30,
            "evidence_path": slo_path,
            "evidence_sha256": slo_hash,
        },
        "controls": controls,
    }


def test_complete_exact_commit_evidence_can_pass_gate(
    tmp_path: Path,
) -> None:
    report = _quality_report()
    evidence = _valid_operational_evidence(tmp_path)

    gate = evaluate_production_readiness(
        report,
        evidence,
        repository_root=tmp_path,
        now_utc=NOW,
        expected_commit=COMMIT,
    )

    assert gate["release_ready"] is True, gate
    assert gate["blockers"] == []
    assert len(gate["verified_operational_controls"]) == len(
        REQUIRED_OPERATIONAL_CONTROLS
    )


def test_missing_operational_evidence_fails_closed(
    tmp_path: Path,
) -> None:
    gate = evaluate_production_readiness(
        _quality_report(),
        None,
        repository_root=tmp_path,
        now_utc=NOW,
        expected_commit=COMMIT,
    )

    assert gate["release_ready"] is False
    codes = {item["code"] for item in gate["blockers"]}
    assert "OPERATIONAL_ATTESTATION_MISSING" in codes
    assert "OPERATIONAL_CONTROL_NOT_VERIFIED" in codes


def test_section14_q10_cannot_pass_without_structured_criteria(
    tmp_path: Path,
) -> None:
    evidence = _valid_operational_evidence(tmp_path)

    gate = evaluate_production_readiness(
        _quality_report(q10_complete=False),
        evidence,
        repository_root=tmp_path,
        now_utc=NOW,
        expected_commit=COMMIT,
    )

    assert gate["release_ready"] is False
    assert any(
        item["code"] == "S14_Q10_STRUCTURED_SEARCH_NOT_VERIFIED"
        for item in gate["blockers"]
    )


def test_evidence_from_another_commit_is_rejected(
    tmp_path: Path,
) -> None:
    evidence = _valid_operational_evidence(tmp_path)
    evidence["tested_commit_sha"] = "c" * 40

    gate = evaluate_production_readiness(
        _quality_report(),
        evidence,
        repository_root=tmp_path,
        now_utc=NOW,
    )

    assert gate["release_ready"] is False
    assert any(
        item["code"] == "ATTESTATION_COMMIT_MISMATCH"
        for item in gate["blockers"]
    )


def test_tampered_evidence_hash_is_rejected(
    tmp_path: Path,
) -> None:
    evidence = _valid_operational_evidence(tmp_path)
    evidence["controls"][0]["evidence_sha256"] = "0" * 64

    gate = evaluate_production_readiness(
        _quality_report(),
        evidence,
        repository_root=tmp_path,
        now_utc=NOW,
    )

    assert gate["release_ready"] is False
    assert any(
        item["code"] == "OPERATIONAL_CONTROL_EVIDENCE_INVALID"
        for item in gate["blockers"]
    )


def test_stale_controls_are_rejected(
    tmp_path: Path,
) -> None:
    evidence = _valid_operational_evidence(tmp_path)
    evidence["controls"][0]["verified_at_utc"] = (
        "2026-01-01T00:00:00+00:00"
    )

    gate = evaluate_production_readiness(
        _quality_report(),
        evidence,
        repository_root=tmp_path,
        now_utc=NOW,
    )

    assert gate["release_ready"] is False
    assert any(
        "stale" in item["detail"] or "timestamp" in item["detail"]
        for item in gate["blockers"]
    )


def test_availability_must_meet_approved_slo_for_30_days(
    tmp_path: Path,
) -> None:
    evidence = _valid_operational_evidence(tmp_path)
    evidence["availability_slo"]["measured_percent"] = 99.0
    evidence["availability_slo"]["measurement_window_days"] = 7

    gate = evaluate_production_readiness(
        _quality_report(),
        evidence,
        repository_root=tmp_path,
        now_utc=NOW,
    )

    assert gate["release_ready"] is False
    codes = {item["code"] for item in gate["blockers"]}
    assert "AVAILABILITY_SLO_NOT_MET" in codes
    assert "AVAILABILITY_WINDOW_INVALID" in codes


def test_quality_measurements_must_meet_approved_thresholds(
    tmp_path: Path,
) -> None:
    evidence = _valid_operational_evidence(tmp_path)
    evidence["quality_thresholds"]["measured_metrics"][
        "citation_precision"
    ] = 0.80

    gate = evaluate_production_readiness(
        _quality_report(),
        evidence,
        repository_root=tmp_path,
        now_utc=NOW,
    )

    assert gate["release_ready"] is False
    assert any(
        item["code"] == "QUALITY_THRESHOLD_NOT_MET"
        for item in gate["blockers"]
    )


def test_symlink_evidence_is_never_accepted(
    tmp_path: Path,
) -> None:
    evidence = _valid_operational_evidence(tmp_path)
    original = evidence["controls"][0]["evidence_path"]
    source = tmp_path / original
    link = tmp_path / "evidence" / "linked.txt"
    link.symlink_to(source)
    evidence["controls"][0]["evidence_path"] = "evidence/linked.txt"

    gate = evaluate_production_readiness(
        _quality_report(),
        evidence,
        repository_root=tmp_path,
        now_utc=NOW,
    )

    assert gate["release_ready"] is False
    assert any(
        "symlink" in item["detail"]
        for item in gate["blockers"]
    )
