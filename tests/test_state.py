"""Tests for the chain state machine — the loop caps and gates it enforces."""

import tempfile
import unittest
from pathlib import Path

from agent_runtime import chains, state
from agent_runtime.state import (
    AWAITING_APPROVAL,
    DONE,
    EXHAUSTED,
    REJECTED,
    RUNNING,
    STALLED,
    Run,
    StateError,
)

AUDITOR = "PA Right-Hand Audit & Testing"
CLEAN = "AUDIT CLEAN - no issues found"


class ClassifyTests(unittest.TestCase):
    def test_audit_clean_report_passes(self):
        passed, findings = state.classify("audit", f"- [ ] hooks fine\n{CLEAN}")
        self.assertTrue(passed)
        self.assertEqual(findings, [])

    def test_audit_marks_failed_findings(self):
        passed, findings = state.classify(
            "audit", "- [ ] docs ok\n- [x] env_guard still force-adds\n"
        )
        self.assertFalse(passed)
        self.assertEqual(findings, ["- [x] env_guard still force-adds"])

    def test_json_pass(self):
        passed, findings = state.classify("json", '{"status": "PASS"}')
        self.assertTrue(passed)
        self.assertEqual(findings, [])

    def test_json_fail_collects_feedback_fields(self):
        payload = '{"status": "FAIL", "backend_feedback": "missing models.py"}'
        passed, findings = state.classify("json", payload)
        self.assertFalse(passed)
        self.assertEqual(findings, ["backend_feedback: missing models.py"])

    def test_json_surrounded_by_prose_still_parses(self):
        passed, _ = state.classify("json", 'Here you go:\n{"status": "PASS"}\nDone.')
        self.assertTrue(passed)

    def test_non_json_output_is_a_failure_not_a_crash(self):
        passed, findings = state.classify("json", "looks good to me")
        self.assertFalse(passed)
        self.assertIn("did not return a JSON object", findings[0])

    def test_unknown_mode_is_rejected(self):
        with self.assertRaises(ValueError):
            state.classify("vibes", "whatever")


class AuditChainTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.runs_dir = Path(self.temp.name)
        self.addCleanup(self.temp.cleanup)
        self.chain = chains.AUDIT
        self.run = state.start(self.chain, "harden env_guard.py", self.runs_dir)

    def drive_to_verdict(self) -> None:
        """Walk the chain up to (not including) the audit step."""
        self.run.record(self.chain, "Architect Advisor", "the plan")
        self.run.record(self.chain, "Bug Fixer", "the diff")
        self.run.approve(self.chain)
        self.run.record(self.chain, "Bug Fixer", "applied")

    def test_starts_on_the_first_step(self):
        self.assertEqual(self.run.status, RUNNING)
        self.assertEqual(self.run.pending_agents(self.chain), ["Architect Advisor"])

    def test_gate_pauses_before_the_diff_is_applied(self):
        self.run.record(self.chain, "Architect Advisor", "the plan")
        self.run.record(self.chain, "Bug Fixer", "the diff")
        self.assertEqual(self.run.status, AWAITING_APPROVAL)
        self.assertEqual(self.run.gate_reason, "Apply the proposed diff to the working tree")
        self.assertFalse(self.run.gate_is_final)

    def test_clean_audit_finishes_the_run(self):
        self.drive_to_verdict()
        self.run.record(self.chain, AUDITOR, CLEAN)
        self.assertEqual(self.run.status, DONE)
        self.assertEqual(self.run.findings, [])

    def test_failed_audit_restarts_the_chain_on_the_next_pass(self):
        self.drive_to_verdict()
        self.run.record(self.chain, AUDITOR, "- [x] still broken")
        self.assertEqual(self.run.status, RUNNING)
        self.assertEqual(self.run.pass_number, 2)
        self.assertEqual(self.run.step_index, 0)
        self.assertEqual(self.run.findings, ["- [x] still broken"])

    def test_identical_findings_twice_stalls_instead_of_looping(self):
        self.drive_to_verdict()
        self.run.record(self.chain, AUDITOR, "- [x] same problem")
        self.drive_to_verdict()
        self.run.record(self.chain, AUDITOR, "- [x] same problem")
        self.assertEqual(self.run.status, STALLED)
        self.assertEqual(self.run.pass_number, 2)

    def test_pass_cap_stops_a_run_that_keeps_failing_differently(self):
        for attempt in range(1, 4):
            self.drive_to_verdict()
            self.run.record(self.chain, AUDITOR, f"- [x] problem {attempt}")
        self.assertEqual(self.run.status, EXHAUSTED)
        self.assertEqual(self.run.pass_number, self.chain.max_passes)

    def test_rejecting_the_gate_ends_the_run(self):
        self.run.record(self.chain, "Architect Advisor", "the plan")
        self.run.record(self.chain, "Bug Fixer", "the diff")
        self.run.reject()
        self.assertEqual(self.run.status, REJECTED)

    def test_wrong_agent_is_refused(self):
        with self.assertRaises(StateError) as caught:
            self.run.record(self.chain, "Code Mentor", "unsolicited advice")
        self.assertIn("expects Architect Advisor", str(caught.exception))

    def test_same_agent_cannot_report_twice_for_one_step(self):
        self.run.record(self.chain, "Architect Advisor", "the plan")
        self.run.record(self.chain, "Bug Fixer", "the diff")
        self.run.approve(self.chain)
        self.run.record(self.chain, "Bug Fixer", "applied")
        # Step 4 belongs to the auditor, so Bug Fixer is now out of turn.
        with self.assertRaises(StateError):
            self.run.record(self.chain, "Bug Fixer", "again")

    def test_recording_after_a_terminal_status_is_refused(self):
        self.drive_to_verdict()
        self.run.record(self.chain, AUDITOR, CLEAN)
        with self.assertRaises(StateError):
            self.run.record(self.chain, AUDITOR, CLEAN)

    def test_approving_when_no_gate_is_open_is_refused(self):
        with self.assertRaises(StateError):
            self.run.approve(self.chain)

    def test_state_survives_a_save_and_load(self):
        self.run.record(self.chain, "Architect Advisor", "the plan")
        self.run.save(self.runs_dir)
        reloaded = Run.load(self.runs_dir)
        self.assertEqual(reloaded.run_id, self.run.run_id)
        self.assertEqual(reloaded.step_index, 1)
        self.assertEqual(reloaded.task, "harden env_guard.py")


class PipelineChainTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.runs_dir = Path(self.temp.name)
        self.addCleanup(self.temp.cleanup)
        self.chain = chains.PIPELINE
        self.run = state.start(self.chain, "todo app", self.runs_dir)

    def test_parallel_step_waits_for_both_coders(self):
        self.run.record(self.chain, "Pipeline Planner", '{"project_name": "todo"}')
        self.assertEqual(self.run.step_index, 1)

        self.run.record(self.chain, "Pipeline Frontend Coder", "=== FILE === app.jsx")
        self.assertEqual(self.run.step_index, 1, "should still be on the coder step")
        self.assertEqual(self.run.pending_agents(self.chain), ["Pipeline Backend Coder"])

        self.run.record(self.chain, "Pipeline Backend Coder", "=== FILE === main.py")
        self.assertEqual(self.run.step_index, 2)
        self.assertEqual(self.run.pending_agents(self.chain), ["Pipeline Reviewer"])

    def test_passing_review_opens_the_write_gate_rather_than_finishing(self):
        self.run.record(self.chain, "Pipeline Planner", '{"project_name": "todo"}')
        self.run.record(self.chain, "Pipeline Frontend Coder", "files")
        self.run.record(self.chain, "Pipeline Backend Coder", "files")
        self.run.record(self.chain, "Pipeline Reviewer", '{"status": "PASS"}')

        self.assertEqual(self.run.status, AWAITING_APPROVAL)
        self.assertTrue(self.run.gate_is_final)
        self.assertEqual(self.run.gate_reason, "Write the generated files to disk")

        self.run.approve(self.chain)
        self.assertEqual(self.run.status, DONE)


if __name__ == "__main__":
    unittest.main()
