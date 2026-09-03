"""T16 PART-02 — Python source intelligence.

Read-only AST-based extraction of source-module imports.
No project code is imported or executed.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path


class SourceParseError(RuntimeError):
    """Raised when Python source cannot be parsed safely."""


@dataclass(frozen=True, slots=True)
class ImportEvidence:
    """One statically observed Python import."""

    source_path: str
    imported_name: str
    import_kind: str
    line_number: int


def parse_imports(
    root: Path,
    relative_path: str,
) -> tuple[ImportEvidence, ...]:
    """Extract deterministic import evidence from one Python source file."""

    source_file = root / relative_path

    if not source_file.is_file():
        raise SourceParseError(
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
        raise SourceParseError(
            f"Unable to parse Python source: {relative_path}"
        ) from exc

    evidence: list[ImportEvidence] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                evidence.append(
                    ImportEvidence(
                        source_path=relative_path,
                        imported_name=alias.name,
                        import_kind="IMPORT",
                        line_number=node.lineno,
                    )
                )

        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""

            prefix = "." * node.level

            imported_name = (
                f"{prefix}{module}"
                if module
                else prefix
            )

            evidence.append(
                ImportEvidence(
                    source_path=relative_path,
                    imported_name=imported_name,
                    import_kind="FROM_IMPORT",
                    line_number=node.lineno,
                )
            )

    evidence.sort(
        key=lambda item: (
            item.source_path,
            item.line_number,
            item.import_kind,
            item.imported_name,
        )
    )

    return tuple(evidence)


__all__ = [
    "ImportEvidence",
    "SourceParseError",
    "parse_imports",
]
