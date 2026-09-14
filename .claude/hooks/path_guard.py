"""
PreToolUse hook: blocks Write/Edit/Read on files outside the project directory.
Receives tool input JSON on stdin. Exits with code 2 to block the action.
"""
import sys
import json
import os

PROJECT_ROOT = os.path.normpath("D:/my-muti-agentic")
MEMORY_ROOT = os.path.normpath(
    r"C:\Users\zoroa\.claude\projects\D--my-muti-agentic\memory"
)
ALLOWED_ROOTS = (PROJECT_ROOT, MEMORY_ROOT)


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return

    tool_input = data.get("tool_input", {})
    file_path = tool_input.get("file_path", "")

    if not file_path:
        return

    if os.path.isabs(file_path):
        normalized = os.path.normpath(file_path)
    else:
        normalized = os.path.normpath(os.path.join(PROJECT_ROOT, file_path))

    if not any(
        normalized == root or normalized.startswith(root + os.sep)
        for root in ALLOWED_ROOTS
    ):
        print(
            f"[path-guard] BLOCKED: '{file_path}' is outside the project root.\n"
            f"  Allowed: {', '.join(ALLOWED_ROOTS)}\n"
            f"  Request explicit user permission before modifying files outside this project.",
            file=sys.stderr,
        )
        sys.exit(2)


if __name__ == "__main__":
    main()
