"""Tests for the whole-project audit and its HTML report."""

import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from agent_runtime import audit, cli, report

PERSONA = """---
name: {name}
description: "A persona."
model: claude-sonnet-4-6
---

You are {name}.
"""


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class ParseFindingsTests(unittest.TestCase):
    def test_reads_severity_location_and_message(self):
        findings = audit.parse_findings("- [H] hooks/env_guard.py:42 — force-add slips through")
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].severity, "H")
        self.assertEqual(findings[0].location, "hooks/env_guard.py:42")
        self.assertEqual(findings[0].message, "force-add slips through")

    def test_checkbox_findings_become_medium(self):
        findings = audit.parse_findings("- [x] docs drifted from behaviour")
        self.assertEqual(findings[0].severity, "M")

    def test_passed_checkboxes_are_ignored(self):
        self.assertEqual(audit.parse_findings("- [ ] all good here"), [])

    def test_finding_without_a_location_still_parses(self):
        findings = audit.parse_findings("[M] no obvious owner for this file")
        self.assertEqual(findings[0].location, "")
        self.assertEqual(findings[0].message, "no obvious owner for this file")

    def test_plain_prose_is_not_a_finding(self):
        self.assertEqual(audit.parse_findings("I reviewed everything and it looks fine."), [])

    def test_hyphen_separator_is_accepted(self):
        findings = audit.parse_findings("[L] README.md - stale wording")
        self.assertEqual(findings[0].location, "README.md")
        self.assertEqual(findings[0].message, "stale wording")

    def test_byte_order_mark_does_not_swallow_the_first_finding(self):
        """Regression: a BOM once made the first [H] finding vanish silently.

        Files saved on Windows routinely start with one, and a dropped High
        finding is the worst possible thing for this tool to do quietly.
        """
        text = "﻿- [H] hooks/env_guard.py:31 - misses `git add -A`\n- [M] docs.md - stale\n"
        findings = audit.parse_findings(text)
        self.assertEqual(len(findings), 2)
        self.assertEqual(findings[0].severity, "H")

    def test_cli_reads_a_findings_file_that_has_a_bom(self):
        with tempfile.TemporaryDirectory() as directory:
            findings_file = Path(directory) / "findings.md"
            findings_file.write_text(
                "- [H] a.py:1 - broken\n", encoding="utf-8-sig"
            )
            buffer = io.StringIO()
            with contextlib.redirect_stdout(buffer):
                code = cli.main([
                    "audit",
                    "--no-tests",
                    "--findings", str(findings_file),
                    "--html", str(Path(directory) / "report.html"),
                ])
            output = buffer.getvalue()
            self.assertEqual(code, 0)
            self.assertIn("SUBAGENT_FINDINGS=1", output)
            self.assertIn("HIGH=1", output)


class CategoriseTests(unittest.TestCase):
    def test_known_categories(self):
        cases = {
            ".claude/agents/bug-fixer.md": "Agent personas",
            ".claude/skills/diagnose.md": "Skills",
            ".claude/commands/audit-chain.md": "Commands",
            ".claude/hooks/path_guard.py": "Hooks",
            ".claude/settings.json": "Claude config",
            "agent_runtime/state.py": "Runtime",
            "tests/test_state.py": "Tests",
            "my-project/job-auto-apply/app.py": "Subprojects",
            "docs/agent-workflow.md": "Docs",
            "CLAUDE.md": "Root files",
        }
        for path, expected in cases.items():
            self.assertEqual(audit.categorise(path), expected, path)


class FakeProjectTests(unittest.TestCase):
    """The drift checks, run against a project built for the purpose."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.addCleanup(self.temp.cleanup)

    def test_persona_problems_are_reported(self):
        write(self.root / ".claude/agents/good.md", PERSONA.format(name="Good"))
        write(self.root / ".claude/agents/nameless.md", "---\ndescription: no name\n---\n\nBody.")
        write(self.root / ".claude/agents/dupe-a.md", PERSONA.format(name="Twin"))
        write(self.root / ".claude/agents/dupe-b.md", PERSONA.format(name="Twin"))
        write(self.root / ".claude/agents/hollow.md", "---\nname: Hollow\ndescription: x\nmodel: m\n---\n")

        check = audit.check_personas(self.root)
        messages = [finding.message for finding in check.findings]
        self.assertFalse(check.passed)
        self.assertTrue(any("no `name:`" in message for message in messages))
        self.assertTrue(any("duplicate agent name" in message for message in messages))
        self.assertTrue(any("body is empty" in message for message in messages))

    def test_clean_personas_pass(self):
        write(self.root / ".claude/agents/good.md", PERSONA.format(name="Good"))
        check = audit.check_personas(self.root)
        self.assertTrue(check.passed, check.findings)
        self.assertIn("1 personas", check.detail)

    def test_skill_index_drift_both_directions(self):
        write(self.root / ".claude/skills/README.md", "| `listed.md` | x | y |\n| `ghost.md` | x | y |")
        write(self.root / ".claude/skills/listed.md", "# Listed")
        write(self.root / ".claude/skills/orphan.md", "# Orphan")

        check = audit.check_skill_table(self.root)
        messages = [finding.message for finding in check.findings]
        self.assertTrue(any("does not exist" in message for message in messages))
        self.assertTrue(any("not listed in README" in message for message in messages))

    def test_command_index_drift(self):
        write(self.root / "CLAUDE.md", "| `/documented` | does a thing |")
        write(self.root / ".claude/commands/documented.md", "steps")
        write(self.root / ".claude/commands/undocumented.md", "steps")

        check = audit.check_command_table(self.root)
        messages = [finding.message for finding in check.findings]
        self.assertTrue(any("not in the CLAUDE.md table" in message for message in messages))
        self.assertTrue(all("has no command file" not in message for message in messages))

    def test_missing_command_file_is_high(self):
        write(self.root / "CLAUDE.md", "| `/ghost` | never written |")
        (self.root / ".claude/commands").mkdir(parents=True)
        check = audit.check_command_table(self.root)
        self.assertEqual([finding.severity for finding in check.findings], ["H"])

    def test_orphan_hook_script_is_reported(self):
        write(self.root / ".claude/settings.json", '{"hooks": {}}')
        write(self.root / ".claude/hooks/unused.ps1", "# nothing references me")
        check = audit.check_hook_wiring(self.root)
        self.assertFalse(check.passed)
        self.assertIn("never runs", check.findings[0].message)

    def test_settings_naming_a_missing_script_is_high(self):
        write(
            self.root / ".claude/settings.json",
            '{"hooks": {"Stop": [{"hooks": [{"type": "command",'
            ' "command": "python \\"D:/p/.claude/hooks/ghost.py\\""}]}]}}',
        )
        (self.root / ".claude/hooks").mkdir(parents=True)
        check = audit.check_hook_wiring(self.root)
        self.assertEqual([finding.severity for finding in check.findings], ["H"])
        self.assertIn("ghost.py", check.findings[0].message)

    def test_wired_script_passes(self):
        write(
            self.root / ".claude/settings.json",
            '{"hooks": {"Stop": [{"hooks": [{"type": "command",'
            ' "command": ".claude/hooks/notify.ps1"}]}]}}',
        )
        write(self.root / ".claude/hooks/notify.ps1", "# wired")
        self.assertTrue(audit.check_hook_wiring(self.root).passed)

    def test_settings_local_counts_as_wiring(self):
        """A script wired only from the gitignored local file is NOT an orphan.

        Regression for a real mistake: `git grep` cannot see .gitignored files,
        so a hook wired only in settings.local.json looked unreferenced.
        """
        write(self.root / ".claude/settings.json", '{"hooks": {}}')
        write(
            self.root / ".claude/settings.local.json",
            '{"hooks": {"Stop": [{"hooks": [{"type": "command",'
            ' "command": ".claude/hooks/personal.ps1"}]}]}}',
        )
        write(self.root / ".claude/hooks/personal.ps1", "# wired locally only")
        check = audit.check_hook_wiring(self.root)
        self.assertTrue(check.passed, check.findings)
        self.assertIn("2 settings file(s)", check.detail)

    def test_externally_invoked_script_is_not_an_orphan(self):
        """A script launched by an OS protocol handler declares itself."""
        write(self.root / ".claude/settings.json", '{"hooks": {}}')
        write(
            self.root / ".claude/hooks/focus.ps1",
            "# hook-wiring: external - launched by a protocol handler\nexit 0",
        )
        check = audit.check_hook_wiring(self.root)
        self.assertTrue(check.passed, check.findings)
        self.assertIn("1 externally invoked", check.detail)

    def test_non_script_files_in_hooks_are_ignored(self):
        write(self.root / ".claude/settings.json", '{"hooks": {}}')
        write(self.root / ".claude/hooks/README.md", "docs, not a hook")
        self.assertTrue(audit.check_hook_wiring(self.root).passed)

    def test_syntax_errors_are_found(self):
        write(self.root / "broken.py", "def oops(:\n    pass\n")
        write(self.root / "fine.py", "x = 1\n")
        inventory = audit.take_inventory(self.root)
        check = audit.check_python_syntax(self.root, inventory)
        self.assertEqual(len(check.findings), 1)
        self.assertIn("broken.py", check.findings[0].location)

    def test_dead_doc_links_are_found(self):
        write(self.root / "README.md", "[gone](missing.md) and [here](exists.md) and [web](https://x.dev)")
        write(self.root / "exists.md", "# Exists")
        inventory = audit.take_inventory(self.root)
        check = audit.check_doc_links(self.root, inventory)
        self.assertEqual(len(check.findings), 1)
        self.assertIn("missing.md", check.findings[0].message)

    def test_references_are_excluded_unless_asked_for(self):
        write(self.root / "references/vendor/thing.md", "# Vendored")
        write(self.root / "CLAUDE.md", "# Project")

        without = audit.take_inventory(self.root)
        self.assertNotIn("Vendored references", without)

        with_refs = audit.take_inventory(self.root, include_references=True)
        self.assertIn("Vendored references", with_refs)

    def test_always_skipped_directories_stay_out(self):
        write(self.root / "runs/20260101-audit/state.json", "{}")
        write(self.root / "__pycache__/x.pyc", "junk")
        write(self.root / "CLAUDE.md", "# Project")
        inventory = audit.take_inventory(self.root)
        self.assertEqual(audit.files_of(inventory, "Root files"), ["CLAUDE.md"])


class ReportTests(unittest.TestCase):
    def make_result(self, findings=()) -> audit.AuditResult:
        return audit.AuditResult(
            root=Path("D:/example-project"),
            generated_at="2026-09-27T00:00:00+00:00",
            inventory={"Root files": ["CLAUDE.md"]},
            checks=[audit.Check("Demo check", "1 thing", list(findings))],
            tests=audit.TestOutcome(ran=49, ok=True, detail="49 tests passed"),
        )

    def test_report_is_self_contained_html(self):
        html = report.render(self.make_result())
        self.assertTrue(html.startswith("<!doctype html>"))
        self.assertIn("Audit Report", html)
        self.assertIn("49 tests passed", html)
        self.assertNotIn("<script", html)

    def test_clean_audit_says_so(self):
        self.assertIn("No findings", report.render(self.make_result()))

    def test_findings_are_html_escaped(self):
        finding = audit.Finding("H", "demo", "a.py:1", "breaks on <script>alert(1)</script>")
        html = report.render(self.make_result([finding]))
        self.assertIn("&lt;script&gt;", html)
        self.assertNotIn("<script>alert", html)

    def test_severity_counts_reach_the_summary(self):
        result = self.make_result([audit.Finding("H", "demo", "a.py", "bad")])
        self.assertEqual(result.count("H"), 1)
        self.assertIn("high", report.render(result))

    def test_write_creates_the_file(self):
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "nested" / "audit-report.html"
            written = report.write(self.make_result(), destination)
            self.assertTrue(written.exists())
            self.assertIn("Audit Report", written.read_text(encoding="utf-8"))


class RealProjectAuditTests(unittest.TestCase):
    """The audit must run over this repo without crashing.

    Tests are skipped here deliberately: running the suite from inside the
    suite would recurse.
    """

    @classmethod
    def setUpClass(cls):
        cls.result = audit.run_audit(with_tests=False)

    def test_inventory_finds_the_expected_categories(self):
        self.assertIn("Agent personas", self.result.inventory)
        self.assertIn("Runtime", self.result.inventory)
        self.assertGreater(self.result.file_count, 20)

    def test_every_check_ran(self):
        self.assertEqual(len(self.result.checks), 8)
        for check in self.result.checks:
            self.assertTrue(check.detail, check.name)

    def test_report_renders_for_the_real_project(self):
        html = report.render(self.result)
        self.assertIn("Files audited", html)


if __name__ == "__main__":
    unittest.main()
