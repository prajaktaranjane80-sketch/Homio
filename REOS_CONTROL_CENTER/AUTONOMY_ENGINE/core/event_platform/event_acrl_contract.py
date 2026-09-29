from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Mapping, Any
from uuid import UUID


class ACRLEventContractError(ValueError):
    """CORE-002 / ACRL integration contract violation."""


@dataclass(frozen=True, slots=True)
class ACRLReconstructionDescriptor:
    event_id: UUID
    tenant_id: UUID
    contract_key: str
    fingerprint: str


@dataclass(frozen=True, slots=True)
class ACRLCheckpointDescriptor:
    checkpoint_id: str
    event_id: UUID
    tenant_id: UUID
    sequence: int | None


class ACRLIntegrationBoundary:
    """
    Read/reconstruct/verify boundary.

    ACRL can reconstruct CORE-002 event context,
    but does not become the owner of domain state.
    """

    def __init__(
        self,
        *,
        reconstruct: Callable[
            [UUID],
            Mapping[str, Any],
        ],
        discover_dependencies: Callable[
            [str],
            list[str],
        ],
        detect_drift: Callable[
            [str, str],
            bool,
        ],
    ) -> None:
        self._reconstruct = reconstruct
        self._discover_dependencies = (
            discover_dependencies
        )
        self._detect_drift = detect_drift

    def reconstruct_event(
        self,
        event_id: UUID,
    ) -> Mapping[str, Any]:
        if not isinstance(
            event_id,
            UUID,
        ):
            raise TypeError(
                "event_id must be UUID"
            )

        result = self._reconstruct(
            event_id
        )

        if not isinstance(
            result,
            Mapping,
        ):
            raise ACRLEventContractError(
                "reconstruction must return mapping"
            )

        return dict(result)

    def dependencies(
        self,
        contract_key: str,
    ) -> tuple[str, ...]:
        if not isinstance(
            contract_key,
            str,
        ) or not contract_key.strip():
            raise ValueError(
                "contract_key is required"
            )

        result = self._discover_dependencies(
            contract_key
        )

        return tuple(
            str(item)
            for item in result
        )

    def drift_detected(
        self,
        *,
        expected_fingerprint: str,
        actual_fingerprint: str,
    ) -> bool:
        return bool(
            self._detect_drift(
                expected_fingerprint,
                actual_fingerprint,
            )
        )


__all__ = [
    "ACRLEventContractError",
    "ACRLReconstructionDescriptor",
    "ACRLCheckpointDescriptor",
    "ACRLIntegrationBoundary",
]
