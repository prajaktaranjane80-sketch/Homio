from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent

ACTIVATION_SCRIPT_PATH = (
    SCRIPT_DIR / "activate_backend_workstream.py"
)

EVIDENCE_ONLY_ACTIVATION_PATHS = frozenset(
    {
        "REOS_CONTROL_CENTER/PS Output",
    }
)


REPAIRED_ACTIVATION_PATHS = {
    ".github/actions/homio-backend-ci/transitions/"
    "backend-workstream-activation/action.yml",
    ".github/actions/homio-backend-ci/transitions/"
    "backend-workstream-activation/scripts/"
    "activate_backend_workstream.py",
    ".github/actions/homio-backend-ci/transitions/"
    "backend-workstream-activation/scripts/"
    "activate_backend_workstream_wrapper.py",
    ".github/workflows/backend-ci.yml",
    ".github/workflows/reusable-backend-workstream-activation.yml",
    "REOS_CONTROL_CENTER/context/phase_projection.py",
    "REOS_CONTROL_CENTER/context/test_phase_projection.py",
    "REOS_CONTROL_CENTER/context/backend_workstream_transition.py",
    "REOS_CONTROL_CENTER/context/test_backend_workstream_transition.py",
    "REOS_CONTROL_CENTER/context/github_actions_identity.py",
    "REOS_CONTROL_CENTER/context/test_github_actions_identity.py",
    "REOS_CONTROL_CENTER/context/test_backend_control_projection.py",
    "REOS_CONTROL_CENTER/reos_control_center.py",
    "REOS_CONTROL_CENTER/evidence/BACKEND-001/"
    "B0-live-repository-audit.md",
    ".github/actions/homio-backend-ci/verification/scripts/"
    "financial_context_tenant.sh",
    ".github/actions/homio-backend-ci/verification/scripts/"
    "wiring_tests.sh",
    "REOS_CONTROL_CENTER/context/"
    "test_backend_activation_import_bootstrap.py",
    "REOS_CONTROL_CENTER/PS Output",
    "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/continuity/acrl/"
    "T17_Change_Impact_Dependency_Analysis/change_impact_analysis.py",
    "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/continuity/acrl/"
    "T17_Change_Impact_Dependency_Analysis/test_change_impact_analysis.py",
}


def source_paths_for_t17(
    changed_paths,
) -> list[str]:
    """Exclude only the one canonical evidence-only diagnostic path."""

    return sorted(
        path
        for path in changed_paths
        if path not in EVIDENCE_ONLY_ACTIVATION_PATHS
    )


def _load_original_activation():
    if not ACTIVATION_SCRIPT_PATH.is_file():
        raise FileNotFoundError(
            f"Existing activation engine is missing: "
            f"{ACTIVATION_SCRIPT_PATH}"
        )

    spec = importlib.util.spec_from_file_location(
        "homio_backend_activation_runtime",
        ACTIVATION_SCRIPT_PATH,
    )

    if spec is None or spec.loader is None:
        raise RuntimeError(
            "Could not load the existing BACKEND-001 activation engine."
        )

    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    return module


def load_guarded_activation():
    """Load and apply the exact reviewed compatibility boundary."""

    module = _load_original_activation()

    legacy_paths = set(module.EXPECTED_ACTIVATION_PATHS)

    expected_legacy_paths = set(REPAIRED_ACTIVATION_PATHS)

    expected_legacy_paths.discard(
        "REOS_CONTROL_CENTER/reos_control_center.py"
    )
    expected_legacy_paths.discard(
        "REOS_CONTROL_CENTER/PS Output"
    )
    expected_legacy_paths.discard(
        "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/continuity/acrl/"
        "T17_Change_Impact_Dependency_Analysis/change_impact_analysis.py"
    )
    expected_legacy_paths.discard(
        "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/continuity/acrl/"
        "T17_Change_Impact_Dependency_Analysis/test_change_impact_analysis.py"
    )
    expected_legacy_paths.discard(
        ".github/actions/homio-backend-ci/transitions/"
        "backend-workstream-activation/scripts/"
        "activate_backend_workstream_wrapper.py"
    )

    expected_legacy_paths.add(
        "REOS_CONTROL_CENTER/context/reos_control_center.py"
    )

    if legacy_paths != expected_legacy_paths:
        module.fail(
            "Legacy activation allowlist changed unexpectedly; "
            "wrapper will not silently override it."
        )

    # The corrected inventory is now the only allowlist used by
    # verify_repository_baseline().
    module.EXPECTED_ACTIVATION_PATHS = set(
        REPAIRED_ACTIVATION_PATHS
    )

    original_authorize = module.authorize_activation

    def guarded_authorize_activation(
        *,
        expected_sha,
        state,
        changed_paths,
        owner_event,
    ):
        all_changed_paths = sorted(
            set(changed_paths)
        )

        evidence_only_paths = sorted(
            set(all_changed_paths)
            & set(EVIDENCE_ONLY_ACTIVATION_PATHS)
        )

        source_paths = source_paths_for_t17(
            all_changed_paths
        )

        if not source_paths:
            module.fail(
                "No source-code paths remain for T17 impact analysis."
            )

        result = original_authorize(
            expected_sha=expected_sha,
            state=state,
            changed_paths=source_paths,
            owner_event=owner_event,
        )

        operator_report, impact_report, authorization, approval_record = (
            result
        )

        safe_approval_record = dict(
            approval_record
        )

        safe_approval_record[
            "evidence_only_changed_paths"
        ] = evidence_only_paths

        return (
            operator_report,
            impact_report,
            authorization,
            safe_approval_record,
        )

    module.authorize_activation = guarded_authorize_activation

    original_evidence_writer = (
        module.write_activation_evidence
    )

    def write_activation_evidence_with_scope_note(
        *args,
        **kwargs,
    ):
        original_evidence_writer(
            *args,
            **kwargs,
        )

        approval_record = kwargs.get(
            "approval_record",
            {},
        )

        evidence_only_paths = approval_record.get(
            "evidence_only_changed_paths",
            [],
        )

        if not evidence_only_paths:
            return

        evidence_path = (
            module.ROOT
            / module.ACTIVATION_EVIDENCE_PATH
        )

        with evidence_path.open(
            "a",
            encoding="utf-8",
            newline="\n",
        ) as stream:
            stream.write(
                "\n## Evidence-only repository changes\n\n"
            )

            for relative_path in evidence_only_paths:
                stream.write(
                    f"- `{relative_path}` was retained in the "
                    "activation source inventory and excluded from "
                    "T17 source-code impact analysis by the exact "
                    "evidence-only path policy.\n"
                )

    module.write_activation_evidence = (
        write_activation_evidence_with_scope_note
    )

    return module


def main() -> None:
    activation = load_guarded_activation()
    activation.main()


if __name__ == "__main__":
    main()
