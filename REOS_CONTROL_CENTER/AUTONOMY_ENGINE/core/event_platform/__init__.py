"""
CORE-002 Event & Platform Core.

Transport-independent event domain and integration boundaries.
"""

from .event_domain import (
    EventDomainError,
    EventValidationError,
    EventTenantViolation,
    EventMutationError,
    EventSerializationError,
    EventTraceContext,
    EventEnvelope,
)

from .event_contract import (
    EventContractError,
    UnknownEventTypeError,
    UnsupportedEventVersionError,
    IncompatibleEventSchemaError,
    EventContract,
    EventContractRegistry,
)

from .event_delivery import (
    DeliveryError,
    DeliveryAuthorizationError,
    DuplicateDeliveryError,
    DeliveryStateError,
    DeliveryStatus,
    DeliveryFailureClass,
    DeliveryAttempt,
    DeliveryRecord,
    DeliveryPolicy,
    EventDeliveryCoordinator,
)

from .event_transaction import (
    TransactionBoundaryError,
    InvalidPublicationStateError,
    PublicationState,
    OutboxContract,
    PublicationStateMachine,
    build_publication_contract,
)

from .event_replay import (
    ReplayError,
    ReplayAuthorizationError,
    ReplayScopeError,
    ReplayDuplicateError,
    ReplayStatus,
    ReplayScope,
    ReplayRequest,
    ReplayResult,
    ReplayAuthorizationBoundary,
    ReplayCoordinator,
)

from .event_ordering import (
    OrderingError,
    StaleEventError,
    OutOfOrderEventError,
    OrderingViolation,
    StreamPosition,
    OrderingDecision,
    EventOrderingGuard,
    validate_stream_identity,
)

from .event_resilience import (
    ResilienceError,
    RetryExhaustedError,
    PoisonMessageError,
    FailureClass,
    FailureDisposition,
    FailureClassification,
    RetryDecision,
    QuarantineRecord,
    FailureClassifier,
    RetryPolicy,
    ResilienceBoundary,
)

from .event_observability import (
    EvidenceType,
    EventEvidence,
    DeliveryMetric,
    EventEvidenceFactory,
    validate_evidence_tenant,
)

from .event_security import (
    EventSecurityError,
    CrossTenantEventError,
    ProducerAuthorizationError,
    ConsumerAuthorizationError,
    EventIntegrityError,
    ProducerIdentity,
    ConsumerIdentity,
    EventSecurityBoundary,
)

from .event_reos_contract import (
    REOSEventContractError,
    REOSIntegrationContract,
    REOSIntegrationBoundary,
)

from .event_acrl_contract import (
    ACRLEventContractError,
    ACRLReconstructionDescriptor,
    ACRLCheckpointDescriptor,
    ACRLIntegrationBoundary,
)

from .event_transport import (
    TransportAdapterError,
    TransportSerializationError,
    TransportMessage,
    EventTransportAdapter,
    TransportRegistry,
)

__all__ = [
    "EventDomainError",
    "EventValidationError",
    "EventTenantViolation",
    "EventMutationError",
    "EventSerializationError",
    "EventTraceContext",
    "EventEnvelope",
    "EventContractError",
    "UnknownEventTypeError",
    "UnsupportedEventVersionError",
    "IncompatibleEventSchemaError",
    "EventContract",
    "EventContractRegistry",
    "DeliveryError",
    "DeliveryAuthorizationError",
    "DuplicateDeliveryError",
    "DeliveryStateError",
    "DeliveryStatus",
    "DeliveryFailureClass",
    "DeliveryAttempt",
    "DeliveryRecord",
    "DeliveryPolicy",
    "EventDeliveryCoordinator",
    "TransactionBoundaryError",
    "InvalidPublicationStateError",
    "PublicationState",
    "OutboxContract",
    "PublicationStateMachine",
    "build_publication_contract",
    "ReplayError",
    "ReplayAuthorizationError",
    "ReplayScopeError",
    "ReplayDuplicateError",
    "ReplayStatus",
    "ReplayScope",
    "ReplayRequest",
    "ReplayResult",
    "ReplayAuthorizationBoundary",
    "ReplayCoordinator",
    "OrderingError",
    "StaleEventError",
    "OutOfOrderEventError",
    "OrderingViolation",
    "StreamPosition",
    "OrderingDecision",
    "EventOrderingGuard",
    "validate_stream_identity",
    "ResilienceError",
    "RetryExhaustedError",
    "PoisonMessageError",
    "FailureClass",
    "FailureDisposition",
    "FailureClassification",
    "RetryDecision",
    "QuarantineRecord",
    "FailureClassifier",
    "RetryPolicy",
    "ResilienceBoundary",
    "EvidenceType",
    "EventEvidence",
    "DeliveryMetric",
    "EventEvidenceFactory",
    "validate_evidence_tenant",
    "EventSecurityError",
    "CrossTenantEventError",
    "ProducerAuthorizationError",
    "ConsumerAuthorizationError",
    "EventIntegrityError",
    "ProducerIdentity",
    "ConsumerIdentity",
    "EventSecurityBoundary",
    "REOSEventContractError",
    "REOSIntegrationContract",
    "REOSIntegrationBoundary",
    "ACRLEventContractError",
    "ACRLReconstructionDescriptor",
    "ACRLCheckpointDescriptor",
    "ACRLIntegrationBoundary",
    "TransportAdapterError",
    "TransportSerializationError",
    "TransportMessage",
    "EventTransportAdapter",
    "TransportRegistry",
]
