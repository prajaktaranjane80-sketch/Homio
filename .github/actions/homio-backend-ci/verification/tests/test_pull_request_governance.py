
from __future__ import annotations

from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[5]
WORKFLOWS = ROOT / ".github" / "workflows"
VERIFICATION_ACTION = (
    ROOT
    / ".github"
    / "actions"
    / "homio-backend-ci"
    / "verification"
    / "action.yml"
)
GOVERNANCE_RUNBOOK = (
    ROOT
    / ".github"
    / "actions"
    / "homio-backend-ci"
    / "README.md"
)

BRANCH = "reos-development"
VERIFICATION_JOB_NAME = "Backend, T21, and ACRL runtime verification"
REQUIRED_CHECK_CONTEXT = (
    f"{VERIFICATION_JOB_NAME} / {VERIFICATION_JOB_NAME}"
)

TRANSITION_WORKFLOW_GLOBS = (
    "reusable-ai001-*.yml",
    "reusable-core008-*.yml",
)


def read(path: Path) -> str:
    assert path.is_file(), (
        f"Required governance source is missing: {path.relative_to(ROOT)}"
    )
    return path.read_text(encoding="utf-8")


def top_level_section(
    source: str,
    section_name: str,
    next_section_name: str,
) -> str:
    start_marker = f"  {section_name}:\n"
    end_marker = f"  {next_section_name}:\n"

    assert source.count(start_marker) == 1, (
        f"Expected exactly one top-level {section_name} section."
    )
    assert source.count(end_marker) == 1, (
        f"Expected exactly one top-level {next_section_name} section."
    )

    start = source.index(start_marker)
    end = source.index(end_marker, start + len(start_marker))
    assert end > start, f"Invalid YAML section order: {section_name}"
    return source[start:end]


def job_block(source: str, job_id: str) -> str:
    lines = source.splitlines()
    marker = f"  {job_id}:"

    positions = [
        index
        for index, line in enumerate(lines)
        if line == marker
    ]
    assert len(positions) == 1, (
        f"Expected exactly one workflow job named {job_id!r}."
    )

    start = positions[0]
    end = len(lines)
    for index in range(start + 1, len(lines)):
        if re.fullmatch(r"  [A-Za-z0-9_-]+:", lines[index]):
            end = index
            break

    return "\n".join(lines[start:end]) + "\n"


def test_pull_request_trigger_covers_every_change_to_canonical_branch() -> None:
    workflow = read(WORKFLOWS / "backend-ci.yml")
    pull_request = top_level_section(
        workflow,
        "pull_request",
        "workflow_dispatch",
    )

    assert f"      - {BRANCH}\n" in pull_request
    assert '      - "**"\n' in pull_request
    assert "paths:" in pull_request
    assert "paths-ignore:" not in pull_request
    assert "types:" not in pull_request

    # Pull requests must not use the elevated pull_request_target event.
    assert "pull_request_target:" not in workflow


def test_push_filter_remains_scoped_and_does_not_replace_pr_coverage() -> None:
    workflow = read(WORKFLOWS / "backend-ci.yml")
    push = top_level_section(workflow, "push", "pull_request")

    assert f"      - {BRANCH}\n" in push
    assert "    paths:\n" in push
    assert '      - "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/**"' in push
    assert '      - ".github/actions/homio-backend-ci/**"' in push


def test_pull_request_invokes_the_read_only_verification_job() -> None:
    workflow = read(WORKFLOWS / "backend-ci.yml")
    caller_job = job_block(workflow, "verification")

    assert (
        "uses: ./.github/workflows/reusable-backend-verification.yml"
        in caller_job
    )
    assert "permissions:\n      contents: read" in caller_job
    assert "if:" not in caller_job

    reusable = read(
        WORKFLOWS / "reusable-backend-verification.yml"
    )
    assert "workflow_call:" in reusable
    assert "permissions:\n  contents: read" in reusable

    verification_job = job_block(reusable, "verify")
    assert f"name: {VERIFICATION_JOB_NAME}" in verification_job
    assert "permissions:\n      contents: read" in verification_job
    assert "ref: ${{ github.sha }}" in verification_job


def test_required_check_context_matches_the_live_github_check_run_name() -> None:
    assert REQUIRED_CHECK_CONTEXT == (
        "Backend, T21, and ACRL runtime verification / "
        "Backend, T21, and ACRL runtime verification"
    )

    reusable = read(
        WORKFLOWS / "reusable-backend-verification.yml"
    )
    verification_job = job_block(reusable, "verify")
    assert f"name: {VERIFICATION_JOB_NAME}" in verification_job


def test_all_control_center_transition_jobs_are_push_only() -> None:
    workflow = read(WORKFLOWS / "backend-ci.yml")
    job_ids = re.findall(
        r"^  (control_center_[A-Za-z0-9_]+):$",
        workflow,
        flags=re.MULTILINE,
    )

    assert len(job_ids) >= 10, (
        "Expected the existing guarded Control Center transition inventory."
    )

    for job_id in job_ids:
        block = job_block(workflow, job_id)
        assert "github.event_name == 'push'" in block, job_id
        assert "github.ref == 'refs/heads/reos-development'" in block, job_id
        assert "startsWith(github.event.head_commit.message" in block, job_id
        assert "pull_request" not in block, job_id


def test_all_reusable_transition_workflows_keep_exact_push_guards() -> None:
    paths: list[Path] = []
    for pattern in TRANSITION_WORKFLOW_GLOBS:
        paths.extend(WORKFLOWS.glob(pattern))

    paths = sorted(set(paths))
    assert len(paths) >= 17, (
        "The reviewed AI-001 and CORE-008 transition/approval workflow "
        f"inventory changed: expected at least 17, found {len(paths)}."
    )

    for path in paths:
        workflow = read(path)
        assert "workflow_call:" in workflow, path.name

        guards = [
            line.strip()
            for line in workflow.splitlines()
            if line.lstrip().startswith("if:")
        ]
        assert len(guards) == 1, (
            f"{path.name} must have exactly one guarded transition condition."
        )

        guard = guards[0]
        assert "github.event_name == 'push'" in guard, path.name
        assert "github.ref == 'refs/heads/reos-development'" in guard, path.name
        assert "startsWith(github.event.head_commit.message" in guard, path.name
        assert "EXPECTED_SHA: ${{ github.sha }}" in workflow, path.name
        assert "VERIFIED_CODE_SHA: ${{ github.sha }}" in workflow, path.name


def test_verification_permissions_remain_read_only() -> None:
    workflow = read(WORKFLOWS / "backend-ci.yml")
    reusable = read(
        WORKFLOWS / "reusable-backend-verification.yml"
    )

    assert "permissions:\n  contents: read" in workflow
    assert "permissions:\n  contents: read" in reusable
    assert "permissions:\n      contents: read" in reusable

    # The read-only verification entry point must not receive write scope.
    verification = job_block(workflow, "verification")
    assert "contents: write" not in verification


def test_governance_test_is_wired_and_runbook_matches_the_live_check() -> None:
    action = read(VERIFICATION_ACTION)
    runbook = read(GOVERNANCE_RUNBOOK)

    test_path = (
        ".github/actions/homio-backend-ci/verification/tests/"
        "test_pull_request_governance.py"
    )
    assert test_path in action
    assert "Verify pull-request merge governance contract" in action
    assert REQUIRED_CHECK_CONTEXT in runbook
    assert "HOMIO-reos-development-protection" in runbook


def action_step_block(source: str, step_name: str) -> str:
    lines = source.splitlines()
    marker = f"    - name: {step_name}"

    positions = [
        index
        for index, line in enumerate(lines)
        if line == marker
    ]
    assert len(positions) == 1, (
        f"Expected exactly one composite-action step named {step_name!r}."
    )

    start = positions[0]
    end = len(lines)
    for index in range(start + 1, len(lines)):
        if re.fullmatch(r"    - name: .+", lines[index]):
            end = index
            break

    return "\n".join(lines[start:end]) + "\n"


def test_pull_request_cannot_restore_or_publish_trusted_t14_resume_cache() -> None:
    action = read(VERIFICATION_ACTION)

    protected_steps = {
        "Restore previous derived T14 audit resume cache": (
            "actions/cache/restore@",
        ),
        "Save refreshed external T14 resume cache": (
            "actions/cache/save@",
            "steps.restore_resume_cache.outputs.cache-hit != 'true'",
        ),
        "Seal and independently read back external T14 resume cache": (
            "audit_resume_manifest_cache.py",
            "--refresh-after-ci",
        ),
        "Publish sealed external T14 resume cache as run evidence": (
            "actions/upload-artifact@",
            "if-no-files-found: error",
        ),
    }

    required_guards = (
        "github.repository == 'prajaktaranjane80-sketch/Homio'",
        "github.ref == 'refs/heads/reos-development'",
        "github.event_name == 'push'",
        "github.event_name == 'workflow_dispatch'",
    )

    for step_name, required_contents in protected_steps.items():
        block = action_step_block(action, step_name)

        assert "      if: ${{" in block, (
            f"{step_name} must have an explicit execution guard."
        )

        for guard in required_guards:
            assert guard in block, (
                f"{step_name} is missing required trust-boundary guard: {guard}"
            )

        for required_content in required_contents:
            assert required_content in block, (
                f"{step_name} is missing expected operation contract: "
                f"{required_content}"
            )

    # Restore/save keys are scoped to the exact branch, commit, run, and attempt.
    cache_key = (
        "homio-acrl-resume-${{ github.ref_name }}-${{ github.sha }}-"
        "${{ github.run_id }}-${{ github.run_attempt }}"
    )
    for step_name in (
        "Restore previous derived T14 audit resume cache",
        "Save refreshed external T14 resume cache",
    ):
        block = action_step_block(action, step_name)
        assert cache_key in block, (
            f"{step_name} must use an exact-run cache key."
        )

def test_repository_write_permissions_are_limited_to_guarded_control_center_jobs() -> None:
    workflow = read(WORKFLOWS / "backend-ci.yml")

    job_ids = re.findall(
        r"^  ([A-Za-z0-9_-]+):$",
        workflow,
        flags=re.MULTILINE,
    )
    control_center_jobs = {
        job_id
        for job_id in job_ids
        if job_id.startswith("control_center_")
    }

    assert control_center_jobs, "Expected guarded Control Center jobs."

    write_permission_jobs: set[str] = set()

    for job_id in job_ids:
        block = job_block(workflow, job_id)

        if not re.search(
            r"^      contents: write$",
            block,
            flags=re.MULTILINE,
        ):
            continue

        write_permission_jobs.add(job_id)

        assert job_id.startswith("control_center_"), (
            f"Unexpected job has repository write permission: {job_id}"
        )
        assert "needs: verification" in block, job_id
        assert "github.event_name == 'push'" in block, job_id
        assert "github.ref == 'refs/heads/reos-development'" in block, job_id
        assert "startsWith(github.event.head_commit.message" in block, job_id

    assert write_permission_jobs == control_center_jobs, (
        "Repository write permission must remain limited to the guarded "
        "Control Center transition jobs."
    )
