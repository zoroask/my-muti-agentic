"""Tests for the path_guard PreToolUse hook.

Runs the real script as a subprocess with crafted stdin. PATH_GUARD_ROOT and
PATH_GUARD_MEMORY point it at temp trees so nothing depends on this machine's
actual project location.

Exit code 2 means blocked; 0 means allowed through.
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from agent_runtime import registry

HOOK = registry.project_root() / ".claude" / "hooks" / "path_guard.py"
BLOCKED = 2
ALLOWED = 0


class PathGuardTests(unittest.TestCase):
    def setUp(self):
        self.project = tempfile.TemporaryDirectory()
        self.memory = tempfile.TemporaryDirectory()
        self.addCleanup(self.project.cleanup)
        self.addCleanup(self.memory.cleanup)
        self.project_root = Path(self.project.name)
        self.memory_root = Path(self.memory.name)

    def run_hook(self, tool_input, raw_stdin=None):
        payload = raw_stdin if raw_stdin is not None else json.dumps({"tool_input": tool_input})
        result = subprocess.run(
            [sys.executable, str(HOOK)],
            input=payload,
            capture_output=True,
            text=True,
            timeout=30,
            env={
                **os.environ,
                "PATH_GUARD_ROOT": str(self.project_root),
                "PATH_GUARD_MEMORY": str(self.memory_root),
            },
        )
        return result.returncode, result.stderr

    # --- allowed ---------------------------------------------------------

    def test_path_inside_the_project_is_allowed(self):
        code, _ = self.run_hook({"file_path": str(self.project_root / "app.py")})
        self.assertEqual(code, ALLOWED)

    def test_relative_path_resolves_against_the_project(self):
        code, _ = self.run_hook({"file_path": "agent_runtime/state.py"})
        self.assertEqual(code, ALLOWED)

    def test_memory_root_is_allowed(self):
        code, _ = self.run_hook({"file_path": str(self.memory_root / "note.md")})
        self.assertEqual(code, ALLOWED)

    def test_tool_with_no_path_passes_through(self):
        code, _ = self.run_hook({"pattern": "TODO", "output_mode": "content"})
        self.assertEqual(code, ALLOWED)

    def test_malformed_stdin_does_not_crash(self):
        code, _ = self.run_hook(None, raw_stdin="not json")
        self.assertEqual(code, ALLOWED)

    def test_command_with_only_relative_paths_is_allowed(self):
        code, _ = self.run_hook({"command": "python -m agent_runtime audit"})
        self.assertEqual(code, ALLOWED)

    def test_registry_path_is_not_mistaken_for_a_drive_path(self):
        """Without the lookbehind, HKCU:\\Software matches on U:\\Software."""
        code, stderr = self.run_hook({"command": "reg query HKCU:\\Software\\Classes"})
        self.assertEqual(code, ALLOWED, stderr)

    def test_env_var_path_is_not_caught(self):
        """Documents the known limit: a variable defeats the shell scan."""
        code, _ = self.run_hook({"command": "Get-Content $env:LOCALAPPDATA\\thing.txt"})
        self.assertEqual(code, ALLOWED)

    # --- blocked ---------------------------------------------------------

    def test_absolute_path_outside_is_blocked(self):
        code, stderr = self.run_hook({"file_path": "C:\\Windows\\System32\\drivers\\etc\\hosts"})
        self.assertEqual(code, BLOCKED)
        self.assertIn("outside the project root", stderr)

    def test_parent_directory_escape_is_blocked(self):
        code, _ = self.run_hook({"file_path": "../secrets.txt"})
        self.assertEqual(code, BLOCKED)

    def test_notebook_path_is_checked(self):
        """notebook_path was never inspected before this change."""
        code, stderr = self.run_hook({"notebook_path": "C:\\elsewhere\\book.ipynb"})
        self.assertEqual(code, BLOCKED)
        self.assertIn("book.ipynb", stderr)

    def test_grep_path_is_checked(self):
        """Glob and Grep use `path`, which was never inspected before."""
        code, _ = self.run_hook({"pattern": "secret", "path": "C:\\Users\\someone"})
        self.assertEqual(code, BLOCKED)

    def test_batch_edit_targets_are_checked(self):
        code, _ = self.run_hook({"edits": [{"file_path": "C:\\Windows\\win.ini"}]})
        self.assertEqual(code, BLOCKED)

    def test_literal_outside_path_in_a_shell_command_is_blocked(self):
        code, stderr = self.run_hook({"command": 'Get-Content "C:\\Windows\\win.ini"'})
        self.assertEqual(code, BLOCKED)
        self.assertIn("named in this command", stderr)

    def test_forward_slash_absolute_path_is_blocked(self):
        code, _ = self.run_hook({"command": "cat C:/Windows/win.ini"})
        self.assertEqual(code, BLOCKED)

    def test_unc_path_is_blocked(self):
        code, _ = self.run_hook({"command": "copy \\\\server\\share\\file.txt ."})
        self.assertEqual(code, BLOCKED)

    def test_first_offending_path_of_several_is_reported(self):
        code, stderr = self.run_hook(
            {"file_path": str(self.project_root / "ok.py"), "path": "C:\\Windows"}
        )
        self.assertEqual(code, BLOCKED)
        self.assertIn("Windows", stderr)


if __name__ == "__main__":
    unittest.main()
