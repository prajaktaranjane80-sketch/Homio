"""
REOS Capability Reuse / No-Duplicate Guard.

Derived intelligence boundary for AUTONOMY_ENGINE.

It decides whether a proposed capability should be:
REUSE | EXTEND | CREATE_NEW | BLOCK

It does not own canonical state, architecture authority, Git, or execution.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from hashlib import sha256
import json
import re
from typing import Iterable, Mapping, Protocol, Sequence


class ReuseDecision(StrEnum):
    REUSE = "REUSE"
    EXTEND = "EXTEND"
    CREATE_NEW = "CREATE_NEW"
    BLOCK = "BLOCK"


class ReuseReason(StrEnum):
    EXACT_CAPABILITY = "EXACT_CAPABILITY"
    EXACT_RESPONSIBILITY = "EXACT_RESPONSIBILITY"
    STRUCTURAL_OVERLAP = "STRUCTURAL_OVERLAP"
    HIGH_RESPONSIBILITY_OVERLAP = "HIGH_RESPONSIBILITY_OVERLAP"
    MULTIPLE_MATCHES_AMBIGUOUS = "MULTIPLE_MATCHES_AMBIGUOUS"
    NO_EXISTING_MATCH = "NO_EXISTING_MATCH"
    CATALOG_CHANGED = "CATALOG_CHANGED"


class CapabilityLike(Protocol):
    capability_id: str
    name: str
    description: str
    enabled: bool
    risk_class: str
    metadata: dict[str, object] | None


_STOPWORDS = frozenset({
    "a", "an", "and", "as", "at", "by", "for", "from", "in", "into",
    "of", "on", "or", "the", "to", "with", "within", "via",
})


def _normalize(value: str) -> str:
    value = value.casefold().replace("_", " ").replace("-", " ")
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return " ".join(value.split())


def _tokens(value: str) -> frozenset[str]:
    return frozenset(
        token
        for token in _normalize(value).split()
        if token and token not in _STOPWORDS
    )


def _string_set(values: Iterable[str] | None) -> frozenset[str]:
    return frozenset(
        _normalize(value)
        for value in (values or ())
        if isinstance(value, str) and value.strip()
    )


def _jaccard(left: frozenset[str], right: frozenset[str]) -> float:
    if not left and not right:
        return 1.0
    union = left | right
    return len(left & right) / len(union) if union else 1.0


@dataclass(frozen=True, slots=True)
class CapabilityRecord:
    capability_id: str
    name: str
    description: str = ""
    responsibility: str = ""
    architecture_ids: tuple[str, ...] = ()
    source_of_truth: str = ""
    inputs: tuple[str, ...] = ()
    outputs: tuple[str, ...] = ()
    owner: str = ""
    enabled: bool = True
    risk_class: str = "standard"

    def __post_init__(self) -> None:
        if not isinstance(self.capability_id, str) or not self.capability_id.strip():
            raise ValueError("capability_id must be a non-empty string")
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("name must be a non-empty string")
        if not isinstance(self.enabled, bool):
            raise TypeError("enabled must be bool")

    @property
    def responsibility_tokens(self) -> frozenset[str]:
        return _tokens(" ".join((self.name, self.description, self.responsibility)))

    @property
    def pure_responsibility_tokens(self) -> frozenset[str]:
        """
        Tokens derived only from the declared responsibility.

        Name and description are intentionally excluded so that two
        capabilities with different labels/descriptions but the same
        responsibility are treated as the same responsibility.
        """
        return _tokens(self.responsibility)

    @property
    def architecture_set(self) -> frozenset[str]:
        return _string_set(self.architecture_ids)

    @property
    def source_key(self) -> str:
        return _normalize(self.source_of_truth)

    @classmethod
    def from_capability(cls, capability: CapabilityLike) -> "CapabilityRecord":
        metadata = capability.metadata or {}

        def as_tuple(key: str) -> tuple[str, ...]:
            value = metadata.get(key, ())
            if isinstance(value, str):
                return (value,)
            if isinstance(value, Sequence):
                return tuple(str(item) for item in value if isinstance(item, (str, int, float)))
            return ()

        return cls(
            capability_id=capability.capability_id,
            name=capability.name,
            description=capability.description,
            responsibility=str(metadata.get("responsibility", "")),
            architecture_ids=as_tuple("architecture_ids"),
            source_of_truth=str(metadata.get("source_of_truth", "")),
            inputs=as_tuple("inputs"),
            outputs=as_tuple("outputs"),
            owner=str(metadata.get("owner", "")),
            enabled=capability.enabled,
            risk_class=capability.risk_class,
        )


@dataclass(frozen=True, slots=True)
class CapabilityRequest:
    capability_id: str
    name: str
    description: str = ""
    responsibility: str = ""
    architecture_ids: tuple[str, ...] = ()
    source_of_truth: str = ""
    inputs: tuple[str, ...] = ()
    outputs: tuple[str, ...] = ()
    owner: str = ""
    allow_create_new: bool = True

    def as_record(self) -> CapabilityRecord:
        return CapabilityRecord(
            capability_id=self.capability_id,
            name=self.name,
            description=self.description,
            responsibility=self.responsibility,
            architecture_ids=self.architecture_ids,
            source_of_truth=self.source_of_truth,
            inputs=self.inputs,
            outputs=self.outputs,
            owner=self.owner,
        )


@dataclass(frozen=True, slots=True)
class ReuseMatch:
    capability_id: str
    decision: ReuseDecision
    reason: ReuseReason
    responsibility_score: float
    architecture_overlap: tuple[str, ...]
    source_of_truth_match: bool
    confidence: float

    def to_dict(self) -> dict[str, object]:
        return {
            "capability_id": self.capability_id,
            "decision": self.decision.value,
            "reason": self.reason.value,
            "responsibility_score": round(self.responsibility_score, 6),
            "architecture_overlap": list(self.architecture_overlap),
            "source_of_truth_match": self.source_of_truth_match,
            "confidence": round(self.confidence, 6),
        }


@dataclass(frozen=True, slots=True)
class ReuseDecisionResult:
    decision: ReuseDecision
    reason: ReuseReason
    selected_capability_id: str | None
    matches: tuple[ReuseMatch, ...]
    request_fingerprint: str
    catalog_fingerprint: str
    blockers: tuple[str, ...] = ()
    evidence: Mapping[str, object] = field(default_factory=dict)

    @property
    def allowed_to_create(self) -> bool:
        return self.decision == ReuseDecision.CREATE_NEW and not self.blockers

    def to_dict(self) -> dict[str, object]:
        return {
            "decision": self.decision.value,
            "reason": self.reason.value,
            "selected_capability_id": self.selected_capability_id,
            "matches": [match.to_dict() for match in self.matches],
            "request_fingerprint": self.request_fingerprint,
            "catalog_fingerprint": self.catalog_fingerprint,
            "blockers": list(self.blockers),
            "allowed_to_create": self.allowed_to_create,
            "evidence": dict(self.evidence),
        }


class CapabilityReuseGuard:
    """Deterministic pre-implementation reuse gate."""

    def __init__(
        self,
        *,
        strong_responsibility_threshold: float = 0.80,
        extend_responsibility_threshold: float = 0.67,
    ) -> None:
        if not 0 <= extend_responsibility_threshold <= 1:
            raise ValueError("extend_responsibility_threshold must be 0..1")
        if not 0 <= strong_responsibility_threshold <= 1:
            raise ValueError("strong_responsibility_threshold must be 0..1")
        if extend_responsibility_threshold > strong_responsibility_threshold:
            raise ValueError("extend threshold cannot exceed strong threshold")
        self.strong_threshold = strong_responsibility_threshold
        self.extend_threshold = extend_responsibility_threshold

    @staticmethod
    def fingerprint_record(record: CapabilityRecord) -> str:
        payload = {
            "capability_id": record.capability_id,
            "name": _normalize(record.name),
            "description": _normalize(record.description),
            "responsibility": _normalize(record.responsibility),
            "architecture_ids": sorted(record.architecture_set),
            "source_of_truth": record.source_key,
            "inputs": sorted(_string_set(record.inputs)),
            "outputs": sorted(_string_set(record.outputs)),
            "owner": _normalize(record.owner),
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return sha256(canonical.encode("utf-8")).hexdigest()

    @classmethod
    def fingerprint_catalog(cls, records: Iterable[CapabilityRecord]) -> str:
        payload = [
            (record.capability_id, cls.fingerprint_record(record))
            for record in sorted(records, key=lambda item: item.capability_id)
        ]
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return sha256(canonical.encode("utf-8")).hexdigest()

    def evaluate(
        self,
        request: CapabilityRequest,
        existing: Iterable[CapabilityRecord],
        *,
        expected_catalog_fingerprint: str | None = None,
    ) -> ReuseDecisionResult:
        request_record = request.as_record()
        catalog = tuple(existing)
        catalog_fingerprint = self.fingerprint_catalog(catalog)

        if expected_catalog_fingerprint is not None and expected_catalog_fingerprint != catalog_fingerprint:
            return self._blocked(
                request_record,
                catalog,
                ReuseReason.CATALOG_CHANGED,
                ("capability_catalog_changed",),
                evidence={"catalog_revalidation_required": True},
            )

        enabled = tuple(item for item in catalog if item.enabled)

        exact_id = next(
            (
                item
                for item in enabled
                if _normalize(item.capability_id) == _normalize(request.capability_id)
            ),
            None,
        )
        if exact_id is not None:
            match = self._match(
                request_record,
                exact_id,
                ReuseDecision.REUSE,
                ReuseReason.EXACT_CAPABILITY,
                1.0,
            )
            return self._result(
                request_record,
                catalog,
                ReuseDecision.REUSE,
                ReuseReason.EXACT_CAPABILITY,
                exact_id.capability_id,
                (match,),
            )

        scored: list[ReuseMatch] = []
        for candidate in enabled:
            responsibility_score = _jaccard(
                request_record.pure_responsibility_tokens,
                candidate.pure_responsibility_tokens,
            )
            architecture_overlap = tuple(
                sorted(request_record.architecture_set & candidate.architecture_set)
            )
            source_match = bool(request_record.source_key) and request_record.source_key == candidate.source_key

            same_responsibility = (
                responsibility_score >= self.strong_threshold
                and bool(request_record.responsibility_tokens)
            )
            structural_overlap = (
                source_match
                and bool(architecture_overlap)
                and responsibility_score >= self.extend_threshold
            )
            exact_structure = (
                source_match
                and bool(architecture_overlap)
                and (
                    responsibility_score >= self.strong_threshold
                    or (
                        _string_set(request_record.inputs) == _string_set(candidate.inputs)
                        and _string_set(request_record.outputs) == _string_set(candidate.outputs)
                    )
                )
            )

            if same_responsibility:
                decision = ReuseDecision.REUSE
                reason = ReuseReason.EXACT_RESPONSIBILITY
            elif exact_structure:
                decision = ReuseDecision.EXTEND
                reason = ReuseReason.STRUCTURAL_OVERLAP
            elif structural_overlap:
                decision = ReuseDecision.EXTEND
                reason = ReuseReason.HIGH_RESPONSIBILITY_OVERLAP
            else:
                continue

            confidence = max(
                responsibility_score,
                1.0 if exact_structure else 0.0,
                0.95 if same_responsibility else 0.0,
            )
            scored.append(
                ReuseMatch(
                    capability_id=candidate.capability_id,
                    decision=decision,
                    reason=reason,
                    responsibility_score=responsibility_score,
                    architecture_overlap=architecture_overlap,
                    source_of_truth_match=source_match,
                    confidence=confidence,
                )
            )

        scored.sort(key=lambda item: (-item.confidence, item.capability_id))

        if not scored:
            if not request.allow_create_new:
                return self._blocked(
                    request_record,
                    catalog,
                    ReuseReason.NO_EXISTING_MATCH,
                    ("new_capability_creation_disabled",),
                )
            return self._result(
                request_record,
                catalog,
                ReuseDecision.CREATE_NEW,
                ReuseReason.NO_EXISTING_MATCH,
                None,
                (),
            )

        strongest = scored[0]
        tied = tuple(
            item for item in scored if abs(item.confidence - strongest.confidence) < 0.02
        )
        if len(tied) > 1:
            return self._blocked(
                request_record,
                catalog,
                ReuseReason.MULTIPLE_MATCHES_AMBIGUOUS,
                ("multiple_strong_reuse_candidates",),
                matches=tuple(scored),
            )

        return self._result(
            request_record,
            catalog,
            strongest.decision,
            strongest.reason,
            strongest.capability_id,
            tuple(scored),
        )

    def assert_create_allowed(self, result: ReuseDecisionResult) -> None:
        if not result.allowed_to_create:
            raise RuntimeError(
                "New capability creation blocked by reuse guard: "
                f"{result.decision.value}/{result.reason.value}"
            )

    def revalidate(
        self,
        result: ReuseDecisionResult,
        current_catalog: Iterable[CapabilityRecord],
    ) -> ReuseDecisionResult:
        current = tuple(current_catalog)
        current_fingerprint = self.fingerprint_catalog(current)
        if current_fingerprint == result.catalog_fingerprint:
            return result
        return ReuseDecisionResult(
            decision=ReuseDecision.BLOCK,
            reason=ReuseReason.CATALOG_CHANGED,
            selected_capability_id=None,
            matches=result.matches,
            request_fingerprint=result.request_fingerprint,
            catalog_fingerprint=current_fingerprint,
            blockers=("capability_catalog_changed",),
            evidence={
                "previous_catalog_fingerprint": result.catalog_fingerprint,
                "current_catalog_fingerprint": current_fingerprint,
                "revalidation_required": True,
            },
        )

    @staticmethod
    def _match(
        request: CapabilityRecord,
        candidate: CapabilityRecord,
        decision: ReuseDecision,
        reason: ReuseReason,
        confidence: float,
    ) -> ReuseMatch:
        return ReuseMatch(
            capability_id=candidate.capability_id,
            decision=decision,
            reason=reason,
            responsibility_score=_jaccard(request.responsibility_tokens, candidate.responsibility_tokens),
            architecture_overlap=tuple(sorted(request.architecture_set & candidate.architecture_set)),
            source_of_truth_match=bool(request.source_key) and request.source_key == candidate.source_key,
            confidence=confidence,
        )

    @classmethod
    def _result(
        cls,
        request: CapabilityRecord,
        catalog: tuple[CapabilityRecord, ...],
        decision: ReuseDecision,
        reason: ReuseReason,
        selected_capability_id: str | None,
        matches: tuple[ReuseMatch, ...],
    ) -> ReuseDecisionResult:
        return ReuseDecisionResult(
            decision=decision,
            reason=reason,
            selected_capability_id=selected_capability_id,
            matches=matches,
            request_fingerprint=cls.fingerprint_record(request),
            catalog_fingerprint=cls.fingerprint_catalog(catalog),
            evidence={
                "candidate_count": len(catalog),
                "match_count": len(matches),
                "decision_is_derived": True,
                "revalidation_required_before_write": True,
            },
        )

    @classmethod
    def _blocked(
        cls,
        request: CapabilityRecord,
        catalog: tuple[CapabilityRecord, ...],
        reason: ReuseReason,
        blockers: tuple[str, ...],
        *,
        matches: tuple[ReuseMatch, ...] = (),
        evidence: Mapping[str, object] | None = None,
    ) -> ReuseDecisionResult:
        return ReuseDecisionResult(
            decision=ReuseDecision.BLOCK,
            reason=reason,
            selected_capability_id=None,
            matches=matches,
            request_fingerprint=cls.fingerprint_record(request),
            catalog_fingerprint=cls.fingerprint_catalog(catalog),
            blockers=blockers,
            evidence=dict(evidence or {}),
        )


__all__ = [
    "CapabilityRecord",
    "CapabilityRequest",
    "CapabilityReuseGuard",
    "ReuseDecision",
    "ReuseDecisionResult",
    "ReuseMatch",
    "ReuseReason",
]
