#!/usr/bin/env python3
"""Losslessly integrate the generated HOMIO Atlas contract into EntryPoint.

This is a file transformer only. It performs no network access, Git mutation,
state transition, or source-code execution. It preserves existing EntryPoint
owners and places the managed block before the CLI entry point so both imports
and direct startup observe the Atlas integration.
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
CLI_MARKER = "# 24. CLI"

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

MANAGED_BLOCK = r'''# BEGIN HOMIO PROJECT REFERENCE ATLAS (managed)
# Generated navigation metadata only. state.json and live GitHub source remain authoritative.
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
    "The Atlas is a technical navigation index, never task state, approval, evidence, or execution authority.",
    "Fetch the Atlas from reos-project-reference using the GitHub repository connector; this EntryPoint has no network runtime.",
    "Validate repository identity, source branch, source commit SHA, source tree SHA, state.json blob SHA, and EntryPoint blob SHA before relying on it.",
    "If any identity or SHA differs, treat the Atlas as stale and consult existing T14/T16 targeted or full-audit decisions.",
    "Use Git-tracked inventory and exact blob SHAs to avoid repeated broad reads; fetch only task-relevant files whose current SHA requires verification.",
    "Use existing ACRL owners: T07 bootstrap, T14 resume/freshness, T16 repository discovery, T17 impact, T19 test selection/diagnosis, T20 repair verification, T23 evidence resolution, and T30 completion proof.",
    "Do not create duplicate scanners, dependency engines, evidence registries, failure engines, task managers, or orchestration layers.",
    "Distinguish complete Git inventory from partial semantic analysis; unresolved owners, unsupported formats, and parser failures must remain explicit.",
    "Never copy secret values, credentials, environment values, or full repository source into the Atlas.",
    "The Atlas generator and this updater do not mutate state.json, grant authorization, or mark a task complete.",
)


def project_reference_atlas_rules() -> list[str]:
    """Return stable Atlas-consumption rules for the engineering agent."""
    return list(PROJECT_REFERENCE_ATLAS_RULES)


def project_reference_atlas_generation() -> dict[str, Any]:
    """Return the existing-owner generation and validation boundaries."""
    return {
        "generator_owner": "acrl_t16",
        "freshness_owner": "acrl_t14",
        "impact_owner": "acrl_t17",
        "test_selection_and_failure_diagnosis_owner": "acrl_t19",
        "evidence_resolution_owner": "acrl_t23",
        "new_chat_bootstrap_owner": "acrl_t07",
        "source_branch": "reos-development",
        "publication_branch": "reos-project-reference",
        "atlas_path": PROJECT_REFERENCE_ATLAS_REFERENCE["path"],
        "schema_path": PROJECT_REFERENCE_ATLAS_REFERENCE["schema_path"],
        "workflow_path": PROJECT_REFERENCE_ATLAS_REFERENCE["workflow_path"],
        "generation_mode": "AUTOMATED_FROM_EXACT_LIVE_SOURCE_COMMIT",
        "entrypoint_update_mode": "COMPLETE_GENERATED_REPLACEMENT_WITH_OWNER_READBACK",
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

if 'project_reference_atlas' in SOURCE_OF_TRUTH:
    raise ValueError("SOURCE_OF_TRUTH already contains project_reference_atlas")

SOURCE_OF_TRUTH['project_reference_atlas'] = (
    "Derived technical index on reos-project-reference; never execution state or authorization."
)

if 'project_reference_atlas' in ACRL_OWNER_ROUTING:
    raise ValueError("ACRL_OWNER_ROUTING already contains project_reference_atlas")

ACRL_OWNER_ROUTING['project_reference_atlas'] = "acrl_t16"
ACRL_OWNER_ROUTING['project_reference_atlas_resume_and_freshness'] = "acrl_t14"
ACRL_OWNER_ROUTING['project_reference_atlas_change_impact'] = "acrl_t17"
ACRL_OWNER_ROUTING['project_reference_atlas_failure_diagnosis'] = "acrl_t19"
ACRL_OWNER_ROUTING['project_reference_atlas_evidence_resolution'] = "acrl_t23"
ACRL_OWNER_ROUTING['project_reference_atlas_new_chat_bootstrap'] = "acrl_t07"

_PROJECT_REFERENCE_ATLAS_BASE_REPOSITORY_PATHS = repository_paths


def repository_paths() -> dict[str, str]:
    """Return existing paths plus the generated Atlas references."""
    paths = dict(_PROJECT_REFERENCE_ATLAS_BASE_REPOSITORY_PATHS())
    paths['project_reference_atlas'] = PROJECT_REFERENCE_ATLAS_REFERENCE["path"]
    paths['project_reference_atlas_schema'] = PROJECT_REFERENCE_ATLAS_REFERENCE["schema_path"]
    paths['project_reference_atlas_generator'] = PROJECT_REFERENCE_ATLAS_REFERENCE["generator_path"]
    paths['project_reference_atlas_workflow'] = PROJECT_REFERENCE_ATLAS_REFERENCE["workflow_path"]
    return paths


_PROJECT_REFERENCE_ATLAS_BASE_STARTUP_INSTRUCTIONS = startup_instructions


def startup_instructions() -> dict[str, Any]:
    """Expose Atlas instructions while preserving the original startup payload."""
    instructions = dict(_PROJECT_REFERENCE_ATLAS_BASE_STARTUP_INSTRUCTIONS())
    return {
        **instructions,
        "project_reference_atlas": dict(PROJECT_REFERENCE_ATLAS_REFERENCE),
        'project_reference_atlas_rules': list(PROJECT_REFERENCE_ATLAS_RULES),
        'project_reference_atlas_generation': project_reference_atlas_generation(),
    }
# END HOMIO PROJECT REFERENCE ATLAS (managed)
'''


def _top_level_bindings(tree: ast.Module) -> dict[str, ast.AST | None]:
    result: dict[str, ast.AST | None] = {}

    for node in tree.body:
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            result[node.target.id] = node.value

        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    result[target.id] = node.value

    return result


def _top_level_functions(tree: ast.Module) -> set[str]:
    return {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def _literal_dictionary_has_key(
    node: ast.AST | None,
    key: str,
) -> bool:
    if not isinstance(node, ast.Dict):
        raise ValueError(
            "EntryPoint registry must be a literal dictionary"
        )

    for key_node in node.keys:
        try:
            if ast.literal_eval(key_node) == key:
                return True
        except (ValueError, TypeError):
            continue

    return False


def _validate_base_entrypoint(source: str) -> ast.Module:
    try:
        tree = ast.parse(
            source,
            filename=ENTRYPOINT_RELATIVE_PATH,
        )
    except SyntaxError as exc:
        raise ValueError(
            f"Existing EntryPoint has invalid Python syntax: {exc}"
        ) from exc

    bindings = _top_level_bindings(tree)

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

    for name in (
        "NEW_SESSION_READ_ORDER",
        "NEW_SESSION_WORKFLOW",
    ):
        if not isinstance(bindings[name], (ast.Tuple, ast.List)):
            raise ValueError(
                f"EntryPoint {name} must remain a tuple/list"
            )

    missing_functions = sorted(
        {"repository_paths", "startup_instructions"}
        - _top_level_functions(tree)
    )
    if missing_functions:
        raise ValueError(
            "EntryPoint is missing required public functions: "
            + ", ".join(missing_functions)
        )

    for name in (
        "DOCUMENT_REGISTRY",
        "SOURCE_OF_TRUTH",
        "ACRL_OWNER_ROUTING",
    ):
        if _literal_dictionary_has_key(
            bindings[name],
            "project_reference_atlas",
        ):
            raise ValueError(
                f"{name} already contains project_reference_atlas; "
                "refusing duplicate ownership"
            )

    return tree


def _tuple_item_line(
    tree: ast.Module,
    variable: str,
    marker: str,
) -> int:
    node = _top_level_bindings(tree).get(variable)

    if not isinstance(node, (ast.Tuple, ast.List)):
        raise ValueError(
            f"Cannot locate {variable} tuple"
        )

    matches = [
        item
        for item in node.elts
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
    tree = ast.parse(
        source,
        filename=ENTRYPOINT_RELATIVE_PATH,
    )
    lines = source.splitlines(keepends=True)

    line_number = _tuple_item_line(
        tree,
        variable,
        marker,
    )
    target = lines[line_number - 1]

    indent = target[
        : len(target) - len(target.lstrip())
    ]
    newline = (
        "\r\n"
        if target.endswith("\r\n")
        else "\n"
    )

    lines.insert(
        line_number - 1,
        f"{insertion!r},{newline}",
    )

    return "".join(lines)


def _managed_block_position(source: str) -> tuple[int, int]:
    if source.count(BEGIN) != 1 or source.count(END) != 1:
        raise ValueError(
            "Managed Atlas block is incomplete or duplicated"
        )

    start = source.index(BEGIN)
    end = source.index(END, start) + len(END)

    if start >= end:
        raise ValueError(
            "Managed Atlas block markers are out of order"
        )

    return start, end


def _validate_managed_block(source: str) -> None:
    start, end = _managed_block_position(source)

    cli_count = source.count(CLI_MARKER)
    cli = source.find(CLI_MARKER)

    if cli_count > 1:
        raise ValueError(
            "EntryPoint contains duplicate CLI section markers"
        )

    if cli_count == 1 and start > cli:
        raise ValueError(
            "Managed Atlas block must appear before the EntryPoint CLI startup block"
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
        item for item in required
        if item not in source
    ]

    if missing:
        raise ValueError(
            "Managed Atlas integration is incomplete: "
            + ", ".join(missing)
        )

    if not (0 <= start < end <= len(source)):
        raise ValueError(
            "Managed Atlas block range is invalid"
        )

    try:
        ast.parse(
            source,
            filename=ENTRYPOINT_RELATIVE_PATH,
        )
    except SyntaxError as exc:
        raise ValueError(
            f"Managed EntryPoint replacement has invalid Python syntax: {exc}"
        ) from exc


def _insert_managed_block_before_cli(source: str) -> str:
    marker_count = source.count(CLI_MARKER)

    if marker_count > 1:
        raise ValueError(
            "EntryPoint contains duplicate CLI section markers"
        )

    insertion = MANAGED_BLOCK.rstrip() + "\n\n"

    if marker_count == 0:
        # Small contract-test fixtures may omit the real CLI section.
        # The production EntryPoint has the canonical CLI marker.
        return source.rstrip() + "\n\n" + insertion

    marker = source.index(CLI_MARKER)
    line_start = source.rfind("\n", 0, marker) + 1

    return (
        source[:line_start]
        + insertion
        + source[line_start:]
    )


def update_entrypoint(source: str) -> str:
    """Return a complete, lossless, idempotent EntryPoint replacement."""
    if not isinstance(source, str) or not source.strip():
        raise ValueError(
            "EntryPoint source must be a non-empty string"
        )

    has_begin = BEGIN in source
    has_end = END in source

    if has_begin or has_end:
        if not (has_begin and has_end):
            raise ValueError(
                "Partial managed Atlas block detected; refusing unsafe repair"
            )

        start, end = _managed_block_position(source)
        cli = source.find(CLI_MARKER)

        if cli >= 0 and start > cli:
            # Repair an older generated layout that appended the block
            # after the CLI. Preserve all source outside the managed block.
            block = source[start:end]
            remainder = source[:start] + source[end:]

            if remainder.count(CLI_MARKER) != 1:
                raise ValueError(
                    "Cannot safely relocate the managed block: "
                    "CLI marker is not unique"
                )

            marker = remainder.index(CLI_MARKER)
            line_start = remainder.rfind("\n", 0, marker) + 1

            updated = (
                remainder[:line_start]
                + block
                + "\n\n"
                + remainder[line_start:]
            )

            _validate_managed_block(updated)
            return updated

        _validate_managed_block(source)
        return source

    if (
        READ_ORDER_INSERTION in source
        or WORKFLOW_INSERTION in source
    ):
        raise ValueError(
            "Atlas startup instruction exists without the complete managed block"
        )

    _validate_base_entrypoint(source)

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

    updated = _insert_managed_block_before_cli(updated)

    _validate_managed_block(updated)
    return updated


def _write_atomic(path: Path, content: str) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

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

        os.replace(
            temporary_name,
            path,
        )

    except Exception:
        try:
            os.unlink(temporary_name)
        except OSError:
            pass
        raise


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__
    )

    parser.add_argument(
        "--source",
        type=Path,
        required=True,
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
    )

    args = parser.parse_args(argv)

    source_path = args.source.resolve()
    output_path = args.output.resolve()

    if source_path == output_path:
        parser.error(
            "--output must differ from --source; "
            "the source EntryPoint is never overwritten"
        )

    original = source_path.read_text(
        encoding="utf-8-sig"
    )

    replacement = update_entrypoint(original)

    compile(
        replacement,
        str(source_path),
        "exec",
    )

    _write_atomic(
        output_path,
        replacement,
    )

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
        "managed_block_before_cli": (
            CLI_MARKER not in replacement
            or replacement.index(BEGIN) < replacement.index(CLI_MARKER)
        ),
        "idempotent": (
            update_entrypoint(replacement) == replacement
        ),
    }, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
