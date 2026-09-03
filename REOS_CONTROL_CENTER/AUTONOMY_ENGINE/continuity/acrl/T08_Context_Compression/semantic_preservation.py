"""ACRL T08 — Semantic Preservation.

Classifies context sections according to their safety importance.

This module does not compress or mutate data. It only determines
whether information must be preserved, may be summarized, may be
omitted, or must cause rejection.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping


class SemanticPreservationError(ValueError):
    """Base semantic-preservation error."""


class PreservationClass(str, Enum):
    """Semantic preservation classes."""

    AUTHORITATIVE_REQUIRED = "AUTHORITATIVE_REQUIRED"
    IDENTITY_REQUIRED = "IDENTITY_REQUIRED"
    RESUME_REQUIRED = "RESUME_REQUIRED"
    DERIVED_OPTIONAL = "DERIVED_OPTIONAL"
    CONTEXT_OPTIONAL = "CONTEXT_OPTIONAL"


@dataclass(frozen=True)
class PreservationDecision:
    """Immutable classification result for one section."""

    section: str
    classification: PreservationClass
    preserve: bool
    summarizable: bool
    omittable: bool
    reason: str

    def __post_init__(self) -> None:
        if not self.section.strip():
            raise SemanticPreservationError(
                "Section name cannot be empty."
            )

        if not self.reason.strip():
            raise SemanticPreservationError(
                "Preservation reason cannot be empty."
            )

        if self.preserve and self.omittable:
            raise SemanticPreservationError(
                "A section cannot be both preserved and omittable."
            )


class SemanticPreservationClassifier:
    """Deterministic T08 semantic classifier."""

    REQUIRED_CLASSIFICATIONS = {
        "project_identity": PreservationClass.IDENTITY_REQUIRED,
        "architecture": PreservationClass.AUTHORITATIVE_REQUIRED,
        "execution": PreservationClass.RESUME_REQUIRED,
        "gate_continuity": PreservationClass.RESUME_REQUIRED,
        "dependency_authority": PreservationClass.AUTHORITATIVE_REQUIRED,
        "checkpoint": PreservationClass.RESUME_REQUIRED,
    }

    @classmethod
    def classify(
        cls,
        section: str,
        value: Any,
    ) -> PreservationDecision:
        """Classify one context section."""

        if not section.strip():
            raise SemanticPreservationError(
                "Section name cannot be empty."
            )

        if value is None:
            raise SemanticPreservationError(
                f"Section '{section}' contains no value."
            )

        required = cls.REQUIRED_CLASSIFICATIONS.get(
            section
        )

        if required is not None:
            return PreservationDecision(
                section=section,
                classification=required,
                preserve=True,
                summarizable=False,
                omittable=False,
                reason=(
                    "Required for authoritative identity or safe resume."
                ),
            )

        if isinstance(value, Mapping):
            return PreservationDecision(
                section=section,
                classification=PreservationClass.DERIVED_OPTIONAL,
                preserve=False,
                summarizable=True,
                omittable=True,
                reason=(
                    "Non-required structured data may be summarized "
                    "or omitted under policy."
                ),
            )

        return PreservationDecision(
            section=section,
            classification=PreservationClass.CONTEXT_OPTIONAL,
            preserve=False,
            summarizable=True,
            omittable=True,
            reason=(
                "Non-authoritative contextual information is optional."
            ),
        )

    @classmethod
    def classify_all(
        cls,
        sections: Mapping[str, Any],
    ) -> tuple[PreservationDecision, ...]:
        """Classify sections in deterministic key order."""

        if not isinstance(sections, Mapping):
            raise SemanticPreservationError(
                "Sections must be a mapping."
            )

        return tuple(
            cls.classify(section, sections[section])
            for section in sorted(sections)
        )

    @classmethod
    def required_sections(
        cls,
    ) -> tuple[str, ...]:
        """Return all mandatory preservation sections."""

        return tuple(
            sorted(cls.REQUIRED_CLASSIFICATIONS)
        )

    @classmethod
    def validate_required_sections(
        cls,
        sections: Mapping[str, Any],
    ) -> None:
        """Fail closed if a mandatory section is absent."""

        if not isinstance(sections, Mapping):
            raise SemanticPreservationError(
                "Sections must be a mapping."
            )

        missing = set(
            cls.REQUIRED_CLASSIFICATIONS
        ) - set(sections)

        if missing:
            raise SemanticPreservationError(
                "Mandatory semantic sections are missing: "
                f"{sorted(missing)}"
            )


__all__ = [
    "PreservationClass",
    "PreservationDecision",
    "SemanticPreservationClassifier",
    "SemanticPreservationError",
]