"""Compatibility namespace for relocated ACRL T16 implementation."""

from importlib import import_module
import sys

CANONICAL = "AUTONOMY_ENGINE.continuity.acrl.T16_Repository_Intelligence_File_Discovery.repository_discovery"

sys.modules[
    __name__ + ".boundary"
] = import_module(
    CANONICAL + ".boundary"
)
sys.modules[
    __name__ + ".classification"
] = import_module(
    CANONICAL + ".classification"
)
sys.modules[
    __name__ + ".fingerprint"
] = import_module(
    CANONICAL + ".fingerprint"
)
sys.modules[
    __name__ + ".identity"
] = import_module(
    CANONICAL + ".identity"
)
sys.modules[
    __name__ + ".topology"
] = import_module(
    CANONICAL + ".topology"
)

