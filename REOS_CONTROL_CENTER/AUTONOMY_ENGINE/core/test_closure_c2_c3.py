from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import subprocess
import sys

import pytest

from AUTONOMY_ENGINE.core import (
    CORE_PACKAGE_NAMES,
    get_core_package,
    iter_core_packages,
)
from AUTONOMY_ENGINE.core.commission_financial.commission_calculation import (
    CommissionCalculation,
    CommissionCalculationState,
)
from AUTONOMY_ENGINE.core.commission_financial.financial_domain import (
    Currency,
    MonetaryAmount,
)
from AUTONOMY_ENGINE.core.deal_transaction.deal_evidence_audit import (
    DealAuditEntry,
)


EXPECTED_CORE_PACKAGES = (
    "identity_tenant",
    "event_platform",
    "lead_ownership",
    "inventory",
    "search_matching",
    "deal_transaction",
    "trust_fraud_governance",
    "commission_financial",
)


def _run_python(script: str) -> subprocess.CompletedProcess[str]:
    control_center_root = (
        Path(__file__).resolve().parents[2]
    )

    return subprocess.run(
        [
            sys.executable,
            "-c",
            script,
        ],
        cwd=control_center_root,
        capture_output=True,
        text=True,
        check=False,
    )


def _make_deal_audit(
    metadata: dict,
) -> DealAuditEntry:
    return DealAuditEntry.create(
        deal_id="deal-001",
        tenant_id="tenant-001",
        action="VISIT_RECORDED",
        actor_id="actor-001",
        deal_version=1,
        audit_id="audit-001",
        metadata=metadata,
        at=datetime(
            2026,
            10,
            3,
            10,
            0,
            tzinfo=timezone.utc,
        ),
    )


def _make_commission_calculation(
    metadata: dict,
) -> CommissionCalculation:
    currency = Currency(
        code="USD",
        minor_unit=2,
    )

    amount = MonetaryAmount.create(
        "1000.00",
        currency,
    )

    return CommissionCalculation(
        calculation_id="calc-001",
        tenant_id="tenant-001",
        commission_id="commission-001",
        contract_version=1,
        calculation_version=1,
        basis_reference="basis-001",
        source_reference="deal-001",
        formula_code="PERCENTAGE_OF_BASIS",
        basis_amount=amount,
        commission_amount=MonetaryAmount.create(
            "100.00",
            currency,
        ),
        calculated_at=datetime(
            2026,
            10,
            3,
            10,
            0,
            tzinfo=timezone.utc,
        ),
        eligibility_reference="eligibility-001",
        provenance_reference="provenance-001",
        idempotency_key="idem-001",
        state=CommissionCalculationState.CALCULATED,
        metadata=metadata,
    )


def test_core_root_does_not_eagerly_load_bounded_packages() -> None:
    script = """
import sys

expected = (
    "identity_tenant",
    "event_platform",
    "lead_ownership",
    "inventory",
    "search_matching",
    "deal_transaction",
    "trust_fraud_governance",
    "commission_financial",
)

import AUTONOMY_ENGINE.core as core

assert core.iter_core_packages() == expected
assert core.CORE_PACKAGE_NAMES == expected

for package_name in expected:
    assert (
        f"AUTONOMY_ENGINE.core.{package_name}"
        not in sys.modules
    )

core.get_core_package("inventory")

assert (
    "AUTONOMY_ENGINE.core.inventory"
    in sys.modules
)
"""

    result = _run_python(
        script
    )

    assert result.returncode == 0, (
        result.stdout
        + result.stderr
    )


def test_core_root_rejects_unknown_package() -> None:
    assert (
        iter_core_packages()
        == EXPECTED_CORE_PACKAGES
    )

    assert (
        CORE_PACKAGE_NAMES
        == EXPECTED_CORE_PACKAGES
    )

    with pytest.raises(ValueError):
        get_core_package(
            "unknown_core_package"
        )


def test_legacy_inventory_export_remains_compatible() -> None:
    script = """
from AUTONOMY_ENGINE.core import Inventory

assert Inventory is not None
"""

    result = _run_python(
        script
    )

    assert result.returncode == 0, (
        result.stdout
        + result.stderr
    )


def test_deal_audit_metadata_is_deeply_immutable() -> None:
    source = {
        "proof": {
            "events": [
                {
                    "kind": "visit",
                    "attributes": {
                        "source": "broker",
                    },
                }
            ]
        }
    }

    audit = _make_deal_audit(
        source
    )

    source["proof"]["events"][0][
        "attributes"
    ]["source"] = "tampered"

    assert (
        audit.metadata["proof"]["events"][0][
            "attributes"
        ]["source"]
        == "broker"
    )

    with pytest.raises(TypeError):
        audit.metadata["proof"] = {}

    with pytest.raises(TypeError):
        audit.metadata["proof"]["events"][0][
            "attributes"
        ]["source"] = "tampered"

    with pytest.raises(AttributeError):
        audit.metadata["proof"]["events"].append(
            {"kind": "tampered"}
        )

    serialized = audit.to_dict()

    serialized["metadata"]["proof"]["events"][0][
        "attributes"
    ]["source"] = "serialized-tamper"

    assert (
        audit.to_dict()["metadata"]["proof"]["events"][0][
            "attributes"
        ]["source"]
        == "broker"
    )


def test_deal_audit_serialization_round_trip_is_stable() -> None:
    metadata = {
        "proof": {
            "events": [
                {
                    "kind": "visit",
                    "attributes": {
                        "source": "broker",
                    },
                }
            ]
        }
    }

    audit = _make_deal_audit(
        metadata
    )

    first = audit.to_dict()
    second = audit.to_dict()

    assert first == second
    assert (
        audit.semantic_key()
        == _make_deal_audit(metadata).semantic_key()
    )


def test_commission_metadata_is_deeply_immutable() -> None:
    source = {
        "calculation": {
            "inputs": [
                {
                    "basis": "1000.00",
                    "currency": {
                        "code": "USD",
                    },
                }
            ]
        }
    }

    calculation = _make_commission_calculation(
        source
    )

    source["calculation"]["inputs"][0][
        "basis"
    ] = "9999.00"

    assert (
        calculation.metadata["calculation"]["inputs"][0][
            "basis"
        ]
        == "1000.00"
    )

    with pytest.raises(TypeError):
        calculation.metadata["calculation"] = {}

    with pytest.raises(TypeError):
        calculation.metadata["calculation"]["inputs"][0][
            "basis"
        ] = "tampered"

    with pytest.raises(AttributeError):
        calculation.metadata["calculation"]["inputs"].append(
            {"basis": "tampered"}
        )


def test_commission_fingerprint_and_serialization_remain_stable() -> None:
    metadata = {
        "calculation": {
            "inputs": [
                {
                    "basis": "1000.00",
                    "currency": {
                        "code": "USD",
                    },
                }
            ]
        }
    }

    calculation = _make_commission_calculation(
        metadata
    )

    fingerprint_before = (
        calculation.immutable_fingerprint
    )

    serialized = calculation.to_dict()

    serialized["metadata"]["calculation"]["inputs"][0][
        "basis"
    ] = "tampered"

    assert (
        calculation.immutable_fingerprint
        == fingerprint_before
    )

    assert (
        calculation.to_dict()["metadata"][
            "calculation"
        ]["inputs"][0]["basis"]
        == "1000.00"
    )

    assert (
        calculation.to_dict(
            include_fingerprint=False
        )["metadata"]
        == {
            "calculation": {
                "inputs": [
                    {
                        "basis": "1000.00",
                        "currency": {
                            "code": "USD",
                        },
                    }
                ]
            }
        }
    )


def test_commission_state_and_identity_remain_unchanged_after_hardening() -> None:
    calculation = _make_commission_calculation(
        {
            "source": "closure-test",
        }
    )

    assert calculation.state is (
        CommissionCalculationState.CALCULATED
    )

    assert calculation.identity_key == (
        "tenant-001",
        "commission-001",
        1,
        1,
    )
