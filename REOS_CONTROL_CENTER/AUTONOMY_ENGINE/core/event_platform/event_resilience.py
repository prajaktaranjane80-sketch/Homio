from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable
from uuid import UUID


class ResilienceError(ValueError):
    """Base resilience error."""


class RetryExhaustedError(ResilienceError):
    """All permitted retry attempts were exhausted."""


class PoisonMessageError(ResilienceError):
    """Message is unsafe to continue retrying."""


class FailureClass(str, Enum):
    TRANSIENT = "TRANSIENT"
    PERMANENT = "PERMANENT"
    POISON = "POISON"
    AUTHORIZATION = "AUTHORIZATION"


class FailureDisposition(str, Enum):
    RETRY = "RETRY"
    DLQ = "DLQ"
    QUARANTINE = "QUARANTINE"
    DROP = "DROP"


@dataclass(frozen=True, slots=True)
class FailureClassification:
    failure_class: FailureClass
    disposition: FailureDisposition
    reason: str


@dataclass(frozen=True, slots=True)
class RetryDecision:
    attempt: int
    max_attempts: int
    should_retry: bool
    exhausted: bool


@dataclass(frozen=True, slots=True)
class QuarantineRecord:
    event_id: UUID
    tenant_id: UUID
    reason: str
    failure_class: FailureClass
    attempt: int


class FailureClassifier:
    """
    Pure failure classification policy.

    No retry execution, DLQ storage, or broker logic lives here.
    """

    def classify(
        self,
        exc: Exception,
    ) -> FailureClassification:
        name = type(exc).__name__.lower()

        if (
            "authorization" in name
            or "permission" in name
        ):
            return FailureClassification(
                failure_class=FailureClass.AUTHORIZATION,
                disposition=FailureDisposition.DROP,
                reason=type(exc).__name__,
            )

        if (
            "poison" in name
            or "deserialization" in name
        ):
            return FailureClassification(
                failure_class=FailureClass.POISON,
                disposition=FailureDisposition.QUARANTINE,
                reason=type(exc).__name__,
            )

        if isinstance(
            exc,
            (TypeError, ValueError),
        ):
            return FailureClassification(
                failure_class=FailureClass.PERMANENT,
                disposition=FailureDisposition.DLQ,
                reason=type(exc).__name__,
            )

        return FailureClassification(
            failure_class=FailureClass.TRANSIENT,
            disposition=FailureDisposition.RETRY,
            reason=type(exc).__name__,
        )


class RetryPolicy:
    def __init__(
        self,
        *,
        max_attempts: int = 3,
    ) -> None:
        if (
            not isinstance(max_attempts, int)
            or max_attempts < 1
        ):
            raise ValueError(
                "max_attempts must be >= 1"
            )

        self.max_attempts = max_attempts

    def decide(
        self,
        *,
        attempt: int,
        failure_class: FailureClass,
    ) -> RetryDecision:
        if (
            not isinstance(attempt, int)
            or attempt < 1
        ):
            raise ValueError(
                "attempt must be >= 1"
            )

        terminal = failure_class in {
            FailureClass.PERMANENT,
            FailureClass.POISON,
            FailureClass.AUTHORIZATION,
        }

        exhausted = (
            attempt >= self.max_attempts
        )

        return RetryDecision(
            attempt=attempt,
            max_attempts=self.max_attempts,
            should_retry=(
                not terminal
                and not exhausted
            ),
            exhausted=exhausted,
        )


class ResilienceBoundary:
    """
    Fail-closed resilience decision boundary.

    The caller supplies execution.
    CORE-002 decides only classification/disposition.
    """

    def __init__(
        self,
        *,
        classifier: FailureClassifier | None = None,
        retry_policy: RetryPolicy | None = None,
    ) -> None:
        self.classifier = (
            classifier
            or FailureClassifier()
        )
        self.retry_policy = (
            retry_policy
            or RetryPolicy()
        )

    def handle_failure(
        self,
        *,
        event_id: UUID,
        tenant_id: UUID,
        attempt: int,
        exc: Exception,
    ) -> FailureClassification:
        classification = (
            self.classifier.classify(exc)
        )

        decision = self.retry_policy.decide(
            attempt=attempt,
            failure_class=(
                classification.failure_class
            ),
        )

        if decision.exhausted and (
            classification.failure_class
            == FailureClass.TRANSIENT
        ):
            return FailureClassification(
                failure_class=FailureClass.TRANSIENT,
                disposition=FailureDisposition.DLQ,
                reason="retry_exhausted",
            )

        return classification

    def execute_once(
        self,
        *,
        operation: Callable[[], None],
    ) -> None:
        """
        Single execution boundary.

        It deliberately does not hide retries in a loop.
        """
        if not callable(operation):
            raise TypeError(
                "operation must be callable"
            )

        operation()


__all__ = [
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
]
