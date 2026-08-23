#!/usr/bin/env python3
"""Validate the ww-skills routing and invocation contract without dependencies."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SOFTWARE_ROUTER = "software-engineering-router"
WORKFLOW_ROUTER = "requirement-workflow-router"
DIRECT_LEAVES = {
    "decision-partner-communication",
    "force-thinker",
    "repo-alive",
}
WORKFLOW_STAGES = {
    "requirement-align",
    "requirement-close",
    "requirement-execute",
    "requirement-frame",
    "requirement-plan",
    "requirement-research",
}
REQUIRED_SKILLS = {SOFTWARE_ROUTER, WORKFLOW_ROUTER} | DIRECT_LEAVES | WORKFLOW_STAGES
SKILL_REF_RE = re.compile(r"\$([a-z0-9][a-z0-9-]*)")
POLICY_RE = re.compile(
    r"^\s*allow_implicit_invocation:\s*(true|false)\s*(?:#.*)?$", re.MULTILINE
)
CLASSIFICATIONS = {
    "question",
    "understand",
    "diagnose",
    "review",
    "design",
    "small_fix",
    "nontrivial_requirement",
    "resume",
    "status",
}
ALLOWED_ROUTER_RESOURCES = {
    "SKILL.md",
    "agents/openai.yaml",
    "references/routing-contract.md",
    "scripts/check_suite_contract.py",
    "scripts/test_suite_contract.py",
}
ROUTER_SEMANTIC_RULES = {
    "explicit Skill precedence": (
        r"explicitly\s+names?\s+a\s+skill.{0,100}invocation\s+wins?",
    ),
    "ask-once workflow admission": (
        r"ask\s+once.{0,160}requirement-workflow-router",
    ),
    "refusal continuation without re-asking": (
        r"declines?.{0,160}continue.{0,180}do\s+not\s+ask\s+again",
    ),
    "resume without inferred workflow state": (
        r"for\s+`resume`.{0,160}only\s+when.{0,200}(?:proves?|authoritative)",
        r"otherwise.{0,160}resume.{0,160}directly",
    ),
    "Repo Alive explicit repository root": (
        r"repository\s+root\s+explicitly",
    ),
    "Repo Alive JSON status parsing": (
        r"parse\s+the\s+status\s+command's\s+json",
    ),
    "Repo Alive non-fresh exit-zero handling": (
        r"non-fresh\s+statuses\s+may\s+exit\s+0",
        r"never\s+infer\s+freshness\s+from\s+the\s+exit\s+code",
    ),
    "Repo Alive invalid empty changed_paths handling": (
        r"`invalid`.{0,120}`changed_paths`\s+is\s+empty",
    ),
    "Repo Alive fresh limited meaning": (
        r"`fresh`\s+proves\s+snapshot\s+and\s+artifact\s+closure\s+only",
        r"does\s+not\s+prove\s+semantic\s+correctness",
        r"tests.{0,80}runtime\s+health",
    ),
    "Repo Alive explicit map-mode writes": (
        r"map\s+mode\s+requires\s+an\s+explicit\s+request",
        r"may\s+write\s+only.{0,40}\.repo-alive/\*\*",
    ),
}


def _frontmatter_and_body(path: Path) -> tuple[dict[str, str], str, list[str]]:
    errors: list[str] = []
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return {}, "", [f"cannot read {path}: {exc}"]
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text, [f"{path}: missing opening frontmatter delimiter"]
    try:
        end = next(index for index in range(1, len(lines)) if lines[index].strip() == "---")
    except StopIteration:
        return {}, text, [f"{path}: missing closing frontmatter delimiter"]

    metadata: dict[str, str] = {}
    for line in lines[1:end]:
        if not line.strip() or line[:1].isspace():
            continue
        match = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if not match:
            errors.append(f"{path}: malformed top-level frontmatter line: {line!r}")
            continue
        metadata[match.group(1)] = match.group(2).strip().strip("'\"")
    return metadata, "\n".join(lines[end + 1 :]), errors


def _implicit_policy(path: Path) -> tuple[bool | None, list[str]]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return None, [f"cannot read {path}: {exc}"]
    matches = POLICY_RE.findall(text)
    if len(matches) > 1:
        return None, [f"{path}: allow_implicit_invocation appears more than once"]
    malformed = re.search(r"^\s*allow_implicit_invocation:\s*([^#\s]+)", text, re.MULTILINE)
    if malformed and malformed.group(1) not in {"true", "false"}:
        return None, [f"{path}: allow_implicit_invocation must be true or false"]
    # Product metadata defaults this policy to true when omitted.
    return (matches[0] == "true") if matches else True, []


def _find_cycle(graph: dict[str, set[str]]) -> list[str] | None:
    visiting: set[str] = set()
    visited: set[str] = set()
    stack: list[str] = []

    def visit(node: str) -> list[str] | None:
        if node in visiting:
            start = stack.index(node)
            return stack[start:] + [node]
        if node in visited:
            return None
        visiting.add(node)
        stack.append(node)
        for target in sorted(graph.get(node, set())):
            cycle = visit(target)
            if cycle:
                return cycle
        stack.pop()
        visiting.remove(node)
        visited.add(node)
        return None

    for node in sorted(graph):
        cycle = visit(node)
        if cycle:
            return cycle
    return None


def validate_repo(repo: Path) -> list[str]:
    repo = repo.expanduser().resolve()
    skills_dir = repo / "skills"
    if not skills_dir.is_dir():
        return [f"repository has no skills directory: {skills_dir}"]

    skill_dirs = {
        path.name: path
        for path in skills_dir.iterdir()
        if path.is_dir() and (path / "SKILL.md").is_file()
    }
    errors: list[str] = []
    missing = sorted(REQUIRED_SKILLS - set(skill_dirs))
    if missing:
        errors.append(f"missing required skills: {', '.join(missing)}")

    graph: dict[str, set[str]] = {}
    implicit: list[str] = []
    bodies: dict[str, str] = {}
    for name, directory in sorted(skill_dirs.items()):
        metadata, body, frontmatter_errors = _frontmatter_and_body(directory / "SKILL.md")
        errors.extend(frontmatter_errors)
        bodies[name] = body
        if metadata.get("name") != name:
            errors.append(
                f"{directory / 'SKILL.md'}: name {metadata.get('name')!r} does not match directory"
            )
        refs = set(SKILL_REF_RE.findall(body))
        unknown = sorted(refs - set(skill_dirs))
        if unknown:
            errors.append(f"{name}: references unknown skills: {', '.join(unknown)}")
        graph[name] = refs & set(skill_dirs)

        agent_file = directory / "agents" / "openai.yaml"
        if not agent_file.is_file():
            errors.append(f"{name}: missing agents/openai.yaml")
            continue
        is_implicit, policy_errors = _implicit_policy(agent_file)
        errors.extend(policy_errors)
        if is_implicit:
            implicit.append(name)

    if implicit != [SOFTWARE_ROUTER]:
        rendered = ", ".join(implicit) if implicit else "none"
        errors.append(
            f"exactly {SOFTWARE_ROUTER} must allow implicit invocation; effective implicit skills: {rendered}"
        )

    router_targets = graph.get(SOFTWARE_ROUTER, set())
    required_router_targets = DIRECT_LEAVES | {WORKFLOW_ROUTER}
    missing_targets = sorted(required_router_targets - router_targets)
    if missing_targets:
        errors.append(f"{SOFTWARE_ROUTER}: missing route targets: {', '.join(missing_targets)}")
    forbidden_router_targets = sorted(router_targets & WORKFLOW_STAGES)
    if forbidden_router_targets:
        errors.append(
            f"{SOFTWARE_ROUTER}: must reach stages only through {WORKFLOW_ROUTER}: "
            + ", ".join(forbidden_router_targets)
        )
    unexpected_router_targets = sorted(router_targets - required_router_targets)
    if unexpected_router_targets:
        errors.append(
            f"{SOFTWARE_ROUTER}: unexpected direct route targets: "
            + ", ".join(unexpected_router_targets)
        )

    workflow_targets = graph.get(WORKFLOW_ROUTER, set())
    missing_stages = sorted(WORKFLOW_STAGES - workflow_targets)
    if missing_stages:
        errors.append(f"{WORKFLOW_ROUTER}: missing stage targets: {', '.join(missing_stages)}")
    unexpected_workflow_targets = sorted(workflow_targets - WORKFLOW_STAGES)
    if unexpected_workflow_targets:
        errors.append(
            f"{WORKFLOW_ROUTER}: unexpected route targets: "
            + ", ".join(unexpected_workflow_targets)
        )

    for name, targets in sorted(graph.items()):
        if name not in {SOFTWARE_ROUTER, WORKFLOW_ROUTER} and targets:
            errors.append(
                f"{name}: non-router skills must have no outgoing Skill references: "
                + ", ".join(sorted(targets))
            )

    cycle = _find_cycle(graph)
    if cycle:
        errors.append("skill dependency cycle: " + " -> ".join(cycle))

    router_body = bodies.get(SOFTWARE_ROUTER, "")
    missing_classes = sorted(
        name for name in CLASSIFICATIONS if f"`{name}`" not in router_body
    )
    if missing_classes:
        errors.append(f"{SOFTWARE_ROUTER}: missing classifications: {', '.join(missing_classes)}")
    for rule_name, patterns in ROUTER_SEMANTIC_RULES.items():
        if not all(re.search(pattern, router_body, re.IGNORECASE | re.DOTALL) for pattern in patterns):
            errors.append(f"{SOFTWARE_ROUTER}: missing semantic rule: {rule_name}")

    router_dir = skill_dirs.get(SOFTWARE_ROUTER)
    if router_dir:
        resources = {
            str(path.relative_to(router_dir))
            for path in router_dir.rglob("*")
            if path.is_file() and "__pycache__" not in path.parts
        }
        unexpected_resources = sorted(resources - ALLOWED_ROUTER_RESOURCES)
        if unexpected_resources:
            errors.append(
                f"{SOFTWARE_ROUTER}: unexpected resources or persistent state: "
                + ", ".join(unexpected_resources)
            )
        missing_resources = sorted(ALLOWED_ROUTER_RESOURCES - resources)
        if missing_resources:
            errors.append(
                f"{SOFTWARE_ROUTER}: missing required resources: " + ", ".join(missing_resources)
            )
        forbidden_state = sorted(
            str(path.relative_to(router_dir))
            for path in router_dir.rglob("*")
            if path.is_file() and path.suffix.lower() in {".db", ".json", ".sqlite", ".sqlite3"}
        )
        if forbidden_state:
            errors.append(
                f"{SOFTWARE_ROUTER}: persistent state files are forbidden: "
                + ", ".join(forbidden_state)
            )
        if (router_dir / "scripts" / "workflow_state.py").exists():
            errors.append(f"{SOFTWARE_ROUTER}: must not own workflow_state.py")

    return errors


def default_repo() -> Path:
    return Path(__file__).resolve().parents[3]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=default_repo())
    args = parser.parse_args(argv)
    repo = args.repo.expanduser().resolve()
    errors = validate_repo(repo)
    result = {
        "repo": str(repo),
        "status": "valid" if not errors else "invalid",
        "errors": errors,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
