"""ACRL T14 observational metrics."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class RegressionMetrics:
    total_layers: int
    passed_layers: int
    failed_layers: int
    total_test_files: int
    syntax_failures: int


def summarize(results: Iterable[object]) -> RegressionMetrics:
    items = tuple(results)
    passed = sum(bool(getattr(x, "passed", False)) for x in items)
    tests = sum(len(getattr(x, "test_files", ())) for x in items)
    syntax_failures = sum(bool(getattr(x, "syntax_error", False)) for x in items)
    return RegressionMetrics(len(items), passed, len(items) - passed, tests, syntax_failures)
