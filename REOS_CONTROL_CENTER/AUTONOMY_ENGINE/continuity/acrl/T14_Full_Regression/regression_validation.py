"""ACRL T14 structural validation."""
from __future__ import annotations
from typing import Any


def validate_string(value: Any, field: str, max_length: int = 256) -> str:
    if not isinstance(value, str) or not value or len(value) > max_length:
        raise ValueError(f"Invalid {field}.")
    return value


def validate_layer_spec_fields(layer_number: int, name: str, directory: str,
                                core_file: str, test_glob: str) -> None:
    if not isinstance(layer_number, int) or layer_number < 1 or layer_number > 14:
        raise ValueError("Invalid T14 layer number.")
    validate_string(name, "layer name")
    validate_string(directory, "layer directory")
    validate_string(core_file, "core file")
    validate_string(test_glob, "test glob")
    if "/" in directory or "\\" in directory or directory.startswith("."):
        raise ValueError("Layer directory must be a canonical relative folder name.")
