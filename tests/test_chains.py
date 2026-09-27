"""Tests that the declared chains match the personas actually on disk.

This is the check that would have caught a chain pointing at an agent that was
renamed or removed — the failure mode a prompt-only chain finds at runtime.
"""

import unittest

from agent_runtime import chains, registry


class ChainDataTests(unittest.TestCase):
    def test_unknown_chain_names_the_valid_ones(self):
        with self.assertRaises(KeyError) as caught:
            chains.get("nope")
        self.assertIn("audit", str(caught.exception))
        self.assertIn("pipeline", str(caught.exception))

    def test_agent_names_dedupes_and_keeps_first_use_order(self):
        # Bug Fixer appears twice in the audit chain; it should be listed once.
        self.assertEqual(
            chains.agent_names(chains.AUDIT),
            ["Architect Advisor", "Bug Fixer", "PA Right-Hand Audit & Testing"],
        )

    def test_audit_chain_has_one_gate_and_one_verdict(self):
        gates = [step for step in chains.AUDIT.steps if step.gate]
        verdicts = [step for step in chains.AUDIT.steps if step.verdict]
        self.assertEqual(len(gates), 1)
        self.assertEqual(len(verdicts), 1)
        self.assertIsNone(chains.AUDIT.final_gate)

    def test_pipeline_gates_the_disk_write(self):
        self.assertIsNotNone(chains.PIPELINE.final_gate)

    def test_pipeline_runs_the_two_coders_together(self):
        coder_step = chains.PIPELINE.steps[1]
        self.assertEqual(len(coder_step.agents), 2)

    def test_every_verdict_step_uses_a_known_mode(self):
        for chain in chains.CHAINS.values():
            for step in chain.steps:
                if step.verdict:
                    self.assertIn(step.verdict, {"audit", "json"}, chain.name)

    def test_every_chain_ends_with_a_verdict_step(self):
        for chain in chains.CHAINS.values():
            self.assertTrue(chain.steps[-1].verdict, f"{chain.name} has no verifier")


class ChainsMatchPersonasTests(unittest.TestCase):
    """Integration: the chains must name agents that really exist."""

    @classmethod
    def setUpClass(cls):
        cls.agents = registry.load_agents()

    def test_every_chain_agent_exists_as_a_persona(self):
        for chain in chains.CHAINS.values():
            for name in chains.agent_names(chain):
                self.assertIn(name, self.agents, f"{chain.name} references {name!r}")

    def test_no_chain_uses_a_retired_persona(self):
        for chain in chains.CHAINS.values():
            for name in chains.agent_names(chain):
                agent = self.agents.get(name)
                if agent is not None:
                    self.assertFalse(agent.is_retired, f"{chain.name} uses retired {name!r}")


if __name__ == "__main__":
    unittest.main()
