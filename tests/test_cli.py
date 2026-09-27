"""Tests for the command line surface Claude Code reads."""

import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from agent_runtime import cli


def run(*argv: str, runs_dir: Path) -> tuple[int, str]:
    """Invoke the CLI and capture its exit code and stdout."""
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        code = cli.main(["--runs-dir", str(runs_dir), *argv])
    return code, buffer.getvalue()


def field(output: str, key: str) -> str:
    """The value of the first `KEY=value` line with this key."""
    for line in output.splitlines():
        name, separator, value = line.partition("=")
        if separator and name.strip() == key:
            return value
    raise AssertionError(f"{key} not found in:\n{output}")


class CliTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.runs_dir = Path(self.temp.name)
        self.addCleanup(self.temp.cleanup)

    def start_audit(self) -> str:
        code, output = run("start", "audit", "harden env_guard.py", runs_dir=self.runs_dir)
        self.assertEqual(code, 0)
        return output

    def test_start_reports_the_first_agent_and_a_prompt(self):
        output = self.start_audit()
        self.assertEqual(field(output, "STATUS"), "RUNNING")
        self.assertEqual(field(output, "NEXT_AGENTS"), "Architect Advisor")
        self.assertEqual(field(output, "PASS"), "1/3")
        self.assertIn("PROMPT<<<", output)
        self.assertIn("harden env_guard.py", output)

    def test_record_advances_to_the_next_agent(self):
        self.start_audit()
        code, output = run(
            "record", "--agent", "Architect Advisor", "--text", "the plan",
            runs_dir=self.runs_dir,
        )
        self.assertEqual(code, 0)
        self.assertEqual(field(output, "NEXT_AGENTS"), "Bug Fixer")

    def test_gate_is_reported_and_cleared_by_approve(self):
        self.start_audit()
        run("record", "--agent", "Architect Advisor", "--text", "plan", runs_dir=self.runs_dir)
        _, output = run("record", "--agent", "Bug Fixer", "--text", "diff", runs_dir=self.runs_dir)
        self.assertEqual(field(output, "GATE"), "approval_required")
        self.assertIn("STOP", field(output, "NOTE"))

        _, output = run("approve", runs_dir=self.runs_dir)
        self.assertEqual(field(output, "STATUS"), "RUNNING")

    def test_wrong_agent_is_an_error_not_a_silent_skip(self):
        self.start_audit()
        code, output = run(
            "record", "--agent", "Code Mentor", "--text", "hi", runs_dir=self.runs_dir
        )
        self.assertEqual(code, 2)
        self.assertIn("expects Architect Advisor", field(output, "ERROR"))

    def test_failed_audit_puts_findings_into_the_next_prompt(self):
        self.start_audit()
        run("record", "--agent", "Architect Advisor", "--text", "plan", runs_dir=self.runs_dir)
        run("record", "--agent", "Bug Fixer", "--text", "diff", runs_dir=self.runs_dir)
        run("approve", runs_dir=self.runs_dir)
        run("record", "--agent", "Bug Fixer", "--text", "applied", runs_dir=self.runs_dir)
        _, output = run(
            "record",
            "--agent",
            "PA Right-Hand Audit & Testing",
            "--text",
            "- [x] force-add still possible",
            runs_dir=self.runs_dir,
        )
        self.assertEqual(field(output, "PASS"), "2/3")
        self.assertEqual(field(output, "NEXT_AGENTS"), "Architect Advisor")
        self.assertIn("force-add still possible", output)
        self.assertIn("This is pass 2", output)

    def test_record_reads_an_output_file(self):
        self.start_audit()
        report = self.runs_dir / "report.md"
        report.write_text("plan from a file", encoding="utf-8")
        _, output = run(
            "record", "--agent", "Architect Advisor", "--output-file", str(report),
            runs_dir=self.runs_dir,
        )
        self.assertEqual(field(output, "NEXT_AGENTS"), "Bug Fixer")

    def test_status_without_a_run_is_a_clean_error(self):
        code, output = run("status", runs_dir=self.runs_dir)
        self.assertEqual(code, 2)
        self.assertIn("no current run", field(output, "ERROR"))

    def test_transcript_records_each_step(self):
        self.start_audit()
        run("record", "--agent", "Architect Advisor", "--text", "plan", runs_dir=self.runs_dir)
        ledgers = list(self.runs_dir.glob("*/transcript.jsonl"))
        self.assertEqual(len(ledgers), 1)
        lines = ledgers[0].read_text(encoding="utf-8").strip().splitlines()
        self.assertEqual(len(lines), 2)  # start + one record
        self.assertIn("Architect Advisor", lines[1])

    def test_list_shows_both_chains(self):
        code, output = run("list", runs_dir=self.runs_dir)
        self.assertEqual(code, 0)
        self.assertIn("CHAIN=audit", output)
        self.assertIn("CHAIN=pipeline", output)

    def test_validate_passes_against_the_real_personas(self):
        code, output = run("validate", runs_dir=self.runs_dir)
        self.assertEqual(code, 0, output)
        self.assertEqual(field(output, "RESULT"), "OK")


if __name__ == "__main__":
    unittest.main()
