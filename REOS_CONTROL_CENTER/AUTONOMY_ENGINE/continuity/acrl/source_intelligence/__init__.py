"""Compatibility namespace for relocated ACRL T16 implementation."""

from importlib import import_module
import sys

CANONICAL = "AUTONOMY_ENGINE.continuity.acrl.T16_Repository_Intelligence_File_Discovery.source_intelligence"

sys.modules[
    __name__ + ".dependency_graph"
] = import_module(
    CANONICAL + ".dependency_graph"
)
sys.modules[
    __name__ + ".intelligence"
] = import_module(
    CANONICAL + ".intelligence"
)
sys.modules[
    __name__ + ".source_parser"
] = import_module(
    CANONICAL + ".source_parser"
)

