from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock

from .evidence_models import EvidenceReference


class EvidenceIdentityConflict(RuntimeError):
    pass


@dataclass
class EvidenceRegistry:
    _items: dict[str, EvidenceReference] = field(
        default_factory=dict
    )
    _lock: Lock = field(
        default_factory=Lock
    )

    def register(
        self,
        evidence: EvidenceReference,
    ) -> None:
        with self._lock:
            existing = self._items.get(
                evidence.evidence_id
            )

            if existing is None:
                self._items[
                    evidence.evidence_id
                ] = evidence
                return

            if existing == evidence:
                return

            raise EvidenceIdentityConflict(
                "Evidence identity already exists with different content."
            )

    def get(
        self,
        evidence_id: str,
    ) -> EvidenceReference | None:
        with self._lock:
            return self._items.get(
                evidence_id
            )

    def contains(
        self,
        evidence_id: str,
    ) -> bool:
        with self._lock:
            return evidence_id in self._items

    def values(
        self,
    ) -> tuple[EvidenceReference, ...]:
        with self._lock:
            return tuple(
                self._items.values()
            )

    def size(self) -> int:
        with self._lock:
            return len(self._items)
