from pathlib import Path
import json


CONTRACT_PATH = (
    Path(__file__).resolve().parent
    / "t18.contract.json"
)


def test_t18_contract_exists():
    assert CONTRACT_PATH.is_file()


def test_t18_contract_schema():
    data = json.loads(
        CONTRACT_PATH.read_text(
            encoding="utf-8"
        )
    )

    assert data["layer"] == "T18"
    assert (
        data["name"]
        == "Safe Execution Authorization Guard"
    )
    assert data["schema_version"] == "1.0"
    assert data["mode"] == "authorization-only"


def test_t18_contract_forbids_execution_by_guard():
    data = json.loads(
        CONTRACT_PATH.read_text(
            encoding="utf-8"
        )
    )

    assert "business operation execution" in data["forbidden"]
    assert "state.json mutation" in data["forbidden"]
    assert "self approval" in data["forbidden"]


def test_t18_contract_has_required_upstream_layers():
    data = json.loads(
        CONTRACT_PATH.read_text(
            encoding="utf-8"
        )
    )

    assert "T15_AI_Operator_Autonomy" in data["upstream"]
    assert (
        "T17_Change_Impact_Dependency_Analysis"
        in data["upstream"]
    )
