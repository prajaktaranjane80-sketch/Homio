from __future__ import annotations

import importlib.util
import json
import os
import sys
import subprocess
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


atlas = load_module("homio_atlas_under_test", HERE / "project_reference_atlas.py")
entrypoint_updater = load_module(
    "homio_entrypoint_updater_under_test",
    HERE / "update_entrypoint_atlas_reference.py",
)


class GitTreeAndIdentityTests(unittest.TestCase):
    def _repository(self, root: Path) -> None:
        subprocess.run(["git", "init", "-b", "reos-development"], cwd=root, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test Owner"], cwd=root, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=root, check=True)
        subprocess.run(
            ["git", "remote", "add", "origin", "https://github.com/prajaktaranjane80-sketch/Homio.git"],
            cwd=root, check=True,
        )
        (root / "REOS_CONTROL_CENTER" / "data").mkdir(parents=True)
        (root / "REOS_CONTROL_CENTER" / "data" / "state.json").write_text("{}\n", encoding="utf-8")
        (root / "REOS_CONTROL_CENTER" / "AI_AGENT_ENTRYPOINT.py").write_text("ENTRYPOINT_RELATIVE_PATH = 'x'\n", encoding="utf-8")
        (root / "space file.py").write_text("VALUE = 1\n", encoding="utf-8")
        (root / "README.md").write_text("# Atlas\n`space file.py`\n", encoding="utf-8")
        subprocess.run(["git", "add", "-A"], cwd=root, check=True)
        subprocess.run(["git", "commit", "-m", "baseline"], cwd=root, check=True, capture_output=True)

    def test_git_tree_reads_complete_leaf_inventory_including_spaces(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._repository(root)
            entries = atlas._git_entries(root)
            paths = {item.path for item in entries}
            self.assertIn("space file.py", paths)
            self.assertIn("README.md", paths)
            self.assertIn("REOS_CONTROL_CENTER/data/state.json", paths)

    def test_identity_requires_canonical_repo_branch_and_clean_tree(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._repository(root)
            identity = atlas._identity(root, "reos-development", require_live_tip=False)
            self.assertEqual(identity["repository"], atlas.REPOSITORY_FULL_NAME)
            self.assertEqual(identity["source_branch"], "reos-development")
            self.assertEqual(len(identity["source_commit_sha"]), 40)
            (root / "untracked.txt").write_text("dirty", encoding="utf-8")
            with self.assertRaises(atlas.AtlasGenerationError):
                atlas._identity(root, "reos-development", require_live_tip=False)

    def test_wrong_origin_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._repository(root)
            subprocess.run(
                ["git", "remote", "set-url", "origin", "https://github.com/example/other.git"],
                cwd=root, check=True,
            )
            with self.assertRaises(atlas.AtlasGenerationError):
                atlas._identity(root, "reos-development", require_live_tip=False)

    def test_path_traversal_is_rejected(self):
        with self.assertRaises(atlas.AtlasGenerationError):
            atlas._safe_repo_path("../outside.py")

    def test_document_reference_index_only_emits_exact_tracked_paths(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._repository(root)
            entries = atlas._git_entries(root)
            known = {item.path for item in entries}
            refs, skipped = atlas._documentation_references(root, entries, known)
            self.assertEqual(skipped, [])
            self.assertIn(
                {"source_path": "README.md", "target_path": "space file.py", "evidence": "EXACT_BACKTICK_PATH"},
                refs,
            )


class AtlasIntegrityTests(unittest.TestCase):
    def _valid(self):
        result = {
            "atlas_schema_version": "1.0.0",
            "status": "CURRENT",
            "repository": atlas.REPOSITORY_FULL_NAME,
            "source_baseline": {
                "repository": atlas.REPOSITORY_FULL_NAME,
                "source_branch": "reos-development",
                "source_commit_sha": "a" * 40,
                "source_tree_sha": "b" * 40,
                "state_json_path": atlas.STATE_RELATIVE_PATH,
                "state_json_blob_sha": "c" * 40,
                "entrypoint_path": atlas.ENTRYPOINT_RELATIVE_PATH,
                "entrypoint_blob_sha": "d" * 40,
                "reference_branch": atlas.REFERENCE_BRANCH,
                "reference_path": atlas.ATLAS_RELATIVE_PATH,
            },
            "authority_model": {},
            "coverage": {
                "inventory_complete": True,
                "tracked_entry_count": 1,
                "inventory_entry_count": 1,
                "runtime_relationships_proven": False,
                "all_repository_code_semantics_proven": False,
            },
            "inventory": {
                "source": "git ls-tree -r -z --full-tree HEAD",
                "entries": [{"path": "a.py", "object_sha": "e" * 40, "object_type": "blob"}],
                "indexes": {},
            },
            "architecture": {},
            "relationships": {},
            "provenance": {},
            "known_limitations": [],
        }
        result["integrity"] = {"algorithm": "sha256", "sha256": atlas._canonical_fingerprint(result)}
        return result

    def test_valid_atlas_integrity_is_accepted(self):
        atlas.validate_atlas(self._valid())

    def test_modified_atlas_is_rejected_by_integrity_fingerprint(self):
        result = self._valid()
        result["coverage"]["tracked_entry_count"] = 2
        with self.assertRaises(atlas.AtlasGenerationError):
            atlas.validate_atlas(result)

    def test_inventory_complete_claim_must_match_exact_count(self):
        result = self._valid()
        result["coverage"]["tracked_entry_count"] = 2
        result["integrity"]["sha256"] = atlas._canonical_fingerprint(result)
        with self.assertRaises(atlas.AtlasGenerationError):
            atlas.validate_atlas(result)

    def test_semantic_status_is_partial_when_any_source_parser_fails(self):
        self.assertEqual(
            atlas._atlas_status(
                t16_available=True,
                parser_failures=[],
                invalid_t16_modules=[],
            ),
            "CURRENT",
        )
        self.assertEqual(
            atlas._atlas_status(
                t16_available=True,
                parser_failures=["bad.ts:WebSourceParseError"],
                invalid_t16_modules=[],
            ),
            "INVENTORY_CURRENT_SEMANTICS_PARTIAL",
        )
        self.assertEqual(
            atlas._atlas_status(
                t16_available=True,
                parser_failures=[],
                invalid_t16_modules=["bad.py"],
            ),
            "INVENTORY_CURRENT_SEMANTICS_PARTIAL",
        )
        self.assertEqual(
            atlas._atlas_status(
                t16_available=False,
                parser_failures=[],
                invalid_t16_modules=[],
            ),
            "INVENTORY_CURRENT_SEMANTICS_PARTIAL",
        )

    def test_atlas_rejects_semantic_authority_overclaim(self):
        result = self._valid()
        result["coverage"]["runtime_relationships_proven"] = True
        result["integrity"]["sha256"] = atlas._canonical_fingerprint(result)
        with self.assertRaises(atlas.AtlasGenerationError):
            atlas.validate_atlas(result)

    def test_atlas_rejects_wrong_reference_branch(self):
        result = self._valid()
        result["source_baseline"]["reference_branch"] = "reos-development"
        result["integrity"]["sha256"] = atlas._canonical_fingerprint(result)
        with self.assertRaises(atlas.AtlasGenerationError):
            atlas.validate_atlas(result)

    def test_checked_in_schema_contract_matches_generator_top_level(self):
        schema_path = HERE.parents[5] / atlas.SCHEMA_RELATIVE_PATH
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        atlas.validate_schema_contract(schema)

    def test_schema_contract_rejects_missing_required_sections(self):
        with self.assertRaises(atlas.AtlasGenerationError):
            atlas.validate_schema_contract({"$schema": "https://json-schema.org/draft/2020-12/schema", "required": []})


class EntryPointUpdaterTests(unittest.TestCase):
    SAMPLE = '''"""Existing HOMIO policy."""
from __future__ import annotations
ENTRYPOINT_RELATIVE_PATH = "REOS_CONTROL_CENTER/AI_AGENT_ENTRYPOINT.py"
DOCUMENT_REGISTRY = {
}
SOURCE_OF_TRUTH = {
}
ACRL_OWNER_ROUTING = {
}
NEW_SESSION_READ_ORDER = (
    "9. Read the selected workstream's master reference.",
)
NEW_SESSION_WORKFLOW = (
    "11. Read approved architecture and the selected workstream master plan.",
)
def repository_paths():
    return {
    }
def startup_instructions():
    return {
    }
'''

    def test_full_replacement_preserves_existing_policy_and_adds_atlas_contract(self):
        replacement = entrypoint_updater.update_entrypoint(self.SAMPLE)
        self.assertIn('"""Existing HOMIO policy."""', replacement)
        self.assertIn("def repository_paths():", replacement)
        self.assertIn("PROJECT_REFERENCE_ATLAS_REFERENCE", replacement)
        self.assertIn("'project_reference_atlas'", replacement)
        self.assertIn("'project_reference_atlas_rules'", replacement)
        self.assertIn("'project_reference_atlas_generation'", replacement)
        self.assertLess(
            replacement.index("Before broad source reads, retrieve the exact Atlas"),
            replacement.index("9. Read the selected workstream's master reference"),
        )
        self.assertLess(
            replacement.index("Validate the derived project reference Atlas"),
            replacement.index("11. Read approved architecture"),
        )
        compile(replacement, "AI_AGENT_ENTRYPOINT.py", "exec")

    def test_updater_is_idempotent(self):
        once = entrypoint_updater.update_entrypoint(self.SAMPLE)
        twice = entrypoint_updater.update_entrypoint(once)
        self.assertEqual(once, twice)

    def test_partial_managed_block_is_rejected(self):
        broken = self.SAMPLE + "\n" + entrypoint_updater.BEGIN + "\n"
        with self.assertRaises(ValueError):
            entrypoint_updater.update_entrypoint(broken)

    def test_managed_block_with_missing_registry_or_startup_integration_is_rejected(self):
        installed = entrypoint_updater.update_entrypoint(self.SAMPLE)
        broken = installed.replace(
            "'project_reference_atlas_rules': list(PROJECT_REFERENCE_ATLAS_RULES),",
            "",
        )
        with self.assertRaises(ValueError):
            entrypoint_updater.update_entrypoint(broken)

    def test_existing_registry_key_is_not_duplicated(self):
        already = self.SAMPLE.replace("DOCUMENT_REGISTRY = {", "DOCUMENT_REGISTRY = {\n    'project_reference_atlas': {},")
        with self.assertRaises(ValueError):
            entrypoint_updater.update_entrypoint(already)


class EndToEndAtlasTests(unittest.TestCase):
    def _write(self, root: Path, relative: str, content: str) -> None:
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

    def test_full_git_bound_atlas_builds_with_existing_t16_owner(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            package = (
                "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/continuity/acrl/"
                "T16_Repository_Intelligence_File_Discovery"
            )
            for folder in (
                "REOS_CONTROL_CENTER",
                "REOS_CONTROL_CENTER/AUTONOMY_ENGINE",
                "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/continuity",
                "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/continuity/acrl",
                package,
                package + "/source_intelligence",
            ):
                self._write(root, folder + "/__init__.py", "")
            self._write(
                root,
                package + "/repository_intelligence.py",
                "from types import SimpleNamespace\n"
                "class RepositoryIntelligenceEngine:\n"
                "    def __init__(self, root): self.root = root\n"
                "    def discover(self):\n"
                "        return SimpleNamespace(schema_version='test', files=(), modules=(), excluded_paths=(), fingerprint='t16-test-snapshot')\n",
            )
            self._write(root, package + "/source_intelligence/__init__.py", "")
            self._write(
                root,
                package + "/source_intelligence/source_parser.py",
                "def parse_imports(root, path): return ()\n",
            )
            self._write(
                root,
                package + "/source_intelligence/web_source_parser.py",
                "def parse_web_imports(root, path): return ()\n",
            )
            self._write(root, "REOS_CONTROL_CENTER/data/state.json", '{"meta":{"version":"test"}}\n')
            self._write(
                root,
                "REOS_CONTROL_CENTER/AI_AGENT_ENTRYPOINT.py",
                "ENTRYPOINT_RELATIVE_PATH = 'REOS_CONTROL_CENTER/AI_AGENT_ENTRYPOINT.py'\n"
                "DOCUMENT_REGISTRY = {'backend_master': {'path': 'REOS_CONTROL_CENTER/architecture/backend/plans/HOMIO_Backend_Structure', 'role': 'Master', 'authority': 'PLAN'}}\n"
                "WORKSTREAM_ROUTING = {'BACKEND': {'master_reference': 'REOS_CONTROL_CENTER/architecture/backend/plans/HOMIO_Backend_Structure'}}\n"
                "ACRL_OWNER_ROUTING = {'repository_discovery_and_snapshot': 'acrl_t16'}\n",
            )
            source_schema = HERE.parents[5] / atlas.SCHEMA_RELATIVE_PATH
            self._write(root, atlas.SCHEMA_RELATIVE_PATH, source_schema.read_text(encoding="utf-8"))
            self._write(root, atlas.GENERATOR_RELATIVE_PATH, Path(atlas.__file__).read_text(encoding="utf-8"))
            self._write(root, "README.md", "# Index\nSee `REOS_CONTROL_CENTER/data/state.json`.\n")
            self._write(root, "module.py", "VALUE = 1\n")
            self._write(root, ".gitignore", "__pycache__/\n*.pyc\n")
            self._write(root, ".github/workflows/demo.yml", "name: Demo\njobs:\n  verify:\n    runs-on: ubuntu-latest\n")
            subprocess.run(["git", "init", "-b", "reos-development"], cwd=root, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.name", "Test Owner"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=root, check=True)
            subprocess.run(["git", "remote", "add", "origin", "https://github.com/prajaktaranjane80-sketch/Homio.git"], cwd=root, check=True)
            subprocess.run(["git", "add", "-A"], cwd=root, check=True)
            subprocess.run(["git", "commit", "-m", "test baseline"], cwd=root, check=True, capture_output=True)

            built = atlas.build_atlas(root, require_t16=True, require_live_tip=False)
            atlas.validate_atlas(built)
            self.assertTrue(built["coverage"]["inventory_complete"])
            self.assertEqual(built["coverage"]["tracked_entry_count"], built["coverage"]["inventory_entry_count"])
            self.assertEqual(built["status"], "CURRENT")
            self.assertEqual(built["source_baseline"]["source_branch"], "reos-development")
            self.assertEqual(built["source_baseline"]["reference_branch"], "reos-project-reference")
            self.assertTrue(any(item["target_path"] == "REOS_CONTROL_CENTER/data/state.json" for item in built["relationships"]["documentation_references"]))
            self.assertEqual(built["architecture"]["ci_workflows"][0]["job_names"], ["verify"])
            self.assertTrue(built["integrity"]["sha256"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
