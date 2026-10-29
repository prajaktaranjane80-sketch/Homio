
"""Evidence-bounded RAG orchestration for HOMIO / REOS.

Reuses the existing search owner and provider-independent model gateway.
Does not own identity, canonical inventory, authorization, indexing or a
parallel vector store. Safe by default: RAG generation remains disabled
unless explicitly enabled by approved server-side runtime configuration.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from time import monotonic
from typing import Protocol

from .contracts import (
    AIRequest,
    AIResponse,
    ObservabilityEvent,
    RequestContext,
    _identifier,
    _positive_int,
    _text,
)
from .errors import (
    AIPlatformError,
    GatewayDisabledError,
    InvalidRequestError,
    ObservabilityUnavailableError,
    ProviderCallFailedError,
    ProviderResponseInvalidError,
    RequestContextMissingError,
    RetrievalResultInvalidError,
    RetrievalUnavailableError,
)
from .observability import StructuredLoggingObservability
from .ports import ObservabilityPort
from .prompt_templates import PromptTemplate, SourceCitation
from .retrieval_adapter import (
    RetrievalRequest,
    RetrievalResponse,
    RetrievedSource,
)

_INLINE_CITATION = re.compile(r"\[(S[0-9]+)\]")

# The current RetrievedSource contract does not contain authoritative legal,
# valuation, credit or investment evidence. Until canonical source contracts
# supply these facts, this read-only RAG boundary must qualify such questions.
_UNSUPPORTED_HIGH_IMPACT_PATTERNS = (
    re.compile(
        r"\b(?:valuation|market value|appraisal|appraised value|property worth)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:rental yield|yield|roi|return on investment|capital appreciation|"
        r"investment return|guaranteed return)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:clear title|title clearance|encumbrance|rera|litigation|"
        r"legal approval|legally approved|legal status|title deed|ownership verified)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:loan eligibility|loan approval|mortgage|emi|affordability|"
        r"creditworthiness|financing eligibility)\b",
        re.IGNORECASE,
    ),
)


class RetrievalPort(Protocol):
    """Existing authorized retrieval adapter."""

    def retrieve(self, request: RetrievalRequest) -> RetrievalResponse:
        """Return tenant/resource-scoped, provenance-checked results."""


class ModelGatewayPort(Protocol):
    """Existing gateway enforcing authorization, usage and telemetry."""

    def complete(self, request: AIRequest) -> AIResponse:
        """Execute one governed text-generation request."""


@dataclass(frozen=True, slots=True)
class RAGSettings:
    """Bounded safe-by-default settings; not provider credentials."""

    enabled: bool = False
    max_question_chars: int = 4_000
    max_sources: int = 8
    max_context_chars: int = 12_000
    max_output_tokens: int = 512
    max_output_chars: int = 8_000

    def __post_init__(self) -> None:
        if not isinstance(self.enabled, bool):
            raise TypeError("enabled must be a boolean")

        for name, value, maximum in (
            ("max_question_chars", self.max_question_chars, 16_000),
            ("max_sources", self.max_sources, 100),
            ("max_context_chars", self.max_context_chars, 100_000),
            ("max_output_tokens", self.max_output_tokens, 8_192),
            ("max_output_chars", self.max_output_chars, 100_000),
        ):
            _positive_int(value, name)
            if value > maximum:
                raise ValueError(f"{name} exceeds its hard safety limit")


@dataclass(frozen=True, slots=True)
class RAGRequest:
    """Internal server-side request; context must derive from trusted auth."""

    request_id: str
    question: str
    embedding_model_id: str
    context: RequestContext | None
    model_id: str | None = None
    source_limit: int = 5
    max_output_tokens: int | None = None
    idempotency_key: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "request_id", _identifier(self.request_id, "request_id")
        )
        object.__setattr__(
            self,
            "question",
            _text(
                self.question,
                "question",
                16_000,
                allow_multiline=False,
            ),
        )
        object.__setattr__(
            self,
            "embedding_model_id",
            _identifier(self.embedding_model_id, "embedding_model_id"),
        )

        if self.context is not None and not isinstance(
            self.context, RequestContext
        ):
            raise TypeError("context must be RequestContext or None")

        if self.model_id is not None:
            object.__setattr__(
                self, "model_id", _identifier(self.model_id, "model_id")
            )

        _positive_int(self.source_limit, "source_limit")
        if self.max_output_tokens is not None:
            _positive_int(self.max_output_tokens, "max_output_tokens")

        if self.idempotency_key is not None:
            object.__setattr__(
                self,
                "idempotency_key",
                _identifier(self.idempotency_key, "idempotency_key"),
            )


@dataclass(frozen=True, slots=True)
class RAGResponse:
    """Answer with verified citations and prompt/model provenance."""

    request_id: str
    answer: str
    citations: tuple[SourceCitation, ...]
    insufficient_evidence: bool
    generation_performed: bool
    provider_id: str | None
    model_id: str | None
    prompt_template_id: str
    prompt_template_version: str
    policy_version: str
    retrieved_source_count: int

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "request_id", _identifier(self.request_id, "request_id")
        )
        object.__setattr__(
            self,
            "answer",
            _text(self.answer, "answer", 100_000, allow_multiline=True),
        )

        for name in ("prompt_template_id", "prompt_template_version", "policy_version"):
            object.__setattr__(
                self, name, _identifier(getattr(self, name), name)
            )

        if not isinstance(self.insufficient_evidence, bool):
            raise TypeError("insufficient_evidence must be a boolean")
        if not isinstance(self.generation_performed, bool):
            raise TypeError("generation_performed must be a boolean")

        if (
            isinstance(self.retrieved_source_count, bool)
            or not isinstance(self.retrieved_source_count, int)
            or self.retrieved_source_count < 0
        ):
            raise ValueError("retrieved_source_count must be a non-negative integer")

        citations = tuple(self.citations)
        if any(not isinstance(item, SourceCitation) for item in citations):
            raise TypeError("citations must contain SourceCitation values")
        labels = [item.citation_id for item in citations]
        if len(set(labels)) != len(labels):
            raise ValueError("response citations must be unique")
        object.__setattr__(self, "citations", citations)

        if self.generation_performed:
            if self.provider_id is None or self.model_id is None:
                raise ValueError("generated responses require provider/model IDs")
            object.__setattr__(
                self, "provider_id", _identifier(self.provider_id, "provider_id")
            )
            object.__setattr__(
                self, "model_id", _identifier(self.model_id, "model_id")
            )
        else:
            if self.provider_id is not None or self.model_id is not None:
                raise ValueError(
                    "non-generated responses must not claim provider/model use"
                )
            if not self.insufficient_evidence or citations:
                raise ValueError(
                    "non-generated responses must be evidence-limited"
                )
            if self.retrieved_source_count != 0:
                raise ValueError(
                    "non-generated evidence-limited responses require zero sources"
                )

        if not self.insufficient_evidence and not citations:
            raise ValueError(
                "answers marked sufficiently supported must have citations"
            )


class RAGPipeline:
    """Retrieve authorized evidence, assemble bounded prompts and validate output."""

    _OPERATION = "property.search"
    _NO_EVIDENCE_ANSWER = (
        "I couldn't find enough authorized, current property records to answer "
        "this question. Please refine the query or provide more detail."
    )
    _HIGH_IMPACT_QUALIFICATION = (
        "This AI property-search service cannot verify legal title or approvals, "
        "property valuation, rental yield, loan eligibility, affordability, or "
        "investment returns from its current listing fields. Check the relevant "
        "official records and consult an appropriately qualified property, "
        "legal, or financial professional."
    )

    def __init__(
        self,
        *,
        retrieval: RetrievalPort,
        gateway: ModelGatewayPort,
        settings: RAGSettings | None = None,
        prompt_template: PromptTemplate | None = None,
        observability: ObservabilityPort | None = None,
    ) -> None:
        if retrieval is None or not callable(getattr(retrieval, "retrieve", None)):
            raise TypeError("retrieval must expose a callable retrieve method")
        if gateway is None or not callable(getattr(gateway, "complete", None)):
            raise TypeError("gateway must expose a callable complete method")

        selected_settings = settings if settings is not None else RAGSettings()
        if not isinstance(selected_settings, RAGSettings):
            raise TypeError("settings must be RAGSettings")

        selected_template = (
            prompt_template if prompt_template is not None else PromptTemplate()
        )
        if not isinstance(selected_template, PromptTemplate):
            raise TypeError("prompt_template must be PromptTemplate")

        selected_observability = (
            observability
            if observability is not None
            else StructuredLoggingObservability()
        )
        if not callable(getattr(selected_observability, "emit", None)):
            raise TypeError("observability must expose a callable emit method")

        self._retrieval = retrieval
        self._gateway = gateway
        self._settings = selected_settings
        self._prompt_template = selected_template
        self._observability = selected_observability

    @staticmethod
    def _duration_ms(started_at: float) -> int:
        return max(0, int((monotonic() - started_at) * 1000))

    @staticmethod
    def _event_error_code(
        error: BaseException | None,
        fallback: str | None = None,
    ) -> str | None:
        if error is None:
            return fallback
        code = getattr(error, "code", None)
        value = getattr(code, "value", None)
        if isinstance(value, str) and value:
            return value
        if isinstance(code, str) and code:
            return code
        return fallback

    def _emit_event(
        self,
        request: RAGRequest,
        *,
        event_name: str,
        outcome: str,
        error_code: str | None = None,
        duration_ms: int | None = None,
        provider_id: str | None = None,
        model_id: str | None = None,
    ) -> None:
        """Emit only approved operational fields; never request/property content."""
        context = request.context
        correlation_id = (
            context.correlation_id
            if isinstance(context, RequestContext)
            else request.request_id
        )
        event = ObservabilityEvent(
            event_name=event_name,
            request_id=request.request_id,
            correlation_id=correlation_id,
            outcome=outcome,
            provider_id=provider_id,
            model_id=model_id,
            duration_ms=duration_ms,
            error_code=error_code,
        )
        try:
            self._observability.emit(event)
        except Exception:
            # This path requires an audit record. Never return an answer after
            # a required telemetry event failed to be recorded.
            raise ObservabilityUnavailableError() from None

    def _evidence_limited_response(
        self,
        request: RAGRequest,
        *,
        answer: str,
    ) -> RAGResponse:
        return RAGResponse(
            request_id=request.request_id,
            answer=answer,
            citations=(),
            insufficient_evidence=True,
            generation_performed=False,
            provider_id=None,
            model_id=None,
            prompt_template_id=self._prompt_template.template_id,
            prompt_template_version=self._prompt_template.template_version,
            policy_version=self._prompt_template.policy_version,
            retrieved_source_count=0,
        )

    def _reject_retrieval_result(
        self,
        request: RAGRequest,
        *,
        duration_ms: int | None = None,
    ) -> None:
        self._emit_event(
            request,
            event_name="RETRIEVAL_VALIDATION_FAILED",
            outcome="FAILED",
            error_code="AI_RETRIEVAL_RESULT_INVALID",
            duration_ms=duration_ms,
        )
        raise RetrievalResultInvalidError()

    @staticmethod
    def _is_unsupported_high_impact_question(question: str) -> bool:
        normalized = " ".join(question.casefold().split())
        return any(
            pattern.search(normalized)
            for pattern in _UNSUPPORTED_HIGH_IMPACT_PATTERNS
        )

    @staticmethod
    def _conflicting_evidence_labels(
        sources: tuple[SourceCitation, ...],
    ) -> tuple[str, ...]:
        """Find conflicting critical facts for a listing within one project."""
        groups: dict[tuple[str, str], list[SourceCitation]] = {}
        for source in sources:
            key = (
                source.project_id.casefold(),
                source.inventory_code.casefold(),
            )
            groups.setdefault(key, []).append(source)

        conflicting_ids: set[str] = set()
        for records in groups.values():
            if len(records) < 2:
                continue
            has_conflict = any(
                len({
                    getattr(record, field_name).strip().casefold()
                    for record in records
                }) > 1
                for field_name in ("availability", "lifecycle", "inventory_type")
            )
            if has_conflict:
                conflicting_ids.update(record.citation_id for record in records)

        return tuple(
            source.citation_id
            for source in sources
            if source.citation_id in conflicting_ids
        )

    def answer(self, request: RAGRequest) -> RAGResponse:
        """Answer a read-only property question using authorized evidence only."""
        if not isinstance(request, RAGRequest):
            raise InvalidRequestError()

        if not self._settings.enabled:
            self._emit_event(
                request,
                event_name="RAG_DISABLED",
                outcome="FAILED",
                error_code="AI_GATEWAY_DISABLED",
            )
            raise GatewayDisabledError()

        context = request.context
        if not isinstance(context, RequestContext):
            self._emit_event(
                request,
                event_name="RAG_REQUEST_REJECTED",
                outcome="FAILED",
                error_code="AI_REQUEST_CONTEXT_MISSING",
            )
            raise RequestContextMissingError()

        if (
            len(request.question) > self._settings.max_question_chars
            or request.source_limit > self._settings.max_sources
            or (
                request.max_output_tokens is not None
                and request.max_output_tokens > self._settings.max_output_tokens
            )
        ):
            self._emit_event(
                request,
                event_name="RAG_REQUEST_REJECTED",
                outcome="FAILED",
                error_code="AI_INVALID_REQUEST",
            )
            raise InvalidRequestError()

        # No authoritative price/legal/finance evidence contract is available
        # in the current listing source. Qualify these claims before retrieval.
        if self._is_unsupported_high_impact_question(request.question):
            self._emit_event(
                request,
                event_name="UNSUPPORTED_HIGH_IMPACT_REQUEST",
                outcome="QUALIFIED",
                error_code="AI_UNSUPPORTED_OPERATION",
            )
            return self._evidence_limited_response(
                request,
                answer=self._HIGH_IMPACT_QUALIFICATION,
            )

        output_tokens = (
            request.max_output_tokens or self._settings.max_output_tokens
        )
        retrieval_request = RetrievalRequest(
            request_id=request.request_id,
            query_text=request.question,
            embedding_model_id=request.embedding_model_id,
            context=context,
            limit=request.source_limit,
        )

        retrieval_started = monotonic()
        try:
            retrieval_response = self._retrieval.retrieve(retrieval_request)
        except AIPlatformError as exc:
            self._emit_event(
                request,
                event_name="RETRIEVAL_FAILED",
                outcome="FAILED",
                error_code=self._event_error_code(
                    exc, "AI_RETRIEVAL_UNAVAILABLE"
                ),
                duration_ms=self._duration_ms(retrieval_started),
            )
            raise
        except Exception:
            self._emit_event(
                request,
                event_name="RETRIEVAL_FAILED",
                outcome="FAILED",
                error_code="AI_RETRIEVAL_UNAVAILABLE",
                duration_ms=self._duration_ms(retrieval_started),
            )
            raise RetrievalUnavailableError() from None

        retrieval_duration = self._duration_ms(retrieval_started)
        if not isinstance(retrieval_response, RetrievalResponse):
            self._reject_retrieval_result(request, duration_ms=retrieval_duration)

        if (
            retrieval_response.request_id != request.request_id
            or retrieval_response.tenant_id != context.tenant_id
        ):
            self._reject_retrieval_result(request, duration_ms=retrieval_duration)

        results = tuple(retrieval_response.results)
        if len(results) > request.source_limit:
            self._reject_retrieval_result(request, duration_ms=retrieval_duration)
        if any(not isinstance(item, RetrievedSource) for item in results):
            self._reject_retrieval_result(request, duration_ms=retrieval_duration)
        if any(item.tenant_id != context.tenant_id for item in results):
            self._reject_retrieval_result(request, duration_ms=retrieval_duration)

        record_ids = [item.record_id for item in results]
        if len(set(record_ids)) != len(record_ids):
            self._reject_retrieval_result(request, duration_ms=retrieval_duration)

        self._emit_event(
            request,
            event_name="RETRIEVAL_COMPLETED",
            outcome="SUCCEEDED" if results else "NO_EVIDENCE",
            error_code=None if results else "AI_RETRIEVAL_NO_EVIDENCE",
            duration_ms=retrieval_duration,
        )

        if not results:
            response = self._evidence_limited_response(
                request,
                answer=self._NO_EVIDENCE_ANSWER,
            )
            self._emit_event(
                request,
                event_name="RAG_RESPONSE_QUALIFIED",
                outcome="QUALIFIED",
                error_code="AI_RETRIEVAL_NO_EVIDENCE",
                duration_ms=retrieval_duration,
            )
            return response

        try:
            rendered = self._prompt_template.render(request.question, results)
        except (TypeError, ValueError):
            self._emit_event(
                request,
                event_name="RAG_REQUEST_REJECTED",
                outcome="FAILED",
                error_code="AI_INVALID_REQUEST",
            )
            raise InvalidRequestError() from None

        if len(rendered.prompt) > self._settings.max_context_chars:
            self._emit_event(
                request,
                event_name="RAG_REQUEST_REJECTED",
                outcome="FAILED",
                error_code="AI_INVALID_REQUEST",
            )
            raise InvalidRequestError()

        gateway_request = AIRequest(
            request_id=request.request_id,
            operation=self._OPERATION,
            input_text=rendered.prompt,
            context=context,
            model_id=request.model_id,
            max_output_tokens=output_tokens,
            idempotency_key=request.idempotency_key,
        )

        generation_started = monotonic()
        try:
            gateway_response = self._gateway.complete(gateway_request)
        except AIPlatformError as exc:
            self._emit_event(
                request,
                event_name="RAG_GENERATION_FAILED",
                outcome="FAILED",
                error_code=self._event_error_code(
                    exc, "AI_PROVIDER_CALL_FAILED"
                ),
                duration_ms=self._duration_ms(generation_started),
            )
            raise
        except Exception:
            self._emit_event(
                request,
                event_name="RAG_GENERATION_FAILED",
                outcome="FAILED",
                error_code="AI_PROVIDER_CALL_FAILED",
                duration_ms=self._duration_ms(generation_started),
            )
            raise ProviderCallFailedError() from None

        if not isinstance(gateway_response, AIResponse):
            self._emit_event(
                request,
                event_name="RAG_OUTPUT_REJECTED",
                outcome="FAILED",
                error_code="AI_PROVIDER_RESPONSE_INVALID",
                duration_ms=self._duration_ms(generation_started),
            )
            raise ProviderResponseInvalidError()

        if (
            gateway_response.request_id != request.request_id
            or gateway_response.correlation_id != context.correlation_id
        ):
            self._emit_event(
                request,
                event_name="RAG_OUTPUT_REJECTED",
                outcome="FAILED",
                error_code="AI_PROVIDER_RESPONSE_INVALID",
                duration_ms=self._duration_ms(generation_started),
                provider_id=gateway_response.provider_id,
                model_id=gateway_response.model_id,
            )
            raise ProviderResponseInvalidError()

        if len(gateway_response.text) > self._settings.max_output_chars:
            self._emit_event(
                request,
                event_name="RAG_OUTPUT_REJECTED",
                outcome="FAILED",
                error_code="AI_PROVIDER_RESPONSE_INVALID",
                duration_ms=self._duration_ms(generation_started),
                provider_id=gateway_response.provider_id,
                model_id=gateway_response.model_id,
            )
            raise ProviderResponseInvalidError()

        try:
            answer, citation_labels, insufficient = self._parse_output(
                gateway_response.text,
                allowed_labels={
                    source.citation_id for source in rendered.sources
                },
            )
        except AIPlatformError as exc:
            self._emit_event(
                request,
                event_name="RAG_OUTPUT_REJECTED",
                outcome="FAILED",
                error_code=self._event_error_code(
                    exc, "AI_PROVIDER_RESPONSE_INVALID"
                ),
                duration_ms=self._duration_ms(generation_started),
                provider_id=gateway_response.provider_id,
                model_id=gateway_response.model_id,
            )
            raise

        conflicting_labels = self._conflicting_evidence_labels(rendered.sources)
        if conflicting_labels:
            # Structured source conflict overrides model confidence.
            answer = (
                "The retrieved records disagree about current listing details, "
                "so I cannot safely confirm the property's current status. "
                "Please verify it with the responsible listing source."
            )
            citation_labels = conflicting_labels
            insufficient = True
            self._emit_event(
                request,
                event_name="GROUNDING_CONFLICT_DETECTED",
                outcome="QUALIFIED",
                error_code="AI_RETRIEVAL_SOURCE_CONFLICT",
                duration_ms=self._duration_ms(generation_started),
                provider_id=gateway_response.provider_id,
                model_id=gateway_response.model_id,
            )

        source_by_label = {
            source.citation_id: source for source in rendered.sources
        }
        citations = tuple(source_by_label[label] for label in citation_labels)
        response = RAGResponse(
            request_id=request.request_id,
            answer=answer,
            citations=citations,
            insufficient_evidence=insufficient,
            generation_performed=True,
            provider_id=gateway_response.provider_id,
            model_id=gateway_response.model_id,
            prompt_template_id=rendered.template_id,
            prompt_template_version=rendered.template_version,
            policy_version=rendered.policy_version,
            retrieved_source_count=len(results),
        )

        self._emit_event(
            request,
            event_name=(
                "RAG_RESPONSE_QUALIFIED"
                if insufficient
                else "RAG_RESPONSE_COMPLETED"
            ),
            outcome="QUALIFIED" if insufficient else "SUCCEEDED",
            error_code="AI_INSUFFICIENT_EVIDENCE" if insufficient else None,
            duration_ms=self._duration_ms(generation_started),
            provider_id=gateway_response.provider_id,
            model_id=gateway_response.model_id,
        )
        return response

    @staticmethod
    def _parse_output(
        raw_text: str,
        *,
        allowed_labels: set[str],
    ) -> tuple[str, tuple[str, ...], bool]:
        """Accept only the expected JSON contract and known inline citations."""
        try:
            payload = json.loads(raw_text)
        except (TypeError, ValueError):
            raise ProviderResponseInvalidError() from None

        expected_keys = {
            "answer",
            "citations",
            "insufficient_evidence",
        }
        if not isinstance(payload, dict) or set(payload) != expected_keys:
            raise ProviderResponseInvalidError()

        raw_answer = payload["answer"]
        raw_citations = payload["citations"]
        insufficient = payload["insufficient_evidence"]

        if not isinstance(raw_answer, str):
            raise ProviderResponseInvalidError()
        answer = raw_answer.strip()
        if not answer:
            raise ProviderResponseInvalidError()

        if not isinstance(raw_citations, list):
            raise ProviderResponseInvalidError()
        if any(not isinstance(item, str) for item in raw_citations):
            raise ProviderResponseInvalidError()

        citation_labels = tuple(raw_citations)
        if len(set(citation_labels)) != len(citation_labels):
            raise ProviderResponseInvalidError()
        if any(label not in allowed_labels for label in citation_labels):
            raise ProviderResponseInvalidError()
        if not isinstance(insufficient, bool):
            raise ProviderResponseInvalidError()

        inline_labels = set(_INLINE_CITATION.findall(answer))
        if inline_labels != set(citation_labels):
            raise ProviderResponseInvalidError()
        if not insufficient and not citation_labels:
            raise ProviderResponseInvalidError()

        return answer, citation_labels, insufficient


__all__ = (
    "RAGPipeline",
    "RAGRequest",
    "RAGResponse",
    "RAGSettings",
    "RetrievalPort",
    "ModelGatewayPort",
)
