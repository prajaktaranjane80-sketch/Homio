from __future__ import annotations

import copy
import unittest

from guarded_transition import (
    BASELINE_CONTRACT_BLOB_SHA,
    BASELINE_HEAD,
    BASELINE_MASTER_BLOB_SHA,
    BASELINE_STATE_BLOB_SHA,
    CONTRACT_PATH,
    controller,
    expected_subtask_statuses,
    read_state,
    validate_state,
    verify_contract,
)


class B3CanonicalTransitionContractTests(unittest.TestCase):
    @staticmethod
    def _rehash(state: dict) -> None:
        state["integrity"]["sha256"] = controller.calculate_hash(state)

    def test_baseline_is_pinned_to_the_live_b3_audit(self) -> None:
        self.assertEqual(len(BASELINE_HEAD), 40)
        self.assertEqual(len(BASELINE_STATE_BLOB_SHA), 40)
        self.assertEqual(len(BASELINE_MASTER_BLOB_SHA), 40)
        self.assertEqual(len(BASELINE_CONTRACT_BLOB_SHA), 40)
        self.assertTrue(CONTRACT_PATH.endswith("python-runtime/v1/contract.json"))

    def test_expected_statuses_close_only_b3_and_advance_to_b4(self) -> None:
        before = expected_subtask_statuses(transitioned=False)
        after = expected_subtask_statuses(transitioned=True)

        self.assertEqual(before["BACKEND-001-B3"], "CURRENT")
        self.assertEqual(before["BACKEND-001-B4"], "PENDING")
        self.assertEqual(after["BACKEND-001-B3"], "DONE")
        self.assertEqual(after["BACKEND-001-B4"], "CURRENT")
        self.assertEqual(after["BACKEND-001-B2-PRODUCTION-BINDING"], "PENDING")
        self.assertEqual(
            set(after),
            {
                "BACKEND-001-B0",
                "BACKEND-001-B1",
                "BACKEND-001-B2-FOUNDATION",
                "BACKEND-001-B3",
                "BACKEND-001-B4",
                "BACKEND-001-B2-PRODUCTION-BINDING",
                *(f"BACKEND-001-B{number}" for number in range(5, 11)),
            },
        )

    def test_live_canonical_state_passes_b3_pre_transition_validation(self) -> None:
        validate_state(read_state(), transitioned=False)

    def test_post_transition_projection_changes_only_b3_to_b4(self) -> None:
        state = copy.deepcopy(read_state())
        gate = state["gate_plans"]["BACKEND-001"]
        execution = state["execution"]
        subtasks = {item["id"]: item for item in gate["subtasks"]}

        subtasks["BACKEND-001-B3"]["status"] = "DONE"
        subtasks["BACKEND-001-B3"]["note"] = (
            "B3 completed; source SHA=0123456789abcdef0123456789abcdef01234567; "
            "run 987654321; mutations remain disabled until B4."
        )
        subtasks["BACKEND-001-B4"]["status"] = "CURRENT"
        gate["current_subtask"] = "BACKEND-001-B4"
        execution["current_subtask"] = "BACKEND-001-B4"
        execution["current_acceptance_criteria"] = subtasks["BACKEND-001-B4"]["acceptance_criteria"]
        execution["current_task"] = "BACKEND-001-B4: PostgreSQL integration."
        self._rehash(state)

        validate_state(
            state,
            transitioned=True,
            expected_sha="0123456789abcdef0123456789abcdef01234567",
            run_id="987654321",
        )

    def test_transition_rejects_any_gate_level_acceptance_change(self) -> None:
        state = copy.deepcopy(read_state())
        state["gate_plans"]["BACKEND-001"]["criteria_state"][0]["status"] = "VERIFIED"
        self._rehash(state)
        with self.assertRaises(SystemExit):
            validate_state(state, transitioned=False)

    def test_transition_rejects_mutating_b4_or_b2_production_order(self) -> None:
        state = copy.deepcopy(read_state())
        gate = state["gate_plans"]["BACKEND-001"]
        gate["subtasks"][4]["status"] = "CURRENT"
        self._rehash(state)
        with self.assertRaises(SystemExit):
            validate_state(state, transitioned=False)

    def test_read_only_contract_and_future_b4_prerequisites_are_valid(self) -> None:
        contract = verify_contract()
        self.assertFalse(contract["mutation_policy"]["enabled"])
        self.assertIsNone(contract["request_envelope"]["idempotency"])
        self.assertEqual(
            contract["mutation_policy"]["non_null_idempotency"],
            "reject with MUTATION_NOT_ENABLED",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
