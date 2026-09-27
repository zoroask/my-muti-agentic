"""
PreToolUse hook: blocks git commands that would commit or push .env-style
secret files. Receives tool input JSON on stdin. Exits with code 2 to block.

Wired to both the Bash and PowerShell tools. Covering only Bash left git run
through PowerShell completely unguarded, which is how every commit in one
session slipped past this hook without anyone noticing.

Every git call here fails closed: if we cannot prove no secret is at risk, we
block rather than assume the best.
"""
import sys
import json
import re
import os
import subprocess

# ENV_GUARD_ROOT lets the tests point the guard at a scratch repo.
PROJECT_ROOT = os.path.normpath(os.environ.get("ENV_GUARD_ROOT", "D:/my-muti-agentic"))

# A force-add that names a .env outright.
FORCE_ADD_ENV = re.compile(
    r"git\s+add\b.*(-f\b|--force\b).*\.env\S*|git\s+add\b.*\.env\S*.*(-f\b|--force\b)"
)
# A force-add of a directory or glob names no .env but sweeps one in anyway:
# `git add -f .` defeats .gitignore. The lookahead stays inside one command
# segment so an unrelated --force later in a chain does not trigger it.
FORCE_ADD_ANY = re.compile(r"\bgit\s+add\b(?=[^;&|]*(?:\s-f\b|\s--force\b))")
COMMIT_OR_PUSH = re.compile(r"\bgit\s+(commit|push)\b")


def block(message):
    print(f"[env-guard] BLOCKED: {message}", file=sys.stderr)
    sys.exit(2)


def is_env_file(path):
    name = os.path.basename(path.strip())
    if name == ".env":
        return True
    if name.startswith(".env.") and name != ".env.example":
        return True
    return False


def git(*args):
    """Run git in the project, failing closed on any problem."""
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=PROJECT_ROOT, capture_output=True, text=True, timeout=10,
        )
    except Exception as e:
        block(f"cannot run git ({e}); failing closed.")
    if result.returncode != 0:
        block(
            f"'git {' '.join(args)}' failed; cannot confirm no .env is at risk; "
            "failing closed."
        )
    return result.stdout


def staged_env_files():
    """Env files already in the index."""
    return [f for f in git("diff", "--cached", "--name-only").splitlines() if is_env_file(f)]


def ignored_env_files():
    """Env files git is currently ignoring - what a force-add would sweep in."""
    found = []
    for line in git("status", "--porcelain", "--ignored=matching").splitlines():
        if not line.startswith("!!"):
            continue
        path = line[2:].strip()
        if path.endswith("/"):
            continue  # a collapsed directory, not a file
        if is_env_file(path):
            found.append(path)
    return found


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return

    command = data.get("tool_input", {}).get("command", "")
    if not command or "git" not in command:
        return

    if FORCE_ADD_ENV.search(command):
        block(
            "this force-adds a .env file, which is gitignored on purpose.\n"
            f"  Command: {command}"
        )

    if FORCE_ADD_ANY.search(command):
        offenders = ignored_env_files()
        if offenders:
            block(
                "this is a force-add, which defeats .gitignore, and these secret "
                "files would be swept in:\n"
                + "\n".join(f"  {f}" for f in offenders)
                + "\n  Add the specific paths you want instead of forcing."
            )

    if COMMIT_OR_PUSH.search(command):
        offenders = staged_env_files()
        if offenders:
            block(
                ".env file(s) are staged and would be committed/pushed:\n"
                + "\n".join(f"  {f}" for f in offenders)
                + "\n  Run 'git reset HEAD <file>' to unstage before committing."
            )


if __name__ == "__main__":
    main()
