"""
PreToolUse hook: blocks git commands that would commit or push .env-style
secret files. Receives tool input JSON on stdin. Exits with code 2 to block.
"""
import sys
import json
import re
import os
import subprocess

PROJECT_ROOT = os.path.normpath("D:/my-muti-agentic")

FORCE_ADD_ENV = re.compile(
    r"git\s+add\b.*(-f\b|--force\b).*\.env\S*|git\s+add\b.*\.env\S*.*(-f\b|--force\b)"
)
COMMIT_OR_PUSH = re.compile(r"\bgit\s+(commit|push)\b")


def is_env_file(path):
    name = os.path.basename(path.strip())
    if name == ".env":
        return True
    if name.startswith(".env.") and name != ".env.example":
        return True
    return False


def staged_env_files():
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            cwd=PROJECT_ROOT, capture_output=True, text=True, timeout=10,
        )
    except Exception:
        return []
    return [f for f in result.stdout.splitlines() if is_env_file(f)]


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return

    command = data.get("tool_input", {}).get("command", "")
    if not command or "git" not in command:
        return

    if FORCE_ADD_ENV.search(command):
        print(
            "[env-guard] BLOCKED: this force-adds a .env file, which is gitignored on purpose.\n"
            f"  Command: {command}",
            file=sys.stderr,
        )
        sys.exit(2)

    if COMMIT_OR_PUSH.search(command):
        offenders = staged_env_files()
        if offenders:
            print(
                "[env-guard] BLOCKED: .env file(s) are staged and would be committed/pushed:\n"
                + "\n".join(f"  {f}" for f in offenders)
                + "\n  Run 'git reset HEAD <file>' to unstage before committing.",
                file=sys.stderr,
            )
            sys.exit(2)


if __name__ == "__main__":
    main()
