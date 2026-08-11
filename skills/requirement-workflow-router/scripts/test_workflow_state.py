#!/usr/bin/env python3

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
import uuid


SCRIPT = Path(__file__).with_name("workflow_state.py")


class WorkflowStateTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name) / "control"
        self.materials = Path(self.tempdir.name) / "materials"
        self.cli("init", "--materials-root", str(self.materials))

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def cli(self, *args: str, expect: int = 0) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            ["python3", str(SCRIPT), "--home", str(self.root), *args],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self.assertEqual(result.returncode, expect, result.stderr)
        return result

    def operation(self) -> str:
        return str(uuid.uuid4())

    def git(self, *args: str) -> str:
        return subprocess.run(
            ["git", "-C", str(self.materials), *args],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        ).stdout.strip()

    def commit_file(self, relative: str, body: str) -> str:
        path = self.materials / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
        self.git("add", relative)
        self.git("commit", "-m", f"add {relative}")
        return hashlib.sha256(body.encode("utf-8")).hexdigest()

    def admit(self, requirement_id: str) -> dict:
        result = self.cli(
            "admit",
            "--id",
            requirement_id,
            "--title",
            requirement_id,
            "--project-root",
            str(Path(self.tempdir.name) / "product"),
            "--owner-label",
            "owner",
            "--operation-id",
            self.operation(),
        )
        return json.loads(result.stdout)

    def test_pilot_slot_material_publish_and_approval_gate(self) -> None:
        first = self.admit("REQ-1")
        self.assertEqual((first["lifecycle"], first["slot"], first["stage"]), ("active", 1, "frame"))
        second = self.admit("REQ-2")
        self.assertEqual((second["lifecycle"], second["slot"]), ("queued", None))

        self.commit_file("REQ-1/需求与边界.md", "# frame\n")
        published = json.loads(
            self.cli(
                "publish-material",
                "--id",
                "REQ-1",
                "--kind",
                "frame",
                "--path",
                "REQ-1/需求与边界.md",
                "--operation-id",
                self.operation(),
            ).stdout
        )
        self.assertEqual(published["materials"][0]["kind"], "frame")

        self.cli(
            "transition",
            "--id",
            "REQ-1",
            "--expected-stage",
            "frame",
            "--to-stage",
            "align",
            "--owner-generation",
            "1",
            "--operation-id",
            self.operation(),
        )
        self.cli(
            "transition",
            "--id",
            "REQ-1",
            "--expected-stage",
            "align",
            "--to-stage",
            "plan",
            "--owner-generation",
            "1",
            "--operation-id",
            self.operation(),
        )

        roadmap_digest = self.commit_file("REQ-1/路线图.md", "# roadmap\n")
        self.cli(
            "publish-material",
            "--id",
            "REQ-1",
            "--kind",
            "roadmap",
            "--path",
            "REQ-1/路线图.md",
            "--operation-id",
            self.operation(),
        )
        self.cli(
            "transition",
            "--id",
            "REQ-1",
            "--expected-stage",
            "plan",
            "--to-stage",
            "execute",
            "--owner-generation",
            "1",
            "--approved-roadmap-sha256",
            roadmap_digest,
            "--operation-id",
            self.operation(),
            expect=1,
        )
        self.cli(
            "approve-plan",
            "--id",
            "REQ-1",
            "--roadmap-sha256",
            roadmap_digest,
            "--operation-id",
            self.operation(),
        )
        executed = json.loads(
            self.cli(
                "transition",
                "--id",
                "REQ-1",
                "--expected-stage",
                "plan",
                "--to-stage",
                "execute",
                "--owner-generation",
                "1",
                "--approved-roadmap-sha256",
                roadmap_digest,
                "--operation-id",
                self.operation(),
            ).stdout
        )
        self.assertEqual(executed["stage"], "execute")
        verified = json.loads(self.cli("verify").stdout)
        self.assertEqual(verified["quick_check"], "ok")
        self.assertEqual(verified["max_active"], 1)

    def test_operation_id_and_owner_generation_are_fenced(self) -> None:
        operation_id = self.operation()
        args = (
            "admit",
            "--id",
            "REQ-1",
            "--title",
            "first",
            "--project-root",
            str(Path(self.tempdir.name) / "product"),
            "--operation-id",
            operation_id,
        )
        first = self.cli(*args).stdout
        replay = self.cli(*args).stdout
        self.assertEqual(json.loads(first), json.loads(replay))
        self.cli(
            "admit",
            "--id",
            "REQ-1",
            "--title",
            "changed",
            "--project-root",
            str(Path(self.tempdir.name) / "product"),
            "--operation-id",
            operation_id,
            expect=1,
        )
        claimed = json.loads(
            self.cli(
                "claim",
                "--id",
                "REQ-1",
                "--expected-generation",
                "1",
                "--owner-label",
                "fresh-owner",
                "--operation-id",
                self.operation(),
            ).stdout
        )
        self.assertEqual(claimed["owner_generation"], 2)
        self.cli(
            "transition",
            "--id",
            "REQ-1",
            "--expected-stage",
            "frame",
            "--to-stage",
            "align",
            "--owner-generation",
            "1",
            "--operation-id",
            self.operation(),
            expect=1,
        )


if __name__ == "__main__":
    unittest.main()
