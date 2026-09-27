"""Tests for the env_guard PreToolUse hook.

The hook is the project's only security control, so these run the real script as
a subprocess with crafted stdin rather than importing around it. ENV_GUARD_ROOT
points it at a scratch repo so nothing touches the real index.

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

HOOK = registry.project_root() / ".claude" / "hooks" / "env_guard.py"
BLOCKED = 2
ALLOWED = 0


def run_hook(command, root, raw_stdin=None):
    """Feed the hook a tool_input payload and return (exit code, stderr)."""
    payload = raw_stdin
    if payload is None:
        payload = json.dumps({"tool_input": {"command": command}})
    environment = {**os.environ, "ENV_GUARD_ROOT": str(root)}
    result = subprocess.run(
        [sys.executable, str(HOOK)],
        input=payload,
        capture_output=True,
        text=True,
        timeout=30,
        env=environment,
    )
    return result.returncode, result.stderr


def git(root, *args):
    subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=True)


class EnvGuardTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.addCleanup(self.temp.cleanup)

        git(self.root, "init", "-q")
        git(self.root, "config", "user.email", "test@example.com")
        git(self.root, "config", "user.name", "Test")
        (self.root / ".gitignore").write_text(".env\n", encoding="utf-8")
        (self.root / "app.py").write_text("x = 1\n", encoding="utf-8")
        git(self.root, "add", ".gitignore", "app.py")
        git(self.root, "commit", "-q", "-m", "init")

    def add_secret(self):
        (self.root / ".env").write_text("TOKEN=super-secret\n", encoding="utf-8")

    # --- commands that must pass straight through ------------------------

    def test_non_git_command_is_allowed(self):
        code, _ = run_hook("ls -la", self.root)
        self.assertEqual(code, ALLOWED)

    def test_malformed_stdin_does_not_crash(self):
        code, _ = run_hook(None, self.root, raw_stdin="not json at all")
        self.assertEqual(code, ALLOWED)

    def test_empty_stdin_does_not_crash(self):
        code, _ = run_hook(None, self.root, raw_stdin="")
        self.assertEqual(code, ALLOWED)

    def test_ordinary_add_is_allowed(self):
        code, _ = run_hook("git add app.py", self.root)
        self.assertEqual(code, ALLOWED)

    def test_commit_with_clean_index_is_allowed(self):
        code, _ = run_hook("git commit -m ok", self.root)
        self.assertEqual(code, ALLOWED)

    # --- the things it exists to stop ------------------------------------

    def test_force_adding_a_named_env_is_blocked(self):
        code, stderr = run_hook("git add -f .env", self.root)
        self.assertEqual(code, BLOCKED)
        self.assertIn("force-adds a .env", stderr)

    def test_force_adding_a_directory_that_hides_an_env_is_blocked(self):
        """`git add -f .` names no .env but defeats .gitignore anyway."""
        self.add_secret()
        code, stderr = run_hook("git add -f .", self.root)
        self.assertEqual(code, BLOCKED)
        self.assertIn(".env", stderr)

    def test_force_adding_a_directory_with_no_secret_present_is_allowed(self):
        code, _ = run_hook("git add -f .", self.root)
        self.assertEqual(code, ALLOWED)

    def test_committing_a_staged_env_is_blocked(self):
        self.add_secret()
        git(self.root, "add", "-f", ".env")
        code, stderr = run_hook("git commit -m sneaky", self.root)
        self.assertEqual(code, BLOCKED)
        self.assertIn(".env", stderr)

    def test_pushing_a_staged_env_is_blocked(self):
        self.add_secret()
        git(self.root, "add", "-f", ".env")
        code, _ = run_hook("git push origin master", self.root)
        self.assertEqual(code, BLOCKED)

    def test_env_example_is_not_treated_as_a_secret(self):
        (self.root / ".env.example").write_text("TOKEN=\n", encoding="utf-8")
        git(self.root, "add", ".env.example")
        code, _ = run_hook("git commit -m docs", self.root)
        self.assertEqual(code, ALLOWED)

    def test_env_variant_is_treated_as_a_secret(self):
        (self.root / ".gitignore").write_text(".env\n.env.local\n", encoding="utf-8")
        (self.root / ".env.local").write_text("TOKEN=x\n", encoding="utf-8")
        git(self.root, "add", "-f", ".env.local")
        code, stderr = run_hook("git commit -m nope", self.root)
        self.assertEqual(code, BLOCKED)
        self.assertIn(".env.local", stderr)

    # --- fail-closed behaviour -------------------------------------------

    def test_unusable_repo_fails_closed_on_commit(self):
        """If git cannot answer, block rather than assume nothing is staged."""
        with tempfile.TemporaryDirectory() as not_a_repo:
            code, stderr = run_hook("git commit -m x", Path(not_a_repo))
            self.assertEqual(code, BLOCKED)
            self.assertIn("failing closed", stderr)

    # --- the gap this change closes --------------------------------------

    def test_powershell_style_invocation_is_still_caught(self):
        """The guard now runs for the PowerShell tool, whose commands differ."""
        self.add_secret()
        git(self.root, "add", "-f", ".env")
        code, _ = run_hook("cd D:\\proj; git commit -q -m x", self.root)
        self.assertEqual(code, BLOCKED)

    def test_unrelated_force_later_in_a_chain_does_not_false_positive(self):
        self.add_secret()
        code, _ = run_hook("git add app.py; rm --force junk.txt", self.root)
        self.assertEqual(code, ALLOWED)


if __name__ == "__main__":
    unittest.main()
