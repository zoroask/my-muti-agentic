"""
PreToolUse hook: blocks tool calls that reach outside the project directory.
Receives tool input JSON on stdin. Exits with code 2 to block the action.

Covers every tool that names a path in its input. Tools disagree on the field
name - file_path, notebook_path, path - and checking only one of them let the
others straight through, so all are inspected.

Bash and PowerShell are a weaker case on purpose: their paths live inside
free-text shell script. See shell_paths() for exactly how far that goes.
"""
import sys
import json
import os
import re

# The *_ROOT overrides exist so the tests can point the guard at a temp tree.
PROJECT_ROOT = os.path.normpath(os.environ.get("PATH_GUARD_ROOT", "D:/my-muti-agentic"))
MEMORY_ROOT = os.path.normpath(
    os.environ.get(
        "PATH_GUARD_MEMORY",
        r"C:\Users\zoroa\.claude\projects\D--my-muti-agentic\memory",
    )
)
ALLOWED_ROOTS = (PROJECT_ROOT, MEMORY_ROOT)

# Every field name a tool might carry a path in.
PATH_FIELDS = ("file_path", "notebook_path", "path")

# A literal drive-letter or UNC path. The lookbehind keeps it from matching
# inside a longer token: without it, HKCU:\Software matches on "U:\Software".
LITERAL_ABS = re.compile(r"(?<![A-Za-z0-9_])(?:[A-Za-z]:[\\/]|\\\\)[^\s\"'<>|;,)]+")


def block(path, reason):
    print(
        f"[path-guard] BLOCKED: '{path}' {reason}.\n"
        f"  Allowed: {', '.join(ALLOWED_ROOTS)}\n"
        "  Request explicit user permission before reaching outside this project.",
        file=sys.stderr,
    )
    sys.exit(2)


def is_allowed(path):
    """True when path resolves inside an allowed root.

    A relative path is resolved against the project, so `../secrets` is caught
    rather than quietly accepted.
    """
    if os.path.isabs(path):
        resolved = os.path.normpath(path)
    else:
        resolved = os.path.normpath(os.path.join(PROJECT_ROOT, path))
    return any(
        resolved == root or resolved.startswith(root + os.sep)
        for root in ALLOWED_ROOTS
    )


def candidate_paths(tool_input):
    """Every path this tool call names, across the differing field names."""
    found = []
    for field in PATH_FIELDS:
        value = tool_input.get(field)
        if isinstance(value, str) and value.strip():
            found.append(value)

    # Batch-edit shapes carry a list of edits, each with its own target.
    edits = tool_input.get("edits")
    if isinstance(edits, list):
        for edit in edits:
            if isinstance(edit, dict):
                value = edit.get("file_path")
                if isinstance(value, str) and value.strip():
                    found.append(value)
    return found


def shell_paths(command):
    """Literal absolute paths named in a shell command.

    This is a speed bump, not a boundary. An environment variable, a relative
    path, or a `cd` into another directory all defeat it. It exists to catch
    the careless case; do not read it as containment, and do not rely on it
    when deciding whether reaching outside the project is safe.
    """
    if not isinstance(command, str):
        return []
    return [match.group(0).rstrip(".,;:)") for match in LITERAL_ABS.finditer(command)]


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return

    tool_input = data.get("tool_input")
    if not isinstance(tool_input, dict):
        return

    for path in candidate_paths(tool_input):
        if not is_allowed(path):
            block(path, "is outside the project root")

    for path in shell_paths(tool_input.get("command")):
        if not is_allowed(path):
            block(path, "is named in this command and is outside the project root")


if __name__ == "__main__":
    main()
