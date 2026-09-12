from __future__ import annotations
# Compatibility facade kept intentionally tiny.
from .state_reader import CanonicalStateReader, StateReadError

__all__ = ["CanonicalStateReader", "StateReadError"]
