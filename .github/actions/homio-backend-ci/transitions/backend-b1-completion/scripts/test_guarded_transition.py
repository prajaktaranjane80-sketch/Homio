from __future__ import annotations

import copy
import unittest

from guarded_transition import (
    expected_subtask_statuses,
    read_state,
    validate_state,
)


class CanonicalSubtaskIdentifierTests(unittest.TestCase):
    def test_expected_contract_uses_unpadded_ids(self) -> None:
        statuses = expected_subtask_statuses(
            transitioned=False
        )

        for number in range(3, 11):
            canonical_id = f"BACKEND-001-B{number}"
            padded_alias = f"BACKEND-001-B{number:02d}"

            self.assertIn(canonical_id, statuses)
            self.assertNotIn(padded_alias, statuses)

    def test_expected_contract_contains_exactly_b0_through_b10(
        self,
    ) -> None:
        statuses = expected_subtask_statuses(
            transitioned=False
        )

        expected_ids = {
            f"BACKEND-001-B{number}"
            for number in range(0, 11)
        }

        self.assertEqual(set(statuses), expected_ids)

    def test_live_canonical_state_passes_pre_transition_validation(
        self,
    ) -> None:
        state = read_state()

        validate_state(
            state,
            transitioned=False,
        )

    def test_transitioned_state_contract_is_validated(self) -> None:
        state = copy.deepcopy(read_state())

        gate = state["gate_plans"]["BACKEND-001"]
        execution = state["execution"]

        subtasks = {
            item["id"]: item
            for item in gate["subtasks"]
        }

        subtasks["BACKEND-001-B1"]["status"] = "DONE"
        subtasks["BACKEND-001-B1"]["note"] = (
            "Verified test transition "
            "SHA=0123456789abcdef "
            "RUN=987654321"
        )

        subtasks["BACKEND-001-B2"]["status"] = "CURRENT"

        gate["current_subtask"] = "BACKEND-001-B2"
        execution["current_subtask"] = "BACKEND-001-B2"

        validate_state(
            state,
            transitioned=True,
            expected_sha="0123456789abcdef",
            run_id="987654321",
        )

    def test_zero_padded_alias_is_rejected(self) -> None:
        state = copy.deepcopy(read_state())

        gate = state["gate_plans"]["BACKEND-001"]

        canonical_b3 = next(
            item
            for item in gate["subtasks"]
            if item["id"] == "BACKEND-001-B3"
        )

        canonical_b3["id"] = "BACKEND-001-B03"

        with self.assertRaisesRegex(
            SystemExit,
            "canonical subtask identifier set mismatch",
        ):
            validate_state(
                state,
                transitioned=False,
            )

    def test_duplicate_subtask_identifier_is_rejected(self) -> None:
        state = copy.deepcopy(read_state())

        gate = state["gate_plans"]["BACKEND-001"]
        duplicate = copy.deepcopy(
            next(
                item
                for item in gate["subtasks"]
                if item["id"] == "BACKEND-001-B3"
            )
        )

        gate["subtasks"].append(duplicate)

        with self.assertRaisesRegex(
            SystemExit,
            "duplicate subtask identifiers",
        ):
            validate_state(
                state,
                transitioned=False,
            )

    def test_additional_padded_alias_is_rejected(self) -> None:
        state = copy.deepcopy(read_state())

        gate = state["gate_plans"]["BACKEND-001"]
        alias = copy.deepcopy(
            next(
                item
                for item in gate["subtasks"]
                if item["id"] == "BACKEND-001-B3"
            )
        )

        alias["id"] = "BACKEND-001-B03"
        gate["subtasks"].append(alias)

        with self.assertRaisesRegex(
            SystemExit,
            "canonical subtask identifier set mismatch",
        ):
            validate_state(
                state,
                transitioned=False,
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
