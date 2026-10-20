"""ACRL T07 — New-Chat Bootstrap and validated fast-resume adapter."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping, Sequence

from .new_chat_bootstrap import (
    BootstrapAuthorityError,
    BootstrapContext,
    BootstrapError,
    BootstrapIntegrityError,
    BootstrapValidationError,
    NewChatBootstrapEngine,
    RestartPayload,
)


def evaluate_fast_resume(
    *,
    manifest: Mapping[str, Any],
    live_snapshot: Mapping[str, Any],
    dependency_graph: Mapping[str, Sequence[str]] | None = None,
    now: datetime | None = None,
) -> Any:
    """Evaluate the T14 manifest against independently observed live state.

    The manifest is only a cache. This adapter does not read or modify
    canonical state.json and does not authorize execution.
    """
    return NewChatBootstrapEngine.evaluate_fast_resume(
        manifest=manifest,
        live_snapshot=live_snapshot,
        dependency_graph=dependency_graph,
        now=now,
    )


__all__ = [
    "BootstrapAuthorityError",
    "BootstrapContext",
    "BootstrapError",
    "BootstrapIntegrityError",
    "BootstrapValidationError",
    "NewChatBootstrapEngine",
    "RestartPayload",
    "evaluate_fast_resume",
]
