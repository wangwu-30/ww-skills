#!/usr/bin/env python3
"""Unit tests for the software-engineering suite contract."""

from __future__ import annotations

import importlib.util
import os
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("check_suite_contract.py")
SPEC = importlib.util.spec_from_file_location("check_suite_contract", SCRIPT)
assert SPEC and SPEC.loader
CHECKER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECKER)


class SuiteFixture:
    def __init__(self, root: Path) -> None:
        self.root = root
        for name in sorted(CHECKER.REQUIRED_SKILLS):
            self.add_skill(name, implicit=name == CHECKER.SOFTWARE_ROUTER)
        self.set_body(
            CHECKER.SOFTWARE_ROUTER,
            " ".join(
                [
                    *(f"`{name}`" for name in sorted(CHECKER.CLASSIFICATIONS)),
                    *(f"${name}" for name in sorted(CHECKER.DIRECT_LEAVES)),
                    f"${CHECKER.WORKFLOW_ROUTER}",
                    "If the user explicitly names a Skill, that invocation wins.",
                    "Ask once whether to enter $requirement-workflow-router.",
                    "If the user declines, continue as ordinary engineering and do not ask again.",
                    "For `resume`, use workflow only when authoritative evidence proves admission; "
                    "otherwise resume ordinary work directly.",
                    "Resolve the repository root explicitly and parse the status command's JSON.",
                    "Non-fresh statuses may exit 0; never infer freshness from the exit code.",
                    "`invalid` remains invalid even when `changed_paths` is empty.",
                    "`fresh` proves snapshot and artifact closure only; it does not prove semantic "
                    "correctness, tests, architecture, or runtime health.",
                    "Map mode requires an explicit request and may write only `.repo-alive/**`.",
                ]
            ),
        )
        self.set_body(
            CHECKER.WORKFLOW_ROUTER,
            " ".join(f"${name}" for name in sorted(CHECKER.WORKFLOW_STAGES)),
        )
        router = self.root / "skills" / CHECKER.SOFTWARE_ROUTER
        for relative in sorted(
            CHECKER.ALLOWED_ROUTER_RESOURCES - {"SKILL.md", "agents/openai.yaml"}
        ):
            path = router / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("fixture\n", encoding="utf-8")

    def add_skill(self, name: str, *, implicit: bool = False, include_policy: bool = True) -> None:
        directory = self.root / "skills" / name
        (directory / "agents").mkdir(parents=True, exist_ok=True)
        self.set_body(name, "fixture")
        policy = (
            f"policy:\n  allow_implicit_invocation: {'true' if implicit else 'false'}\n"
            if include_policy
            else ""
        )
        (directory / "agents" / "openai.yaml").write_text(
            f'interface:\n  display_name: "{name}"\n{policy}', encoding="utf-8"
        )

    def set_body(self, name: str, body: str) -> None:
        path = self.root / "skills" / name / "SKILL.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            f"---\nname: {name}\ndescription: Fixture for {name}.\n---\n\n{body}\n",
            encoding="utf-8",
        )

    def set_policy(self, name: str, value: str | None) -> None:
        path = self.root / "skills" / name / "agents" / "openai.yaml"
        policy = "" if value is None else f"policy:\n  allow_implicit_invocation: {value}\n"
        path.write_text(f'interface:\n  display_name: "{name}"\n{policy}', encoding="utf-8")

    def replace_router_text(self, old: str, new: str = "") -> None:
        path = self.root / "skills" / CHECKER.SOFTWARE_ROUTER / "SKILL.md"
        text = path.read_text(encoding="utf-8")
        if old not in text:
            raise AssertionError(f"fixture marker not found: {old}")
        path.write_text(text.replace(old, new), encoding="utf-8")


class SuiteContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "arbitrary-checkout"
        self.fixture = SuiteFixture(self.root)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def errors(self) -> list[str]:
        return CHECKER.validate_repo(self.root)

    def assert_error_contains(self, text: str) -> None:
        errors = self.errors()
        self.assertTrue(any(text in error for error in errors), errors)

    def test_valid_suite(self) -> None:
        self.assertEqual(self.errors(), [])

    def test_repo_argument_is_independent_of_current_directory(self) -> None:
        original = Path.cwd()
        elsewhere = Path(self.temp.name) / "elsewhere"
        elsewhere.mkdir()
        try:
            os.chdir(elsewhere)
            self.assertEqual(CHECKER.validate_repo(self.root), [])
        finally:
            os.chdir(original)

    def test_missing_skills_directory_fails_cleanly(self) -> None:
        errors = CHECKER.validate_repo(Path(self.temp.name) / "not-a-repo")
        self.assertEqual(len(errors), 1)
        self.assertIn("no skills directory", errors[0])

    def test_second_implicit_skill_is_rejected(self) -> None:
        self.fixture.set_policy("repo-alive", "true")
        self.assert_error_contains("effective implicit skills")

    def test_omitted_policy_uses_product_default_true(self) -> None:
        self.fixture.set_policy("repo-alive", None)
        self.assert_error_contains("effective implicit skills")

    def test_wrong_sole_implicit_skill_is_rejected(self) -> None:
        self.fixture.set_policy(CHECKER.SOFTWARE_ROUTER, "false")
        self.fixture.set_policy("repo-alive", "true")
        self.assert_error_contains(f"exactly {CHECKER.SOFTWARE_ROUTER}")

    def test_malformed_policy_is_rejected(self) -> None:
        self.fixture.set_policy("repo-alive", "yes")
        self.assert_error_contains("must be true or false")

    def test_missing_required_skill_is_rejected(self) -> None:
        target = self.root / "skills" / "requirement-close" / "SKILL.md"
        target.unlink()
        self.assert_error_contains("missing required skills: requirement-close")

    def test_router_cannot_bypass_workflow_router(self) -> None:
        path = self.root / "skills" / CHECKER.SOFTWARE_ROUTER / "SKILL.md"
        path.write_text(
            path.read_text(encoding="utf-8") + "\n$requirement-frame\n", encoding="utf-8"
        )
        self.assert_error_contains("must reach stages only through")

    def test_leaf_cannot_call_back_to_software_router(self) -> None:
        self.fixture.set_body("repo-alive", f"Call ${CHECKER.SOFTWARE_ROUTER}.")
        self.assert_error_contains("must have no outgoing Skill references")

    def test_leaf_cannot_call_back_to_workflow_router(self) -> None:
        self.fixture.set_body("requirement-frame", f"Call ${CHECKER.WORKFLOW_ROUTER}.")
        self.assert_error_contains("must have no outgoing Skill references")

    def test_workflow_router_cannot_invoke_communication_leaf(self) -> None:
        path = self.root / "skills" / CHECKER.WORKFLOW_ROUTER / "SKILL.md"
        path.write_text(
            path.read_text(encoding="utf-8") + "\n$decision-partner-communication\n",
            encoding="utf-8",
        )
        self.assert_error_contains("unexpected route targets: decision-partner-communication")

    def test_stage_cannot_invoke_communication_leaf(self) -> None:
        self.fixture.set_body("requirement-align", "Use $decision-partner-communication.")
        self.assert_error_contains("must have no outgoing Skill references")

    def test_unknown_skill_reference_is_rejected(self) -> None:
        self.fixture.set_body("repo-alive", "Call $not-installed.")
        self.assert_error_contains("references unknown skills")

    def test_dependency_cycle_is_rejected(self) -> None:
        self.fixture.set_body("repo-alive", "Call $force-thinker.")
        self.fixture.set_body("force-thinker", "Call $repo-alive.")
        self.assert_error_contains("dependency cycle")

    def test_all_classifications_are_required(self) -> None:
        path = self.root / "skills" / CHECKER.SOFTWARE_ROUTER / "SKILL.md"
        path.write_text(
            path.read_text(encoding="utf-8").replace("`diagnose`", "diagnosis"),
            encoding="utf-8",
        )
        self.assert_error_contains("missing classifications: diagnose")

    def test_explicit_skill_precedence_is_required(self) -> None:
        self.fixture.replace_router_text("that invocation wins", "route it again")
        self.assert_error_contains("missing semantic rule: explicit Skill precedence")

    def test_ask_once_admission_is_required(self) -> None:
        self.fixture.replace_router_text("Ask once", "Ask")
        self.assert_error_contains("missing semantic rule: ask-once workflow admission")

    def test_refusal_must_continue_without_reasking(self) -> None:
        self.fixture.replace_router_text("continue as ordinary engineering and do not ask again", "stop")
        self.assert_error_contains("missing semantic rule: refusal continuation without re-asking")

    def test_resume_requires_authoritative_state_and_direct_fallback(self) -> None:
        self.fixture.replace_router_text("only when authoritative evidence proves admission", "from chat")
        self.assert_error_contains("missing semantic rule: resume without inferred workflow state")

    def test_repo_alive_requires_explicit_repository_root(self) -> None:
        self.fixture.replace_router_text("repository root explicitly", "nearest repository")
        self.assert_error_contains("missing semantic rule: Repo Alive explicit repository root")

    def test_repo_alive_requires_json_status_parsing(self) -> None:
        self.fixture.replace_router_text("parse the status command's JSON", "run status")
        self.assert_error_contains("missing semantic rule: Repo Alive JSON status parsing")

    def test_repo_alive_handles_nonfresh_exit_zero(self) -> None:
        self.fixture.replace_router_text("Non-fresh statuses may exit 0", "Trust exit 0")
        self.assert_error_contains("missing semantic rule: Repo Alive non-fresh exit-zero handling")

    def test_repo_alive_handles_invalid_with_empty_changed_paths(self) -> None:
        self.fixture.replace_router_text("even when `changed_paths` is empty", "only with paths")
        self.assert_error_contains(
            "missing semantic rule: Repo Alive invalid empty changed_paths handling"
        )

    def test_repo_alive_fresh_has_limited_meaning(self) -> None:
        self.fixture.replace_router_text("it does not prove semantic correctness", "it proves correctness")
        self.assert_error_contains("missing semantic rule: Repo Alive fresh limited meaning")

    def test_repo_alive_map_mode_requires_explicit_request_and_bounded_writes(self) -> None:
        self.fixture.replace_router_text("Map mode requires an explicit request", "Map automatically")
        self.assert_error_contains("missing semantic rule: Repo Alive explicit map-mode writes")

    def test_persistent_router_state_is_rejected(self) -> None:
        state = self.root / "skills" / CHECKER.SOFTWARE_ROUTER / "route.json"
        state.write_text("{}\n", encoding="utf-8")
        self.assert_error_contains("persistent state")

    def test_router_cannot_own_workflow_state_tool(self) -> None:
        tool = (
            self.root
            / "skills"
            / CHECKER.SOFTWARE_ROUTER
            / "scripts"
            / "workflow_state.py"
        )
        tool.write_text("# forbidden duplicate\n", encoding="utf-8")
        self.assert_error_contains("must not own workflow_state.py")


if __name__ == "__main__":
    unittest.main()
