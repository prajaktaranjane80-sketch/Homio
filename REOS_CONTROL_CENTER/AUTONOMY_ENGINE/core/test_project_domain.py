from __future__ import annotations

import pytest

from AUTONOMY_ENGINE.core.project import (
    Project,
    ProjectDomainError,
    ProjectLifecycle,
    ProjectLocation,
    ProjectOperatingMode,
    ProjectTenantViolation,
    ProjectTransitionError,
)


@pytest.fixture
def location() -> ProjectLocation:
    return ProjectLocation(
        country_code="in",
        region="Maharashtra",
        city="Pune",
        postal_code="411037",
    )


@pytest.fixture
def project(location: ProjectLocation) -> Project:
    return Project.create(
        tenant_id="tenant-001",
        developer_id="developer-001",
        project_code="PROJ-001",
        name="HOMIO Test Project",
        location=location,
        operating_mode=ProjectOperatingMode.BUILDER_SAAS,
        at="2026-08-28T10:00:00+00:00",
    )


def test_project_creation_is_draft_and_tenant_scoped(project: Project) -> None:
    assert project.lifecycle is ProjectLifecycle.DRAFT
    assert project.version == 1
    assert project.identity_key == "tenant-001:PROJ-001"
    assert project.source_of_truth == "project"


def test_project_supports_all_approved_operating_modes(location: ProjectLocation) -> None:
    for mode in ProjectOperatingMode:
        project = Project.create(
            tenant_id="tenant-001",
            developer_id="developer-001",
            project_code="PROJ-001",
            name="Mode Test",
            location=location,
            operating_mode=mode,
        )
        assert project.operating_mode is mode


def test_project_location_normalizes_country_code(location: ProjectLocation) -> None:
    assert location.country_code == "IN"
    assert location.city == "Pune"


@pytest.mark.parametrize("field_name", ["tenant_id", "developer_id", "project_code", "name"])
def test_required_fields_fail_closed(location: ProjectLocation, field_name: str) -> None:
    kwargs = dict(
        tenant_id="tenant-001",
        developer_id="developer-001",
        project_code="PROJ-001",
        name="Valid",
        location=location,
        operating_mode=ProjectOperatingMode.BUILDER_SAAS,
    )
    kwargs[field_name] = ""
    with pytest.raises(ProjectDomainError):
        Project.create(**kwargs)


@pytest.mark.parametrize("code", ["proj-001", "P", "bad code", "PROJ/001"])
def test_project_code_is_strictly_validated(location: ProjectLocation, code: str) -> None:
    with pytest.raises(ProjectDomainError):
        Project.create(
            tenant_id="tenant-001",
            developer_id="developer-001",
            project_code=code,
            name="Valid",
            location=location,
            operating_mode=ProjectOperatingMode.BUILDER_SAAS,
        )


def test_lifecycle_transition_is_deterministic_and_versioned(project: Project) -> None:
    updated, event = project.transition(
        ProjectLifecycle.ONBOARDING,
        tenant_id="tenant-001",
        at="2026-08-28T10:01:00+00:00",
    )
    assert updated.lifecycle is ProjectLifecycle.ONBOARDING
    assert updated.version == 2
    assert event.event_type == "PROJECT_LIFECYCLE_CHANGED"
    assert event.project_version == 2
    assert event.payload["from"] == "DRAFT"
    assert event.payload["to"] == "ONBOARDING"


def test_invalid_transition_is_blocked(project: Project) -> None:
    with pytest.raises(ProjectTransitionError):
        project.transition(ProjectLifecycle.ACTIVE, tenant_id="tenant-001")


def test_archived_project_is_terminal(project: Project) -> None:
    archived, _ = project.transition(
        ProjectLifecycle.ARCHIVED,
        tenant_id="tenant-001",
    )
    with pytest.raises(ProjectTransitionError):
        archived.transition(ProjectLifecycle.ACTIVE, tenant_id="tenant-001")


def test_cross_tenant_transition_is_blocked(project: Project) -> None:
    with pytest.raises(ProjectTenantViolation):
        project.transition(ProjectLifecycle.ONBOARDING, tenant_id="tenant-002")


def test_serialization_contains_authoritative_identity(project: Project) -> None:
    payload = project.to_dict()
    assert payload["project_id"] == project.project_id
    assert payload["tenant_id"] == "tenant-001"
    assert payload["developer_id"] == "developer-001"
    assert payload["lifecycle"] == "DRAFT"
    assert payload["operating_mode"] == "BUILDER_SAAS"
    assert payload["location"]["country_code"] == "IN"
    assert payload["source_of_truth"] == "project"


def test_transition_preserves_project_identity(project: Project) -> None:
    updated, _ = project.transition(
        ProjectLifecycle.ONBOARDING,
        tenant_id="tenant-001",
    )
    assert updated.project_id == project.project_id
    assert updated.tenant_id == project.tenant_id
    assert updated.developer_id == project.developer_id
    assert updated.project_code == project.project_code

