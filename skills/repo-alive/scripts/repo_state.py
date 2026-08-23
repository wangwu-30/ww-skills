#!/usr/bin/env python3
"""Create and validate content-sensitive repo-alive knowledge fingerprints."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any

SCHEMA_VERSION = 1
FINGERPRINT = "fingerprint.json"
REQUIRED_KNOWLEDGE = ("overview.md", "routes.md")
# Only version-control metadata is excluded from non-Git content snapshots.  Build,
# dependency, cache, and virtual-environment directory names are user content here.
VCS_METADATA_DIRS = {".git", ".hg", ".svn"}


def _run_git(repo: Path, *args: str) -> subprocess.CompletedProcess[bytes] | None:
    try:
        return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, check=False)
    except OSError:
        return None


def _git_root(repo: Path) -> Path | None:
    result = _run_git(repo, "rev-parse", "--show-toplevel")
    if result is None or result.returncode:
        return None
    return Path(result.stdout.decode("utf-8", "surrogateescape").strip()).resolve()


def _git_head(root: Path) -> str | None:
    result = _run_git(root, "rev-parse", "--verify", "HEAD")
    return None if result is None or result.returncode else result.stdout.decode("ascii", "replace").strip()


def _inside(path: Path, root: Path) -> str | None:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return None


def _excluded(name: str, knowledge_rel: str | None) -> bool:
    return bool(knowledge_rel and (name == knowledge_rel or name.startswith(knowledge_rel + "/")))


def _digest_records(records: list[tuple[str, bytes]]) -> str:
    digest = hashlib.sha256()
    for name, value in sorted(records):
        digest.update(name.encode("utf-8", "surrogateescape")); digest.update(b"\0")
        digest.update(value); digest.update(b"\0")
    return digest.hexdigest()


def _git_index_digest(root: Path, knowledge_rel: str | None) -> str:
    result = _run_git(root, "ls-files", "--stage", "-z")
    if result is None or result.returncode:
        raise ValueError("unable to read Git index")
    records: list[tuple[str, bytes]] = []
    for entry in result.stdout.split(b"\0"):
        if not entry:
            continue
        metadata, raw_name = entry.split(b"\t", 1)
        name = raw_name.decode("utf-8", "surrogateescape")
        if not _excluded(name, knowledge_rel):
            # mode, object id, and stage are all included exactly as Git reports them.
            records.append((name, b"I\0" + metadata))
    return _digest_records(records)


def _worktree_record(root: Path, name: str) -> bytes:
    path = root / name
    try:
        stat = path.lstat()
    except FileNotFoundError:
        return b"MISSING"
    mode = format(stat.st_mode & 0o7777, "o").encode()
    if path.is_symlink():
        return b"L\0" + mode + b"\0" + os.readlink(path).encode("utf-8", "surrogateescape")
    if not path.is_file():
        return b"OTHER\0" + mode
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return b"F\0" + mode + b"\0" + digest.digest()


def _git_worktree_digest(root: Path, knowledge_rel: str | None) -> str:
    # cached gives all tracked paths; --others + --exclude-standard adds only unignored files.
    result = _run_git(root, "ls-files", "-z", "--cached", "--others", "--exclude-standard")
    if result is None or result.returncode:
        raise ValueError("unable to enumerate Git worktree")
    names = {part.decode("utf-8", "surrogateescape") for part in result.stdout.split(b"\0") if part}
    return _digest_records([(name, _worktree_record(root, name)) for name in names if not _excluded(name, knowledge_rel)])


def _filesystem_digest(root: Path, knowledge_dir: Path) -> str:
    knowledge_rel = _inside(knowledge_dir, root)
    records: list[tuple[str, bytes]] = []
    for current, dirs, files in os.walk(root, topdown=True, followlinks=False):
        current_path = Path(current); rel_current = current_path.relative_to(root)
        descend: list[str] = []
        for dirname in sorted(dirs):
            name = (rel_current / dirname).as_posix()
            path = root / name
            if dirname in VCS_METADATA_DIRS or _excluded(name, knowledge_rel):
                continue
            if path.is_symlink():
                records.append((name, _worktree_record(root, name)))
            else:
                descend.append(dirname)
        dirs[:] = descend
        for filename in sorted(files):
            name = (rel_current / filename).as_posix()
            if not _excluded(name, knowledge_rel):
                records.append((name, _worktree_record(root, name)))
    return _digest_records(records)


def source_snapshot(repo: Path, knowledge_dir: Path) -> dict[str, Any]:
    root = _git_root(repo)
    if root is None:
        return {"kind": "filesystem", "content_digest": _filesystem_digest(repo, knowledge_dir)}
    knowledge_rel = _inside(knowledge_dir, root)
    snapshot: dict[str, Any] = {"kind": "git", "index_digest": _git_index_digest(root, knowledge_rel), "worktree_digest": _git_worktree_digest(root, knowledge_rel)}
    head = _git_head(root)
    if head is not None:
        snapshot["git_head"] = head
    return snapshot


def _git_status_paths(repo: Path, knowledge_dir: Path) -> list[str]:
    root = _git_root(repo)
    if root is None: return []
    result = _run_git(root, "status", "--porcelain=v1", "-z", "--untracked-files=all")
    if result is None or result.returncode: return []
    excluded = _inside(knowledge_dir, root); paths: set[str] = set(); fields = result.stdout.split(b"\0"); index = 0
    while index < len(fields):
        item = fields[index]; index += 1
        if not item: continue
        candidates = [item[3:].decode("utf-8", "surrogateescape")]
        if (item[:1] in (b"R", b"C") or item[1:2] in (b"R", b"C")) and index < len(fields):
            candidates.append(fields[index].decode("utf-8", "surrogateescape")); index += 1
        paths.update(name for name in candidates if not _excluded(name, excluded))
    return sorted(paths)


def _head_changed_paths(repo: Path, old: str, new: str, knowledge_dir: Path) -> list[str]:
    result = _run_git(repo, "diff", "--name-only", "-z", old, new, "--")
    root = _git_root(repo)
    if result is None or result.returncode or root is None: return []
    excluded = _inside(knowledge_dir, root)
    names = (part.decode("utf-8", "surrogateescape") for part in result.stdout.split(b"\0") if part)
    return sorted({name for name in names if not _excluded(name, excluded)})


def _safe_manifest_path(value: object) -> str | None:
    if not isinstance(value, str) or not value or "\0" in value: return None
    path = Path(value)
    if path.is_absolute() or ".." in path.parts: return None
    normalized = path.as_posix()
    return normalized if normalized not in (".", FINGERPRINT) else None


def _file_hash(path: Path) -> str:
    if not path.is_file() or path.is_symlink(): raise ValueError("not a regular file")
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""): digest.update(chunk)
    return digest.hexdigest()


def _artifact_manifest(knowledge_dir: Path) -> dict[str, str]:
    manifest: dict[str, str] = {}
    for path in sorted(knowledge_dir.rglob("*")):
        if path == knowledge_dir / FINGERPRINT: continue
        if path.is_symlink(): raise ValueError("knowledge artifacts must not be symlinks")
        if path.is_file(): manifest[path.relative_to(knowledge_dir).as_posix()] = _file_hash(path)
    return manifest


def _valid_snapshot(snapshot: object) -> bool:
    if not isinstance(snapshot, dict): return False
    kind = snapshot.get("kind")
    if kind == "filesystem": return set(snapshot) == {"kind", "content_digest"} and _valid_hash(snapshot.get("content_digest"))
    if kind == "git":
        allowed = {"kind", "git_head", "index_digest", "worktree_digest"}
        return set(snapshot).issubset(allowed) and {"kind", "index_digest", "worktree_digest"}.issubset(snapshot) and all(_valid_hash(snapshot[k]) for k in ("index_digest", "worktree_digest")) and ("git_head" not in snapshot or isinstance(snapshot["git_head"], str))
    return False


def _valid_hash(value: object) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(char in "0123456789abcdef" for char in value)


def _read_and_validate_fingerprint(knowledge_dir: Path) -> tuple[dict[str, Any] | None, str | None]:
    path = knowledge_dir / FINGERPRINT
    if not path.exists(): return None, "fingerprint is missing"
    if path.is_symlink() or not path.is_file(): return None, "fingerprint is not a regular file"
    try: data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError): return None, "fingerprint is malformed"
    if not isinstance(data, dict) or data.get("schema_version") != SCHEMA_VERSION or not _valid_snapshot(data.get("source_snapshot")) or not isinstance(data.get("artifact_manifest"), dict): return None, "fingerprint is malformed"
    manifest = data["artifact_manifest"]
    if not all(name in manifest for name in REQUIRED_KNOWLEDGE): return None, "fingerprint is missing required knowledge artifacts"
    for rel, expected in manifest.items():
        if _safe_manifest_path(rel) is None or not _valid_hash(expected): return None, "fingerprint contains an unsafe artifact path"
    try: actual = _artifact_manifest(knowledge_dir)
    except (OSError, ValueError): return None, "knowledge artifact is missing or unsafe"
    if set(actual) != set(manifest): return None, "knowledge artifact set differs from fingerprint"
    for rel, expected in manifest.items():
        safe = _safe_manifest_path(rel)
        if actual.get(safe) != expected: return None, "knowledge artifact hash drift detected"
    return data, None


def status(repo: Path, knowledge_dir: Path, force: bool = False) -> dict[str, Any]:
    current = source_snapshot(repo, knowledge_dir); data, error = _read_and_validate_fingerprint(knowledge_dir)
    if force: return {"state": "forced", "reason": "freshness check was forced", "source_snapshot": current, "changed_paths": []}
    if data is None: return {"state": "missing" if error == "fingerprint is missing" else "invalid", "reason": error, "source_snapshot": current, "changed_paths": []}
    stored = data["source_snapshot"]
    if stored == current: return {"state": "fresh", "reason": "source and knowledge artifacts match the fingerprint", "source_snapshot": current, "changed_paths": []}
    changed = _git_status_paths(repo, knowledge_dir); old = stored.get("git_head"); new = current.get("git_head")
    if isinstance(old, str) and isinstance(new, str) and old != new: changed = sorted(set(changed).union(_head_changed_paths(repo, old, new, knowledge_dir)))
    return {"state": "stale", "reason": "source snapshot changed since knowledge was stamped", "source_snapshot": current, "changed_paths": changed}


def stamp(repo: Path, knowledge_dir: Path) -> dict[str, Any]:
    missing = [name for name in REQUIRED_KNOWLEDGE if not (knowledge_dir / name).is_file() or (knowledge_dir / name).is_symlink()]
    if missing: return {"state": "invalid", "reason": "required knowledge files are missing: " + ", ".join(missing)}
    try: snapshot, manifest = source_snapshot(repo, knowledge_dir), _artifact_manifest(knowledge_dir)
    except (OSError, ValueError) as error: return {"state": "invalid", "reason": str(error)}
    payload: dict[str, Any] = {"schema_version": SCHEMA_VERSION, "git_head": snapshot.get("git_head", "NO_GIT"), "source_snapshot": snapshot, "artifact_manifest": manifest}
    target = knowledge_dir / FINGERPRINT; temp_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=knowledge_dir, prefix=".fingerprint.", delete=False) as handle:
            temp_name = handle.name; json.dump(payload, handle, sort_keys=True, separators=(",", ":")); handle.write("\n"); handle.flush(); os.fsync(handle.fileno())
        os.replace(temp_name, target); temp_name = None
    except OSError as error:
        return {"state": "invalid", "reason": "unable to write fingerprint: " + str(error)}
    finally:
        if temp_name:
            try: Path(temp_name).unlink(missing_ok=True)
            except OSError: pass
    return {"state": "fresh", "reason": "fingerprint written", "source_snapshot": snapshot, "changed_paths": []}


def _paths(repo_arg: Path, knowledge_arg: str) -> tuple[Path | None, Path | None, str | None]:
    repo = repo_arg.absolute()
    if not repo.is_dir(): return None, None, "repository path is missing or not a directory"
    root = _git_root(repo) or repo.resolve()
    raw_knowledge = Path(knowledge_arg) if Path(knowledge_arg).is_absolute() else root / knowledge_arg
    if raw_knowledge.is_symlink(): return None, None, "knowledge directory must not be a symlink"
    knowledge = raw_knowledge.resolve()
    if _inside(knowledge, root) is None: return None, None, "knowledge directory must be inside the repository root"
    if knowledge == root: return None, None, "knowledge directory must not be the repository root"
    if knowledge.exists() and not knowledge.is_dir(): return None, None, "knowledge path is not a directory"
    return root, knowledge, None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__); sub = parser.add_subparsers(dest="command", required=True)
    for name in ("status", "stamp", "verify"):
        command = sub.add_parser(name); command.add_argument("--repo", type=Path, default=Path.cwd()); command.add_argument("--knowledge-dir", default=".repo-alive")
        if name == "status": command.add_argument("--force", action="store_true")
    args = parser.parse_args(argv); repo, knowledge, error = _paths(args.repo, args.knowledge_dir)
    if error: result, code = {"state": "invalid", "reason": error, "changed_paths": []}, (0 if args.command == "status" else 1)
    else:
        try:
            if args.command == "stamp": result = stamp(repo, knowledge); code = 0 if result["state"] == "fresh" else 1
            else: result = status(repo, knowledge, getattr(args, "force", False)); code = 0 if args.command == "status" or result["state"] == "fresh" else 1
        except (OSError, ValueError) as exception:
            result, code = {"state": "invalid", "reason": "repository state operation failed: " + str(exception), "changed_paths": []}, (0 if args.command == "status" else 1)
    print(json.dumps(result, sort_keys=True, separators=(",", ":"))); return code


if __name__ == "__main__": raise SystemExit(main())
