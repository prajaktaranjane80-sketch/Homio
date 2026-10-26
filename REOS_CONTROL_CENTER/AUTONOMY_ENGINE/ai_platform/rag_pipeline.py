
"""Evidence-bounded RAG orchestration for HOMIO / REOS.

The pipeline reuses the existing search owner and provider-independent AI
gateway. It does not own canonical inventory, identity, authorization,
indexing, or a second vector store.

Safe by default: RAG generation is disabled unless explicitly enabled by the
approved server-side runtime configuration.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Protocol

from .contracts import (
    AIRequest,
    AIResponse,
    RequestContext,
    _identifier,
    _positive_int,
    _text,
)
from .errors import (
    AIPlatformError,
    GatewayDisabledError,
    InvalidRequestError,
    ProviderCallFailedError,
    ProviderResponseInvalidError,
    RequestContextMissingError,
    RetrievalResultInvalidError,
    RetrievalUnavailableError,
)
from .prompt_templates import (
    POLICY_VERSION,
    PROMPT_TEMPLATE_ID,
    PROMPT_TEMPLATE_VERSION,
    PromptTemplate,
    SourceCitation,
)
from .retrieval_adapter import (
    RetrievalRequest,
    RetrievalResponse,
    RetrievedSource,
)


_INLINE_CITATION = re.compile(r"\[(S[0-9]+)\]")


class RetrievalPort(Protocol):
    """Existing authorized retrieval adapter."""

    def retrieve(self, request: RetrievalRequest) -> RetrievalResponse:
        """Return tenant/resource-scoped, provenance-checked results."""


class ModelGatewayPort(Protocol):
    """Existing gateway that enforces authorization, usage and telemetry."""

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

        limits = (
            ("max_question_chars", self.max_question_chars, 16_000),
            ("max_sources", self.max_sources, 100),
            ("max_context_chars", self.max_context_chars, 100_000),
            ("max_output_tokens", self.max_output_tokens, 8_192),
            ("max_output_chars", self.max_output_chars, 100_000),
        )

        for name, value, maximum in limits:
            _positive_int(value, name)
            if value > maximum:
                raise ValueError(f"{name} exceeds its hard safety limit")


@dataclass(frozen=True, slots=True)
class RAGRequest:
    """Internal server-side request; context must be derived from trusted auth."""

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
            self,
            "request_id",
            _identifier(self.request_id, "request_id"),
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
            self.context,
            RequestContext,
        ):
            raise TypeError("context must be RequestContext or None")

        if self.model_id is not None:
            object.__setattr__(
                self,
                "model_id",
                _identifier(self.model_id, "model_id"),
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
    """Answer plus verifiable citations and prompt/model provenance."""

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
            self,
            "request_id",
            _identifier(self.request_id, "request_id"),
        )
        object.__setattr__(
            self,
            "answer",
            _text(
                self.answer,
                "answer",
                100_000,
                allow_multiline=True,
            ),
        )

        for name in (
            "prompt_template_id",
            "prompt_template_version",
            "policy_version",
        ):
            object.__setattr__(
                self,
                name,
                _identifier(getattr(self, name), name),
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
                self,
                "provider_id",
                _identifier(self.provider_id, "provider_id"),
            )
            object.__setattr__(
                self,
                "model_id",
                _identifier(self.model_id, "model_id"),
            )
        else:
            if self.provider_id is not None or self.model_id is not None:
                raise ValueError(
                    "non-generated responses must not claim provider/model use"
                )
            if not self.insufficient_evidence or citations:
                raise ValueError(
                    "non-generated responses must be an evidence-limited response"
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
    """Retrieve authorized evidence, build a bounded prompt and validate output."""

    _OPERATION = "property.search"
    _NO_EVIDENCE_ANSWER = (
        "I couldn't find enough authorized, current property records to answer "
        "this question. Please refine the query or provide more detail."
    )

    def __init__(
        self,
        *,
        retrieval: RetrievalPort,
        gateway: ModelGatewayPort,
        settings: RAGSettings | None = None,
        prompt_template: PromptTemplate | None = None,
    ) -> None:
        if retrieval is None or not callable(
            getattr(retrieval, "retrieve", None)
        ):
            raise TypeError("retrieval must expose a callable retrieve method")

        if gateway is None or not callable(
            getattr(gateway, "complete", None)
        ):
            raise TypeError("gateway must expose a callable complete method")

        selected_settings = settings or RAGSettings()
        if not isinstance(selected_settings, RAGSettings):
            raise TypeError("settings must be RAGSettings")

        selected_template = prompt_template or PromptTemplate()
        if not isinstance(selected_template, PromptTemplate):
            raise TypeError("prompt_template must be PromptTemplate")

        self._retrieval = retrieval
        self._gateway = gateway
        self._settings = selected_settings
        self._prompt_template = selected_template

    def answer(self, request: RAGRequest) -> RAGResponse:
        """Answer a read-only property question using authorized evidence only."""
        if not self._settings.enabled:
            raise GatewayDisabledError()

        if not isinstance(request, RAGRequest):
            raise InvalidRequestError()

        context = request.context
        if not isinstance(context, RequestContext):
            raise RequestContextMissingError()

        if len(request.question) > self._settings.max_question_chars:
            raise InvalidRequestError()

        if request.source_limit > self._settings.max_sources:
            raise InvalidRequestError()

        output_tokens = (
            request.max_output_tokens or self._settings.max_output_tokens
        )
        if output_tokens > self._settings.max_output_tokens:
            raise InvalidRequestError()

        retrieval_request = RetrievalRequest(
            request_id=request.request_id,
            query_text=request.question,
            embedding_model_id=request.embedding_model_id,
            context=context,
            limit=request.source_limit,
        )

        try:
            retrieval_response = self._retrieval.retrieve(retrieval_request)
        except AIPlatformError:
            raise
        except Exception:
            raise RetrievalUnavailableError() from None

        if not isinstance(retrieval_response, RetrievalResponse):
            raise RetrievalResultInvalidError()

        if (
            retrieval_response.request_id != request.request_id
            or retrieval_response.tenant_id != context.tenant_id
        ):
            raise RetrievalResultInvalidError()

        results = tuple(retrieval_response.results)

        if len(results) > request.source_limit:
            raise RetrievalResultInvalidError()

        if any(not isinstance(item, RetrievedSource) for item in results):
            raise RetrievalResultInvalidError()

        if any(item.tenant_id != context.tenant_id for item in results):
            raise RetrievalResultInvalidError()

        record_ids = [item.record_id for item in results]
        if len(set(record_ids)) != len(record_ids):
            raise RetrievalResultInvalidError()

        # Do not spend a generation request or invent facts if search returned
        # no authorized/current evidence.
        if not results:
            return RAGResponse(
                request_id=request.request_id,
                answer=self._NO_EVIDENCE_ANSWER,
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

        try:
            rendered = self._prompt_template.render(
                request.question,
                results,
            )
        except (TypeError, ValueError):
            raise InvalidRequestError() from None

        if len(rendered.prompt) > self._settings.max_context_chars:
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

        try:
            gateway_response = self._gateway.complete(gateway_request)
        except AIPlatformError:
            raise
        except Exception:
            raise ProviderCallFailedError() from None

        if not isinstance(gateway_response, AIResponse):
            raise ProviderResponseInvalidError()

        if (
            gateway_response.request_id != request.request_id
            or gateway_response.correlation_id != context.correlation_id
        ):
            raise ProviderResponseInvalidError()

        if len(gateway_response.text) > self._settings.max_output_chars:
            raise ProviderResponseInvalidError()

        answer, citation_labels, insufficient = self._parse_output(
            gateway_response.text,
            allowed_labels={
                source.citation_id for source in rendered.sources
            },
        )

        source_by_label = {
            source.citation_id: source
            for source in rendered.sources
        }
        citations = tuple(
            source_by_label[label] for label in citation_labels
        )

        return RAGResponse(
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

        # Citation metadata and inline citations must agree exactly. This
        # blocks invented source labels and unsupported uncited answers.
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
