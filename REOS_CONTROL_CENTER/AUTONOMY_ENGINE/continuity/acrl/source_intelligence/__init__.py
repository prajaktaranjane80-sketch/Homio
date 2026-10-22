"""Compatibility namespace for the relocated ACRL T16 implementation."""

from importlib import import_module
import sys

CANONICAL = (
    "AUTONOMY_ENGINE.continuity.acrl."
    "T16_Repository_Intelligence_File_Discovery.source_intelligence"
)

for module_name in (
    "dependency_graph",
    "intelligence",
    "source_parser",
    "web_source_parser",
):
    sys.modules[f"{__name__}.{module_name}"] = import_module(
        f"{CANONICAL}.{module_name}"
    )
