
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

@dataclass(frozen=True)
class SemanticField:
    path: str
    value: Any
    semantic_owner: str
    semantic_state: str
    lifecycle: str
    authority: str

@dataclass(frozen=True)
class Comparison:
    status: str
    reason: str
    left: SemanticField
    right: SemanticField

class SemanticConsistencyEngine:
    """
    Conservative semantic comparison.

    Two fields are NOT considered contradictory just because their values
    differ. They must first be proven to represent the same semantic state.
    """

    def __init__(self, resolver: Callable[[str, Any], SemanticField | None]) -> None:
        self.resolver = resolver

    def compare(self, left_path: str, left_value: Any, right_path: str, right_value: Any) -> Comparison:
        left = self.resolver(left_path, left_value)
        right = self.resolver(right_path, right_value)

        if not left or not right:
            # Unknown semantics are first-class; never invent a mismatch.
            return Comparison(
                "UNKNOWN",
                "Semantic owner/lifecycle/authority not proven for both fields.",
                left or SemanticField(left_path, left_value, "UNKNOWN", "UNKNOWN", "UNKNOWN", "UNKNOWN"),
                right or SemanticField(right_path, right_value, "UNKNOWN", "UNKNOWN", "UNKNOWN", "UNKNOWN"),
            )

        same_dimension = (
            left.semantic_owner == right.semantic_owner
            and left.semantic_state == right.semantic_state
            and left.lifecycle == right.lifecycle
            and left.authority == right.authority
        )

        if not same_dimension:
            return Comparison(
                "NOT_COMPARABLE",
                "Fields have different proven semantic dimensions.",
                left,
                right,
            )

        if left.value == right.value:
            return Comparison("CONSISTENT", "Values match under the same semantic dimension.", left, right)

        return Comparison("CONTRADICTION", "Values differ under the same proven semantic dimension.", left, right)
