"""T16 PART-03 — Static Python symbol intelligence.

Extracts structural symbols from Python source using AST only.
No project code is imported or executed.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path


class SymbolExtractionError(RuntimeError):
    """Raised when source symbols cannot be extracted safely."""


class SymbolKind(str):
    """Stable symbol-kind values."""

    MODULE = "MODULE"
    CLASS = "CLASS"
    FUNCTION = "FUNCTION"
    ASYNC_FUNCTION = "ASYNC_FUNCTION"
    METHOD = "METHOD"
    ASYNC_METHOD = "ASYNC_METHOD"
    CONSTANT = "CONSTANT"


@dataclass(frozen=True, slots=True)
class SymbolRecord:
    """Immutable static representation of one source symbol."""

    source_path: str
    qualified_name: str
    symbol_name: str
    kind: str
    line_number: int
    end_line_number: int


def _symbol_kind(node: ast.AST, parent: ast.AST | None) -> str | None:
    """Return the stable symbol kind for an AST node."""

    if isinstance(node, ast.ClassDef):
        return SymbolKind.CLASS

    if isinstance(node, ast.AsyncFunctionDef):
        if isinstance(parent, ast.ClassDef):
            return SymbolKind.ASYNC_METHOD
        return SymbolKind.ASYNC_FUNCTION

    if isinstance(node, ast.FunctionDef):
        if isinstance(parent, ast.ClassDef):
            return SymbolKind.METHOD
        return SymbolKind.FUNCTION

    return None


def _walk_symbols(
    nodes: list[ast.AST],
    prefix: str,
    parent: ast.AST | None,
    output: list[SymbolRecord],
    relative_path: str,
) -> None:
    """Recursively collect structural symbols."""

    for node in nodes:
        kind = _symbol_kind(
            node,
            parent,
        )

        if kind is not None:
            name = getattr(
                node,
                "name",
                "",
            )

            qualified_name = (
                f"{prefix}.{name}"
                if prefix
                else name
            )

            output.append(
                SymbolRecord(
                    source_path=relative_path,
                    qualified_name=qualified_name,
                    symbol_name=name,
                    kind=kind,
                    line_number=getattr(node, "lineno", 0),
                    end_line_number=getattr(
                        node,
                        "end_lineno",
                        getattr(node, "lineno", 0),
                    ),
                )
            )

            child_prefix = qualified_name

            child_body = getattr(
                node,
                "body",
                [],
            )

            _walk_symbols(
                child_body,
                child_prefix,
                node,
                output,
                relative_path,
            )

            continue

        child_body = getattr(
            node,
            "body",
            [],
        )

        if child_body:
            _walk_symbols(
                child_body,
                prefix,
                parent,
                output,
                relative_path,
            )


def extract_symbols(
    root: Path,
    relative_path: str,
) -> tuple[SymbolRecord, ...]:
    """Extract deterministic static symbols from one Python source file."""

    source_file = root / relative_path

    if not source_file.is_file():
        raise SymbolExtractionError(
            f"Source file does not exist: {relative_path}"
        )

    if source_file.suffix.lower() not in {".py", ".pyi"}:
        return ()

    try:
        source = source_file.read_text(
            encoding="utf-8",
        )

        tree = ast.parse(
            source,
            filename=str(source_file),
        )

    except (OSError, UnicodeError, SyntaxError) as exc:
        raise SymbolExtractionError(
            f"Unable to parse source for symbols: {relative_path}"
        ) from exc

    records: list[SymbolRecord] = []

    _walk_symbols(
        tree.body,
        "",
        None,
        records,
        relative_path,
    )

    records.sort(
        key=lambda item: (
            item.source_path,
            item.line_number,
            item.qualified_name,
            item.kind,
        )
    )

    return tuple(records)


__all__ = [
    "SymbolExtractionError",
    "SymbolKind",
    "SymbolRecord",
    "extract_symbols",
]