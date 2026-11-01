"""Tests for tools/sync_plugin.py.

Each test builds a scratch git repo with a .claude/ source and a plugin copy,
commits it as the baseline, then changes one side and checks the status.
"""

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "tools" / "sync_plugin.py"
spec = importlib.util.spec_from_file_location("sync_plugin", SCRIPT)
sync_plugin = importlib.util.module_from_spec(spec)
sys.modules["sync_plugin"] = sync_plugin  # dataclasses look the module up here
spec.loader.exec_module(sync_plugin)

SOURCE = ".claude/agents/a.md"
TARGET = "plugins/data-analysis-and-quality-plugin/agents/a.md"
FULL_PATH = "D:" + "\\my-muti-agentic"


def git(root, *args):
    subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@t", *args],
        cwd=root, capture_output=True, check=True,
    )


class SyncPluginTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        for folder in (".claude/agents", ".claude/commands", ".claude/skills", ".claude/hooks"):
            (self.root / folder).mkdir(parents=True)
        for name in sync_plugin.HOOKS:
            (self.root / ".claude/hooks" / name).write_text("x = 1\n")
            self.put(f"plugins/data-analysis-and-quality-plugin/hooks/{name}", "x = 1\n")
        git(self.root, "init", "-q")

    def tearDown(self):
        self.tmp.cleanup()

    def put(self, relative, text):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(text.encode("utf-8"))

    def commit(self):
        git(self.root, "add", "-A")
        git(self.root, "commit", "-q", "-m", "baseline")

    def status(self, target=TARGET, write=False):
        for entry in sync_plugin.sync(self.root, write=write):
            if entry.target == target:
                return entry.status
        return None

    def test_transform_rules_and_line_endings(self):
        text = f"Project (`{FULL_PATH}`).\r\nSee my-project/x.\r\n"
        self.assertEqual(sync_plugin.transform(text), "Project.\nSee <project-root>/x.\n")

    def test_ok_when_plugin_matches_rules(self):
        self.put(SOURCE, "see my-project/\n")
        self.put(TARGET, "see <project-root>/\n")
        self.commit()
        self.assertEqual(self.status(), "ok")

    def test_custom_when_hand_edited_and_source_unchanged(self):
        self.put(SOURCE, "line\n")
        self.put(TARGET, "line edited for plugin\n")
        self.commit()
        self.assertEqual(self.status(), "custom")

    def test_update_and_write_when_source_changed(self):
        self.put(SOURCE, "v1\n")
        self.put(TARGET, "v1\n")
        self.commit()
        self.put(SOURCE, "v2 my-project/\n")
        self.assertEqual(self.status(), "update")
        self.assertEqual(self.status(write=True), "written")
        self.assertEqual((self.root / TARGET).read_text(), "v2 <project-root>/\n")

    def test_manual_never_overwritten(self):
        self.put(SOURCE, "v1\n")
        self.put(TARGET, "v1 hand edit\n")
        self.commit()
        self.put(SOURCE, "v2\n")
        self.assertEqual(self.status(write=True), "manual")
        self.assertEqual((self.root / TARGET).read_text(), "v1 hand edit\n")

    def test_new_source_file_is_created(self):
        self.commit_empty_baseline()
        self.put(SOURCE, "fresh\n")
        self.assertEqual(self.status(), "new")
        self.status(write=True)
        self.assertEqual((self.root / TARGET).read_text(), "fresh\n")

    def test_excluded_files_are_skipped(self):
        self.put(".claude/agents/monitor-agent.md", "retired\n")
        self.commit()
        self.assertIsNone(self.status("plugins/data-analysis-and-quality-plugin/agents/monitor-agent.md"))

    def test_orphan_reported_but_plugin_only_skill_is_not(self):
        self.put(TARGET, "left behind\n")
        rules = "plugins/data-analysis-and-quality-plugin/skills/plugin-rules/SKILL.md"
        self.put(rules, "plugin only\n")
        self.commit()
        self.assertEqual(self.status(), "orphan")
        self.assertIsNone(self.status(rules))

    def commit_empty_baseline(self):
        self.put("README.md", "x\n")
        self.commit()


if __name__ == "__main__":
    unittest.main()
