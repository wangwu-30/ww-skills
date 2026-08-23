#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).with_name("repo_state.py")


class RepoStateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp.name) / "repo with spaces"
        self.repo.mkdir()
        self.knowledge = self.repo / ".repo-alive"

    def tearDown(self) -> None:
        self.temp.cleanup()

    def run_tool(self, command: str, *extra: str, expected: int = 0) -> dict:
        process = subprocess.run(
            [sys.executable, str(SCRIPT), command, "--repo", str(self.repo), *extra],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(process.returncode, expected, process.stderr + process.stdout)
        return json.loads(process.stdout)

    def git(self, *args: str) -> None:
        process = subprocess.run(["git", "-C", str(self.repo), *args], capture_output=True, text=True, check=False)
        self.assertEqual(process.returncode, 0, process.stderr)

    def init_git(self) -> None:
        self.git("init")
        self.git("config", "user.email", "test@example.invalid")
        self.git("config", "user.name", "Test User")
        (self.repo / "source.txt").write_text("one\n", encoding="utf-8")
        self.git("add", "source.txt")
        self.git("commit", "-m", "initial")

    def knowledge_files(self) -> None:
        self.knowledge.mkdir(exist_ok=True)
        (self.knowledge / "overview.md").write_text("overview\n", encoding="utf-8")
        (self.knowledge / "routes.md").write_text("routes\n", encoding="utf-8")

    def stamp(self) -> None:
        self.assertEqual(self.run_tool("stamp")["state"], "fresh")

    def test_missing(self) -> None:
        result = self.run_tool("status")
        self.assertEqual(result["state"], "missing")

    def test_clean_stamp_fresh_and_knowledge_excluded(self) -> None:
        self.init_git(); self.knowledge_files(); self.stamp()
        (self.knowledge / "overview.md").write_text("changed output\n", encoding="utf-8")
        result = self.run_tool("status")
        self.assertEqual(result["state"], "invalid")
        self.assertIn("artifact", result["reason"])
        # A newly stamped output is excluded from source digest changes.
        self.stamp()
        self.assertEqual(self.run_tool("status")["state"], "fresh")

    def test_same_head_staged_unstaged_and_untracked_source(self) -> None:
        self.init_git(); self.knowledge_files(); self.stamp()
        (self.repo / "source.txt").write_text("two\n", encoding="utf-8")
        self.git("add", "source.txt")
        result = self.run_tool("status")
        self.assertEqual(result["state"], "stale")
        self.assertIn("source.txt", result["changed_paths"])
        self.git("reset", "--", "source.txt")
        self.stamp()
        (self.repo / "untracked.txt").write_text("new\n", encoding="utf-8")
        result = self.run_tool("status")
        self.assertEqual(result["state"], "stale")
        self.assertIn("untracked.txt", result["changed_paths"])

    def test_index_change_survives_worktree_restore(self) -> None:
        self.init_git(); self.knowledge_files(); self.stamp()
        (self.repo / "source.txt").write_text("staged only\n", encoding="utf-8")
        self.git("add", "source.txt")
        self.git("restore", "--worktree", "source.txt")
        result = self.run_tool("verify", expected=1)
        self.assertEqual(result["state"], "stale")
        self.assertIn("source.txt", result["changed_paths"])

    def test_chmod_only_change_is_stale_when_observable(self) -> None:
        self.init_git(); self.knowledge_files(); self.stamp()
        source = self.repo / "source.txt"
        source.chmod(source.stat().st_mode | 0o111)
        result = self.run_tool("status")
        if "source.txt" not in result["changed_paths"]:
            self.skipTest("filesystem or Git configuration does not observe executable mode")
        self.assertEqual(result["state"], "stale")

    def test_gitignored_untracked_is_excluded(self) -> None:
        self.init_git(); (self.repo / ".gitignore").write_text(".env\nbuild/\n", encoding="utf-8")
        self.git("add", ".gitignore"); self.git("commit", "-m", "ignore")
        self.knowledge_files(); self.stamp()
        (self.repo / ".env").write_text("secret\n", encoding="utf-8")
        (self.repo / "build").mkdir(); (self.repo / "build/out").write_text("output\n", encoding="utf-8")
        self.assertEqual(self.run_tool("status")["state"], "fresh")

    def test_dirty_stamp_then_source_changes(self) -> None:
        self.init_git(); self.knowledge_files()
        (self.repo / "source.txt").write_text("dirty\n", encoding="utf-8")
        self.stamp()
        self.assertEqual(self.run_tool("verify")["state"], "fresh")
        (self.repo / "source.txt").write_text("dirtier\n", encoding="utf-8")
        self.assertEqual(self.run_tool("verify", expected=1)["state"], "stale")

    def test_new_commit_changed_paths(self) -> None:
        self.init_git(); self.knowledge_files(); self.stamp()
        (self.repo / "source.txt").write_text("two\n", encoding="utf-8")
        self.git("add", "source.txt"); self.git("commit", "-m", "next")
        result = self.run_tool("status")
        self.assertEqual(result["state"], "stale")
        self.assertIn("source.txt", result["changed_paths"])

    def test_newline_path_in_committed_change_is_reported(self) -> None:
        self.init_git(); self.knowledge_files(); self.stamp()
        name = "source\nname.txt"
        (self.repo / name).write_text("newline path\n", encoding="utf-8")
        self.git("add", name); self.git("commit", "-m", "newline path")
        result = self.run_tool("status")
        self.assertEqual(result["state"], "stale")
        self.assertIn(name, result["changed_paths"])

    def test_staged_and_unstaged_renames_report_both_paths(self) -> None:
        self.init_git(); self.knowledge_files(); self.stamp()
        old, new = "old name.txt", "new name.txt"
        (self.repo / old).write_text("rename me\n", encoding="utf-8")
        self.git("add", old); self.git("commit", "-m", "add old")
        self.stamp(); self.git("mv", old, new)
        result = self.run_tool("status")
        self.assertEqual(result["state"], "stale")
        self.assertTrue({old, new}.issubset(result["changed_paths"]))
        self.git("reset", "--hard", "HEAD")
        self.stamp(); (self.repo / old).rename(self.repo / new)
        result = self.run_tool("status")
        self.assertEqual(result["state"], "stale")
        self.assertTrue({old, new}.issubset(result["changed_paths"]))

    def test_non_git_directory_symlink_repoint_is_stale(self) -> None:
        self.knowledge_files(); target_one = Path(self.temp.name) / "target-one"; target_two = Path(self.temp.name) / "target-two"
        target_one.mkdir(); target_two.mkdir()
        link = self.repo / "linked-dir"
        try:
            link.symlink_to(target_one, target_is_directory=True)
        except OSError:
            self.skipTest("symlinks are unavailable")
        self.stamp(); link.unlink(); link.symlink_to(target_two, target_is_directory=True)
        self.assertEqual(self.run_tool("verify", expected=1)["state"], "stale")

    def test_non_git_common_directories_are_source_content(self) -> None:
        directories = ("build", "dist", "node_modules", ".cache", "venv")
        for directory in directories:
            with self.subTest(directory=directory):
                case_root = self.repo / directory
                case_root.mkdir(parents=True, exist_ok=True)
                self.knowledge_files(); self.stamp()
                artifact = case_root / "state.txt"
                artifact.write_text("new\n", encoding="utf-8")
                self.assertEqual(self.run_tool("verify", expected=1)["state"], "stale")
                self.stamp()
                artifact.write_text("modified\n", encoding="utf-8")
                self.assertEqual(self.run_tool("verify", expected=1)["state"], "stale")

    def test_malformed_missing_and_tampered_artifact(self) -> None:
        self.init_git(); self.knowledge_files(); self.stamp()
        (self.knowledge / "fingerprint.json").write_text("not json", encoding="utf-8")
        self.assertEqual(self.run_tool("verify", expected=1)["state"], "invalid")
        self.stamp()
        (self.knowledge / "routes.md").unlink()
        self.assertEqual(self.run_tool("status")["state"], "invalid")

    def test_root_fingerprint_symlink_is_invalid_and_not_trusted(self) -> None:
        self.init_git(); self.knowledge_files(); self.stamp()
        target = Path(self.temp.name) / "trusted-looking.json"
        target.write_text((self.knowledge / "fingerprint.json").read_text(encoding="utf-8"), encoding="utf-8")
        (self.knowledge / "fingerprint.json").unlink()
        (self.knowledge / "fingerprint.json").symlink_to(target)
        result = self.run_tool("verify", expected=1)
        self.assertEqual(result["state"], "invalid")
        self.assertIn("regular", result["reason"])

    def test_nested_fingerprint_artifact_is_manifested_and_drift_detected(self) -> None:
        self.init_git(); self.knowledge_files()
        domains = self.knowledge / "domains"; domains.mkdir()
        nested = domains / "fingerprint.json"
        nested.write_text("domain artifact\n", encoding="utf-8")
        self.stamp()
        fingerprint = json.loads((self.knowledge / "fingerprint.json").read_text(encoding="utf-8"))
        self.assertIn("domains/fingerprint.json", fingerprint["artifact_manifest"])
        nested.write_text("drifted domain artifact\n", encoding="utf-8")
        self.assertEqual(self.run_tool("verify", expected=1)["state"], "invalid")
        self.knowledge_files(); self.stamp()
        (self.knowledge / "routes.md").write_text("tampered\n", encoding="utf-8")
        self.assertEqual(self.run_tool("status")["state"], "invalid")

    def test_unsafe_artifact_path_is_invalid(self) -> None:
        self.init_git(); self.knowledge_files(); self.stamp()
        fingerprint_path = self.knowledge / "fingerprint.json"
        fingerprint = json.loads(fingerprint_path.read_text(encoding="utf-8"))
        fingerprint["artifact_manifest"]["../outside.md"] = "0" * 64
        fingerprint_path.write_text(json.dumps(fingerprint), encoding="utf-8")
        result = self.run_tool("status")
        self.assertEqual(result["state"], "invalid")
        self.assertIn("unsafe", result["reason"])

    def test_unmanifested_and_missing_required_manifest_artifact(self) -> None:
        self.init_git(); self.knowledge_files(); self.stamp()
        (self.knowledge / "extra.md").write_text("extra\n", encoding="utf-8")
        self.assertEqual(self.run_tool("status")["state"], "invalid")
        self.stamp()
        path = self.knowledge / "fingerprint.json"; data = json.loads(path.read_text(encoding="utf-8"))
        del data["artifact_manifest"]["routes.md"]
        path.write_text(json.dumps(data), encoding="utf-8")
        self.assertEqual(self.run_tool("verify", expected=1)["state"], "invalid")

    def test_external_symlink_knowledge_and_invalid_repo_are_controlled(self) -> None:
        self.init_git(); self.knowledge_files()
        external = Path(self.temp.name) / "external"; external.mkdir()
        result = self.run_tool("status", "--knowledge-dir", str(external))
        self.assertEqual(result["state"], "invalid")
        for child in self.knowledge.iterdir():
            child.unlink()
        self.knowledge.rmdir(); self.knowledge.symlink_to(external, target_is_directory=True)
        result = self.run_tool("status")
        self.assertEqual(result["state"], "invalid")
        process = subprocess.run([sys.executable, str(SCRIPT), "verify", "--repo", str(self.repo / "none")], capture_output=True, text=True)
        self.assertEqual(process.returncode, 1); self.assertEqual(json.loads(process.stdout)["state"], "invalid")

    def test_repository_root_cannot_be_knowledge_directory(self) -> None:
        self.init_git()
        result = self.run_tool("status", "--knowledge-dir", ".")
        self.assertEqual(result["state"], "invalid")
        self.assertIn("must not be the repository root", result["reason"])
        self.assertEqual(self.run_tool("stamp", "--knowledge-dir", ".", expected=1)["state"], "invalid")

    def test_force_non_git_and_no_absolute_paths(self) -> None:
        self.knowledge_files(); self.stamp()
        self.assertEqual(self.run_tool("status", "--force")["state"], "forced")
        (self.repo / "plain.txt").write_text("changed\n", encoding="utf-8")
        self.assertEqual(self.run_tool("status")["state"], "stale")
        fingerprint = (self.knowledge / "fingerprint.json").read_text(encoding="utf-8")
        self.assertNotIn(str(self.repo), fingerprint)


if __name__ == "__main__":
    unittest.main(verbosity=2)
