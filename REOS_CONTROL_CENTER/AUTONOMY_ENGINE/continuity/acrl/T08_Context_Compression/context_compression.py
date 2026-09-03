"""ACRL T08 — Context Compression.

Additive-only context compression layer.

Purpose:
    Convert a complete T07 New-Chat Bootstrap context into a compact,
    deterministic and loss-aware-safe resume context.

Rules:
    - Never modify T01-T07.
    - Never modify __init__.py.
    - Never discard authoritative execution information.
    - Never invent project state.
    - Never change architecture.
    - Fail closed on invalid or tampered bootstrap data.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Mapping

from .new_chat_bootstrap import (
    BootstrapAuthorityError,
    BootstrapContext,
    BootstrapIntegrityError,
    BootstrapValidationError,
    NewChatBootstrapEngine,
)


class ContextCompressionError(RuntimeError):
    """Base T08 compression error."""


class ContextCompressionIntegrityError(
    ContextCompressionError
):
    """Raised when compressed context integrity fails."""


class ContextCompressionAuthorityError(
    ContextCompressionError
):
    """Raised when authoritative information is missing."""


class ContextCompressionValidationError(
    ContextCompressionError
):
    """Raised when compression input is invalid."""


@dataclass(frozen=True)
class CompressedContext:
    """Immutable compressed autonomous resume context."""

    schema_version: str
    source_bootstrap_id: str
    authority: str
    project_identity: Mapping[str, Any]
    architecture: Mapping[str, Any]
    execution: Mapping[str, Any]
    gate_continuity: Mapping[str, Any]
    dependency_authority: Mapping[str, Any]
    checkpoint: Mapping[str, Any]
    resume_mode: str
    compression_version: str
    preserved_sections: tuple[str, ...]
    fingerprint: str

    def to_dict(self) -> dict[str, Any]:
        """Return machine-readable compressed context."""

        return {
            "schema_version": self.schema_version,
            "source_bootstrap_id": self.source_bootstrap_id,
            "authority": self.authority,
            "project_identity": dict(
                self.project_identity
            ),
            "architecture": dict(
                self.architecture
            ),
            "execution": dict(
                self.execution
            ),
            "gate_continuity": dict(
                self.gate_continuity
            ),
            "dependency_authority": dict(
                self.dependency_authority
            ),
            "checkpoint": dict(
                self.checkpoint
            ),
            "resume_mode": self.resume_mode,
            "compression_version": self.compression_version,
            "preserved_sections": list(
                self.preserved_sections
            ),
            "fingerprint": self.fingerprint,
        }

    def verify_integrity(self) -> bool:
        """Verify compressed context fingerprint."""

        payload = {
            "schema_version": self.schema_version,
            "source_bootstrap_id": self.source_bootstrap_id,
            "authority": self.authority,
            "project_identity": dict(
                self.project_identity
            ),
            "architecture": dict(
                self.architecture
            ),
            "execution": dict(
                self.execution
            ),
            "gate_continuity": dict(
                self.gate_continuity
            ),
            "dependency_authority": dict(
                self.dependency_authority
            ),
            "checkpoint": dict(
                self.checkpoint
            ),
            "resume_mode": self.resume_mode,
            "compression_version": self.compression_version,
            "preserved_sections": list(
                self.preserved_sections
            ),
        }

        canonical = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )

        expected = hashlib.sha256(
            canonical.encode("utf-8")
        ).hexdigest()

        return expected == self.fingerprint


class ContextCompressionEngine:
    """Compress validated T07 contexts without semantic loss."""

    SCHEMA_VERSION = "1.0"
    COMPRESSION_VERSION = "T08-1.0"
    AUTHORITY = "REOS_CONTROL_CENTER"
    RESUME_MODE = "SAFE_AUTONOMOUS_RESUME"

    REQUIRED_SECTIONS = (
        "project_identity",
        "architecture",
        "execution",
        "gate_continuity",
        "dependency_authority",
        "checkpoint",
    )

    @staticmethod
    def _canonical(
        payload: Mapping[str, Any],
    ) -> str:
        try:
            return json.dumps(
                payload,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
            )
        except (TypeError, ValueError) as exc:
            raise ContextCompressionValidationError(
                "Context cannot be deterministically serialized."
            ) from exc

    @classmethod
    def _fingerprint(
        cls,
        payload: Mapping[str, Any],
    ) -> str:
        return hashlib.sha256(
            cls._canonical(payload).encode("utf-8")
        ).hexdigest()

    @staticmethod
    def _require_mapping(
        name: str,
        value: Any,
    ) -> dict[str, Any]:
        if not isinstance(value, Mapping):
            raise ContextCompressionAuthorityError(
                f"Authoritative section '{name}' "
                "is missing or invalid."
            )

        return dict(value)

    @classmethod
    def _extract_authoritative_payload(
        cls,
        context: BootstrapContext,
    ) -> dict[str, Any]:
        return {
            "project_identity": cls._require_mapping(
                "project_identity",
                context.project_dna,
            ),
            "architecture": cls._require_mapping(
                "architecture",
                context.architecture_lock,
            ),
            "execution": cls._require_mapping(
                "execution",
                context.execution_state,
            ),
            "gate_continuity": cls._require_mapping(
                "gate_continuity",
                context.gate_continuity,
            ),
            "dependency_authority": cls._require_mapping(
                "dependency_authority",
                context.dependency_authority,
            ),
            "checkpoint": cls._require_mapping(
                "checkpoint",
                context.checkpoint,
            ),
        }

    @classmethod
    def compress(
        cls,
        context: BootstrapContext,
    ) -> CompressedContext:
        """Compress a validated T07 bootstrap context."""

        # IMPORTANT:
        # Validate the public input type before delegating to T07.
        # This keeps T08 validation errors deterministic and prevents
        # unrelated T07 errors from masking an invalid T08 input.
        if not isinstance(
            context,
            BootstrapContext,
        ):
            raise ContextCompressionValidationError(
                "Input must be a BootstrapContext."
            )

        try:
            NewChatBootstrapEngine.validate_for_resume(
                context
            )
        except BootstrapIntegrityError as exc:
            raise ContextCompressionIntegrityError(
                "T07 bootstrap integrity verification failed."
            ) from exc
        except BootstrapAuthorityError as exc:
            raise ContextCompressionAuthorityError(
                "T07 bootstrap authority validation failed."
            ) from exc
        except BootstrapValidationError as exc:
            raise ContextCompressionValidationError(
                "T07 bootstrap validation failed."
            ) from exc

        if (
            context.authority
            != cls.AUTHORITY
        ):
            raise ContextCompressionAuthorityError(
                "Context authority mismatch."
            )

        if (
            context.resume_mode
            != cls.RESUME_MODE
        ):
            raise ContextCompressionAuthorityError(
                "Context resume mode is unsafe."
            )

        authoritative = (
            cls._extract_authoritative_payload(
                context
            )
        )

        preserved_sections = (
            cls.REQUIRED_SECTIONS
        )

        payload = {
            "schema_version": cls.SCHEMA_VERSION,
            "source_bootstrap_id": context.bootstrap_id,
            "authority": cls.AUTHORITY,
            **authoritative,
            "resume_mode": cls.RESUME_MODE,
            "compression_version": cls.COMPRESSION_VERSION,
            "preserved_sections": list(
                preserved_sections
            ),
        }

        fingerprint = cls._fingerprint(
            payload
        )

        return CompressedContext(
            schema_version=cls.SCHEMA_VERSION,
            source_bootstrap_id=context.bootstrap_id,
            authority=cls.AUTHORITY,
            project_identity=authoritative[
                "project_identity"
            ],
            architecture=authoritative[
                "architecture"
            ],
            execution=authoritative[
                "execution"
            ],
            gate_continuity=authoritative[
                "gate_continuity"
            ],
            dependency_authority=authoritative[
                "dependency_authority"
            ],
            checkpoint=authoritative[
                "checkpoint"
            ],
            resume_mode=cls.RESUME_MODE,
            compression_version=(
                cls.COMPRESSION_VERSION
            ),
            preserved_sections=(
                preserved_sections
            ),
            fingerprint=fingerprint,
        )

    @classmethod
    def validate_for_resume(
        cls,
        context: CompressedContext,
    ) -> None:
        """Fail closed when compressed context is unsafe."""

        if not isinstance(
            context,
            CompressedContext,
        ):
            raise ContextCompressionValidationError(
                "Invalid compressed context."
            )

        if not context.verify_integrity():
            raise ContextCompressionIntegrityError(
                "Compressed context fingerprint verification failed."
            )

        if (
            context.authority
            != cls.AUTHORITY
        ):
            raise ContextCompressionAuthorityError(
                "Compressed context authority mismatch."
            )

        if (
            context.resume_mode
            != cls.RESUME_MODE
        ):
            raise ContextCompressionAuthorityError(
                "Compressed context resume mode is unsafe."
            )

        for section in cls.REQUIRED_SECTIONS:
            value = getattr(
                context,
                section,
                None,
            )

            if not isinstance(
                value,
                Mapping,
            ):
                raise ContextCompressionAuthorityError(
                    f"Required section '{section}' "
                    "is unavailable."
                )

        preserved = set(
            context.preserved_sections
        )

        missing = (
            set(cls.REQUIRED_SECTIONS)
            - preserved
        )

        if missing:
            raise ContextCompressionAuthorityError(
                "Required authoritative sections "
                f"were not preserved: {sorted(missing)}"
            )

    @classmethod
    def resume_summary(
        cls,
        context: CompressedContext,
    ) -> dict[str, str]:
        """Return the minimum safe continuation state."""

        cls.validate_for_resume(
            context
        )

        execution = dict(
            context.execution
        )

        gate = dict(
            context.gate_continuity
        )

        current_gate = str(
            execution.get(
                "current_gate",
                gate.get(
                    "current_gate",
                    "",
                ),
            )
        )

        current_subtask = str(
            execution.get(
                "current_subtask",
                gate.get(
                    "current_subtask",
                    "",
                ),
            )
        )

        if not current_gate:
            raise ContextCompressionAuthorityError(
                "Current gate cannot be recovered."
            )

        if not current_subtask:
            raise ContextCompressionAuthorityError(
                "Current subtask cannot be recovered."
            )

        return {
            "authority": context.authority,
            "source_bootstrap_id": (
                context.source_bootstrap_id
            ),
            "current_gate": current_gate,
            "current_subtask": current_subtask,
            "resume_mode": context.resume_mode,
            "compression_version": (
                context.compression_version
            ),
            "fingerprint": context.fingerprint,
        }


def compress_bootstrap_context(
    context: BootstrapContext,
) -> CompressedContext:
    """Convenience API for T08 compression."""

    return ContextCompressionEngine.compress(
        context
    )


__all__ = [
    "CompressedContext",
    "ContextCompressionAuthorityError",
    "ContextCompressionEngine",
    "ContextCompressionError",
    "ContextCompressionIntegrityError",
    "ContextCompressionValidationError",
    "compress_bootstrap_context",
]