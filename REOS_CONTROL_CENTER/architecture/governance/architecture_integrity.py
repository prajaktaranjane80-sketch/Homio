from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


CANONICAL_ARCHITECTURE_FILENAME = (
    "HOMIO_REOS_MASTER_ARCHITECTURE.json"
)

EXPECTED_ARCHITECTURE_ID = "ARCH-039"
EXPECTED_ARCHITECTURE_NAME = "HOMIO / REOS Master Architecture"
EXPECTED_SCHEMA_VERSION = "1.0"
EXPECTED_MASTER_VERSION = "1.0"
EXPECTED_CONTENT_STATUS = "FINAL_ARCHITECTURE_CONTENT"

VALID_NODE_STATUSES = frozenset(
    {
        "APPROVED",
        "PENDING",
    }
)

EXPECTED_ARCHITECTURE_IDS = tuple(
    f"ARCH-{index:03d}"
    for index in range(1, 40)
)

EXPECTED_GRAPH_IDS = frozenset(
    {
        "GRAPH-001",
        "GRAPH-002",
        "GRAPH-003",
        "GRAPH-004",
        "GRAPH-005",
        "GRAPH-006",
    }
)

REQUIRED_AUTHORITY_VALUES = {
    "architecture_source": "This file",
    "execution_state": "REOS_CONTROL_CENTER/data/state.json",
    "execution_templates": "REOS_CONTROL_CENTER/GATE_TEMPLATES.json",
    "code_truth": "Git repository",
    "continuity_truth": (
        "ACRL derived from canonical machine state "
        "and repository evidence"
    ),
    "chat_is_authority": False,
    "parallel_master_architecture_forbidden": True,
}

REQUIRED_GLOBAL_INVARIANTS = frozenset(
    {
        "One authoritative source per business responsibility",
        "No duplicate domain logic",
        "Derived views remain rebuildable",
    }
)


@dataclass(frozen=True)
class IntegrityIssue:
    code: str
    message: str
    path: str | None = None

    def to_dict(self) -> dict[str, str | None]:
        return {
            "code": self.code,
            "message": self.message,
            "path": self.path,
        }


@dataclass(frozen=True)
class IntegrityReport:
    ok: bool
    issues: tuple[IntegrityIssue, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "issue_count": len(self.issues),
            "issues": [
                issue.to_dict()
                for issue in self.issues
            ],
        }

    def raise_if_invalid(self) -> None:
        if self.ok:
            return

        messages = "\n".join(
            (
                f"[{issue.code}] "
                f"{issue.message}"
            )
            for issue in self.issues
        )

        raise ArchitectureIntegrityError(messages)


class ArchitectureIntegrityError(
    RuntimeError
):
    """Raised when canonical architecture integrity fails."""


def _load_json(path: Path) -> Any:
    if not path.exists():
        raise ArchitectureIntegrityError(
            f"Required JSON file missing: {path}"
        )

    try:
        return json.loads(
            path.read_text(
                encoding="utf-8"
            ).lstrip("\ufeff")
        )
    except OSError as exc:
        raise ArchitectureIntegrityError(
            f"JSON read failure: {path}: {exc}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise ArchitectureIntegrityError(
            f"Strict JSON parse failure: {path}: {exc}"
        ) from exc


def _duplicate_values(
    values: Iterable[str],
) -> set[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()

    for value in values:
        if value in seen:
            duplicates.add(value)
        else:
            seen.add(value)

    return duplicates


def _architecture_nodes(
    architecture: dict[str, Any],
) -> list[dict[str, Any]]:
    nodes = architecture.get(
        "architecture_nodes"
    )

    if not isinstance(nodes, list):
        return []

    return [
        node
        for node in nodes
        if isinstance(node, dict)
    ]


def validate_master_architecture(
    architecture: Any,
) -> IntegrityReport:
    issues: list[IntegrityIssue] = []

    if not isinstance(
        architecture,
        dict,
    ):
        return IntegrityReport(
            ok=False,
            issues=(
                IntegrityIssue(
                    "ROOT_NOT_OBJECT",
                    "Master Architecture root must be an object.",
                ),
            ),
        )

    if architecture.get(
        "schema_version"
    ) != EXPECTED_SCHEMA_VERSION:
        issues.append(
            IntegrityIssue(
                "INVALID_SCHEMA_VERSION",
                (
                    "Master Architecture schema_version "
                    f"must be {EXPECTED_SCHEMA_VERSION}."
                ),
                "schema_version",
            )
        )

    if architecture.get(
        "architecture_id"
    ) != EXPECTED_ARCHITECTURE_ID:
        issues.append(
            IntegrityIssue(
                "INVALID_ARCHITECTURE_ID",
                (
                    "architecture_id must be "
                    f"{EXPECTED_ARCHITECTURE_ID}."
                ),
                "architecture_id",
            )
        )

    if architecture.get(
        "name"
    ) != EXPECTED_ARCHITECTURE_NAME:
        issues.append(
            IntegrityIssue(
                "INVALID_ARCHITECTURE_NAME",
                "Canonical Master Architecture name is incorrect.",
                "name",
            )
        )

    if architecture.get(
        "version"
    ) != EXPECTED_MASTER_VERSION:
        issues.append(
            IntegrityIssue(
                "INVALID_ARCHITECTURE_VERSION",
                (
                    "Master Architecture version must be "
                    f"{EXPECTED_MASTER_VERSION}."
                ),
                "version",
            )
        )

    if architecture.get(
        "status"
    ) != EXPECTED_CONTENT_STATUS:
        issues.append(
            IntegrityIssue(
                "INVALID_CONTENT_STATUS",
                (
                    "Top-level architecture status must remain "
                    f"{EXPECTED_CONTENT_STATUS}. "
                    "Freeze/approval authority belongs to state."
                ),
                "status",
            )
        )

    authority = architecture.get(
        "authority"
    )

    if not isinstance(
        authority,
        dict,
    ):
        issues.append(
            IntegrityIssue(
                "AUTHORITY_SECTION_MISSING",
                "Canonical authority section is required.",
                "authority",
            )
        )
    else:
        for key, expected in (
            REQUIRED_AUTHORITY_VALUES.items()
        ):
            if authority.get(key) != expected:
                issues.append(
                    IntegrityIssue(
                        "INVALID_AUTHORITY_VALUE",
                        (
                            f"authority.{key} does not match "
                            "the canonical authority contract."
                        ),
                        f"authority.{key}",
                    )
                )

        if authority.get("role") != (
            "Single canonical architectural blueprint "
            "for HOMIO / REOS."
        ):
            issues.append(
                IntegrityIssue(
                    "INVALID_AUTHORITY_ROLE",
                    "Canonical architecture role is missing or incorrect.",
                    "authority.role",
                )
            )

    nodes_raw = architecture.get(
        "architecture_nodes"
    )

    if not isinstance(
        nodes_raw,
        list,
    ):
        issues.append(
            IntegrityIssue(
                "ARCHITECTURE_NODES_MISSING",
                "architecture_nodes must be a list.",
                "architecture_nodes",
            )
        )
        nodes_raw = []

    node_ids: list[str] = []

    for index, node in enumerate(
        nodes_raw
    ):
        if not isinstance(
            node,
            dict,
        ):
            issues.append(
                IntegrityIssue(
                    "INVALID_NODE_OBJECT",
                    "Architecture node must be an object.",
                    f"architecture_nodes[{index}]",
                )
            )
            continue

        node_id = node.get("id")
        node_name = node.get("name")
        node_status = node.get("status")

        if not isinstance(
            node_id,
            str,
        ) or not node_id:
            issues.append(
                IntegrityIssue(
                    "NODE_ID_MISSING",
                    "Architecture node id is required.",
                    f"architecture_nodes[{index}].id",
                )
            )
            continue

        node_ids.append(node_id)

        if not isinstance(
            node_name,
            str,
        ) or not node_name.strip():
            issues.append(
                IntegrityIssue(
                    "NODE_NAME_MISSING",
                    "Architecture node name is required.",
                    f"architecture_nodes[{index}].name",
                )
            )

        if node_status not in VALID_NODE_STATUSES:
            issues.append(
                IntegrityIssue(
                    "INVALID_NODE_STATUS",
                    (
                        f"Node {node_id} has invalid status "
                        f"{node_status!r}."
                    ),
                    f"architecture_nodes[{index}].status",
                )
            )

    for duplicate in sorted(
        _duplicate_values(node_ids)
    ):
        issues.append(
            IntegrityIssue(
                "DUPLICATE_NODE_ID",
                (
                    f"Architecture node id {duplicate} "
                    "appears more than once."
                ),
                "architecture_nodes",
            )
        )

    node_id_set = set(node_ids)

    for required_id in EXPECTED_ARCHITECTURE_IDS:
        if required_id not in node_id_set:
            issues.append(
                IntegrityIssue(
                    "MANDATORY_NODE_MISSING",
                    (
                        f"Mandatory architecture node "
                        f"{required_id} is missing."
                    ),
                    "architecture_nodes",
                )
            )

    unexpected_ids = sorted(
        node_id_set
        - set(EXPECTED_ARCHITECTURE_IDS)
    )

    for unexpected_id in unexpected_ids:
        issues.append(
            IntegrityIssue(
                "UNEXPECTED_ARCHITECTURE_NODE",
                (
                    f"Unexpected top-level architecture node "
                    f"{unexpected_id} detected."
                ),
                "architecture_nodes",
            )
        )

    graphs = architecture.get(
        "canonical_graphs"
    )

    if not isinstance(
        graphs,
        list,
    ):
        issues.append(
            IntegrityIssue(
                "CANONICAL_GRAPHS_MISSING",
                "canonical_graphs must be a list.",
                "canonical_graphs",
            )
        )
        graph_ids: set[str] = set()
    else:
        graph_ids = {
            item.get("id")
            for item in graphs
            if isinstance(
                item,
                dict,
            )
            and isinstance(
                item.get("id"),
                str,
            )
        }

        for duplicate in sorted(
            _duplicate_values(
                item.get("id")
                for item in graphs
                if isinstance(
                    item,
                    dict,
                )
                and isinstance(
                    item.get("id"),
                    str,
                )
            )
        ):
            issues.append(
                IntegrityIssue(
                    "DUPLICATE_GRAPH_ID",
                    (
                        f"Canonical graph id {duplicate} "
                        "appears more than once."
                    ),
                    "canonical_graphs",
                )
            )

    for graph_id in sorted(
        EXPECTED_GRAPH_IDS - graph_ids
    ):
        issues.append(
            IntegrityIssue(
                "MANDATORY_GRAPH_MISSING",
                f"Mandatory graph {graph_id} is missing.",
                "canonical_graphs",
            )
        )

    truth = architecture.get(
        "canonical_truth_rules"
    )

    if not isinstance(
        truth,
        dict,
    ):
        issues.append(
            IntegrityIssue(
                "CANONICAL_TRUTH_RULES_MISSING",
                "canonical_truth_rules section is required.",
                "canonical_truth_rules",
            )
        )
    else:
        business_truth = truth.get(
            "business_truth"
        )

        derived_views = truth.get(
            "derived_views"
        )

        if not isinstance(
            business_truth,
            list,
        ) or not business_truth:
            issues.append(
                IntegrityIssue(
                    "BUSINESS_TRUTH_MISSING",
                    "Canonical business_truth list is required.",
                    "canonical_truth_rules.business_truth",
                )
            )

        if not isinstance(
            derived_views,
            list,
        ) or not derived_views:
            issues.append(
                IntegrityIssue(
                    "DERIVED_VIEWS_MISSING",
                    "Canonical derived_views list is required.",
                    "canonical_truth_rules.derived_views",
                )
            )

        if truth.get(
            "rule"
        ) != (
            "Derived systems can consume canonical truth and events, "
            "but cannot silently become business source of truth."
        ):
            issues.append(
                IntegrityIssue(
                    "INVALID_TRUTH_RULE",
                    "Canonical truth rule is missing or changed.",
                    "canonical_truth_rules.rule",
                )
            )

    invariants = architecture.get(
        "global_invariants"
    )

    if not isinstance(
        invariants,
        list,
    ):
        issues.append(
            IntegrityIssue(
                "GLOBAL_INVARIANTS_MISSING",
                "global_invariants must be a list.",
                "global_invariants",
            )
        )
    else:
        invariant_set = set(
            item
            for item in invariants
            if isinstance(
                item,
                str,
            )
        )

        for required in sorted(
            REQUIRED_GLOBAL_INVARIANTS
        ):
            if required not in invariant_set:
                issues.append(
                    IntegrityIssue(
                        "GLOBAL_INVARIANT_MISSING",
                        (
                            "Required global invariant is missing: "
                            f"{required}"
                        ),
                        "global_invariants",
                    )
                )

    architecture_change_policy = architecture.get(
        "architecture_change_policy"
    )

    if not isinstance(
        architecture_change_policy,
        dict,
    ):
        issues.append(
            IntegrityIssue(
                "CHANGE_POLICY_MISSING",
                "architecture_change_policy is required.",
                "architecture_change_policy",
            )
        )
    else:
        requires_review = architecture_change_policy.get(
            "requires_review"
        )

        forbidden = architecture_change_policy.get(
            "forbidden_without_explicit_approval"
        )

        if not isinstance(
            requires_review,
            list,
        ) or not requires_review:
            issues.append(
                IntegrityIssue(
                    "CHANGE_REVIEW_RULES_MISSING",
                    "Architecture change review rules are required.",
                    "architecture_change_policy.requires_review",
                )
            )

        if not isinstance(
            forbidden,
            list,
        ) or not forbidden:
            issues.append(
                IntegrityIssue(
                    "CHANGE_FORBIDDEN_RULES_MISSING",
                    "Architecture forbidden-change rules are required.",
                    (
                        "architecture_change_policy."
                        "forbidden_without_explicit_approval"
                    ),
                )
            )

    return IntegrityReport(
        ok=not issues,
        issues=tuple(issues),
    )


def validate_state_alignment(
    architecture: dict[str, Any],
    state: dict[str, Any],
) -> IntegrityReport:
    issues: list[IntegrityIssue] = []

    if not isinstance(
        state,
        dict,
    ):
        return IntegrityReport(
            ok=False,
            issues=(
                IntegrityIssue(
                    "STATE_NOT_OBJECT",
                    "Canonical state root must be an object.",
                ),
            ),
        )

    architecture_state = state.get(
        "architecture"
    )

    if not isinstance(
        architecture_state,
        dict,
    ):
        return IntegrityReport(
            ok=False,
            issues=(
                IntegrityIssue(
                    "STATE_ARCHITECTURE_MISSING",
                    "state.json architecture section is required.",
                    "architecture",
                ),
            ),
        )

    nodes = {
        node.get("id"): node
        for node in architecture.get(
            "architecture_nodes",
            []
        )
        if isinstance(
            node,
            dict,
        )
        and isinstance(
            node.get("id"),
            str,
        )
    }

    approved = architecture_state.get(
        "approved",
        []
    )

    pending = architecture_state.get(
        "pending",
        []
    )

    if not isinstance(
        approved,
        list,
    ):
        issues.append(
            IntegrityIssue(
                "STATE_APPROVED_INVALID",
                "architecture.approved must be a list.",
                "architecture.approved",
            )
        )
        approved = []

    if not isinstance(
        pending,
        list,
    ):
        issues.append(
            IntegrityIssue(
                "STATE_PENDING_INVALID",
                "architecture.pending must be a list.",
                "architecture.pending",
            )
        )
        pending = []

    approved_ids = [
        item.get("id")
        for item in approved
        if isinstance(
            item,
            dict,
        )
    ]

    pending_ids = [
        item.get("id")
        for item in pending
        if isinstance(
            item,
            dict,
        )
    ]

    for duplicate in sorted(
        _duplicate_values(
            approved_ids + pending_ids
        )
    ):
        issues.append(
            IntegrityIssue(
                "STATE_DUPLICATE_AUTHORITY_ENTRY",
                (
                    f"Architecture id {duplicate} "
                    "appears more than once in state authority lists."
                ),
                "architecture",
            )
        )

    overlap = set(approved_ids) & set(
        pending_ids
    )

    for architecture_id in sorted(
        overlap
    ):
        issues.append(
            IntegrityIssue(
                "STATE_APPROVED_PENDING_OVERLAP",
                (
                    f"{architecture_id} is simultaneously "
                    "approved and pending."
                ),
                "architecture",
            )
        )

    for architecture_id in approved_ids:
        node = nodes.get(
            architecture_id
        )

        if node is None:
            issues.append(
                IntegrityIssue(
                    "STATE_APPROVED_UNKNOWN_NODE",
                    (
                        f"State approves unknown architecture "
                        f"node {architecture_id}."
                    ),
                    "architecture.approved",
                )
            )
            continue

        if node.get("status") != "APPROVED":
            issues.append(
                IntegrityIssue(
                    "STATE_ARCHITECTURE_STATUS_MISMATCH",
                    (
                        f"State approves {architecture_id}, "
                        "but the Master Architecture node is not APPROVED."
                    ),
                    f"architecture.approved[{architecture_id}]",
                )
            )

    for architecture_id in pending_ids:
        node = nodes.get(
            architecture_id
        )

        if node is None:
            issues.append(
                IntegrityIssue(
                    "STATE_PENDING_UNKNOWN_NODE",
                    (
                        f"State keeps unknown architecture "
                        f"node {architecture_id} pending."
                    ),
                    "architecture.pending",
                )
            )
            continue

        if node.get("status") != "PENDING":
            issues.append(
                IntegrityIssue(
                    "STATE_ARCHITECTURE_STATUS_MISMATCH",
                    (
                        f"State keeps {architecture_id} pending, "
                        "but the Master Architecture node is not PENDING."
                    ),
                    f"architecture.pending[{architecture_id}]",
                )
            )

    expected_ids = set(
        nodes.keys()
    )

    state_ids = (
        set(approved_ids)
        | set(pending_ids)
    )

    missing_from_state = (
        expected_ids - state_ids
    )

    for architecture_id in sorted(
        missing_from_state
    ):
        issues.append(
            IntegrityIssue(
                "ARCHITECTURE_NODE_MISSING_FROM_STATE",
                (
                    f"{architecture_id} is present in the "
                    "Master Architecture but absent from state "
                    "approved/pending authority lists."
                ),
                "architecture",
            )
        )

    locked = architecture_state.get(
        "locked"
    )

    if locked is True:
        if pending_ids:
            issues.append(
                IntegrityIssue(
                    "LOCKED_WITH_PENDING_ARCHITECTURE",
                    (
                        "architecture.locked is true while "
                        "pending architecture nodes remain."
                    ),
                    "architecture.locked",
                )
            )

        if nodes.get(
            EXPECTED_ARCHITECTURE_ID,
            {}
        ).get("status") != "APPROVED":
            issues.append(
                IntegrityIssue(
                    "LOCKED_MASTER_NOT_APPROVED",
                    (
                        "ARCH-039 cannot be locked while "
                        "the Master Architecture node is not APPROVED."
                    ),
                    "architecture.locked",
                )
            )

    execution = state.get(
        "execution"
    )

    execution_plan = state.get(
        "execution_plan"
    )

    if isinstance(
        execution_plan,
        dict,
    ):
        sequence = execution_plan.get(
            "authoritative_sequence",
            []
        )

        if isinstance(
            sequence,
            list,
        ):
            arch039_plan = next(
                (
                    item
                    for item in sequence
                    if isinstance(
                        item,
                        dict,
                    )
                    and item.get("gate")
                    == EXPECTED_ARCHITECTURE_ID
                ),
                None,
            )

            if (
                isinstance(
                    arch039_plan,
                    dict,
                )
                and arch039_plan.get("status")
                == "COMPLETE"
                and EXPECTED_ARCHITECTURE_ID
                in set(pending_ids)
            ):
                issues.append(
                    IntegrityIssue(
                        "EXECUTION_COMPLETE_WHILE_ARCH_PENDING",
                        (
                            "ARCH-039 is marked COMPLETE in the "
                            "execution plan while its canonical "
                            "architecture node remains PENDING."
                        ),
                        (
                            "execution_plan.authoritative_sequence"
                        ),
                    )
                )

    if isinstance(
        execution,
        dict,
    ):
        current_gate = execution.get(
            "current_gate"
        )

        if (
            current_gate
            == EXPECTED_ARCHITECTURE_ID
            and EXPECTED_ARCHITECTURE_ID
            in set(approved_ids)
        ):
            issues.append(
                IntegrityIssue(
                    "EXECUTION_GATE_REOPENED_AFTER_APPROVAL",
                    (
                        "ARCH-039 cannot remain the current execution "
                        "gate after approval."
                    ),
                    "execution.current_gate",
                )
            )

    return IntegrityReport(
        ok=not issues,
        issues=tuple(issues),
    )


def validate_repository_master_uniqueness(
    control_center_root: Path,
) -> IntegrityReport:
    architecture_dir = (
        control_center_root
        / "architecture"
    )

    canonical_path = (
        architecture_dir
        / CANONICAL_ARCHITECTURE_FILENAME
    )

    if not architecture_dir.exists():
        return IntegrityReport(
            ok=False,
            issues=(
                IntegrityIssue(
                    "ARCHITECTURE_DIRECTORY_MISSING",
                    (
                        f"Architecture directory missing: "
                        f"{architecture_dir}"
                    ),
                ),
            ),
        )

    master_candidates = sorted(
        path
        for path in architecture_dir.iterdir()
        if (
            path.is_file()
            and "MASTER_ARCHITECTURE"
            in path.name.upper()
            and path.suffix.lower()
            == ".json"
        )
    )

    issues: list[IntegrityIssue] = []

    if canonical_path not in master_candidates:
        issues.append(
            IntegrityIssue(
                "CANONICAL_MASTER_MISSING",
                (
                    "Canonical Master Architecture file "
                    "is not present."
                ),
                str(canonical_path),
            )
        )

    if len(master_candidates) != 1:
        issues.append(
            IntegrityIssue(
                "SECOND_MASTER_ARCHITECTURE",
                (
                    "Exactly one Master Architecture JSON is "
                    f"allowed; found {len(master_candidates)}."
                ),
                str(architecture_dir),
            )
        )

    return IntegrityReport(
        ok=not issues,
        issues=tuple(issues),
    )


def run_integrity_check(
    control_center_root: Path,
) -> IntegrityReport:
    master_path = (
        control_center_root
        / "architecture"
        / CANONICAL_ARCHITECTURE_FILENAME
    )

    state_path = (
        control_center_root
        / "data"
        / "state.json"
    )

    issues: list[IntegrityIssue] = []

    architecture = _load_json(
        master_path
    )

    state = _load_json(
        state_path
    )

    content_report = validate_master_architecture(
        architecture
    )

    issues.extend(
        content_report.issues
    )

    if isinstance(
        architecture,
        dict,
    ) and isinstance(
        state,
        dict,
    ):
        state_report = validate_state_alignment(
            architecture,
            state,
        )
        issues.extend(
            state_report.issues
        )

    uniqueness_report = (
        validate_repository_master_uniqueness(
            control_center_root
        )
    )

    issues.extend(
        uniqueness_report.issues
    )

    return IntegrityReport(
        ok=not issues,
        issues=tuple(issues),
    )


__all__ = [
    "ArchitectureIntegrityError",
    "CANONICAL_ARCHITECTURE_FILENAME",
    "EXPECTED_ARCHITECTURE_ID",
    "IntegrityIssue",
    "IntegrityReport",
    "run_integrity_check",
    "validate_master_architecture",
    "validate_repository_master_uniqueness",
    "validate_state_alignment",
]
