"""Focused regression tests for T16 web-source import discovery."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from AUTONOMY_ENGINE.continuity.acrl.T16_Repository_Intelligence_File_Discovery.source_intelligence.web_source_parser import (
    WebSourceParseError,
    parse_web_imports,
)


def write_source(
    root: Path,
    relative_path: str,
    content: str,
) -> Path:
    """Write a UTF-8 fixture below the temporary repository root."""
    target = root / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return target


def write_bytes(
    root: Path,
    relative_path: str,
    content: bytes,
) -> Path:
    """Write bytes for encoding and file-size boundary tests."""
    target = root / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(content)
    return target


@pytest.fixture
def repository(tmp_path: Path) -> Path:
    """Create an isolated repository for static parsing tests."""
    root = tmp_path / "repo"
    root.mkdir()
    return root


def test_static_and_dynamic_imports_are_resolved_deterministically(
    repository: Path,
) -> None:
    write_source(
        repository,
        "src/page.tsx",
        (
            'import { Button } from "./components/Button";\n'
            'import "./setup";\n'
            'export { shared } from "./shared";\n'
            'const Lazy = import("./lazy");\n'
            'const runtime = require("./runtime");\n'
            'import React from "react";\n'
        ),
    )

    write_source(
        repository,
        "src/components/Button.tsx",
        "export function Button() { return null; }\n",
    )
    write_source(repository, "src/setup.ts", "export {};\n")
    write_source(repository, "src/shared.ts", "export const shared = true;\n")
    write_source(repository, "src/lazy.ts", "export default {};\n")
    write_source(repository, "src/runtime.js", "module.exports = {};\n")

    first = parse_web_imports(repository, "src/page.tsx")
    second = parse_web_imports(repository, "src/page.tsx")

    observed = [
        (
            item.imported_name,
            item.import_kind,
            item.line_number,
            item.resolved_path,
        )
        for item in first
    ]

    assert observed == [
        (
            "./components/Button",
            "STATIC_IMPORT",
            1,
            "src/components/Button.tsx",
        ),
        ("./setup", "SIDE_EFFECT_IMPORT", 2, "src/setup.ts"),
        ("./shared", "STATIC_IMPORT", 3, "src/shared.ts"),
        ("./lazy", "DYNAMIC_IMPORT", 4, "src/lazy.ts"),
        ("./runtime", "COMMONJS_REQUIRE", 5, "src/runtime.js"),
        ("react", "STATIC_IMPORT", 6, None),
    ]
    assert first == second


def test_frontend_tsconfig_aliases_are_resolved(
    repository: Path,
) -> None:
    config_path = (
        "REOS_CONTROL_CENTER/Frontend/tsconfig.json"
    )
    page_path = (
        "REOS_CONTROL_CENTER/Frontend/src/app/page.tsx"
    )
    component_path = (
        "REOS_CONTROL_CENTER/Frontend/src/components/Card.tsx"
    )

    write_source(
        repository,
        config_path,
        json.dumps(
            {
                "compilerOptions": {
                    "baseUrl": ".",
                    "paths": {
                        "@/*": ["src/*"],
                    },
                },
            }
        ),
    )
    write_source(
        repository,
        page_path,
        'import Card from "@/components/Card";\n',
    )
    write_source(
        repository,
        component_path,
        "export default function Card() { return null; }\n",
    )

    evidence = parse_web_imports(repository, page_path)

    assert len(evidence) == 1
    assert evidence[0].imported_name == "@/components/Card"
    assert evidence[0].resolved_path == component_path


def test_css_imports_are_classified_and_external_urls_stay_external(
    repository: Path,
) -> None:
    write_source(repository, "styles/tokens.css", ":root { --gap: 1rem; }\n")
    write_source(repository, "styles/theme.scss", "$color: black;\n")
    write_source(
        repository,
        "styles/main.css",
        (
            '@import "./tokens.css";\n'
            '@import url("./theme.scss");\n'
            '@import url("https://cdn.example/theme.css");\n'
        ),
    )

    evidence = parse_web_imports(repository, "styles/main.css")

    assert [
        (
            item.imported_name,
            item.import_kind,
            item.line_number,
            item.resolved_path,
        )
        for item in evidence
    ] == [
        ("./tokens.css", "CSS_IMPORT", 1, "styles/tokens.css"),
        ("./theme.scss", "CSS_IMPORT", 2, "styles/theme.scss"),
        (
            "https://cdn.example/theme.css",
            "CSS_IMPORT",
            3,
            None,
        ),
    ]


@pytest.mark.parametrize(
    "relative_path",
    [
        "",
        "/absolute/page.tsx",
        "../outside.tsx",
        "src/../outside.tsx",
        "src//page.tsx",
    ],
)
def test_unsafe_source_paths_are_rejected(
    repository: Path,
    relative_path: str,
) -> None:
    with pytest.raises(WebSourceParseError):
        parse_web_imports(repository, relative_path)


def test_missing_and_unsupported_sources_are_rejected(
    repository: Path,
) -> None:
    with pytest.raises(WebSourceParseError):
        parse_web_imports(repository, "src/missing.tsx")

    write_source(repository, "config.json", '{"enabled": true}\n')

    with pytest.raises(WebSourceParseError):
        parse_web_imports(repository, "config.json")


def test_symbolic_link_source_is_rejected(
    repository: Path,
) -> None:
    write_source(repository, "src/target.ts", "export {};\n")
    link = repository / "src" / "linked.ts"

    try:
        link.symlink_to("target.ts")
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"Symbolic links are unavailable: {exc}")

    with pytest.raises(
        WebSourceParseError,
        match="Symbolic-link",
    ):
        parse_web_imports(repository, "src/linked.ts")


def test_utf8_bom_is_supported_and_invalid_encoding_fails_closed(
    repository: Path,
) -> None:
    write_source(repository, "src/dependency.ts", "export {};\n")
    write_bytes(
        repository,
        "src/bom.ts",
        b'\xef\xbb\xbfimport "./dependency";\n',
    )

    evidence = parse_web_imports(repository, "src/bom.ts")

    assert len(evidence) == 1
    assert evidence[0].imported_name == "./dependency"
    assert evidence[0].resolved_path == "src/dependency.ts"

    write_bytes(repository, "src/invalid.ts", b"\xff\xfe\xfa")

    with pytest.raises(
        WebSourceParseError,
        match="Unable to decode",
    ):
        parse_web_imports(repository, "src/invalid.ts")


def test_source_size_limit_fails_closed(
    repository: Path,
) -> None:
    write_bytes(
        repository,
        "src/oversized.ts",
        b"x" * (2 * 1024 * 1024 + 1),
    )

    with pytest.raises(
        WebSourceParseError,
        match="size limit",
    ):
        parse_web_imports(repository, "src/oversized.ts")


def test_malformed_tsconfig_fails_closed_for_alias_resolution(
    repository: Path,
) -> None:
    write_source(
        repository,
        "REOS_CONTROL_CENTER/Frontend/tsconfig.json",
        "{ this is not valid JSON }\n",
    )
    write_source(
        repository,
        "REOS_CONTROL_CENTER/Frontend/src/page.tsx",
        'import Card from "@/Card";\n',
    )

    with pytest.raises(
        WebSourceParseError,
        match="Unable to read frontend tsconfig",
    ):
        parse_web_imports(
            repository,
            "REOS_CONTROL_CENTER/Frontend/src/page.tsx",
        )
