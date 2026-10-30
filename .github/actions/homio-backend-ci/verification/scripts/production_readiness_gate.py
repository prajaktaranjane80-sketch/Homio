"""Fail-closed production-readiness gate for HOMIO AI.

Deterministic Section 14 tests are necessary, not sufficient. This gate requires
exact-commit search proof, approved/measured quality and availability, and fresh
hashed operational evidence before reporting production readiness.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timedelta, timezone
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import re
import sys
from typing import Any, Mapping

REPOSITORY = "prajaktaranjane80-sketch/Homio"
BRANCH = "reos-development"
SCHEMA_VERSION = 1
MAX_EVIDENCE_AGE = timedelta(days=30)
MAX_FUTURE_SKEW = timedelta(minutes=5)
SHA1 = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
CURRENCY = re.compile(r"^[A-Z]{3}$")
REQUIRED_CASES = {f"S14-Q{i:02d}" for i in range(1, 11)}
SEARCH_FIELDS = (
    "bedroom_count", "budget_min_minor", "budget_max_minor",
    "currency", "city_id", "transit_radius_m",
)
QUALITY_METRICS = (
    "grounded_answer_rate", "citation_precision",
    "unsupported_claim_refusal_rate", "tenant_isolation_pass_rate",
    "tool_authorization_pass_rate",
)
OPERATIONAL_CONTROLS = (
    "provider_model_configuration", "secret_storage_and_rotation",
    "runtime_timeout_retry_policy", "tenant_usage_budgets_and_quotas",
    "production_rate_limits", "provider_data_residency",
    "data_retention_and_deletion", "production_monitoring_alerts_and_on_call",
    "operational_kill_switch", "tested_rollback",
    "production_release_workflow_and_protected_environment",
)
REQUIRED_OPERATIONAL_CONTROLS = OPERATIONAL_CONTROLS
REQUIRED_QUALITY_METRICS = QUALITY_METRICS


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _number(value: Any) -> bool:
    return (
        not isinstance(value, bool)
        and isinstance(value, (int, float))
        and math.isfinite(float(value))
    )


def _timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if result.tzinfo is None or result.utcoffset() is None:
        return None
    return result.astimezone(timezone.utc)


def _fresh(value: Any, now: datetime) -> bool:
    parsed = _timestamp(value)
    if parsed is None:
        return False
    age = now - parsed
    return -MAX_FUTURE_SKEW <= age <= MAX_EVIDENCE_AGE


def _evidence_file(
    root: Path,
    relative: Any,
    digest: Any,
) -> tuple[bool, str]:
    if (
        not _text(relative)
        or "\\" in relative
        or not isinstance(digest, str)
        or not SHA256.fullmatch(digest)
    ):
        return False, "path_or_sha256_invalid"

    path = PurePosixPath(relative.strip())
    if path.is_absolute() or any(
        part in {"", ".", ".."} for part in path.parts
    ):
        return False, "path_invalid"

    cursor = root.resolve()
    for part in path.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            return False, "symlink_forbidden"

    try:
        target = cursor.resolve(strict=True)
        target.relative_to(root.resolve())
        if not target.is_file():
            return False, "not_regular_file"
        actual = hashlib.sha256(target.read_bytes()).hexdigest()
    except (OSError, ValueError):
        return False, "file_missing_unreadable_or_outside_repository"

    return (
        (True, "verified")
        if actual == digest
        else (False, "sha256_mismatch")
    )


def _check_q10(report: Mapping[str, Any]) -> list[str]:
    problems: list[str] = []
    cases = report.get("cases")

    if not isinstance(cases, list):
        return ["cases_missing"]

    ids = [
        case.get("case_id")
        for case in cases
        if isinstance(case, Mapping)
    ]

    if len(ids) != len(cases) or len(ids) != len(set(ids)):
        problems.append("case_ids_invalid_or_duplicate")

    missing = sorted(REQUIRED_CASES - set(ids))
    if missing:
        problems.append("required_cases_missing:" + ",".join(missing))

    q10 = [
        case
        for case in cases
        if isinstance(case, Mapping)
        and case.get("case_id") == "S14-Q10"
    ]

    if len(q10) != 1:
        return problems + ["q10_missing_or_duplicate"]

    case = q10[0]

    if case.get("outcome") != "PASS":
        problems.append("q10_not_pass")

    invariants = case.get("invariant_results")
    if (
        not isinstance(invariants, Mapping)
        or not invariants
        or any(value is not True for value in invariants.values())
    ):
        problems.append("q10_invariants_not_all_true")

    observed = case.get("observed_result")
    request = (
        observed.get("canonical_search_request")
        if isinstance(observed, Mapping)
        else None
    )

    if not isinstance(request, Mapping):
        return problems + ["canonical_request_missing"]

    if request.get("filters_present") is not True:
        problems.append("structured_filters_missing")

    if not _text(request.get("tenant_id")):
        problems.append("trusted_tenant_missing")

    identity = request.get("identity_sha256")
    if not isinstance(identity, str) or not SHA256.fullmatch(identity):
        problems.append("search_identity_invalid")

    criteria = request.get("structured_criteria")
    if not isinstance(criteria, Mapping):
        problems.append("structured_criteria_missing")
    else:
        missing_fields = [
            field for field in SEARCH_FIELDS if field not in criteria
        ]
        if missing_fields:
            problems.append(
                "structured_fields_missing:" + ",".join(missing_fields)
            )

        bedrooms = criteria.get("bedroom_count")
        lower = criteria.get("budget_min_minor")
        upper = criteria.get("budget_max_minor")

        if (
            isinstance(bedrooms, bool)
            or not isinstance(bedrooms, int)
            or bedrooms < 0
        ):
            problems.append("bedroom_count_invalid")

        if (
            isinstance(lower, bool)
            or not isinstance(lower, int)
            or lower < 0
            or isinstance(upper, bool)
            or not isinstance(upper, int)
            or upper < 1
            or (
                isinstance(lower, int)
                and isinstance(upper, int)
                and lower > upper
            )
        ):
            problems.append("budget_range_invalid")

        currency = criteria.get("currency")
        if (
            not isinstance(currency, str)
            or not CURRENCY.fullmatch(currency)
        ):
            problems.append("currency_invalid")

        if not _text(criteria.get("city_id")):
            problems.append("city_id_invalid")

        radius = criteria.get("transit_radius_m")
        if (
            isinstance(radius, bool)
            or not isinstance(radius, int)
            or not 1 <= radius <= 10000
        ):
            problems.append("transit_radius_invalid")

    unsupported = request.get("unsupported_criteria")
    if not isinstance(unsupported, list) or unsupported:
        problems.append("unsupported_criteria_present_or_unreported")

    if not _text(request.get("criteria_contract_version")):
        problems.append("criteria_contract_version_missing")

    return problems


def evaluate_production_readiness(
    report: Mapping[str, Any],
    attestation: Mapping[str, Any] | None,
    *,
    repository_root: str | Path,
    expected_commit: str | None = None,
    now_utc: datetime | None = None,
) -> dict[str, Any]:
    now = now_utc or datetime.now(timezone.utc)
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("now_utc must be timezone-aware")

    now = now.astimezone(timezone.utc)
    root = Path(repository_root).resolve()
    blockers: list[dict[str, str]] = []

    def block(code: str, detail: str) -> None:
        item = {"code": code, "detail": detail}
        if item not in blockers:
            blockers.append(item)

    if not isinstance(report, Mapping):
        report = {}
        block(
            "QUALITY_REPORT_INVALID",
            "Section 14 report must be a JSON object.",
        )

    meta = (
        report.get("run_metadata")
        if isinstance(report.get("run_metadata"), Mapping)
        else {}
    )
    commit = meta.get("commit_sha")

    if not isinstance(commit, str) or not SHA1.fullmatch(commit):
        block(
            "QUALITY_COMMIT_INVALID",
            "A full 40-character tested commit is required.",
        )

    if expected_commit and commit != expected_commit:
        block(
            "QUALITY_COMMIT_MISMATCH",
            "Report does not match the triggering commit.",
        )

    if meta.get("repository") != REPOSITORY:
        block(
            "REPOSITORY_NOT_CANONICAL",
            "Only the canonical HOMIO repository is accepted.",
        )

    if meta.get("branch") != BRANCH:
        block(
            "BRANCH_NOT_CANONICAL",
            "Only reos-development is accepted.",
        )

    summary = (
        report.get("summary")
        if isinstance(report.get("summary"), Mapping)
        else {}
    )
    count_fields = (
        "executable_cases",
        "passed_cases",
        "failed_cases",
        "blocked_cases",
    )

    for field in count_fields:
        value = summary.get(field)
        if (
            isinstance(value, bool)
            or not isinstance(value, int)
            or value < 0
        ):
            block("QUALITY_SUMMARY_INVALID", field)

    cases = report.get("cases")
    if not isinstance(cases, list):
        block(
            "QUALITY_CASES_MISSING",
            "Section 14 case records are missing.",
        )
        cases = []
    else:
        outcomes = Counter(
            case.get("outcome")
            for case in cases
            if isinstance(case, Mapping)
        )
        expected_counts = {
            "PASS": summary.get("passed_cases"),
            "FAIL": summary.get("failed_cases"),
            "BLOCKED": summary.get("blocked_cases"),
        }
        valid_counts = [
            value
            for value in expected_counts.values()
            if isinstance(value, int) and not isinstance(value, bool)
        ]
        if len(cases) != sum(valid_counts):
            block(
                "QUALITY_CASE_COUNT_MISMATCH",
                "Case records do not match summary totals.",
            )
        for outcome, count in expected_counts.items():
            if outcomes.get(outcome, 0) != count:
                block("QUALITY_OUTCOME_COUNT_MISMATCH", outcome)

    if summary.get("failed_cases") != 0:
        block(
            "QUALITY_REGRESSIONS_FAILED",
            "All executable Section 14 cases must pass.",
        )

    if summary.get("blocked_cases") != 0:
        block(
            "QUALITY_CASES_BLOCKED",
            "No Section 14 case may remain blocked.",
        )

    if summary.get("passed_cases") != summary.get("executable_cases"):
        block(
            "QUALITY_CASES_INCOMPLETE",
            "Every executable Section 14 case must pass.",
        )

    if summary.get("quality_thresholds_approved") is not True:
        block(
            "QUALITY_THRESHOLDS_NOT_APPROVED",
            "Approved thresholds are not recorded in the manifest.",
        )

    for reason in _check_q10(report):
        block("S14_Q10_STRUCTURED_SEARCH_NOT_VERIFIED", reason)

    verified_controls: list[str] = []

    if not isinstance(attestation, Mapping):
        block(
            "OPERATIONAL_ATTESTATION_MISSING",
            "Production attestation is absent or invalid JSON.",
        )
        for control in OPERATIONAL_CONTROLS:
            block("OPERATIONAL_CONTROL_NOT_VERIFIED", control)
        block(
            "QUALITY_APPROVAL_MISSING",
            "Numeric quality thresholds and approval evidence are required.",
        )
        block(
            "AVAILABILITY_SLO_MISSING",
            "Approved SLO and at least 30 days of measured evidence are required.",
        )
    else:
        if attestation.get("schema_version") != SCHEMA_VERSION:
            block("ATTESTATION_SCHEMA_INVALID", "Unsupported attestation schema.")

        if attestation.get("environment") != "production":
            block(
                "ATTESTATION_ENVIRONMENT_INVALID",
                "Attestation must be for production.",
            )

        if attestation.get("tested_commit_sha") != commit:
            block(
                "ATTESTATION_COMMIT_MISMATCH",
                "Operational evidence must match the exact tested commit.",
            )

        if (
            not _text(attestation.get("verified_by"))
            or not _fresh(attestation.get("verified_at_utc"), now)
        ):
            block(
                "ATTESTATION_VERIFIER_OR_TIMESTAMP_INVALID",
                "Attester and a fresh timestamp are required.",
            )

        quality = attestation.get("quality_thresholds")
        if not isinstance(quality, Mapping) or quality.get("status") != "APPROVED":
            block(
                "QUALITY_APPROVAL_MISSING",
                "Approved numeric quality thresholds are required.",
            )
        else:
            if (
                not all(
                    _text(quality.get(key))
                    for key in ("approval_reference", "approved_by")
                )
                or not _fresh(quality.get("approved_at_utc"), now)
            ):
                block(
                    "QUALITY_APPROVAL_INVALID",
                    "Quality approval reference, approver and fresh date are required.",
                )

            thresholds = quality.get("thresholds")
            measured = quality.get("measured_metrics")
            if not isinstance(thresholds, Mapping) or not isinstance(measured, Mapping):
                block(
                    "QUALITY_METRICS_MISSING",
                    "Approved thresholds and measured quality values are required.",
                )
            else:
                for metric in QUALITY_METRICS:
                    target = thresholds.get(metric)
                    value = measured.get(metric)

                    if not _number(target) or not 0 <= float(target) <= 1:
                        block("QUALITY_THRESHOLD_INVALID", metric)

                    if not _number(value) or not 0 <= float(value) <= 1:
                        block("QUALITY_MEASUREMENT_INVALID", metric)
                    elif _number(target) and float(value) < float(target):
                        block("QUALITY_THRESHOLD_NOT_MET", metric)

            ok, reason = _evidence_file(
                root,
                quality.get("evidence_path"),
                quality.get("evidence_sha256"),
            )
            if not ok:
                block("QUALITY_EVIDENCE_FILE_INVALID", reason)

        slo = attestation.get("availability_slo")
        if not isinstance(slo, Mapping) or slo.get("status") != "APPROVED":
            block(
                "AVAILABILITY_SLO_MISSING",
                "Approved availability SLO is required.",
            )
        else:
            if (
                not all(
                    _text(slo.get(key))
                    for key in ("approval_reference", "approved_by")
                )
                or not _fresh(slo.get("approved_at_utc"), now)
            ):
                block(
                    "AVAILABILITY_SLO_APPROVAL_INVALID",
                    "SLO approval reference, approver and fresh date are required.",
                )

            target = slo.get("target_percent")
            value = slo.get("measured_percent")
            window = slo.get("measurement_window_days")

            if not _number(target) or not 0 < float(target) <= 100:
                block(
                    "AVAILABILITY_TARGET_INVALID",
                    "SLO target must be in (0,100].",
                )

            if not _number(value) or not 0 <= float(value) <= 100:
                block(
                    "AVAILABILITY_MEASUREMENT_INVALID",
                    "Measured availability must be in [0,100].",
                )
            elif _number(target) and float(value) < float(target):
                block(
                    "AVAILABILITY_SLO_NOT_MET",
                    "Measured availability is below its approved target.",
                )

            if (
                isinstance(window, bool)
                or not isinstance(window, int)
                or window < 30
            ):
                block(
                    "AVAILABILITY_WINDOW_INVALID",
                    "At least 30 days of availability evidence are required.",
                )

            ok, reason = _evidence_file(
                root,
                slo.get("evidence_path"),
                slo.get("evidence_sha256"),
            )
            if not ok:
                block("AVAILABILITY_EVIDENCE_FILE_INVALID", reason)

        controls = attestation.get("controls")
        found: dict[str, Mapping[str, Any]] = {}

        if not isinstance(controls, list):
            controls = []
            block(
                "OPERATIONAL_CONTROLS_INVALID",
                "controls must be an explicit evidence list.",
            )

        for record in controls:
            if (
                not isinstance(record, Mapping)
                or not _text(record.get("control_id"))
            ):
                block(
                    "OPERATIONAL_CONTROL_RECORD_INVALID",
                    "Every control needs a control_id.",
                )
                continue

            key = record["control_id"].strip()
            if key in found:
                block("OPERATIONAL_CONTROL_DUPLICATE", key)
            else:
                found[key] = record

        for control in OPERATIONAL_CONTROLS:
            record = found.get(control)
            if record is None:
                block("OPERATIONAL_CONTROL_NOT_VERIFIED", control)
                continue

            reasons = []
            if record.get("status") != "VERIFIED":
                reasons.append("status_not_verified")
            if not _text(record.get("verified_by")):
                reasons.append("verified_by_missing")
            if not _fresh(record.get("verified_at_utc"), now):
                reasons.append("timestamp_stale_or_invalid")
            if (
                control in {
                    "provider_data_residency",
                    "data_retention_and_deletion",
                }
                and not _text(record.get("approval_reference"))
            ):
                reasons.append("approval_reference_missing")

            ok, reason = _evidence_file(
                root,
                record.get("evidence_path"),
                record.get("evidence_sha256"),
            )
            if not ok:
                reasons.append(reason)

            if reasons:
                for reason in reasons:
                    block(
                        "OPERATIONAL_CONTROL_EVIDENCE_INVALID",
                        f"{control}:{reason}",
                    )
            else:
                verified_controls.append(control)

    blockers.sort(key=lambda item: (item["code"], item["detail"]))
    ready = not blockers

    return {
        "schema_version": SCHEMA_VERSION,
        "gate_id": "HOMIO-AI-PRODUCTION-READINESS",
        "decision": (
            "READY_FOR_PRODUCTION_ENABLEMENT"
            if ready
            else "NOT_READY_FOR_PRODUCTION_ENABLEMENT"
        ),
        "release_ready": ready,
        "tested_commit_sha": commit if isinstance(commit, str) else None,
        "repository": meta.get("repository"),
        "branch": meta.get("branch"),
        "environment": (
            attestation.get("environment")
            if isinstance(attestation, Mapping)
            else None
        ),
        "evaluated_at_utc": now.isoformat(),
        "checks": {
            "synthetic_quality_suite": (
                summary.get("failed_cases") == 0
                and summary.get("blocked_cases") == 0
                and summary.get("passed_cases")
                == summary.get("executable_cases")
            ),
            "approved_quality_thresholds": (
                summary.get("quality_thresholds_approved") is True
                and isinstance(attestation, Mapping)
                and isinstance(attestation.get("quality_thresholds"), Mapping)
                and attestation["quality_thresholds"].get("status") == "APPROVED"
            ),
            "structured_property_search": not any(
                item["code"] == "S14_Q10_STRUCTURED_SEARCH_NOT_VERIFIED"
                for item in blockers
            ),
            "availability_slo": (
                isinstance(attestation, Mapping)
                and isinstance(attestation.get("availability_slo"), Mapping)
                and attestation["availability_slo"].get("status") == "APPROVED"
            ),
            "operational_controls": (
                len(verified_controls) == len(OPERATIONAL_CONTROLS)
            ),
        },
        "required_operational_controls": list(OPERATIONAL_CONTROLS),
        "verified_operational_controls": sorted(verified_controls),
        "blocker_count": len(blockers),
        "blockers": blockers,
        "limitations": [
            "Synthetic tests do not establish live-model quality.",
            "Evidence must match the exact tested commit and production environment.",
            "Evidence hashes detect file changes but do not authenticate the human approver; production deployment must additionally use protected GitHub Environment reviewers and administrator-controlled secrets.",
            "This gate does not provision infrastructure, monitoring, secrets, or rollback.",
        ],
    }


def update_quality_report(
    *,
    quality_report_path: str | Path,
    operational_evidence_path: str | Path,
    repository_root: str | Path,
    output_path: str | Path,
    expected_commit: str | None = None,
) -> dict[str, Any]:
    quality_path = Path(quality_report_path)
    evidence_path = Path(operational_evidence_path)

    try:
        report = json.loads(quality_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("Section 14 report is unreadable JSON.") from exc

    if not isinstance(report, dict):
        raise ValueError("Section 14 report root must be a JSON object.")

    try:
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        evidence = None
    except (OSError, json.JSONDecodeError):
        evidence = None

    gate = evaluate_production_readiness(
        report,
        evidence,
        repository_root=repository_root,
        expected_commit=expected_commit,
    )

    report["production_readiness"] = gate
    summary = report.setdefault("summary", {})
    if not isinstance(summary, dict):
        raise ValueError("Section 14 summary root must be a JSON object.")

    summary["release_ready"] = gate["release_ready"]
    summary["production_readiness_blocker_count"] = gate["blocker_count"]
    summary["production_readiness_blockers"] = gate["blockers"]

    output = (
        json.dumps(
            report,
            ensure_ascii=True,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n"
    )

    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + ".tmp")
    temporary.write_text(output, encoding="utf-8")
    temporary.replace(target)

    if quality_path.resolve() != target.resolve():
        temp = quality_path.with_suffix(quality_path.suffix + ".tmp")
        temp.write_text(output, encoding="utf-8")
        temp.replace(quality_path)

    return gate


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quality-report", required=True)
    parser.add_argument("--operational-evidence", required=True)
    parser.add_argument("--repository-root", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--expected-commit", default=None)
    parser.add_argument(
        "--enforce",
        action="store_true",
        help="Fail the deployment job when any release blocker remains.",
    )
    args = parser.parse_args(argv)

    try:
        gate = update_quality_report(
            quality_report_path=args.quality_report,
            operational_evidence_path=args.operational_evidence,
            repository_root=args.repository_root,
            output_path=args.output,
            expected_commit=args.expected_commit or None,
        )
    except ValueError as exc:
        print(
            f"PRODUCTION_READINESS_GATE_ERROR={type(exc).__name__}",
            file=sys.stderr,
        )
        return 2

    print(f"PRODUCTION_RELEASE_READY={str(gate['release_ready']).lower()}")
    print(f"PRODUCTION_RELEASE_BLOCKERS={gate['blocker_count']}")
    for item in gate["blockers"]:
        print(
            "PRODUCTION_RELEASE_BLOCKER="
            f"{item['code']}:{item['detail']}"
        )

    return 1 if args.enforce and not gate["release_ready"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
