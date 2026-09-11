"""Compatibility namespace for relocated ACRL T16 implementation."""

from importlib import import_module
import sys

CANONICAL = "AUTONOMY_ENGINE.continuity.acrl.T16_Repository_Intelligence_File_Discovery.symbol_intelligence"

sys.modules[
    __name__ + ".lineage"
] = import_module(
    CANONICAL + ".lineage"
)
sys.modules[
    __name__ + ".snapshot"
] = import_module(
    CANONICAL + ".snapshot"
)
sys.modules[
    __name__ + ".symbols"
] = import_module(
    CANONICAL + ".symbols"
)

