"""Tests for parsing persona files."""

import tempfile
import unittest
from pathlib import Path

from agent_runtime import registry

PERSONA = """---
name: Test Agent
description: "[PIPELINE AGENT] Does a thing."
model: claude-sonnet-4-6
---

You are a test agent.

Second paragraph.
"""

NO_FRONTMATTER = "Just notes, not a persona.\n"

RETIRED = """---
name: Old Agent
description: "[RETIRED] Historical persona."
model: claude-sonnet-4-6
---

You are retired.
"""


class ParseFrontmatterTests(unittest.TestCase):
    def test_splits_fields_and_body(self):
        fields, body = registry.parse_frontmatter(PERSONA)
        self.assertEqual(fields["name"], "Test Agent")
        self.assertEqual(fields["model"], "claude-sonnet-4-6")
        self.assertTrue(body.startswith("You are a test agent."))
        self.assertIn("Second paragraph.", body)

    def test_strips_quotes_from_values(self):
        fields, _ = registry.parse_frontmatter(PERSONA)
        self.assertEqual(fields["description"], "[PIPELINE AGENT] Does a thing.")

    def test_file_without_frontmatter_is_all_body(self):
        fields, body = registry.parse_frontmatter(NO_FRONTMATTER)
        self.assertEqual(fields, {})
        self.assertEqual(body, "Just notes, not a persona.")

    def test_unterminated_frontmatter_does_not_crash(self):
        fields, body = registry.parse_frontmatter("---\nname: Half\nstill going\n")
        self.assertEqual(fields["name"], "Half")
        self.assertIn("still going", body)


class LoadAgentsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.directory = Path(self.temp.name)
        self.addCleanup(self.temp.cleanup)

    def write(self, filename: str, text: str) -> None:
        (self.directory / filename).write_text(text, encoding="utf-8")

    def test_loads_personas_keyed_by_name(self):
        self.write("test-agent.md", PERSONA)
        agents = registry.load_agents(self.directory)
        self.assertEqual(list(agents), ["Test Agent"])
        self.assertEqual(agents["Test Agent"].path.name, "test-agent.md")

    def test_skips_files_without_a_name_field(self):
        self.write("notes.md", NO_FRONTMATTER)
        self.assertEqual(registry.load_agents(self.directory), {})

    def test_detects_retired_personas(self):
        self.write("old.md", RETIRED)
        self.write("test-agent.md", PERSONA)
        agents = registry.load_agents(self.directory)
        self.assertTrue(agents["Old Agent"].is_retired)
        self.assertFalse(agents["Test Agent"].is_retired)


class ProjectRootTests(unittest.TestCase):
    def test_root_contains_claude_directory(self):
        self.assertTrue((registry.project_root() / ".claude").is_dir())

    def test_real_personas_load(self):
        agents = registry.load_agents()
        self.assertIn("Architect Advisor", agents)
        self.assertTrue(agents["Architect Advisor"].system_prompt)


if __name__ == "__main__":
    unittest.main()
