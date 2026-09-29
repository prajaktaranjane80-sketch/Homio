"""
CORE-005 / Point 09 — Observability & Evidence.

Owns immutable search observability/evidence metadata.

Responsibilities:
- query correlation
- source version
- projection version
- ranking version
- match explanation
- search evidence
- index health evidence
- reproducibility metadata

Does NOT:
- write external logs
- create a second audit engine
- create a second evidence store
- mutate canonical state
- make business decisions
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Mapping

from .search_consistency import (
    ConsistencyEvaluation,
    ConsistencyStatus,
)
from .search_domain import SearchIdentity, SearchRequest
from .search_ranking import RankingExplanation


class SearchObservabilityError(ValueError):
    """Base observability error."""


class SearchEvidenceError(SearchObservabilityError):
    """Raised for invalid search evidence."""


class SearchCorrelationError(SearchObservabilityError):
    """Raised for invalid correlation metadata."""


class IndexHealthStatus(str):
    HEALTHY = "HEALTHY"
    LAGGING = "LAGGING"
    STALE = "STALE"
    DEGRADED = "DEGRADED"
    UNKNOWN = "UNKNOWN"


def _required_text(
    value: str,
    field_name: str,
) -> str:
    if (
        not isinstance(
            value,
            str,
        )
        or not value.strip()
    ):
        raise SearchObservabilityError(
            f"{field_name} must be non-empty."
        )

    return value.strip()


@dataclass(frozen=True, slots=True)
class SearchCorrelation:
    """
    Correlation identity for one search operation.
    """

    correlation_id: str
    request_identity: SearchIdentity
    tenant_id: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "correlation_id",
            _required_text(
                self.correlation_id,
                "correlation_id",
            ),
        )

        object.__setattr__(
            self,
            "tenant_id",
            _required_text(
                self.tenant_id,
                "tenant_id",
            ),
        )

        if not isinstance(
            self.request_identity,
            SearchIdentity,
        ):
            raise SearchCorrelationError(
                "request_identity must be SearchIdentity."
            )


@dataclass(frozen=True, slots=True)
class SearchIndexHealthEvidence:
    """
    Point-in-time derived index health evidence.
    """

    status: str
    indexed_documents: int
    stale_documents: int
    failed_documents: int
    schema_version: int
    index_version: int
    index_fingerprint: str

    def __post_init__(self) -> None:
        allowed = {
            IndexHealthStatus.HEALTHY,
            IndexHealthStatus.LAGGING,
            IndexHealthStatus.STALE,
            IndexHealthStatus.DEGRADED,
            IndexHealthStatus.UNKNOWN,
        }

        if self.status not in allowed:
            raise SearchEvidenceError(
                "Invalid index health status."
            )

        for field_name in (
            "indexed_documents",
            "stale_documents",
            "failed_documents",
            "schema_version",
            "index_version",
        ):
            value = getattr(
                self,
                field_name,
            )

            if (
                isinstance(value, bool)
                or not isinstance(value, int)
                or value < 0
            ):
                raise SearchEvidenceError(
                    f"{field_name} must be a non-negative integer."
                )

        object.__setattr__(
            self,
            "index_fingerprint",
            _required_text(
                self.index_fingerprint,
                "index_fingerprint",
            ),
        )

        if (
            self.stale_documents > 0
            and self.status == IndexHealthStatus.HEALTHY
        ):
            raise SearchEvidenceError(
                "HEALTHY index cannot report stale documents."
            )


@dataclass(frozen=True, slots=True)
class SearchVersionEvidence:
    """
    Search version provenance.
    """

    source_version: int
    projection_version: int
    ranking_version: int | None

    def __post_init__(self) -> None:
        for field_name in (
            "source_version",
            "projection_version",
        ):
            value = getattr(
                self,
                field_name,
            )

            if (
                isinstance(value, bool)
                or not isinstance(value, int)
                or value < 1
            ):
                raise SearchEvidenceError(
                    f"{field_name} must be positive."
                )

        if self.ranking_version is not None:
            if (
                isinstance(
                    self.ranking_version,
                    bool,
                )
                or not isinstance(
                    self.ranking_version,
                    int,
                )
                or self.ranking_version < 1
            ):
                raise SearchEvidenceError(
                    "ranking_version must be positive."
                )


@dataclass(frozen=True, slots=True)
class SearchEvidence:
    """
    Immutable evidence record.

    This object is an evidence representation.
    It is not an evidence store.
    """

    correlation: SearchCorrelation
    versions: SearchVersionEvidence
    consistency: ConsistencyEvaluation | None = None
    ranking_explanation: RankingExplanation | None = None
    match_explanation: Mapping[str, Any] = field(
        default_factory=dict
    )
    index_health: SearchIndexHealthEvidence | None = None
    result_count: int = 0
    generated_at: datetime = field(
        default_factory=lambda: datetime.now(
            timezone.utc
        )
    )

    def __post_init__(self) -> None:
        if (
            isinstance(
                self.result_count,
                bool,
            )
            or not isinstance(
                self.result_count,
                int,
            )
            or self.result_count < 0
        ):
            raise SearchEvidenceError(
                "result_count must be non-negative."
            )

        if self.consistency is not None:
            if not isinstance(
                self.consistency,
                ConsistencyEvaluation,
            ):
                raise SearchEvidenceError(
                    "consistency must be ConsistencyEvaluation."
                )

        if self.ranking_explanation is not None:
            if not isinstance(
                self.ranking_explanation,
                RankingExplanation,
            ):
                raise SearchEvidenceError(
                    "ranking_explanation must be RankingExplanation."
                )

        if not isinstance(
            self.match_explanation,
            Mapping,
        ):
            raise SearchEvidenceError(
                "match_explanation must be a mapping."
            )

        if not isinstance(
            self.generated_at,
            datetime,
        ):
            raise SearchEvidenceError(
                "generated_at must be datetime."
            )

        if self.generated_at.tzinfo is None:
            raise SearchEvidenceError(
                "generated_at must be timezone-aware."
            )

        object.__setattr__(
            self,
            "match_explanation",
            dict(self.match_explanation),
        )

    @property
    def is_reproducible(self) -> bool:
        """
        Reproducibility requires source/projection metadata
        and, when ranking is involved, ranking provenance.
        """
        if (
            self.versions.source_version
            < self.versions.projection_version
        ):
            return False

        if self.ranking_explanation is not None:
            return (
                self.versions.ranking_version
                is not None
                and (
                    self.versions.ranking_version
                    == self.ranking_explanation.ranking_version
                )
            )

        return True

    @property
    def consistency_disclosed(self) -> bool:
        return self.consistency is not None

    def to_dict(self) -> dict[str, Any]:
        return {
            "correlation": {
                "correlation_id": (
                    self.correlation.correlation_id
                ),
                "request_identity": (
                    self.correlation.request_identity.value
                ),
                "tenant_id": self.correlation.tenant_id,
            },
            "versions": {
                "source_version": (
                    self.versions.source_version
                ),
                "projection_version": (
                    self.versions.projection_version
                ),
                "ranking_version": (
                    self.versions.ranking_version
                ),
            },
            "consistency": (
                {
                    "status": (
                        self.consistency.status.value
                    ),
                    "lag": self.consistency.lag,
                    "stale": self.consistency.stale,
                    "result_eligible": (
                        self.consistency.result_eligible
                    ),
                }
                if self.consistency is not None
                else None
            ),
            "ranking_explanation": (
                self.ranking_explanation.to_dict()
                if self.ranking_explanation is not None
                else None
            ),
            "match_explanation": dict(
                self.match_explanation
            ),
            "index_health": (
                {
                    "status": self.index_health.status,
                    "indexed_documents": (
                        self.index_health.indexed_documents
                    ),
                    "stale_documents": (
                        self.index_health.stale_documents
                    ),
                    "failed_documents": (
                        self.index_health.failed_documents
                    ),
                    "schema_version": (
                        self.index_health.schema_version
                    ),
                    "index_version": (
                        self.index_health.index_version
                    ),
                    "index_fingerprint": (
                        self.index_health.index_fingerprint
                    ),
                }
                if self.index_health is not None
                else None
            ),
            "result_count": self.result_count,
            "generated_at": self.generated_at.isoformat(),
        }

    def reproducibility_fingerprint(self) -> str:
        canonical = json.dumps(
            self.to_dict(),
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
        )

        return hashlib.sha256(
            canonical.encode("utf-8")
        ).hexdigest()


def build_search_correlation(
    request: SearchRequest,
    correlation_id: str,
) -> SearchCorrelation:
    if not isinstance(
        request,
        SearchRequest,
    ):
        raise SearchCorrelationError(
            "request must be SearchRequest."
        )

    return SearchCorrelation(
        correlation_id=correlation_id,
        request_identity=request.identity,
        tenant_id=request.tenant.tenant_id,
    )


__all__ = [
    "SearchObservabilityError",
    "SearchEvidenceError",
    "SearchCorrelationError",
    "IndexHealthStatus",
    "SearchCorrelation",
    "SearchIndexHealthEvidence",
    "SearchVersionEvidence",
    "SearchEvidence",
    "build_search_correlation",
]
