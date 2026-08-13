#!/usr/bin/env python3
"""Single-writer mechanical state for the explicit requirement-workflow pilot."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
from typing import Any


SCHEMA_VERSION = 1
HARD_MAX_ACTIVE = 3
STAGES = ("frame", "research", "align", "plan", "execute", "close", "closed")
LIFECYCLES = ("queued", "active", "paused", "closed")
MATERIAL_KINDS = (
    "context",
    "frame",
    "research",
    "proposal",
    "decisions",
    "roadmap",
    "acceptance",
)
ALLOWED_TRANSITIONS = {
    "frame": {"research", "align"},
    "research": {"frame", "align"},
    "align": {"research", "plan"},
    "plan": {"align", "execute"},
    "execute": {"plan", "align", "close"},
    "close": {"execute", "align", "closed"},
    "closed": set(),
}


class WorkflowError(RuntimeError):
    pass


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def run_git(repo: Path, *args: str, binary: bool = False) -> str | bytes:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        stderr = result.stderr.decode("utf-8", "replace").strip()
        raise WorkflowError(f"git {' '.join(args)} failed: {stderr}")
    if binary:
        return result.stdout
    return result.stdout.decode("utf-8").strip()


def workflow_home(explicit: str | None) -> Path:
    raw = explicit or os.environ.get("REQUIREMENT_WORKFLOW_HOME")
    if raw:
        return Path(raw).expanduser().resolve()
    return (Path.home() / ".codex" / "requirement-workflow").resolve()


def connect(db_path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(db_path, timeout=5.0)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys=ON")
    connection.execute("PRAGMA busy_timeout=5000")
    connection.execute("PRAGMA synchronous=FULL")
    journal_mode = connection.execute("PRAGMA journal_mode").fetchone()[0].lower()
    if journal_mode != "delete":
        connection.close()
        raise WorkflowError(f"state database must use DELETE journal mode, got {journal_mode}")
    return connection


def initialize(root: Path, materials_root_arg: str | None) -> dict[str, Any]:
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(root, 0o700)
    materials_root = (
        Path(materials_root_arg).expanduser().resolve()
        if materials_root_arg
        else (root / "materials").resolve()
    )
    materials_root.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(materials_root, 0o700)
    if not (materials_root / ".git").exists():
        subprocess.run(
            ["git", "init", "-b", "main", str(materials_root)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        run_git(materials_root, "config", "user.name", "Codex Requirement Workflow")
        run_git(materials_root, "config", "user.email", "requirement-workflow@local.invalid")

    db_path = root / "state.sqlite3"
    connection = sqlite3.connect(db_path, timeout=5.0)
    try:
        connection.execute("PRAGMA journal_mode=DELETE")
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA busy_timeout=5000")
        connection.execute("PRAGMA synchronous=FULL")
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS requirements (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL CHECK(length(title) BETWEEN 1 AND 240),
                project_root TEXT NOT NULL,
                lifecycle TEXT NOT NULL CHECK(lifecycle IN ('queued','active','paused','closed')),
                stage TEXT NOT NULL CHECK(stage IN ('frame','research','align','plan','execute','close','closed')),
                slot INTEGER CHECK(slot BETWEEN 1 AND 3),
                owner_label TEXT,
                owner_generation INTEGER NOT NULL DEFAULT 1 CHECK(owner_generation >= 1),
                approved_plan_sha256 TEXT CHECK(approved_plan_sha256 IS NULL OR approved_plan_sha256 GLOB '[0-9a-f]*' AND length(approved_plan_sha256)=64),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                CHECK(
                    (lifecycle='active' AND slot IS NOT NULL AND stage <> 'closed') OR
                    (lifecycle<>'active' AND slot IS NULL)
                ),
                CHECK((lifecycle='closed' AND stage='closed') OR lifecycle<>'closed')
            );

            CREATE UNIQUE INDEX IF NOT EXISTS active_slot_unique
            ON requirements(slot) WHERE lifecycle='active';

            CREATE TABLE IF NOT EXISTS materials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                requirement_id TEXT NOT NULL REFERENCES requirements(id) ON DELETE CASCADE,
                kind TEXT NOT NULL CHECK(kind IN ('context','frame','research','proposal','decisions','roadmap','acceptance')),
                git_commit TEXT NOT NULL CHECK(length(git_commit)=40),
                relative_path TEXT NOT NULL,
                sha256 TEXT NOT NULL CHECK(length(sha256)=64),
                is_current INTEGER NOT NULL CHECK(is_current IN (0,1)),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE UNIQUE INDEX IF NOT EXISTS current_material_kind_unique
            ON materials(requirement_id,kind) WHERE is_current=1;

            CREATE TABLE IF NOT EXISTS approvals (
                requirement_id TEXT PRIMARY KEY REFERENCES requirements(id) ON DELETE CASCADE,
                roadmap_sha256 TEXT NOT NULL CHECK(length(roadmap_sha256)=64),
                granted_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                revoked_at TEXT
            );

            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                operation_id TEXT NOT NULL UNIQUE,
                requirement_id TEXT,
                action TEXT NOT NULL,
                payload_sha256 TEXT NOT NULL CHECK(length(payload_sha256)=64),
                result_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(requirement_id) REFERENCES requirements(id) ON DELETE CASCADE
            );
            """
        )
        metadata = {
            "schema_version": str(SCHEMA_VERSION),
            "max_active": "1",
            "materials_root": str(materials_root),
        }
        for key, value in metadata.items():
            connection.execute(
                "INSERT INTO metadata(key,value) VALUES(?,?) ON CONFLICT(key) DO NOTHING",
                (key, value),
            )
        stored_root = connection.execute(
            "SELECT value FROM metadata WHERE key='materials_root'"
        ).fetchone()[0]
        if Path(stored_root).resolve() != materials_root:
            raise WorkflowError(
                f"materials root is already bound to {stored_root}, not {materials_root}"
            )
        connection.commit()
    finally:
        connection.close()
    os.chmod(db_path, 0o600)
    return {"database": str(db_path), "materials_root": str(materials_root), "max_active": 1}


def require_initialized(root: Path) -> tuple[Path, Path]:
    db_path = root / "state.sqlite3"
    if not db_path.is_file():
        raise WorkflowError(f"workflow state is not initialized: {db_path}")
    connection = connect(db_path)
    try:
        row = connection.execute(
            "SELECT value FROM metadata WHERE key='materials_root'"
        ).fetchone()
        if not row:
            raise WorkflowError("materials_root metadata is missing")
        materials_root = Path(row[0]).resolve()
    finally:
        connection.close()
    if not (materials_root / ".git").is_dir():
        raise WorkflowError(f"materials repository is missing: {materials_root}")
    return db_path, materials_root


def row_to_requirement(row: sqlite3.Row) -> dict[str, Any]:
    return {key: row[key] for key in row.keys()}


def requirement_snapshot(connection: sqlite3.Connection, requirement_id: str) -> dict[str, Any]:
    row = connection.execute(
        "SELECT * FROM requirements WHERE id=?", (requirement_id,)
    ).fetchone()
    if not row:
        raise WorkflowError(f"unknown requirement: {requirement_id}")
    result = row_to_requirement(row)
    result["materials"] = [
        {key: material[key] for key in material.keys()}
        for material in connection.execute(
            """
            SELECT kind,git_commit,relative_path,sha256,created_at
            FROM materials
            WHERE requirement_id=? AND is_current=1
            ORDER BY kind
            """,
            (requirement_id,),
        ).fetchall()
    ]
    return result


def begin_operation(
    connection: sqlite3.Connection,
    operation_id: str,
    requirement_id: str | None,
    action: str,
    payload: dict[str, Any],
) -> dict[str, Any] | None:
    payload_sha = sha256_bytes(canonical_json(payload).encode("utf-8"))
    existing = connection.execute(
        "SELECT requirement_id,action,payload_sha256,result_json FROM events WHERE operation_id=?",
        (operation_id,),
    ).fetchone()
    if not existing:
        return None
    if (
        existing["requirement_id"] != requirement_id
        or existing["action"] != action
        or existing["payload_sha256"] != payload_sha
    ):
        raise WorkflowError(f"operation-id conflict: {operation_id}")
    return json.loads(existing["result_json"])


def finish_operation(
    connection: sqlite3.Connection,
    operation_id: str,
    requirement_id: str | None,
    action: str,
    payload: dict[str, Any],
    result: dict[str, Any],
) -> None:
    payload_sha = sha256_bytes(canonical_json(payload).encode("utf-8"))
    connection.execute(
        """
        INSERT INTO events(operation_id,requirement_id,action,payload_sha256,result_json)
        VALUES(?,?,?,?,?)
        """,
        (operation_id, requirement_id, action, payload_sha, canonical_json(result)),
    )


def next_slot(connection: sqlite3.Connection, max_active: int) -> int | None:
    used = {
        row[0]
        for row in connection.execute(
            "SELECT slot FROM requirements WHERE lifecycle='active'"
        ).fetchall()
    }
    for slot in range(1, max_active + 1):
        if slot not in used:
            return slot
    return None


def command_admit(root: Path, args: argparse.Namespace) -> dict[str, Any]:
    db_path, _ = require_initialized(root)
    payload = {
        "id": args.id,
        "title": args.title,
        "project_root": str(Path(args.project_root).expanduser().resolve()),
    }
    connection = connect(db_path)
    try:
        connection.execute("BEGIN IMMEDIATE")
        replay = begin_operation(connection, args.operation_id, args.id, "admit", payload)
        if replay is not None:
            connection.rollback()
            return replay
        if connection.execute("SELECT 1 FROM requirements WHERE id=?", (args.id,)).fetchone():
            raise WorkflowError(f"requirement already exists: {args.id}")
        max_active = int(
            connection.execute("SELECT value FROM metadata WHERE key='max_active'").fetchone()[0]
        )
        slot = next_slot(connection, max_active)
        lifecycle = "active" if slot is not None else "queued"
        connection.execute(
            """
            INSERT INTO requirements(id,title,project_root,lifecycle,stage,slot,owner_label)
            VALUES(?,?,?,?,?,?,?)
            """,
            (args.id, args.title, payload["project_root"], lifecycle, "frame", slot, args.owner_label),
        )
        result = requirement_snapshot(connection, args.id)
        finish_operation(connection, args.operation_id, args.id, "admit", payload, result)
        connection.commit()
        return result
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def command_claim(root: Path, args: argparse.Namespace) -> dict[str, Any]:
    db_path, _ = require_initialized(root)
    payload = {
        "expected_generation": args.expected_generation,
        "owner_label": args.owner_label,
    }
    connection = connect(db_path)
    try:
        connection.execute("BEGIN IMMEDIATE")
        replay = begin_operation(connection, args.operation_id, args.id, "claim", payload)
        if replay is not None:
            connection.rollback()
            return replay
        cursor = connection.execute(
            """
            UPDATE requirements
            SET owner_generation=owner_generation+1,owner_label=?,updated_at=CURRENT_TIMESTAMP
            WHERE id=? AND owner_generation=? AND lifecycle IN ('active','paused')
            """,
            (args.owner_label, args.id, args.expected_generation),
        )
        if cursor.rowcount != 1:
            raise WorkflowError("stale owner generation or requirement is not claimable")
        result = requirement_snapshot(connection, args.id)
        finish_operation(connection, args.operation_id, args.id, "claim", payload, result)
        connection.commit()
        return result
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def safe_material_path(materials_root: Path, relative_path: str) -> tuple[Path, str]:
    path_obj = Path(relative_path)
    if path_obj.is_absolute() or ".." in path_obj.parts:
        raise WorkflowError("material path must be a safe repository-relative path")
    resolved = (materials_root / path_obj).resolve()
    try:
        resolved.relative_to(materials_root)
    except ValueError as exc:
        raise WorkflowError("material path escapes the materials repository") from exc
    if not resolved.is_file() or resolved.is_symlink():
        raise WorkflowError(f"material must be a regular non-symlink file: {resolved}")
    return resolved, path_obj.as_posix()


def committed_material(materials_root: Path, relative_path: str) -> tuple[str, str]:
    resolved, rel = safe_material_path(materials_root, relative_path)
    commit = str(run_git(materials_root, "rev-parse", "HEAD"))
    committed_bytes = run_git(materials_root, "show", f"{commit}:{rel}", binary=True)
    working_bytes = resolved.read_bytes()
    if committed_bytes != working_bytes:
        raise WorkflowError(f"material differs from committed HEAD bytes: {rel}")
    return commit, sha256_bytes(working_bytes)


def command_publish_material(root: Path, args: argparse.Namespace) -> dict[str, Any]:
    db_path, materials_root = require_initialized(root)
    if args.kind not in MATERIAL_KINDS:
        raise WorkflowError(f"unsupported material kind: {args.kind}")
    commit, digest = committed_material(materials_root, args.path)
    _, rel = safe_material_path(materials_root, args.path)
    payload = {"kind": args.kind, "path": rel, "commit": commit, "sha256": digest}
    connection = connect(db_path)
    try:
        connection.execute("BEGIN IMMEDIATE")
        replay = begin_operation(connection, args.operation_id, args.id, "publish-material", payload)
        if replay is not None:
            connection.rollback()
            return replay
        if not connection.execute("SELECT 1 FROM requirements WHERE id=?", (args.id,)).fetchone():
            raise WorkflowError(f"unknown requirement: {args.id}")
        connection.execute(
            "UPDATE materials SET is_current=0 WHERE requirement_id=? AND kind=? AND is_current=1",
            (args.id, args.kind),
        )
        connection.execute(
            """
            INSERT INTO materials(requirement_id,kind,git_commit,relative_path,sha256,is_current)
            VALUES(?,?,?,?,?,1)
            """,
            (args.id, args.kind, commit, rel, digest),
        )
        result = requirement_snapshot(connection, args.id)
        finish_operation(connection, args.operation_id, args.id, "publish-material", payload, result)
        connection.commit()
        return result
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def command_approve_plan(root: Path, args: argparse.Namespace) -> dict[str, Any]:
    db_path, _ = require_initialized(root)
    payload = {"roadmap_sha256": args.roadmap_sha256}
    connection = connect(db_path)
    try:
        connection.execute("BEGIN IMMEDIATE")
        replay = begin_operation(connection, args.operation_id, args.id, "approve-plan", payload)
        if replay is not None:
            connection.rollback()
            return replay
        current = connection.execute(
            """
            SELECT sha256 FROM materials
            WHERE requirement_id=? AND kind='roadmap' AND is_current=1
            """,
            (args.id,),
        ).fetchone()
        if not current or current[0] != args.roadmap_sha256:
            raise WorkflowError("approved digest does not match the current committed roadmap")
        connection.execute(
            """
            INSERT INTO approvals(requirement_id,roadmap_sha256,revoked_at)
            VALUES(?,?,NULL)
            ON CONFLICT(requirement_id) DO UPDATE SET
              roadmap_sha256=excluded.roadmap_sha256,
              granted_at=CURRENT_TIMESTAMP,
              revoked_at=NULL
            """,
            (args.id, args.roadmap_sha256),
        )
        connection.execute(
            "UPDATE requirements SET approved_plan_sha256=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (args.roadmap_sha256, args.id),
        )
        result = requirement_snapshot(connection, args.id)
        finish_operation(connection, args.operation_id, args.id, "approve-plan", payload, result)
        connection.commit()
        return result
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def command_transition(root: Path, args: argparse.Namespace) -> dict[str, Any]:
    db_path, _ = require_initialized(root)
    if args.to_stage not in ALLOWED_TRANSITIONS.get(args.expected_stage, set()):
        raise WorkflowError(f"invalid transition: {args.expected_stage} -> {args.to_stage}")
    payload = {
        "expected_stage": args.expected_stage,
        "to_stage": args.to_stage,
        "owner_generation": args.owner_generation,
        "approved_roadmap_sha256": args.approved_roadmap_sha256,
    }
    connection = connect(db_path)
    try:
        connection.execute("BEGIN IMMEDIATE")
        replay = begin_operation(connection, args.operation_id, args.id, "transition", payload)
        if replay is not None:
            connection.rollback()
            return replay
        row = connection.execute(
            "SELECT stage,lifecycle,owner_generation,approved_plan_sha256 FROM requirements WHERE id=?",
            (args.id,),
        ).fetchone()
        if not row:
            raise WorkflowError(f"unknown requirement: {args.id}")
        if row["lifecycle"] != "active":
            raise WorkflowError("only an active requirement may transition")
        if row["stage"] != args.expected_stage or row["owner_generation"] != args.owner_generation:
            raise WorkflowError("stage or owner-generation precondition failed")
        if args.to_stage == "execute":
            if not args.approved_roadmap_sha256:
                raise WorkflowError("execute transition requires the approved roadmap digest")
            approval = connection.execute(
                """
                SELECT roadmap_sha256 FROM approvals
                WHERE requirement_id=? AND revoked_at IS NULL
                """,
                (args.id,),
            ).fetchone()
            if (
                not approval
                or approval[0] != args.approved_roadmap_sha256
                or row["approved_plan_sha256"] != args.approved_roadmap_sha256
            ):
                raise WorkflowError("roadmap approval is missing, revoked, or mismatched")
        if args.to_stage == "closed":
            acceptance = connection.execute(
                """
                SELECT 1 FROM materials
                WHERE requirement_id=? AND kind='acceptance' AND is_current=1
                """,
                (args.id,),
            ).fetchone()
            if not acceptance:
                raise WorkflowError("closure requires committed current acceptance material")
            connection.execute(
                """
                UPDATE requirements
                SET stage='closed',lifecycle='closed',slot=NULL,updated_at=CURRENT_TIMESTAMP
                WHERE id=?
                """,
                (args.id,),
            )
        else:
            connection.execute(
                "UPDATE requirements SET stage=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",
                (args.to_stage, args.id),
            )
        result = requirement_snapshot(connection, args.id)
        finish_operation(connection, args.operation_id, args.id, "transition", payload, result)
        connection.commit()
        return result
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def command_configure(root: Path, args: argparse.Namespace) -> dict[str, Any]:
    db_path, _ = require_initialized(root)
    if not 1 <= args.max_active <= HARD_MAX_ACTIVE:
        raise WorkflowError(f"max-active must be between 1 and {HARD_MAX_ACTIVE}")
    payload = {"max_active": args.max_active}
    connection = connect(db_path)
    try:
        connection.execute("BEGIN IMMEDIATE")
        replay = begin_operation(connection, args.operation_id, None, "configure", payload)
        if replay is not None:
            connection.rollback()
            return replay
        active_count = connection.execute(
            "SELECT count(*) FROM requirements WHERE lifecycle='active'"
        ).fetchone()[0]
        if active_count > args.max_active:
            raise WorkflowError("cannot lower max-active below the current active count")
        connection.execute(
            "UPDATE metadata SET value=? WHERE key='max_active'", (str(args.max_active),)
        )
        result = {"max_active": args.max_active}
        finish_operation(connection, args.operation_id, None, "configure", payload, result)
        connection.commit()
        return result
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def command_snapshot(root: Path, args: argparse.Namespace) -> dict[str, Any]:
    db_path, _ = require_initialized(root)
    connection = connect(db_path)
    try:
        return requirement_snapshot(connection, args.id)
    finally:
        connection.close()


def command_verify(root: Path) -> dict[str, Any]:
    db_path, materials_root = require_initialized(root)
    connection = connect(db_path)
    try:
        quick = connection.execute("PRAGMA quick_check").fetchone()[0]
        if quick != "ok":
            raise WorkflowError(f"quick_check failed: {quick}")
        foreign = connection.execute("PRAGMA foreign_key_check").fetchall()
        if foreign:
            raise WorkflowError(f"foreign_key_check failed: {foreign}")
        max_active = int(
            connection.execute("SELECT value FROM metadata WHERE key='max_active'").fetchone()[0]
        )
        active_count = connection.execute(
            "SELECT count(*) FROM requirements WHERE lifecycle='active'"
        ).fetchone()[0]
        if active_count > max_active or max_active > HARD_MAX_ACTIVE:
            raise WorkflowError("active-slot invariant failed")
        materials = connection.execute(
            "SELECT git_commit,relative_path,sha256 FROM materials WHERE is_current=1"
        ).fetchall()
        for material in materials:
            committed = run_git(
                materials_root,
                "show",
                f"{material['git_commit']}:{material['relative_path']}",
                binary=True,
            )
            if sha256_bytes(committed) != material["sha256"]:
                raise WorkflowError(
                    f"material digest mismatch: {material['relative_path']}"
                )
        return {
            "quick_check": "ok",
            "foreign_key_check": "ok",
            "journal_mode": "delete",
            "active": active_count,
            "max_active": max_active,
            "current_materials": len(materials),
        }
    finally:
        connection.close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--home", help="workflow root; defaults to REQUIREMENT_WORKFLOW_HOME")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init")
    init_parser.add_argument("--materials-root")

    admit = subparsers.add_parser("admit")
    admit.add_argument("--id", required=True)
    admit.add_argument("--title", required=True)
    admit.add_argument("--project-root", required=True)
    admit.add_argument("--owner-label")
    admit.add_argument("--operation-id", required=True)

    claim = subparsers.add_parser("claim")
    claim.add_argument("--id", required=True)
    claim.add_argument("--expected-generation", required=True, type=int)
    claim.add_argument("--owner-label", required=True)
    claim.add_argument("--operation-id", required=True)

    publish = subparsers.add_parser("publish-material")
    publish.add_argument("--id", required=True)
    publish.add_argument("--kind", required=True, choices=MATERIAL_KINDS)
    publish.add_argument("--path", required=True)
    publish.add_argument("--operation-id", required=True)

    approve = subparsers.add_parser("approve-plan")
    approve.add_argument("--id", required=True)
    approve.add_argument("--roadmap-sha256", required=True)
    approve.add_argument("--operation-id", required=True)

    transition = subparsers.add_parser("transition")
    transition.add_argument("--id", required=True)
    transition.add_argument("--expected-stage", required=True, choices=STAGES)
    transition.add_argument("--to-stage", required=True, choices=STAGES)
    transition.add_argument("--owner-generation", required=True, type=int)
    transition.add_argument("--approved-roadmap-sha256")
    transition.add_argument("--operation-id", required=True)

    configure = subparsers.add_parser("configure")
    configure.add_argument("--max-active", required=True, type=int)
    configure.add_argument("--operation-id", required=True)

    snapshot = subparsers.add_parser("snapshot")
    snapshot.add_argument("--id", required=True)

    subparsers.add_parser("verify")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    root = workflow_home(args.home)
    try:
        if args.command == "init":
            result = initialize(root, args.materials_root)
        elif args.command == "admit":
            result = command_admit(root, args)
        elif args.command == "claim":
            result = command_claim(root, args)
        elif args.command == "publish-material":
            result = command_publish_material(root, args)
        elif args.command == "approve-plan":
            result = command_approve_plan(root, args)
        elif args.command == "transition":
            result = command_transition(root, args)
        elif args.command == "configure":
            result = command_configure(root, args)
        elif args.command == "snapshot":
            result = command_snapshot(root, args)
        elif args.command == "verify":
            result = command_verify(root)
        else:
            parser.error(f"unknown command: {args.command}")
            return 2
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
        return 0
    except (WorkflowError, sqlite3.Error, OSError, subprocess.SubprocessError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
