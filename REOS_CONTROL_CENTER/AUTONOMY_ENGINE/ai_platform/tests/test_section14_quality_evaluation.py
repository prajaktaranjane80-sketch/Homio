"""Section 14 deterministic AI quality evaluations and regression tests.

Fixtures are synthetic. The evidence report never stores full answer text,
raw provider exceptions, prompts, credentials, or property record contents.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace
from typing import Any

# The file is under REOS_CONTROL_CENTER/AUTONOMY_ENGINE/ai_platform/tests.
CONTROL_CENTER_ROOT = Path(__file__).resolve().parents[3]
if str(CONTROL_CENTER_ROOT) not in sys.path:
    sys.path.insert(0, str(CONTROL_CENTER_ROOT))

import pytest

from AUTONOMY_ENGINE.ai_platform.contracts import (  # noqa: E402
    AIResponse,
    ObservabilityEvent,
    RequestContext,
)
from AUTONOMY_ENGINE.ai_platform.errors import (  # noqa: E402
    AIPlatformError,
    ObservabilityUnavailableError,
)
from AUTONOMY_ENGINE.ai_platform.rag_pipeline import (  # noqa: E402
    RAGPipeline,
    RAGRequest,
    RAGSettings,
)
from AUTONOMY_ENGINE.ai_platform.retrieval_adapter import (  # noqa: E402
    RetrievalResponse,
    RetrievedSource,
)
from AUTONOMY_ENGINE.ai_platform.tool_bridge import (  # noqa: E402
    ToolBridge,
    ToolDefinition,
    ToolExecutionBlockedError,
    ToolProposal,
)

from AUTONOMY_ENGINE.core.search_matching.search_domain import (  # noqa: E402
    SearchRequest,
    SearchTenantContext,
)

FIXTURE_PATH = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "section14_quality_cases.json"
)
CONTEXT = RequestContext(
    principal_id="synthetic-user",
    tenant_id="synthetic-tenant",
    authentication_context_ref="synthetic-auth-context",
    correlation_id="section14-correlation",
)


def _canonical_json(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _load_manifest() -> dict[str, Any]:
    manifest = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict) or manifest.get("schema_version") != 1:
        raise ValueError("Section 14 fixture schema is unsupported")

    cases = manifest.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("Section 14 fixture must define cases")

    ids = [
        case.get("case_id")
        for case in cases
        if isinstance(case, dict)
    ]
    if len(ids) != len(cases) or len(set(ids)) != len(ids):
        raise ValueError("Section 14 case IDs must be unique")

    for case in cases:
        if case.get("status") not in {"EXECUTABLE", "BLOCKED"}:
            raise ValueError("Each case must be EXECUTABLE or BLOCKED")
        if not isinstance(case.get("expected_invariants"), list):
            raise ValueError("Every case must define expected invariants")
        if not isinstance(case.get("input"), dict):
            raise ValueError("Every case must define a synthetic input fixture")

    return manifest


def _source(
    *,
    tenant_id: str = "synthetic-tenant",
    record_id: str = "sample-inventory-1",
    inventory_code: str = "SAMPLE-101",
    availability: str = "AVAILABLE",
    name: str = "Synthetic apartment",
) -> RetrievedSource:
    """Build a source using the repository's actual RetrievedSource contract."""
    return RetrievedSource(
        tenant_id=tenant_id,
        source_reference="CORE-004.Inventory",
        record_id=record_id,
        source_version=1,
        project_id="synthetic-project",
        inventory_code=inventory_code,
        inventory_type="UNIT",
        lifecycle="ACTIVE",
        availability=availability,
        name=name,
        index_key=f"{tenant_id}:{record_id}",
        index_schema_version=1,
        index_version=1,
        index_fingerprint="synthetic-index-v1",
        source_kind="HYBRID",
        lexical_rank=1,
        vector_rank=1,
        lexical_score=0.8,
        vector_score=0.7,
        rrf_score=0.9,
    )


def _retrieval_response(
    request_id: str,
    *,
    tenant_id: str = "synthetic-tenant",
    sources: tuple[RetrievedSource, ...] = (),
) -> RetrievalResponse:
    return RetrievalResponse(
        request_id=request_id,
        tenant_id=tenant_id,
        embedding_model_id="synthetic-embedding-model",
        embedding_model_version="synthetic-embedding-v1",
        embedding_dimension=4,
        results=sources,
    )


class _FakeRetrieval:
    def __init__(
        self,
        response: object,
        *,
        error: Exception | None = None,
    ) -> None:
        self.response = response
        self.error = error
        self.requests: list[object] = []

    def retrieve(self, request):
        self.requests.append(request)
        if self.error is not None:
