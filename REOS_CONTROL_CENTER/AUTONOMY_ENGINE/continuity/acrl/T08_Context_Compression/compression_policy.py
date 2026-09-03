"""ACRL T08 — Compression Policy.

Defines the deterministic semantic policy used by T08 context compression.

Boundary:
    Policy classification only.
    No state mutation.
    No authority mutation.
    No controller execution.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Final


class CompressionPolicyError(ValueError):
    """Base compression-policy error."""


class CompressionAction(str, Enum):
    """Allowed semantic actions during compression."""

    PRESERVE = "PRESERVE"
    SUMMARIZE = "SUMMARIZE"
    OMIT = "OMIT"
    REJECT = "REJECT"


class SemanticPriority(str, Enum):
    """Semantic preservation priority."""

    AUTHORITATIVE_REQUIRED = "AUTHORITATIVE_REQUIRED"
    IDENTITY_REQUIRED = "IDENTITY_REQUIRED"
    RESUME_REQUIRED = "RESUME_REQUIRED"
    DERIVED_OPTIONAL = "DERIVED_OPTIONAL"
    CONTEXT_OPTIONAL = "CONTEXT_OPTIONAL"


@dataclass(frozen=True)
class CompressionRule:
    """Immutable compression rule."""

    section: str
    action: CompressionAction
    priority: SemanticPriority
    reason: str

    def __post_init__(self) -> None:
        if not self.section.strip():
            raise CompressionPolicyError(
                "Compression rule section cannot be empty."
            )

        if not self.reason.strip():
            raise CompressionPolicyError(
                "Compression rule reason cannot be empty."
            )


class CompressionPolicy:
    """Deterministic T08 semantic compression policy."""

    VERSION: Final[str] = "T08-POLICY-1.0"

    REQUIRED_SECTIONS: Final[tuple[str, ...]] = (
        "project_identity",
        "architecture",
        "execution",
        "gate_continuity",
        "dependency_authority",
        "checkpoint",
    )

    DEFAULT_RULES: Final[tuple[CompressionRule, ...]] = (
        CompressionRule(
            section="project_identity",
            action=CompressionAction.PRESERVE,
            priority=SemanticPriority.IDENTITY_REQUIRED,
            reason="Project identity is required for safe continuation.",
        ),
        CompressionRule(
            section="architecture",
            action=CompressionAction.PRESERVE,
            priority=SemanticPriority.AUTHORITATIVE_REQUIRED,
            reason="Frozen architecture must never be semantically discarded.",
        ),
        CompressionRule(
            section="execution",
            action=CompressionAction.PRESERVE,
            priority=SemanticPriority.RESUME_REQUIRED,
            reason="Execution position is required for safe resume.",
        ),
        CompressionRule(
            section="gate_continuity",
            action=CompressionAction.PRESERVE,
            priority=SemanticPriority.RESUME_REQUIRED,
            reason="Gate and subtask continuity must survive compression.",
        ),
        CompressionRule(
            section="dependency_authority",
            action=CompressionAction.PRESERVE,
            priority=SemanticPriority.AUTHORITATIVE_REQUIRED,
            reason="Dependency authority boundaries must survive compression.",
        ),
        CompressionRule(
            section="checkpoint",
            action=CompressionAction.PRESERVE,
            priority=SemanticPriority.RESUME_REQUIRED,
            reason="Checkpoint identity and evidence are required for recovery.",
        ),
    )

    @classmethod
    def default(cls) -> "CompressionPolicy":
        """Return the immutable default policy."""

        return cls(
            rules=cls.DEFAULT_RULES,
        )

    def __init__(
        self,
        rules: tuple[CompressionRule, ...],
    ) -> None:
        self._rules = tuple(rules)
        self._validate_rules()

    @property
    def rules(self) -> tuple[CompressionRule, ...]:
        """Return immutable policy rules."""

        return self._rules

    @property
    def version(self) -> str:
        """Return policy version."""

        return self.VERSION

    def rule_for(self, section: str) -> CompressionRule:
        """Return the rule for a section."""

        for rule in self._rules:
            if rule.section == section:
                return rule

        raise CompressionPolicyError(
            f"No compression policy exists for section '{section}'."
        )

    def action_for(self, section: str) -> CompressionAction:
        """Return compression action for a section."""

        return self.rule_for(section).action

    def priority_for(self, section: str) -> SemanticPriority:
        """Return semantic priority for a section."""

        return self.rule_for(section).priority

    def required_sections(self) -> tuple[str, ...]:
        """Return sections that must be preserved."""

        return tuple(
            rule.section
            for rule in self._rules
            if rule.priority
            in {
                SemanticPriority.AUTHORITATIVE_REQUIRED,
                SemanticPriority.IDENTITY_REQUIRED,
                SemanticPriority.RESUME_REQUIRED,
            }
        )

    def validate_sections(
        self,
        sections: tuple[str, ...],
    ) -> None:
        """Fail closed if mandatory sections are not preserved."""

        required = set(self.required_sections())
        provided = set(sections)
        missing = required - provided

        if missing:
            raise CompressionPolicyError(
                "Compression policy requirements are not satisfied: "
                f"{sorted(missing)}"
            )

    def _validate_rules(self) -> None:
        if not self._rules:
            raise CompressionPolicyError(
                "Compression policy cannot contain zero rules."
            )

        names = [rule.section for rule in self._rules]

        if len(names) != len(set(names)):
            raise CompressionPolicyError(
                "Compression policy contains duplicate sections."
            )

        self.validate_sections(tuple(names))


DEFAULT_COMPRESSION_POLICY = CompressionPolicy.default()


__all__ = [
    "CompressionAction",
    "CompressionPolicy",
    "CompressionPolicyError",
    "CompressionRule",
    "DEFAULT_COMPRESSION_POLICY",
    "SemanticPriority",
]