from pathlib import Path
import json

CONTRACT = Path(
    "AUTONOMY_ENGINE/core/identity_tenant/identity_contract.json"
)

def _load_contract():
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


def test_machine_contract_exists_and_is_valid():
    contract = _load_contract()

    assert contract["contract"]["domain"] == "CORE-001"
    assert contract["contract"]["subtask"] == "CORE-001-T01"
    assert contract["contract"]["status"] == "ACTIVE"


def test_machine_contract_contains_all_identity_types():
    from AUTONOMY_ENGINE.core.identity_tenant.identity import IdentityType

    contract = _load_contract()

    assert contract["entities"]["Identity"]["identity_types"] == [
        x.value for x in IdentityType
    ]


def test_machine_contract_contains_identity_fields():
    from dataclasses import fields
    from AUTONOMY_ENGINE.core.identity_tenant.identity import Identity

    contract = _load_contract()

    assert contract["entities"]["Identity"]["fields"] == [
        f.name for f in fields(Identity)
    ]


def test_machine_contract_contains_external_identity_contract():
    from dataclasses import fields
    from AUTONOMY_ENGINE.core.identity_tenant.identity import (
        ExternalIdentityReference,
    )

    contract = _load_contract()

    assert contract["entities"]["ExternalIdentityReference"]["fields"] == [
        f.name for f in fields(ExternalIdentityReference)
    ]

    assert contract["entities"]["ExternalIdentityReference"]["key"] == [
        "provider",
        "subject",
    ]


def test_machine_contract_contains_fail_closed_security_invariants():
    contract = _load_contract()

    invariants = set(contract["security_invariants"])

    required = {
        "duplicate_external_binding_cannot_rebind_identity",
        "unknown_external_identity_fails_closed",
        "revoked_external_identity_fails_closed",
        "inactive_canonical_identity_fails_closed",
    }

    assert required.issubset(invariants)


def test_machine_contract_resolution_outcomes_match_runtime():
    from AUTONOMY_ENGINE.core.identity_tenant.identity import (
        IdentityResolutionStatus,
    )

    contract = _load_contract()

    assert contract["resolution_outcomes"] == [
        x.value for x in IdentityResolutionStatus
    ]
