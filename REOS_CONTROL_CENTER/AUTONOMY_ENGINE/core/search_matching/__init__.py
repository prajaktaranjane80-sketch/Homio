"""
CORE-005 Search & Matching Core.

Public integration surface for the complete 13-domain architecture.

The package exposes contracts from each domain while keeping
runtime backend implementations behind adapter boundaries.
"""

from .acrl_integration import (
    ACRL_CONTRACT_VERSION,
    ACRLDependency,
    ACRLDiscoverabilityError,
    ACRLDriftError,
    ACRLDriftReport,
    ACRLIntegrationContract,
    ACRLIntegrationError,
    ACRLReconstructionManifest,
)

from .matching import (
    MatchExplanation,
    MatchRecommendation,
    MatchingCandidateError,
    MatchingCriteriaError,
    MatchingDomainError,
    MatchingProfile,
    MatchingRecommendationPipeline,
    MatchingTenantError,
)

from .projection_sync import (
    ProjectionApplyStatus,
    ProjectionChange,
    ProjectionEventError,
    ProjectionOperation,
    ProjectionSyncError,
    ProjectionTenantError,
    ProjectionVersion,
    ProjectionVersionError,
    SearchProjectionSink,
    SearchProjectionSynchronizer,
    SearchSourceEvent,
)

from .reos_integration import (
    CORE_005_COMPONENT,
    REOS_AUTHORITY,
    REOS_INTEGRATION_SCHEMA_VERSION,
    REOSAuthorityViolation,
    REOSCompatibilityError,
    REOSCompatibilityProfile,
    REOSIntegrationContract,
    REOSIntegrationDecision,
    REOSIntegrationError,
    REOSIntegrationReport,
    REOSVerificationError,
    REOSVerificationEvidence,
)

from .runtime_adapter import (
    BackendIndependentSearchRuntime,
    DeterministicRebuildAdapter,
    QdrantIndexAdapter,
    RuntimeAdapterCapabilityError,
    RuntimeAdapterConfigurationError,
    RuntimeAdapterError,
    RuntimeAdapterOperationError,
    RuntimeAdapterRegistry,
    RuntimeBackendIdentity,
    RuntimeSearchHit,
    SearchBackendAdapter,
    SearchIndexAdapter,
    SearchRebuildAdapter,
)

from .search_consistency import (
    ConsistencyEvent,
    ConsistencyEvaluation,
    ConsistencyStatus,
    ConsistencyVersionState,
    SearchConsistencyError,
    SearchConsistencyTenantError,
    SearchConsistencyTracker,
    SearchConsistencyVersionError,
)

from .search_domain import (
    SearchDomainError,
    SearchIdentity,
    SearchPagination,
    SearchPaginationError,
    SearchQueryError,
    SearchRequest,
    SearchResultError,
    SearchResultItem,
    SearchResultPage,
    SearchSort,
    SearchSortDirection,
    SearchSortError,
    SearchSortField,
    SearchTenantContext,
    SearchTenantContextError,
    normalize_search_query,
)

from .search_execution import (
    CallableSearchCandidateProvider,
    SearchCandidateProvider,
    SearchExecutionBoundsError,
    SearchExecutionCandidate,
    SearchExecutionCandidateError,
    SearchExecutionConfig,
    SearchExecutionEngine,
    SearchExecutionError,
    SearchExecutionQueryError,
)

from .search_filters import (
    StructuredSearchFilter,
    StructuredSearchFilterError,
    StructuredSearchTenantError,
)

from .search_index_contract import (
    EXPECTED_INDEX_FINGERPRINT,
    SEARCH_INDEX_VERSION,
    SEARCH_INDEXED_FIELDS,
    SEARCH_SCHEMA_VERSION,
    SEARCH_SOURCE_DOMAIN,
    InventoryIndexDocument,
    InventoryIndexingError,
    InventoryIndexingHook,
    InventoryIndexStaleVersionError,
    SearchIndexContractError,
    SearchIndexDocumentError,
    SearchIndexOperation,
    SearchIndexSchemaError,
    SearchIndexScopeError,
    SearchIndexVersionError,
    build_inventory_index,
    build_inventory_index_delete,
    calculate_index_fingerprint,
)

from .search_observability import (
    IndexHealthStatus,
    SearchCorrelation,
    SearchCorrelationError,
    SearchEvidence,
    SearchEvidenceError,
    SearchIndexHealthEvidence,
    SearchObservabilityError,
    SearchVersionEvidence,
    build_search_correlation,
)

from .search_ranking import (
    RANKING_VERSION,
    RankedSearchResult,
    RankingCandidate,
    RankingConfig,
    RankingExplanation,
    RankingFeature,
    SearchRankingError,
    SearchRankingInputError,
    SearchRankingPipeline,
    SearchRankingVersionError,
)

from .search_security import (
    CallableSearchAuthorizationProvider,
    SearchAbuseBoundaryError,
    SearchAuthorizationContext,
    SearchAuthorizationError,
    SearchAuthorizationProvider,
    SearchDataLeakageError,
    SearchSecurityBoundary,
    SearchSecurityDecision,
    SearchSecurityError,
    SearchSecurityPolicy,
    SearchTenantIsolationError,
    SecurityDecision,
    SecurityDenyReason,
    sanitize_search_document,
)

from .search_visibility import (
    SearchVisibilityPolicy,
    TenantScopeError,
    TenantVisibilityFilter,
    VisibilityDecision,
    VisibilityError,
    VisibilityPolicyError,
    VisibilityReason,
    VisibilityResultError,
)


__all__ = [
    # Point 01
    "SearchDomainError",
    "SearchIdentity",
    "SearchPagination",
    "SearchPaginationError",
    "SearchQueryError",
    "SearchRequest",
    "SearchResultError",
    "SearchResultItem",
    "SearchResultPage",
    "SearchSort",
    "SearchSortDirection",
    "SearchSortError",
    "SearchSortField",
    "SearchTenantContext",
    "SearchTenantContextError",
    "normalize_search_query",

    # Point 02
    "SEARCH_SCHEMA_VERSION",
    "SEARCH_INDEX_VERSION",
    "SEARCH_SOURCE_DOMAIN",
    "SEARCH_INDEXED_FIELDS",
    "EXPECTED_INDEX_FINGERPRINT",
    "calculate_index_fingerprint",
    "InventoryIndexDocument",
    "InventoryIndexingError",
    "InventoryIndexingHook",
    "InventoryIndexStaleVersionError",
    "SearchIndexContractError",
    "SearchIndexDocumentError",
    "SearchIndexOperation",
    "SearchIndexSchemaError",
    "SearchIndexScopeError",
    "SearchIndexVersionError",
    "build_inventory_index",
    "build_inventory_index_delete",

    # Point 03
    "ProjectionApplyStatus",
    "ProjectionChange",
    "ProjectionEventError",
    "ProjectionOperation",
    "ProjectionSyncError",
    "ProjectionTenantError",
    "ProjectionVersion",
    "ProjectionVersionError",
    "SearchProjectionSink",
    "SearchProjectionSynchronizer",
    "SearchSourceEvent",

    # Point 04
    "CallableSearchCandidateProvider",
    "SearchCandidateProvider",
    "SearchExecutionBoundsError",
    "SearchExecutionCandidate",
    "SearchExecutionCandidateError",
    "SearchExecutionConfig",
    "SearchExecutionEngine",
    "SearchExecutionError",
    "SearchExecutionQueryError",

    # Point 05
    "MatchExplanation",
    "MatchRecommendation",
    "MatchingCandidateError",
    "MatchingCriteriaError",
    "MatchingDomainError",
    "MatchingProfile",
    "MatchingRecommendationPipeline",
    "MatchingTenantError",

    # Point 06
    "RANKING_VERSION",
    "RankedSearchResult",
    "RankingCandidate",
    "RankingConfig",
    "RankingExplanation",
    "RankingFeature",
    "SearchRankingError",
    "SearchRankingInputError",
    "SearchRankingPipeline",
    "SearchRankingVersionError",

    # Point 07
    "ConsistencyEvent",
    "ConsistencyEvaluation",
    "ConsistencyStatus",
    "ConsistencyVersionState",
    "SearchConsistencyError",
    "SearchConsistencyTenantError",
    "SearchConsistencyTracker",
    "SearchConsistencyVersionError",

    # Point 08
    "CallableSearchAuthorizationProvider",
    "SearchAbuseBoundaryError",
    "SearchAuthorizationContext",
    "SearchAuthorizationError",
    "SearchAuthorizationProvider",
    "SearchDataLeakageError",
    "SearchSecurityBoundary",
    "SearchSecurityDecision",
    "SearchSecurityError",
    "SearchSecurityPolicy",
    "SearchTenantIsolationError",
    "SecurityDecision",
    "SecurityDenyReason",
    "sanitize_search_document",

    # Existing visibility boundary
    "SearchVisibilityPolicy",
    "TenantScopeError",
    "TenantVisibilityFilter",
    "VisibilityDecision",
    "VisibilityError",
    "VisibilityPolicyError",
    "VisibilityReason",
    "VisibilityResultError",

    # Point 09
    "IndexHealthStatus",
    "SearchCorrelation",
    "SearchCorrelationError",
    "SearchEvidence",
    "SearchEvidenceError",
    "SearchIndexHealthEvidence",
    "SearchObservabilityError",
    "SearchVersionEvidence",
    "build_search_correlation",

    # Point 10
    "CORE_005_COMPONENT",
    "REOS_AUTHORITY",
    "REOS_INTEGRATION_SCHEMA_VERSION",
    "REOSAuthorityViolation",
    "REOSCompatibilityError",
    "REOSCompatibilityProfile",
    "REOSIntegrationContract",
    "REOSIntegrationDecision",
    "REOSIntegrationError",
    "REOSIntegrationReport",
    "REOSVerificationError",
    "REOSVerificationEvidence",

    # Point 11
    "ACRL_CONTRACT_VERSION",
    "ACRLDependency",
    "ACRLDiscoverabilityError",
    "ACRLDriftError",
    "ACRLDriftReport",
    "ACRLIntegrationContract",
    "ACRLIntegrationError",
    "ACRLReconstructionManifest",

    # Point 12
    "BackendIndependentSearchRuntime",
    "DeterministicRebuildAdapter",
    "QdrantIndexAdapter",
    "RuntimeAdapterCapabilityError",
    "RuntimeAdapterConfigurationError",
    "RuntimeAdapterError",
    "RuntimeAdapterOperationError",
    "RuntimeAdapterRegistry",
    "RuntimeBackendIdentity",
    "RuntimeSearchHit",
    "SearchBackendAdapter",
    "SearchIndexAdapter",
    "SearchRebuildAdapter",
]
