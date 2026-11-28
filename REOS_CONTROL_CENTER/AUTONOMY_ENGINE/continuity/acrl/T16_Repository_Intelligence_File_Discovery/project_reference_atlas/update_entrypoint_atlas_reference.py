#!/usr/bin/env python3
"""Install the generated HOMIO Project Reference Atlas contract in EntryPoint.

The updater is deliberately lossless: it preserves the complete existing
EntryPoint and adds one validated, idempotent managed block plus two ordered
startup instructions. It never contacts GitHub and never changes project state.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any

BEGIN = "# BEGIN HOMIO PROJECT REFERENCE ATLAS (managed)"
END = "# END HOMIO PROJECT REFERENCE ATLAS (managed)"

ENTRYPOINT_RELATIVE_PATH = "REOS_CONTROL_CENTER/AI_AGENT_ENTRYPOINT.py"
ATLAS_RELATIVE_PATH = "REOS_CONTROL_CENTER/HOMIO_PROJECT_REFERENCE_ATLAS.json"
SCHEMA_RELATIVE_PATH = "REOS_CONTROL_CENTER/contracts/project_reference_atlas.schema.json"
GENERATOR_RELATIVE_PATH = (
    "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/continuity/acrl/"
    "T16_Repository_Intelligence_File_Discovery/project_reference_atlas/"
    "project_reference_atlas.py"
)
WORKFLOW_RELATIVE_PATH = ".github/workflows/homio-project-reference-atlas.yml"
SOURCE_BRANCH = "reos-development"
REFERENCE_BRANCH = "reos-project-reference"

READ_ORDER_INSERTION = (
    "Before broad source reads, retrieve the exact Atlas from the "
    "reos-project-reference branch when available; validate repository, "
    "source branch, source HEAD, source tree SHA, state.json blob SHA and "
    "EntryPoint blob SHA against live reos-development. Treat any mismatch "
    "as stale and use the existing T14/T16 targeted or full-audit boundary."
)
WORKFLOW_INSERTION = (
    "Validate the derived project reference Atlas against live repository "
    "identity and source SHAs before using it; use it only as a technical "
    "navigation/index aid, never as task state, authorization or evidence."
)


def _top_level_bindings(tree: ast.Module) -> dict[str, ast.AST]:
    bindings: dict[str, ast.AST] = {}
    for node in tree.body:
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            bindings[node.target.id] = node.value
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    bindings[target.id] = node.value
    return bindings


def _top_level_functions(tree: ast.Module) -> set[str]:
    return {
        node.name for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def _dictionary_has_key(node: ast.AST | None, key: str) -> bool:
    if not isinstance(node, ast.Dict):
        raise ValueError("EntryPoint registry must be a literal dictionary")
    for key_node in node.keys:
        try:
            if ast.literal_eval(key_node) == key:
                return True
        except (ValueError, TypeError):
            continue
    return False


def _validate_base_entrypoint(source: str) -> ast.Module:
    try:
        tree = ast.parse(source, filename=ENTRYPOINT_RELATIVE_PATH)
    except SyntaxError as exc:
        raise ValueError(
            f"Existing EntryPoint has invalid Python syntax: {exc}"
        ) from exc

    bindings = _top_level_bindings(tree)
    functions = _top_level_functions(tree)

    required_bindings = {
        "ENTRYPOINT_RELATIVE_PATH",
        "DOCUMENT_REGISTRY",
        "SOURCE_OF_TRUTH",
        "ACRL_OWNER_ROUTING",
        "NEW_SESSION_READ_ORDER",
        "NEW_SESSION_WORKFLOW",
    }

    missing = sorted(required_bindings - set(bindings))
    if missing:
        raise ValueError(
            "EntryPoint is missing required top-level owners: "
            + ", ".join(missing)
        )

    for name in (
        "DOCUMENT_REGISTRY",
        "SOURCE_OF_TRUTH",
        "ACRL_OWNER_ROUTING",
    ):
        if not isinstance(bindings[name], ast.Dict):
            raise ValueError(
                f"EntryPoint {name} must remain a literal dictionary"
            )

    for name in ("NEW_SESSION_READ_ORDER", "NEW_SESSION_WORKFLOW"):
        if not isinstance(bindings[name], (ast.Tuple, ast.List)):
            raise ValueError(
                f"EntryPoint {name} must remain a tuple/list"
            )

    missing_functions = sorted(
        {"repository_paths", "startup_instructions"} - functions
    )
    if missing_functions:
        raise ValueError(
            "EntryPoint is missing required public functions: "
            + ", ".join(missing_functions)
        )

    if _dictionary_has_key(
        bindings["DOCUMENT_REGISTRY"], "project_reference_atlas"
    ):
        raise ValueError(
            "DOCUMENT_REGISTRY already contains project_reference_atlas; "
            "refusing to create a duplicate or silently overwrite an owner entry"
        )

    if _dictionary_has_key(
        bindings["SOURCE_OF_TRUTH"], "project_reference_atlas"
    ):
        raise ValueError(
            "SOURCE_OF_TRUTH already contains project_reference_atlas"
        )

    if _dictionary_has_key(
        bindings["ACRL_OWNER_ROUTING"], "project_reference_atlas"
    ):
        raise ValueError(
            "ACRL_OWNER_ROUTING already contains project_reference_atlas"
        )

    return tree


def _tuple_item_line(
    tree: ast.Module,
    variable: str,
    marker: str,
) -> int:
    bindings = _top_level_bindings(tree)
    tuple_node = bindings.get(variable)

    if not isinstance(tuple_node, (ast.Tuple, ast.List)):
        raise ValueError(f"Cannot locate {variable} tuple")

    matches = [
        item
        for item in tuple_node.elts
        if (
            isinstance(item, ast.Constant)
            and isinstance(item.value, str)
            and marker in item.value
        )
    ]

    if len(matches) != 1:
        raise ValueError(
            f"Expected exactly one {marker!r} item in "
            f"{variable}; found {len(matches)}"
        )

    return matches[0].lineno


def _insert_tuple_instruction(
    source: str,
    variable: str,
    marker: str,
    insertion: str,
) -> str:
    tree = ast.parse(source, filename=ENTRYPOINT_RELATIVE_PATH)
    lines = source.splitlines(keepends=True)

    line_number = _tuple_item_line(tree, variable, marker)
    target_line = lines[line_number - 1]

    indent = target_line[
        : len(target_line) - len(target_line.lstrip())
    ]
    newline = (
        "\r\n" if target_line.endswith("\r\n") else "\n"
    )

    lines.insert(
        line_number - 1,
        f"{indent}{insertion!r},{newline}",
    )

    return "".join(lines)


MANAGED_BLOCK = r'''# BEGIN HOMIO PROJECT REFERENCE ATLAS (managed)
# Derived navigation metadata only. The live state.json and source branch remain authoritative.
PROJECT_REFERENCE_ATLAS_REFERENCE: dict[str, str] = {
    "repository": "prajaktaranjane80-sketch/Homio",
    "source_branch": "reos-development",
    "reference_branch": "reos-project-reference",
    "path": "REOS_CONTROL_CENTER/HOMIO_PROJECT_REFERENCE_ATLAS.json",
    "schema_path": "REOS_CONTROL_CENTER/contracts/project_reference_atlas.schema.json",
    "generator_path": "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/continuity/acrl/T16_Repository_Intelligence_File_Discovery/project_reference_atlas/project_reference_atlas.py",
    "workflow_path": ".github/workflows/homio-project-reference-atlas.yml",
    "authority": "DERIVED_TECHNICAL_REFERENCE_ONLY",
}

PROJECT_REFERENCE_ATLAS_RULES: tuple[str, ...] = (
    "Fetch the Atlas from reos-project-reference only after confirming the repository and branch identity.",
    "Compare source_commit_sha and source_tree_sha with the live reos-development branch before relying on any Atlas section.",
    "Compare state_json_blob_sha and entrypoint_blob_sha with the current tracked files; reject the Atlas if either differs.",
    "Use exact tracked paths and blob SHAs as navigation evidence; verify each target file from live GitHub before editing it.",
    "Treat owner, parser and dependency classifications as evidence-labelled metadata, not proof of runtime behavior.",
    "Use existing ACRL T16 for repository inventory and static discovery, T14 for resume/freshness decisions, and T17 for change impact.",
    "Never treat the Atlas as state.json, task authorization, approval, completion evidence, or a replacement for an owner reference.",
    "If the Atlas is absent, invalid, stale or partially parsed, use the existing T14/T16 targeted or full-audit route and state the limitation.",
    "The EntryPoint performs no network access, Git mutation, task transition or hidden command execution.",
)


def project_reference_atlas_rules() -> list[str]:
    """Return the Atlas consumption rules for a new engineering session."""
    return list(PROJECT_REFERENCE_ATLAS_RULES)


def project_reference_atlas_generation() -> dict[str, Any]:
    """Describe the existing T16-owned, source-commit-bound generation path."""
    return {
        "generator_owner": "acrl_t16",
        "freshness_owner": "acrl_t14",
        "impact_owner": "acrl_t17",
        "source_branch": "reos-development",
        "publication_branch": "reos-project-reference",
        "atlas_path": PROJECT_REFERENCE_ATLAS_REFERENCE["path"],
        "schema_path": PROJECT_REFERENCE_ATLAS_REFERENCE["schema_path"],
        "workflow_path": PROJECT_REFERENCE_ATLAS_REFERENCE["workflow_path"],
        "generation_mode": "AUTOMATED_FROM_EXACT_LIVE_SOURCE_COMMIT",
        "entrypoint_update_mode": "GENERATED_COMPLETE_REPLACEMENT_REQUIRES_OWNER_READBACK",
        "writes_to_source_branch": False,
        "updates_state_json": False,
    }


if 'project_reference_atlas' in DOCUMENT_REGISTRY:
    raise ValueError("DOCUMENT_REGISTRY already contains project_reference_atlas")

DOCUMENT_REGISTRY['project_reference_atlas'] = {
    "path": PROJECT_REFERENCE_ATLAS_REFERENCE["path"],
    "role": "Generated, source-commit-bound technical inventory and navigation index.",
    "authority": "DERIVED_TECHNICAL_REFERENCE_ONLY",
}

SOURCE_OF_TRUTH['project_reference_atlas'] = (
    "Derived technical index on reos-project-reference; never execution state or authorization."
)

ACRL_OWNER_ROUTING['project_reference_atlas'] = "acrl_t16"
ACRL_OWNER_ROUTING['project_reference_atlas_resume_and_freshness'] = "acrl_t14"
ACRL_OWNER_ROUTING['project_reference_atlas_change_impact'] = "acrl_t17"

_PROJECT_REFERENCE_ATLAS_BASE_REPOSITORY_PATHS = repository_paths


def repository_paths() -> dict[str, str]:
    """Return the existing path map plus the generated Atlas pointer."""
    paths = dict(_PROJECT_REFERENCE_ATLAS_BASE_REPOSITORY_PATHS())
    paths['project_reference_atlas'] = PROJECT_REFERENCE_ATLAS_REFERENCE["path"]
    paths['project_reference_atlas_schema'] = PROJECT_REFERENCE_ATLAS_REFERENCE["schema_path"]
    paths['project_reference_atlas_generator'] = PROJECT_REFERENCE_ATLAS_REFERENCE["generator_path"]
    return paths


_PROJECT_REFERENCE_ATLAS_BASE_STARTUP_INSTRUCTIONS = startup_instructions


def startup_instructions() -> dict[str, Any]:
    """Return existing startup data enriched with source-bound Atlas rules."""
    instructions = dict(_PROJECT_REFERENCE_ATLAS_BASE_STARTUP_INSTRUCTIONS())
    return {
        **instructions,
        'project_reference_atlas': dict(PROJECT_REFERENCE_ATLAS_REFERENCE),
        'project_reference_atlas_rules': list(PROJECT_REFERENCE_ATLAS_RULES),
        'project_reference_atlas_generation': project_reference_atlas_generation(),
    }
# END HOMIO PROJECT REFERENCE ATLAS (managed)
'''


def _validate_managed_block(source: str) -> None:
    if source.count(BEGIN) != 1 or source.count(END) != 1:
        raise ValueError(
            "Managed Atlas block is incomplete or duplicated"
        )

    if source.index(BEGIN) >= source.index(END):
        raise ValueError(
            "Managed Atlas block markers are out of order"
        )

    required = (
        "PROJECT_REFERENCE_ATLAS_REFERENCE",
        "PROJECT_REFERENCE_ATLAS_RULES",
        "project_reference_atlas_rules",
        "project_reference_atlas_generation",
        "DOCUMENT_REGISTRY['project_reference_atlas']",
        "SOURCE_OF_TRUTH['project_reference_atlas']",
        "ACRL_OWNER_ROUTING['project_reference_atlas']",
        "'project_reference_atlas_rules': list(PROJECT_REFERENCE_ATLAS_RULES),",
        "'project_reference_atlas_generation': project_reference_atlas_generation(),",
        READ_ORDER_INSERTION,
        WORKFLOW_INSERTION,
    )

    missing = [
        item for item in required if item not in source
    ]

    if missing:
        raise ValueError(
            "Managed Atlas integration is incomplete: "
            + ", ".join(missing)
        )

    try:
        ast.parse(source, filename=ENTRYPOINT_RELATIVE_PATH)
    except SyntaxError as exc:
        raise ValueError(
            f"Managed EntryPoint replacement has invalid Python syntax: {exc}"
        ) from exc


def update_entrypoint(source: str) -> str:
    """Return a complete lossless EntryPoint replacement with Atlas integration."""
    if not isinstance(source, str) or not source.strip():
        raise ValueError(
            "EntryPoint source must be a non-empty string"
        )

    has_begin = BEGIN in source
    has_end = END in source

    if has_begin or has_end:
        if not (has_begin and has_end):
            raise ValueError(
                "Partial managed Atlas block detected; refusing an unsafe repair"
            )

        _validate_managed_block(source)
        return source

    if (
        READ_ORDER_INSERTION in source
        or WORKFLOW_INSERTION in source
    ):
        raise ValueError(
            "Atlas startup instruction exists without the complete managed block"
        )

    tree = _validate_base_entrypoint(source)
    bindings = _top_level_bindings(tree)

    for mapping_name in (
        "DOCUMENT_REGISTRY",
        "SOURCE_OF_TRUTH",
        "ACRL_OWNER_ROUTING",
    ):
        if _dictionary_has_key(
            bindings[mapping_name], "project_reference_atlas"
        ):
            raise ValueError(
                f"{mapping_name} already contains project_reference_atlas"
            )

    updated = _insert_tuple_instruction(
        source,
        "NEW_SESSION_READ_ORDER",
        "9. Read the selected workstream's master reference",
        READ_ORDER_INSERTION,
    )

    updated = _insert_tuple_instruction(
        updated,
        "NEW_SESSION_WORKFLOW",
        "11. Read approved architecture",
        WORKFLOW_INSERTION,
    )

    updated = updated.rstrip() + "\n\n" + MANAGED_BLOCK + "\n"

    _validate_managed_block(updated)
    return updated


def _write_atomic(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    fd, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
    )

    try:
        with os.fdopen(
            fd,
            "w",
            encoding="utf-8",
            newline="\n",
        ) as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())

        os.replace(temporary_name, path)

    except Exception:
        try:
            os.unlink(temporary_name)
        except OSError:
            pass
        raise


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)

    args = parser.parse_args(argv)

    source_path = args.source.resolve()
    output_path = args.output.resolve()

    if source_path == output_path:
        parser.error(
            "--output must differ from --source; "
            "the source EntryPoint is never overwritten"
        )

    original = source_path.read_text(encoding="utf-8-sig")
    replacement = update_entrypoint(original)

    compile(replacement, str(source_path), "exec")
    _write_atomic(output_path, replacement)

    print(json.dumps({
        "status": "GENERATED_COMPLETE_REPLACEMENT",
        "source_path": str(source_path),
        "output_path": str(output_path),
        "source_sha256": hashlib.sha256(
            original.encode("utf-8")
        ).hexdigest(),
        "replacement_sha256": hashlib.sha256(
            replacement.encode("utf-8")
        ).hexdigest(),
        "source_lines": len(original.splitlines()),
        "replacement_lines": len(replacement.splitlines()),
        "idempotent": update_entrypoint(replacement) == replacement,
    }, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
